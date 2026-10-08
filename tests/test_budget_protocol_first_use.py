"""单技能真实首次使用：预算拒绝规范错误码、原任务与产物保全。"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        return {name:db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall() for name in ['tasks','executions','leases','workflow_runs','workflow_nodes','budget_accounts','workflow_budget_links','events']}

@unittest.skipUnless(os.environ.get('CRAFT_BUDGET_PROTOCOL_FIRST_USE')=='1','requires retained output and public pinned native runtime')
class BudgetProtocolFirstUseTests(unittest.TestCase):
    def test_revision_exhaustion_preserves_original_task_and_has_canonical_error(self):
        root=Path(os.environ['CRAFT_BUDGET_PROTOCOL_OUTPUT']).resolve();root.mkdir(parents=True,exist_ok=False)
        source=Path(os.environ.get('CRAFT_BUDGET_PROTOCOL_SKILL',ROOT/'skills/artcraft-cli-execute'))
        skill=root/'.agents/skills/artcraft-cli-execute';shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
        runtime,project=root/'fresh-runtime',root/'project';self.assertFalse(runtime.exists())
        env=dict(os.environ,PATH='/usr/bin:/bin')
        for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):env.pop(key,None)
        calls=[]
        def run(script,*args,code=0):
            result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args)],env=env,capture_output=True,text=True,timeout=600)
            log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr)
            calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(log)})
            self.assertEqual(result.returncode,code,result.stdout+result.stderr);return json.loads(result.stdout)
        plan=json.loads((skill/'examples/brand-campaign.json').read_text());plan['nodes']=[n for n in plan['nodes'] if n['id']=='logo'];plan['budget']['maxRevisions']=0
        path=root/'plan.json';path.write_text(json.dumps(plan))
        args=[path,'--output',project,'--runtime-home',runtime,'--owner','budget-owner','--authorization','budget-scope']
        first=run('workflow.py',*args);self.assertEqual(first['state'],'review_ready')
        node=first['nodes']['logo'];receipt=node['taskReceipt'];native=Path(node['root'])
        files={str(p.relative_to(native)):sha(p) for p in native.rglob('*') if p.is_file()};before=snapshot(project/'tasks.sqlite')
        self.assertEqual(len(before['tasks']),1);self.assertEqual(len(before['executions']),1);self.assertFalse(before['leases'])
        plan['revision']='v2';plan['nodes'][0]['payload']['plan']['document']['name']='Changed budget-blocked design';path.write_text(json.dumps(plan))
        refused=[]
        for repeat in range(2):
            reply=run('workflow.py',*args,code=1);refused.append(reply)
            self.assertEqual(reply['errorDetail'],{'code':'budget_exhausted','message':'budget_exceeded: revisions'})
            self.assertEqual(reply['workflowReceipt']['error'],'budget_exceeded: revisions')
            self.assertEqual(reply['workflowReceipt']['errorDetail'],reply['errorDetail'])
            self.assertNotIn('taskReceipt',reply);self.assertNotIn('nodes',reply['workflowReceipt'])
            self.assertEqual(snapshot(project/'tasks.sqlite'),before)
            self.assertEqual(files,{str(p.relative_to(native)):sha(p) for p in native.rglob('*') if p.is_file()})
        current=run('cli.py','--runtime-home',runtime,'--','status','--database',project/'tasks.sqlite','--task',receipt['taskId'])
        self.assertEqual(current,receipt);self.assertFalse(any(skill.rglob('*.pyc')))
        proof={'schema':'craft-budget-protocol-first-use/v1','result':'PASS','runtimeVersion':json.loads((project/'installation-receipt.json').read_text())['version'],'taskReceipt':receipt,'canonicalError':refused[0]['errorDetail'],'legacyError':refused[0]['workflowReceipt']['error'],'repeatedRefusalStable':True,'allLedgerTablesUnchanged':list(before),'originalNativeFiles':files,'calls':calls,'scope':'single copied skill cold public runtime; native Vector create, two revision-cap refusals, durable task/attempt and ledger/native preservation; not all budget/creative/full protocol acceptance'}
        (root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':unittest.main()
