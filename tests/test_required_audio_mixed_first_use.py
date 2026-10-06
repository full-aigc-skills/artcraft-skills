"""单 ArtCraft 技能冷安装：必需源音轨缺失必须失败并阻断消费节点。"""
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

@unittest.skipUnless(os.environ.get('CRAFT_REQUIRED_AUDIO_MIXED_FIRST_USE') == '1', 'requires runtime/domain downloads and ffmpeg')
class RequiredAudioMixedFirstUseTests(unittest.TestCase):
    def test_missing_source_audio_retains_diagnostics_and_blocks_consumer_without_replay(self):
        source = Path(os.environ.get('CRAFT_REQUIRED_AUDIO_ART_SKILL_ROOT', ROOT / 'skills/artcraft-cli-execute'))
        with tempfile.TemporaryDirectory(prefix='artcraft-required-audio-') as temporary:
            root = Path(temporary); skill = root / '.agents/skills/artcraft-cli-execute'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            def hashes(directory):
                return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
            original_skill = hashes(skill)
            shot = root / 'silent-shot.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=320x180:r=12:d=1', '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(shot)], check=True)
            plan = json.loads((skill / 'examples/brand-campaign.json').read_text())
            film = next(n for n in plan['nodes'] if n['id'] == 'film')
            film['providedAssets'] = ['shot']
            film['payload']['assetBindings'] = [{'name':'intro','assetId':'intro-video'}, {'name':'shot','assetId':'shot'}]
            operations = film['payload']['plan']['operations']
            operations[1]['params']['asset'] = 'shot'; operations[1]['as'] = 'shot'
            operations[2]['params']['item'] = {'$ref':'shot.item'}
            del operations[3]
            consumer = json.loads(json.dumps(film)); consumer.update(id='consumer', projectKey='consumer-project', dependsOn=['film'], providedAssets=[])
            consumer['payload']['assetBindings'] = [{'name':'intro','assetId':'film-video'}]
            consumer['payload']['plan']['operations'] = [{'command':'asset.import','params':{'asset':'intro'},'as':'intro'}, {'command':'timeline.place','params':{'item':{'$ref':'intro.item'},'track':'V1','time':'0','sourceIn':'0','duration':'254016000000','insert':False}}]
            consumer['payload']['plan']['export']['audioRequired'] = False
            consumer['payload']['outputs'][0]['assetId'] = 'consumer-video'
            plan['nodes'].append(consumer)
            path = root / 'plan.json'; path.write_text(json.dumps(plan))
            runtime, project = root / 'empty-runtime', root / 'project'
            self.assertFalse(runtime.exists())
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            def run(script, args):
                command = [sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime)]
                if os.environ.get('CRAFT_BUNDLE_DIRECTORY'): command += ['--bundle-dir',os.environ['CRAFT_BUNDLE_DIRECTORY']]
                command += list(map(str,args))
                return subprocess.run(command,capture_output=True,text=True,env=environment,timeout=600)
            def workflow():
                result = run('workflow.py',[path,'--output',project,'--authorization','required-audio-first-use','--asset','shot='+str(shot)])
                self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
                return json.loads(json.loads(result.stdout)['error'])
            first = workflow(); self.assertEqual(first['state'],'failed')
            failed = first['nodes']['film']; self.assertEqual(failed['status'],'failed'); self.assertEqual(failed['outputs'],[])
            self.assertEqual(first['nodes']['consumer']['status'],'blocked'); self.assertFalse(first['nodes']['consumer'].get('taskId'))
            diagnostics = failed['failure']['diagnostics']
            self.assertEqual(diagnostics['domainCode'],'export_audio_missing'); self.assertEqual(diagnostics['source'],'stdout'); self.assertTrue(diagnostics['stdout']['complete'])
            failed_root = Path(failed['root']); files = hashes(failed_root)
            self.assertFalse((failed_root/'manifest.json').exists())
            check = json.loads((failed_root/'audio-check.json').read_text()); self.assertTrue(check['required']); self.assertEqual(check['sourceAliases'],[])
            self.assertEqual(json.loads((failed_root/'failure.json').read_text())['error'],'export_audio_missing')
            self.assertTrue((failed_root/'project.fcproj').is_file()); self.assertTrue((failed_root/'film.mp4').is_file())
            upstream = {name: hashes(Path(first['nodes'][name]['root'])) for name in ('logo','poster','intro')}
            status_args = ['--','status','--database',project/'tasks.sqlite','--task',failed['taskId']]
            status = run('cli.py',status_args); self.assertEqual(status.returncode,2,status.stdout+status.stderr); stopped=json.loads(status.stdout)
            self.assertEqual(stopped['error']['diagnostics'],diagnostics)
            again = workflow(); self.assertEqual(again['budget'],first['budget']); self.assertEqual(again['nodes']['film']['taskId'],failed['taskId']); self.assertEqual(again['nodes']['film']['failure'],failed['failure'])
            repeated_status=run('cli.py',status_args); self.assertEqual(json.loads(repeated_status.stdout)['attemptId'],stopped['attemptId'])
            self.assertEqual(hashes(failed_root),files)
            for name, before in upstream.items(): self.assertEqual(hashes(Path(first['nodes'][name]['root'])),before)
            self.assertEqual(hashes(skill),original_skill); self.assertFalse(list(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_REQUIRED_AUDIO_ART_EVIDENCE'):
                proof={'schema':'artcraft-required-audio-mixed-first-use/v1','scope':'copied single skill; empty runtime; three successful upstream native domains; actual failed Film export; consumer blocked; synthetic silent input','installation':json.loads((project/'installation-receipt.json').read_text()),'diagnostics':diagnostics,'failedFiles':files,'audioCheck':check,'attemptId':stopped['attemptId'],'repeatBudgetAndAttemptPreserved':True,'upstreamAndSkillFilesPreserved':True}
                with Path(os.environ['CRAFT_REQUIRED_AUDIO_ART_EVIDENCE']).open('x') as stream: json.dump(proof,stream,indent=2)

if __name__ == '__main__': unittest.main()
