"""固定安装 Art 技能的需求记录、零安装拒绝、四领域交付与移动包验收。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import unittest
import wave


def read(path):
    return json.loads(path.read_text())


def hashes(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_NATIVE_BRIEF_ACCEPTANCE') == '1',
                     'requires fixed installed Art skill and verified native runtime cache')
class NativeBriefAcceptance(unittest.TestCase):
    def test_installed_brief_preflight_native_delivery_and_independent_package(self):
        root = Path(os.environ['CRAFT_NATIVE_BRIEF_ROOT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        source = Path(os.environ['CRAFT_NATIVE_BRIEF_SKILL']).resolve()
        runtime = Path(os.environ['CRAFT_NATIVE_BRIEF_RUNTIME']).resolve()
        original = hashes(source)
        skill = root / '.agents/skills/artcraft-cli-execute'
        shutil.copytree(source, skill)
        environment = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('CRAFT_RUNTIME_HOME', 'CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY',
                    'CRAFT_NATIVE_ARCHIVE_DIRECTORY'):
            environment.pop(key, None)
        calls = []

        def run(script, arguments, label, expected=0):
            command = [sys.executable, '-I', '-B', str(skill / 'scripts' / script), *map(str, arguments)]
            completed = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=600)
            (root / (label + '.stdout')).write_text(completed.stdout)
            (root / (label + '.stderr')).write_text(completed.stderr)
            calls.append(dict(label=label, exitCode=completed.returncode,
                              stdoutSha256=hashlib.sha256(completed.stdout.encode()).hexdigest(),
                              stderrSha256=hashlib.sha256(completed.stderr.encode()).hexdigest()))
            self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
            return json.loads(completed.stdout)

        plan = read(skill / 'examples/brand-campaign.json')
        brief = read(skill / 'examples/brand-brief.json')
        owner, authorization = brief['ownerId'], brief['authorizationRef']
        brief['deliverables'][-1]['frameRate'] = dict(num=12, den=1)
        plan_file = root / 'plan.json'
        plan_file.write_text(json.dumps(plan))
        voice = root / 'voice.wav'
        with wave.open(str(voice), 'wb') as output:
            output.setparams((1, 2, 48000, 48000, 'NONE', 'not compressed'))
            output.writeframes(struct.pack('<h', 1000) * 48000)
        cases = []
        for label in ['upload', 'ambiguity', 'font', 'subject', 'format', 'budget', 'authorization']:
            value = copy.deepcopy(brief)
            candidate = copy.deepcopy(plan)
            if label == 'upload':
                value['deliverables'][0]['execution'] = 'cloud'
                reason = 'upload_forbidden'
            elif label == 'ambiguity':
                value['ambiguities'] = [dict(id='name', question='Confirm name', affects=['logo'])]
                reason = 'ambiguity:name'
            elif label == 'font':
                value['brand']['fonts'] = ['A font outside this plan']
                value['brand']['appliesTo'] = ['logo']
                reason = 'brand_font_mismatch'
            elif label == 'subject':
                value['subjects'] = [dict(id='hero', role='product', description='Confirmed product',
                    appliesTo=['logo'], referenceAssets=[dict(assetId='missing', version='v2', sha256='a' * 64)])]
                reason = 'reference_asset_missing_or_stale'
            elif label == 'format':
                value['deliverables'][0]['nativeFormat'] = '.pcraft'
                reason = 'native_format_mismatch'
            elif label == 'budget':
                candidate['budget']['maxMinorUnits'] = 1
                reason = 'brief_budget_mismatch'
            else:
                value['authorizationRef'] = 'different-authorization'
                reason = 'brief_authorization_mismatch'
            input_file, record = root / (label + '-brief.json'), root / (label + '-record')
            input_file.write_text(json.dumps(value))
            receipt = run('brief.py', ['create', '--input', input_file, '--output', record], label + '-create')
            candidate_file = root / (label + '-plan.json')
            candidate_file.write_text(json.dumps(candidate))
            if label in ['budget', 'authorization']:
                target, empty_runtime = root / (label + '-project'), root / (label + '-empty-runtime')
                refused = run('workflow.py', [candidate_file, '--output', target, '--runtime-home', empty_runtime,
                    '--owner', owner, '--authorization', authorization, '--brief', record,
                    '--brief-sha', receipt['sha256'], '--asset', 'voice=' + str(voice)], label + '-execute', expected=1)
                self.assertIn(reason, refused['error'])
                self.assertEqual(hashes(target), {'.artcraft-write.lock': hashlib.sha256(b'').hexdigest()})
                self.assertFalse(empty_runtime.exists())
                cases.append(dict(name=label, reason=reason, zeroInstall=True))
                continue
            assessment = run('brief.py', ['assess', '--brief', record, '--sha', receipt['sha256'],
                '--plan', candidate_file, '--owner', owner, '--authorization', authorization], label + '-assess')
            self.assertEqual(assessment['state'], 'blocked')
            self.assertIn(reason, assessment['blocked'][0]['reasons'])
            # 另加不依赖品牌图形的本地节点，确认只读检查仍然报告其通过。
            independent = copy.deepcopy(candidate['nodes'][0])
            independent.update(id='independent', dependsOn=[], projectKey='independent-project')
            independent['payload']['plan']['operations'] = []
            independent['payload']['outputs'][0]['assetId'] = 'independent-png'
            candidate['nodes'].append(independent)
            value['deliverables'].append(dict(id='independent', nativeFormat='.vectorcraft',
                width=256, height=256, dependsOn=[], execution='local'))
            input_file.write_text(json.dumps(value))
            independent_record = root / (label + '-independent-record')
            second = run('brief.py', ['create', '--input', input_file, '--output', independent_record], label + '-independent-create')
            candidate_file.write_text(json.dumps(candidate))
            independent_report = run('brief.py', ['assess', '--brief', independent_record, '--sha', second['sha256'],
                '--plan', candidate_file, '--owner', owner, '--authorization', authorization], label + '-independent-assess')
            self.assertIn('independent', independent_report['ready'])
            target, empty_runtime = root / (label + '-project'), root / (label + '-empty-runtime')
            refused = run('workflow.py', [candidate_file, '--output', target, '--runtime-home', empty_runtime,
                '--owner', owner, '--authorization', authorization, '--brief', independent_record,
                '--brief-sha', second['sha256'], '--asset', 'voice=' + str(voice)], label + '-execute', expected=1)
            self.assertIn('brief_plan_blocked', refused['error'])
            # 写入锁先保护项目目录；拒绝后只能留下空锁，不得安装、登记任务或发布产物。
            self.assertEqual(hashes(target), {'.artcraft-write.lock': hashlib.sha256(b'').hexdigest()})
            self.assertFalse(empty_runtime.exists())
            cases.append(dict(name=label, reason=reason, independentCheckReady=True, zeroInstall=True))
        input_file = root / 'brief-input.json'
        input_file.write_text(json.dumps(brief))
        record = root / 'brief-record'
        receipt = run('brief.py', ['create', '--input', input_file, '--output', record], 'brief-create')
        record.rename(root / 'moved-brief')
        record = root / 'moved-brief'
        verified = run('brief.py', ['verify', '--brief', record, '--sha', receipt['sha256']], 'brief-verify-moved')
        self.assertEqual(verified['brief'], brief)
        before = (record / 'brief.json').read_bytes()
        altered = copy.deepcopy(brief)
        altered['brand']['name'] = 'Altered after recording'
        (record / 'brief.json').write_text(json.dumps(altered))
        refused = run('workflow.py', [plan_file, '--output', root / 'tamper-project',
            '--runtime-home', root / 'tamper-empty-runtime', '--owner', owner, '--authorization', authorization,
            '--brief', record, '--brief-sha', receipt['sha256'], '--asset', 'voice=' + str(voice)], 'tamper-execute', expected=1)
        self.assertIn('brief_file_mismatch', refused['error'])
        self.assertEqual(hashes(root / 'tamper-project'), {'.artcraft-write.lock': hashlib.sha256(b'').hexdigest()})
        self.assertFalse((root / 'tamper-empty-runtime').exists())
        (record / 'brief.json').write_bytes(before)
        cases.append(dict(name='tamper', reason='brief_file_mismatch', zeroInstall=True))
        project = root / 'project'
        arguments = [plan_file, '--output', project, '--runtime-home', runtime, '--owner', owner,
            '--authorization', authorization, '--brief', record, '--brief-sha', receipt['sha256'],
            '--asset', 'voice=' + str(voice)]
        first = run('workflow.py', arguments, 'first')
        self.assertEqual(first['state'], 'review_ready')
        originals = {}
        for name, node in first['nodes'].items():
            self.assertEqual(node['status'], 'review_ready')
            originals[name] = hashes(Path(node['root']))
            for filename, digest in read(Path(node['root']) / 'manifest.json')['files'].items():
                self.assertEqual(originals[name][filename], digest)
        second = run('workflow.py', arguments, 'repeat')
        self.assertEqual(second['state'], 'review_ready')
        self.assertEqual(second['budget'], first['budget'])
        for name, node in first['nodes'].items():
            self.assertEqual(second['nodes'][name]['status'], 'reused')
            self.assertEqual(second['nodes'][name]['taskId'], node['taskId'])
            self.assertEqual(hashes(Path(node['root'])), originals[name])
        cli = ['--runtime-home', runtime, '--']
        package = root / 'package'
        packed = run('cli.py', [*cli, 'package', '--database', project / 'tasks.sqlite',
            '--workflow', first['runKey'], '--owner', owner, '--authorization', authorization,
            '--output', package], 'package')
        moved = root / 'moved-package'
        package.rename(moved)
        project.rename(root / 'retained-project')
        voice.rename(root / 'retained-voice.wav')
        self.assertFalse(project.exists())
        self.assertFalse(voice.exists())
        checked = run('cli.py', [*cli, 'verify-package', '--package', moved, '--sha', packed['sha256']], 'verify-package')
        self.assertEqual(len(checked['children']), 4)
        self.assertEqual(read(moved / 'workflow-plan-portable.json')['projectBrief'], brief)
        self.assertEqual(hashes(source), original)
        self.assertEqual(hashes(skill), original)
        proof = dict(schema='craft-native-brief-public-acceptance/v1', result='PASS',
            calls=calls, blockedCases=cases, briefSha256=receipt['sha256'], packageSha256=packed['sha256'],
            children=4, budgetReused=True, taskIdsReused=True, movedBriefVerified=True,
            movedPackageIndependent=True, frozenBriefRetained=True, skillFiles=original,
            scope='fixed installed skill with warm verified native cache; not cold install or creative acceptance')
        (root / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
