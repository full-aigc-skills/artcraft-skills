"""独立 Art 技能的四领域字体缺失状态与移动源重开；原生验收显式启用。"""
from contextlib import nullcontext
import hashlib,json,math,os,shutil,struct,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('CRAFT_INSTALLED_FONT_ART_SKILL',str(ROOT/'skills/artcraft-use')))
@unittest.skipUnless(os.environ.get('CRAFT_FONT_FIRST_USE')=='1','requires explicit installed skill and pinned public native runtimes')
class FontDependenciesFirstUse(unittest.TestCase):
 def test_four_domains_keep_missing_font_states_after_package_move_and_source_reopen(self):
  retained=os.environ.get('CRAFT_FONT_RETAIN_ROOT')
  if retained:Path(retained).resolve().mkdir(parents=True,exist_ok=False)
  with (nullcontext(str(Path(retained).resolve())) if retained else tempfile.TemporaryDirectory()) as temporary:
   root=Path(temporary);skill=root/'.agents/skills/artcraft-use';shutil.copytree(SOURCE,skill,ignore=shutil.ignore_patterns('__pycache__'))
   sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
   inventory=lambda:{p.relative_to(skill).as_posix():sha(p) for p in skill.rglob('*') if p.is_file()}
   before=inventory();runtime=Path(os.environ.get('CRAFT_FONT_RUNTIME_HOME',str(root/'empty-runtime')));warm=runtime.exists();project=root/'project';calls=[]
   env=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ['CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME']:env.pop(key,None)
   def run(script,*args):
    result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/script),'--runtime-home',str(runtime),*map(str,args)],env=env,capture_output=True,text=True,timeout=600)
    log=root/('call-%02d.log'%len(calls));log.write_text(result.stdout+result.stderr);calls.append({'script':script,'exitCode':result.returncode,'logSha256':sha(log)})
    self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
   voice=root/'voice.wav'
   with wave.open(str(voice),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(b''.join(struct.pack('<h',round(5000*math.sin(i*2*math.pi*440/48000))) for i in range(48000)))
   voice_before=sha(voice)
   plan=json.loads((skill/'examples/brand-campaign.json').read_text());plan['workflowId']='four-domain-fonts';intro=next(n for n in plan['nodes'] if n['id']=='intro')
   intro['payload']['plan']['operations'].append({'command':'layer.newText','params':{'name':'Font title','text':'NOVA','font':'Arial','size':20,'position':[30,50]},'as':'fontTitle'})
   path=root/'create-plan.json';path.write_text(json.dumps(plan));first=run('workflow.py',path,'--output',project,'--authorization','font-first-use','--asset','voice='+str(voice));self.assertEqual(first['state'],'review_ready')
   reused=run('workflow.py',path,'--output',project,'--authorization','font-first-use','--asset','voice='+str(voice));self.assertEqual(reused['state'],'review_ready');self.assertTrue(all(node['status']=='reused' for node in reused['nodes'].values()))
   def fonts(output):
    deps=[d for d in output['dependencies'] if d['kind']=='font'];self.assertTrue(deps)
    for dep in deps:
     self.assertIsNone(dep['assetRef']);self.assertFalse(dep['packaged']);self.assertEqual(dep['missingReason'],'font_file_not_collected');self.assertEqual(dep['fontRequirement']['nativeProjectSha256'],output['nativeProjectRef']['sha256']);self.assertIn(dep['fontRequirement']['inspectionRef'],output['evidenceRefs'])
    return sorted(d['fontRequirement']['family'] for d in deps)
   required={node['id']:fonts(first['nodes'][node['id']]['outputs'][0]) for node in plan['nodes']}
   self.assertEqual(required,{'logo':['Source Sans 3'],'poster':['Arial'],'intro':['Arial'],'film':['Arial']})
   original={str(p.relative_to(project)):sha(p) for p in (project/'outputs').rglob('*') if p.is_file()}
   packed=run('package.py','create','--project',project,'--workflow',first['runKey'],'--authorization','font-first-use','--output',root/'package');shutil.move(root/'package',root/'moved');verified=run('package.py','verify','--package',root/'moved','--sha',packed['sha256']);self.assertEqual(len(verified['children']),4)
   reopen={'workflowId':plan['workflowId'],'revision':'reopen-v2','budget':dict(plan['budget']),'nodes':[]}
   for child in verified['children']:
    original_node=next(n for n in plan['nodes'] if n['id']==child['nodeId']);old=child['outputs'][0];domain=original_node['pluginId'];native_plan=original_node['payload']['plan'];new_plan={'operations':[]}
    for key in ['exports','frames','export']:
     if key in native_plan:new_plan[key]=native_plan[key]
    reopen['nodes'].append({'id':child['nodeId'],'dependsOn':[],'projectKey':'reopen-'+child['nodeId'],'pluginId':domain,'expectedRevision':old['nativeProjectRef']['sha256'],'externalInputs':[{'root':child['root'],'artifact':old}],'payload':{'schemaVersion':'craft-skill-workflow/v1','sourceProject':{'assetId':old['assetId']},'plan':new_plan,'assetBindings':[],'outputs':[{**o,'assetId':o['assetId']+'-reopened'} for o in original_node['payload']['outputs']]}})
   path=root/'reopen-plan.json';path.write_text(json.dumps(reopen));second=run('workflow.py',path,'--output',project,'--authorization','font-first-use');self.assertEqual(second['state'],'review_ready')
   self.assertEqual({n['id']:fonts(second['nodes'][n['id']]['outputs'][0]) for n in reopen['nodes']},required)
   second_package=run('package.py','create','--project',project,'--workflow',second['runKey'],'--authorization','font-first-use','--output',root/'reopened-package');run('package.py','verify','--package',root/'reopened-package','--sha',second_package['sha256'])
   self.assertTrue(all(sha(project/name)==digest for name,digest in original.items()));self.assertEqual(sha(voice),voice_before);self.assertEqual(inventory(),before)
   installation=json.loads((project/'installation-receipt.json').read_text());expected=os.environ.get('CRAFT_FONT_EXPECTED_RUNTIME','0.1.0-dev.138-runtime.1');self.assertEqual(installation['version'],expected)
   if retained:(root/'proof.json').write_text(json.dumps({'schema':'artcraft-fonts-installed-first-use/v1','status':'passed','runtimeVersion':installation['version'],'warmRuntimeCache':warm,'fonts':required,'calls':calls,'initialResult':first,'reopenedResult':second,'packageSha256':packed['sha256'],'reopenedPackageSha256':second_package['sha256'],'sourceSkillHashes':before,'sourceAndSkillPreserved':True,'scope':'single isolated fixed skill, public pinned runtime installer, four native domains, moved package source reopen; not target font availability or host64 acceptance'},indent=2)+'\n')
