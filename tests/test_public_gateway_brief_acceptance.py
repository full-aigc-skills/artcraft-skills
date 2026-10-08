"""固定安装的独立技能：Brief 网关冷启动、真实尺寸、源返工及移动交付。"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_GATEWAY_BRIEF_SKILL'), 'fixed installed skill opt-in')
class PublicGatewayBrief(unittest.TestCase):
    def test_cold_gateway_brief_source_revision_and_package(self):
        from PIL import Image
        original = Path(os.environ['CRAFT_GATEWAY_BRIEF_SKILL'])
        original_hashes = hashes(original)
        root = Path(os.environ['CRAFT_GATEWAY_BRIEF_ROOT'])
        root.mkdir(parents=True, exist_ok=False)
        skill = root / '.agents/skills' / original.name
        shutil.copytree(original, skill)
        runtime, project = root / 'empty-runtime', root / 'project'
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith('CRAFT_')}
        environment['PATH'] = '/usr/bin:/bin'
        calls = []

        def call(script, args, label, reject=False):
            argv = [sys.executable, '-I', '-B', str(skill / 'scripts' / script), *map(str, args)]
            result = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=900)
            (root / (label + '.stdout')).write_text(result.stdout)
            (root / (label + '.stderr')).write_text(result.stderr)
            calls.append({'label': label, 'exitCode': result.returncode,
                          'stdoutSha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                          'stderrSha256': hashlib.sha256(result.stderr.encode()).hexdigest()})
            reply = json.loads(result.stdout)
            if reject:
                self.assertNotEqual(result.returncode, 0, reply)
                self.assertNotIn('Traceback', result.stderr)
            else:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return reply

        def gateway(width):
            return {'command': 'native.command', 'params': {
                'command': 'artboard.setProps', 'params': {'index': 0, 'width': width, 'height': 64}}}

        plan = json.loads((skill / 'examples/vector-appearance-workflow.json').read_text())
        node = plan['nodes'][0]
        node['payload']['plan'] = {
            'document': {'name': 'Gateway Brief', 'width': 128, 'height': 64, 'units': 'Pixels'},
            'operations': [{'command': 'shape.rectangle', 'params': {'x': 4, 'y': 4, 'width': 32, 'height': 32}},
                           gateway(160)], 'exports': [{'format': 'png', 'artboard': 0}]}
        node['payload']['outputs'] = [{'assetId': 'badge-png', 'location': 'artboard-1.png', 'mediaType': 'image/png'}]
        plan['projectBrief']['deliverables'][0]['width'] = 160
        plan['projectBrief']['deliverables'][0]['height'] = 64
        owner, authorization = plan['ownerId'], plan['authorizationRef']

        def execute(value, label, output=project, reject=False, auth=authorization):
            file = root / (label + '.json')
            file.write_text(json.dumps(value))
            return call('workflow.py', [file, '--output', output, '--runtime-home', runtime,
                                       '--owner', owner, '--authorization', auth], label, reject)

        # 每个独立入口先证明错误不会触发依赖下载，再走真实冷启动。
        for case in ('authorization', 'ambiguity', 'dependency', 'malformed-gateway'):
            value = copy.deepcopy(plan)
            auth = authorization
            if case == 'authorization':
                auth = 'wrong-authorization'
            elif case == 'ambiguity':
                value['projectBrief']['ambiguities'] = [{'id': 'name', 'question': 'Confirm name', 'affects': ['badge']}]
            elif case == 'dependency':
                value['nodes'][0]['dependsOn'] = ['missing']
            else:
                value['nodes'][0]['payload']['plan']['operations'][-1]['params']['executor'] = 'untrusted'
            execute(value, case, root / ('rejected-' + case), True, auth)
            self.assertFalse(runtime.exists(), case)

        first = execute(plan, 'create')
        self.assertEqual(first['state'], 'review_ready')
        initial = first['nodes']['badge']
        source = Path(initial['root'])
        source_hashes = hashes(source)
        with Image.open(source / 'artboard-1.png') as image:
            self.assertEqual(image.size, (160, 64))
        self.assertEqual(execute(plan, 'reuse')['nodes']['badge']['taskId'], initial['taskId'])
        revised = copy.deepcopy(plan)
        revised['revision'] = 'v2'
        revised['projectBrief']['revision'] = 'brief-v2'
        revised['projectBrief']['deliverables'][0]['width'] = 192
        revised_node = revised['nodes'][0]
        artifact = initial['outputs'][0]
        revised_node['expectedRevision'] = artifact['nativeProjectRef']['sha256']
        revised_node['externalInputs'] = [{'root': str(source), 'artifact': artifact}]
        revised_node['payload']['sourceProject'] = {'assetId': artifact['assetId']}
        revised_node['payload']['plan'].pop('document')
        revised_node['payload']['plan']['operations'] = [gateway(192)]
        second = execute(revised, 'revise')
        self.assertEqual(second['state'], 'review_ready')
        self.assertNotEqual(second['nodes']['badge']['taskId'], initial['taskId'])
        with Image.open(Path(second['nodes']['badge']['root']) / 'artboard-1.png') as image:
            self.assertEqual(image.size, (192, 64))
        self.assertEqual(hashes(source), source_hashes)
        packed = call('package.py', ['create', '--project', project, '--workflow', second['runKey'],
                                    '--owner', owner, '--authorization', authorization, '--output', root / 'package',
                                    '--runtime-home', runtime], 'package')
        (root / 'package').rename(root / 'moved')
        project.rename(root / 'original-project-offline')
        verified = call('package.py', ['verify', '--package', root / 'moved', '--sha', packed['sha256'],
                                      '--runtime-home', runtime], 'verify-moved')
        self.assertEqual(len(verified['children']), 1)
        for domain in ('filmcraft', 'effectcraft', 'photocraft'):
            self.assertFalse((runtime / domain).exists())
            self.assertFalse((runtime / 'artcraft/bundles' / (domain + '-skills')).exists())
        self.assertEqual(hashes(original), original_hashes)
        self.assertEqual(hashes(skill), original_hashes)
        (root / 'proof.json').write_text(json.dumps({
            'schema': 'artcraft-public-gateway-brief/v1', 'result': 'PASS', 'skill': original.name,
            'calls': calls, 'skillFiles': original_hashes, 'coldPublicRuntime': True,
            'actualWidths': [160, 192], 'initialDeclaredWidth': 128,
            'preDownloadRefusals': ['authorization', 'ambiguity', 'dependency', 'malformed-gateway'],
            'sourcePreserved': True, 'reused': True, 'movedChildren': 1,
            'packageSha256': packed['sha256'],
            'scope': 'Vector metadata-changing gateway per installed Art entry; full mixed gateway is separate'}, indent=2) + '\n')
