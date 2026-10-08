"""固定安装的真实原生执行区间、同源单写及异常图拒绝；不注入延时执行器。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import unittest


def read(path):
    return json.loads(path.read_text())


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def events(database):
    with sqlite3.connect('file:' + str(database) + '?mode=ro', uri=True) as connection:
        rows = connection.execute('SELECT sequence,task_id,to_state,detail_json,occurred_at FROM events ORDER BY sequence').fetchall()
    return [{'sequence': row[0], 'taskId': row[1], 'state': row[2],
             'detail': json.loads(row[3]), 'time': row[4]} for row in rows]


def interval(rows, task_id):
    own = [row for row in rows if row['taskId'] == task_id]
    spawned = [row for row in own if row['detail'].get('execution') == 'spawned']
    stopped = [row for row in own if row['detail'].get('execution') == 'closed']
    ready = [row for row in own if row['state'] == 'review_ready']
    assert len(spawned) == len(stopped) == len(ready) == 1
    assert stopped[0]['detail']['groupStopped'] and stopped[0]['detail']['exitCode'] == 0
    return {'start': spawned[0]['sequence'], 'stop': stopped[0]['sequence'],
            'verified': ready[0]['sequence'], 'pid': spawned[0]['detail']['pid'],
            'startTime': spawned[0]['time'], 'stopTime': stopped[0]['time']}


@unittest.skipUnless(os.environ.get('CRAFT_NATIVE_SCHEDULING_ACCEPTANCE') == '1',
                     'requires fixed installed Art skill, native four-domain source deliveries and runtime')
class NativeSchedulingAcceptance(unittest.TestCase):
    def test_real_native_intervals_shared_source_serialization_and_invalid_inputs(self):
        root = Path(os.environ['CRAFT_NATIVE_SCHEDULING_ROOT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        baseline = Path(os.environ['CRAFT_NATIVE_SCHEDULING_BASELINE']).resolve()
        source = Path(os.environ['CRAFT_NATIVE_SCHEDULING_SKILL']).resolve()
        runtime = Path(os.environ['CRAFT_NATIVE_SCHEDULING_RUNTIME']).resolve()
        skill = root / '.agents/skills/artcraft-cli-execute'
        source_hashes = hashes(source)
        shutil.copytree(source, skill)
        first = read(baseline / 'first.stdout')
        original_plan = read(baseline / 'opaque-plan.json')
        baseline_rows = events(baseline / 'project/tasks.sqlite')
        baseline_intervals = {node: interval(baseline_rows, result['taskId'])
                              for node, result in first['nodes'].items()}
        dependency_checks = []
        for node in original_plan['nodes']:
            for parent in node['dependsOn']:
                self.assertLess(baseline_intervals[parent]['verified'], baseline_intervals[node['id']]['start'])
                selected = [item for item in first['nodes'][parent]['outputs']
                            if 'inputBindings' not in node or any(binding['from'] == parent and binding['assetId'] == item['assetId']
                                   for binding in node['inputBindings'])]
                self.assertTrue(selected)
                refs = [ref for item in first['nodes'][node['id']]['outputs'] for ref in item['sourceRefs']]
                for item in selected:
                    self.assertIn({key: item[key] for key in ['assetId', 'version', 'sha256']}, refs)
                dependency_checks.append({'from': parent, 'to': node['id'], 'verifiedBeforeSpawn': True})
        domains = [('__proto__', 'vectorcraft'), ('constructor', 'photocraft'),
                   ('toString', 'effectcraft'), ('hasOwnProperty', 'filmcraft')]
        originals = {name: hashes(Path(first['nodes'][name]['root'])) for name, _ in domains}
        plan = {'workflowId': 'native-scheduling', 'revision': 'v1',
                'budget': original_plan['budget'], 'nodes': []}
        for name, domain in domains:
            prior = first['nodes'][name]
            native_root = Path(prior['root'])
            artifact = prior['outputs'][0]
            template = next(node for node in original_plan['nodes'] if node['id'] == name)
            for branch in ['a', 'b']:
                node = copy.deepcopy(template)
                node.update(id=domain + '-' + branch, dependsOn=[], projectKey='shared-native-' + domain,
                            expectedRevision=artifact['nativeProjectRef']['sha256'],
                            externalInputs=[{'root': str(native_root), 'artifact': artifact}])
                node.pop('providedAssets', None)
                node.pop('inputBindings', None)
                node['payload']['sourceProject'] = {'assetId': artifact['assetId']}
                node['payload']['assetBindings'] = []
                node['payload']['plan'].pop('document')
                width = 336 if branch == 'a' else 352
                if domain == 'vectorcraft':
                    operation = {'command': 'artboard.setProps', 'params': {'index': 0, 'width': width, 'height': 256}}
                elif domain == 'photocraft':
                    operation = {'command': 'image.canvasSize', 'params': {'width': width, 'height': 400, 'anchor': 'center', 'extensionColor': 'transparent'}}
                elif domain == 'effectcraft':
                    comp = read(native_root / 'manifest.json')['bindings']['composition']['comp']
                    operation = {'command': 'comp.settings', 'params': {'comp': comp, 'width': width}}
                else:
                    operation = {'command': 'captions.setStyle', 'params': {'track': 'C1', 'font': 'Arial', 'size': 18 if branch == 'a' else 20, 'color': '#ffffff', 'background': True}}
                node['payload']['plan']['operations'] = [operation]
                plan['nodes'].append(node)
        environment = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('CRAFT_RUNTIME_HOME', 'CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY'):
            environment.pop(key, None)
        calls = []

        def run(value, directory, label, expected=0):
            path = root / (label + '.json')
            path.write_text(json.dumps(value))
            argv = [sys.executable, '-I', '-B', str(skill / 'scripts/workflow.py'), str(path),
                    '--output', str(directory), '--runtime-home', str(runtime),
                    '--owner', 'native-scheduling-owner', '--authorization', 'native-scheduling-authority']
            completed = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=600)
            (root / (label + '.stdout')).write_text(completed.stdout)
            (root / (label + '.stderr')).write_text(completed.stderr)
            calls.append({'label': label, 'exitCode': completed.returncode,
                          'stdoutSha256': hashlib.sha256(completed.stdout.encode()).hexdigest()})
            self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
            return json.loads(completed.stdout)

        project = root / 'project'
        result = run(plan, project, 'shared-source')
        self.assertEqual(result['state'], 'review_ready')
        rows = events(project / 'tasks.sqlite')
        intervals = {node: interval(rows, record['taskId']) for node, record in result['nodes'].items()}
        shared_checks = []
        for _, domain in domains:
            a, b = intervals[domain + '-a'], intervals[domain + '-b']
            self.assertLess(a['verified'], b['start'])
            shared_checks.append({'pluginId': domain, 'a': a, 'b': b, 'serializedThroughVerification': True})
        overlap = [(a, b) for a in intervals for b in intervals if a < b and a.split('-')[0] != b.split('-')[0]
                   and intervals[a]['start'] < intervals[b]['stop'] and intervals[b]['start'] < intervals[a]['stop']]
        self.assertTrue(overlap, intervals)
        for node in plan['nodes']:
            saved = read(Path(result['nodes'][node['id']]['root']) / 'native.json')
            if node['pluginId'] == 'vectorcraft':
                rect = saved['artboards'][0]['rect']
                self.assertEqual(rect['x1'] - rect['x0'], node['payload']['plan']['operations'][0]['params']['width'])
            elif node['pluginId'] == 'photocraft':
                self.assertEqual(saved['width'], node['payload']['plan']['operations'][0]['params']['width'])
            elif node['pluginId'] == 'effectcraft':
                self.assertEqual(saved['composition']['width'], node['payload']['plan']['operations'][0]['params']['width'])
        repeated = run(plan, project, 'repeat')
        self.assertEqual(repeated['state'], 'review_ready')
        self.assertEqual(events(project / 'tasks.sqlite'), rows)
        self.assertEqual(repeated['budget'], result['budget'])
        for name, record in result['nodes'].items():
            self.assertEqual(repeated['nodes'][name]['taskId'], record['taskId'])
        refused = []
        for label, reason in [('cycle', 'dependency_cycle'), ('missing', 'dependency_missing'),
                              ('input-version', 'artifact_version_conflict'), ('damaged-file', 'artifact_digest_mismatch')]:
            bad = copy.deepcopy(plan)
            bad['workflowId'] = label
            if label == 'cycle':
                bad['nodes'][0]['dependsOn'] = [bad['nodes'][1]['id']]
                bad['nodes'][1]['dependsOn'] = [bad['nodes'][0]['id']]
            elif label == 'missing':
                bad['nodes'][0]['dependsOn'] = ['absent']
            elif label == 'input-version':
                bad['nodes'][0]['externalInputs'][0]['artifact']['sha256'] = '0' * 64
            else:
                damaged = root / 'damaged-delivery'
                shutil.copytree(Path(bad['nodes'][0]['externalInputs'][0]['root']), damaged)
                (damaged / bad['nodes'][0]['externalInputs'][0]['artifact']['location']).write_bytes(b'corrupted')
                bad['nodes'][0]['externalInputs'][0]['root'] = str(damaged)
            directory = root / label
            rejected = run(bad, directory, label, 1)
            self.assertIn(reason, json.dumps(rejected))
            with sqlite3.connect('file:' + str(directory / 'tasks.sqlite') + '?mode=ro', uri=True) as database:
                for table in ['tasks', 'executions', 'leases']:
                    self.assertEqual(database.execute('SELECT count(*) FROM ' + table).fetchone()[0], 0)
            refused.append({'case': label, 'reason': reason, 'childTasks': 0, 'executions': 0, 'leases': 0})
        for name, _ in domains:
            self.assertEqual(hashes(Path(first['nodes'][name]['root'])), originals[name])
        self.assertEqual(hashes(source), source_hashes)
        self.assertEqual(hashes(skill), source_hashes)
        proof = {'schema': 'artcraft-native-scheduling-acceptance/v1', 'result': 'PASS',
                 'runtimeVersion': read(project / 'installation-receipt.json')['version'],
                 'nativeSourceChildren': 4, 'nativeRevisionChildren': 8, 'sameSourceSingleWriter': shared_checks,
                 'independentOverlappingWorkerPairs': overlap, 'verifiedDependencyHandoffs': dependency_checks,
                 'invalidGraphOrInputRefusals': refused, 'repeatedEventsUnchanged': True,
                 'sourceDeliveriesPreserved': True, 'installedAndCopiedSkillsPreserved': True,
                 'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'calls': calls,
                 'scope': 'fixed installed skill and real domain worker intervals; same logical project key and source digest; isolated editable copies; not in-place concurrent mutation or per-native-CLI-subcall tracing'}
        Path(os.environ['CRAFT_NATIVE_SCHEDULING_EVIDENCE']).write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
