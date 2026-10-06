"""单独安装恢复技能：实际期限停止原生渲染，阻止依赖启动与重放。"""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import copy
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


@unittest.skipUnless(os.environ.get('CRAFT_DEADLINE_FIRST_USE') == '1', 'requires installed recover skill and public native runtimes')
class DeadlineFirstUseTests(unittest.TestCase):
    def test_deadline_cancels_live_render_and_never_starts_consumer(self):
        original=Path(os.environ['CRAFT_INSTALLED_RECOVER_SKILL']);expected_hash=tree_hash(original)
        with tempfile.TemporaryDirectory(prefix='artcraft-deadline-') as temporary:
            root=Path(temporary).resolve();skill=root/'.agents/skills/artcraft-cli-recover'
            shutil.copytree(original,skill)
            runtime,project=root/'empty-runtime',root/'project';self.assertFalse(runtime.exists())
            environment=dict(os.environ,PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
            setup=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/bootstrap.py'),'--runtime-home',str(runtime),'--plugin','effectcraft'],env=environment,capture_output=True,text=True,timeout=240)
            self.assertEqual(setup.returncode,0,setup.stdout+setup.stderr)
            installation=json.loads(setup.stdout)
            plan=json.loads((skill/'examples/brand-campaign.json').read_text())
            node=next(node for node in plan['nodes'] if node['id']=='intro')
            node['dependsOn']=[];node.pop('inputBindings',None);node['payload']['assetBindings']=[]
            node['payload']['plan']={'document':{'name':'Deadline intro','width':1280,'height':720,'frameRate':24,'duration':3600},'operations':[{'command':'layer.newText','params':{'name':'Title','text':'NOVA','font':'Arial','size':64,'position':[600,360]},'as':'title'}],'frames':[0],'exports':[{'format':'mp4'}]}
            consumer=copy.deepcopy(node);consumer.update(id='consumer',projectKey='consumer-project',dependsOn=['intro']);consumer['payload']['plan']['document'].update(name='Must not launch',duration=1)
            deadline=(datetime.now(timezone.utc)+timedelta(seconds=4)).isoformat(timespec='milliseconds').replace('+00:00','Z')
            plan.update(workflowId='installed-deadline',deadline=deadline,nodes=[node,consumer])
            plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan))
            argv=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(plan_path),'--output',str(project),'--runtime-home',str(runtime),'--owner','deadline-test','--authorization','deadline-test-scope']
            process=subprocess.Popen(argv,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            database=project/'tasks.sqlite';observed=False;before=None;started=time.monotonic()
            try:
                while process.poll() is None and time.monotonic()-started<30:
                    snapshot=read_database(database)
                    if snapshot and snapshot['executions'] and snapshot['executions'][0]['status']=='running':
                        rows=subprocess.check_output(['/bin/ps','-axo','command='],text=True,errors='replace').splitlines()
                        if any(str(project) in row and 'effectcraft-cli' in row and ' render ' in row for row in rows):
                            observed=True
                            if before is None:before=snapshot
                    time.sleep(.02)
                out,err=process.communicate(timeout=30)
                self.assertEqual(process.returncode,0,out+err)
                result=json.loads(out);self.assertTrue(observed,'actual renderer must run before deadline')
                self.assertEqual(result['state'],'cancelled')
                self.assertEqual(result['nodes']['intro']['status'],'cancelled')
                self.assertEqual(result['nodes']['consumer']['status'],'cancelled')
                self.assertNotIn('taskId',result['nodes']['consumer'])
                after=read_database(database);self.assertEqual(len(after['tasks']),1);self.assertEqual(after['tasks'][0]['state'],'cancelled')
                execution=after['executions'][0];self.assertEqual(execution['status'],'stopped');self.assertEqual(execution['group_stopped'],1)
                self.assertIn(execution['signal'],['SIGTERM','SIGKILL'])
                self.assertEqual(before['budgets'],after['budgets']);self.assertEqual(before['tasks'][0]['attempt_id'],after['tasks'][0]['attempt_id'])
                events=after['events'];spawn=[e for e in events if json.loads(e['detail_json']).get('execution')=='spawned'];closed=[e for e in events if json.loads(e['detail_json']).get('execution')=='closed'];settled=[e for e in events if e['to_state']=='cancelled']
                self.assertEqual((len(spawn),len(closed),len(settled)),(1,1,1));self.assertLess(closed[0]['sequence'],settled[0]['sequence'])
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM leases').fetchone()[0],0)
                    self.assertEqual(db.execute('SELECT count(*) FROM outcomes').fetchone()[0],0)
                repeated=subprocess.run(argv,env=environment,capture_output=True,text=True,timeout=90)
                self.assertEqual(repeated.returncode,0,repeated.stdout+repeated.stderr);self.assertEqual(json.loads(repeated.stdout)['state'],'cancelled')
                final=read_database(database);self.assertEqual(final['executions'],after['executions']);self.assertEqual(final['budgets'],after['budgets'])
                self.assertEqual(tree_hash(skill),expected_hash);self.assertEqual(tree_hash(original),expected_hash)
                evidence={'schema':'craft-installed-deadline-first-use/v1','result':'passed','skillSha256':expected_hash,'planSha256':digest(plan_path),'runtimeVersion':installation['version'],'firstUse':'single copied recover skill; empty runtime default-public bootstrap selects EffectCraft; same runtime reused for bounded-deadline workflow','relativeDeadlineSeconds':4,'actualNativeRenderObserved':True,'terminationSignal':execution['signal'],'nativeSpawnCount':1,'consumerTaskCount':0,'stopBeforeCancelled':True,'leaseCountAfterStop':0,'publishedOutcomeCount':0,'sameAttempt':True,'budgetPreserved':True,'repeatDoesNotReplay':True,'installedSkillBytesPreserved':True,'unverified':['installation time within four-second deadline','worker crash','model dispatch','GUI','creative acceptance']}
                if os.environ.get('CRAFT_DEADLINE_EVIDENCE'):
                    with Path(os.environ['CRAFT_DEADLINE_EVIDENCE']).open('x') as output:json.dump(evidence,output,ensure_ascii=False,indent=2);output.write('\n')
            finally:
                if process.poll() is None:process.terminate();process.communicate(timeout=30)


if __name__=='__main__':unittest.main()
