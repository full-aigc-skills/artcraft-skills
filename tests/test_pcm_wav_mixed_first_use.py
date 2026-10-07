"""标准 PCM WAV 冷启动、原生音画交付及迁移验包。"""
import hashlib,json,os,shutil,struct,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_WAV_MIXED_FIRST_USE')=='1','requires public native runtimes')
class PcmWavMixedFirstUse(unittest.TestCase):
 def test_pcm_voice_facts_survive_native_delivery_and_moved_package(self):
  with tempfile.TemporaryDirectory(dir=os.environ.get('CRAFT_WAV_TEST_PARENT')) as temporary:
   root=Path(temporary);source_skill=Path(os.environ.get('CRAFT_INSTALLED_WAV_ART_SKILL',ROOT/'skills/artcraft-cli-execute'));skill=root/'.agents/skills'/source_skill.name;shutil.copytree(source_skill,skill,ignore=shutil.ignore_patterns('__pycache__'))
   hashes=lambda path:{p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
   before=hashes(skill);voice=root/'voice.bin'
   with wave.open(str(voice),'wb') as stream:
    stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(48000);stream.writeframes(struct.pack('<h',7000)*48000)
   voice_sha=hashlib.sha256(voice.read_bytes()).hexdigest();runtime=root/'empty-runtime';self.assertFalse(runtime.exists());project=root/'project'
   def run(script,args):
    argv=[sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime)]
    if os.environ.get('CRAFT_WAV_BUNDLE_DIR'):argv+=['--bundle-dir',os.environ['CRAFT_WAV_BUNDLE_DIR']]
    result=subprocess.run(argv+list(map(str,args)),text=True,capture_output=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600);self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   result=run('workflow.py',[skill/'examples/brand-token-campaign.json','--output',project,'--authorization','wav-first-use','--asset','voice='+str(voice)])
   source=json.loads(next(p for p in (project/'plans').glob('*.json') if not p.name.endswith('.binding.json')).read_text())
   film=next(n for n in source['nodes'] if n['id']=='film');artifact=next(x['artifact'] for x in film['externalInputs'] if x['artifact']['assetId']=='voice')
   self.assertEqual(artifact['mediaType'],'audio/wav');self.assertEqual(artifact['sha256'],voice_sha);self.assertEqual(artifact['technicalMetadata'],{'audio':{'sampleRate':48000,'channels':1},'bitDepth':16,'durationTicks':'48000','timeBase':{'num':1,'den':48000}})
   self.assertEqual(result['state'],'review_ready')
   film_result=result['nodes']['film']
   self.assertTrue(any(ref['assetId']=='voice' and ref['sha256']==voice_sha for output in film_result['outputs'] for ref in output['sourceRefs']))
   native=json.loads((Path(film_result['root'])/'native.json').read_text())
   self.assertTrue(native['sequence']['audio'])
   package=root/'package'
   packed=run('package.py',['create','--project',project,'--workflow',result['runKey'],'--authorization','wav-first-use','--output',package]);moved=root/'moved-package';shutil.move(package,moved)
   verified=run('package.py',['verify','--package',moved,'--sha',packed['sha256']]);self.assertEqual(len(verified['children']),5)
   self.assertEqual(hashlib.sha256(voice.read_bytes()).hexdigest(),voice_sha);self.assertEqual(hashes(skill),before)
   evidence=os.environ.get('CRAFT_WAV_MIXED_EVIDENCE')
   if evidence:
    with Path(evidence).open('x') as stream:json.dump({'schema':'artcraft-pcm-wav-mixed-first-use/v1','result':'passed','runtimeVersion':json.loads((project/'installation-receipt.json').read_text())['version'],'skillName':source_skill.name,'voice':artifact,'filmOutputs':film_result['outputs'],'movedPackageSha256':packed['sha256'],'nativeAudioPresent':True,'movedPackageChildren':5,'voiceAndSkillPreserved':True,'runtimeMode':'explicit local bundles' if os.environ.get('CRAFT_WAV_BUNDLE_DIR') else 'default public downloads'},stream,indent=2)
