"""嵌套公开入口保留安装诊断；返工未知步骤不得因此重放。"""
from pathlib import Path
from argparse import Namespace
import contextlib,importlib.util,io,json,shutil,subprocess,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_revision
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 spec=importlib.util.spec_from_file_location('nested_'+path.stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class NestedSetupTests(unittest.TestCase):
 def test_ten_single_skills_preserve_review_domain_and_revision_setup_failure(self):
  for source in sorted((ROOT/'skills').iterdir()):
   if not (source/'SKILL.md').is_file():continue
   with self.subTest(skill=source.name),tempfile.TemporaryDirectory(prefix='nested 安装 ') as temporary:
    root=Path(temporary);skill=root/'.agents/skills'/source.name;shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'));(skill/'scripts/node.lock.json').write_text('null');runtime=root/'runtime';package=root/'package';package.mkdir()
    commands=[('review.py',['verify','--package',str(package),'--package-sha','a'*64,'--review',str(root/'review'),'--review-sha','b'*64]),('domain_commands.py',['check','vectorcraft',str(skill/'examples/domain-vectorcraft-create.json')])]
    for script,argv in commands:
     with self.subTest(entry=script):
      result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*argv,'--runtime-home',str(runtime)],capture_output=True,text=True,timeout=20);self.assertEqual(result.returncode,1,result.stdout+result.stderr);reply=json.loads(result.stdout)
      self.assertEqual(reply.get('dependencySetup',{}).get('bootstrapScript'),str((skill/'scripts/bootstrap.py').resolve()))
      self.assertEqual(reply['installationReceipt']['error'],'node_lock_invalid');self.assertEqual(reply['result'],'failed');self.assertFalse(runtime.exists());self.assertNotIn('workflowReceipt',reply);self.assertNotIn('Traceback',result.stderr)
    m=load(skill/'scripts/revision.py');args=Namespace(runtime_home=runtime,node_archive=None,bundle_dir=None,native_archive_dir=None)
    with self.assertRaises(RuntimeError) as stopped:m.invoke(args,'package.py',['verify','--package',package,'--sha','a'*64])
    self.assertEqual(stopped.exception.diagnostic['dependencySetup']['bootstrapScript'],str((skill/'scripts/bootstrap.py').resolve()));self.assertEqual(stopped.exception.diagnostic['installationReceipt']['error'],'node_lock_invalid');self.assertFalse(runtime.exists())
 def test_pending_workflow_install_failure_keeps_identity_rounds_and_no_replay(self):
  fixture=test_revision.RevisionTests();m=fixture.module()
  with tempfile.TemporaryDirectory() as temporary:
   args,package,review,request=fixture.harness(m,Path(temporary));launches=[]
   reply={'error':'setup_failed','result':'failed','dependencySetup':{'bootstrapScript':'untrusted-other-install'},'installationReceipt':{'error':'node_lock_invalid','installed':False}}
   def invoke(args,script,values):
    if script=='review.py':return review
    if script=='workflow.py':
     launches.append(script);raise m.P.PublicCallFailure('fixture setup',reply,args.runtime_home)
    return package
   with patch.object(m,'invoke',side_effect=invoke):
    first=m.step(args);self.assertEqual(first['state'],'outcome_unknown');self.assertIn('dependencySetup',first);state=m.read_state(args.project);self.assertEqual(state['rounds'],1);pending=state['pending']['key'];self.assertIn('publicCallReceipt',state['pending'])
    second=m.step(args);self.assertEqual(second['state'],'outcome_unknown');self.assertEqual(second['pendingStep'],pending);self.assertEqual(len(launches),1);self.assertEqual(m.read_state(args.project)['rounds'],1)
    args.resume=True
    def install_refusal(args,script,values):
     if script=='package.py':raise m.P.PublicCallFailure('preflight setup failed',reply,args.runtime_home)
     return invoke(args,script,values)
    with patch.object(m,'invoke',side_effect=install_refusal):
     refused=m.step(args);self.assertEqual(refused['state'],'outcome_unknown');self.assertEqual(refused['pendingStep'],pending);self.assertIn('dependencySetup',refused)
    self.assertEqual(len(launches),1);self.assertEqual(m.read_state(args.project)['rounds'],1)
 def test_review_preserves_native_refusal_without_installation_classification(self):
  m=load(ROOT/'skills/artcraft-use/scripts/review.py')
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);result=SimpleNamespace(returncode=1,stdout=json.dumps({'error':'artifact_invalid'}),stderr='');args=Namespace(package=root,package_sha='a'*64,runtime_home=root/'runtime',node_archive=None,bundle_dir=None,native_archive_dir=None)
   with patch.object(m.subprocess,'run',return_value=result),self.assertRaises(RuntimeError) as stopped:m.verify_package(args)
   self.assertEqual(stopped.exception.diagnostic['publicCallReceipt'],{'error':'artifact_invalid'});self.assertNotIn('dependencySetup',stopped.exception.diagnostic)
 def test_direct_installer_timeout_and_nested_unknown_have_own_recovery_path(self):
  m=load(ROOT/'skills/artcraft-use/scripts/domain_commands.py')
  with tempfile.TemporaryDirectory() as temporary:
   home=Path(temporary)/'runtime'
   with patch.object(m.P.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',.1)) as run,self.assertRaises(RuntimeError) as stopped:m.P.run(['fixture'],'fixture: ',home,installation=True)
   self.assertEqual(stopped.exception.diagnostic['result'],'unknown');self.assertFalse(stopped.exception.diagnostic['dependencySetup']['automaticRetry']);self.assertFalse(home.exists());run.assert_called_once()
   reply={'error':'timeout','result':'unknown','dependencySetup':{'bootstrapScript':'another installation'},'installationReceipt':{'error':'timeout'}}
   error=m.P.PublicCallFailure('nested',reply,home)
   self.assertEqual(error.diagnostic['dependencySetup']['bootstrapScript'],str((ROOT/'skills/artcraft-use/scripts/bootstrap.py').resolve()));self.assertEqual(error.diagnostic['result'],'unknown')
   self.assertEqual(error.diagnostic['publicCallReceipt'],reply)

 def test_direct_installer_zero_exit_invalid_identity_is_refused(self):
  m=load(ROOT/'skills/artcraft-use/scripts/domain_commands.py')
  for value in ({},{'schema':'wrong'},{'schema':'artcraft-setup/v1','nodeExecutable':None}):
   with self.subTest(value=value),patch.object(m.P.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(value),stderr='')),self.assertRaisesRegex(RuntimeError,'setup_incomplete') as stopped:m.P.run(['fixture'],'fixture: ',Path('/not-used-runtime'),installation=True)
   self.assertIn('dependencySetup',stopped.exception.diagnostic)

if __name__=='__main__':unittest.main()
