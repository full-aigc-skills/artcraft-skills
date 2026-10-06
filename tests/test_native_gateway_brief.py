"""公开 Python Brief 预检须与实际原生输出核验一致，不能提前拒绝完整网关。"""
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NativeGatewayBrief(unittest.TestCase):
 def test_valid_gateway_defers_native_output_but_keeps_authorization_and_ambiguity(self):
  for skill in (ROOT/'skills').iterdir():
   if not (skill/'SKILL.md').is_file():continue
   with self.subTest(skill=skill.name):
    spec=importlib.util.spec_from_file_location('actual_brief',skill/'scripts/brief.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    brief=json.loads((skill/'examples/brand-brief.json').read_text());brief['brand']=None;brief['subjects']=[];item=next(d for d in brief['deliverables'] if d['id']=='film');item.update(dependsOn=[],durationSeconds=1);brief['deliverables']=[item]
    plan=json.loads((skill/'examples/brand-campaign.json').read_text());node=next(n for n in plan['nodes'] if n['id']=='film');node['dependsOn']=[];plan['nodes']=[node]
    op=next(o for o in node['payload']['plan']['operations'] if o['command']=='captions.setStyle');op['params']={'command':op['command'],'params':op['params']};op['command']='native.command'
    result=m.assess(brief,plan,brief['ownerId'],brief['authorizationRef']);self.assertEqual(result['blocked'][0]['reasons'],['native_output_inspection_required']);self.assertTrue(m.pending_native_assessment(result,plan))
    with self.assertRaises(ValueError):m.assess(brief,plan,brief['ownerId'],'wrong')
    bad=copy.deepcopy(plan);bad['nodes'][0]['payload']['plan']['operations'][0]={'command':'native.command','params':{'command':'captions.setStyle','params':{},'executor':'anything'}}
    # Remove the valid gateway and change declared size; a malformed wrapper must not waive metadata checks.
    bad['nodes'][0]['payload']['plan']['operations']=[bad['nodes'][0]['payload']['plan']['operations'][0]];bad['nodes'][0]['payload']['plan']['document']['width']=1
    result=m.assess(brief,bad,brief['ownerId'],brief['authorizationRef']);self.assertIn('document_size_mismatch',result['blocked'][0]['reasons']);self.assertFalse(m.pending_native_assessment(result,bad))
