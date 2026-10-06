"""真实 EffectCraft 参数拒绝跨 ArtCraft 调度、查询与局部恢复传播。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
ROOT=Path(__file__).resolve().parents[1]

def hashes(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

@unittest.skipUnless(os.environ.get('CRAFT_EFFECT_MAPPING_MIXED_FIRST_USE')=='1','requires public native domain runtimes')
class EffectMappingMixedFirstUse(unittest.TestCase):
 def test_failed_effect_blocks_film_persists_query_and_corrected_revision_reuses_upstream(self):
  with tempfile.TemporaryDirectory(dir=os.environ.get('CRAFT_MAPPING_TEST_PARENT')) as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-cli-execute'
   shutil.copytree(Path(os.environ.get('CRAFT_INSTALLED_MAPPING_ART_SKILL',ROOT/'skills/artcraft-cli-execute')),skill,ignore=shutil.ignore_patterns('__pycache__'))
   skill_before=hashes(skill);runtime=root/'empty-runtime';project=root/'project';self.assertFalse(runtime.exists())
   voice=root/'voice.wav'
   with wave.open(str(voice),'wb') as stream:
    stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(48000);stream.writeframes(struct.pack('<h',7000)*48000)
   voice_sha=hashlib.sha256(voice.read_bytes()).hexdigest()
   plan=json.loads((skill/'examples/brand-token-campaign.json').read_text());intro=next(n for n in plan['nodes'] if n['id']=='intro')
   # 原实例已有图像素材图层；对同层应用受支持效果时故意携带非法字段。
   layer_operation=next(op for op in intro['payload']['plan']['operations'] if op['command']=='layer.addItem')
   alias=layer_operation['as'];bad={'command':'effect.apply','params':{'effect':'Gaussian Blur','layers':[{'$ref':alias+'.layer'}],'private_parameter_field':12}}
   intro['payload']['plan']['operations'].append(bad)
   path=root/'plan.json'
   def run(script,args):
    argv=[sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime)]
    if os.environ.get('CRAFT_MAPPING_BUNDLE_DIR'):argv+=['--bundle-dir',os.environ['CRAFT_MAPPING_BUNDLE_DIR']]
    return subprocess.run(argv+list(map(str,args)),capture_output=True,text=True,env=dict(os.environ,PATH='/usr/bin:/bin'),timeout=600)
   def workflow(value,success):
    path.write_text(json.dumps(value));result=run('workflow.py',[path,'--output',project,'--authorization','mapping-mixed-first-use','--asset','voice='+str(voice)])
    if success:self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
    self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
    try:return json.loads(json.loads(result.stdout)['error'])
    except (ValueError,KeyError,TypeError):self.fail('unexpected workflow failure: '+str(result.returncode)+' '+result.stdout+' '+result.stderr)
   failed=workflow(plan,False);self.assertEqual(failed['state'],'failed');node=failed['nodes']['intro'];self.assertEqual(node['status'],'failed');self.assertEqual(node['outputs'],[])
   diag=node['failure']['diagnostics']
   if os.environ.get('CRAFT_MAPPING_MIXED_FAILURE_EVIDENCE'):
    with Path(os.environ['CRAFT_MAPPING_MIXED_FAILURE_EVIDENCE']).open('x') as stream:json.dump({'schema':'artcraft-mapping-propagation-failure/v1','diagnostics':diag,'state':failed['state'],'introFailed':node['status']=='failed','filmBlocked':failed['nodes']['film']['status']=='blocked','scope':'single copied source skill; public runtime dev.48 and fixed Effect dev.7 native rejection'},stream,indent=2)
   self.assertEqual(diag['domainCode'],'unsupported_mapping');self.assertEqual(diag['source'],'stdout');self.assertTrue(diag['stdout']['complete']);self.assertNotIn('private_parameter_field',json.dumps(diag))
   self.assertEqual(failed['nodes']['film']['status'],'blocked');self.assertFalse(failed['nodes']['film'].get('taskId'))
   originals={name:hashes(Path(failed['nodes'][name]['root'])) for name in ('logo','poster','badge')}
   status_args=['--','status','--database',project/'tasks.sqlite','--task',node['taskId']]
   queried=run('cli.py',status_args);self.assertEqual(queried.returncode,2,queried.stdout+queried.stderr);status=json.loads(queried.stdout);self.assertEqual(status['error']['diagnostics'],diag)
   again=workflow(plan,False);self.assertEqual(again['budget'],failed['budget']);self.assertEqual(again['nodes']['intro']['taskId'],node['taskId']);self.assertEqual(again['nodes']['intro']['failure']['diagnostics'],diag)
   self.assertEqual(json.loads(run('cli.py',status_args).stdout)['attemptId'],status['attemptId'])
   plan['revision']='v2';del bad['params']['private_parameter_field'];good=workflow(plan,True);self.assertEqual(good['state'],'review_ready')
   self.assertNotEqual(good['nodes']['intro']['taskId'],node['taskId'])
   for name,before in originals.items():
    self.assertEqual(good['nodes'][name]['taskId'],failed['nodes'][name]['taskId']);self.assertEqual(hashes(Path(good['nodes'][name]['root'])),before)
   package=root/'package';packed=run('package.py',['create','--project',project,'--workflow',good['runKey'],'--authorization','mapping-mixed-first-use','--output',package]);self.assertEqual(packed.returncode,0,packed.stdout+packed.stderr);receipt=json.loads(packed.stdout)
   checked=run('package.py',['verify','--package',package,'--sha',receipt['sha256']]);self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr);self.assertEqual(len(json.loads(checked.stdout)['children']),5)
   installation=json.loads((project/'installation-receipt.json').read_text());self.assertEqual(installation['skills']['effectcraft']['runtimeIdentity']['pluginVersion'],'0.1.0-dev.7')
   self.assertEqual(hashes(skill),skill_before);self.assertFalse(list(skill.rglob('*.pyc')));self.assertEqual(hashlib.sha256(voice.read_bytes()).hexdigest(),voice_sha)
   if os.environ.get('CRAFT_MAPPING_MIXED_EVIDENCE'):
    proof={'schema':'artcraft-effect-mapping-mixed-first-use/v1','result':'passed','runtimeVersion':installation['version'],'effectRuntimeIdentity':installation['skills']['effectcraft']['runtimeIdentity'],'diagnostics':diag,'failedTaskId':node['taskId'],'failedAttemptId':status['attemptId'],'correctedTaskId':good['nodes']['intro']['taskId'],'reusedNodes':['logo','poster','badge'],'downstreamBlockedBeforeCorrection':True,'repeatAttemptDiagnosticsAndBudgetPreserved':True,'priorFilesVoiceAndSkillPreserved':True,'packageChildren':5,'runtimeMode':'explicit local bundles' if os.environ.get('CRAFT_MAPPING_BUNDLE_DIR') else 'default public download'}
    with Path(os.environ['CRAFT_MAPPING_MIXED_EVIDENCE']).open('x') as stream:json.dump(proof,stream,indent=2)

if __name__=='__main__':unittest.main()
