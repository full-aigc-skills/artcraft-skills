"""独立技能公开安装后，新授权任务不得复用旧授权生产者；不证明创作接受。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('CRAFT_INSTALLED_AUTH_SKILL_ROOT', ROOT / 'skills/artcraft-use'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@unittest.skipUnless(os.environ.get('CRAFT_AUTH_FIRST_USE') == '1', 'requires public pinned native downloads')
class AuthorizationFirstUseTests(unittest.TestCase):
    def test_new_authorization_registers_native_task_preserves_old_delivery_and_replays_itself(self):
        with tempfile.TemporaryDirectory(prefix='artcraft-auth-first-use-') as temporary:
            root = Path(temporary);skill = root / 'single skill';shutil.copytree(SOURCE, skill, ignore=shutil.ignore_patterns('__pycache__'))
            runtime = root / 'fresh runtime';project = root / 'project'
            def run(script, *args):
                command = [sys.executable, '-I', '-B', str(skill / 'scripts' / script), *map(str, args), '--runtime-home', str(runtime)]
                result = subprocess.run(command, env=dict(os.environ, PATH='/usr/bin:/bin'), capture_output=True, text=True, timeout=600)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text());plan['nodes'] = [n for n in plan['nodes'] if n['id'] == 'logo']
            path = root / 'plan.json';path.write_text(json.dumps(plan))
            first = run('workflow.py', path, '--output', project, '--authorization', 'scope-one')
            self.assertEqual(first['state'], 'review_ready');old = first['nodes']['logo'];old_root = Path(old['root'])
            original = {str(p.relative_to(old_root)): sha(p) for p in old_root.rglob('*') if p.is_file()}
            plan['revision'] = 'new-scope-v2';path.write_text(json.dumps(plan))
            second = run('workflow.py', path, '--output', project, '--authorization', 'scope-two')
            self.assertEqual(second['state'], 'review_ready');new = second['nodes']['logo']
            self.assertNotEqual(new['taskId'], old['taskId']);self.assertEqual(new['status'], 'review_ready')
            self.assertEqual(second['budget']['allocated'], {'minorUnits': 0, 'externalCalls': 0, 'revisions': 0})
            with sqlite3.connect(project / 'tasks.sqlite') as database:
                requests = {row[0]: json.loads(row[1]) for row in database.execute('SELECT task_id,request_json FROM tasks')}
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[old['taskId']]['authorizationRef'], 'scope-one')
            self.assertEqual(requests[new['taskId']]['authorizationRef'], 'scope-two')
            replay = run('workflow.py', path, '--output', project, '--authorization', 'scope-two')
            self.assertEqual(replay['nodes']['logo']['taskId'], new['taskId'])
            self.assertEqual(replay['budget'], second['budget'])
            self.assertEqual({str(p.relative_to(old_root)): sha(p) for p in old_root.rglob('*') if p.is_file()}, original)
            package = root / 'package'
            packed = run('package.py', 'create', '--project', project, '--workflow', second['runKey'], '--authorization', 'scope-two', '--output', package)
            checked = run('package.py', 'verify', '--package', package, '--sha', packed['sha256'])
            self.assertEqual(checked['workflow']['authorizationRef'], 'scope-two')
            self.assertEqual(checked['children'][0]['taskId'], new['taskId'])
            setup = json.loads((project / 'installation-receipt.json').read_text())
            self.assertEqual(set(setup['skills']), {'vectorcraft'})
            self.assertFalse(any(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_AUTH_EVIDENCE_FILE'):
                value = {'schema': 'craft-native-authorization-observation/v1', 'runtimeVersion': setup['version'], 'originalFiles': original,
                         'newFiles': {str(p.relative_to(Path(new['root']))): sha(p) for p in Path(new['root']).rglob('*') if p.is_file()},
                         'packageSha256': packed['sha256'], 'taskIds': [old['taskId'], new['taskId']], 'authorizations': ['scope-one', 'scope-two'],
                         'requestSha256': {task: hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest() for task, request in requests.items()}}
                with Path(os.environ['CRAFT_AUTH_EVIDENCE_FILE']).open('x') as output:
                    json.dump(value, output, ensure_ascii=False, indent=2);output.write('\n')

if __name__ == '__main__':
    unittest.main()
