"""Art独立入口首次安装新版Vector领域包并保留真实原生外观返工。"""
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
class AppearanceContract(unittest.TestCase):
 def test_each_skill_owns_vector_recipe_and_pins_new_domain(self):
  for skill in (ROOT/'skills').iterdir():
   if not (skill/'SKILL.md').is_file():continue
   plan=json.loads((skill/'examples/vector-appearance-workflow.json').read_text());self.assertEqual(plan['nodes'][0]['pluginId'],'vectorcraft')
   self.assertTrue((skill/'references/vector-appearance.md').is_file());self.assertIn('references/vector-appearance.md',(skill/'SKILL.md').read_text())
   lock=json.loads((skill/'scripts/distribution.lock.json').read_text());self.assertEqual(lock['bundles']['vectorcraft-skills']['version'],'0.1.0-dev.33');self.assertEqual(lock['bundles']['artcraft-runtime']['version'],'0.1.0-dev.113-runtime.1')
@unittest.skipUnless(os.environ.get('CRAFT_ART_VECTOR_APPEARANCE')=='1','explicit public native opt-in')
class AppearancePublicFirstUse(unittest.TestCase):
 def test_cold_native_creation_source_revision_and_moved_package(self):
  from PIL import Image
  original=Path(os.environ.get('CRAFT_ART_APPEARANCE_SKILL',ROOT/'skills/artcraft-use'));before=hashes(original)
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);skill=root/'.agents/skills'/original.name;shutil.copytree(original,skill,ignore=shutil.ignore_patterns('__pycache__'));identity=hashes(skill);runtime=root/'empty-runtime';self.assertFalse(runtime.exists());project=root/'project'
   env=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):env.pop(key,None)
   def call(script,args):
    r=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args)],env=env,capture_output=True,text=True,timeout=900);self.assertEqual(r.returncode,0,r.stdout+r.stderr);return json.loads(r.stdout)
   def execute(plan):
    file=root/(plan['revision']+'.json');file.write_text(json.dumps(plan));result=call('workflow.py',[file,'--output',project,'--runtime-home',runtime,'--owner','local-user','--authorization','vector-appearance-local']);self.assertEqual(result['state'],'review_ready');return result
   plan=json.loads((skill/'examples/vector-appearance-workflow.json').read_text());first=execute(plan);node=first['nodes']['badge'];old=Path(node['root']);old_files=hashes(old);manifest=json.loads((old/'manifest.json').read_text());native=json.loads((old/'native.json').read_text())
   def objects(model):
    result={}
    def visit(n):
     result[n['id']]=n
     for c in n.get('kind',{}).get('children',[]):visit(c)
    for n in model['layers']:visit(n)
    return result
   badge=manifest['bindings']['badge']['id'];control=manifest['bindings']['control']['id'];old_objects=objects(native);self.assertEqual(len(old_objects[badge]['appearance']['items']),3)
   repeated=execute(plan);self.assertEqual(repeated['nodes']['badge']['taskId'],node['taskId'])
   revised=json.loads(json.dumps(plan));revised['revision']='v2';n=revised['nodes'][0];artifact=node['outputs'][0];n['expectedRevision']=artifact['nativeProjectRef']['sha256'];n['externalInputs']=[{'root':node['root'],'artifact':artifact}];n['payload']['sourceProject']={'assetId':artifact['assetId']};n['payload']['plan']=json.loads((skill/'examples/vector-appearance-revision-plan.json').read_text());n['payload']['plan'].pop('expectedProjectSha256',None)
   second=execute(revised);new=Path(second['nodes']['badge']['root']);new_objects=objects(json.loads((new/'native.json').read_text()));self.assertNotEqual(second['nodes']['badge']['taskId'],node['taskId']);self.assertEqual(old_objects[control],new_objects[control]);self.assertEqual(old_objects[badge]['kind'],new_objects[badge]['kind']);self.assertEqual(set(old_objects),set(new_objects));self.assertEqual(old_objects[badge]['appearance']['items'][2],new_objects[badge]['appearance']['items'][2]);self.assertNotEqual(old_objects[badge]['appearance']['items'][0]['paint'],new_objects[badge]['appearance']['items'][0]['paint']);self.assertEqual(old_files,hashes(old))
   with Image.open(old/'artboard-1.png') as a,Image.open(new/'artboard-1.png') as b:
    a=a.convert('RGBA');b=b.convert('RGBA');self.assertEqual(a.size,(128,64));self.assertEqual(b.size,(128,64));self.assertNotEqual(a.getpixel((16,32)),b.getpixel((16,32)));self.assertEqual(a.crop((82,16,114,48)).tobytes(),b.crop((82,16,114,48)).tobytes())
   for output in [old,new]:
    self.assertTrue((output/'artboard-1.pdf').read_bytes().startswith(b'%PDF-'));self.assertTrue(ET.parse(output/'artboard-1.svg').findall('.//{http://www.w3.org/2000/svg}linearGradient'))
   packed=call('package.py',['create','--project',project,'--workflow',second['runKey'],'--owner','local-user','--authorization','vector-appearance-local','--output',root/'package','--runtime-home',runtime]);(root/'package').rename(root/'moved');verified=call('package.py',['verify','--package',root/'moved','--sha',packed['sha256'],'--runtime-home',runtime]);self.assertEqual(len(verified['children']),1)
   bundles=runtime/'artcraft/bundles';self.assertTrue((bundles/'vectorcraft-skills').is_dir());self.assertFalse(any((bundles/(d+'-skills')).exists() for d in ('filmcraft','effectcraft','photocraft')))
   self.assertEqual(before,hashes(original));self.assertEqual(identity,hashes(skill));self.assertFalse(list(skill.rglob('*.pyc')))
   if os.environ.get('CRAFT_ART_APPEARANCE_REPORT'):
    Path(os.environ['CRAFT_ART_APPEARANCE_REPORT']).write_text(json.dumps({'schema':'artcraft-vector-appearance-first-use/v1','result':'PASS','skill':original.name,'emptyPublicRuntime':True,'sourceRevision':True,'nativeProjectSha256':second['nodes']['badge']['outputs'][0]['nativeProjectRef']['sha256'],'originalPreserved':True,'controlNodeAndPixelsUnchanged':True,'targetPaintChanged':True,'idsGeometryAndTopFillPreserved':True,'svgGradientObserved':True,'pdfHeaderOnly':True,'movedChildren':1,'skillUnchanged':True,'packageSha256':packed['sha256'],'scope':'Vector native appearance sample, not exhaustive command/GUI/PDF visual/fullV1'},indent=2)+'\n')
