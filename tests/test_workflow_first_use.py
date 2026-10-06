"""干净复制一项 ArtCraft 技能，安装全部依赖并交付四个原生工程。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
import struct
import math

SOURCE = Path(os.environ['CRAFT_INSTALLED_SKILL_ROOT']).resolve() if os.environ.get('CRAFT_INSTALLED_SKILL_ROOT') else Path(__file__).resolve().parents[1]/'skills/artcraft-use'

def archive_arguments(environment):
    # 在线验收必须走默认公开下载，不能误用宿主遗留的离线制品参数。
    if environment.get('CRAFT_ONLINE_FIRST_USE') == '1':
        return []
    if not environment.get('CRAFT_NODE_ARCHIVE') or not environment.get('CRAFT_BUNDLE_DIRECTORY'):
        raise ValueError('offline_archives_required')
    return ['--node-archive', environment['CRAFT_NODE_ARCHIVE'],
            '--bundle-dir', environment['CRAFT_BUNDLE_DIRECTORY']]


class FirstUseArgumentTests(unittest.TestCase):
    def test_online_mode_does_not_forward_archive_overrides(self):
        self.assertEqual(archive_arguments({'CRAFT_ONLINE_FIRST_USE': '1',
                                           'CRAFT_NODE_ARCHIVE': 'stale-node',
                                           'CRAFT_BUNDLE_DIRECTORY': 'stale-bundles'}), [])

    def test_offline_mode_requires_both_verified_archive_inputs(self):
        with self.assertRaisesRegex(ValueError, 'offline_archives_required'):
            archive_arguments({'CRAFT_NODE_ARCHIVE': 'node'})
        self.assertEqual(archive_arguments({'CRAFT_NODE_ARCHIVE': 'node', 'CRAFT_BUNDLE_DIRECTORY': 'bundles'}),
                         ['--node-archive', 'node', '--bundle-dir', 'bundles'])


@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST') == '1' and
                     (os.environ.get('CRAFT_ONLINE_FIRST_USE') == '1' or
                      (os.environ.get('CRAFT_NODE_ARCHIVE') and os.environ.get('CRAFT_BUNDLE_DIRECTORY'))),
                     'requires declared online first use or verified offline archives')
class FirstWorkflowTests(unittest.TestCase):
    def test_isolated_single_skill_installs_runs_and_reuses_four_native_deliveries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();skill=root/'only-artcraft-use';shutil.copytree(SOURCE, skill, ignore=shutil.ignore_patterns('__pycache__'))
            voice=root/'voice.wav'
            with wave.open(str(voice), 'wb') as output:
                output.setparams((1,2,48000,48000,'NONE','not compressed'))
                output.writeframes(b''.join(struct.pack('<h',round(4000*math.sin(i*2*math.pi*440/48000))) for i in range(48000)))
            runtime=root/'runtime';project=root/'project'
            args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(skill/'examples/brand-campaign.json'),'--output',str(project),'--runtime-home',str(runtime),'--authorization','isolated-first-use','--asset','voice='+str(voice)]
            # 使用复制的单技能公开入口创建需求记录，不借用仓库内部 API。
            brief=json.loads((skill/'examples/brand-brief.json').read_text());brief['authorizationRef']='isolated-first-use'
            brief_input=root/'brief-input.json';brief_input.write_text(json.dumps(brief));brief_root=root/'brief-v1'
            created=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/brief.py'),'create','--input',str(brief_input),'--output',str(brief_root)],capture_output=True,text=True,timeout=30)
            self.assertEqual(created.returncode,0,created.stdout+created.stderr);brief_receipt=json.loads(created.stdout)
            args.extend(['--brief',str(brief_root),'--brief-sha',brief_receipt['sha256']])
            args.extend(archive_arguments(os.environ))
            environment=dict(os.environ,PATH='/usr/bin:/bin')
            first_run=subprocess.run(args,capture_output=True,text=True,env=environment,timeout=240)
            self.assertEqual(first_run.returncode,0,first_run.stdout+first_run.stderr)
            first=json.loads(first_run.stdout);self.assertEqual(first['state'],'review_ready')
            for id, suffix in [('logo','vectorcraft'),('poster','pcraft'),('intro','ecproj'),('film','fcproj')]:
                node=first['nodes'][id];self.assertEqual(node['status'],'review_ready')
                self.assertTrue((Path(node['root'])/('project.'+suffix)).is_file())
            setup=json.loads((project/'installation-receipt.json').read_text())
            self.assertTrue(Path(setup['nodeExecutable']).is_relative_to(runtime))
            self.assertTrue(Path(setup['entryPoint']).is_relative_to(runtime))
            self.assertEqual(set(setup['skills']),{'filmcraft','effectcraft','photocraft','vectorcraft'})
            distribution=json.loads((skill/'scripts/distribution.lock.json').read_text())
            self.assertEqual(setup['version'],distribution['version'])
            for name,value in setup['skills'].items():self.assertEqual(value['runtimeIdentity']['pluginVersion'],distribution['bundles'][name+'-skills'].get('version',distribution['version']))
            self.assertEqual(first['budget']['allocated'],{'minorUnits':0,'externalCalls':0,'revisions':0})
            for value in setup['skills'].values():
                self.assertTrue(Path(value['executable']).is_relative_to(runtime))
                self.assertTrue(Path(value['skillRoot']).is_relative_to(runtime))
            second_run=subprocess.run(args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(second_run.returncode,0,second_run.stdout+second_run.stderr)
            second=json.loads(second_run.stdout)
            for id in first['nodes']:self.assertEqual(first['nodes'][id]['taskId'],second['nodes'][id]['taskId'])
            cli=[setup['nodeExecutable'],setup['entryPoint'],'status','--database',str(project/'tasks.sqlite')]
            status=json.loads(subprocess.run(cli,check=True,capture_output=True,text=True,env=environment,timeout=30).stdout)
            self.assertEqual(len(status['tasks']),4);self.assertFalse(status['leases'])
            # 切换缓存位置会改变可信登记绑定；拒绝后不能发布新项目安装身份。
            prior_files={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()}
            relocated_args=list(args);relocated_args[relocated_args.index('--runtime-home')+1]=str(root/'different-runtime')
            rejected=subprocess.run(relocated_args,capture_output=True,text=True,env=environment,timeout=240)
            self.assertEqual(rejected.returncode,1);self.assertIn('workflow_revision_conflict',rejected.stdout)
            self.assertEqual({str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()},prior_files)
            changed=json.loads((skill/'examples/brand-campaign.json').read_text());changed['nodes'][0]['payload']['plan']['document']['name']='Changed without new revision'
            changed_file=root/'changed.json';changed_file.write_text(json.dumps(changed))
            bad_args=list(args);bad_args[4]=str(changed_file)
            bad=subprocess.run(bad_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(bad.returncode,1);self.assertIn('workflow_revision_conflict',bad.stdout)
            self.assertEqual(hashlib.sha256(voice.read_bytes()).hexdigest(),first['nodes']['film']['outputs'][0]['sourceRefs'][1]['sha256'])

            # 单技能首次使用后的公开打包入口，不依赖全局 Node 或仓库脚本。
            package=root/'delivery-package'
            pack_args=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'create','--project',str(project),'--workflow',first['runKey'],'--output',str(package),'--authorization','isolated-first-use','--runtime-home',str(runtime)]
            pack_args.extend(archive_arguments(os.environ))
            packed_run=subprocess.run(pack_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(packed_run.returncode,0,packed_run.stdout+packed_run.stderr)
            packed=json.loads(packed_run.stdout);self.assertEqual(len(packed['children']),4)
            moved=root/'moved-package';package.rename(moved)
            verify_args=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'verify','--package',str(moved),'--sha',packed['sha256'],'--runtime-home',str(runtime)]
            verify_args.extend(archive_arguments(os.environ))
            verified_run=subprocess.run(verify_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(verified_run.returncode,0,verified_run.stdout+verified_run.stderr)
            self.assertEqual(len(json.loads(verified_run.stdout)['children']),4)
            self.assertEqual(json.loads((moved/'workflow-plan-portable.json').read_text())['projectBrief'],brief)
            if os.environ.get('CRAFT_WORKFLOW_EVIDENCE_FILE'):
                artifacts={id:[{'assetId':a['assetId'],'sha256':a['sha256'],'bytes':a['bytes'],'mediaType':a['mediaType'],'nativeProjectRef':a['nativeProjectRef']} for a in value['outputs']] for id,value in first['nodes'].items()}
                proof={'schema':'craft-installed-mixed-first-use/v1','python':sys.version.split()[0],'runtimeVersion':setup['version'],'briefSha256':brief_receipt['sha256'],'artifacts':artifacts,'packageSha256':packed['sha256'],'voiceSha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'sourceSkillVersions':{name:entry['version'] for name,entry in distribution['bundles'].items()},'checks':['four native domain deliveries','same-revision no replay','status has four tasks and zero leases','relocated runtime conflict preserves whole project','changed frozen plan refused','voice source digest bound','four-child moved package verified','portable Brief retained'],'scope':'single copied installed skill, fresh default online install and system-only PATH; technical fixture, not creative acceptance'}
                with Path(os.environ['CRAFT_WORKFLOW_EVIDENCE_FILE']).open('x') as output:json.dump(proof,output,ensure_ascii=False,indent=2);output.write('\n')

if __name__ == '__main__':unittest.main()
