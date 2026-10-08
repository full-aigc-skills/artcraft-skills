"""公开Python入口必须将升级参数交给固定运行时，不能在安装前错误拒绝。"""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class PublicUpgradeForwardingTests(unittest.TestCase):
 def test_all_ten_public_entries_forward_upgrade_to_their_pinned_runtime(self):
  for skill in sorted((ROOT/'skills').iterdir()):
   if not (skill/'SKILL.md').is_file():continue
   with self.subTest(skill=skill.name),tempfile.TemporaryDirectory() as directory:
    script=skill/'scripts/cli.py';spec=importlib.util.spec_from_file_location('upgrade_cli',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=Path(directory);home=root/'runtime';database=root/'prior.sqlite';node=root/'node';entry=root/'src/cli.ts';calls=[]
    def run(argv,**options):
     calls.append(argv)
     if len(calls)==1:
      self.assertEqual(Path(argv[3]),skill/'scripts/bootstrap.py');self.assertIn('--runtime-only',argv)
      return SimpleNamespace(returncode=0,stdout=json.dumps({'nodeExecutable':str(node),'entryPoint':str(entry)}))
     self.assertEqual(argv,[str(node),str(entry),'upgrade','--database',str(database)])
     return SimpleNamespace(returncode=0)
    with patch.object(module.sys,'argv',[str(script),'--runtime-home',str(home),'--','upgrade','--database',str(database)]),patch.object(module.subprocess,'run',side_effect=run):
     try:result=module.main()
     except SystemExit as error:result='rejected:'+str(error.code)
    self.assertEqual(result,0,'documented upgrade must reach the locked runtime through public Python CLI')
    self.assertEqual(len(calls),2);self.assertFalse(database.exists())
if __name__=='__main__':unittest.main()
