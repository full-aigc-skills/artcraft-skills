"""公开旧 Art26／Photo6 不支持笔刷时必须保留失败与原交付；仅显式在线验收运行。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import unittest
import urllib.request
import zipfile


@unittest.skipUnless(os.environ.get('CRAFT_CONSISTENCY_LEGACY_FIRST_USE') == '1', 'explicit legacy public-release first use')
class LegacyConsistencyFirstUse(unittest.TestCase):
    def test_old_dependency_refuses_stroke_without_ready_delivery_or_source_changes(self):
        root = Path(os.environ['CRAFT_CONSISTENCY_LEGACY_OUTPUT']).resolve()
        root.mkdir(parents=True, exist_ok=False)
        expected_sha = '12bccde093a30874c77538207a44f8ec9af8410a6e27966af91a9a13b64847ec'
        source_commit = '65b1b53e61deecb26ccc97f6a523a8893c10bf10'
        url = 'https://github.com/full-aigc-skills/artcraft-skills/releases/download/v0.1.0-dev.26/artcraft-skills-0.1.0-dev.26.zip'
        archive = root / 'source26.zip'
        with urllib.request.urlopen(url, timeout=120) as response:
            archive.write_bytes(response.read(16 * 1024 * 1024))
        sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(sha(archive), expected_sha)
        remote = subprocess.run(['git', 'ls-remote', 'https://github.com/full-aigc-skills/artcraft-skills.git', 'refs/tags/v0.1.0-dev.26'], capture_output=True, text=True, timeout=45)
        self.assertEqual(remote.returncode, 0, remote.stderr)
        self.assertEqual(remote.stdout.split()[0], source_commit)
        extracted = root / 'source26'
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                self.assertFalse(Path(entry.filename).is_absolute())
                self.assertNotIn('..', Path(entry.filename).parts)
                self.assertFalse(stat.S_ISLNK(entry.external_attr >> 16))
            bundle.extractall(extracted)
        skill = root / 'single-art26'
        shutil.copytree(extracted / 'skills/artcraft-use', skill)
        inventory = lambda directory: {str(f.relative_to(directory)): sha(f) for f in directory.rglob('*') if f.is_file()}
        skill_before = inventory(skill)
        distribution = json.loads((skill / 'scripts/distribution.lock.json').read_text())
        self.assertEqual(distribution['version'], '0.1.0-dev.28')
        self.assertEqual(distribution['bundles']['photocraft-skills']['version'], '0.1.0-dev.6')
        runtime, project = root / 'runtime', root / 'project'
        environment = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ('CRAFT_RUNTIME_HOME', 'CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY'):
            environment.pop(key, None)
        calls = []

        def call(label, script, args, expected):
            argv = [sys.executable, '-I', '-B', str(skill / 'scripts' / script), *map(str, args), '--runtime-home', str(runtime)]
            result = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=600)
            (root / (label + '.stdout')).write_text(result.stdout)
            (root / (label + '.stderr')).write_text(result.stderr)
            calls.append({'label': label, 'script': script, 'exitCode': result.returncode,
                          'stdoutSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                          'stderrSha256': hashlib.sha256(result.stderr.encode()).hexdigest()})
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            return json.loads(result.stdout)

        payload = {'schemaVersion': 'craft-skill-workflow/v1', 'plan': {
            'document': {'name': 'Legacy source preservation', 'width': 320, 'height': 400, 'background': '#faf4e8'},
            'minimumLayers': 2,
            'operations': [{'command': 'type.create', 'params': {'x': 28, 'y': 60, 'text': 'NOVA', 'name': 'Headline', 'font': 'Arial', 'size': 32, 'color': '#192a3b'}, 'as': 'headline'},
                           {'command': 'layer.new.layer', 'params': {'name': 'Product'}, 'as': 'product'}],
            'exports': [{'format': 'png'}]}, 'assetBindings': [],
            'outputs': [{'assetId': 'poster-png', 'location': 'design.png', 'mediaType': 'image/png'}]}
        node = {'id': 'poster', 'pluginId': 'photocraft', 'dependsOn': [], 'projectKey': 'poster', 'expectedRevision': None, 'payload': payload}
        plan = {'workflowId': 'legacy-unsupported-retouch', 'revision': 'v1',
                'budget': {'currency': 'USD', 'maxMinorUnits': 0, 'maxExternalCalls': 0, 'maxRevisions': 1}, 'nodes': [node]}
        plan_file = root / 'create.json'; plan_file.write_text(json.dumps(plan))
        args = [plan_file, '--output', project, '--authorization', 'legacy-refusal-evaluation']
        first = call('create', 'workflow.py', args, 0)
        self.assertEqual(first['state'], 'review_ready')
        original = first['nodes']['poster']; old_root = Path(original['root']); original_files = inventory(old_root)
        artifact = original['outputs'][0]
        plan['revision'] = 'v2'
        node['expectedRevision'] = artifact['nativeProjectRef']['sha256']
        node['externalInputs'] = [{'root': str(old_root), 'artifact': artifact}]
        payload['sourceProject'] = {'assetId': 'poster-png'}
        domain_plan = {'minimumLayers': 2, 'operations': [
            {'command': 'layer.select', 'params': {'layer': {'$ref': 'product.layer'}}},
            {'command': 'paint.stroke', 'params': {'points': [[130, 180], [135, 180]], 'size': 12, 'hardness': 1, 'opacity': 1, 'flow': 1, 'color': '#0033ff'}}],
            'exports': [{'format': 'png'}], 'protectedRegions': [{'id': 'footer', 'rect': [0, 240, 320, 160]}]}
        payload['plan'] = domain_plan
        plan_file = root / 'revise.json'; plan_file.write_text(json.dumps(plan))
        args = [plan_file, '--output', project, '--authorization', 'legacy-refusal-evaluation']
        failed = json.loads(call('refused', 'workflow.py', args, 1)['error'])
        self.assertEqual(failed['state'], 'failed')
        self.assertEqual(failed['nodes']['poster']['status'], 'failed')
        self.assertEqual(failed['nodes']['poster']['outputs'], [])
        again = json.loads(call('same-failure', 'workflow.py', args, 1)['error'])
        self.assertEqual(again['nodes']['poster']['taskId'], failed['nodes']['poster']['taskId'])
        self.assertEqual(again['budget'], failed['budget'])
        self.assertEqual(original_files, inventory(old_root))
        setup = json.loads((project / 'installation-receipt.json').read_text())
        self.assertEqual(setup['skills']['photocraft']['runtimeIdentity']['pluginVersion'], '0.1.0-dev.6')
        # 旧 Art 只提供通用失败码；单独执行同一旧领域公开入口观察原因，不伪造 Art 的诊断能力。
        domain_file = root / 'domain-plan.json'; domain_file.write_text(json.dumps(domain_plan))
        domain_skill = Path(setup['skills']['photocraft']['skillRoot'])
        native = subprocess.run([sys.executable, '-I', '-B', str(domain_skill / 'scripts/workflow.py'), str(domain_file), '--output', str(root / 'domain-refused'), '--runtime-home', str(runtime)], env=environment, capture_output=True, text=True, timeout=60)
        (root / 'domain-refused.stdout').write_text(native.stdout)
        (root / 'domain-refused.stderr').write_text(native.stderr)
        self.assertEqual(native.returncode, 1, native.stdout + native.stderr)
        self.assertEqual(json.loads(native.stdout)['error'], 'unsupported_command')
        self.assertFalse((root / 'domain-refused').exists())
        self.assertEqual(original_files, inventory(old_root))
        packed = call('pack-old-source', 'package.py', ['create', '--project', project, '--workflow', first['runKey'], '--authorization', 'legacy-refusal-evaluation', '--output', root / 'package'], 0)
        (root / 'package').rename(root / 'moved-package')
        verified = call('verify-old-source', 'package.py', ['verify', '--package', root / 'moved-package', '--sha', packed['sha256']], 0)
        self.assertEqual(verified['state'], 'review_ready')
        self.assertEqual(skill_before, inventory(skill))
        self.assertFalse(list(skill.rglob('*.pyc')))
        value = {'schema': 'craft-consistency-legacy-refusal/v1', 'sourceRef': 'v0.1.0-dev.26',
                 'sourceCommit': source_commit, 'sourceZipSha256': expected_sha, 'runtime': setup['version'],
                 'photoSource': setup['skills']['photocraft']['runtimeIdentity'], 'calls': calls,
                 'originalFiles': original_files, 'sourcePreserved': True, 'oldPackageSha256': packed['sha256'],
                 'failedTaskId': failed['nodes']['poster']['taskId'], 'failedNodeStatus': failed['nodes']['poster']['status'],
                 'failedOutputs': failed['nodes']['poster']['outputs'], 'sameFailureTaskAndBudget': True,
                 'domainPublicRefusal': json.loads(native.stdout),
                 'domainPublicRefusalStdoutSha256': hashlib.sha256(native.stdout.encode()).hexdigest(),
                 'scope': 'legacy public Art26/runtime28 with pinned Photo6; separate domain unsupported_command observation; generic Art failure not promoted to uncollected domain diagnostics; original source and moved old package preserved'}
        (root / 'proof.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
