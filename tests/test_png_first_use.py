"""候选独立技能首次登记 PNG，使用既有公开运行时完成 Photo 原生交付。"""
import hashlib,json,os,shutil,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('CRAFT_INSTALLED_PNG_ART_SKILL',str(ROOT/'skills/artcraft-cli-execute')))
@unittest.skipUnless(os.environ.get('CRAFT_PNG_FIRST_USE')=='1','requires public downloads and native Photo runtime')
class PngFirstUse(unittest.TestCase):
 def test_isolated_skill_registers_real_png_and_packages_native_poster(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-execute';shutil.copytree(SOURCE,skill,ignore=shutil.ignore_patterns('__pycache__'))
   hashes=lambda:{p.relative_to(skill).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()}
   before=hashes()
   def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
   product=root/'product.bin';product.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\0\0\x80'))+chunk(b'IEND',b''));original=product.read_bytes()
   plan=json.loads((skill/'examples/brand-campaign.json').read_text());poster=next(n for n in plan['nodes'] if n['id']=='poster');poster['dependsOn']=[];poster['providedAssets']=['product'];poster['payload']['assetBindings']=[{'name':'logo','assetId':'product'}];plan['nodes']=[poster]
   plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan));runtime=root/'empty-runtime';project=root/'project'
   def run(script,args):
    result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime),*map(str,args)],env=dict(os.environ,PATH='/usr/bin:/bin'),capture_output=True,text=True,timeout=600)
    self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   result=run('workflow.py',[plan_path,'--output',project,'--authorization','png-first-use','--asset','product='+str(product)])
   self.assertEqual(result['state'],'review_ready');frozen=json.loads(next(p for p in (project/'plans').glob('*.json') if not p.name.endswith('.binding.json')).read_text());asset=frozen['nodes'][0]['externalInputs'][0]['artifact']
   self.assertEqual(asset['mediaType'],'image/png');self.assertEqual(asset['technicalMetadata'],{'width':1,'height':1,'bitDepth':8,'alpha':True})
   package=root/'package';packed=run('package.py',['create','--project',project,'--workflow',result['runKey'],'--authorization','png-first-use','--output',package]);moved=root/'moved';shutil.move(package,moved)
   verified=run('package.py',['verify','--package',moved,'--sha',packed['sha256']]);self.assertEqual(len(verified['children']),1);self.assertEqual(product.read_bytes(),original);self.assertEqual(hashes(),before)
   if os.environ.get('CRAFT_PNG_FIRST_USE_EVIDENCE'):
    evidence={'schema':'artcraft-png-installed-first-use/v1','result':'passed','runtimeVersion':json.loads((project/'installation-receipt.json').read_text())['version'],'mediaType':asset['mediaType'],'technicalMetadata':asset['technicalMetadata'],'movedPackageChildren':1,'sourceAndSkillPreserved':True,'runtimeMode':'default public downloads','skillFiles':before}
    with Path(os.environ['CRAFT_PNG_FIRST_USE_EVIDENCE']).open('x') as stream:json.dump(evidence,stream,indent=2)
