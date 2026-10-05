"""单独安装 ArtCraft 后，蒙版局部返工仅更新动态片头和成片。"""
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
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('CRAFT_MASK_FIRST_USE')=='1','requires default online native dependencies and Pillow')
class MaskRevisionFirstUseTests(unittest.TestCase):
    def test_mask_revision_preserves_animation_and_updates_only_consumers(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-revise'
            shutil.copytree(ROOT/'skills/artcraft-cli-revise',skill,ignore=shutil.ignore_patterns('__pycache__'))
            runtime=root/'runtime';project=root/'project';voice=root/'voice.wav'
            with wave.open(str(voice),'wb') as stream:
                stream.setparams((1,2,48000,48000,'NONE','not compressed'));stream.writeframes(b'\x00\x00'*48000)
            plan=json.loads((skill/'examples/brand-campaign.json').read_text())
            intro=next(n for n in plan['nodes'] if n['id']=='intro')
            intro['payload']['plan']['operations'].append({'command':'mask.new','params':{'layer':{'$ref':'logoLayer.layer'},'vertices':[[0,0],[128,0],[128,256],[0,256]],'closed':True,'mode':'Add'},'as':'crop'})
            film=next(n for n in plan['nodes'] if n['id']=='film');film['payload']['plan']['operations'][2]['as']='introClip'
            common=['--output',str(project),'--runtime-home',str(runtime),'--authorization','mask-first-use']
            def run(plan,initial=False):
                path=root/(plan['revision']+'.json');path.write_text(json.dumps(plan))
                args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(path),*common]
                if initial:args+=['--asset','voice='+str(voice)]
                result=subprocess.run(args,capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=300)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);value=json.loads(result.stdout)
                self.assertEqual(value['state'],'review_ready',result.stdout);return value
            first=run(plan,True)
            old_files={}
            for name,node in first['nodes'].items():old_files[name]=json.loads((Path(node['root'])/'manifest.json').read_text())['files']
            revised=json.loads(json.dumps(plan));revised['revision']='v2'
            for node in revised['nodes']:
                if node['id'] not in ('intro','film'):continue
                node.pop('providedAssets',None)
                old=first['nodes'][node['id']];artifact=old['outputs'][0]
                node['expectedRevision']=artifact['nativeProjectRef']['sha256'];node['externalInputs']=[{'root':old['root'],'artifact':artifact}]
                node['payload']['sourceProject']={'assetId':artifact['assetId']};node['payload']['plan'].pop('document')
                if node['id']=='intro':
                    node['dependsOn']=[]
                    node['payload']['assetBindings']=[]
                    node['payload']['plan']['operations']=[{'command':'mask.setVertex','params':{'layer':{'$ref':'logoLayer.layer'},'mask':{'$ref':'crop.mask'},'index':i,'point':point}} for i,point in [(1,[256,0]),(2,[256,256])]]
                else:
                    node['payload']['assetBindings']=[{'name':'replacement','assetId':'intro-video'}]
                    node['payload']['plan']['operations']=[{'command':'asset.import','params':{'asset':'replacement'},'as':'replacement'},{'command':'clip.replaceFromBin','params':{'clips':{'$ref':'introClip.clips'},'item':{'$ref':'replacement.item'}}}]
            second=run(revised)
            for name in ('logo','poster'):self.assertEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId'])
            for name in ('intro','film'):
                self.assertNotEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId'])
                self.assertNotEqual(first['nodes'][name]['outputs'][0]['sha256'],second['nodes'][name]['outputs'][0]['sha256'])
            for name,node in first['nodes'].items():
                for filename,sha in old_files[name].items():self.assertEqual(hashlib.sha256((Path(node['root'])/filename).read_bytes()).hexdigest(),sha)
            def native(result,name):return json.loads((Path(result['nodes'][name]['root'])/'native.json').read_text())
            before=native(first,'intro');after=native(second,'intro')
            def groups(node,path):
                if node.get('path')==path:return node
                for child in node.get('children',[]):
                    found=groups(child,path)
                    if found is not None:return found
                return None
            self.assertEqual(set(before['layers']),set(after['layers']))
            for layer in before['layers']:
                self.assertEqual(groups(before['layers'][layer]['properties'],'transform/opacity'),groups(after['layers'][layer]['properties'],'transform/opacity'))
            with Image.open(Path(first['nodes']['intro']['root'])/'frame-0001.png') as a,Image.open(Path(second['nodes']['intro']['root'])/'frame-0001.png') as b:
                self.assertGreater(sum(b.getchannel('A').histogram()[i]*i for i in range(256)),sum(a.getchannel('A').histogram()[i]*i for i in range(256)))
            self.assertEqual(native(first,'film')['sequence']['audio'],native(second,'film')['sequence']['audio'])
            self.assertEqual((Path(first['nodes']['film']['root'])/'captions.srt').read_bytes(),(Path(second['nodes']['film']['root'])/'captions.srt').read_bytes())
            repeat=run(revised);self.assertEqual({n:v['taskId'] for n,v in second['nodes'].items()},{n:v['taskId'] for n,v in repeat['nodes'].items()})
            self.assertEqual(second['budget'],repeat['budget'])
            def package(*args):
                result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/package.py'),*map(str,args),'--runtime-home',str(runtime)],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=120)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
            output=root/'delivery';packed=package('create','--project',project,'--workflow',second['runKey'],'--authorization','mask-first-use','--output',output)
            self.assertEqual(len(package('verify','--package',output,'--sha',packed['sha256'])['children']),4)
            self.assertFalse(any(skill.rglob('*.pyc')))
