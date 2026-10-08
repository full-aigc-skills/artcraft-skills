"""实际安装单技能验证不透明节点名；四领域原生结果与移动包分别核验。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from contextlib import nullcontext


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_DAG_IDENTITY_FIRST_USE') == '1',
                     'requires fixed installed Art skill and public native downloads')
class DagIdentityFirstUseTests(unittest.TestCase):
    def test_opaque_names_native_delivery_resume_and_moved_package(self):
        retained = os.environ.get('CRAFT_DAG_IDENTITY_ROOT')
        if retained:
            Path(retained).mkdir(parents=True, exist_ok=False)
        with nullcontext(retained) if retained else tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = Path(os.environ['CRAFT_INSTALLED_DAG_IDENTITY_SKILL'])
            baseline = hashes(source)
            skill = root / '.agents/skills/artcraft-cli-execute'
            shutil.copytree(source, skill)
            runtime, project = root / 'empty-runtime', root / 'project'
            voice = root / 'voice.wav'
            with wave.open(str(voice), 'wb') as output:
                output.setparams((1, 2, 48000, 48000, 'NONE', 'not compressed'))
                output.writeframes(struct.pack('<h', 1000) * 48000)
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text())
            names = {'logo': '__proto__', 'poster': 'constructor',
                     'intro': 'toString', 'film': 'hasOwnProperty'}
            for node in plan['nodes']:
                node['id'] = names[node['id']]
                node['dependsOn'] = [names[name] for name in node['dependsOn']]
                for binding in node.get('inputBindings', []):
                    binding['from'] = names[binding['from']]
            plan_file = root / 'opaque-plan.json'
            plan_file.write_text(json.dumps(plan))
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            for key in ('CRAFT_RUNTIME_HOME', 'CRAFT_NODE_ARCHIVE',
                        'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY'):
                environment.pop(key, None)
            calls = []

            def run(args, label):
                result = subprocess.run([sys.executable, '-I', '-B', *args],
                                        capture_output=True, text=True, env=environment, timeout=600)
                (root / (label + '.stdout')).write_text(result.stdout)
                (root / (label + '.stderr')).write_text(result.stderr)
                calls.append({'label': label, 'exitCode': result.returncode,
                              'stdoutSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                              'stderrSha256': hashlib.sha256(result.stderr.encode()).hexdigest()})
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)

            args = [str(skill / 'scripts/workflow.py'), str(plan_file), '--output', str(project),
                    '--runtime-home', str(runtime), '--owner', 'identity-owner',
                    '--authorization', 'identity-authority', '--asset', 'voice=' + str(voice)]
            self.assertFalse(runtime.exists())
            first = run(args, 'first')
            self.assertEqual(first['state'], 'review_ready')
            self.assertEqual(set(first['nodes']), set(names.values()))
            suffixes = {'logo': 'vectorcraft', 'poster': 'pcraft', 'intro': 'ecproj', 'film': 'fcproj'}
            originals = {}
            for old, suffix in suffixes.items():
                record = first['nodes'][names[old]]
                self.assertEqual(record['status'], 'review_ready')
                delivery = Path(record['root'])
                manifest = json.loads((delivery / 'manifest.json').read_text())
                self.assertTrue((delivery / ('project.' + suffix)).is_file())
                self.assertTrue((delivery / 'native.json').is_file())
                for path, digest in manifest['files'].items():
                    self.assertEqual(hashlib.sha256((delivery / path).read_bytes()).hexdigest(), digest)
                originals[names[old]] = hashes(delivery)
            second = run(args, 'restart')
            self.assertEqual(second['state'], 'review_ready')
            self.assertEqual(second['budget'], first['budget'])
            for name, record in first['nodes'].items():
                self.assertEqual(second['nodes'][name]['taskId'], record['taskId'])
                self.assertEqual(second['nodes'][name]['status'], 'reused')
                self.assertEqual(hashes(Path(record['root'])), originals[name])
            cli = [str(skill / 'scripts/cli.py'), '--runtime-home', str(runtime), '--']
            package = root / 'package'
            packed = run([*cli, 'package', '--database', str(project / 'tasks.sqlite'),
                          '--workflow', first['runKey'], '--owner', 'identity-owner',
                          '--authorization', 'identity-authority', '--output', str(package)], 'package')
            moved = root / 'moved-package'
            package.rename(moved)
            verified = run([*cli, 'verify-package', '--package', str(moved),
                            '--sha', packed['sha256']], 'verify-moved')
            self.assertEqual(verified['state'], 'review_ready')
            self.assertEqual(len(json.loads((moved / 'project.json').read_text())['children']), 4)
            self.assertEqual(hashes(source), baseline)
            self.assertEqual(hashes(skill), baseline)
            setup = json.loads((project / 'installation-receipt.json').read_text())
            if os.environ.get('CRAFT_DAG_IDENTITY_EVIDENCE'):
                proof = {'schema': 'artcraft-dag-identity-fixed-first-use/v1', 'result': 'PASS',
                         'runtimeVersion': setup['version'], 'nodeIds': list(names.values()),
                         'coldPublicInstall': True, 'nativeChildren': 4, 'calls': calls,
                         'taskIdsReused': True, 'budgetReused': True, 'oldDeliveriesPreserved': True,
                         'movedPackageVerified': True, 'installedAndCopiedSkillsPreserved': True,
                         'sourceFiles': baseline, 'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                         'scope': 'fixed installed single skill, public cold four-domain native DAG and restart; not all concurrent single-writer scenarios'}
                Path(os.environ['CRAFT_DAG_IDENTITY_EVIDENCE']).write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
