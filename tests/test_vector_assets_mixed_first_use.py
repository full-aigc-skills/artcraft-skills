"""单 ArtCraft 技能公开冷安装：Vector 登记素材、Photo 交接与局部返工。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('CRAFT_INSTALLED_VECTOR_ART_SKILL', ROOT/'skills/artcraft-cli-revise'))


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(root).rglob('*') if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_VECTOR_MIXED_FIRST_USE') == '1',
                     'requires public runtime downloads and existing Pillow')
class VectorAssetsMixedFirstUse(unittest.TestCase):
    def test_registered_asset_revision_rebuilds_poster_and_preserves_independent_icon(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(prefix='craft-vector-mixed-first-use-') as temporary:
            root = Path(temporary)
            skill = root/'.agents/skills/artcraft-cli-revise'
            shutil.copytree(SOURCE, skill, ignore=shutil.ignore_patterns('__pycache__'))
            original_skill, copied_skill = hashes(SOURCE), hashes(skill)
            provided = root/'provided'; provided.mkdir()
            Image.new('RGB', (32, 24), '#ed3412').save(provided/'product.png')
            Image.new('RGB', (64, 48), '#175cce').save(provided/'replacement.jpg', quality=100)
            original_inputs = hashes(provided)
            runtime, project = root/'empty-runtime', root/'project'
            self.assertFalse(runtime.exists())

            def payload(plan, bindings, asset_id, location):
                return {'schemaVersion': 'craft-skill-workflow/v1', 'plan': plan,
                        'assetBindings': bindings,
                        'outputs': [{'assetId': asset_id, 'location': location, 'mediaType': 'image/png'}]}

            def node(name, domain, dependencies, value):
                return {'id': name, 'pluginId': domain, 'projectKey': name,
                        'dependsOn': dependencies, 'expectedRevision': None, 'payload': value}

            vector = {'document': {'name': 'Provided brand', 'width': 120, 'height': 80},
                      'operations': [
                          {'command': 'asset.place', 'params': {'asset': 'product', 'rect': [8, 8, 32, 24]}, 'as': 'productObject'},
                          {'command': 'shape.rectangle', 'params': {'x': 90, 'y': 50, 'width': 15, 'height': 15, 'fill': '#21c563'}, 'as': 'unrelated'}],
                      'exports': [{'format': 'png'}]}
            poster = {'document': {'name': 'Brand poster', 'width': 160, 'height': 120, 'background': '#faf4e8'},
                      'operations': [{'command': 'asset.place', 'params': {'asset': 'brand', 'center': [80, 60], 'name': 'Brand'}}],
                      'exports': [{'format': 'png'}, {'format': 'psd'}]}
            icon = {'document': {'name': 'Independent icon', 'width': 40, 'height': 40},
                    'operations': [{'command': 'shape.rectangle', 'params': {'x': 8, 'y': 8, 'width': 24, 'height': 24, 'fill': '#21c563'}}],
                    'exports': [{'format': 'png'}]}
            plan = {'workflowId': 'provided-vector-brand-first-use', 'revision': 'v1',
                    'budget': {'currency': 'USD', 'maxMinorUnits': 0, 'maxRevisions': 1, 'maxExternalCalls': 0},
                    'nodes': [
                        {**node('brand', 'vectorcraft', [], payload(vector, [{'name': 'product', 'assetId': 'product'}], 'brand-png', 'artboard-1.png')), 'providedAssets': ['product']},
                        {**node('poster', 'photocraft', ['brand'], payload(poster, [{'name': 'brand', 'assetId': 'brand-png'}], 'poster-png', 'design.png')), 'inputBindings': [{'from': 'brand', 'assetId': 'brand-png'}]},
                        node('independent', 'vectorcraft', [], payload(icon, [], 'icon-png', 'artboard-1.png'))]}

            def run(value, assignment):
                path = root/(value['revision']+'.json'); path.write_text(json.dumps(value))
                command = [sys.executable, '-I', '-B', str(skill/'scripts/workflow.py'), str(path),
                           '--output', str(project), '--runtime-home', str(runtime),
                           '--authorization', 'vector-assets-first-use', '--asset', assignment]
                result = subprocess.run(command, env=dict(os.environ, PATH='/usr/bin:/bin'),
                                        capture_output=True, text=True, timeout=600)
                if result.returncode and os.environ.get('CRAFT_VECTOR_MIXED_FAILURE_DIRECTORY'):
                    shutil.copytree(project, Path(os.environ['CRAFT_VECTOR_MIXED_FAILURE_DIRECTORY']))
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                value = json.loads(result.stdout)
                self.assertEqual(value['state'], 'review_ready', result.stdout)
                return value

            first = run(plan, 'product='+str(provided/'product.png'))
            installation = json.loads((project/'installation-receipt.json').read_text())
            self.assertEqual(set(installation['skills']), {'vectorcraft', 'photocraft'})
            original_deliveries = {name: hashes(Path(item['root'])) for name, item in first['nodes'].items()}
            old = Path(first['nodes']['brand']['root'])
            old_manifest = json.loads((old/'manifest.json').read_text())
            changed = json.loads(json.dumps(plan)); changed['revision'] = 'v2'
            prior = first['nodes']['brand']['outputs'][0]
            brand = changed['nodes'][0]
            brand['expectedRevision'] = prior['nativeProjectRef']['sha256']
            brand['externalInputs'] = [{'root': str(old), 'artifact': prior}]
            brand['providedAssets'] = ['new-product']
            brand['payload'] = {**payload(
                {'operations': [{'command': 'asset.replace', 'params': {'asset': 'product', 'replacement': 'updated'}}], 'exports': [{'format': 'png'}]},
                [{'name': 'updated', 'assetId': 'new-product'}], 'brand-png', 'artboard-1.png'),
                'sourceProject': {'assetId': 'brand-png'}}
            second = run(changed, 'new-product='+str(provided/'replacement.jpg'))
            for name in ['brand', 'poster']:
                self.assertNotEqual(first['nodes'][name]['taskId'], second['nodes'][name]['taskId'])
                self.assertNotEqual(first['nodes'][name]['outputs'][0]['sha256'], second['nodes'][name]['outputs'][0]['sha256'])
            self.assertEqual(first['nodes']['independent']['taskId'], second['nodes']['independent']['taskId'])
            new = Path(second['nodes']['brand']['root'])
            new_manifest = json.loads((new/'manifest.json').read_text())
            self.assertEqual(new_manifest['assets']['product']['ids'], old_manifest['assets']['product']['ids'])
            replacement_hash = original_inputs['replacement.jpg']
            self.assertEqual(new_manifest['assets']['product']['sha256'], replacement_hash)
            self.assertTrue(any(ref['assetId'] == 'new-product' and ref['sha256'] == replacement_hash
                                for ref in second['nodes']['brand']['outputs'][0]['sourceRefs']))
            for name, item in first['nodes'].items():
                self.assertEqual(hashes(Path(item['root'])), original_deliveries[name])
            for name, filename, point in [('brand', 'artboard-1.png', (20, 20)), ('poster', 'design.png', (40, 40))]:
                with Image.open(Path(first['nodes'][name]['root'])/filename) as image:
                    self.assertEqual(image.convert('RGB').getpixel(point), (237, 52, 18))
                with Image.open(Path(second['nodes'][name]['root'])/filename) as image:
                    self.assertTrue(all(abs(a-b) <= 2 for a, b in zip(image.convert('RGB').getpixel(point), (23, 92, 206))))
            with Image.open(Path(second['nodes']['poster']['root'])/'design.psd') as image:
                image.load(); self.assertEqual(image.size, (160, 120))
            repeated = run(changed, 'new-product='+str(provided/'replacement.jpg'))
            self.assertEqual(second['budget'], repeated['budget'])
            self.assertEqual({name: item['taskId'] for name, item in second['nodes'].items()},
                             {name: item['taskId'] for name, item in repeated['nodes'].items()})

            def package(arguments):
                result = subprocess.run([sys.executable, '-I', '-B', str(skill/'scripts/package.py'),
                                         '--runtime-home', str(runtime), *arguments],
                                        env=dict(os.environ, PATH='/usr/bin:/bin'), capture_output=True, text=True, timeout=180)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                return json.loads(result.stdout)

            packed = package(['create', '--project', str(project), '--workflow', second['runKey'],
                              '--authorization', 'vector-assets-first-use', '--output', str(root/'package')])
            shutil.move(root/'package', root/'moved-package')
            checked = package(['verify', '--package', str(root/'moved-package'), '--sha', packed['sha256']])
            self.assertEqual(len(checked['children']), 3)
            self.assertEqual(hashes(provided), original_inputs)
            self.assertEqual(hashes(skill), copied_skill); self.assertEqual(hashes(SOURCE), original_skill)
            if os.environ.get('CRAFT_VECTOR_MIXED_EVIDENCE'):
                proof = {'schema': 'artcraft-vector-assets-public-first-use/v1', 'result': 'passed',
                         'scope': 'one copied revise skill; empty runtime; default public downloads; Vector/Photo three-node native workflow',
                         'runtimeVersion': installation['version'], 'skillFiles': copied_skill,
                         'domainVersions': {name: item['runtimeIdentity']['pluginVersion'] for name, item in installation['skills'].items()},
                         'rasterIdsRetained': True, 'onlyConsumersRebuilt': True, 'independentTaskReused': True,
                         'realVectorAndPosterPixelsChanged': True, 'originalDeliveriesAndInputsPreserved': True,
                         'repeatBudgetAndTasksPreserved': True, 'movedPackageChildren': 3,
                         'excluded': ['four-domain complete creative acceptance', 'model dispatch', 'GUI', 'SVG provided-input registration']}
                with Path(os.environ['CRAFT_VECTOR_MIXED_EVIDENCE']).open('x') as stream:
                    json.dump(proof, stream, ensure_ascii=False, indent=2)
