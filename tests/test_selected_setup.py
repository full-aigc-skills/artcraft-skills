"""按所需领域安装，不把未安装工具写入能力回执。"""
import importlib.util
import json
import hashlib
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/artcraft-use/scripts/setup.py'
spec=importlib.util.spec_from_file_location('selected_setup',SCRIPT);setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
W=ROOT/'skills/artcraft-use/scripts/workflow.py'
spec=importlib.util.spec_from_file_location('selected_workflow',W);workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)

class SelectedSetupTests(unittest.TestCase):
    def test_selected_install_receipt_contains_only_real_dependencies(self):
        lock=json.loads(SCRIPT.with_name('distribution.lock.json').read_text())
        for plugins in (['vectorcraft'],[],None):
            expected=list(setup.NAMES) if plugins is None else plugins
            with self.subTest(plugins=plugins),tempfile.TemporaryDirectory() as temporary:
                installed=[]
                def bundle(entry,target,archive):
                    name=next(k for k,v in lock['bundles'].items() if v is entry);installed.append(name)
                    return ROOT if name=='artcraft-runtime' else ROOT.parent/name
                def run(args,**kwargs):
                    if args[-1]=='--version':value=json.dumps({'name':'artcraft','version':lock['version']})
                    elif args[-2:]==['commands','--json']:value=b'[{"id":"test"}]'
                    else:value=json.dumps({'executable':'/usr/bin/true','binarySha256':'a'*64})
                    return subprocess.CompletedProcess(args,0,stdout=value)
                with patch.object(setup,'install_bundle',side_effect=bundle),patch.object(setup.subprocess,'run',side_effect=run):
                    receipt=setup.setup(lock,Path(temporary)/'runtime',{'nodeExecutable':'/fixture/node'},plugins=plugins)
                self.assertEqual(set(installed),{'artcraft-runtime',*[n+'-skills' for n in expected]})
                self.assertEqual(set(receipt['bundleHashes']),set(installed))
                self.assertEqual(set(receipt['skills']),set(expected))
                for name in expected:
                    domain=receipt['skills'][name]
                    digest=domain['capabilitySnapshot']['scriptHashes']['preserved_stage.py']
                    self.assertEqual(digest,setup.sha(Path(domain['skillRoot'])/'scripts/preserved_stage.py'))
                    self.assertIn({'path':str(Path(domain['skillRoot'])/'scripts/preserved_stage.py'),'sha256':digest},domain['files'])
                    if name == 'vectorcraft':
                        guard = Path(domain['skillRoot'])/'scripts/brand_variants.py'
                        digest = domain['capabilitySnapshot']['scriptHashes']['brand_variants.py']
                        self.assertEqual(digest, setup.sha(guard))
                        self.assertIn({'path':str(guard),'sha256':digest}, domain['files'])
                    if name == 'photocraft':
                        delivery = Path(domain['skillRoot'])/'scripts/delivery.py'
                        digest = domain['capabilitySnapshot']['scriptHashes']['delivery.py']
                        self.assertEqual(digest, setup.sha(delivery))
                        self.assertIn({'path':str(delivery),'sha256':digest}, domain['files'])

    def test_skill_first_use_instructions_do_not_preinstall_unused_domains(self):
        suite=json.loads((ROOT/'skill-suite.json').read_text())
        for entry in suite['skills']:
            text=(ROOT/'skills'/entry['name']/'SKILL.md').read_text()
            commands=[line for line in text.splitlines() if line.startswith('python3 ') and '$SKILL_DIR/scripts/bootstrap.py' in line]
            self.assertTrue(commands,entry['name'])
            self.assertTrue(all('--runtime-only' in line for line in commands),entry['name'])
            self.assertNotIn('Video Factory 的适配尚未接入',text)

    def test_domain_failure_preserves_bootstrap_error(self):
        lock=json.loads(SCRIPT.with_name('distribution.lock.json').read_text())
        def bundle(entry,target,archive):
            name=next(k for k,v in lock['bundles'].items() if v is entry)
            return ROOT if name=='artcraft-runtime' else ROOT.parent/name
        def run(args,**kwargs):
            if args[-1]=='--version':return subprocess.CompletedProcess(args,0,stdout=json.dumps({'name':'artcraft','version':lock['version']}))
            return subprocess.CompletedProcess(args,1,stdout='{"error":"archive_digest_mismatch"}')
        with tempfile.TemporaryDirectory() as temporary,patch.object(setup,'install_bundle',side_effect=bundle),patch.object(setup.subprocess,'run',side_effect=run):
            with self.assertRaisesRegex(ValueError,'domain_setup_failed: vectorcraft: .*archive_digest_mismatch'):
                setup.setup(lock,Path(temporary)/'runtime',{'nodeExecutable':'/fixture/node'},plugins=['vectorcraft'])

    def test_invalid_selection_fails_before_writing_runtime(self):
        lock=json.loads(SCRIPT.with_name('distribution.lock.json').read_text())
        for plugins in (['jianying'],['vectorcraft','vectorcraft'],'vectorcraft',[None]):
            with self.subTest(plugins=plugins),tempfile.TemporaryDirectory() as temporary:
                runtime=Path(temporary)/'runtime'
                with self.assertRaisesRegex(ValueError,'plugin_selection_invalid'):
                    setup.setup(lock,runtime,{},plugins=plugins)
                self.assertFalse(runtime.exists())

    def test_duplicate_bootstrap_selection_does_not_install_node(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime=Path(temporary)/'runtime'
            result=subprocess.run([sys.executable,'-I','-B',str(SCRIPT.with_name('bootstrap.py')),'--runtime-home',str(runtime),'--plugin','vectorcraft','--plugin','vectorcraft'],capture_output=True,text=True)
            self.assertEqual(result.returncode,1);self.assertIn('plugin_selection_invalid',result.stdout);self.assertFalse(runtime.exists())

    def test_task_graph_selection_refuses_missing_or_conflicting_executor(self):
        self.assertEqual(workflow.required_plugins({'nodes':[{'pluginId':'vectorcraft'},{'runtimeIdentity':{'pluginId':'photocraft'}},{'pluginId':'vectorcraft'}]}),['photocraft','vectorcraft'])
        self.assertEqual(workflow.required_plugins({'nodes':[{'pluginId':'video-factory'}]}),[])
        for nodes in ([{'pluginId':'jianying'}],[{}],[{'pluginId':'vectorcraft','runtimeIdentity':{'pluginId':'filmcraft'}}]):
            with self.assertRaisesRegex(ValueError,'capability_missing|runtime_identity_mismatch'):
                workflow.required_plugins({'nodes':nodes})

@unittest.skipUnless(os.environ.get('CRAFT_SELECTED_FIRST_USE')=='1','requires default public dependencies and native macOS arm64 CLIs')
class SelectedFirstUseTests(unittest.TestCase):
    def test_vector_only_then_incremental_poster_and_unknown_executor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-plan'
            shutil.copytree(ROOT/'skills/artcraft-cli-plan',skill,ignore=shutil.ignore_patterns('__pycache__'))
            runtime=root/'runtime';project=root/'project'
            template=json.loads((skill/'examples/brand-campaign.json').read_text())
            plan=json.loads(json.dumps(template));plan['nodes']=[n for n in plan['nodes'] if n['id']=='logo']
            def run(value,home=runtime,output=project):
                path=root/(value['revision']+'.json');path.write_text(json.dumps(value))
                result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(path),'--output',str(output),'--runtime-home',str(home),'--authorization','selected-first-use'],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
                return result
            first=run(plan);self.assertEqual(first.returncode,0,first.stdout+first.stderr);one=json.loads(first.stdout)
            self.assertEqual(one['state'],'review_ready')
            receipt=json.loads((project/'installation-receipt.json').read_text())
            self.assertEqual(set(receipt['skills']),{'vectorcraft'})
            self.assertEqual(set(receipt['bundleHashes']),{'artcraft-runtime','vectorcraft-skills'})
            for name in ['filmcraft','effectcraft','photocraft']:
                self.assertFalse((runtime/name).exists());self.assertFalse((runtime/'artcraft/bundles'/(name+'-skills')).exists())
            old=Path(one['nodes']['logo']['root']);old_hashes={str(p.relative_to(old)):hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
            plan['revision']='v2';plan['nodes'].append(next(n for n in template['nodes'] if n['id']=='poster'))
            second=run(plan);self.assertEqual(second.returncode,0,second.stdout+second.stderr);two=json.loads(second.stdout)
            self.assertEqual(two['state'],'review_ready');self.assertEqual(one['nodes']['logo']['taskId'],two['nodes']['logo']['taskId'])
            self.assertTrue((Path(two['nodes']['poster']['root'])/'project.pcraft').is_file())
            receipt=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(set(receipt['skills']),{'photocraft','vectorcraft'})
            for name in ['filmcraft','effectcraft']:
                self.assertFalse((runtime/name).exists());self.assertFalse((runtime/'artcraft/bundles'/(name+'-skills')).exists())
            for path,digest in old_hashes.items():self.assertEqual(hashlib.sha256((old/path).read_bytes()).hexdigest(),digest)
            again=run(plan);self.assertEqual(again.returncode,0,again.stdout+again.stderr);three=json.loads(again.stdout)
            self.assertEqual(two['budget'],three['budget']);self.assertEqual({k:n['taskId'] for k,n in two['nodes'].items()},{k:n['taskId'] for k,n in three['nodes'].items()})
            def query(script,*arguments,home=runtime):
                result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,arguments),'--runtime-home',str(home)],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
            packed=query('package.py','create','--project',project,'--workflow',two['runKey'],'--authorization','selected-first-use','--output',root/'delivery')
            self.assertEqual(len(query('package.py','verify','--package',root/'delivery','--sha',packed['sha256'])['children']),2)
            clean_verify=root/'verify-runtime'
            self.assertEqual(len(query('package.py','verify','--package',root/'delivery','--sha',packed['sha256'],home=clean_verify)['children']),2)
            self.assertTrue((clean_verify/'artcraft').is_dir())
            for name in setup.NAMES:self.assertFalse((clean_verify/name).exists())
            status=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/cli.py'),'--runtime-home',str(runtime),'--','status','--database',str(project/'tasks.sqlite')],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
            self.assertEqual(status.returncode,0,status.stdout+status.stderr)
            for name in ['filmcraft','effectcraft']:
                self.assertFalse((runtime/name).exists());self.assertFalse((runtime/'artcraft/bundles'/(name+'-skills')).exists())
            plan['revision']='v3';plan['nodes'][0]['pluginId']='jianying';newruntime=root/'unsupported-runtime'
            failed=run(plan,newruntime,root/'unsupported-project');self.assertNotEqual(failed.returncode,0);self.assertIn('capability_missing: jianying',failed.stdout);self.assertFalse(newruntime.exists())
            self.assertFalse(any(skill.rglob('*.pyc')))

if __name__=='__main__':unittest.main()
