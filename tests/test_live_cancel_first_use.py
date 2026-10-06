"""固定恢复技能首次使用：在真实原生渲染中取消且等待停止证据。"""
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from test_scheduler_crash_first_use import digest, tree_hash, read_database

sys.dont_write_bytecode = True


@unittest.skipUnless(os.environ.get('CRAFT_LIVE_CANCEL_FIRST_USE') == '1', 'requires installed recover skill and public native runtimes')
class LiveCancelFirstUseTests(unittest.TestCase):
    def test_live_native_render_cancel_waits_for_stop_and_does_not_replay(self):
        original=Path(os.environ['CRAFT_INSTALLED_RECOVER_SKILL'])
        expected_hash=tree_hash(original)
        with tempfile.TemporaryDirectory(prefix='artcraft-live-cancel-') as temporary:
            root=Path(temporary).resolve();skill=root/'.agents/skills/artcraft-cli-recover'
            shutil.copytree(original,skill)
            runtime,project=root/'empty-runtime',root/'project'
            self.assertFalse(runtime.exists())
            plan=json.loads((skill/'examples/brand-campaign.json').read_text())
            node=next(node for node in plan['nodes'] if node['id']=='intro')
            node['dependsOn']=[];node.pop('inputBindings',None);node['payload']['assetBindings']=[]
            node['payload']['plan']={'document':{'name':'Live cancel intro','width':1280,'height':720,'frameRate':24,'duration':30},'operations':[{'command':'layer.newText','params':{'name':'Title','text':'NOVA','font':'Arial','size':64,'position':[600,360]},'as':'title'}],'frames':[0],'exports':[{'format':'mp4'}]}
            plan.update(workflowId='installed-live-cancel',nodes=[node])
            plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan))
            argv=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(plan_path),'--output',str(project),'--runtime-home',str(runtime),'--owner','cancel-test','--authorization','cancel-test-scope']
            environment=dict(os.environ,PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
            process=subprocess.Popen(argv,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            database=project/'tasks.sqlite';cancelled=False
            try:
                deadline=time.monotonic()+240
                while time.monotonic()<deadline:
                    before=read_database(database)
                    if before and before['executions'] and before['executions'][0]['status']=='running':
                        rows=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,command='],text=True,errors='replace').splitlines()
                        rendering=[]
                        for row in rows:
                            fields=row.strip().split(None,2)
                            if len(fields)==3 and str(project) in fields[2] and 'effectcraft-cli' in fields[2] and ' render ' in fields[2]:rendering.append(int(fields[0]))
                        if rendering:
                            self.assertEqual(len(rendering),1,'owned native renderer not uniquely identified')
                            with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
                                run_key=db.execute('SELECT run_key FROM workflow_runs').fetchone()[0]
                                self.assertEqual(db.execute('SELECT count(*) FROM leases').fetchone()[0],1)
                            cancel_args=[sys.executable,'-I','-B',str(skill/'scripts/cli.py'),'--runtime-home',str(runtime),'--','cancel','--database',str(database),'--workflow',run_key]
                            cancellation=subprocess.run(cancel_args,env=environment,capture_output=True,text=True,timeout=30)
                            self.assertEqual(cancellation.returncode,0,cancellation.stdout+cancellation.stderr)
                            self.assertEqual(json.loads(cancellation.stdout)['state'],'cancel_requested')
                            cancelled=True;break
                    if process.poll() is not None:
                        out,err=process.communicate();self.fail('native render finished before live cancellation: '+out+err)
                    time.sleep(.02)
                self.assertTrue(cancelled,'live native render not observed')
                out,err=process.communicate(timeout=60)
                self.assertEqual(process.returncode,0,out+err)
                receipt=json.loads(out)
                if receipt['state']!='cancelled':
                    current=read_database(database)
                    group=current['executions'][0]['pid']
                    process_rows=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,pgid=,stat=,comm='],text=True,errors='replace')
                    members=[]
                    for row in process_rows.splitlines():
                        fields=row.strip().split(None,4)
                        if len(fields)==5 and int(fields[2])==group:members.append({'pid':int(fields[0]),'ppid':int(fields[1]),'pgid':int(fields[2]),'state':fields[3],'command':Path(fields[4]).name})
                    debug={'state':receipt['state'],'taskState':current['tasks'][0]['state'],'execution':{key:current['executions'][0][key] for key in ('status','pid','exit_code','signal','group_stopped','stop_evidence_json')},'members':members}
                    Path('/tmp/artcraft-live-cancel-debug-20261006.json').write_text(json.dumps(debug,indent=2)+'\n')
                self.assertEqual(receipt['state'],'cancelled')
                after=read_database(database);execution=after['executions'][0]
                self.assertEqual(after['tasks'][0]['state'],'cancelled')
                self.assertEqual(execution['status'],'stopped');self.assertEqual(execution['group_stopped'],1)
                self.assertIn(execution['signal'],['SIGTERM','SIGKILL'])
                self.assertEqual(before['budgets'],after['budgets'])
                self.assertEqual(before['tasks'][0]['attempt_id'],after['tasks'][0]['attempt_id'])
                events=after['events']
                spawn=[e for e in events if json.loads(e['detail_json']).get('execution')=='spawned']
                closed=[e for e in events if json.loads(e['detail_json']).get('execution')=='closed']
                settled=[e for e in events if e['to_state']=='cancelled']
                self.assertEqual(len(spawn),1);self.assertEqual(len(closed),1);self.assertEqual(len(settled),1)
                self.assertTrue(spawn[0]['sequence']<closed[0]['sequence']<settled[0]['sequence'])
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM leases').fetchone()[0],0)
                    self.assertEqual(db.execute('SELECT count(*) FROM outcomes').fetchone()[0],0)
                repeated=subprocess.run(argv,env=environment,capture_output=True,text=True,timeout=90)
                self.assertEqual(repeated.returncode,0,repeated.stdout+repeated.stderr)
                self.assertEqual(json.loads(repeated.stdout)['state'],'cancelled')
                final=read_database(database)
                self.assertEqual(final['executions'],after['executions']);self.assertEqual(final['budgets'],after['budgets'])
                self.assertEqual(tree_hash(skill),expected_hash);self.assertEqual(tree_hash(original),expected_hash)
                evidence={'schema':'craft-installed-live-cancel-first-use/v1','result':'passed','skillSha256':expected_hash,'planSha256':digest(plan_path),'runtimeMode':'single installed recover skill; empty runtime; default public installation','nativeRenderObservedBeforeCancel':True,'requestedVideo':{'width':1280,'height':720,'frameRate':24,'durationSeconds':30},'nativeSpawnCount':1,'terminationSignal':execution['signal'],'eventOrder':['native spawned','native close and group stopped','task cancelled'],'leaseReleasedAfterStop':True,'publishedOutcomeCount':0,'sameAttempt':True,'budgetPreserved':True,'repeatedWorkflowDoesNotReplay':True,'installedSkillBytesPreserved':True,'unverified':['deadline expiry','worker crash','GUI/model dispatch','creative acceptance']}
                if os.environ.get('CRAFT_LIVE_CANCEL_EVIDENCE'):
                    with Path(os.environ['CRAFT_LIVE_CANCEL_EVIDENCE']).open('x') as output:json.dump(evidence,output,ensure_ascii=False,indent=2);output.write('\n')
            finally:
                if process.poll() is None:
                    process.terminate();process.communicate(timeout=30)


if __name__=='__main__':unittest.main()
