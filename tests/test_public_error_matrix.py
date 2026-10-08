"""独立技能主入口保留已知上游错误，规范化旧预算错误而不重放。"""
import importlib.util,io,json,sys,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
class PublicErrorMatrixTests(unittest.TestCase):
 def module(self,skill):
  spec=importlib.util.spec_from_file_location('error_workflow',skill/'scripts/workflow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_all_single_skills_normalize_legacy_budget_error_and_preserve_message(self):
  for skill in (ROOT/'skills').iterdir():
   m=self.module(skill)
   for dimension in ['minorUnits','externalCalls','revisions']:
    message='budget_exceeded: '+dimension;output=io.StringIO()
    with self.subTest(skill=skill.name,dimension=dimension),patch.object(sys,'argv',['workflow.py','plan.json','--output','unused','--authorization','scope']),patch.object(m,'execute',side_effect=ValueError(message)),patch.object(m.subprocess,'run',side_effect=AssertionError('replayed')),redirect_stdout(output):
     with self.assertRaises(SystemExit) as stopped:m.main()
     self.assertEqual(stopped.exception.code,1);reply=json.loads(output.getvalue());self.assertEqual(reply['error'],message);self.assertEqual(reply['errorDetail'],{'code':'budget_exhausted','message':message});self.assertNotIn('taskReceipt',reply)
 def test_all_single_skills_preserve_known_upstream_receipts_and_normalize_legacy_alias(self):
  for skill in (ROOT/'skills').iterdir():
   m=self.module(skill)
   for code in ['runtime_missing','capability_missing','revision_conflict','idempotency_conflict','outcome_unknown','artifact_invalid','budget_exhausted','authorization_required','budget_exceeded']:
    message=code+': compatibility message';receipt={'error':message,'errorDetail':{'code':code,'message':message}};output=io.StringIO()
    with self.subTest(skill=skill.name,code=code),patch.object(sys,'argv',['workflow.py','plan.json','--output','unused','--authorization','scope']),patch.object(m,'execute',side_effect=m.WorkflowFailure(receipt)),patch.object(m.subprocess,'run',side_effect=AssertionError('replayed')),redirect_stdout(output):
     with self.assertRaises(SystemExit):m.main()
     reply=json.loads(output.getvalue());self.assertEqual(reply['errorDetail'],{'code':'budget_exhausted' if code=='budget_exceeded' else code,'message':message});self.assertEqual(reply['workflowReceipt'],receipt);self.assertEqual(json.loads(reply['error']),receipt);self.assertNotIn('taskReceipt',reply)
if __name__=='__main__':unittest.main()
