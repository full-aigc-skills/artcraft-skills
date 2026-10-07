"""分发锁结构错误必须先于 Node 安装和所有目录写入拒绝。"""
import copy,importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/artcraft-use/scripts'
class DistributionPreflightTests(unittest.TestCase):
 def cases(self):
  original=json.loads((SCRIPTS/'distribution.lock.json').read_text());cases=[None,[],{},'invalid']
  for field,value in [('version',None),('version',7),('bundles',[]),('bundles',None)]:
   changed=copy.deepcopy(original);changed[field]=value;cases.append(changed)
  for value in [None,[],{},dict(original['bundles']['artcraft-runtime'],url=None),dict(original['bundles']['artcraft-runtime'],bytes=True),dict(original['bundles']['artcraft-runtime'],files={'LICENSE':[]}),dict(original['bundles']['artcraft-runtime'],filename='../bundle.zip')]:
   changed=copy.deepcopy(original);changed['bundles']['artcraft-runtime']=value;cases.append(changed)
  return cases
 def module(self):
  spec=importlib.util.spec_from_file_location('preflight_bootstrap',SCRIPTS/'bootstrap.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 def test_public_bootstrap_rejects_distribution_before_node_install(self):
  import contextlib,io
  for lock in self.cases():
   with self.subTest(lock=lock),tempfile.TemporaryDirectory() as temporary:
    module=self.module();runtime=Path(temporary)/'runtime';out=io.StringIO()
    node=json.loads((SCRIPTS/'node.lock.json').read_text())
    def read(path,*args,**kwargs):return json.dumps(node if path.name=='node.lock.json' else lock)
    with patch.object(Path,'read_text',read),patch.object(module,'install_node',side_effect=AssertionError('Node installation reached')) as install,patch.object(sys,'argv',['bootstrap.py','--runtime-home',str(runtime),'--runtime-only']),contextlib.redirect_stdout(out):
     with self.assertRaises(SystemExit) as stopped:module.main()
    self.assertEqual(stopped.exception.code,1);install.assert_not_called();self.assertFalse(runtime.exists())
    result=json.loads(out.getvalue());self.assertIn('invalid',result['error']);self.assertIn('dependencySetup',result)
 def test_public_copied_bootstrap_and_cli_return_json_for_null_distribution(self):
  with tempfile.TemporaryDirectory(prefix='craft 分发锁 ') as temporary:
   root=Path(temporary);skill=root/'one skill';shutil.copytree(SCRIPTS.parent,skill,ignore=shutil.ignore_patterns('__pycache__'))
   (skill/'scripts/distribution.lock.json').write_text('null');runtime=root/'runtime'
   for entry in ['bootstrap.py','cli.py']:
    args=[sys.executable,'-I','-B',str(skill/'scripts'/entry),'--runtime-home',str(runtime)]
    args+=['--','--version'] if entry=='cli.py' else ['--runtime-only']
    result=subprocess.run(args,capture_output=True,text=True,timeout=30);self.assertEqual(result.returncode,1,result.stdout+result.stderr)
    self.assertNotIn('Traceback',result.stderr);reply=json.loads(result.stdout);self.assertEqual(reply['error'],'distribution_lock_invalid')
    self.assertFalse(runtime.exists());self.assertEqual(reply['dependencySetup']['bootstrapScript'],str((skill/'scripts/bootstrap.py').resolve()))
if __name__=='__main__':unittest.main()
