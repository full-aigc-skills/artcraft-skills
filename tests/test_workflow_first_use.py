"""干净复制一项 ArtCraft 技能，安装全部依赖并交付四个原生工程。"""
import hashlib
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
import struct
import math

SOURCE = Path(os.environ['CRAFT_INSTALLED_SKILL_ROOT']).resolve() if os.environ.get('CRAFT_INSTALLED_SKILL_ROOT') else Path(__file__).resolve().parents[1]/'skills/artcraft-use'

def archive_arguments(environment):
    # 在线验收必须走默认公开下载，不能误用宿主遗留的离线制品参数。
    if environment.get('CRAFT_ONLINE_FIRST_USE') == '1':
        return []
    if not environment.get('CRAFT_NODE_ARCHIVE') or not environment.get('CRAFT_BUNDLE_DIRECTORY'):
        raise ValueError('offline_archives_required')
    return ['--node-archive', environment['CRAFT_NODE_ARCHIVE'],
            '--bundle-dir', environment['CRAFT_BUNDLE_DIRECTORY']]


class FirstUseArgumentTests(unittest.TestCase):
    def test_online_mode_does_not_forward_archive_overrides(self):
        self.assertEqual(archive_arguments({'CRAFT_ONLINE_FIRST_USE': '1',
                                           'CRAFT_NODE_ARCHIVE': 'stale-node',
                                           'CRAFT_BUNDLE_DIRECTORY': 'stale-bundles'}), [])

    def test_offline_mode_requires_both_verified_archive_inputs(self):
        with self.assertRaisesRegex(ValueError, 'offline_archives_required'):
            archive_arguments({'CRAFT_NODE_ARCHIVE': 'node'})
        self.assertEqual(archive_arguments({'CRAFT_NODE_ARCHIVE': 'node', 'CRAFT_BUNDLE_DIRECTORY': 'bundles'}),
                         ['--node-archive', 'node', '--bundle-dir', 'bundles'])


@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST') == '1' and
                     (os.environ.get('CRAFT_ONLINE_FIRST_USE') == '1' or
                      (os.environ.get('CRAFT_NODE_ARCHIVE') and os.environ.get('CRAFT_BUNDLE_DIRECTORY'))),
                     'requires declared online first use or verified offline archives')
class FirstWorkflowTests(unittest.TestCase):
    def test_isolated_single_skill_installs_runs_and_reuses_four_native_deliveries(self):
        retained=os.environ.get('CRAFT_MIXED_RETAINED_OUTPUT')
        if retained:
            target=Path(retained)
            if not target.is_absolute():raise ValueError('retained_output_absolute_required')
            target.mkdir(exist_ok=False)
            workspace=contextlib.nullcontext(str(target))
        else:workspace=tempfile.TemporaryDirectory()
        with workspace as temporary:
            root=Path(temporary).resolve()
            path_case=os.environ.get('CRAFT_UNICODE_PATH_FIRST_USE')=='1'
            if path_case:root=root/'首次 使用 中文路径';root.mkdir()
            skill=root/'only-artcraft-use';shutil.copytree(SOURCE, skill, ignore=shutil.ignore_patterns('__pycache__'))
            if path_case:self.assertIn(' ',str(skill));self.assertIn('中文',str(skill))
            voice=root/'voice.wav'
            with wave.open(str(voice), 'wb') as output:
                output.setparams((1,2,48000,48000,'NONE','not compressed'))
                output.writeframes(b''.join(struct.pack('<h',round(4000*math.sin(i*2*math.pi*440/48000))) for i in range(48000)))
            runtime=root/'runtime';project=root/'project';self.assertFalse(runtime.exists())
            calls=[]
            def run(argv, **kwargs):
                result=subprocess.run(argv, **kwargs)
                label='call-'+str(len(calls))
                (root/(label+'.stdout')).write_text(result.stdout or '')
                (root/(label+'.stderr')).write_text(result.stderr or '')
                calls.append({'label':label,'argv':list(map(str,argv)),'exitCode':result.returncode,
                              'stdoutSha256':hashlib.sha256((result.stdout or '').encode()).hexdigest(),
                              'stderrSha256':hashlib.sha256((result.stderr or '').encode()).hexdigest()})
                return result
            gateway_mode=os.environ.get('CRAFT_MIXED_GATEWAY_FIRST_USE')=='1'
            def gateway(operation):
                return {**operation,'command':'native.command','params':{'command':operation['command'],'params':operation.get('params',{})}}
            args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(skill/'examples/brand-campaign.json'),'--output',str(project),'--runtime-home',str(runtime),'--authorization','isolated-first-use','--asset','voice='+str(voice)]
            if gateway_mode:
                gateway_plan=json.loads((skill/'examples/brand-campaign.json').read_text())
                selected={'logo':'paint.setFill','poster':'type.create','intro':'prop.addKey','film':'captions.setStyle'}
                for node in gateway_plan['nodes']:
                    operations=node['payload']['plan']['operations']
                    self.assertTrue(any(op['command']==selected[node['id']] for op in operations))
                    node['payload']['plan']['operations']=[gateway(op) if op['command']==selected[node['id']] else op for op in operations]
                gateway_file=root/'gateway-create.json';gateway_file.write_text(json.dumps(gateway_plan));args[4]=str(gateway_file)
            # 使用复制的单技能公开入口创建需求记录，不借用仓库内部 API。
            brief=json.loads((skill/'examples/brand-brief.json').read_text());brief['authorizationRef']='isolated-first-use'
            brief_input=root/'brief-input.json';brief_input.write_text(json.dumps(brief));brief_root=root/'brief-v1'
            created=run([sys.executable,'-I','-B',str(skill/'scripts/brief.py'),'create','--input',str(brief_input),'--output',str(brief_root)],capture_output=True,text=True,timeout=30)
            self.assertEqual(created.returncode,0,created.stdout+created.stderr);brief_receipt=json.loads(created.stdout)
            args.extend(['--brief',str(brief_root),'--brief-sha',brief_receipt['sha256']])
            args.extend(archive_arguments(os.environ))
            environment=dict(os.environ,PATH='/usr/bin:/bin')
            if os.environ.get('CRAFT_ONLINE_FIRST_USE')=='1':
                for key in ('CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY','CRAFT_RUNTIME_HOME'):environment.pop(key,None)
            first_run=run(args,capture_output=True,text=True,env=environment,timeout=240)
            self.assertEqual(first_run.returncode,0,first_run.stdout+first_run.stderr)
            first=json.loads(first_run.stdout);self.assertEqual(first['state'],'review_ready')
            for id, suffix in [('logo','vectorcraft'),('poster','pcraft'),('intro','ecproj'),('film','fcproj')]:
                node=first['nodes'][id];self.assertEqual(node['status'],'review_ready')
                self.assertTrue((Path(node['root'])/('project.'+suffix)).is_file())
            # 保存后时长必须来自实际重开工程和成片记录，且与交付清单摘要绑定。
            film_root=Path(first['nodes']['film']['root'])
            film_manifest=json.loads((film_root/'manifest.json').read_text())
            film_native=json.loads((film_root/'native.json').read_text())
            film_probe=json.loads((film_root/'export-probe.json').read_text())
            self.assertEqual(next(item for item in brief['deliverables'] if item['id']=='film')['durationSeconds'],1)
            self.assertEqual(film_native['sequence']['duration'],'254016000000')
            rate=film_native['sequence']['settings']['frame_rate']
            self.assertEqual(film_probe['video']['frame_rate'],rate)
            self.assertLessEqual(abs(int(film_probe['duration'])-254016000000),254016000000*rate['den']//rate['num'])
            for name in ['project.fcproj','film.mp4','native.json','export-probe.json']:
                self.assertEqual(hashlib.sha256((film_root/name).read_bytes()).hexdigest(),film_manifest['files'][name])
            gateway_receipts={}
            if gateway_mode:
                for id,result in first['nodes'].items():
                    records=json.loads((Path(result['root'])/'operations.json').read_text())
                    gateway_receipts[id]=[record for record in records if 'nativeCommand' in record]
                    self.assertTrue(gateway_receipts[id],id)
            setup=json.loads((project/'installation-receipt.json').read_text())
            self.assertTrue(Path(setup['nodeExecutable']).is_relative_to(runtime))
            self.assertTrue(Path(setup['entryPoint']).is_relative_to(runtime))
            self.assertEqual(set(setup['skills']),{'filmcraft','effectcraft','photocraft','vectorcraft'})
            distribution=json.loads((skill/'scripts/distribution.lock.json').read_text())
            self.assertEqual(setup['version'],distribution['version'])
            for name,value in setup['skills'].items():self.assertEqual(value['runtimeIdentity']['pluginVersion'],distribution['bundles'][name+'-skills'].get('version',distribution['version']))
            self.assertEqual(first['budget']['allocated'],{'minorUnits':0,'externalCalls':0,'revisions':0})
            for value in setup['skills'].values():
                self.assertTrue(Path(value['executable']).is_relative_to(runtime))
                self.assertTrue(Path(value['skillRoot']).is_relative_to(runtime))
            # 混合执行必须实际进入四领域的保护入口，而不只核验分发目录。
            def domain_guard(domain, delivery, revision):
                target=Path(delivery).resolve()
                target_hash=hashlib.sha256(str(target).encode()).hexdigest()
                record=target.parent/('.'+domain+'-execution-'+target_hash+'.json')
                before=record.read_bytes();value=json.loads(before)
                self.assertEqual(value['schema'],domain+'-output-execution/v1')
                self.assertEqual(value['state'],'finished')
                self.assertFalse(value['replayAllowed'])
                self.assertEqual(value['targetHash'],target_hash)
                native_sha=hashlib.sha256(Path(setup['skills'][domain]['executable']).read_bytes()).hexdigest()
                self.assertEqual(value['identity']['runtimeSha256'],native_sha)
                self.assertEqual(value['identity']['projectRevision'],revision)
                plan=json.loads((target/'plan.json').read_text())
                plan_sha=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
                self.assertEqual(value['identity']['planHash'],plan_sha)
                asset_entries=plan.get('assets',{}) if domain=='filmcraft' else json.loads((target/'manifest.json').read_text()).get('assets',{})
                self.assertEqual(value['identity']['inputHashes'],{name:entry['sha256'] for name,entry in asset_entries.items()})
                return record,before,value
            domains={'logo':('vectorcraft','vectorcraft'),'poster':('photocraft','pcraft'),'intro':('effectcraft','ecproj'),'film':('filmcraft','fcproj')}
            first_guards={id:domain_guard(domain,first['nodes'][id]['root'],None) for id,(domain,suffix) in domains.items()}
            first_guard,first_guard_bytes,first_guard_value=first_guards['film']
            second_run=run(args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(second_run.returncode,0,second_run.stdout+second_run.stderr)
            for record,before,value in first_guards.values():self.assertEqual(record.read_bytes(),before)
            second=json.loads(second_run.stdout)
            for id in first['nodes']:self.assertEqual(first['nodes'][id]['taskId'],second['nodes'][id]['taskId'])
            cli=[setup['nodeExecutable'],setup['entryPoint'],'status','--database',str(project/'tasks.sqlite')]
            status=json.loads(run(cli,check=True,capture_output=True,text=True,env=environment,timeout=30).stdout)
            self.assertEqual(len(status['tasks']),4);self.assertFalse(status['leases'])
            # 已验证混合交付的复用仍须检查真实领域 CLI 的安装回执。
            native_receipt=Path(setup['skills']['filmcraft']['executable']).parent/'installation.json'
            receipt_before=native_receipt.read_bytes()
            altered=json.loads(receipt_before);altered['platform']='wrong-platform'
            native_receipt.write_text(json.dumps(altered))
            project_before={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()}
            runtime_before={str(p.relative_to(native_receipt.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in native_receipt.parent.rglob('*') if p.is_file()}
            refused_receipt=run(args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(refused_receipt.returncode,1,refused_receipt.stdout+refused_receipt.stderr)
            self.assertIn('installation_receipt_mismatch',refused_receipt.stdout)
            self.assertEqual(project_before,{str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()})
            self.assertEqual(runtime_before,{str(p.relative_to(native_receipt.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in native_receipt.parent.rglob('*') if p.is_file()})
            native_receipt.write_bytes(receipt_before)
            resumed_receipt=run(args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(resumed_receipt.returncode,0,resumed_receipt.stdout+resumed_receipt.stderr)
            resumed=json.loads(resumed_receipt.stdout)
            for id in first['nodes']:
                self.assertEqual(resumed['nodes'][id]['status'],'reused')
                self.assertEqual(first['nodes'][id]['taskId'],resumed['nodes'][id]['taskId'])
            # 切换缓存位置会改变可信登记绑定；拒绝后不能发布新项目安装身份。
            prior_files={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()}
            relocated_args=list(args);relocated_args[relocated_args.index('--runtime-home')+1]=str(root/'different-runtime')
            rejected=run(relocated_args,capture_output=True,text=True,env=environment,timeout=240)
            self.assertEqual(rejected.returncode,1);self.assertIn('workflow_revision_conflict',rejected.stdout)
            self.assertEqual({str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()},prior_files)
            changed=json.loads((skill/'examples/brand-campaign.json').read_text());changed['nodes'][0]['payload']['plan']['document']['name']='Changed without new revision'
            changed_file=root/'changed.json';changed_file.write_text(json.dumps(changed))
            bad_args=list(args);bad_args[4]=str(changed_file)
            bad=run(bad_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(bad.returncode,1);self.assertIn('workflow_revision_conflict',bad.stdout)
            self.assertEqual(hashlib.sha256(voice.read_bytes()).hexdigest(),first['nodes']['film']['outputs'][0]['sourceRefs'][1]['sha256'])

            # 同一个首次安装环境，通过单技能公开入口返工四种真实源工程。
            source_plan=json.loads((skill/'examples/brand-campaign.json').read_text())
            source_plan['workflowId']='cold-source-brief';source_plan['revision']='v1'
            source_brief=json.loads(json.dumps(brief));source_brief['workflowId']=source_plan['workflowId']
            source_hashes={}
            for node in source_plan['nodes']:
                prior=first['nodes'][node['id']];artifact=prior['outputs'][0];native_root=Path(prior['root'])
                source_hashes[node['id']]={str(p.relative_to(native_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in native_root.rglob('*') if p.is_file()}
                node['dependsOn']=[];node.pop('providedAssets',None);node.pop('inputBindings',None)
                node['externalInputs']=[{'root':str(native_root),'artifact':artifact}];node['expectedRevision']=artifact['nativeProjectRef']['sha256']
                node['payload']['sourceProject']={'assetId':artifact['assetId']};node['payload']['assetBindings']=[]
                node['payload']['plan'].pop('document');node['payload']['plan']['operations']=[]
                if node['id']=='film':node['payload']['plan']['operations']=[{'command':'captions.setStyle','params':{'track':'C1','font':'Arial','size':18,'color':'#ffffff','background':True}}]
                elif node['id']=='logo':node['payload']['plan']['operations']=[{'command':'artboard.setProps','params':{'index':0,'width':352,'height':256}}]
                elif node['id']=='poster':
                    native=json.loads((native_root/'native.json').read_text())
                    background=next(layer['id'] for layer in native['layers'] if layer['name']=='Background')
                    node['payload']['plan']['operations']=[{'command':'image.canvasSize','params':{'width':352,'height':400,'anchor':'center','extensionColor':'transparent'}}]
                    node['payload']['plan']['variant']={'width':352,'height':400,'safeArea':[8,8,336,384],'roles':{'background':background,'product':{'$ref':'logo.layer'},'text':{'$ref':'title.layer'}}}
                else:
                    manifest=json.loads((native_root/'manifest.json').read_text())
                    node['payload']['plan']['operations']=[{'command':'comp.settings','params':{'comp':manifest['bindings']['composition']['comp'],'width':352}}]
                if gateway_mode:
                    if node['id']=='poster':
                        node['payload']['plan']['operations'].append(gateway({'command':'layer.select','params':{'layer':background}}))
                    else:
                        node['payload']['plan']['operations']=[gateway(op) for op in node['payload']['plan']['operations']]
            for item in source_brief['deliverables']:
                item['dependsOn']=[]
                if item['id']!='film':item['width']=352
            source_plan['projectBrief']=source_brief
            source_file=root/'source-brief-plan.json';source_file.write_text(json.dumps(source_plan));source_project=root/'source-project'
            source_args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(source_file),'--output',str(source_project),'--runtime-home',str(runtime),'--authorization','isolated-first-use']+archive_arguments(os.environ)
            source_run=run(source_args,capture_output=True,text=True,env=environment,timeout=240)
            self.assertEqual(source_run.returncode,0,source_run.stdout+source_run.stderr);source_result=json.loads(source_run.stdout)
            self.assertEqual(source_result['state'],'review_ready')
            source_gateway_receipts={}
            if gateway_mode:
                for id,result in source_result['nodes'].items():
                    records=json.loads((Path(result['root'])/'operations.json').read_text())
                    source_gateway_receipts[id]=[record for record in records if 'nativeCommand' in record]
                    self.assertTrue(source_gateway_receipts[id],id)
            photo_delivery=Path(setup['skills']['photocraft']['skillRoot'])/'scripts/delivery.py'
            photo_digest=hashlib.sha256(photo_delivery.read_bytes()).hexdigest()
            self.assertEqual(photo_digest,distribution['bundles']['photocraft-skills']['files']['skills/photocraft-use/scripts/delivery.py'])
            self.assertEqual(photo_digest,setup['skills']['photocraft']['capabilitySnapshot']['scriptHashes']['delivery.py'])
            photo_integrity=[]
            for photo_root in [Path(first['nodes']['poster']['root']),Path(source_result['nodes']['poster']['root'])]:
                manifest_digest=hashlib.sha256((photo_root/'manifest.json').read_bytes()).hexdigest()
                checked=run([sys.executable,'-I','-B',str(photo_delivery),str(photo_root),'--expected-manifest-sha256',manifest_digest],capture_output=True,text=True,env=environment,timeout=30)
                self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
                observed=json.loads(checked.stdout);self.assertEqual(observed['result'],'PASS');photo_integrity.append(observed)

            saved_source_evidence={}
            for id,result in source_result['nodes'].items():
                self.assertEqual(result['sourceInspection']['nativeProjectSha256'],first['nodes'][id]['outputs'][0]['nativeProjectRef']['sha256'])
                revised_root=Path(result['root']);manifest=json.loads((revised_root/'manifest.json').read_text());native=json.loads((revised_root/'native.json').read_text())
                if id=='logo':
                    rect=native['artboards'][0]['rect'];document={'width':rect['x1']-rect['x0'],'height':rect['y1']-rect['y0']}
                elif id=='intro':document=native['composition']
                elif id=='film':document=native['sequence']['settings']
                else:document=native
                expected=next(item for item in source_brief['deliverables'] if item['id']==id)
                self.assertEqual((document['width'],document['height']),(expected['width'],expected['height']))
                if id=='poster':
                    layout=json.loads((revised_root/'layout-variant.json').read_text())
                    self.assertEqual(layout['targetSize'],[352,400]);self.assertEqual(layout['steps'][0]['padding'],{'left':16,'top':0,'right':16,'bottom':0})
                    self.assertEqual(layout['roles']['text']['kind'],'Type')
                    self.assertEqual(manifest['layoutVariant']['sha256'],hashlib.sha256((revised_root/'layout-variant.json').read_bytes()).hexdigest())
                if id=='intro':self.assertEqual((document['frameRate'],document['duration']),(12,1))
                if id=='film':self.assertEqual(native['sequence']['duration'],'254016000000')
                files={}
                for name in ['native.json',result['outputs'][0]['location'],result['outputs'][0]['nativeProjectRef']['location']]:
                    self.assertEqual(hashlib.sha256((revised_root/name).read_bytes()).hexdigest(),manifest['files'][name]);files[name]=manifest['files'][name]
                saved_source_evidence[id]={'width':document['width'],'height':document['height'],'files':files}
                if id=='intro':
                    probed=run([setup['skills']['effectcraft']['executable'],'--empty','run','file.import',json.dumps({'paths':[str(revised_root/'intro.mp4')]}),'project.summary','{}','file.interpretFootage','{"items":[1]}','--json'],check=True,capture_output=True,text=True,env=environment,timeout=30)
                    responses=json.loads(probed.stdout);self.assertEqual(responses[0]['result']['errors'],[])
                    media=responses[1]['result']['items'][0];self.assertEqual((media['type'],media['size'],media['duration']),('Video',[352,180],1))
                    self.assertEqual(responses[2]['result']['items'][0]['frameRate'],12)
                    saved_source_evidence[id]['exportProbe']={'width':352,'height':180,'durationSeconds':1,'frameRate':12,'responseSha256':hashlib.sha256(probed.stdout.encode()).hexdigest()}
                original=Path(first['nodes'][id]['root'])
                self.assertEqual({str(p.relative_to(original)):hashlib.sha256(p.read_bytes()).hexdigest() for p in original.rglob('*') if p.is_file()},source_hashes[id])
            revised_guards={id:domain_guard(domain,source_result['nodes'][id]['root'],json.loads((Path(first['nodes'][id]['root'])/'manifest.json').read_text())['files']['project.'+suffix]) for id,(domain,suffix) in domains.items()}
            revised_guard,revised_guard_bytes,revised_guard_value=revised_guards['film']
            for record,before,value in first_guards.values():self.assertEqual(record.read_bytes(),before)
            source_replay=run(source_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(source_replay.returncode,0,source_replay.stdout+source_replay.stderr)
            for record,before,value in revised_guards.values():self.assertEqual(record.read_bytes(),before)
            self.assertTrue(all(result['status']=='reused' for result in json.loads(source_replay.stdout)['nodes'].values()))
            source_status=json.loads(run([setup['nodeExecutable'],setup['entryPoint'],'status','--database',str(source_project/'tasks.sqlite')],check=True,capture_output=True,text=True,env=environment,timeout=30).stdout)
            self.assertFalse(source_status['leases'])
            layout_path=Path(source_result['nodes']['poster']['root'])/'layout-variant.json';layout_bytes=layout_path.read_bytes()
            layout_path.write_text('{}')
            stale_run=run(source_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(stale_run.returncode,1,stale_run.stdout+stale_run.stderr);self.assertIn('photo_variant_evidence_stale',stale_run.stdout)
            layout_path.write_bytes(layout_bytes)
            restored_run=run(source_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(restored_run.returncode,0,restored_run.stdout+restored_run.stderr)
            restored=json.loads(restored_run.stdout);self.assertTrue(all(result['status']=='reused' for result in restored['nodes'].values()))
            self.assertEqual({id:result['taskId'] for id,result in restored['nodes'].items()},{id:result['taskId'] for id,result in source_result['nodes'].items()})


            variant_package=root/'variant-package'
            variant_args=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'create','--project',str(source_project),'--workflow',source_result['runKey'],'--output',str(variant_package),'--authorization','isolated-first-use','--runtime-home',str(runtime)]+archive_arguments(os.environ)
            variant_run=run(variant_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(variant_run.returncode,0,variant_run.stdout+variant_run.stderr)
            variant_receipt=json.loads(variant_run.stdout);variant_moved=root/'variant-moved';variant_package.rename(variant_moved)
            variant_verify=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'verify','--package',str(variant_moved),'--sha',variant_receipt['sha256'],'--runtime-home',str(runtime)]+archive_arguments(os.environ)
            verified_variant=run(variant_verify,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(verified_variant.returncode,0,verified_variant.stdout+verified_variant.stderr)
            layouts=list(variant_moved.rglob('layout-variant.json'));self.assertEqual(len(layouts),1)
            variant_layout=json.loads(layouts[0].read_text());self.assertEqual(variant_layout['targetSize'],[352,400])
            retained_layout=layouts[0].read_bytes()
            layouts[0].write_text('{}')
            rejected_variant=run(variant_verify,capture_output=True,text=True,env=environment,timeout=120)
            self.assertNotEqual(rejected_variant.returncode,0,rejected_variant.stdout+rejected_variant.stderr)
            layouts[0].write_bytes(retained_layout)
            restored_variant=run(variant_verify,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(restored_variant.returncode,0,restored_variant.stdout+restored_variant.stderr)

            # 单技能首次使用后的公开打包入口，不依赖全局 Node 或仓库脚本。
            package=root/'delivery-package'
            pack_args=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'create','--project',str(project),'--workflow',first['runKey'],'--output',str(package),'--authorization','isolated-first-use','--runtime-home',str(runtime)]
            pack_args.extend(archive_arguments(os.environ))
            packed_run=run(pack_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(packed_run.returncode,0,packed_run.stdout+packed_run.stderr)
            packed=json.loads(packed_run.stdout);self.assertEqual(len(packed['children']),4)
            moved=root/'moved-package';package.rename(moved)
            verify_args=[sys.executable,'-I','-B',str(skill/'scripts/package.py'),'verify','--package',str(moved),'--sha',packed['sha256'],'--runtime-home',str(runtime)]
            verify_args.extend(archive_arguments(os.environ))
            verified_run=run(verify_args,capture_output=True,text=True,env=environment,timeout=120)
            self.assertEqual(verified_run.returncode,0,verified_run.stdout+verified_run.stderr)
            self.assertEqual(len(json.loads(verified_run.stdout)['children']),4)
            self.assertEqual(json.loads((moved/'workflow-plan-portable.json').read_text())['projectBrief'],brief)
            if os.environ.get('CRAFT_WORKFLOW_EVIDENCE_FILE'):
                artifacts={id:[{'assetId':a['assetId'],'sha256':a['sha256'],'bytes':a['bytes'],'mediaType':a['mediaType'],'nativeProjectRef':a['nativeProjectRef']} for a in value['outputs']] for id,value in first['nodes'].items()}
                proof={'calls':calls,'gatewayMode':gateway_mode,'gatewayReceipts':gateway_receipts,'sourceGatewayReceipts':source_gateway_receipts,'schema':'craft-installed-mixed-first-use/v1','retainedOutputs':bool(retained),'photoDeliveryIntegrity':{'scriptSha256':photo_digest,'launcherIdentityBound':True,'deliveries':photo_integrity},'pathCase':{'unicodeAndSpaces':path_case,'parentName':root.name,'runtimeInitiallyAbsent':True},'python':sys.version.split()[0],'runtimeVersion':setup['version'],'filmOutputGuards':[first_guard_value,revised_guard_value],'domainOutputGuards':{id:[first_guards[id][2],revised_guards[id][2]] for id in domains},'briefSha256':brief_receipt['sha256'],'artifacts':artifacts,'packageSha256':packed['sha256'],'voiceSha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'sourceSkillVersions':{name:entry['version'] for name,entry in distribution['bundles'].items()},'photoVariant':{'layout':variant_layout,'packageSha256':variant_receipt['sha256'],'movedPackageVerified':True,'tamperedLayoutRejected':True,'staleCachedLayoutBlocked':True,'restoredWithoutReplay':True},'sourceBrief':{'savedOutputs':saved_source_evidence,'nativeProjectHashes':{id:result['sourceInspection']['nativeProjectSha256'] for id,result in source_result['nodes'].items()},'inspections':{id:result['sourceInspection'] for id,result in source_result['nodes'].items()},'originalFilesPreserved':True,'reused':True,'leases':0},'filmDuration':{'requiredSeconds':1,'nativeTicks':film_native['sequence']['duration'],'exportTicks':film_probe['duration'],'frameRate':rate,'files':{name:film_manifest['files'][name] for name in ['project.fcproj','film.mp4','native.json','export-probe.json']}},'nativeReceipt':{'mismatchRejected':True,'installationPreserved':True,'projectFilesPreserved':True,'restoredTaskIdsReused':True},'checks':['Film installation receipt checked before mixed reuse','hash-bound native and export Film duration','four native domain source Brief revisions and reuse','four native domain deliveries','same-revision no replay','status has four tasks and zero leases','relocated runtime conflict preserves whole project','changed frozen plan refused','voice source digest bound','four-child moved package verified','portable Brief retained'],'scope':'single copied installed skill, fresh default online install and system-only PATH; technical fixture, not creative acceptance'}
                with Path(os.environ['CRAFT_WORKFLOW_EVIDENCE_FILE']).open('x') as output:json.dump(proof,output,ensure_ascii=False,indent=2);output.write('\n')

if __name__ == '__main__':unittest.main()
