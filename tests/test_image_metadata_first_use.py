"""独立技能公开安装后的三领域图片交接；不证明创作或颜色保真。"""
import hashlib,json,os,shutil,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_IMAGE_METADATA_FIRST_USE')=='1','requires public image metadata runtime')
class ImageMetadataFirstUseTests(unittest.TestCase):
 def test_public_images_revise_reuse_and_move_with_actual_facts(self):
  root=Path(os.environ['CRAFT_IMAGE_METADATA_OUTPUT']);self.assertTrue(root.is_absolute());root.mkdir(parents=True,exist_ok=False)
  source=Path(os.environ.get('CRAFT_IMAGE_METADATA_SKILL',ROOT/'skills/artcraft-cli-execute'));skill=root/'.agents/skills'/source.name;shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
  def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
  def tree(path):return {str(p.relative_to(path)):sha(p) for p in path.rglob('*') if p.is_file()}
  before=tree(skill);runtime=root/'empty runtime';project=root/'project';self.assertFalse(runtime.exists());calls=[]
  decoder=shutil.which('ffprobe');self.assertIsNotNone(decoder)
  environment=dict(os.environ,PATH='/usr/bin:/bin')
  for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
  def run(script,*args):
   argv=[sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)]
   result=subprocess.run(argv,env=environment,capture_output=True,text=True,timeout=600)
   log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr);calls.append({'argv':argv,'cwd':str(Path.cwd()),'exitCode':result.returncode,'logSha256':sha(log)})
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
  value=json.loads((skill/'examples/brand-campaign.json').read_text());value['workflowId']='image-metadata';value['nodes']=[n for n in value['nodes'] if n['id']!='film']
  poster=next(n for n in value['nodes'] if n['id']=='poster');poster['payload']['plan']['exports'].append({'format':'jpg'});poster['payload']['outputs'].append({'assetId':'poster-jpeg','location':'design.jpg','mediaType':'image/jpeg'})
  intro=next(n for n in value['nodes'] if n['id']=='intro');intro['payload']['plan']['exports']=[];intro['payload']['outputs']=[{'assetId':'intro-preview','location':'frame-0001.png','mediaType':'image/png'}]
  plan=root/'plan.json';plan.write_text(json.dumps(value));authorization='image-metadata-scope'
  def check_images(nodes):
   facts=[]
   for name,node in nodes.items():
    for output in node['outputs']:
     if output['mediaType'] not in ('image/png','image/jpeg'):continue
     file=Path(node['root'])/output['location'];self.assertEqual(sha(file),output['sha256'])
     decoded=subprocess.run([decoder,'-v','error','-show_streams','-of','json',str(file)],capture_output=True,text=True,timeout=30);self.assertEqual(decoded.returncode,0,decoded.stderr)
     stream=json.loads(decoded.stdout)['streams'][0];meta=output['technicalMetadata']
     self.assertEqual(set(meta),{'width','height','bitDepth','alpha'});self.assertEqual((meta['width'],meta['height']),(stream['width'],stream['height']));self.assertEqual(meta['bitDepth'],8)
     if output['mediaType']=='image/png':self.assertIn(stream['pix_fmt'],('rgb24','rgba'))
     self.assertEqual(meta['alpha'],output['mediaType']=='image/png' and stream['pix_fmt']=='rgba')
     self.assertTrue(output['nativeProjectRef']);self.assertTrue(output['lossReportRef'])
     facts.append({'node':name,'artifact':output,'decodedPixelFormat':stream['pix_fmt']})
   self.assertEqual(len(facts),4);return facts
  first=run('workflow.py',plan,'--output',project,'--authorization',authorization);self.assertEqual(first['state'],'review_ready');initial=check_images(first['nodes'])
  original={name:tree(Path(node['root'])) for name,node in first['nodes'].items()}
  reused=run('workflow.py',plan,'--output',project,'--authorization',authorization)
  for name,node in reused['nodes'].items():self.assertEqual(node['taskId'],first['nodes'][name]['taskId']);self.assertEqual(node['status'],'reused');self.assertEqual(node['outputs'],first['nodes'][name]['outputs'])
  value['revision']='v2'
  changed_colors=0
  for operation in value['nodes'][0]['payload']['plan']['operations']:
   if operation['command']=='paint.setFill' and 'color' in operation.get('params',{}):
    operation['params']['color']='#ef5b36' if operation['params']['color']!='#ef5b36' else '#2366e8';changed_colors+=1
  self.assertGreater(changed_colors,0)
  plan.write_text(json.dumps(value));second=run('workflow.py',plan,'--output',project,'--authorization',authorization);self.assertEqual(second['state'],'review_ready');revised=check_images(second['nodes'])
  for name,node in second['nodes'].items():
   self.assertNotEqual(node['taskId'],first['nodes'][name]['taskId']);self.assertNotEqual(node['outputs'][0]['sha256'],first['nodes'][name]['outputs'][0]['sha256']);self.assertEqual(tree(Path(first['nodes'][name]['root'])),original[name])
  package=root/'package';packed=run('package.py','create','--project',project,'--workflow',second['runKey'],'--output',package,'--authorization',authorization);moved=root/'moved package';package.rename(moved)
  verified=run('package.py','verify','--package',moved,'--sha',packed['sha256']);self.assertEqual(verified['state'],'review_ready');self.assertEqual(len(verified['children']),3)
  packaged=check_images({child['nodeId']:child for child in verified['children']})
  def metadata_map(items):return {(item['node'],item['artifact']['assetId']):item['artifact']['technicalMetadata'] for item in items}
  self.assertEqual(metadata_map(packaged),metadata_map(revised))
  self.assertEqual(tree(skill),before);setup=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(set(setup['skills']),{'photocraft','vectorcraft','effectcraft'})
  self.assertEqual(setup['version'],json.loads((skill/'scripts/distribution.lock.json').read_text())['version'])
  proof={'schema':'craft-image-metadata-first-use/v1','result':'PASS','runtimeVersion':setup['version'],'calls':calls,'initialImages':initial,'revisedImages':revised,'packagedImages':packaged,'first':first,'second':second,'packageSha256':packed['sha256'],'skillHashes':before,'originalFilesPreserved':True,'skillPreserved':True,'scope':'single copied skill; empty runtime; default public downloads; three native domains; independent decode; Logo revision; reuse; moved package; no creative or color-fidelity acceptance'}
  (root/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':unittest.main()
