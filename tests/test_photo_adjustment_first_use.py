"""Art单技能蒙版调整计划与可信源返工。"""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PhotoAdjustmentContract(unittest.TestCase):
 def test_each_skill_owns_plan_and_pinned_photo(self):
  for skill in (ROOT/'skills').iterdir():
   if not (skill/'SKILL.md').exists():continue
   plan=json.loads((skill/'examples/photo-adjustment-workflow.json').read_text());self.assertEqual(plan['nodes'][0]['pluginId'],'photocraft');self.assertIn('references/photo-adjustment.md',(skill/'SKILL.md').read_text());self.assertTrue((skill/'references/photo-adjustment.md').exists());lock=json.loads((skill/'scripts/distribution.lock.json').read_text());self.assertEqual(lock['bundles']['photocraft-skills']['version'],'0.1.0-dev.31')

import hashlib,os,shutil,subprocess,sys,tempfile

def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
@unittest.skipUnless(os.environ.get('CRAFT_ART_PHOTO_ADJUSTMENT')=='1','explicit native first-use opt-in')
class PhotoAdjustmentPublic(unittest.TestCase):
 def test_cold_native_mask_revision_and_moved_package(self):
  from PIL import Image
  original=Path(os.environ.get('CRAFT_ART_ADJUSTMENT_SKILL',ROOT/'skills/artcraft-use'));before=hashes(original)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);skill=root/'.agents/skills'/original.name;shutil.copytree(original,skill,ignore=shutil.ignore_patterns('__pycache__'));identity=hashes(skill);runtime=root/'empty-runtime';project=root/'project';self.assertFalse(runtime.exists());env=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):env.pop(key,None)
   def call(script,args):
    r=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args)],env=env,capture_output=True,text=True,timeout=900);self.assertEqual(r.returncode,0,r.stdout+r.stderr);return json.loads(r.stdout)
   def execute(plan):
    p=root/(plan['revision']+'.json');p.write_text(json.dumps(plan));v=call('workflow.py',[p,'--output',project,'--runtime-home',runtime,'--owner','local-user','--authorization','photo-adjustment-local']);self.assertEqual(v['state'],'review_ready');return v
   plan=json.loads((skill/'examples/photo-adjustment-workflow.json').read_text());first=execute(plan);node=first['nodes']['poster'];old=Path(node['root']);old_files=hashes(old);m=json.loads((old/'manifest.json').read_text());native=json.loads((old/'native.json').read_text());adjustment=m['bindings']['adjustment']['layer'];layers={l['id']:l for l in native['layers']};self.assertEqual(layers[adjustment]['adjustment']['BrightnessContrast']['brightness'],30);self.assertTrue(layers[adjustment]['hasMask']);self.assertEqual(execute(plan)['nodes']['poster']['taskId'],node['taskId'])
   revision=json.loads(json.dumps(plan));revision['revision']='v2';n=revision['nodes'][0];artifact=node['outputs'][0];n['expectedRevision']=artifact['nativeProjectRef']['sha256'];n['externalInputs']=[{'root':node['root'],'artifact':artifact}];n['payload']['sourceProject']={'assetId':artifact['assetId']};n['payload']['plan']=json.loads((skill/'examples/photo-adjustment-revision-plan.json').read_text());n['payload']['plan'].pop('expectedProjectSha256',None);second=execute(revision);new=Path(second['nodes']['poster']['root']);changed=json.loads((new/'native.json').read_text());newlayers={l['id']:l for l in changed['layers']};self.assertNotEqual(second['nodes']['poster']['taskId'],node['taskId']);self.assertEqual(newlayers[adjustment]['adjustment']['BrightnessContrast']['brightness'],-30);self.assertTrue(newlayers[adjustment]['hasMask']);self.assertEqual(set(layers),set(newlayers))
   for id,l in layers.items():
    if id!=adjustment:self.assertEqual({k:v for k,v in l.items() if k!='selected'},{k:v for k,v in newlayers[id].items() if k!='selected'})
   with Image.open(old/'design.png') as a,Image.open(new/'design.png') as b:
    a=a.convert('RGBA');b=b.convert('RGBA');self.assertEqual(a.size,(128,64));self.assertEqual(b.size,(128,64));x=a.getpixel((16,32));y=b.getpixel((16,32));self.assertGreater(x[0],128);self.assertLess(y[0],128);self.assertEqual(a.crop((32,0,128,64)).tobytes(),b.crop((32,0,128,64)).tobytes())
   self.assertEqual(old_files,hashes(old));packed=call('package.py',['create','--project',project,'--workflow',second['runKey'],'--owner','local-user','--authorization','photo-adjustment-local','--output',root/'package','--runtime-home',runtime]);(root/'package').rename(root/'moved');verified=call('package.py',['verify','--package',root/'moved','--sha',packed['sha256'],'--runtime-home',runtime]);self.assertEqual(len(verified['children']),1);bundles=runtime/'artcraft/bundles';self.assertTrue((bundles/'photocraft-skills').is_dir());self.assertFalse(any((bundles/(d+'-skills')).exists() for d in ('filmcraft','effectcraft','vectorcraft')));self.assertEqual(before,hashes(original));self.assertEqual(identity,hashes(skill));self.assertFalse(list(skill.rglob('*.pyc')))
   if os.environ.get('CRAFT_ART_ADJUSTMENT_REPORT'):
    Path(os.environ['CRAFT_ART_ADJUSTMENT_REPORT']).write_text(json.dumps({'schema':'artcraft-photo-adjustment-first-use/v1','result':'PASS','skill':original.name,'initialPixel':x,'revisedPixel':y,'emptyPublicRuntime':True,'nativeProjectSha256':second['nodes']['poster']['outputs'][0]['nativeProjectRef']['sha256'],'maskAndAdjustmentPersisted':True,'sourceRevision':True,'controlPixelsUnchanged':True,'nonTargetLayersPreserved':True,'originalDeliveryPreserved':True,'movedChildren':1,'skillUnchanged':True,'packageSha256':packed['sha256'],'scope':'native Photo adjustment/mask sample; not exhaustive748, PSD, GUI, model or fullV1'},indent=2)+'\n')
