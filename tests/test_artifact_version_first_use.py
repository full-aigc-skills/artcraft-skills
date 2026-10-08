"""独立固定技能的原生创建、不可变版本拒绝与有效新版本；不证明创作质量。"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('CRAFT_INSTALLED_ARTIFACT_SKILL_ROOT',ROOT/'skills/artcraft-cli-execute'))


@unittest.skipUnless(os.environ.get('CRAFT_ARTIFACT_VERSION_FIRST_USE')=='1','requires public pinned native downloads')
class ArtifactVersionFirstUseTests(unittest.TestCase):
 def test_native_revisions_refuse_mutable_versions_and_preserve_budget_and_deliveries(self):
  retained=os.environ.get('CRAFT_ARTIFACT_VERSION_OUTPUT')
  if retained:
   root=Path(retained);self.assertTrue(root.is_absolute());root.mkdir(parents=True,exist_ok=False);context=contextlib.nullcontext(str(root))
  else:context=tempfile.TemporaryDirectory(prefix='artcraft-artifact-version-')
  with context as temporary:
   root=Path(temporary);skill=root/'single execute skill';shutil.copytree(SOURCE,skill,ignore=shutil.ignore_patterns('__pycache__'))
   runtime=root/'empty runtime';project=root/'project';self.assertFalse(runtime.exists());calls=[]
   environment=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
   def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
   def skill_hashes():return {str(p.relative_to(skill)):sha(p) for p in skill.rglob('*') if p.is_file()}
   installed_before=skill_hashes()
   def run(script,*args,success=True):
    command=[sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(runtime)]
    result=subprocess.run(command,env=environment,capture_output=True,text=True,timeout=600)
    output=root/('call-%02d.log'%len(calls));output.write_text(result.stdout+result.stderr)
    calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(output)})
    if success:self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    else:self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
    return json.loads(result.stdout)
   def state():
    with sqlite3.connect(project/'tasks.sqlite') as database:
     names=[row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
     return {name:database.execute('SELECT * FROM "'+name+'" ORDER BY rowid').fetchall() for name in names}
   def deliveries():return {str(p.relative_to(project)):sha(p) for p in (project/'outputs').rglob('*') if p.is_file()}
   value=json.loads((skill/'examples/brand-campaign.json').read_text());value['workflowId']='immutable-artifact-first-use';value['budget']['maxRevisions']=4
   value['nodes']=[node for node in value['nodes'] if node['id']=='logo'];path=root/'plan.json'
   def execute(authorization='immutable-scope',success=True):
    path.write_text(json.dumps(value));return run('workflow.py',path,'--output',project,'--authorization',authorization,success=success)
   first=execute();self.assertEqual(first['state'],'review_ready');original=deliveries();old=first['nodes']['logo']['outputs'][0]
   value['revision']='orange-v2'
   for operation in value['nodes'][0]['payload']['plan']['operations']:
    params=operation.get('params',{})
    if 'color' in params:params['color']='#ef5b36'
   second=execute();self.assertEqual(second['state'],'review_ready');new=second['nodes']['logo']['outputs'][0];self.assertNotEqual(old['sha256'],new['sha256']);self.assertNotEqual(old['version'],new['version'])
   self.assertTrue(all(deliveries()[name]==digest for name,digest in original.items()))
   setup=json.loads((project/'installation-receipt.json').read_text());expected=os.environ.get('CRAFT_EXPECTED_ARTIFACT_VERSION_RUNTIME','0.1.0-dev.124-runtime.1');self.assertEqual(setup['version'],expected)
   self.assertEqual(setup['skills'].keys(),{'vectorcraft'})
   before=state();files_before=deliveries();conflict=json.loads(json.dumps(new));conflict['version']=old['version'];conflict['assetId']=old['assetId'];refusals=[]
   value['nodes'][0]['payload']['assetBindings']=[{'name':'registered','assetId':old['assetId']}]
   value['nodes'][0]['payload']['plan']['operations'].append({'command':'asset.place','params':{'asset':'registered','rect':[360,64,80,80]},'as':'registeredInput'})
   value['nodes'][0]['externalInputs']=[{'root':second['nodes']['logo']['root'],'artifact':conflict}]
   for revision,authorization in [('invalid-v3','immutable-scope'),('invalid-v3','immutable-scope'),('invalid-other-scope','other-scope')]:
    value['revision']=revision;reply=execute(authorization,success=False);self.assertEqual(reply['errorDetail']['code'],'artifact_version_conflict');self.assertEqual(state(),before);self.assertEqual(deliveries(),files_before);refusals.append(reply['errorDetail'])
   value['revision']='valid-v3';value['nodes'][0]['externalInputs'][0]['artifact']=new
   accepted=execute();self.assertEqual(accepted['state'],'review_ready');self.assertNotEqual(accepted['nodes']['logo']['taskId'],second['nodes']['logo']['taskId'])
   repeated=execute();self.assertEqual(repeated['nodes']['logo']['status'],'reused');self.assertEqual(repeated['nodes']['logo']['taskId'],accepted['nodes']['logo']['taskId']);self.assertEqual(repeated['budget'],accepted['budget'])
   self.assertTrue(all(deliveries()[name]==digest for name,digest in files_before.items()));self.assertEqual(skill_hashes(),installed_before)
   with sqlite3.connect(project/'tasks.sqlite') as database:
    self.assertEqual(database.execute('SELECT COUNT(*) FROM tasks').fetchone()[0],3);self.assertEqual(database.execute('SELECT COUNT(*) FROM leases').fetchone()[0],0)
   if retained:
    proof={'schema':'craft-artifact-version-installed-first-use/v1','result':'PASS','runtimeVersion':setup['version'],'sourceSkillHashes':installed_before,'calls':calls,'nativeVersions':[{'taskId':receipt['nodes']['logo']['taskId'],'assetId':receipt['nodes']['logo']['outputs'][0]['assetId'],'version':receipt['nodes']['logo']['outputs'][0]['version'],'sha256':receipt['nodes']['logo']['outputs'][0]['sha256']} for receipt in (first,second,accepted)],'refusals':refusals,'tablesPreserved':len(before),'filesPreserved':len(files_before),'validNewVersion':True,'replayTaskAndBudgetPreserved':True,'zeroLeases':True,'publicColdInstallation':True,'skillPreserved':True,'scope':'Single copied installed execution skill, public downloads, real Vector native creation and revisions; cross-scope refusal before new budget/task; no GUI or creative acceptance'}
    (root/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':unittest.main()
