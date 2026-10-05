"""输入素材流式摘要与现有用户目录保护。"""
import hashlib
import importlib.util
import json
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts/workflow.py'
spec=importlib.util.spec_from_file_location('workflow',SCRIPT);workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)

class WorkflowTests(unittest.TestCase):
    def test_multichunk_input_digest_and_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'media.bin';content=b'media-block'*300000;path.write_bytes(content)
            self.assertEqual(workflow.file_digest(path),(hashlib.sha256(content).hexdigest(),len(content)))

    def test_user_directory_is_rejected_and_preserved_before_setup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'user.txt').write_text('keep')
            with self.assertRaisesRegex(ValueError,'project_directory_not_owned'):
                workflow.execute(root/'not-present.json',root,'local-user','scope')
            self.assertEqual((root/'user.txt').read_text(),'keep')
            self.assertFalse((root/'.artcraft-project.json').exists())

    def test_runtime_binding_conflict_preserves_existing_project_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);project=root/'project';plan=root/'plan.json'
            plan.write_text(json.dumps({'workflowId':'fixture','revision':'v1','nodes':[{'id':'logo','pluginId':'vectorcraft','payload':{'schemaVersion':'fixture/v1'}}]}))
            def setup(version):
                return {'schema':'artcraft-setup/v1','nodeExecutable':'fixture-node','entryPoint':'fixture-entry','pythonExecutable':'fixture-python','pythonSha256':'a'*64,'runtimeHome':'fixture-home','skills':{'vectorcraft':{'runtimeIdentity':{'pluginId':'vectorcraft','pluginVersion':version},'skillRoot':'fixture-skill','executable':'fixture-native','files':[]}}}
            launches=[]
            def process(version):
                def run(argv,**kwargs):
                    if 'bootstrap.py' in str(argv[3]):value=setup(version)
                    else:launches.append(argv);value={'runKey':'fixture-run','state':'review_ready'}
                    return SimpleNamespace(returncode=0,stdout=json.dumps(value),stderr='')
                return run
            with patch.object(workflow.subprocess,'run',side_effect=process('old')):workflow.execute(plan,project,'owner','scope')
            before={str(p.relative_to(project)):p.read_bytes() for p in project.rglob('*') if p.is_file()}
            with patch.object(workflow.subprocess,'run',side_effect=process('new')):
                with self.assertRaisesRegex(ValueError,'workflow_revision_conflict'):workflow.execute(plan,project,'owner','scope')
            after={str(p.relative_to(project)):p.read_bytes() for p in project.rglob('*') if p.is_file()}
            self.assertEqual(after,before)
            self.assertEqual(len(launches),1)

if __name__=='__main__':unittest.main()
