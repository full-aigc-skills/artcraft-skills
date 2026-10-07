"""Art独立入口的Effect父级／表达式公开冷安装及可信源返工。"""
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
class ExpressionContract(unittest.TestCase):
 def test_each_skill_owns_expression_recipe_and_fixed_domain(self):
  for skill in (ROOT/'skills').iterdir():
   if not (skill/'SKILL.md').is_file():continue
   plan=json.loads((skill/'examples/effect-expression-workflow.json').read_text());self.assertEqual(plan['nodes'][0]['pluginId'],'effectcraft');self.assertTrue((skill/'references/effect-expression.md').is_file());self.assertIn('references/effect-expression.md',(skill/'SKILL.md').read_text());lock=json.loads((skill/'scripts/distribution.lock.json').read_text());self.assertEqual(lock['bundles']['effectcraft-skills']['version'],'0.1.0-dev.22');self.assertEqual(lock['bundles']['artcraft-runtime']['version'],'0.1.0-dev.83')
@unittest.skipUnless(os.environ.get('CRAFT_ART_EFFECT_EXPRESSION')=='1','explicit public native opt-in')
class ExpressionPublicFirstUse(unittest.TestCase):
 def test_cold_expression_parent_source_revision_and_moved_package(self):
  from PIL import Image
  original=Path(os.environ.get('CRAFT_ART_EXPRESSION_SKILL',ROOT/'skills/artcraft-use'));before=hashes(original)
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);skill=root/'.agents/skills'/original.name;shutil.copytree(original,skill,ignore=shutil.ignore_patterns('__pycache__'));identity=hashes(skill);runtime=root/'empty-runtime';self.assertFalse(runtime.exists());project=root/'project';env=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):env.pop(key,None)
   def call(script,args):
    r=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args)],env=env,capture_output=True,text=True,timeout=900);self.assertEqual(r.returncode,0,r.stdout+r.stderr);return json.loads(r.stdout)
   def execute(plan):
    file=root/(plan['revision']+'.json');file.write_text(json.dumps(plan));value=call('workflow.py',[file,'--output',project,'--runtime-home',runtime,'--owner','local-user','--authorization','effect-expression-local']);self.assertEqual(value['state'],'review_ready');return value
   plan=json.loads((skill/'examples/effect-expression-workflow.json').read_text());first=execute(plan);node=first['nodes']['intro'];old=Path(node['root']);old_files=hashes(old);manifest=json.loads((old/'manifest.json').read_text());native=json.loads((old/'native.json').read_text());target=str(manifest['bindings']['target']['layer']);parent=str(manifest['bindings']['parent']['layer']);control=str(manifest['bindings']['control']['layer']);self.assertEqual(native['layers'][target]['parent'],int(parent))
   repeated=execute(plan);self.assertEqual(repeated['nodes']['intro']['taskId'],node['taskId'])
   revision=json.loads(json.dumps(plan));revision['revision']='v2';n=revision['nodes'][0];artifact=node['outputs'][0];n['expectedRevision']=artifact['nativeProjectRef']['sha256'];n['externalInputs']=[{'root':node['root'],'artifact':artifact}];n['payload']['sourceProject']={'assetId':artifact['assetId']};n['payload']['plan']=json.loads((skill/'examples/effect-expression-revision-plan.json').read_text());n['payload']['plan'].pop('expectedProjectSha256',None)
   second=execute(revision);new=Path(second['nodes']['intro']['root']);changed=json.loads((new/'native.json').read_text());self.assertNotEqual(second['nodes']['intro']['taskId'],node['taskId']);self.assertEqual(set(native['layers']),set(changed['layers']));self.assertEqual(native['layers'][parent],changed['layers'][parent]);self.assertEqual(native['layers'][control],changed['layers'][control]);self.assertEqual(native['composition'],changed['composition']);self.assertEqual(native['layers'][target]['parent'],changed['layers'][target]['parent']);self.assertEqual(old_files,hashes(old))
   alphas=[]
   for index in range(2):
    with Image.open(old/f'frame-{index:04d}.png') as a,Image.open(new/f'frame-{index:04d}.png') as b:
     a=a.convert('RGBA');b=b.convert('RGBA');self.assertEqual(a.size,(128,64));self.assertEqual(b.size,(128,64));x=a.getpixel((32,32))[3];y=b.getpixel((32,32))[3];self.assertAlmostEqual(x,[128,191][index],delta=2);self.assertAlmostEqual(y,[64,128][index],delta=2);self.assertEqual(a.crop((84,20,108,44)).tobytes(),b.crop((84,20,108,44)).tobytes());alphas.append({'seconds':[0,.5][index],'initial':x,'revised':y})
   packed=call('package.py',['create','--project',project,'--workflow',second['runKey'],'--owner','local-user','--authorization','effect-expression-local','--output',root/'package','--runtime-home',runtime]);(root/'package').rename(root/'moved');verified=call('package.py',['verify','--package',root/'moved','--sha',packed['sha256'],'--runtime-home',runtime]);self.assertEqual(len(verified['children']),1);bundles=runtime/'artcraft/bundles';self.assertTrue((bundles/'effectcraft-skills').is_dir());self.assertFalse(any((bundles/(d+'-skills')).exists() for d in ('filmcraft','vectorcraft','photocraft')));self.assertEqual(before,hashes(original));self.assertEqual(identity,hashes(skill));self.assertFalse(list(skill.rglob('*.pyc')))
   if os.environ.get('CRAFT_ART_EXPRESSION_REPORT'):
    Path(os.environ['CRAFT_ART_EXPRESSION_REPORT']).write_text(json.dumps({'schema':'artcraft-effect-expression-first-use/v1','result':'PASS','skill':original.name,'emptyPublicRuntime':True,'sourceRevision':True,'nativeProjectSha256':second['nodes']['intro']['outputs'][0]['nativeProjectRef']['sha256'],'parentControlCompositionAndIdsPreserved':True,'controlPixelsUnchanged':True,'originalDeliveryPreserved':True,'alphaSamples':alphas,'movedChildren':1,'skillUnchanged':True,'packageSha256':packed['sha256'],'scope':'native Effect expression/parent sample, not exhaustive640 commands/GUI/fullV1'},indent=2)+'\n')
