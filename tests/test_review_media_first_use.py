"""当前固定审阅技能：真实电影解码与损坏媒体拒绝；不冒充审美验收。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import struct
import zlib

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

@unittest.skipUnless(os.environ.get('CRAFT_REVIEW_MEDIA_FIRST_USE')=='1','requires public native Film runtime and existing ffmpeg')
class ReviewMediaFirstUseTests(unittest.TestCase):
 def test_undecodable_movie_cannot_be_accepted_using_positive_visual_observation(self):
  root=Path(os.environ['CRAFT_REVIEW_MEDIA_OUTPUT']).resolve();root.mkdir(parents=True,exist_ok=False)
  source=Path(os.environ.get('CRAFT_INSTALLED_REVIEW_SKILL_ROOT',ROOT/'skills/artcraft-cli-review'))
  skill=root/'.agents/skills/artcraft-cli-review';shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
  before={str(f.relative_to(skill)):sha(f) for f in skill.rglob('*') if f.is_file()}
  env=dict(os.environ,PATH='/usr/bin:/bin')
  for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):env.pop(key,None)
  runtime=root/'public-runtime';project=root/'project';calls=[]
  def run(script,*args,success=True):
   result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)],env=env,capture_output=True,text=True,timeout=600)
   log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr)
   calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(log)})
   self.assertEqual(result.returncode,0 if success else 1,result.stdout+result.stderr)
   return json.loads(result.stdout)
  plan={'workflowId':'review-media-boundary','revision':'v1','budget':{'currency':'USD','maxMinorUnits':0,'maxRevisions':0,'maxExternalCalls':0},'nodes':[{'id':'film','dependsOn':[],'projectKey':'film','pluginId':'filmcraft','expectedRevision':None,'payload':{'schemaVersion':'craft-skill-workflow/v1','plan':{'document':{'name':'Review media gate','width':96,'height':64,'frameRate':{'num':12,'den':1}},'operations':[],'frames':['0'],'export':{'audioRequired':False}},'assetBindings':[],'outputs':[{'assetId':'film-video','location':'film.mp4','mediaType':'video/mp4'}]}}]}
  # 测试夹具通过已有素材导入工作流生成短片；完整反射命令另走 domain_commands。
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  still=root/'still.png';still.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\0\0'*96)*64))+chunk(b'IEND',b''))
  node=plan['nodes'][0];node['providedAssets']=['still'];node['payload']['assetBindings']=[{'name':'still','assetId':'still'}]
  node['payload']['plan']['operations']=[{'command':'asset.import','params':{'asset':'still'},'as':'still'},{'command':'timeline.place','params':{'item':{'$ref':'still.item'},'track':'V1','time':'0','sourceIn':'0','duration':'254016000000','insert':False}}]
  path=root/'plan.json';path.write_text(json.dumps(plan));auth='review-media-test-scope'
  first=run('workflow.py',path,'--output',project,'--authorization',auth,'--asset','still='+str(still))
  self.assertEqual(first['state'],'review_ready')
  folder=root/'package';packed=run('package.py','create','--project',project,'--workflow',first['runKey'],'--output',folder,'--authorization',auth)
  package=run('package.py','verify','--package',folder,'--sha',packed['sha256'])
  child=package['children'][0];artifact=child['outputs'][0]
  movie=folder/child['root']/artifact['location']
  decoder=Path(os.environ['CRAFT_REVIEW_FFMPEG']).resolve(strict=True)
  def decode(file):return subprocess.run([str(decoder),'-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True,timeout=30)
  decoded=decode(movie);self.assertEqual(decoded.returncode,0,decoded.stderr)
  evidence=root/'decoder.json';evidence.write_text(json.dumps({'tool':'ffmpeg','executableSha256':sha(decoder),'assetSha256':sha(movie),'returnCode':decoded.returncode,'stderr':decoded.stderr}))
  target={k:artifact[k] for k in ('assetId','version','sha256')};target['nodeId']='film'
  checks=[{'id':dim,'dimension':dim,'status':'PASS','evaluator':{'kind':'tool','id':'ffmpeg' if dim=='technical' else 'declared-visual-fixture','version':'fixed-test'},'target':target,'evidence':[{'location':'decoder.json','sha256':sha(evidence)}],'note':'Actual full decode' if dim=='technical' else 'Positive fixture declaration only; no aesthetic acceptance'} for dim in ('technical','creative')]
  value={'schema':'craft-review-input/v1','packageSha256':packed['sha256'],'planSha256':package['workflow']['planSha256'],'ownerId':package['workflow']['ownerId'],'authorizationRef':auth,'brandReferences':[],'checks':checks}
  inputfile=root/'review-input.json';inputfile.write_text(json.dumps(value));ledger=sha(project/'tasks.sqlite')
  review=run('review.py','record','--package',folder,'--package-sha',packed['sha256'],'--input',inputfile,'--output',root/'valid-review')
  self.assertEqual(review['decision'],'pending');self.assertEqual(review['dimensions']['acceptance'],'NOT_RUN')
  originals={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}
  corrupt=root/'corrupt-package';shutil.copytree(folder,corrupt)
  badmovie=corrupt/movie.relative_to(folder);badmovie.write_bytes(b'undecodable movie')
  rejected_decode=decode(badmovie);self.assertNotEqual(rejected_decode.returncode,0)
  (root/'decode-failure.log').write_text(rejected_decode.stdout+rejected_decode.stderr)
  refused=run('review.py','record','--package',corrupt,'--package-sha',packed['sha256'],'--input',inputfile,'--output',root/'must-not-exist',success=False)
  self.assertFalse((root/'must-not-exist').exists());self.assertIn('package',refused['error'])
  self.assertEqual(sha(project/'tasks.sqlite'),ledger)
  self.assertEqual({str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()},originals)
  self.assertEqual(before,{str(f.relative_to(skill)):sha(f) for f in skill.rglob('*') if f.is_file()})
  self.assertTrue(all(not (runtime/name).exists() for name in ('effectcraft','photocraft','vectorcraft')))
  proof={'schema':'craft-review-media-first-use/v1','result':'PASS','workflow':first,'packageSha256':packed['sha256'],'review':review,'rejection':refused,'validMovieDecodeExit':0,'invalidMovieDecodeExit':rejected_decode.returncode,'decodeFailureLogSha256':sha(root/'decode-failure.log'),'packageAndLedgerPreserved':True,'installedSkillPreserved':True,'calls':calls,'scope':'real fixed installed Film creation/export and full decode; corrupt copied movie cannot bypass package gate using positive fixture observation; no automatic or human aesthetic acceptance'}
  (root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':unittest.main()
