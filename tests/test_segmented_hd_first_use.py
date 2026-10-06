"""单独 Art 技能默认冷安装：四领域动态品牌、局部返工、恢复与移动包。"""
import hashlib
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

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ['CRAFT_INSTALLED_SEGMENTED_HD_SKILL_ROOT']).resolve() if os.environ.get('CRAFT_INSTALLED_SEGMENTED_HD_SKILL_ROOT') else ROOT/'skills/artcraft-cli-revise'
def hashes(root):
 return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}

@unittest.skipUnless(os.environ.get('CRAFT_SEGMENTED_HD_FIRST_USE')=='1','requires default public downloads, Pillow and ffmpeg')
class SegmentedHdFirstUseTests(unittest.TestCase):
 def test_cold_four_domain_logo_revision_recovery_and_portable_delivery(self):
  from PIL import Image, ImageChops
  source_hashes=hashes(SOURCE)
  with tempfile.TemporaryDirectory(prefix='art-segmented-hd-first-use-') as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-revise';shutil.copytree(SOURCE,skill,ignore=shutil.ignore_patterns('__pycache__'));skill_hashes=hashes(skill)
   runtime=root/'empty-runtime';project=root/'project';self.assertFalse(runtime.exists())
   background=root/'background.png';Image.new('RGB',(1920,1080),(0,128,0)).save(background)
   voice=root/'voice.wav'
   with wave.open(str(voice),'wb') as output:
    output.setparams((1,2,48000,240000,'NONE','not compressed'));output.writeframes(b''.join(struct.pack('<h',round(4000*math.sin(i*2*math.pi*440/48000))) for i in range(240000)))
   original_assets={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (background,voice)}
   plan=json.loads((skill/'examples/segmented-hd-brand-campaign.json').read_text())
   environment={k:v for k,v in os.environ.items() if k not in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY')};environment['PATH']='/usr/bin:/bin'
   def run(value,expected=0):
    path=root/(value['revision']+'.json');path.write_text(json.dumps(value));result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(path),'--output',str(project),'--runtime-home',str(runtime),'--authorization','dynamic-first-use','--asset','voice='+str(voice),'--asset','background='+str(background)],capture_output=True,text=True,env=environment,timeout=600)
    if result.returncode!=expected and os.environ.get('CRAFT_SEGMENTED_HD_FAILURE_DIRECTORY'):
     target=Path(os.environ['CRAFT_SEGMENTED_HD_FAILURE_DIRECTORY']);shutil.copytree(project,target,dirs_exist_ok=True);(target/'stdout.log').write_text(result.stdout+result.stderr)
    self.assertEqual(result.returncode,expected,result.stdout+result.stderr);return json.loads(result.stdout)
   first=run(plan);self.assertEqual(first['state'],'review_ready')
   installation=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(set(installation['skills']),{'filmcraft','effectcraft','photocraft','vectorcraft'})
   distribution=json.loads((skill/'scripts/distribution.lock.json').read_text())
   self.assertEqual(installation['version'],distribution['bundles']['artcraft-runtime']['version'])
   for domain,item in installation['skills'].items():
    self.assertEqual(item['runtimeIdentity']['pluginVersion'],distribution['bundles'][domain+'-skills']['version'])
   old={name:hashes(Path(item['root'])) for name,item in first['nodes'].items()};intro=first['nodes']['intro'];sequence=intro['outputs'][0];film=first['nodes']['film'];old_manifest=json.loads((Path(film['root'])/'manifest.json').read_text())
   self.assertEqual(sequence['mediaType'],'application/vnd.craft.image-sequence+json');self.assertEqual(sequence['technicalMetadata']['frameRate'],{'num':24,'den':1});self.assertEqual(sequence['technicalMetadata']['durationTicks'],'120')
   self.assertEqual(len([r for r in sequence['evidenceRefs'] if '/frame_' in r['location']]),120);self.assertEqual(old_manifest['assets']['intro']['probe']['kind'],'ImageSequence')
   for name,suffix in [('logo','vectorcraft'),('poster','pcraft'),('intro','ecproj'),('film','fcproj')]:self.assertIn('project.'+suffix,old[name])
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,duration,nb_read_frames','-of','json',str(Path(film['root'])/'film.mp4')]))['streams'][0]
   self.assertEqual((probe['width'],probe['height'],probe['avg_frame_rate'],probe['nb_read_frames']),(1920,1080,'24/1','120'));self.assertAlmostEqual(float(probe['duration']),5,places=3)
   raw=root/'decoded.rgb';subprocess.run(['ffmpeg','-v','error','-i',str(Path(film['root'])/'film.mp4'),'-f','rawvideo','-pix_fmt','rgb24',str(raw)],check=True);self.assertEqual(raw.stat().st_size,120*1920*1080*3)
   sequence_root=Path(intro['root'])/'rgba-segments';descriptor=json.loads((sequence_root/'segments.json').read_text());self.assertEqual(len(descriptor['segments']),4)
   verified=0
   for segment in descriptor['segments']:
    child=sequence_root/segment['location'];self.assertEqual(hashlib.sha256(child.read_bytes()).hexdigest(),segment['sha256'])
    for frame in json.loads(child.read_text())['frames']:
     path=child.parent/frame['location'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),frame['sha256'])
     with Image.open(path) as image:
      image.load();self.assertEqual(image.size,(1920,1080));self.assertEqual(image.mode,'RGBA');self.assertEqual(hashlib.sha256(image.tobytes()).hexdigest(),frame['rgbaSha256']);self.assertEqual(list(image.getchannel('A').getextrema()),frame['alphaExtrema'])
     verified+=1
   self.assertEqual(verified,120)
   with raw.open('rb') as stream:
    for index in (0,60,119):
     with Image.open(sequence_root/f'segment_{index//32:05d}'/f'frame_{index%32:05d}.png') as overlay:
      expected=Image.alpha_composite(Image.new('RGBA',(1920,1080),(0,128,0,255)),overlay).convert('RGB')
      for x,y in ((10,10),(896,476)):
       stream.seek((index*1920*1080+y*1920+x)*3);actual=stream.read(3);self.assertLessEqual(max(abs(a-b) for a,b in zip(actual,expected.getpixel((x,y)))),20)
    with Image.open(sequence_root/'segment_00000/frame_00000.png') as initial,Image.open(sequence_root/'segment_00001/frame_00028.png') as visible:
     initial.load();visible.load();box=visible.getchannel('A').getbbox();self.assertIsNotNone(box);point=None
     for y in range(box[1],box[3]):
      for x in range(box[0],box[2]):
       if initial.getpixel((x,y))[3]==0 and visible.getpixel((x,y))[3]==255:point=(x,y);break
      if point:break
     self.assertIsNotNone(point);x,y=point;actuals=[]
     for index,image in ((0,initial),(60,visible)):
      expected=Image.alpha_composite(Image.new('RGBA',(1920,1080),(0,128,0,255)),image).convert('RGB').getpixel((x,y));stream.seek((index*1920*1080+y*1920+x)*3);actual=stream.read(3);actuals.append(actual);self.assertLessEqual(max(abs(a-b) for a,b in zip(actual,expected)),20)
     self.assertGreater(max(abs(a-b) for a,b in zip(*actuals)),40)
   changed=json.loads(json.dumps(plan));changed['revision']='v2';logo=changed['nodes'][0];prior=first['nodes']['logo']['outputs'][0]
   logo['expectedRevision']=prior['nativeProjectRef']['sha256'];logo['externalInputs']=[{'root':first['nodes']['logo']['root'],'artifact':prior}];logo['payload']['sourceProject']={'assetId':'logo-png'};logo['payload']['plan']={'operations':[{'command':'paint.setFill','params':{'ids':[{'$ref':'logo.id'}],'color':'#ed3412'}}],'exports':[{'format':'png'},{'format':'svg'}]}
   second=run(changed);self.assertEqual(second['state'],'review_ready')
   for name in ('logo','poster','intro','film'):
    self.assertNotEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId']);self.assertNotEqual(first['nodes'][name]['outputs'][0]['sha256'],second['nodes'][name]['outputs'][0]['sha256'])
   self.assertEqual(first['nodes']['independent']['taskId'],second['nodes']['independent']['taskId'])
   new_film=Path(second['nodes']['film']['root']);new_manifest=json.loads((new_film/'manifest.json').read_text())
   for name in ('background','voice'):self.assertEqual(new_manifest['assets'][name]['sha256'],old_manifest['assets'][name]['sha256'])
   self.assertEqual(new_manifest['files']['frame-0000.png'],old_manifest['files']['frame-0000.png']);self.assertNotEqual(new_manifest['files']['frame-0001.png'],old_manifest['files']['frame-0001.png'])
   for name,filename,point in [('logo','artboard-1.png',(64,64)),('poster','design.png',(160,210))]:
    with Image.open(Path(first['nodes'][name]['root'])/filename) as image:self.assertEqual(image.convert('RGB').getpixel(point),(35,102,232))
    with Image.open(Path(second['nodes'][name]['root'])/filename) as image:self.assertEqual(image.convert('RGB').getpixel(point),(237,52,18))
   repeat=run(changed);self.assertEqual(repeat['budget'],second['budget']);self.assertEqual({k:v['taskId'] for k,v in repeat['nodes'].items()},{k:v['taskId'] for k,v in second['nodes'].items()})
   broken=Path(second['nodes']['intro']['root'])/'rgba-segments/segment_00001/frame_00002.png';saved=broken.read_bytes();broken.write_bytes(b'corrupt frame')
   rejected=run(changed,1);self.assertIn('error',rejected);blocked=json.loads(rejected['error']);self.assertEqual(blocked['state'],'blocked');self.assertIn('image_sequence_',json.dumps(blocked))
   broken.write_bytes(saved);recovered=run(changed);self.assertEqual(recovered['state'],'review_ready');self.assertEqual(recovered['budget'],second['budget']);self.assertEqual({k:v['taskId'] for k,v in recovered['nodes'].items()},{k:v['taskId'] for k,v in second['nodes'].items()})
   def package(args):
    result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/package.py'),'--runtime-home',str(runtime),*args],capture_output=True,text=True,env=environment,timeout=180);self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   packed=package(['create','--project',str(project),'--workflow',recovered['runKey'],'--authorization','dynamic-first-use','--output',str(root/'package')]);shutil.move(root/'package',root/'moved-package');checked=package(['verify','--package',str(root/'moved-package'),'--sha',packed['sha256']]);self.assertEqual(len(checked['children']),5)
   for name,item in first['nodes'].items():self.assertEqual(hashes(Path(item['root'])),old[name])
   for path in (background,voice):self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),original_assets[path.name])
   self.assertEqual(hashes(skill),skill_hashes);self.assertEqual(hashes(SOURCE),source_hashes)
   if os.environ.get('CRAFT_SEGMENTED_HD_EVIDENCE'):
    proof={'schema':'artcraft-segmented-hd-four-domain-first-use/v1','result':'PASS','scope':'one copied skill; empty runtime; default public downloads; four-domain five-node native workflow','runtimeVersion':installation['version'],'driverSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'width':1920,'height':1080,'seconds':5,'segmentCount':4,'independentSourceFrames':verified,'animatedLogoPixelVerified':True,'independentVideoProbe':probe,'distributionLockSha256':hashlib.sha256((skill/'scripts/distribution.lock.json').read_bytes()).hexdigest(),'skillFiles':skill_hashes,'domainVersions':{n:v['runtimeIdentity']['pluginVersion'] for n,v in installation['skills'].items()},'frameCount':120,'frameRate':{'num':24,'den':1},'independentlyDecodedFrames':120,'compositePixelChecks':8,'logoReplacementConsumersRebuilt':['logo','poster','intro','film'],'independentTaskReused':True,'backgroundVoiceAndInitialFramePreserved':True,'actualLogoAndPosterPixelsChanged':True,'originalInputsDeliveriesAndSkillsPreserved':True,'sameRevisionTasksAndBudgetReused':True,'corruptFrameBlockedAndRestoredWithoutReexecution':True,'movedPackageChildren':5,'excluded':['updated fixed Art plugin host until bound to host receipt','generic Skills CLI','model dispatch','GUI','complete creative approval']}
    with Path(os.environ['CRAFT_SEGMENTED_HD_EVIDENCE']).open('x') as stream:json.dump(proof,stream,indent=2)
