"""模式目录须支持实际桌面新增命令并在安装前拒绝缺失命令。"""
import importlib.util
import unittest
import tempfile,shutil,json,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class ModeCatalogTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('mode_commands',ROOT/'skills/artcraft-use/scripts/domain_commands.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_public_mode_queries_select_complete_catalog_without_install(self):
  m=self.module()
  for mode,counts in [('headless',[666,640,755,585]),('desktop',[666,640,748,763]),('bridge',[666,640,748,763])]:
   with patch.object(m.subprocess,'run',side_effect=AssertionError('installed')):
    for domain,count in zip(m.NAMES,counts):
     rows,code=m.dispatch(m.parser().parse_args(['list','--domain',domain,'--mode',mode]));self.assertEqual(code,0);self.assertEqual(len(rows),count)
 def test_extra_and_removed_commands_use_selected_mode(self):
  m=self.module();entry=m.domain_entry('photocraft')
  for command,mode,valid in [('missing.command','headless',False),('brush.presets.rename','desktop',False),('file.new','desktop',True),('file.new','bridge',True)]:
   plan={'schema':'craft-command-plan/v1','operations':[{'command':command,'params':{}}]}
   if valid:m.validate_plan(plan,entry,{},mode)
   else:
    with self.assertRaisesRegex(ValueError,'unknown_command'):m.validate_plan(plan,entry,{},mode)
 def test_parameter_descriptions_are_mode_specific(self):
  m=self.module()
  head,_=m.dispatch(m.parser().parse_args(['describe','filmcraft','file.importImageSequence']))
  desktop,_=m.dispatch(m.parser().parse_args(['describe','filmcraft','file.importImageSequence','--mode','desktop']))
  self.assertIn('frameRate',head['params']);self.assertNotIn('frameRate',desktop['params'])
 def test_vector_ambiguous_registry_is_preserved_and_refused_before_install(self):
  m=self.module();rows,code=m.dispatch(m.parser().parse_args(['list','--domain','vectorcraft','--mode','desktop']))
  self.assertEqual(len(rows),763);self.assertEqual(len({r['id'] for r in rows}),762);self.assertEqual(len([r for r in rows if r['id']=='file.place']),2)
  with self.assertRaisesRegex(ValueError,'mode_catalog_ambiguous'):m.validate_plan({'schema':'craft-command-plan/v1','operations':[{'command':'app.quit','params':{}}]},m.domain_entry('vectorcraft'),{},'desktop')
  with self.assertRaisesRegex(ValueError,'mode_catalog_ambiguous'):m.dispatch(m.parser().parse_args(['describe','vectorcraft','file.place','--mode','desktop']))
 def test_category_query_and_missing_command_refuse_before_install(self):
  m=self.module()
  with patch.object(m.subprocess,'run',side_effect=AssertionError('installed')):
   rows,code=m.dispatch(m.parser().parse_args(['list','--domain','photocraft','--mode','desktop','--category','paint']))
   self.assertTrue(rows);self.assertTrue(all(r['id'].startswith('paint.') for r in rows));self.assertEqual(code,0)
   with tempfile.TemporaryDirectory() as td:
    plan=Path(td)/'plan.json';plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'brush.presets.rename','params':{}}]}))
    for action in ['check','run']:
     argv=[action,'photocraft',str(plan),'--mode','desktop']+(['--output',str(Path(td)/'out')] if action=='run' else [])
     with self.assertRaisesRegex(ValueError,'unknown_command'):m.dispatch(m.parser().parse_args(argv))
    self.assertFalse((Path(td)/'out').exists())
 def test_resource_and_bundle_drift_are_rejected(self):
  m=self.module();lock=json.loads((m.ROOT/'scripts/distribution.lock.json').read_text());bundle=lock['bundles']['photocraft-skills']
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'references').mkdir();source=m.ROOT/'references/mode-command-catalog.json';target=root/'references'/source.name;shutil.copyfile(source,target)
   for field in ['sha256','snapshot','desktop']:
    bad=json.loads(json.dumps(bundle))
    if field=='sha256':bad['sha256']='0'*64
    else:bad['files']['skills/photocraft-use/'+('references/native-command-snapshot.json' if field=='snapshot' else 'scripts/desktop.lock.json')]='0'*64
    with self.assertRaisesRegex(ValueError,'mode_catalog_identity'):m.M.load(root,'photocraft',bad)
   target.write_bytes(target.read_bytes()+b' ')
   with self.assertRaisesRegex(ValueError,'mode_catalog_identity'):m.M.load(root,'photocraft',bundle)
if __name__=='__main__':unittest.main()
