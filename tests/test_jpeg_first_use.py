"""候选独立技能首次登记 JPEG，使用既有公开运行时完成 Photo 原生交付。"""
from contextlib import nullcontext
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('CRAFT_INSTALLED_JPEG_ART_SKILL',str(ROOT/'skills/artcraft-cli-execute')))
@unittest.skipUnless(os.environ.get('CRAFT_JPEG_FIRST_USE')=='1','requires public downloads and native Photo runtime')
class JpegFirstUse(unittest.TestCase):
 def test_isolated_skill_registers_real_jpeg_and_packages_native_poster(self):
  retained=os.environ.get('CRAFT_JPEG_RETAIN_ROOT')
  if retained:Path(retained).resolve().mkdir(parents=True,exist_ok=False)
  with (nullcontext(str(Path(retained).resolve())) if retained else tempfile.TemporaryDirectory()) as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-execute';shutil.copytree(SOURCE,skill,ignore=shutil.ignore_patterns('__pycache__'))
   hashes=lambda:{p.relative_to(skill).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()}
   before=hashes()
   fixture=json.loads((ROOT/'tests/fixtures/jpeg-images.json').read_text())['images']['progressive']
   product=root/'product.bin';product.write_bytes(base64.b64decode(fixture));original=product.read_bytes()
   plan=json.loads((skill/'examples/brand-campaign.json').read_text());poster=next(n for n in plan['nodes'] if n['id']=='poster');poster['dependsOn']=[];poster['providedAssets']=['product'];poster['payload']['assetBindings']=[{'name':'logo','assetId':'product'}];plan['nodes']=[poster]
   poster['payload']['plan']['exports'].append({'format':'jpg'});poster['payload']['outputs'].append({'assetId':'poster-jpeg','location':'design.jpg','mediaType':'image/jpeg'})
   plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan));warm=os.environ.get('CRAFT_FIRST_USE_RUNTIME_HOME');runtime=Path(warm).resolve(strict=True) if warm else root/'empty-runtime';project=root/'project'
   if warm:self.assertTrue(runtime.is_dir())
   else:self.assertFalse(runtime.exists())
   def run(script,args):
    result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime),*map(str,args)],env=dict(os.environ,PATH='/usr/bin:/bin'),capture_output=True,text=True,timeout=600)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   result=run('workflow.py',[plan_path,'--output',project,'--authorization','jpeg-first-use','--asset','product='+str(product)])
   self.assertEqual(result['state'],'review_ready');frozen=json.loads(next(p for p in (project/'plans').glob('*.json') if not p.name.endswith('.binding.json')).read_text());asset=frozen['nodes'][0]['externalInputs'][0]['artifact']
   self.assertEqual(asset['mediaType'],'image/jpeg');self.assertTrue(asset['location'].endswith('.jpg'));self.assertEqual(asset['technicalMetadata'],{'width':7,'height':5,'bitDepth':8,'alpha':False})
   from PIL import Image
   native=list((project/'outputs').rglob('project.pcraft')) if (project/'outputs').exists() else list(project.rglob('project.pcraft'))
   self.assertEqual(len(native),1)
   directory=native[0].parent
   layers=json.loads((directory/'native.json').read_text())['layers'];self.assertGreaterEqual(len(layers),3)
   self.assertTrue((directory/'psd-inspection.json').is_file())
   for exported in [directory/'design.png',directory/'design.psd',directory/'design.jpg']:
    with Image.open(exported) as image:image.load();self.assertEqual(image.size,(320,400))
   derivative=next(item for item in result['nodes']['poster']['outputs'] if item['mediaType']=='image/jpeg')
   self.assertEqual(derivative['technicalMetadata'],{'width':320,'height':400,'bitDepth':8,'alpha':False})
   # 候选运行时的独立核验与既有固定运行时的首次安装分别取证。
   if os.environ.get('CRAFT_JPEG_CANDIDATE_CONTRACTS'):
    validator="import {verifyArtifact} from '"+Path(os.environ['CRAFT_JPEG_CANDIDATE_CONTRACTS']).resolve().as_uri()+"'; await verifyArtifact(JSON.parse(process.argv[1]),process.argv[2]);"
    checked=subprocess.run([os.environ['CRAFT_JPEG_CANDIDATE_NODE'],'--input-type=module','-e',validator,json.dumps(asset),str(project/'provided-assets')],capture_output=True,text=True,timeout=30)
    self.assertEqual(checked.returncode,0,checked.stderr)
   with Image.open(product) as image:image.load();self.assertEqual(image.size,(7,5))
   package=root/'package';packed=run('package.py',['create','--project',project,'--workflow',result['runKey'],'--authorization','jpeg-first-use','--output',package]);moved=root/'moved';shutil.move(package,moved)
   verified=run('package.py',['verify','--package',moved,'--sha',packed['sha256']]);self.assertEqual(len(verified['children']),1);self.assertEqual(product.read_bytes(),original);self.assertEqual(hashes(),before)
   if os.environ.get('CRAFT_JPEG_FIRST_USE_EVIDENCE'):
    evidence={'schema':'artcraft-jpeg-first-use-candidate/v1','result':'passed','runtimeVersion':json.loads((project/'installation-receipt.json').read_text())['version'],'mediaType':asset['mediaType'],'technicalMetadata':asset['technicalMetadata'],'movedPackageChildren':1,'nativeLayers':len(layers),'sourceAndSkillPreserved':True,'independentDecoder':'Pillow; original JPEG, exported PNG and PSD loaded','candidateRuntimeVerified':bool(os.environ.get('CRAFT_JPEG_CANDIDATE_CONTRACTS')),'runtimeMode':'public pinned installer with verified cache' if warm else 'default public downloads','warmRuntimeCache':bool(warm),'publicColdInstallation':not bool(warm),'skillFiles':before}
    evidence['jpegDerivative']=derivative;evidence['independentDecoder']='Pillow; original JPEG, exported PNG, PSD and JPEG loaded';evidence['retainedRoot']=str(root) if retained else None;evidence['resultReceipt']=result;evidence['inputArtifact']=asset;evidence['movedPackageSha256']=packed['sha256'];evidence['inputSha256']=hashlib.sha256(original).hexdigest()
    with Path(os.environ['CRAFT_JPEG_FIRST_USE_EVIDENCE']).open('x') as stream:json.dump(evidence,stream,indent=2)
