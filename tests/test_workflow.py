"""输入素材流式摘要与现有用户目录保护。"""
import hashlib
import importlib.util
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

if __name__=='__main__':unittest.main()
