"""单独审阅技能的真实首次安装、可移动记录与失败边界。评价为测试观察，不证明创作质量。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('CRAFT_REVIEW_FIRST_USE')=='1','requires public native first-use downloads')
class ReviewFirstUseTests(unittest.TestCase):
 def test_single_review_skill_records_native_package_without_unrelated_installs(self):
  retained=os.environ.get('CRAFT_REVIEW_EVIDENCE_ROOT')
  if retained:Path(retained).mkdir(parents=True,exist_ok=False)
  with nullcontext(retained) if retained else tempfile.TemporaryDirectory(prefix='artcraft-review-first-use-') as d:
   root=Path(d);skill=root/'only review skill'
   installed=os.environ.get('CRAFT_INSTALLED_REVIEW_SKILL_ROOT')
   shutil.copytree(Path(installed) if installed else ROOT/'skills/artcraft-cli-review',skill,ignore=shutil.ignore_patterns('__pycache__'))
   skill_snapshot={p.relative_to(skill):p.read_bytes() for p in skill.rglob('*') if p.is_file()}
   runtime=root/'runtime';project=root/'project';authorization='review-fixture-scope';calls=[]
   environment=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
   def run(script,*args,ok=True,home=runtime):
    command=[sys.executable,'-I','-B',str(skill/'scripts'/script),*map(str,args),'--runtime-home',str(home)]
    result=subprocess.run(command,env=environment,capture_output=True,text=True,timeout=600)
    if retained:
     log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr)
     calls.append({'script':script,'exitCode':result.returncode,'logSha256':hashlib.sha256(log.read_bytes()).hexdigest()})
    if ok:self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    else:self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
    return json.loads(result.stdout)
   plan=json.loads((skill/'examples/brand-campaign.json').read_text());plan['nodes']=[n for n in plan['nodes'] if n['id']=='logo']
   plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan))
   made=run('workflow.py',plan_path,'--output',project,'--authorization',authorization)
   packed=run('package.py','create','--project',project,'--workflow',made['runKey'],'--output',root/'package','--authorization',authorization)
   package=run('package.py','verify','--package',root/'package','--sha',packed['sha256'])
   snapshots={p:p.read_bytes() for p in (root/'package').rglob('*') if p.is_file()};ledger=(project/'tasks.sqlite').read_bytes()
   observation=root/'inspection.json';contents=b'{"scope":"fixture record validation only; no aesthetic acceptance"}\n';observation.write_bytes(contents)
   target=package['children'][0]['outputs'][0];ref={key:target[key] for key in ('assetId','version','sha256')};ref['nodeId']='logo'
   input={'schema':'craft-review-input/v1','packageSha256':packed['sha256'],'planSha256':package['workflow']['planSha256'],'ownerId':package['workflow']['ownerId'],'authorizationRef':authorization,'brandReferences':[ref.copy()],'checks':[{'id':'technical-fixture','dimension':'technical','status':'PASS','evaluator':{'kind':'tool','id':'fixture-observer','version':'1'},'target':ref,'evidence':[{'location':'inspection.json','sha256':hashlib.sha256(contents).hexdigest()}],'note':'Tests evidence binding only, not actual media quality'}]}
   source=root/'review-input.json';source.write_text(json.dumps(input))
   receipt=run('review.py','record','--package',root/'package','--package-sha',packed['sha256'],'--input',source,'--output',root/'review')
   self.assertEqual(receipt['decision'],'pending');self.assertEqual(receipt['dimensions']['creative'],'NOT_RUN');self.assertEqual(receipt['taskState'],'review_ready')
   moved=root/'moved review';(root/'review').rename(moved);movedpackage=root/'moved package';(root/'package').rename(movedpackage)
   clean=root/'verify runtime'
   checked=run('review.py','verify','--package',movedpackage,'--package-sha',packed['sha256'],'--review',moved,'--review-sha',receipt['sha256'],home=clean)
   self.assertEqual(checked['decision'],'pending')
   self.assertTrue(all(not (clean/n).exists() for n in ('filmcraft','effectcraft','photocraft','vectorcraft')))
   self.assertTrue(all(not (runtime/n).exists() for n in ('filmcraft','effectcraft','photocraft')))
   self.assertEqual((project/'tasks.sqlite').read_bytes(),ledger)
   for path,contents in snapshots.items():self.assertEqual((movedpackage/path.relative_to(root/'package')).read_bytes(),contents)
   # 新原生修订不能改写旧包或旧审阅，也不能将旧观察套用到新内容。
   old_output=made['nodes']['logo']['outputs'][0]
   old_root=Path(made['nodes']['logo']['root'])
   old_files={p.relative_to(old_root):p.read_bytes() for p in old_root.rglob('*') if p.is_file()}
   review_files={p.relative_to(moved):p.read_bytes() for p in moved.rglob('*') if p.is_file()}
   revised=json.loads(json.dumps(plan));revised['revision']='review-logo-v2'
   node=revised['nodes'][0];node['expectedRevision']=old_output['nativeProjectRef']['sha256']
   node['externalInputs']=[{'root':str(old_root),'artifact':old_output}]
   node['payload']['sourceProject']={'assetId':old_output['assetId']}
   node['payload']['plan'].pop('document')
   node['payload']['plan']['operations']=[{'command':'select.set','params':{'ids':{'$ref':'logo.ids'}}},{'command':'paint.setFill','params':{'color':'#ee6622'}}]
   revised_path=root/'revised-plan.json';revised_path.write_text(json.dumps(revised))
   changed=run('workflow.py',revised_path,'--output',project,'--authorization',authorization)
   self.assertEqual(changed['state'],'review_ready',changed)
   new_output=changed['nodes']['logo']['outputs'][0]
   self.assertEqual(new_output['assetId'],old_output['assetId'])
   self.assertNotEqual(new_output['version'],old_output['version'])
   self.assertNotEqual(new_output['sha256'],old_output['sha256'])
   repeated=run('workflow.py',revised_path,'--output',project,'--authorization',authorization)
   self.assertEqual(repeated['nodes']['logo']['taskId'],changed['nodes']['logo']['taskId'])
   self.assertEqual(repeated['budget'],changed['budget'])
   next_package=root/'revised-package'
   next_receipt=run('package.py','create','--project',project,'--workflow',changed['runKey'],'--output',next_package,'--authorization',authorization)
   old_checked=run('review.py','verify','--package',movedpackage,'--package-sha',packed['sha256'],'--review',moved,'--review-sha',receipt['sha256'],home=clean)
   self.assertEqual(old_checked['decision'],'pending')
   old_on_new=run('review.py','verify','--package',next_package,'--package-sha',next_receipt['sha256'],'--review',moved,'--review-sha',receipt['sha256'],home=clean,ok=False)
   self.assertIn('review_package_stale',old_on_new['error'])
   for path,contents in old_files.items():self.assertEqual((old_root/path).read_bytes(),contents)
   for path,contents in review_files.items():self.assertEqual((moved/path).read_bytes(),contents)
   for path,contents in snapshots.items():self.assertEqual((movedpackage/path.relative_to(root/'package')).read_bytes(),contents)
   input['checks'][0]['target']['version']='stale';source.write_text(json.dumps(input))
   bad=run('review.py','record','--package',movedpackage,'--package-sha',packed['sha256'],'--input',source,'--output',root/'stale-review',ok=False)
   self.assertIn('review_asset_stale',bad['error']);self.assertFalse((root/'stale-review').exists())
   next((moved/'evidence').iterdir()).write_text('tampered')
   bad=run('review.py','verify','--package',movedpackage,'--package-sha',packed['sha256'],'--review',moved,'--review-sha',receipt['sha256'],ok=False,home=clean)
   self.assertIn('review_record_file_mismatch',bad['error'])
   self.assertFalse(any(skill.rglob('*.pyc')))
   self.assertEqual({p.relative_to(skill):p.read_bytes() for p in skill.rglob('*') if p.is_file()},skill_snapshot)
   if retained:
    proof={'schema':'craft-current-review-record-acceptance/v1','result':'PASS','workflow':made,'packageReceipt':packed,'reviewReceipt':receipt,'movedVerification':checked,'ledgerAndPackagePreserved':True,'staleAssetRejected':True,'tamperedObservationRejected':True,'revisionWorkflow':changed,'repeatedRevision':repeated,'revisedPackageReceipt':next_receipt,'oldReviewAfterRevision':old_checked,'oldReviewOnNewPackageRejected':old_on_new,'oldDeliveryReviewAndPackagePreservedAfterRevision':True,'calls':calls,'scope':'actual fixed installed copied single review skill, public cold native Vector source revision plus separate cold runtime-only moved verification; old version review traceability; declared fixture feedback, no aesthetic or human acceptance'}
    (root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
   evidence=os.environ.get('CRAFT_REVIEW_ROLE_EVIDENCE_FILE')
   if evidence:
    record={'schema':'artcraft-review-role-first-use/v1','result':'PASS','packageSha256':packed['sha256'],'reviewSha256':receipt['sha256'],'decision':receipt['decision'],'creative':receipt['dimensions']['creative'],'ledgerPreserved':True,'nativePackagePreserved':True,'staleAssetRejected':True,'tamperedEvidenceRejected':True,'movedVerifyColdRuntime':True,'unrelatedDomainsNotInstalled':True}
    with open(evidence,'x',encoding='utf-8') as stream:
     json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
if __name__=='__main__':unittest.main()
