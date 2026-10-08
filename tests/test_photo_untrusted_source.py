"""使用固定安装的公开入口拒绝蒙版返工中未经验证的源工程。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


def fingerprints(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_ART_UNTRUSTED_PHOTO_ROOT'),
                     'requires retained fixed-install Photo acceptance')
class PhotoUntrustedSource(unittest.TestCase):
    def test_public_entry_refuses_untrusted_sources_without_overwriting_delivery(self):
        root = Path(os.environ['CRAFT_ART_UNTRUSTED_PHOTO_ROOT'])
        original = json.loads((root / 'v2.json').read_text())
        source = Path(original['nodes'][0]['externalInputs'][0]['root'])
        before = fingerprints(source)
        installed = root / '.agents/skills/artcraft-use'
        installed_before = fingerprints(installed)
        evidence_root = root / 'untrusted-source'
        evidence_root.mkdir(exist_ok=False)
        results = []
        for case in ('missing-artifact', 'missing-root', 'wrong-native-digest', 'missing-native-digest'):
            with self.subTest(case=case):
                plan = copy.deepcopy(original)
                plan['revision'] = case
                external = plan['nodes'][0]['externalInputs'][0]
                if case == 'missing-artifact':
                    external.pop('artifact')
                elif case == 'missing-root':
                    external.pop('root')
                elif case == 'wrong-native-digest':
                    external['artifact']['nativeProjectRef']['sha256'] = '0' * 64
                else:
                    external['artifact']['nativeProjectRef'].pop('sha256')
                plan_file = evidence_root / (case + '.json')
                plan_file.write_text(json.dumps(plan))
                output = evidence_root / case
                argv = [sys.executable, '-I', '-B', str(installed / 'scripts/workflow.py'),
                        str(plan_file), '--output', str(output), '--runtime-home',
                        str(root / 'empty-runtime'), '--owner', 'local-user',
                        '--authorization', 'photo-adjustment-local']
                process = subprocess.run(argv, env=dict(os.environ, PATH='/usr/bin:/bin'),
                                         capture_output=True, text=True, timeout=180)
                (evidence_root / (case + '.stdout')).write_text(process.stdout)
                (evidence_root / (case + '.stderr')).write_text(process.stderr)
                # 结构预检或运行时来源核验都允许拒绝，但不能误把启动故障当成通过。
                response = json.loads(process.stdout)
                self.assertNotEqual(response.get('state'), 'review_ready', response)
                self.assertTrue(process.returncode != 0 or response.get('state') in
                                ('failed', 'blocked', 'conflicted'), response)
                self.assertNotIn('Traceback', process.stderr)
                self.assertFalse(list(output.rglob('*.pcraft')))
                self.assertFalse(list(output.rglob('design.png')))
                self.assertEqual(fingerprints(source), before)
                self.assertEqual(fingerprints(installed), installed_before)
                results.append({'case': case, 'exitCode': process.returncode,
                                'response': response, 'sourcePreserved': True,
                                'noNativeOrRenderedDelivery': True})
        (evidence_root / 'proof.json').write_text(json.dumps({
            'schema': 'artcraft-photo-untrusted-source/v1', 'result': 'PASS',
            'cases': results, 'sourceFiles': before,
            'installedSkillUnchanged': True}, indent=2) + '\n')
