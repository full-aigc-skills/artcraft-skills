"""ArtCraft 单技能公开计划必须消费带保护检查的固定 PhotoCraft 技能源。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_PHOTO_PROTECTION_FIRST_USE')=='1','requires pinned public runtime downloads')
class PhotoProtectionFirstUse(unittest.TestCase):
 def test_protected_photo_source_revision_refuses_invalid_region_and_packages_valid_revision(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=Path(os.environ.get('CRAFT_INSTALLED_PHOTO_ART_SKILL_ROOT',ROOT/'skills/artcraft-use'));skill=root/'single-artcraft';shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'));runtime=root/'runtime';project=root/'project'
   def run(script,args):return subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)],capture_output=True,text=True,env={**os.environ,'PATH':'/usr/bin:/bin'},timeout=300)
   def workflow(plan):
    file=root/'plan.json';file.write_text(json.dumps(plan));return run('workflow.py',[file,'--output',project,'--authorization','photo-protection-scope'])
   stroke={'command':'paint.stroke','params':{'points':[[130,180],[135,180]],'size':12,'hardness':1,'opacity':1,'flow':1,'color':'#0033ff'}}
   domain={'document':{'name':'NOVA','width':320,'height':400,'background':'#faf4e8'},'minimumLayers':2,'operations':[{'command':'type.create','params':{'x':28,'y':60,'text':'NOVA','name':'Headline','font':'Arial','size':32,'color':'#192a3b'},'as':'headline'},{'command':'layer.new.layer','params':{'name':'Product'},'as':'product'},{'command':'paint.stroke','params':{'points':[[130,180],[135,180]],'size':60,'hardness':1,'opacity':1,'flow':1,'color':'#e96340'}}],'exports':[{'format':'png'}]}
   payload={'schemaVersion':'craft-skill-workflow/v1','plan':domain,'assetBindings':[],'outputs':[{'assetId':'poster-png','location':'design.png','mediaType':'image/png'}]}
   node={'id':'poster','pluginId':'photocraft','dependsOn':[],'projectKey':'poster','expectedRevision':None,'payload':payload}
   plan={'workflowId':'photo-protection','revision':'v1','budget':{'currency':'USD','maxMinorUnits':0,'maxExternalCalls':0,'maxRevisions':2},'nodes':[node]};first=workflow(plan);self.assertEqual(first.returncode,0,first.stdout+first.stderr);old=json.loads(first.stdout)['nodes']['poster'];old_root=Path(old['root']);original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old_root.iterdir() if p.is_file()};artifact=old['outputs'][0]
   plan['revision']='v2';node['expectedRevision']=artifact['nativeProjectRef']['sha256'];node['externalInputs']=[{'root':str(old_root),'artifact':artifact}];payload['sourceProject']={'assetId':'poster-png'};payload['plan']={'minimumLayers':2,'operations':[{'command':'type.edit','params':{'layer':{'$ref':'headline.layer'},'text':'NOVA PLUS'}}],'exports':[{'format':'png'}],'protectedRegions':[{'id':'header','rect':[0,0,320,100]}]}
   bad=workflow(plan);self.assertNotEqual(bad.returncode,0,bad.stdout+bad.stderr);failed=json.loads(json.loads(bad.stdout)['error']);self.assertEqual(failed['state'],'failed');self.assertEqual(failed['nodes']['poster']['status'],'failed');self.assertFalse(Path(failed['nodes']['poster']['root']).exists())
   self.assertEqual(original,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old_root.iterdir() if p.is_file()})
   plan['revision']='v3';payload['plan']['operations'].extend([{'command':'layer.select','params':{'layer':{'$ref':'product.layer'}}},stroke]);payload['plan']['protectedRegions']=[{'id':'footer','rect':[0,240,320,160]}];good=workflow(plan);self.assertEqual(good.returncode,0,good.stdout+good.stderr);result=json.loads(good.stdout);current=result['nodes']['poster'];report=json.loads((Path(current['root'])/'pixel-protection.json').read_text());self.assertEqual(report['regions'][0]['changedPixels'],0)
   operations=json.loads((Path(current['root'])/'operations.json').read_text());self.assertTrue(next(item['result']['damage'] for item in operations if item['arguments'].get('id')=='paint.stroke'))
   setup=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(set(setup['skills']),{'photocraft'});self.assertEqual(setup['skills']['photocraft']['runtimeIdentity']['pluginVersion'],json.loads((skill/'scripts/distribution.lock.json').read_text())['bundles']['photocraft-skills']['version'])
   package=root/'package';packed=run('package.py',['create','--project',project,'--workflow',result['runKey'],'--authorization','photo-protection-scope','--output',package]);self.assertEqual(packed.returncode,0,packed.stdout+packed.stderr);receipt=json.loads(packed.stdout);moved=root/'moved';package.rename(moved);checked=run('package.py',['verify','--package',moved,'--sha',receipt['sha256']]);self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
   child=json.loads(checked.stdout)['children'][0];self.assertEqual(json.loads((Path(child['root'])/'pixel-protection.json').read_text()),report);self.assertEqual(original,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old_root.iterdir() if p.is_file()});self.assertFalse(list(skill.rglob('*.pyc')))
   if os.environ.get('CRAFT_PHOTO_ART_EVIDENCE_FILE'):
    value={'schema':'craft-photo-protection-first-use/v1','runtimeVersion':setup['version'],'photoSourceVersion':setup['skills']['photocraft']['runtimeIdentity']['pluginVersion'],'photoSourceSha256':json.loads((skill/'scripts/distribution.lock.json').read_text())['bundles']['photocraft-skills']['sha256'],'originalFiles':original,'updatedManifest':json.loads((Path(current['root'])/'manifest.json').read_text()),'protection':report,'packageSha256':receipt['sha256'],'taskIds':[old['taskId'],failed['nodes']['poster']['taskId'],current['taskId']],'budget':result['budget'],'retouchStrokeRecorded':True,'scope':'single copied ArtCraft skill, online Photo-only install, generic worker failure on rejected region, valid native revision and moved package; no creative acceptance'}
    with Path(os.environ['CRAFT_PHOTO_ART_EVIDENCE_FILE']).open('x') as output:json.dump(value,output,ensure_ascii=False,indent=2);output.write('\n')

if __name__=='__main__':unittest.main()
