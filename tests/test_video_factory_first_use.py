"""单技能首次安装后，通过公开外部插件验证本工作流的真实成片。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
ROOT=Path(__file__).resolve().parents[1]

class ExternalPrerequisiteTests(unittest.TestCase):
    def test_missing_external_tool_is_reported_before_installing_or_editing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);plan=root/'plan.json'
            plan.write_text(json.dumps({'workflowId':'external','revision':'v1','nodes':[{'pluginId':'video-factory'}]}))
            result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'skills/artcraft-use/scripts/workflow.py'),str(plan),'--output',str(root/'project'),'--runtime-home',str(root/'runtime'),'--authorization','test'],capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertIn('video_factory_registration_required',result.stdout)
            self.assertFalse((root/'runtime').exists())
            self.assertFalse((root/'project/.artcraft-project.json').exists())

@unittest.skipUnless(os.environ.get('CRAFT_VIDEO_FIRST_USE')=='1','requires declared Video Factory installation and media tools')
class ExternalFirstUseTests(unittest.TestCase):
    def test_cold_single_skill_runs_film_then_video_factory_and_packages_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/artcraft-use'
            shutil.copytree(ROOT/'skills/artcraft-use',skill,ignore=shutil.ignore_patterns('__pycache__'))
            plan=json.loads((skill/'examples/brand-campaign.json').read_text())
            film=next(n for n in plan['nodes'] if n['id']=='film')
            plan['nodes'].append({'id':'external-review','pluginId':'video-factory','dependsOn':['film'],'projectKey':'video-factory-review','expectedRevision':None,'payload':{'schemaVersion':'craft-video-evaluation/v1','assetId':film['payload']['outputs'][0]['assetId'],'expected':{'width':320,'height':180,'fps':12,'durationSeconds':1,'requireAudio':True}}})
            path=root/'plan.json';path.write_text(json.dumps(plan))
            voice=root/'voice.wav'
            with wave.open(str(voice),'wb') as stream:
                stream.setparams((1,2,48000,48000,'NONE','not compressed'));stream.writeframes(b'\x00\x00'*48000)
            runtime=root/'runtime';project=root/'project'
            def run(script,*args):
                command=[sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)]
                if os.environ.get('CRAFT_BUNDLE_DIRECTORY'):command+=['--bundle-dir',os.environ['CRAFT_BUNDLE_DIRECTORY']]
                result=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=300)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
            args=[path,'--output',project,'--authorization','external-first-use','--asset','voice='+str(voice),'--video-factory-root',os.environ['CRAFT_VIDEO_FACTORY_ROOT'],'--ffmpeg',os.environ['CRAFT_FFMPEG'],'--ffprobe',os.environ['CRAFT_FFPROBE']]
            first=run('workflow.py',*args);self.assertEqual(first['state'],'review_ready')
            output=first['nodes']['external-review']['outputs'][0]
            report=json.loads((Path(first['nodes']['external-review']['root'])/output['location']).read_text())
            self.assertEqual(report['input']['sha256'],first['nodes']['film']['outputs'][0]['sha256'])
            self.assertEqual(report['result']['decision'],'review')
            self.assertEqual(next(g['status'] for g in report['result']['gates'] if g['id']=='provenance'),'NOT_RUN')
            second=run('workflow.py',*args)
            self.assertEqual({n:x['taskId'] for n,x in first['nodes'].items()},{n:x['taskId'] for n,x in second['nodes'].items()})
            packed=run('package.py','create','--project',project,'--workflow',first['runKey'],'--authorization','external-first-use','--output',root/'delivery')
            verified=run('package.py','verify','--package',root/'delivery','--sha',packed['sha256'])
            self.assertEqual(len(verified['children']),5)
            self.assertFalse(any(skill.rglob('*.pyc')))
