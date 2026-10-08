"""固定安装的公开任务绑定验收；已有缓存与GUI缺口明确分开记录。"""
from contextlib import closing
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import sys
import unittest
import wave


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}


def project_state(root):
    # SQLite物理日志可因关闭连接而变化；逐表内容是任务状态的比较对象。
    files = {name: digest for name, digest in inventory(root).items()
             if name not in ('tasks.sqlite', 'tasks.sqlite-wal', 'tasks.sqlite-shm')}
    with closing(sqlite3.connect((root/'tasks.sqlite').as_uri()+'?mode=ro', uri=True)) as db:
        names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        tables = {name: db.execute('SELECT * FROM "'+name+'" ORDER BY rowid').fetchall() for name in names}
    return {'files': files, 'tables': tables}


@unittest.skipUnless(os.environ.get('CRAFT_VERSION_BINDING_INSTALLED') == '1',
                     'requires fixed installed Art skill, verified existing runtime and alternate Python')
class VersionBindingInstalledTests(unittest.TestCase):
    def test_frozen_metadata_authorization_and_native_source_boundaries(self):
        source = Path(os.environ['CRAFT_VERSION_BINDING_SKILL']).resolve()
        runtime = Path(os.environ['CRAFT_VERSION_BINDING_RUNTIME']).resolve(strict=True)
        alternate = Path(os.environ['CRAFT_VERSION_BINDING_ALTERNATE_PYTHON']).absolute()
        root = Path(os.environ['CRAFT_VERSION_BINDING_OUTPUT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        skill = root/'.agents/skills/artcraft-cli-revise'
        baseline = inventory(source)
        shutil.copytree(source, skill)
        self.assertEqual(inventory(skill), baseline)
        self.assertNotEqual(sha(Path(sys.executable)), sha(alternate))
        env = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY', 'CRAFT_RUNTIME_HOME', 'NODE_OPTIONS'):
            env.pop(key, None)
        calls = []

        def run(label, script, args, code=0, python=sys.executable):
            argv = [str(python), '-I', '-B', str(skill/'scripts'/script), *map(str, args)]
            if script == 'cli.py':
                argv = [str(python), '-I', '-B', str(skill/'scripts'/script), '--runtime-home', str(runtime), *map(str, args)]
            else:
                argv += ['--runtime-home', str(runtime)]
            reply = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=600)
            (root/(label+'.stdout')).write_text(reply.stdout)
            (root/(label+'.stderr')).write_text(reply.stderr)
            calls.append({'label': label, 'exitCode': reply.returncode,
                          'stdoutSha256': hashlib.sha256(reply.stdout.encode()).hexdigest(),
                          'stderrSha256': hashlib.sha256(reply.stderr.encode()).hexdigest()})
            self.assertEqual(reply.returncode, code, reply.stdout+reply.stderr)
            return json.loads(reply.stdout)

        voice = root/'voice.wav'
        with wave.open(str(voice), 'wb') as output:
            output.setparams((1, 2, 48000, 48000, 'NONE', 'not compressed'))
            output.writeframes(struct.pack('<h', 1000)*48000)
        original_voice = voice.read_bytes()
        value = json.loads((skill/'examples/brand-campaign.json').read_text())
        value.update(workflowId='installed-version-binding', revision='v1')
        value['budget']['maxRevisions'] = 4
        path, project = root/'plan.json', root/'project'
        path.write_text(json.dumps(value))
        owner, scope = 'binding-owner', 'binding-scope-one'
        args = [path, '--output', project, '--owner', owner, '--authorization', scope, '--asset', 'voice='+str(voice)]
        first = run('create', 'workflow.py', args)
        self.assertEqual(first['state'], 'review_ready')
        self.assertEqual(len(first['nodes']), 4)
        original = {name: inventory(Path(node['root'])) for name, node in first['nodes'].items()}
        before = project_state(project)
        refusals = []
        for fault in ('plan', 'authorization', 'input', 'launcher'):
            with self.subTest(frozen=fault):
                changed = copy.deepcopy(value)
                actual_args = list(args)
                python = sys.executable
                if fault == 'plan':
                    changed['nodes'][0]['payload']['plan']['document']['name'] = 'Conflicting frozen design'
                elif fault == 'authorization':
                    actual_args[actual_args.index('--authorization')+1] = 'binding-scope-two'
                elif fault == 'input':
                    voice.write_bytes(original_voice[:-2]+struct.pack('<h', 1200))
                elif fault == 'launcher':
                    python = alternate
                path.write_text(json.dumps(changed))
                try:
                    refused = run('frozen-'+fault, 'workflow.py', actual_args, code=1, python=python)
                    self.assertEqual(refused['errorDetail']['code'], 'workflow_revision_conflict')
                    self.assertNotIn('workflowReceipt', refused)
                    self.assertEqual(project_state(project), before)
                    refusals.append({'fault': fault, 'error': refused['errorDetail']['code'],
                                     'allProjectFilesAndLedgerTablesPreserved': True})
                finally:
                    voice.write_bytes(original_voice)
                    path.write_text(json.dumps(value))
        replay = run('same-scope-replay', 'workflow.py', args)
        self.assertEqual(replay['budget'], first['budget'])
        self.assertEqual({name: n['taskId'] for name, n in replay['nodes'].items()},
                         {name: n['taskId'] for name, n in first['nodes'].items()})
        self.assertTrue(all(n['status'] == 'reused' for n in replay['nodes'].values()))
        value['revision'] = 'v2-same-scope'
        path.write_text(json.dumps(value))
        same_scope = run('same-scope-new-revision', 'workflow.py', args)
        self.assertTrue(all(n['status'] == 'reused' for n in same_scope['nodes'].values()))
        self.assertEqual({name: n['taskId'] for name, n in same_scope['nodes'].items()},
                         {name: n['taskId'] for name, n in first['nodes'].items()})
        self.assertEqual(same_scope['budget']['allocated']['revisions'], 1)
        value['revision'] = 'v3-new-scope'
        path.write_text(json.dumps(value))
        new_args = list(args)
        new_args[new_args.index('--authorization')+1] = 'binding-scope-two'
        fresh = run('new-scope-create', 'workflow.py', new_args)
        self.assertEqual(fresh['state'], 'review_ready')
        self.assertTrue(all(n['status'] == 'review_ready' for n in fresh['nodes'].values()))
        for name, node in fresh['nodes'].items():
            self.assertNotEqual(node['taskId'], first['nodes'][name]['taskId'])
        with closing(sqlite3.connect((project/'tasks.sqlite').as_uri()+'?mode=ro', uri=True)) as db:
            requests = {task: json.loads(request) for task, request in db.execute('SELECT task_id,request_json FROM tasks')}
        self.assertEqual(len(requests), 8)
        for result, authorization in ((first, scope), (fresh, 'binding-scope-two')):
            for node in result['nodes'].values():
                self.assertEqual(requests[node['taskId']]['authorizationRef'], authorization)
                self.assertEqual(node['taskReceipt']['runtimeIdentity'], requests[node['taskId']]['runtimeIdentity'])
        repeated = run('new-scope-replay', 'workflow.py', new_args)
        self.assertEqual(repeated['budget'], fresh['budget'])
        self.assertEqual({name: n['taskId'] for name, n in repeated['nodes'].items()},
                         {name: n['taskId'] for name, n in fresh['nodes'].items()})
        for name, node in first['nodes'].items():
            self.assertEqual(inventory(Path(node['root'])), original[name])
        package = root/'package'
        packed = run('package', 'package.py', ['create', '--project', project, '--workflow', fresh['runKey'], '--owner', owner,
                                              '--authorization', 'binding-scope-two', '--output', package])
        moved = root/'moved-package';package.rename(moved)
        checked = run('verify-moved', 'package.py', ['verify', '--package', moved, '--sha', packed['sha256']])
        self.assertEqual(checked['workflow']['authorizationRef'], 'binding-scope-two')
        self.assertEqual(len(checked['children']), 4)
        self.assertEqual(inventory(source), baseline)
        self.assertEqual(inventory(skill), baseline)
        setup = json.loads((project/'installation-receipt.json').read_text())
        proof = {'schema': 'craft-version-binding-installed/v1', 'result': 'PASS', 'platform': sys.platform,
                 'runtimeVersion': setup['version'], 'skillFiles': baseline,
                 'installation': 'single copied fixed installed skill; existing verified runtime cache; not cold or generic Skills CLI installation',
                 'nativeCreateCount': 8, 'domains': sorted(set(n['runtimeIdentity']['pluginId'] for n in requests.values())),
                 'refusals': refusals, 'requestHashes': {task: hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest() for task, request in requests.items()},
                 'launcherHashes': [sha(Path(sys.executable)), sha(alternate)],
                 'sameScopeReusesOriginalTasks': True, 'newScopeHasOwnTasks': True,
                 'oldDeliveriesPreserved': True, 'movedPackageSha256': packed['sha256'], 'calls': calls,
                 'driverSha256': sha(Path(__file__)),
                 'remaining': ['actual GUI edit and stale-plan revision_conflict; task 5.3 remains open',
                               'single-writer matrix is separate scheduling evidence; not rerun by this test',
                               'human acceptance, model dispatch and other platforms']}
        (root/'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
