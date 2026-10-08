"""固定安装的预算与取消验收：实际原生子进程、公开入口和停止顺序。"""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import unittest


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def database(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=.2)) as db:
        db.row_factory = sqlite3.Row
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {name: [dict(row) for row in db.execute('SELECT * FROM "'+name+'" ORDER BY rowid')] for name in names}


@unittest.skipUnless(os.environ.get('CRAFT_BUDGET_CANCEL_INSTALLED') == '1',
                     'requires fixed installed recover skill and verified existing runtime cache')
class BudgetCancelInstalledTests(unittest.TestCase):
    def test_native_revision_budget_manual_cancel_and_deadline(self):
        source = Path(os.environ['CRAFT_BUDGET_CANCEL_SKILL']).resolve()
        runtime = Path(os.environ['CRAFT_BUDGET_CANCEL_RUNTIME']).resolve(strict=True)
        root = Path(os.environ['CRAFT_BUDGET_CANCEL_OUTPUT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        skill = root/'.agents/skills/artcraft-cli-recover'
        baseline = inventory(source);shutil.copytree(source, skill)
        env = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('NODE_OPTIONS', 'CRAFT_RUNTIME_HOME', 'CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY'):
            env.pop(key, None)
        calls = []

        def argv(script, args):
            prefix = [sys.executable, '-I', '-B', str(skill/'scripts'/script)]
            return (prefix+['--runtime-home', str(runtime)]+list(map(str, args)) if script == 'cli.py'
                    else prefix+list(map(str, args))+['--runtime-home', str(runtime)])

        def record(label, code, out, err):
            (root/(label+'.stdout')).write_text(out);(root/(label+'.stderr')).write_text(err)
            calls.append({'label': label, 'exitCode': code,
                          'stdoutSha256': hashlib.sha256(out.encode()).hexdigest(),
                          'stderrSha256': hashlib.sha256(err.encode()).hexdigest()})
            return json.loads(out)

        def run(label, script, args, code=0):
            result = subprocess.run(argv(script, args), env=env, capture_output=True, text=True, timeout=120)
            value = record(label, result.returncode, result.stdout, result.stderr)
            self.assertEqual(result.returncode, code, result.stdout+result.stderr)
            return value

        template = json.loads((skill/'examples/brand-campaign.json').read_text())
        quota = copy.deepcopy(template);quota.update(workflowId='installed-budget-boundary', revision='v1')
        quota['nodes'] = [n for n in quota['nodes'] if n['id'] == 'logo']
        quota['budget']['maxRevisions'] = 0
        path, project = root/'quota-plan.json', root/'quota-project'
        path.write_text(json.dumps(quota))
        args = [path, '--output', project, '--owner', 'budget-owner', '--authorization', 'budget-scope']
        created = run('quota-native-create', 'workflow.py', args)
        self.assertEqual(created['state'], 'review_ready')
        node = created['nodes']['logo'];native = Path(node['root'])
        originals = inventory(native);before = database(project/'tasks.sqlite')
        quota['revision'] = 'v2';quota['nodes'][0]['payload']['plan']['document']['name'] = 'Must not execute'
        path.write_text(json.dumps(quota))
        for repeat in range(2):
            failed = run('quota-refusal-'+str(repeat), 'workflow.py', args, 1)
            self.assertEqual(failed['errorDetail'], {'code': 'budget_exhausted', 'message': 'budget_exceeded: revisions'})
            self.assertEqual(database(project/'tasks.sqlite'), before)
            self.assertEqual(inventory(native), originals)
        quota['revision'] = 'v3';quota['budget']['maxRevisions'] = 99
        path.write_text(json.dumps(quota))
        raised = run('quota-policy-raise', 'workflow.py', args, 1)
        self.assertEqual(raised['errorDetail']['code'], 'budget_policy_conflict')
        self.assertEqual(database(project/'tasks.sqlite'), before)
        status = run('quota-original-status', 'cli.py', ['--', 'status', '--database', project/'tasks.sqlite', '--task', node['taskId']])
        self.assertEqual(status, node['taskReceipt'])
        records = []
        for kind in ('manual', 'deadline'):
            with self.subTest(cancel=kind):
                plan = copy.deepcopy(template)
                intro = next(n for n in plan['nodes'] if n['id'] == 'intro')
                intro['dependsOn'] = [];intro.pop('inputBindings', None)
                intro['payload']['assetBindings'] = []
                intro['payload']['plan'] = {'document': {'name': 'Bounded cancel '+kind, 'width': 1280, 'height': 720, 'frameRate': 24, 'duration': 3600},
                                           'operations': [{'command': 'layer.newText', 'params': {'name': 'Title', 'text': 'NOVA', 'font': 'Arial', 'size': 64, 'position': [600, 360]}, 'as': 'title'}],
                                           'frames': [0], 'exports': [{'format': 'mp4'}]}
                consumer = copy.deepcopy(intro);consumer.update(id='consumer', projectKey='consumer', dependsOn=['intro'])
                consumer['payload']['plan']['document']['duration'] = 1
                plan.update(workflowId='installed-cancel-'+kind, revision='v1', nodes=[intro, consumer],
                            deadline=(datetime.now(timezone.utc)+timedelta(seconds=4 if kind == 'deadline' else 45)).isoformat(timespec='milliseconds').replace('+00:00', 'Z'))
                plan_path, output = root/(kind+'-plan.json'), root/(kind+'-project')
                plan_path.write_text(json.dumps(plan))
                workflow_args = [plan_path, '--output', output, '--owner', 'cancel-owner', '--authorization', 'cancel-scope']
                process = subprocess.Popen(argv('workflow.py', workflow_args), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                observed = None;cancel_receipt = None
                try:
                    limit = time.monotonic()+30
                    while process.poll() is None and time.monotonic() < limit:
                        try:
                            snapshot = database(output/'tasks.sqlite')
                            executions = snapshot.get('executions', [])
                        except sqlite3.OperationalError:
                            time.sleep(.02);continue
                        if executions and executions[0]['status'] == 'running':
                            processes = subprocess.check_output(['/bin/ps', '-axo', 'command='], text=True, errors='replace').splitlines()
                            if any(str(output) in row and 'effectcraft-cli' in row and ' render ' in row for row in processes):
                                observed = snapshot
                                if kind == 'manual':
                                    cancel_receipt = run('manual-request', 'cli.py', ['--', 'cancel', '--database', output/'tasks.sqlite', '--workflow', snapshot['workflow_runs'][0]['run_key']])
                                    self.assertEqual(cancel_receipt['state'], 'cancel_requested')
                                break
                        time.sleep(.02)
                    self.assertIsNotNone(observed, 'actual renderer must run before cancellation')
                    out, err = process.communicate(timeout=45)
                    result = record(kind+'-settled', process.returncode, out, err)
                    self.assertEqual(process.returncode, 0, out+err)
                    self.assertEqual(result['state'], 'cancelled')
                    self.assertNotIn('taskId', result['nodes']['consumer'])
                    after = database(output/'tasks.sqlite')
                    self.assertEqual(len(after['tasks']), 1)
                    self.assertEqual(after['tasks'][0]['state'], 'cancelled')
                    execution = after['executions'][0]
                    self.assertEqual(execution['status'], 'stopped');self.assertEqual(execution['group_stopped'], 1)
                    self.assertIn(execution['signal'], ['SIGTERM', 'SIGKILL'])
                    self.assertEqual(after['tasks'][0]['attempt_id'], observed['tasks'][0]['attempt_id'])
                    self.assertEqual(after['budget_accounts'], observed['budget_accounts'])
                    self.assertEqual(after['leases'], []);self.assertEqual(after['outcomes'], [])
                    events = after['events']
                    transitions = {state: [event['sequence'] for event in events if event['to_state'] == state] for state in ('cancel_requested', 'cancelled')}
                    closed = [event['sequence'] for event in events if json.loads(event['detail_json']).get('execution') == 'closed']
                    spawned = [event for event in events if json.loads(event['detail_json']).get('execution') == 'spawned']
                    self.assertEqual(len(closed), 1);self.assertEqual(len(spawned), 1)
                    self.assertLess(transitions['cancel_requested'][0], closed[0]);self.assertLess(closed[0], transitions['cancelled'][0])
                    files = inventory(output/'outputs')
                    repeated = run(kind+'-replay', 'workflow.py', workflow_args)
                    self.assertEqual(repeated['state'], 'cancelled')
                    final = database(output/'tasks.sqlite')
                    self.assertEqual(final['executions'], after['executions'])
                    self.assertEqual(final['budget_accounts'], after['budget_accounts'])
                    self.assertEqual(inventory(output/'outputs'), files)
                    records.append({'kind': kind, 'actualNativeRenderObserved': True, 'publicWorkflowCancelRequested': cancel_receipt is not None,
                                    'deadlineSeconds': 4 if kind == 'deadline' else 45, 'stopSignal': execution['signal'],
                                    'spawnCount': len(spawned), 'consumerTaskCount': 0, 'cancelRequestedBeforeStopBeforeCancelled': True,
                                    'attemptAndBudgetPreserved': True, 'repeatDoesNotReplay': True, 'originalFilesPreservedAfterStop': True,
                                    'leaseCountAfterStop': 0, 'outcomeCount': 0})
                finally:
                    if process.poll() is None:
                        process.terminate();process.communicate(timeout=30)
        self.assertEqual(inventory(source), baseline);self.assertEqual(inventory(skill), baseline)
        proof = {'schema': 'craft-budget-cancel-installed/v1', 'result': 'PASS', 'platform': sys.platform,
                 'installation': 'single copied fixed installed recover skill; existing verified runtime cache; no new cold-install claim',
                 'runtimeVersion': json.loads((project/'installation-receipt.json').read_text())['version'],
                 'skillFiles': baseline, 'budgetRefusals': ['budget_exhausted twice', 'budget_policy_conflict'],
                 'quotaOriginalTaskId': node['taskId'], 'quotaAllLedgerTablesPreserved': True, 'nativeOriginalFiles': originals,
                 'cancellations': records, 'calls': calls, 'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'limits': ['local zero-cost adapters only; paid-service cost allocation is separately tested using trusted-adapter fixtures',
                            'EPERM/ESRCH faults and legacy budget history require separate controlled boundary tests',
                            'not human acceptance, model dispatch, GUI or cross-platform qualification']}
        (root/'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
