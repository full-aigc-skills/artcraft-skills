"""独立技能公开冷启动的 Film 精确时间元数据与移动包；不证明创作质量。"""
import hashlib,json,os,shutil,struct,subprocess,sys,unittest,wave,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_FILM_METADATA_FIRST_USE')=='1','requires public pinned Film runtime')
class FilmMetadataFirstUseTests(unittest.TestCase):
 def test_film_native_export_revision_and_moved_package_keep_exact_metadata(self):
  root=Path(os.environ['CRAFT_FILM_METADATA_OUTPUT']);self.assertTrue(root.is_absolute());root.mkdir(parents=True,exist_ok=False)
  source=Path(os.environ.get('CRAFT_FILM_METADATA_SKILL',ROOT/'skills/artcraft-cli-execute'));skill=root/'.agents/skills/artcraft-cli-execute';shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
  def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
  def tree(path):return {str(p.relative_to(path)):sha(p) for p in path.rglob('*') if p.is_file()}
  before=tree(skill);runtime=root/'empty runtime';project=root/'project';self.assertFalse(runtime.exists());calls=[]
  environment=dict(os.environ,PATH='/usr/bin:/bin')
  for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
  def run(script,*args,success=True):
   result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)],env=environment,capture_output=True,text=True,timeout=600)
   log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr);calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(log)})
   self.assertEqual(result.returncode,0 if success else 1,result.stdout+result.stderr);return json.loads(result.stdout)
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  still=root/'still.png';still.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',320,180,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes([239,91,54,255])*320)*180))+chunk(b'IEND',b''))
  voice=root/'voice.wav'
  with wave.open(str(voice),'wb') as audio:audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(48000);audio.writeframes(b'\0\0'*48000)
  input_hashes={p.name:sha(p) for p in (still,voice)}
  value=json.loads((skill/'examples/brand-campaign.json').read_text());value['workflowId']='film-time-metadata';value['nodes']=[n for n in value['nodes'] if n['id']=='film'];node=value['nodes'][0];node['dependsOn']=[];node['providedAssets']=['still','voice']
  node['payload']['assetBindings']=[{'name':'still','assetId':'still'},{'name':'voice','assetId':'voice'}]
  operations=node['payload']['plan']['operations'];operations[0]['params']['asset']='still';operations[0]['as']='still';operations[2]['params']['item']={'$ref':'still.item'}
  plan=root/'plan.json';plan.write_text(json.dumps(value));authorization='film-metadata-scope'
  first=run('workflow.py',plan,'--output',project,'--authorization',authorization,'--asset','still='+str(still),'--asset','voice='+str(voice));self.assertEqual(first['state'],'review_ready')
  output=first['nodes']['film']['outputs'][0];metadata=output['technicalMetadata'];self.assertIn('durationTicks',metadata)
  self.assertEqual(metadata['durationTicks'],'254016000000');self.assertEqual(metadata['timeBase'],{'num':1,'den':254016000000});self.assertEqual(metadata['frameRate'],{'num':12,'den':1});self.assertEqual((metadata['width'],metadata['height'],metadata['alpha']),(320,180,False));self.assertEqual(metadata['audio'],{'sampleRate':48000,'channels':2})
  original_root=Path(first['nodes']['film']['root']);original=tree(original_root)
  for name in ('native.json','export-probe.json'):
   ref=next(r for r in output['evidenceRefs'] if r['location']==name);self.assertEqual(ref['sha256'],sha(original_root/name))
  setup=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(setup['skills'].keys(),{'filmcraft'})
  native=subprocess.run([setup['skills']['filmcraft']['executable'],'--project',str(original_root/'project.fcproj'),'inspect'],capture_output=True,text=True,env=environment,timeout=30);self.assertEqual(native.returncode,0,native.stderr);self.assertEqual(str(json.loads(native.stdout)['sequence']['duration']),metadata['durationTicks'])
  reused=run('workflow.py',plan,'--output',project,'--authorization',authorization,'--asset','still='+str(still),'--asset','voice='+str(voice));self.assertEqual(reused['nodes']['film']['status'],'reused');self.assertEqual(reused['nodes']['film']['taskId'],first['nodes']['film']['taskId']);self.assertEqual(reused['nodes']['film']['outputs'][0]['technicalMetadata'],metadata)
  value['revision']='caption-v2';node.pop('providedAssets');node['expectedRevision']=output['nativeProjectRef']['sha256'];node['externalInputs']=[{'root':str(original_root),'artifact':output}]
  node['payload']['sourceProject']={'assetId':output['assetId']};node['payload']['assetBindings']=[];node['payload']['plan']={'operations':[{'command':'captions.setStyle','params':{'track':'C1','size':72}}],'frames':['127008000000'],'export':{'audioRequired':True}}
  plan.write_text(json.dumps(value));second=run('workflow.py',plan,'--output',project,'--authorization',authorization);self.assertEqual(second['state'],'review_ready');self.assertEqual(second['nodes']['film']['outputs'][0]['technicalMetadata'],metadata);self.assertEqual(tree(original_root),original)
  package=root/'package';packed=run('package.py','create','--project',project,'--workflow',second['runKey'],'--output',package,'--authorization',authorization);moved=root/'moved package';package.rename(moved)
  verified=run('package.py','verify','--package',moved,'--sha',packed['sha256']);self.assertEqual(verified['state'],'review_ready');self.assertEqual(verified['children'][0]['outputs'][0]['technicalMetadata'],metadata);self.assertEqual(packed['sha256'],verified['sha256'])
  self.assertEqual(tree(skill),before);self.assertEqual(input_hashes,{p.name:sha(p) for p in (still,voice)})
  proof={'schema':'craft-film-time-metadata-first-use/v1','result':'PASS','runtimeVersion':setup['version'],'technicalMetadata':metadata,'first':first,'second':second,'packageSha256':packed['sha256'],'calls':calls,'sourceSkillHashes':before,'nativeReopenDuration':metadata['durationTicks'],'originalFilesPreserved':True,'inputsPreserved':True,'skillPreserved':True,'movedPackageVerified':True,'scope':'one copied execution skill, empty runtime, public downloads, native Film create/reopen/caption revision/reuse and moved package; large integer roundtrip separately tested; no long timeline render, GUI or creative acceptance'}
  (root/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':unittest.main()
