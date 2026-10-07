"""单个 Art 技能首次安装及拥有的领域桌面交接；实际原生环境显式运行。"""
import hashlib,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
@unittest.skipUnless(os.environ.get('ARTCRAFT_OWNED_DESKTOP_FIRST_USE')=='1','native owned desktop first use is opt-in')
class OwnedDesktopFirstUse(unittest.TestCase):
 def test_standalone_skill_installs_selected_domain_and_closes_owned_session(self):
  source=Path(os.environ['ARTCRAFT_OWNED_DESKTOP_SKILL']);domain=os.environ.get('ARTCRAFT_OWNED_DESKTOP_DOMAIN','vectorcraft')
  def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
  original=hashes(source)
  with tempfile.TemporaryDirectory(prefix='art-owned-desktop-first-use-') as td:
   root=Path(td);skill=root/'.agents/skills'/source.name;skill.parent.mkdir(parents=True);shutil.copytree(source,skill);before=hashes(skill);output=root/'output';runtime=root/'runtime'
   args=['/opt/anaconda3/bin/python3','-I','-B',str(skill/'scripts/domain_commands.py'),'run',domain,str(skill/'examples'/('domain-'+domain+'-desktop.json')),'--mode','desktop','--output',str(output),'--runtime-home',str(runtime)]
   result=subprocess.run(args,capture_output=True,text=True,timeout=900,env=dict(os.environ,PATH='/usr/bin:/bin'))
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);receipt=json.loads((output/'artcraft-command-call.json').read_text());self.assertEqual(receipt['result'],'PASS');self.assertEqual(receipt['domain'],domain);self.assertEqual(receipt['dagDeliveryAcceptance'],'NOT_RUN');desktop=receipt['desktopReceipt'];self.assertTrue(desktop['ownedProcessesStopped']);self.assertTrue(desktop['listenerOwnedByPID']);self.assertEqual(desktop['sessionsStarted'],1);self.assertFalse(desktop['desktop']['reused']);self.assertEqual(hashes(source),original);self.assertEqual(hashes(skill),before)
   ui_records=[row for row in receipt['commandReceipt']['steps'] if row.get('tool')=='ui_inspect']
   if domain=='effectcraft':
    self.assertEqual(len(ui_records),1);self.assertEqual(ui_records[0]['state'],'succeeded');self.assertIsInstance(ui_records[0]['result'],dict)
   projects=[p for p in output.iterdir() if p.suffix in ('.fcproj','.ecproj','.pcraft','.vectorcraft')];self.assertEqual(len(projects),1);self.assertGreater(projects[0].stat().st_size,0);self.assertEqual(receipt['commandReceipt']['steps'][-1]['state'],'succeeded')
   proof={'schema':'artcraft-owned-desktop-first-use/v1','result':'PASS','skill':source.name,'domain':domain,'emptyRuntime':True,'standaloneSkillUnchanged':True,'ownedProcessesStopped':True,'ownedListenerVerified':True,'sourceBundleSha256':receipt['sourceBundleSha256'],'runtimeSha256':receipt['runtimeSha256'],'desktopBinarySha256':desktop['desktop']['binarySha256'],'bridgeUIInspection':ui_records[0]['result'] if ui_records else None,'operations':len(receipt['commandReceipt']['steps']),'nativeProject':{'name':projects[0].name,'sha256':hashlib.sha256(projects[0].read_bytes()).hexdigest(),'bytes':projects[0].stat().st_size},'finalInspection':receipt['commandReceipt']['steps'][-1]['result'],'scope':'one standalone Art skill, selected domain desktop cold install/native save/reopen/cleanup; not mixed DAG or exhaustive commands'}
   Path(os.environ['ARTCRAFT_OWNED_DESKTOP_REPORT']).write_text(json.dumps(proof,indent=2)+'\n')
