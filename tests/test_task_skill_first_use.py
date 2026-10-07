"""场景技能单独安装后的原生返工、血缘、复用与交付验收。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
SKILLS = Path(os.environ.get('CRAFT_INSTALLED_TASK_SKILLS_ROOT', ROOT/'skills'))


class TaskContractTests(unittest.TestCase):
    def test_current_contracts_do_not_instruct_agents_to_ignore_implemented_features(self):
        for skill in SKILLS.iterdir():
            if not skill.is_dir():
                continue
            text = (skill / 'references/workflow.md').read_text()
            for stale in ('当前共享预算计数仍待实现', '当前须 null', '当前不支持崩溃监督器自动接管'):
                self.assertNotIn(stale, text, skill.name)
            self.assertNotIn('四领域技能保持 dev.1', (skill / 'references/recovery.md').read_text(), skill.name)


@unittest.skipUnless(os.environ.get('CRAFT_TASK_FIRST_USE') == '1',
                     'requires macOS arm64 and default online downloads')
class TaskSkillFirstUseTests(unittest.TestCase):
    def test_isolated_plan_saves_moves_and_blocks_conflicting_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/artcraft-cli-plan'
            shutil.copytree(SKILLS / skill.name, skill,
                            ignore=shutil.ignore_patterns('__pycache__'))
            brief = json.loads((skill / 'examples/brand-brief.json').read_text())
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text())
            brief['deliverables'] = [item for item in brief['deliverables'] if item['id'] == 'logo']
            brief['brand']['appliesTo'] = ['logo']
            plan['nodes'] = [node for node in plan['nodes'] if node['id'] == 'logo']
            source = root / 'brief.json'; source.write_text(json.dumps(brief))
            path = root / 'plan.json'; path.write_text(json.dumps(plan))
            original = source.read_bytes()

            def run(*args):
                result = subprocess.run([sys.executable, '-I', '-B',
                    str(skill / 'scripts/brief.py'), *map(str, args)],
                    env=dict(os.environ, PATH='/usr/bin:/bin'),
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return json.loads(result.stdout)

            receipt = run('create', '--input', source, '--output', root / 'record')
            moved = root / 'moved record'; (root / 'record').rename(moved)
            verified = run('verify', '--brief', moved, '--sha', receipt['sha256'])
            self.assertEqual(verified['brief'], brief)
            args = ['assess', '--brief', moved, '--sha', receipt['sha256'],
                    '--plan', path, '--owner', brief['ownerId'],
                    '--authorization', brief['authorizationRef']]
            ready = run(*args)
            self.assertEqual(ready['state'], 'blocked')
            self.assertEqual(ready['blocked'][0]['reasons'], ['native_output_inspection_required'])
            plan['nodes'][0]['pluginId'] = 'photocraft'
            path.write_text(json.dumps(plan))
            blocked = run(*args)
            self.assertEqual(blocked['state'], 'blocked')
            self.assertEqual(blocked['blocked'][0]['nodeId'], 'logo')
            self.assertIn('native_format_mismatch', blocked['blocked'][0]['reasons'])
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual([p.name for p in skill.parent.iterdir()], [skill.name])
            self.assertFalse(any(skill.rglob('*.pyc')))
            evidence = os.environ.get('CRAFT_PLAN_ROLE_EVIDENCE_FILE')
            if evidence:
                with open(evidence, 'x', encoding='utf-8') as stream:
                    json.dump({'schema': 'artcraft-plan-role-first-use/v1',
                        'result': 'PASS', 'briefSha256': receipt['sha256'],
                        'movedBriefVerified': True, 'nativeGate': ready['blocked'],
                        'conflict': blocked['blocked'], 'inputPreserved': True,
                        'scope': 'installed standalone planning skill; declared constraints only; no native creation'},
                        stream, ensure_ascii=False, indent=2)
                    stream.write('\n')

    def test_isolated_revise_updates_consumers_preserves_unrelated_and_delivers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/artcraft-cli-revise'
            shutil.copytree(SKILLS / 'artcraft-cli-revise', skill,
                            ignore=shutil.ignore_patterns('__pycache__'))
            runtime = root / 'runtime'; project = root / 'project'
            role_observations = []
            voice = root / 'voice.wav'
            with wave.open(str(voice), 'wb') as stream:
                stream.setparams((1, 2, 48000, 48000, 'NONE', 'not compressed'))
                stream.writeframes(b'\x00\x00' * 48000)
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text())
            # 保留片段创建回执，修订以真实绑定定位，不猜测原生 ID。
            film = next(n for n in plan['nodes'] if n['id'] == 'film')
            film['payload']['plan']['operations'][2]['as'] = 'introClip'
            unrelated = json.loads(json.dumps(plan['nodes'][0]))
            unrelated['id'] = 'unrelated'; unrelated['projectKey'] = 'unrelated-project'
            unrelated['payload']['outputs'][0]['assetId'] = 'unrelated-png'
            plan['nodes'].append(unrelated)
            environment = dict(os.environ, PATH='/usr/bin:/bin')

            def run(script, *args, success=True):
                command = [sys.executable, '-I', '-B', str(skill / 'scripts' / script),
                           *map(str, args)]
                result = subprocess.run(command, capture_output=True, text=True,
                                        env=environment, timeout=300)
                self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
                return json.loads(result.stdout)

            path = root / 'plan.json'; path.write_text(json.dumps(plan))
            common = ['--output', project, '--runtime-home', runtime, '--authorization', 'task-first-use']
            first = run('workflow.py', path, *common, '--asset', 'voice=' + str(voice))
            self.assertEqual(first['state'], 'review_ready')
            old_files = {}
            for id, node in first['nodes'].items():
                manifest = json.loads((Path(node['root']) / 'manifest.json').read_text())
                old_files[id] = {name: sha for name, sha in manifest['files'].items()}

            def operation(command, **params):
                return {'command': command, 'params': params}

            def ref(name):
                return {'$ref': name}

            changed = json.loads(json.dumps(plan)); changed['revision'] = 'v2'
            for node in changed['nodes']:
                if node['id'] == 'unrelated':
                    continue
                old = first['nodes'][node['id']]; artifact = old['outputs'][0]
                node.pop('providedAssets', None)
                node['expectedRevision'] = artifact['nativeProjectRef']['sha256']
                node['externalInputs'] = [{'root': old['root'], 'artifact': artifact}]
                node['payload']['sourceProject'] = {'assetId': artifact['assetId']}
                native = node['payload']['plan']; native.pop('document')
                node['payload']['assetBindings'] = []
                if node['id'] == 'logo':
                    native['operations'] = [operation('paint.setFill', ids=[ref('logo.ids.0'), ref('wordmark.id')], color='#d63b42')]
                elif node['id'] == 'poster':
                    # 原 Logo 图层隐藏，新 Logo 保持为独立可编辑图层；文字不重建。
                    native['operations'] = [operation('layer.select', layer=ref('logo.layer')),
                                            operation('layer.layerMask.hideAll'),
                                            operation('asset.place', asset='replacement', center=[160, 210], name='Revised Logo')]
                    node['payload']['assetBindings'] = [{'name': 'replacement', 'assetId': 'logo-png'}]
                elif node['id'] == 'intro':
                    native['operations'] = [operation('asset.replace', asset='logo', replacement='replacement')]
                    node['payload']['assetBindings'] = [{'name': 'replacement', 'assetId': 'logo-png'}]
                else:
                    native['operations'] = [dict(operation('asset.import', asset='replacement'), **{'as': 'replacement'}),
                                            operation('clip.replaceFromBin', clips=ref('introClip.clips'), item=ref('replacement.item'))]
                    node['payload']['assetBindings'] = [{'name': 'replacement', 'assetId': 'intro-video'}]
            changed_path = root / 'revised.json'; changed_path.write_text(json.dumps(changed))
            second = run('workflow.py', changed_path, *common)
            self.assertEqual(second['state'], 'review_ready')
            self.assertEqual(second['nodes']['unrelated']['taskId'], first['nodes']['unrelated']['taskId'])
            for id, old in first['nodes'].items():
                for name, sha in old_files[id].items():
                    self.assertEqual(hashlib.sha256((Path(old['root']) / name).read_bytes()).hexdigest(), sha)
                if id == 'unrelated':
                    continue
                new = second['nodes'][id]
                self.assertNotEqual(new['taskId'], old['taskId'])
                self.assertNotEqual(new['outputs'][0]['sha256'], old['outputs'][0]['sha256'])
                manifest = json.loads((Path(new['root']) / 'manifest.json').read_text())
                self.assertEqual(manifest['sourceProjectSha256'], old['outputs'][0]['nativeProjectRef']['sha256'])
            def native(result, id):
                return json.loads((Path(result['nodes'][id]['root']) / 'native.json').read_text())
            self.assertEqual(native(first, 'intro')['layers'], native(second, 'intro')['layers'])
            self.assertEqual(native(first, 'film')['sequence']['audio'], native(second, 'film')['sequence']['audio'])
            self.assertEqual((Path(first['nodes']['film']['root']) / 'captions.srt').read_bytes(),
                             (Path(second['nodes']['film']['root']) / 'captions.srt').read_bytes())
            repeated = run('workflow.py', changed_path, *common)
            self.assertEqual({id: n['taskId'] for id, n in second['nodes'].items()},
                             {id: n['taskId'] for id, n in repeated['nodes'].items()})
            self.assertEqual(second['budget'], repeated['budget'])

            def switch_skill(name):
                nonlocal skill, runtime
                self.assertFalse(any(skill.rglob('*.pyc')))
                shutil.rmtree(skill)
                skill = root / '.agents/skills' / name
                shutil.copytree(SKILLS / name, skill,
                                ignore=shutil.ignore_patterns('__pycache__'))
                self.assertEqual([p.name for p in skill.parent.iterdir()], [name])
                runtime = root / ('runtime-' + name)
                self.assertFalse(runtime.exists())
                role_observations.append({'skill': name, 'runtimeInitiallyAbsent': True})

            switch_skill('artcraft-cli-assets')
            status = run('cli.py', '--runtime-home', runtime, '--', 'status', '--database', project / 'tasks.sqlite')
            self.assertEqual(len(status['tasks']), 9)
            self.assertFalse(status['leases'])
            switch_skill('artcraft-cli-deliver')
            package = root / 'package'
            packed = run('package.py', 'create', '--project', project, '--workflow', second['runKey'],
                         '--output', package, '--authorization', 'task-first-use', '--runtime-home', runtime)
            moved = root / 'moved'; package.rename(moved)
            verified = run('package.py', 'verify', '--package', moved, '--sha', packed['sha256'], '--runtime-home', runtime)
            self.assertEqual(len(verified['children']), 5)
            switch_skill('artcraft-cli-review')
            checked = run('cli.py', '--runtime-home', runtime, '--', 'verify-package',
                          '--package', moved, '--sha', packed['sha256'])
            self.assertEqual(len(checked['children']), 5)
            switch_skill('artcraft-cli-recover')
            task = first['nodes']['unrelated']['taskId']
            cancelled = run('cli.py', '--runtime-home', runtime, '--', 'cancel',
                            '--database', project / 'tasks.sqlite', '--task', task)
            self.assertEqual(cancelled['state'], 'cancelled')
            again = run('cli.py', '--runtime-home', runtime, '--', 'cancel',
                        '--database', project / 'tasks.sqlite', '--task', task)
            self.assertEqual(again, cancelled)
            evidence = os.environ.get('CRAFT_TASK_ROLE_EVIDENCE_FILE')
            if evidence:
                record = {'schema': 'artcraft-role-first-use/v1', 'result': 'PASS', 'roles': role_observations, 'sourceRevisionNodes': 4, 'unrelatedNodeReused': True, 'packageSha256': packed['sha256'], 'children': len(verified['children']), 'repeatedCancellationStable': True, 'reviewScope': 'package integrity only; creative review NOT_RUN'}
                with open(evidence, 'x', encoding='utf-8') as stream:
                    json.dump(record, stream, ensure_ascii=False, indent=2)
                    stream.write('\n')
            self.assertFalse(run('cli.py', '--runtime-home', runtime, '--', 'status',
                                 '--database', project / 'tasks.sqlite')['leases'])
            self.assertFalse(any(skill.rglob('*.pyc')))


if __name__ == '__main__':
    unittest.main()
