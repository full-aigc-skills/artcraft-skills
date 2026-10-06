"""固定安装的恢复技能：真实调度器 SIGKILL 后接管同一原生任务。"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hash(directory):
    result = hashlib.sha256()
    for path in sorted(p for p in directory.rglob('*') if p.is_file()):
        result.update(path.relative_to(directory).as_posix().encode()+b'\0')
        result.update(digest(path).encode()+b'\n')
    return result.hexdigest()


def read_database(path):
    if not path.exists():
        return None
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=.2)) as db:
            db.row_factory = sqlite3.Row
            tasks = [dict(row) for row in db.execute('SELECT * FROM tasks')]
            executions = [dict(row) for row in db.execute('SELECT * FROM executions')]
            budgets = [dict(row) for row in db.execute('SELECT * FROM budget_accounts')]
            events = [dict(row) for row in db.execute('SELECT * FROM events')]
            return {'tasks':tasks,'executions':executions,'budgets':budgets,'events':events}
    except sqlite3.OperationalError:
        return None


@unittest.skipUnless(os.environ.get('CRAFT_SCHEDULER_CRASH_FIRST_USE') == '1', 'requires fixed installed recover skill and public runtimes')
class SchedulerCrashFirstUseTests(unittest.TestCase):
    def test_installed_recover_skill_reconciles_same_native_attempt(self):
        original = Path(os.environ['CRAFT_INSTALLED_RECOVER_SKILL'])
        expected_hash = tree_hash(original)
        with tempfile.TemporaryDirectory(prefix='artcraft-scheduler-crash-') as temporary:
            root = Path(temporary).resolve()
            skill = root/'.agents/skills/artcraft-cli-recover'
            shutil.copytree(original, skill)
            runtime, project = root/'empty-runtime', root/'project'
            self.assertFalse(runtime.exists())
            campaign = json.loads((skill/'examples/brand-campaign.json').read_text())
            node = next(node for node in campaign['nodes'] if node['id']=='intro')
            node['dependsOn']=[]
            node.pop('inputBindings', None)
            node['payload']['assetBindings']=[]
            effect_plan = {'document':{'name':'Crash recovery intro','width':640,'height':360,'frameRate':24,'duration':4},'operations':[{'command':'layer.newText','params':{'name':'Title','text':'NOVA','font':'Arial','size':48,'position':[240,180]},'as':'title'}],'frames':[0,2],'exports':[{'format':'mp4'}]}
            node['payload']['plan']=effect_plan
            campaign.update(workflowId='installed-scheduler-crash',nodes=[node])
            plan = root/'plan.json';plan.write_text(json.dumps(campaign))
            argv=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(plan),'--output',str(project),'--runtime-home',str(runtime),'--owner','crash-test','--authorization','crash-test-scope']
            environment=dict(os.environ, PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):
                environment.pop(key,None)
            process=subprocess.Popen(argv,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            database=project/'tasks.sqlite'
            deadline=time.monotonic()+240
            killed=False
            try:
                while time.monotonic()<deadline:
                    before=read_database(database)
                    if before and before['executions'] and before['executions'][0]['status']=='running':
                        processes=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,command='],text=True)
                        candidates=[]
                        for line in processes.splitlines():
                            values=line.strip().split(None,2)
                            if len(values)==3 and int(values[1])==process.pid and ' --database '+str(database)+' ' in values[2] and ' run ' in values[2]:
                                candidates.append(int(values[0]))
                        self.assertEqual(len(candidates),1,'owned scheduler child not uniquely identified')
                        os.kill(candidates[0],signal.SIGKILL)
                        killed=True
                        break
                    if process.poll() is not None:
                        stdout,stderr=process.communicate()
                        self.fail('scheduler finished before fault injection: '+stdout+stderr)
                    time.sleep(.02)
                self.assertTrue(killed,'running task not observed')
                stdout,stderr=process.communicate(timeout=30)
                self.assertNotEqual(process.returncode,0)
                # 调度器停止不代表原生任务停止；等待独立监督器的持久化证据。
                deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    stopped=read_database(database)
                    if stopped and stopped['executions'][0]['status']=='stopped':
                        break
                    time.sleep(.05)
                self.assertEqual(stopped['executions'][0]['status'],'stopped')
                self.assertEqual(stopped['executions'][0]['group_stopped'],1)
                self.assertEqual(stopped['executions'][0]['exit_code'],0)
                old=before['executions'][0]
                for field in ('task_id','attempt_id','epoch','token','command_hash','pid'):
                    self.assertEqual(old[field],stopped['executions'][0][field])
                result=subprocess.run(argv,env=environment,capture_output=True,text=True,timeout=180)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                resumed=json.loads(result.stdout)
                self.assertEqual(resumed['state'],'review_ready')
                after=read_database(database)
                self.assertEqual(len(after['tasks']),1)
                self.assertEqual(after['tasks'][0]['attempt_id'],before['tasks'][0]['attempt_id'])
                self.assertEqual(before['budgets'],after['budgets'])
                self.assertEqual(len([event for event in after['events'] if json.loads(event['detail_json']).get('execution')=='spawned']),1)
                artifact_root=Path(resumed['nodes']['intro']['root'])
                files={p.name:digest(p) for p in artifact_root.iterdir() if p.is_file()}
                video=artifact_root/'intro.mp4'
                streams=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(video)]))['streams']
                self.assertEqual((streams[0]['width'],streams[0]['height'],streams[0]['nb_read_frames']),(640,360,'96'))
                repeated=subprocess.run(argv,env=environment,capture_output=True,text=True,timeout=180)
                self.assertEqual(repeated.returncode,0,repeated.stdout+repeated.stderr)
                replay=json.loads(repeated.stdout)
                self.assertEqual(replay['nodes']['intro']['taskId'],resumed['nodes']['intro']['taskId'])
                self.assertEqual(replay['nodes']['intro']['status'],'reused')
                self.assertEqual(files,{p.name:digest(p) for p in artifact_root.iterdir() if p.is_file()})
                self.assertEqual(tree_hash(skill),expected_hash)
                self.assertEqual(tree_hash(original),expected_hash)
                evidence={'schema':'craft-installed-scheduler-crash-first-use/v1','result':'passed','skillSha256':expected_hash,'planSha256':digest(plan),'runtimeMode':'single installed recover skill; empty runtime; default public installation','injectedFault':'SIGKILL only the owned ArtCraft scheduler child; independent worker remains','attemptId':old['attempt_id'],'epoch':old['epoch'],'commandSha256':old['command_hash'],'nativeSpawnCount':1,'budgetPreserved':True,'decodedVideo':{'width':640,'height':360,'frames':96,'frameRate':24},'artifactFiles':files,'sameAttemptRecovered':True,'repeatReusesTask':True,'installedSkillBytesPreserved':True,'unverified':['worker itself crashes','unknown submission window','concurrent recoverers','GUI/model dispatch','creative acceptance']}
                if os.environ.get('CRAFT_SCHEDULER_CRASH_EVIDENCE'):
                    with Path(os.environ['CRAFT_SCHEDULER_CRASH_EVIDENCE']).open('x') as output:
                        json.dump(evidence,output,ensure_ascii=False,indent=2);output.write('\n')
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.communicate(timeout=30)


if __name__=='__main__':unittest.main()
