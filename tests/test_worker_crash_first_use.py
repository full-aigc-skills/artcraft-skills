"""独立恢复技能的真实监督 worker 崩溃：产物存在也不得伪造停止证据或重放。"""
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
from test_scheduler_crash_first_use import read_database, tree_hash


def group_alive(pid):
    try:
        os.kill(-pid, 0)
        return True
    except ProcessLookupError:
        return False


@unittest.skipUnless(os.environ.get('CRAFT_WORKER_CRASH_FIRST_USE') == '1',
                     'requires fixed installed recover skill and public native runtimes')
class WorkerCrashFirstUseTests(unittest.TestCase):
    def test_missing_worker_stop_evidence_preserves_attempt_and_refuses_replay(self):
        original = Path(os.environ['CRAFT_INSTALLED_RECOVER_SKILL'])
        expected = tree_hash(original)
        native_pid = None
        temporary = tempfile.mkdtemp(prefix='artcraft-worker-crash-')
        try:
            root = Path(temporary).resolve()
            skill = root/'.agents/skills/artcraft-cli-recover'
            shutil.copytree(original, skill)
            runtime, project = root/'empty-runtime', root/'project'
            self.assertFalse(runtime.exists())
            campaign = json.loads((skill/'examples/brand-campaign.json').read_text())
            node = next(n for n in campaign['nodes'] if n['id'] == 'intro')
            node['dependsOn'] = []
            node.pop('inputBindings', None)
            node['payload']['assetBindings'] = []
            node['payload']['plan'] = {'document': {'name': 'Worker crash fixture', 'width': 640,
                'height': 360, 'frameRate': 24, 'duration': 4}, 'operations': [
                {'command': 'layer.newText', 'params': {'name': 'Title', 'text': 'NOVA',
                 'font': 'Arial', 'size': 48, 'position': [240, 180]}, 'as': 'title'}],
                'frames': [0, 2], 'exports': [{'format': 'mp4'}]}
            campaign.update(workflowId='installed-worker-crash', nodes=[node])
            plan = root/'plan.json'
            plan.write_text(json.dumps(campaign))
            argv = [sys.executable, '-I', '-B', str(skill/'scripts/workflow.py'), str(plan),
                '--output', str(project), '--runtime-home', str(runtime), '--owner', 'worker-crash-test',
                '--authorization', 'worker-crash-fixture']
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY',
                        'CRAFT_NATIVE_ARCHIVE_DIRECTORY', 'CRAFT_RUNTIME_HOME'):
                environment.pop(key, None)
            process = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            database = project/'tasks.sqlite'
            try:
                deadline = time.monotonic()+240
                while time.monotonic() < deadline:
                    before = read_database(database)
                    if before and before['executions'] and before['executions'][0]['status'] == 'running':
                        native_pid = before['executions'][0]['pid']
                        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,command='], text=True)
                        processes = {int(parts[0]): (int(parts[1]), parts[2])
                            for row in rows.splitlines() if len(parts := row.strip().split(None, 2)) == 3}
                        self.assertIn(native_pid, processes)
                        worker = processes[native_pid][0]
                        self.assertIn('execution_worker.ts', processes[worker][1])
                        # 只终止本测试启动链中的监督器，不用名称匹配其他进程。
                        ancestor = worker
                        for _ in range(5):
                            if ancestor == process.pid:
                                break
                            ancestor = processes[ancestor][0]
                        self.assertEqual(ancestor, process.pid)
                        os.kill(worker, signal.SIGKILL)
                        break
                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        self.fail('native task ended before worker fault injection: '+stdout+stderr)
                    time.sleep(.02)
                self.assertIsNotNone(native_pid, 'running execution not observed')
                stdout, stderr = process.communicate(timeout=30)
                self.assertNotEqual(process.returncode, 0, stdout+stderr)
                pending = json.loads(stdout)
                structured = os.environ.get('CRAFT_EXPECT_STRUCTURED_WORKFLOW_RECEIPT') == '1'
                if structured:
                    self.assertIsInstance(pending.get('workflowReceipt'), dict)
                    self.assertEqual(pending['workflowReceipt'], json.loads(pending['error']))
                pending = pending.get('workflowReceipt') or json.loads(pending['error'])
                self.assertEqual(pending['state'], 'waiting')
                artifact = Path(pending['nodes']['intro']['root'])
                # worker 停止后原生副作用仍可完成；结果存在不能代替停止证据。
                deadline = time.monotonic()+90
                while group_alive(native_pid) and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertFalse(group_alive(native_pid), 'fixture native group still running')
                self.assertTrue((artifact/'project.ecproj').is_file())
                self.assertTrue((artifact/'intro.mp4').is_file())
                files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in artifact.iterdir() if p.is_file()}
                unknown = read_database(database)
                self.assertEqual(unknown['tasks'][0]['state'], 'reconciling')
                self.assertEqual(unknown['executions'][0]['status'], 'running')
                self.assertIsNone(unknown['executions'][0]['stop_evidence_json'])
                self.assertEqual(unknown['executions'][0]['group_stopped'], 0)
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as db:
                    leases = list(db.execute('SELECT project_key, task_id, epoch FROM leases'))
                self.assertEqual(len(leases), 1)
                for _ in range(2):
                    repeated = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=180)
                    self.assertNotEqual(repeated.returncode, 0, repeated.stdout+repeated.stderr)
                    reply = json.loads(repeated.stdout)
                    if structured:
                        self.assertIsInstance(reply.get('workflowReceipt'), dict)
                        self.assertEqual(reply['workflowReceipt'], json.loads(reply['error']))
                    reply = reply.get('workflowReceipt') or json.loads(reply['error'])
                    self.assertEqual(reply['state'], 'waiting')
                after = read_database(database)
                self.assertEqual(after['tasks'][0]['attempt_id'], before['tasks'][0]['attempt_id'])
                self.assertEqual(after['executions'], unknown['executions'])
                self.assertEqual(after['budgets'], before['budgets'])
                self.assertEqual(len([e for e in after['events']
                    if json.loads(e['detail_json']).get('execution') == 'spawned']), 1)
                self.assertEqual(files, {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in artifact.iterdir() if p.is_file()})
                with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as db:
                    self.assertEqual(list(db.execute('SELECT project_key, task_id, epoch FROM leases')), leases)
                self.assertEqual(tree_hash(skill), expected)
                self.assertEqual(tree_hash(original), expected)
                evidence = {'schema': 'craft-installed-worker-crash-first-use/v1', 'result': 'PASS',
                    'skillSha256': expected, 'planSha256': hashlib.sha256(plan.read_bytes()).hexdigest(),
                    'runtimeMode': 'one installed recover skill, empty runtime, default public downloads',
                    'fault': 'SIGKILL only the owned execution supervision worker after native spawn',
                    'attemptId': after['tasks'][0]['attempt_id'], 'executionStatus': after['executions'][0]['status'],
                    'taskState': after['tasks'][0]['state'], 'stopEvidence': None,
                    'nativeGroupGoneObservedByTestOnly': True, 'artifacts': files,
                    'nativeSpawnCount': 1, 'repeatCount': 2, 'structuredWorkflowReceiptChecked': structured, 'budgetPreserved': True,
                    'projectLeasePreserved': True, 'installedSkillBytesPreserved': True,
                    'unverified': ['automatic settlement without trusted stop evidence',
                        'pre-spawn submission window', 'concurrent recoverers', 'creative acceptance']}
                if os.environ.get('CRAFT_WORKER_CRASH_EVIDENCE'):
                    with Path(os.environ['CRAFT_WORKER_CRASH_EVIDENCE']).open('x') as stream:
                        json.dump(evidence, stream, ensure_ascii=False, indent=2)
                        stream.write('\n')
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.communicate(timeout=30)
                # 清理仅涉及已验证的本测试进程组；不在仍活动时删除临时工程。
                if native_pid and group_alive(native_pid):
                    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,pgid=,command='], text=True)
                    owned = [parts[2] for row in rows.splitlines()
                        if len(parts := row.strip().split(None, 2)) == 3 and int(parts[1]) == native_pid]
                    if owned and all(str(root) in command for command in owned):
                        os.kill(-native_pid, signal.SIGTERM)
                        deadline = time.monotonic()+10
                        while group_alive(native_pid) and time.monotonic() < deadline:
                            time.sleep(.05)
                        if group_alive(native_pid):
                            os.kill(-native_pid, signal.SIGKILL)
                            time.sleep(.1)
        finally:
            # 无法证实进程组停止时保留测试工程，绝不删除活动文件。
            if not native_pid or not group_alive(native_pid):
                shutil.rmtree(temporary)


if __name__ == '__main__':
    unittest.main()
