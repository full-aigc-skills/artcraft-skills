"""单 ArtCraft 技能首次在线安装及仅成片音轨增益返工。"""
import array
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from contextlib import nullcontext
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('CRAFT_GAIN_MIXED_FIRST_USE') == '1', 'requires public runtime/domain downloads and ffmpeg')
class AudioGainMixedFirstUseTests(unittest.TestCase):
    def test_gain_revision_only_rebuilds_film_and_preserves_original_delivery(self):
        source = Path(os.environ.get('CRAFT_INSTALLED_GAIN_MIXED_SKILL_ROOT', ROOT / 'skills/artcraft-cli-revise'))
        retained=os.environ.get('CRAFT_GAIN_MIXED_ROOT')
        if retained:Path(retained).mkdir(parents=True,exist_ok=False)
        with nullcontext(retained) if retained else tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            skill = root / '.agents/skills/artcraft-cli-revise'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            def digest(path):
                return hashlib.sha256(path.read_bytes()).hexdigest()
            skill_hashes = {str(p.relative_to(skill)): digest(p) for p in skill.rglob('*') if p.is_file()}
            voice = root / 'voice.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1:sample_rate=48000', '-c:a', 'pcm_s16le', str(voice)], check=True)
            runtime, project = root / 'empty-runtime', root / 'project'
            self.assertFalse(runtime.exists())
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            def run(plan):
                path = root / (plan['revision'] + '.json')
                path.write_text(json.dumps(plan))
                args = [sys.executable, '-I', '-B', str(skill / 'scripts/workflow.py'), str(path), '--output', str(project), '--runtime-home', str(runtime), '--authorization', 'mixed-gain-first-use']
                if os.environ.get('CRAFT_BUNDLE_DIRECTORY'):
                    args += ['--bundle-dir', os.environ['CRAFT_BUNDLE_DIRECTORY']]
                if any('voice' in n.get('providedAssets', []) for n in plan['nodes']):
                    args += ['--asset', 'voice=' + str(voice)]
                result = subprocess.run(args, capture_output=True, text=True, env=environment, timeout=600)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt['state'], 'review_ready', result.stdout)
                return receipt
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text())
            first = run(plan)
            originals = {name: {str(p.relative_to(Path(node['root']))): digest(p) for p in Path(node['root']).rglob('*') if p.is_file()} for name, node in first['nodes'].items()}
            filmroot = Path(first['nodes']['film']['root'])
            artifact = first['nodes']['film']['outputs'][0]
            revised = json.loads(json.dumps(plan)); revised['revision'] = 'gain-v2'
            node = next(n for n in revised['nodes'] if n['id'] == 'film')
            node['expectedRevision'] = artifact['nativeProjectRef']['sha256']
            node['externalInputs'] = [{'root': str(filmroot), 'artifact': artifact}]
            node['providedAssets'] = []
            node['payload']['sourceProject'] = {'assetId': artifact['assetId']}
            node['payload']['assetBindings'] = [{'name': 'intro', 'assetId': 'intro-video', 'retained': True}]
            node['payload']['plan'] = {'operations': [{'command': 'mixer.setStrip', 'params': {'strip': 'A1', 'volumeDb': -6.0}}], 'frames': ['127008000000'], 'export': {'audioRequired': True}}
            second = run(revised)
            for name in ('logo', 'poster', 'intro'):
                self.assertEqual(first['nodes'][name]['taskId'], second['nodes'][name]['taskId'])
            self.assertNotEqual(first['nodes']['film']['taskId'], second['nodes']['film']['taskId'])
            newroot = Path(second['nodes']['film']['root'])
            before = json.loads((filmroot / 'native.json').read_text())['sequence']
            after = json.loads((newroot / 'native.json').read_text())['sequence']
            self.assertEqual(before, after)
            self.assertEqual((filmroot / 'captions.json').read_bytes(), (newroot / 'captions.json').read_bytes())
            self.assertEqual((filmroot / 'frame-0000.png').read_bytes(), (newroot / 'frame-0000.png').read_bytes())
            def rms(path):
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ar', '48000', '-ac', '1', '-f', 'f32le', '-'])
                samples = array.array('f', raw)
                if sys.byteorder != 'little': samples.byteswap()
                selected = samples[12000:36000]
                self.assertEqual(len(selected), 24000)
                return math.sqrt(sum(x*x for x in selected) / len(selected))
            ratio = rms(newroot / 'film.mp4') / rms(filmroot / 'film.mp4')
            self.assertAlmostEqual(ratio, 10 ** (-6 / 20), delta=.025)
            repeated = run(revised)
            self.assertEqual(second['budget'], repeated['budget'])
            self.assertEqual({k: v['taskId'] for k, v in second['nodes'].items()}, {k: v['taskId'] for k, v in repeated['nodes'].items()})
            for name, files in originals.items():
                for filename, sha in files.items(): self.assertEqual(digest(Path(first['nodes'][name]['root']) / filename), sha)
            for filename, sha in skill_hashes.items(): self.assertEqual(digest(skill / filename), sha)
            self.assertFalse(list(skill.rglob('*.pyc')))
            setup = json.loads((project / 'installation-receipt.json').read_text())
            if os.environ.get('CRAFT_GAIN_MIXED_EVIDENCE'):
                proof = {'schema': 'artcraft-audio-gain-mixed-first-use/v1', 'scope': 'single copied revise skill; empty default public runtime/domain install; four native projects; static A1 gain only; synthetic existing audio', 'decodedRmsRatio': ratio, 'expectedRatio': 10 ** (-6 / 20), 'runtimeVersion': setup['version'], 'filmRuntimeIdentity': setup['skills']['filmcraft']['runtimeIdentity'], 'initialTaskIds': {k: v['taskId'] for k, v in first['nodes'].items()}, 'revisedTaskIds': {k: v['taskId'] for k, v in second['nodes'].items()}, 'originalDeliveryPreserved': True, 'nativeSequenceCaptionsPreviewPreserved': True, 'repeatBudgetAndTasksPreserved': True, 'skillFilesPreserved': True, 'initialFilmFiles': originals['film'], 'revisedFilmFiles': {str(p.relative_to(newroot)): digest(p) for p in newroot.rglob('*') if p.is_file()}}
                with Path(os.environ['CRAFT_GAIN_MIXED_EVIDENCE']).open('x') as stream: json.dump(proof, stream, indent=2)
