"""版本化 Brief、只读规划检查及未确认需求的局部阻塞。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/artcraft-use/scripts/brief.py'

class BriefTests(unittest.TestCase):
    def test_film_duration_uses_timeline_ticks_not_document_claim(self):
        m=self.module();value,plan=self.fixture();item=value['deliverables'][0];item['nativeFormat']='.fcproj';item['durationSeconds']=1
        node=plan['nodes'][0];node['pluginId']='filmcraft';domain=node['payload']['plan']
        domain['operations']=[{'command':'timeline.place','params':{'time':'0','duration':'254016000000','insert':False}}]
        self.assertEqual(m.assess(value,plan,'user','scope')['state'],'ready')
        domain['document']['duration']=1;domain['operations'][0]['params']['duration']='508032000000'
        self.assertIn('duration_mismatch',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
    def test_film_duration_counts_all_tracks_and_refuses_uncertain_edits(self):
        m=self.module();value,plan=self.fixture();value['deliverables'][0].update(nativeFormat='.fcproj',durationSeconds=1)
        node=plan['nodes'][0];node['pluginId']='filmcraft';domain=node['payload']['plan']
        base={'command':'timeline.place','params':{'time':'0','duration':'254016000000','insert':False}}
        domain['operations']=[base,{'command':'timeline.place','params':{'time':'0','duration':'508032000000','insert':False,'track':'A1'}}]
        self.assertIn('duration_mismatch',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
        for changed in [dict(base,params={'time':'0','duration':'254016000000','insert':True}),dict(base,params={'time':'0','duration':254016000000,'insert':False}),{'command':'timeline.trim','params':{'delta':'1'}}]:
            domain['operations']=[changed]
            self.assertIn('duration_inspection_required',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
    def test_film_duration_keeps_large_tick_precision_and_rational_seconds(self):
        m=self.module();value,plan=self.fixture();value['deliverables'][0].update(nativeFormat='.fcproj',durationSeconds=86400)
        node=plan['nodes'][0];node['pluginId']='filmcraft';domain=node['payload']['plan']
        domain['operations']=[{'command':'timeline.place','params':{'time':'0','duration':str(86400*254016000000),'insert':False}}]
        self.assertEqual(m.assess(value,plan,'user','scope')['state'],'ready')
        domain['operations'][0]['params']['duration']=str(86400*254016000000+2)
        self.assertIn('duration_mismatch',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
        value['deliverables'][0]['durationSeconds']=1/3;domain['operations'][0]['params'].update(time='0',duration='84672000000')
        self.assertEqual(m.assess(value,plan,'user','scope')['state'],'ready')
    def test_only_film_source_metadata_may_defer_to_trusted_native_inspection(self):
        m=self.module();value,plan=self.fixture();value['deliverables'][0].update(nativeFormat='.fcproj',durationSeconds=1,frameRate={'num':12,'den':1})
        node=plan['nodes'][0];node['pluginId']='filmcraft';node['expectedRevision']='a'*64
        node['payload']['sourceProject']={'assetId':'source'};node['payload']['plan'].pop('document')
        node['externalInputs']=[{'artifact':{'assetId':'source','nativeProjectRef':{'sha256':node['expectedRevision']}}}]
        assessment=m.assess(value,plan,'user','scope')
        self.assertEqual(assessment['state'],'blocked');self.assertTrue(m.pending_native_assessment(assessment,plan))
        value['ambiguities']=[{'id':'question','question':'Confirm title','affects':['logo']}]
        self.assertFalse(m.pending_native_assessment(m.assess(value,plan,'user','scope'),plan))
        value['ambiguities']=[];node['expectedRevision']='invalid'
        self.assertFalse(m.pending_native_assessment(m.assess(value,plan,'user','scope'),plan))
        node['expectedRevision']='a'*64;node['pluginId']='photocraft';value['deliverables'][0]['nativeFormat']='.pcraft'
        self.assertFalse(m.pending_native_assessment(m.assess(value,plan,'user','scope'),plan))

    def test_design_source_deferral_and_metadata_changes_require_native_gate(self):
        m=self.module();value,plan=self.fixture();node=plan['nodes'][0]
        node['expectedRevision']='a'*64;node['payload']['sourceProject']={'assetId':'source'};node['payload']['plan'].pop('document')
        node['externalInputs']=[{'artifact':{'assetId':'source','nativeProjectRef':{'sha256':node['expectedRevision']}}}]
        self.assertTrue(m.pending_native_assessment(m.assess(value,plan,'user','scope'),plan))
        value['deliverables'][0]['durationSeconds']=1
        self.assertFalse(m.pending_native_assessment(m.assess(value,plan,'user','scope'),plan))
        del value['deliverables'][0]['durationSeconds']
        node['pluginId']='photocraft';value['deliverables'][0]['nativeFormat']='.pcraft'
        node['payload']['plan']['operations']=[{'command':'image.canvasSize','params':{'width':320,'height':180}}]
        assessment=m.assess(value,plan,'user','scope')
        self.assertIn('native_output_inspection_required',assessment['blocked'][0]['reasons'])
        self.assertTrue(m.pending_native_assessment(assessment,plan))

    def test_source_deferral_reaches_runtime_and_ambiguity_still_prevents_install(self):
        # 仅验证 Python 桥接分支；原生行为由独立真实工作流测试证明。
        from types import SimpleNamespace
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('source_workflow',SCRIPT.with_name('workflow.py'));workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
        m=self.module();value,plan=self.fixture();value['deliverables'][0].update(nativeFormat='.fcproj',durationSeconds=1,frameRate={'num':12,'den':1})
        node=plan['nodes'][0];node['pluginId']='filmcraft';node['expectedRevision']='a'*64;node['payload']['plan'].pop('document');node['payload']['sourceProject']={'assetId':'source'};node['externalInputs']=[{'artifact':{'assetId':'source','nativeProjectRef':{'sha256':node['expectedRevision']}}}]
        calls=[]
        def process(argv,**kwargs):
            calls.append(argv)
            if 'bootstrap.py' in str(argv[3]):
                identity=lambda name:{'runtimeIdentity':{'pluginId':name,'pluginVersion':'fixture'},'skillRoot':'fixture-skill','executable':'fixture-native','files':[]}
                result={'schema':'artcraft-setup/v1','nodeExecutable':'fixture-node','entryPoint':'fixture-entry','pythonExecutable':'fixture-python','pythonSha256':'b'*64,'runtimeHome':'fixture-home','skills':{name:identity(name) for name in ('filmcraft','vectorcraft','photocraft')}}
                return SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr='')
            return SimpleNamespace(returncode=2,stdout=json.dumps({'state':'blocked','error':'native_inspection_required'}),stderr='')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.json';source.write_text(json.dumps(value));brief=m.create(source,root/'brief');planfile=root/'plan.json';planfile.write_text(json.dumps(plan))
            with patch.object(workflow.subprocess,'run',side_effect=process):
                with self.assertRaisesRegex(RuntimeError,'native_inspection_required'):workflow.execute(planfile,root/'project','user','scope',brief_root=root/'brief',brief_sha=brief['sha256'])
                self.assertEqual(len(calls),2);self.assertIn('run',calls[1])
                calls.clear();value['ambiguities']=[{'id':'title','question':'Confirm title','affects':['logo']}];source.write_text(json.dumps(value));ambiguous=m.create(source,root/'ambiguous')
                with self.assertRaisesRegex(ValueError,'brief_plan_blocked'):workflow.execute(planfile,root/'other','user','scope',brief_root=root/'ambiguous',brief_sha=ambiguous['sha256'])
                self.assertEqual(calls,[])

    def module(self):
        spec=importlib.util.spec_from_file_location('brief',SCRIPT);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def fixture(self):
        budget={'currency':'USD','maxMinorUnits':0,'maxRevisions':2,'maxExternalCalls':0}
        value={'schema':'craft-brief/v1','workflowId':'brand','revision':'brief-v1','ownerId':'user','authorizationRef':'scope','budget':budget,'brand':{'name':'NOVA','colors':['#ef5b36'],'fonts':['Arial'],'appliesTo':['logo','poster'],'referenceAssets':[]},'subjects':[],'dataPolicy':{'allowUpload':False},'ambiguities':[],'deliverables':[{'id':'logo','nativeFormat':'.vectorcraft','width':320,'height':180,'dependsOn':[],'execution':'local'},{'id':'poster','nativeFormat':'.pcraft','width':320,'height':400,'dependsOn':['logo'],'execution':'local'},{'id':'icon','nativeFormat':'.vectorcraft','width':32,'height':32,'dependsOn':[],'execution':'local'}]}
        nodes=[]
        for item,plugin in zip(value['deliverables'],['vectorcraft','photocraft','vectorcraft']):
            nodes.append({'id':item['id'],'pluginId':plugin,'dependsOn':item['dependsOn'],'payload':{'plan':{'document':{'width':item['width'],'height':item['height']},'operations':[]}}})
        return value,{'workflowId':'brand','revision':'v1','budget':budget,'nodes':nodes}
    def test_create_reopen_move_and_refuse_overwrite(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);value,_=self.fixture();source=root/'input.json';source.write_text(json.dumps(value));receipt=m.create(source,root/'brief')
            before=source.read_bytes();self.assertEqual(m.verify(root/'brief',receipt['sha256']),value)
            (root/'brief').rename(root/'moved');self.assertEqual(m.verify(root/'moved',receipt['sha256']),value)
            with self.assertRaisesRegex(ValueError,'brief_output_exists'):m.create(source,root/'moved')
            self.assertEqual(source.read_bytes(),before)
    def test_constraints_are_selected_per_deliverable_and_independent_icon_is_unaffected(self):
        m=self.module();value,plan=self.fixture();report=m.assess(value,plan,'user','scope')
        self.assertEqual(report['ready'],['logo','poster','icon']);self.assertEqual(report['blocked'],[])
        before=m.node_constraints(value,'icon');value['brand']['colors']=['#2366e8']
        self.assertEqual(m.node_constraints(value,'icon'),before)
        self.assertEqual(m.node_constraints(value,'logo')['brand']['colors'],['#2366e8'])
    def test_ambiguity_blocks_transitive_consumers_but_reports_independent_checks(self):
        m=self.module();value,plan=self.fixture();value['ambiguities']=[{'id':'brand-name','question':'Confirm brand name','affects':['logo']}]
        report=m.assess(value,plan,'user','scope');self.assertEqual(report['ready'],['icon'])
        self.assertEqual({row['nodeId'] for row in report['blocked']},{'logo','poster'})
    def test_native_format_cannot_silently_substitute_and_no_upload_blocks_cloud_step(self):
        m=self.module();value,plan=self.fixture();value['deliverables'][0]['nativeFormat']='jianying-draft'
        report=m.assess(value,plan,'user','scope');self.assertIn('capability_missing',report['blocked'][0]['reasons'])
        value,plan=self.fixture();value['deliverables'][0]['execution']='cloud';report=m.assess(value,plan,'user','scope')
        self.assertIn('upload_forbidden',report['blocked'][0]['reasons']);self.assertEqual(report['ready'],['icon'])
    def test_size_font_and_dependency_mismatch_block_only_affected_nodes(self):
        m=self.module();value,plan=self.fixture();plan['nodes'][0]['payload']['plan']['document']['width']=300
        report=m.assess(value,plan,'user','scope');self.assertIn('document_size_mismatch',report['blocked'][0]['reasons'])
        value,plan=self.fixture();plan['nodes'][0]['payload']['plan']['operations']=[{'params':{'font':'OtherFont'}}]
        self.assertIn('brand_font_mismatch',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
        value,plan=self.fixture();plan['nodes'][1]['dependsOn']=[]
        self.assertIn('brief_dependency_mismatch',m.assess(value,plan,'user','scope')['blocked'][0]['reasons'])
    def test_stale_reference_budget_and_authorization_are_not_accepted(self):
        m=self.module();value,plan=self.fixture();value['brand']['referenceAssets']=[{'assetId':'ref','version':'v1','sha256':'a'*64}]
        report=m.assess(value,plan,'user','scope');self.assertIn('reference_asset_missing_or_stale',report['blocked'][0]['reasons'])
        for owner,authorization in [('other','scope'),('user','other')]:
            with self.assertRaisesRegex(ValueError,'brief_authorization_mismatch'):m.assess(value,plan,owner,authorization)
        plan['budget']={**plan['budget'],'maxMinorUnits':1}
        with self.assertRaisesRegex(ValueError,'brief_budget_mismatch'):m.assess(value,plan,'user','scope')
    def test_invalid_dependency_members_and_record_directory_symlinks_are_refused(self):
        m=self.module();value,_=self.fixture();value['deliverables'][0]['dependsOn']=[{}]
        with self.assertRaisesRegex(ValueError,'brief_dependency_invalid'):m.validate(value)
        value,_=self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.json';source.write_text(json.dumps(value));receipt=m.create(source,root/'brief')
            (root/'outside').mkdir();(root/'brief/extra').symlink_to(root/'outside',target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'brief_symlink_refused'):m.verify(root/'brief',receipt['sha256'])

    def test_workflow_refuses_blocked_brief_before_any_installer(self):
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('brief_workflow',SCRIPT.with_name('workflow.py'));workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
        m=self.module();value,plan=self.fixture();value['ambiguities']=[{'id':'name','question':'Confirm name','affects':['logo']}]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'brief.json';source.write_text(json.dumps(value));receipt=m.create(source,root/'record');plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan))
            with patch.object(workflow.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'brief_plan_blocked'):
                    workflow.execute(plan_path,root/'project','user','scope',brief_root=root/'record',brief_sha=receipt['sha256'])
                process.assert_not_called()
            self.assertFalse((root/'project/installation-receipt.json').exists())

    def test_ready_brief_is_frozen_and_changed_brief_requires_new_revision(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        spec=importlib.util.spec_from_file_location('brief_workflow',SCRIPT.with_name('workflow.py'));workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
        m=self.module();value,plan=self.fixture();launches=[]
        def process(argv,**kwargs):
            if 'bootstrap.py' in str(argv[3]):
                identity=lambda name:{'runtimeIdentity':{'pluginId':name,'pluginVersion':'fixture'},'skillRoot':'fixture-skill','executable':'fixture-native','files':[]}
                result={'schema':'artcraft-setup/v1','nodeExecutable':'fixture-node','entryPoint':'fixture-entry','pythonExecutable':'fixture-python','pythonSha256':'a'*64,'runtimeHome':'fixture-home','skills':{name:identity(name) for name in ('vectorcraft','photocraft')}}
            else:launches.append(argv);result={'runKey':'fixture','state':'review_ready'}
            return SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr='')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'brief.json';source.write_text(json.dumps(value));receipt=m.create(source,root/'record');plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan));project=root/'project'
            with patch.object(workflow.subprocess,'run',side_effect=process):
                workflow.execute(plan_path,project,'user','scope',brief_root=root/'record',brief_sha=receipt['sha256'])
                frozen=json.loads(next(p for p in (project/'plans').glob('*.json') if not p.name.endswith('.binding.json')).read_text())
                self.assertEqual(frozen['projectBrief'],value)
                before={str(p.relative_to(project)):p.read_bytes() for p in project.rglob('*') if p.is_file()}
                value['brand']['name']='CHANGED';source.write_text(json.dumps(value));second=m.create(source,root/'second')
                with self.assertRaisesRegex(ValueError,'workflow_revision_conflict'):
                    workflow.execute(plan_path,project,'user','scope',brief_root=root/'second',brief_sha=second['sha256'])
                self.assertEqual({str(p.relative_to(project)):p.read_bytes() for p in project.rglob('*') if p.is_file()},before)
                self.assertEqual(len(launches),1)

    def test_execution_plan_cannot_omit_requested_deliverable(self):
        m=self.module();value,plan=self.fixture();plan['nodes']=plan['nodes'][:2]
        with self.assertRaisesRegex(ValueError,'brief_plan_deliverable_missing'):m.assess(value,plan,'user','scope')

    def test_closed_schema_duplicate_keys_symlinks_and_tampered_record_are_refused(self):
        m=self.module();value,_=self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.json';source.write_text(json.dumps(value));link=root/'link.json';link.symlink_to(source)
            with self.assertRaisesRegex(ValueError,'brief_symlink_refused'):m.create(link,root/'bad')
            receipt=m.create(source,root/'brief');(root/'brief/brief.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'brief_file_mismatch'):m.verify(root/'brief',receipt['sha256'])
            source.write_text('{"schema":"craft-brief/v1","schema":"duplicate"}')
            with self.assertRaisesRegex(ValueError,'brief_duplicate_json_key'):m.create(source,root/'duplicate')
        value['extra']=True
        with self.assertRaisesRegex(ValueError,'brief_schema_invalid'):m.validate(value)

if __name__=='__main__':unittest.main()
