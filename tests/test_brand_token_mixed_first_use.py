"""单 ArtCraft 技能首次安装后，品牌 token 更新传播到真实混合产物。"""
import hashlib
import json
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

class BrandTokenMixedContractTests(unittest.TestCase):
 def test_each_single_skill_contains_bound_native_brand_example(self):
  for directory in sorted((ROOT/'skills').iterdir()):
   if not (directory/'SKILL.md').is_file():continue
   plan=json.loads((directory/'examples/brand-token-campaign.json').read_text())
   nodes={node['id']:node for node in plan['nodes']}
   self.assertEqual(set(nodes),{'logo','poster','intro','film','badge'})
   self.assertEqual(nodes['badge']['dependsOn'],[])
   self.assertEqual(nodes['poster']['dependsOn'],['logo'])
   self.assertEqual(nodes['intro']['dependsOn'],['logo'])
   self.assertEqual(nodes['film']['dependsOn'],['intro'])
   self.assertTrue(any(op['command']=='swatch.new' and op.get('as')=='primary' for op in nodes['logo']['payload']['plan']['operations']))
   lock=json.loads((directory/'scripts/distribution.lock.json').read_text())
   bundle=lock['bundles']['vectorcraft-skills']
   self.assertEqual(bundle['version'],'0.1.0-dev.31')
   self.assertIn('skills/vectorcraft-use/examples/brand-token-assets.json',bundle['files'])
   self.assertIn('skills/vectorcraft-cli-text/references/chinese-text.md',bundle['files'])
   for node_id in ('logo','badge'):
    for operation in nodes[node_id]['payload']['plan']['operations']:
     if operation['command']=='text.create':self.assertEqual(operation['params']['font'],'Source Sans 3')

@unittest.skipUnless(os.environ.get('CRAFT_BRAND_MIXED_FIRST_USE')=='1','requires online native runtimes and Pillow')
class BrandTokenMixedFirstUseTests(unittest.TestCase):
 def test_native_token_revision_rebuilds_consumers_and_reuses_unrelated_node(self):
  from PIL import Image,ImageChops
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-revise'
   shutil.copytree(Path(os.environ.get('CRAFT_INSTALLED_BRAND_MIXED_SKILL_ROOT',ROOT/'skills/artcraft-cli-revise')),skill,ignore=shutil.ignore_patterns('__pycache__'))
   skill_hashes={str(p.relative_to(skill)):hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()}
   runtime=root/'fresh runtime';project=root/'project';voice=root/'voice.wav'
   self.assertFalse(runtime.exists())
   workflow_python=Path(os.environ.get('CRAFT_WORKFLOW_PYTHON',sys.executable)).resolve(strict=True)
   with wave.open(str(voice),'wb') as stream:
    stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(48000);stream.writeframes(struct.pack('<h',7000)*48000)
   voice_sha=hashlib.sha256(voice.read_bytes()).hexdigest()
   plan=json.loads((skill/'examples/brand-token-campaign.json').read_text())
   logo_plan=next(n for n in plan['nodes'] if n['id']=='logo')['payload']['plan']
   for op in logo_plan['operations']:
    if op['command']=='artboard.new':
     op['params'].update({'y':-24,'width':200,'height':240} if op['params']['name']=='Icon' else {'y':-40,'width':192,'height':256})
   logo_plan['exports']=[{'format':fmt,'artboard':i} for i in range(3) for fmt in ('svg','png','pdf')]
   def run(value):
    path=root/(value['revision']+'.json');path.write_text(json.dumps(value))
    args=[str(workflow_python),'-I','-B',str(skill/'scripts/workflow.py'),str(path),'--output',str(project),'--runtime-home',str(runtime),'--authorization','brand-token-mixed-first-use','--asset','voice='+str(voice)]
    if os.environ.get('CRAFT_BUNDLE_DIRECTORY'):args+=['--bundle-dir',os.environ['CRAFT_BUNDLE_DIRECTORY']]
    result=subprocess.run(args,capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   first=run(plan);self.assertEqual(first['state'],'review_ready')
   install=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(Path(install['pythonExecutable']).resolve(),workflow_python);self.assertEqual(install['skills']['vectorcraft']['runtimeIdentity']['pluginVersion'],json.loads((skill/'scripts/distribution.lock.json').read_text())['bundles']['vectorcraft-skills']['version'])
   originals={name:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(node['root']).iterdir() if p.is_file()} for name,node in first['nodes'].items()}
   revised=json.loads(json.dumps(plan));revised['revision']='v2';logo=next(n for n in revised['nodes'] if n['id']=='logo');prior=first['nodes']['logo'];artifact=prior['outputs'][0]
   logo['expectedRevision']=artifact['nativeProjectRef']['sha256'];logo['externalInputs']=[{'root':prior['root'],'artifact':artifact}]
   logo['payload']['sourceProject']={'assetId':artifact['assetId']};logo['payload']['plan']={'operations':[{'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}}]}
   second=run(revised);self.assertEqual(second['state'],'review_ready')
   for name in ('logo','poster','intro','film'):
    self.assertNotEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId'])
    self.assertNotEqual(first['nodes'][name]['outputs'][0]['sha256'],second['nodes'][name]['outputs'][0]['sha256'])
   self.assertEqual(first['nodes']['badge']['taskId'],second['nodes']['badge']['taskId'])
   for name,node in first['nodes'].items():
    for filename,sha in originals[name].items():self.assertEqual(hashlib.sha256((Path(node['root'])/filename).read_bytes()).hexdigest(),sha)
   old=Path(first['nodes']['logo']['root']);new=Path(second['nodes']['logo']['root'])
   initial_native=json.loads((old/'native.json').read_text());revised_native=json.loads((new/'native.json').read_text())
   self.assertEqual(initial_native['artboards'],revised_native['artboards'])
   unchanged={fmt:{'before':hashlib.sha256((old/('artboard-2.'+fmt)).read_bytes()).hexdigest(),'after':hashlib.sha256((new/('artboard-2.'+fmt)).read_bytes()).hexdigest()} for fmt in ('svg','png','pdf')}
   if os.environ.get('CRAFT_BRAND_MIXED_FAILURE_EVIDENCE'):
    with Path(os.environ['CRAFT_BRAND_MIXED_FAILURE_EVIDENCE']).open('x') as stream:json.dump({'schema':'artcraft-mixed-artboard-isolation-regression/v1','unaffectedExports':unchanged,'vectorRuntimeIdentity':install['skills']['vectorcraft']['runtimeIdentity'],'initialTaskIds':{k:v['taskId'] for k,v in first['nodes'].items()},'revisedTaskIds':{k:v['taskId'] for k,v in second['nodes'].items()},'scope':'single ArtCraft revise skill, empty public runtime/domain downloads, five-node brand revision, distinct artboard sizes/origins; before unaffected export gate'},stream,indent=2)
   for fmt in ('svg','png','pdf'):self.assertEqual((old/('artboard-2.'+fmt)).read_bytes(),(new/('artboard-2.'+fmt)).read_bytes(),fmt)

   for name,filename in [('poster','design.png'),('intro','frame-0001.png'),('film','frame-0000.png')]:
    with Image.open(Path(first['nodes'][name]['root'])/filename) as before,Image.open(Path(second['nodes'][name]['root'])/filename) as after:self.assertIsNotNone(ImageChops.difference(before.convert('RGB'),after.convert('RGB')).getbbox(),name)
   self.assertEqual(hashlib.sha256(voice.read_bytes()).hexdigest(),voice_sha)
   repeat=run(revised);self.assertEqual(second['budget'],repeat['budget']);self.assertEqual({n:x['taskId'] for n,x in second['nodes'].items()},{n:x['taskId'] for n,x in repeat['nodes'].items()})
   package=root/'delivery';result=subprocess.run([str(workflow_python),'-I','-B',str(skill/'scripts/package.py'),'create','--project',str(project),'--workflow',second['runKey'],'--authorization','brand-token-mixed-first-use','--output',str(package),'--runtime-home',str(runtime)],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=180)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);packed=json.loads(result.stdout)
   result=subprocess.run([str(workflow_python),'-I','-B',str(skill/'scripts/package.py'),'verify','--package',str(package),'--sha',packed['sha256'],'--runtime-home',str(runtime)],capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=180)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertEqual(len(json.loads(result.stdout)['children']),5)
   self.assertFalse(any(skill.rglob('*.pyc')))
   for filename,sha in skill_hashes.items():self.assertEqual(hashlib.sha256((skill/filename).read_bytes()).hexdigest(),sha)
   if os.environ.get('CRAFT_BRAND_MIXED_EVIDENCE'):
    proof={'schema':'artcraft-brand-artboard-mixed-first-use/v1','scope':'single copied revise skill; empty public runtime/domain install; five native projects, global brand revision and selective reuse; native board geometry and SVG/PNG/PDF byte identity; independent consumer PNG pixel changes; repeated budget/tasks; five-child package verify','runtimeVersion':install['version'],'vectorRuntimeIdentity':install['skills']['vectorcraft']['runtimeIdentity'],'unaffectedExports':unchanged,'initialTaskIds':{k:v['taskId'] for k,v in first['nodes'].items()},'revisedTaskIds':{k:v['taskId'] for k,v in second['nodes'].items()},'originalDeliveryPreserved':True,'providedVoicePreserved':True,'skillFilesPreserved':True,'repeatBudgetAndTasksPreserved':True,'packageChildren':5,'artboards':initial_native['artboards'],'distributionLockSha256':hashlib.sha256((skill/'scripts/distribution.lock.json').read_bytes()).hexdigest()}
    with Path(os.environ['CRAFT_BRAND_MIXED_EVIDENCE']).open('x') as stream:json.dump(proof,stream,indent=2)
