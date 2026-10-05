"""单 ArtCraft 技能在线安装后的中文混合交付与局部字幕返工。"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]


class ChineseMixedContractTests(unittest.TestCase):
    def test_single_skill_has_own_chinese_mixed_example(self):
        plan=json.loads((ROOT/'skills/artcraft-cli-revise/examples/chinese-brand-campaign.json').read_text())
        self.assertEqual(len(plan['nodes']),4)
        film=next(n for n in plan['nodes'] if n['id']=='film')['payload']['plan']
        caption=next(o for o in film['operations'] if o['command']=='caption.add')
        self.assertEqual(caption['params']['text'],'新品上市，轻松剪辑。')
        self.assertEqual(caption['as'],'caption')


@unittest.skipUnless(os.environ.get('CRAFT_CN_MIXED_FIRST_USE')=='1','requires online dependencies, installed explicit Chinese voice, ffmpeg and Pillow')
class ChineseMixedFirstUseTests(unittest.TestCase):
    def test_online_mixed_delivery_and_caption_revision_only_change_film(self):
        from PIL import Image,ImageChops
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-revise'
            installed=os.environ.get('CRAFT_INSTALLED_CN_MIXED_SKILL_ROOT')
            shutil.copytree(Path(installed) if installed else ROOT/'skills/artcraft-cli-revise',skill,ignore=shutil.ignore_patterns('__pycache__'))
            runtime=root/'runtime';project=root/'project';voice=root/'voice.wav';speech=root/'speech.aiff'
            subprocess.run(['/usr/bin/say','-v',os.environ['CRAFT_CN_VOICE'],'-o',str(speech),'新品上市，轻松剪辑。'],check=True)
            subprocess.run(['ffmpeg','-v','error','-i',str(speech),'-af','apad','-t','3','-ar','48000','-ac','1','-c:a','pcm_s16le',str(voice)],check=True)
            def run(plan):
                path=root/(plan['revision']+'.json');path.write_text(json.dumps(plan,ensure_ascii=False))
                args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(path),'--output',str(project),'--runtime-home',str(runtime),'--authorization','chinese-mixed-first-use']
                if any('voice' in node.get('providedAssets',[]) for node in plan['nodes']):args+=['--asset','voice='+str(voice)]
                result=subprocess.run(args,capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                return json.loads(result.stdout)
            plan=json.loads((skill/'examples/chinese-brand-campaign.json').read_text());first=run(plan)
            self.assertEqual(first['state'],'review_ready')
            setup=json.loads((project/'installation-receipt.json').read_text())
            self.assertEqual(setup['skills']['filmcraft']['runtimeIdentity']['cliVersion'],'0.2.0-craft.1')
            self.assertEqual(setup['skills']['filmcraft']['runtimeIdentity']['pluginVersion'],'0.1.0-dev.5')
            for name,suffix in [('logo','vectorcraft'),('poster','pcraft'),('intro','ecproj'),('film','fcproj')]:
                self.assertTrue((Path(first['nodes'][name]['root'])/('project.'+suffix)).is_file())
            filmroot=Path(first['nodes']['film']['root'])
            self.assertIn('新品上市，轻松剪辑。',(filmroot/'captions.srt').read_text())
            images=[]
            for second in ('1','2.5'):
                data=subprocess.check_output(['ffmpeg','-v','error','-ss',second,'-i',str(filmroot/'film.mp4'),'-frames:v','1','-f','image2pipe','-vcodec','png','-'])
                with Image.open(io.BytesIO(data)) as frame:images.append(frame.convert('RGB').copy())
            # H.264 量化可在静止图形区产生低幅像素差；只检查显著字幕变化。
            significant=ImageChops.difference(*images).point(lambda value:255 if value>16 else 0)
            box=significant.getbbox();self.assertIsNotNone(box);self.assertGreater(box[1],180)
            streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(filmroot/'film.mp4')]))['streams']
            video=next(stream for stream in streams if stream['codec_type']=='video')
            self.assertEqual((video['width'],video['height'],video['nb_read_frames']),(640,360,'72'))
            with wave.open(str(voice),'rb') as stream:a=struct.unpack('<'+str(stream.getnframes())+'h',stream.readframes(stream.getnframes()))
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(filmroot/'film.mp4'),'-map','0:a:0','-f','s16le','-ac','1','-ar','48000','-'])
            b=struct.unpack('<'+str(len(raw)//2)+'h',raw);n=min(len(a),len(b));a=a[:n];b=b[:n]
            correlation=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b));self.assertGreater(correlation,.95)
            original={name:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(node['root']).iterdir() if p.is_file()} for name,node in first['nodes'].items()}
            revised=json.loads(json.dumps(plan));revised['revision']='v2'
            node=next(n for n in revised['nodes'] if n['id']=='film');artifact=first['nodes']['film']['outputs'][0]
            node['expectedRevision']=artifact['nativeProjectRef']['sha256'];node['externalInputs']=[{'root':str(filmroot),'artifact':artifact}]
            node['providedAssets']=[];node['payload']['sourceProject']={'assetId':artifact['assetId']};node['payload']['assetBindings']=[{'name':'intro','assetId':'intro-video','retained':True}]
            node['payload']['plan']={'operations':[{'command':'captions.setText','params':{'caption':{'$ref':'caption.caption'},'text':'品牌焕新，精彩呈现。'}}],'frames':['254016000000'],'export':{'audioRequired':True,'burnCaptions':True}}
            second=run(revised)
            for name in ('logo','poster','intro'):self.assertEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId'])
            self.assertNotEqual(first['nodes']['film']['taskId'],second['nodes']['film']['taskId'])
            newroot=Path(second['nodes']['film']['root'])
            self.assertIn('品牌焕新，精彩呈现。',(newroot/'captions.srt').read_text())
            self.assertEqual(json.loads((filmroot/'native.json').read_text())['sequence']['audio'],json.loads((newroot/'native.json').read_text())['sequence']['audio'])
            with Image.open(filmroot/'frame-0000.png') as old,Image.open(newroot/'frame-0000.png') as new:
                self.assertIsNotNone(ImageChops.difference(old.convert('RGB'),new.convert('RGB')).getbbox(),'distinct Chinese captions must not render as identical missing glyphs')
            for name,node in first['nodes'].items():
                for filename,sha in original[name].items():self.assertEqual(hashlib.sha256((Path(node['root'])/filename).read_bytes()).hexdigest(),sha)
            repeat=run(revised);self.assertEqual(second['budget'],repeat['budget'])
            self.assertEqual({name:n['taskId'] for name,n in second['nodes'].items()},{name:n['taskId'] for name,n in repeat['nodes'].items()})
            def package(*args):
                result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/package.py'),*map(str,args),'--runtime-home',str(runtime)],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=180)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
            output=root/'delivery';packed=package('create','--project',project,'--workflow',second['runKey'],'--authorization','chinese-mixed-first-use','--output',output)
            self.assertEqual(len(package('verify','--package',output,'--sha',packed['sha256'])['children']),4)
            if os.environ.get('CRAFT_CN_MIXED_EVIDENCE_DIR'):
                evidence=Path(os.environ['CRAFT_CN_MIXED_EVIDENCE_DIR']);evidence.mkdir(parents=True,exist_ok=False)
                shutil.copytree(project,evidence/'project');shutil.copytree(output,evidence/'delivery')
                (evidence/'receipt.json').write_text(json.dumps({'correlation':correlation,'first':first,'second':second,'package':packed,'filmRuntime':setup['skills']['filmcraft']['runtimeIdentity']},ensure_ascii=False,indent=2)+'\n')
            self.assertFalse(any(skill.rglob('*.pyc')))
