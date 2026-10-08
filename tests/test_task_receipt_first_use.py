"""单技能公开首用的持久任务回执、复用与拒绝边界。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

@unittest.skipUnless(os.environ.get('CRAFT_RECEIPT_FIRST_USE') == '1', 'requires explicit retained output and public native downloads')
class TaskReceiptFirstUseTests(unittest.TestCase):
    def test_cold_single_skill_receipt_reuse_and_rejections(self):
        root = Path(os.environ['CRAFT_RECEIPT_OUTPUT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        source = Path(os.environ.get('CRAFT_RECEIPT_SKILL', ROOT/'skills/artcraft-cli-execute'))
        skill = root/'.agents/skills/artcraft-cli-execute'
        shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
        runtime, project = root/'fresh-runtime', root/'project'
        environment = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):
            environment.pop(key, None)
        calls = []
        def run(script, *args, code=0):
            result = subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args)], env=environment, capture_output=True, text=True, timeout=600)
            log = root/('call-%02d.log' % len(calls)); log.write_text(result.stdout+result.stderr)
            calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(log)})
            self.assertEqual(result.returncode,code,result.stdout+result.stderr)
            return json.loads(result.stdout)
        path = root/'plan.json'; path.write_text('{}')
        args = [path,'--output',project,'--runtime-home',runtime,'--owner','receipt-owner','--authorization','receipt-scope']
        invalid = run('workflow.py',*args,code=1)
        self.assertEqual(invalid['errorDetail']['code'],'workflow_plan_invalid')
        self.assertNotIn('workflowReceipt',invalid); self.assertNotIn('taskReceipt',invalid)
        self.assertFalse(runtime.exists()); self.assertFalse((project/'tasks.sqlite').exists())
        plan = json.loads((skill/'examples/brand-campaign.json').read_text())
        plan['nodes'] = [n for n in plan['nodes'] if n['id']=='logo']
        path.write_text(json.dumps(plan))
        first = run('workflow.py',*args)
        self.assertEqual(first['state'],'review_ready')
        node = first['nodes']['logo']; receipt = node['taskReceipt']
        self.assertEqual(receipt['taskId'],node['taskId']); self.assertTrue(receipt['attemptId'])
        self.assertEqual(receipt['state'],'review_ready'); self.assertIsNone(receipt['error'])
        self.assertEqual(receipt['outputRefs'],node['outputs'])
        self.assertEqual(receipt['runtimeIdentity']['pluginId'],'vectorcraft')
        for field in ('outputRefs','evidenceRefs'):self.assertIsInstance(receipt[field],list)
        native = Path(node['root']); original = {str(p.relative_to(native)):sha(p) for p in native.rglob('*') if p.is_file()}
        def status():
            return run('cli.py','--runtime-home',runtime,'--','status','--database',project/'tasks.sqlite','--task',node['taskId'])
        self.assertEqual(status(),receipt)
        repeated = run('workflow.py',*args)
        self.assertEqual(repeated['nodes']['logo']['status'],'reused')
        self.assertEqual(repeated['nodes']['logo']['taskReceipt'],receipt)
        self.assertEqual(repeated['budget'],first['budget'])
        self.assertEqual(status(),receipt)
        plan['nodes'][0]['payload']['plan']['document']['name']='Conflicting same revision'
        path.write_text(json.dumps(plan))
        rejected = run('workflow.py',*args,code=1)
        self.assertEqual(rejected['errorDetail']['code'],'workflow_revision_conflict')
        self.assertNotIn('workflowReceipt',rejected); self.assertNotIn('taskReceipt',rejected)
        self.assertEqual(status(),receipt)
        self.assertEqual(original,{str(p.relative_to(native)):sha(p) for p in native.rglob('*') if p.is_file()})
        # 真实上游 CLI 在登记前拒绝所有者冲突；Python 包装必须保留其结构化错误。
        plan['ownerId']='different-owner';path.write_text(json.dumps(plan))
        unauthorized_project=root/'unauthorized-project'
        unauthorized=run('workflow.py',path,'--output',unauthorized_project,'--runtime-home',runtime,
                         '--owner','receipt-owner','--authorization','receipt-scope',code=1)
        self.assertEqual(unauthorized['errorDetail']['code'],'authorization_scope_mismatch')
        self.assertEqual(unauthorized['errorDetail'],unauthorized['workflowReceipt']['errorDetail'])
        self.assertNotIn('taskReceipt',unauthorized)
        self.assertFalse((unauthorized_project/'tasks.sqlite').exists())
        self.assertEqual(status(),receipt)
        self.assertFalse(any(skill.rglob('*.pyc')))
        self.assertEqual(set(json.loads((project/'installation-receipt.json').read_text())['skills']),{'vectorcraft'})
        proof={'schema':'craft-native-task-receipt-first-use/v1','result':'PASS','receipt':receipt,'initialRunKey':first['runKey'],'reusedRunKey':repeated['runKey'],'invalidInput':invalid,'revisionConflict':rejected,'authorizationConflict':unauthorized,'oldNativeFiles':original,'calls':calls,'scope':'single copied skill; cold public runtime, Vector native creation, durable receipt query, replay without new attempt, invalid-input/same-revision/authorization refusal; not full protocol or creative acceptance'}
        (root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__':unittest.main()
