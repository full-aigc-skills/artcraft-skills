"""完整领域交接组件的合同；原生验收单独执行。"""
import importlib.util,json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/artcraft-use/scripts/domain_commands.py'
class DomainCommandsTests(unittest.TestCase):
 def module(self,script=SCRIPT):
  spec=importlib.util.spec_from_file_location('domain_commands',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_all_ten_single_skill_queries_need_no_install(self):
  expected={'filmcraft':666,'effectcraft':640,'photocraft':755,'vectorcraft':585}
  for original in sorted((ROOT/'skills').iterdir()):
   with tempfile.TemporaryDirectory() as temporary:
    target=Path(temporary)/'.agents/skills'/original.name;shutil.copytree(original,target);m=self.module(target/'scripts/domain_commands.py')
    with patch.object(m.subprocess,'run',side_effect=AssertionError('query installed dependencies')):
     index=m.load_index();self.assertEqual({d:len(v['commands']) for d,v in index.items()},expected)
     for d,entry in index.items():self.assertEqual(len({x['id'] for x in entry['commands']}),expected[d])
 def test_index_drift_and_unknown_domains_stop_before_install(self):
  with tempfile.TemporaryDirectory() as temporary:
   skill=Path(temporary)/'skill';shutil.copytree(SCRIPT.parent.parent,skill);p=skill/'references/domain-command-index.json';v=json.loads(p.read_text());v['domains']['filmcraft']['catalogText']+=' ';p.write_text(json.dumps(v));m=self.module(skill/'scripts/domain_commands.py')
   with self.assertRaisesRegex(ValueError,'command_index_identity'):m.load_index()
  with self.assertRaisesRegex(ValueError,'domain_unsupported'):self.module().domain_entry('jianying')
 def test_plan_preflight_rejects_unknown_aliases_and_nonfinite_values(self):
  m=self.module();entry=m.domain_entry('filmcraft')
  for plan in [{'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'x':float('inf')}}]}, {'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'x':{'$ref':'missing.id'}}}]}, {'schema':'craft-command-plan/v1','operations':[{'command':'not.registered','params':{}}]}]:
   with self.subTest(plan=repr(plan)),self.assertRaises(ValueError):m.validate_plan(plan,entry,{})
 def test_receipt_requires_actual_identity_and_all_successful_steps(self):
  m=self.module();plan={'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'Test'}}]};digest=hashlib.sha256(json.dumps(plan,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()
  row={'schema':'craft-command-receipt/v1','pluginId':'filmcraft','result':'PASS','planSha256':digest,'runtimeSha256':'a'*64,'catalogSha256':'b'*64,'steps':[{'index':0,'command':'file.newProject','tool':None,'state':'succeeded'}]}
  m.validate_receipt(row,'filmcraft',plan,'a'*64,'b'*64)
  for field,value in [('runtimeSha256','c'*64),('planSha256','c'*64),('pluginId','vectorcraft'),('result','unknown'),('steps',[{'index':0,'command':'file.newProject','state':'started'}])]:
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'outcome_unknown'):m.validate_receipt(dict(row,**{field:value}),'filmcraft',plan,'a'*64,'b'*64)
 def test_existing_output_is_refused_before_install(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);plan=root/'plan.json';plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'Test'}}]}));output=root/'output';output.mkdir();(output/'project.fcproj').write_bytes(b'original')
   args=m.parser().parse_args(['run','filmcraft',str(plan),'--output',str(output),'--runtime-home',str(root/'runtime')])
   with patch.object(m.subprocess,'run',side_effect=AssertionError('installed or executed')):
    with self.assertRaisesRegex(ValueError,'output_exists'):m.dispatch(args)
   self.assertEqual((output/'project.fcproj').read_bytes(),b'original');self.assertFalse((root/'runtime').exists())
 def test_strict_json_rejects_nested_duplicate_and_overflow(self):
  for text in ['{"x":1,"x":2}','{"x":{"a":1,"a":2}}','{"x":NaN}','{"x":1e999}']:
   with self.subTest(text=text),self.assertRaises(ValueError):self.module().json_value(text)
 def test_selected_public_handoff_preserves_unknown_and_rejects_bad_success(self):
  import subprocess
  cases=[(value,'file.newProject') for value in ['PASS','unknown','wrong-plan','tamper','changed-input']]+[('unknown','transcript.generate'),('FAIL','transcript.downloadModel')]
  for outcome,command_id in cases:
   with self.subTest(outcome=outcome,command=command_id),tempfile.TemporaryDirectory() as temporary:
    base=Path(temporary);art=base/'one Art skill';shutil.copytree(SCRIPT.parent.parent,art);m=self.module(art/'scripts/domain_commands.py');domain='filmcraft';entry=m.domain_entry(domain);catalog=entry['catalogSha256'];root=base/'one domain';(root/'scripts').mkdir(parents=True);(root/'references').mkdir();executable=base/'native';executable.write_bytes(b'fixture, not a native runtime');native_sha=hashlib.sha256(executable.read_bytes()).hexdigest();commands=root/'scripts/commands.py';commands.write_text('# fixture only');native=root/'scripts/runtime.lock.json';native.write_text(json.dumps({'artifacts':{'darwin-arm64':{'binarySha256':native_sha}}}));index=json.loads((art/'references/domain-command-index.json').read_text());(root/'references/command-coverage.json').write_text(index['domains'][domain]['catalogText']);(root/'references/native-command-snapshot.json').write_text(index['domains'][domain]['snapshotText']);lock=json.loads((art/'scripts/distribution.lock.json').read_text());prefix='skills/filmcraft-use/';lock['bundles']['filmcraft-skills']['files']={prefix+str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file()};(art/'scripts/distribution.lock.json').write_text(json.dumps(lock));version=lock['bundles']['filmcraft-skills']['version']
    setup={'schema':'artcraft-setup/v1','nodeExecutable':'fixture-node','entryPoint':'fixture-entry','runtimeHome':str(base/'runtime'),'skills':{domain:{'skillRoot':str(root),'executable':str(executable),'runtimeIdentity':{'pluginId':domain,'pluginVersion':version,'sha256':native_sha}}}}
    parameters={'name':'Fixture'} if command_id=='file.newProject' else {'model':'whisper-tiny'} if command_id=='transcript.downloadModel' else {}
    plan={'schema':'craft-command-plan/v1','operations':[{'command':command_id,'params':parameters}]};plan_file=base/'plan.json';plan_file.write_text(json.dumps(plan));output=base/'output';source=base/'source';source.write_bytes(b'original');argv=['run',domain,str(plan_file),'--output',str(output),'--runtime-home',str(base/'runtime')]
    if outcome=='changed-input':argv+=['--input','input='+str(source)]
    args=m.parser().parse_args(argv);calls=[]
    def run(argv,**kwargs):
     calls.append(argv)
     if argv[3].endswith('bootstrap.py'):
      self.assertEqual(argv[-2:],['--plugin',domain])
      if outcome=='changed-input':source.write_bytes(b'changed')
      return subprocess.CompletedProcess(argv,0,stdout=json.dumps(setup))
     self.assertEqual(Path(argv[3]).resolve(),(art/'scripts/native_contract.py').resolve());self.assertEqual(Path(argv[4]),root/'scripts/mcp_session.py');self.assertEqual(Path(argv[5]),commands);self.assertEqual(argv[6],'run');self.assertEqual(argv[argv.index('--runtime-home')+1],setup['runtimeHome']);output.mkdir();(output/'project.fcproj').write_bytes(b'fixture saved before reply');passed=outcome not in ['unknown','FAIL'];result={'schema':'craft-command-receipt/v1','pluginId':domain,'result':'PASS' if passed else outcome,'mode':'headless','planSha256':hashlib.sha256(json.dumps(plan,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest(),'runtimeSha256':native_sha,'catalogSha256':catalog,'inputs':{},'steps':[{'index':0,'command':command_id,'tool':None,'state':'succeeded' if passed else 'unknown' if outcome=='unknown' else 'failed'}]}
     if outcome=='wrong-plan':result['planSha256']='c'*64
     if outcome=='tamper':commands.write_text('changed installed helper')
     (output/('success.json' if passed else 'failure.json')).write_text(json.dumps(result))
     return subprocess.CompletedProcess(argv,0 if passed else 1)
    with patch.object(m.subprocess,'run',side_effect=run):
     if outcome in ['wrong-plan','tamper','changed-input']:
      with self.assertRaisesRegex(ValueError,'outcome_unknown'):m.dispatch(args)
     else:
      value,code=m.dispatch(args);self.assertEqual(value['result'],outcome);self.assertEqual(value['dagDeliveryAcceptance'],'NOT_RUN');self.assertEqual(code,0 if outcome=='PASS' else 1);self.assertTrue((output/m.MARKER).is_file())
    self.assertEqual(len(calls),1 if outcome=='changed-input' else 2)
    if outcome!='changed-input':
     self.assertEqual((output/'project.fcproj').read_bytes(),b'fixture saved before reply')
     with patch.object(m.subprocess,'run',side_effect=AssertionError('replayed')):
      with self.assertRaisesRegex(ValueError,'output_exists'):m.dispatch(args)
 def test_tool_describe_preserves_actual_native_schema_without_install(self):
  m=self.module()
  for domain,entry in m.load_index().items():
   self.assertEqual({x['name'] for x in entry['toolSchemas']},set(entry['nativeTools']))
   tool=entry['toolSchemas'][0];args=m.parser().parse_args(['describe',domain,tool['name'],'--tool'])
   with patch.object(m.subprocess,'run',side_effect=AssertionError('query installed')):result,code=m.dispatch(args)
   self.assertEqual(code,0);self.assertEqual(result,{'domain':domain,**tool})
if __name__=='__main__':unittest.main()

class OwnedDesktopHandoffTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('domain_commands_owned',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_desktop_mode_owns_connection_before_install(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);plan=root/'plan.json';plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{}}]}));args=m.parser().parse_args(['run','filmcraft',str(plan),'--output',str(root/'out'),'--mode','desktop','--connect','127.0.0.1:1234'])
   with patch.object(m.subprocess,'run',side_effect=AssertionError('installed')):
    with self.assertRaisesRegex(ValueError,'desktop_owns_connection'):m.dispatch(args)
   self.assertFalse((root/'out').exists())
 def test_desktop_child_argv_uses_only_owned_launcher(self):
  m=self.module();args=m.parser().parse_args(['run','filmcraft','plan.json','--output','out','--mode','desktop']);argv=m.launch_command(Path('/domain'),args,Path('/frozen.json'),'/runtime',{'asset':Path('/asset')});self.assertEqual(argv[3],str(m.ROOT/'scripts/native_contract.py'));self.assertEqual(argv[4:7],['/domain/scripts/mcp_session.py','/domain/scripts/desktop.py','run']);self.assertNotIn('--mode',argv);self.assertNotIn('--connect',argv);self.assertIn('asset=/asset',argv)

class DesktopReceiptIdentityTests(unittest.TestCase):
 module=OwnedDesktopHandoffTests.module
 def test_desktop_receipt_requires_identity_and_owned_cleanup(self):
  m=self.module();lock={'version':'0.2.0','binarySha256':'a'*64};proof={'schema':'craft-owned-desktop-session/v1','domain':'filmcraft','result':'PASS','ownedProcessesStopped':True,'listenerOwnedByPID':True,'sessionsStarted':1,'desktop':dict(lock)}
  m.validate_desktop_receipt(proof,'filmcraft','PASS',lock,0)
  for field,value in [('domain','photocraft'),('ownedProcessesStopped',False),('listenerOwnedByPID',False),('sessionsStarted',0),('desktop',dict(lock,binarySha256='b'*64)),('result','unknown')]:
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'outcome_unknown'):m.validate_desktop_receipt(dict(proof,**{field:value}),'filmcraft','PASS',lock,0)

class DesktopOutputPreflightTests(unittest.TestCase):
 module=OwnedDesktopHandoffTests.module
 def test_owned_desktop_metadata_refused_before_setup(self):
  m=self.module();entry=m.domain_entry('filmcraft')
  for name in ['desktop-session.json','desktop.log','.desktop-data/prefs.json']:
   plan={'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'path':{'$output':name}}}]}
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'invalid_output_path'):m.validate_plan(plan,entry,{})

class BridgeToolModeTests(unittest.TestCase):
 module=OwnedDesktopHandoffTests.module
 def test_bridge_only_tools_require_explicit_mode(self):
  m=self.module();entry=m.domain_entry('effectcraft');entry['bridgeToolSchemas']=[{'name':'ui_inspect','inputSchema':{'type':'object','properties':{}}}]
  plan={'schema':'craft-command-plan/v1','operations':[{'tool':'ui_inspect','params':{}}]}
  for mode in ['bridge','desktop']:m.validate_plan(plan,entry,{},mode=mode)
  with self.assertRaisesRegex(ValueError,'bridge_tool_requires_bridge'):m.validate_plan(plan,entry,{})
 def test_query_mode_needs_no_installer(self):
  m=self.module();index=m.load_index();index['effectcraft']['bridgeToolSchemas']=[{'name':'ui_inspect','inputSchema':{'type':'object','properties':{}}}]
  with patch.object(m,'load_index',return_value=index),patch.object(m.subprocess,'run',side_effect=AssertionError('installed')):
   value,code=m.dispatch(m.parser().parse_args(['describe','effectcraft','ui_inspect','--tool','--mode','desktop']))
   self.assertEqual(value['name'],'ui_inspect');self.assertEqual(code,0)
   with self.assertRaisesRegex(ValueError,'unknown_command'):m.dispatch(m.parser().parse_args(['describe','effectcraft','ui_inspect','--tool']))
 def test_bridge_index_cannot_be_injected_without_locked_resource(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'skill';shutil.copytree(SCRIPT.parent.parent,root);path=root/'references/domain-command-index.json';value=json.loads(path.read_text());value['domains']['effectcraft']['bridgeSnapshotText']='{}';path.write_text(json.dumps(value));m=DomainCommandsTests().module(root/'scripts/domain_commands.py')
   with self.assertRaisesRegex(ValueError,'command_index_identity'):m.load_index()
 def test_locked_bridge_index_preserves_schema_and_rejects_native_identity_drift(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'skill';shutil.copytree(SCRIPT.parent.parent,root);path=root/'references/domain-command-index.json';lock_path=root/'scripts/distribution.lock.json';value=json.loads(path.read_text());lock=json.loads(lock_path.read_text());snapshot=json.loads(value['domains']['effectcraft']['snapshotText']);tool={'name':'ui_inspect','inputSchema':{'type':'object','properties':{}}};bridge={'schema':'craft-bridge-tools/v1','pluginId':'effectcraft','mode':'bridge','runtimeSha256':snapshot['runtimeSha256'],'tools':[tool]};key='skills/effectcraft-use/references/bridge-tools.json';m=DomainCommandsTests().module(root/'scripts/domain_commands.py')
   for valid in [True,False]:
    bridge['runtimeSha256']=snapshot['runtimeSha256'] if valid else '0'*64;text=json.dumps(bridge);value['domains']['effectcraft']['bridgeSnapshotText']=text;lock['bundles']['effectcraft-skills']['files'][key]=hashlib.sha256(text.encode()).hexdigest();path.write_text(json.dumps(value));lock_path.write_text(json.dumps(lock))
    if valid:self.assertEqual(m.load_index()['effectcraft']['bridgeToolSchemas'],[tool])
    else:
     with self.assertRaisesRegex(ValueError,'command_index_invalid'):m.load_index()

class CheckHandoffCompatibilityTests(unittest.TestCase):
 module=OwnedDesktopHandoffTests.module
 def test_fixed_domain_check_arguments_match_released_parsers(self):
  m=self.module()
  for domain in m.NAMES:
   for mode in ['headless','bridge','desktop']:
    args=m.parser().parse_args(['check',domain,'plan.json','--mode',mode])
    argv=m.launch_command(Path('/domain'),args,Path('/frozen.json'),'/runtime',{})
    with self.subTest(domain=domain,mode=mode):
     self.assertEqual('--mode' in argv,domain=='effectcraft')
     if domain=='effectcraft':self.assertEqual(argv[-1],'bridge' if mode=='desktop' else mode)
 def test_check_failure_preserves_native_reply_and_stderr(self):
  m=self.module()
  for code,stdout,stderr in [(2,b'',b'usage: unrecognized arguments'),(1,b'{"error":"invalid_reference"}',b'native refused'),(0,b'not json',b''),(0,b'[]',b'')]:
   with self.subTest(code=code,stdout=stdout),self.assertRaises(m.P.PublicCallFailure) as failed:
    m.check_reply(code,stdout,stderr,Path('/runtime'))
   diagnostic=failed.exception.diagnostic
   self.assertNotIn('dependencySetup',diagnostic)
   self.assertEqual(diagnostic['domainCall']['returncode'],code)
   self.assertEqual(diagnostic['domainCall']['stderr'],stderr.decode())
   if stdout.startswith(b'{'):self.assertEqual(diagnostic['publicCallReceipt']['error'],'invalid_reference')
  good={'result':'PASS','nativeExecution':'NOT_RUN'}
  self.assertEqual(m.check_reply(0,json.dumps(good).encode(),b'',Path('/runtime')),good)
  with self.assertRaisesRegex(ValueError,'command_check_reply_too_large'):m.check_reply(0,b'x'*65537,b'',Path('/runtime'))

class HeadlessContractLauncherTests(unittest.TestCase):
 module=OwnedDesktopHandoffTests.module
 def test_headless_run_uses_self_contained_contract_launcher(self):
  m=self.module()
  for domain,mode in [(d,k) for d in m.NAMES for k in ['headless','bridge','desktop']]:
   args=m.parser().parse_args(['run',domain,'plan.json','--output','out','--mode',mode])
   argv=m.launch_command(Path('/domain'),args,Path('/frozen.json'),'/runtime',{})
   self.assertEqual(argv[3],str(m.ROOT/'scripts/native_contract.py'))
   self.assertEqual(argv[4:7],['/domain/scripts/mcp_session.py','/domain/scripts/'+('desktop.py' if mode=='desktop' else 'commands.py'),'run'])
 def test_contract_launcher_is_present_in_all_independent_skills(self):
  sources=[(p/'scripts/native_contract.py').read_bytes() for p in sorted((ROOT/'skills').iterdir())]
  self.assertEqual(len(sources),10);self.assertEqual(len(set(sources)),1)
  compile(sources[0],'native_contract.py','exec')
