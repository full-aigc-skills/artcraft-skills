"""隔离 Node 安装器失败边界，不依赖全局 Node 或联网。"""
import hashlib
import importlib.util
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/artcraft-use/scripts/bootstrap.py'
spec = importlib.util.spec_from_file_location('bootstrap', SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)

class BootstrapTests(unittest.TestCase):
    def fixture(self, root, bad_path=False, wrong_version=False):
        binary = b'#!/bin/sh\necho v24.21.0\n' if not wrong_version else b'#!/bin/sh\necho v0.0.0\n'
        archive = root / 'node.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            for name, content in [('bin/node', binary), ('LICENSE', b'fixture MIT license')]:
                info = tarfile.TarInfo('node-v24.21.0-darwin-arm64/' + name)
                info.size = len(content);info.mode = 0o755 if name.endswith('node') else 0o644
                tar.addfile(info, io.BytesIO(content))
            if bad_path:
                info = tarfile.TarInfo('../escape');info.size = 1;tar.addfile(info, io.BytesIO(b'x'))
        lock = {'schema': 'artcraft-node-lock/v1', 'version': '24.21.0', 'platform': 'darwin-arm64', 'url': 'https://nodejs.org/dist/v24.21.0/node-v24.21.0-darwin-arm64.tar.gz', 'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'binarySha256': hashlib.sha256(binary).hexdigest()}
        return lock, archive

    def test_install_and_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);lock, archive = self.fixture(root)
            first = bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            second = bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            self.assertEqual(first, second)
            self.assertTrue(Path(first['nodeExecutable']).is_file())
            self.assertTrue((Path(first['nodeExecutable']).parent.parent/'LICENSE').is_file())

    def test_corrupt_archive_and_bad_path_do_not_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);lock, archive = self.fixture(root)
            lock['archiveSha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'archive_digest_mismatch'):
                bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            lock, archive = self.fixture(root, bad_path=True)
            with self.assertRaisesRegex(ValueError, 'archive_path_invalid'):
                bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            self.assertFalse((root/'runtime/artcraft/node/24.21.0').exists())

    def test_wrong_binary_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);lock, archive = self.fixture(root, wrong_version=True)
            with self.assertRaisesRegex(ValueError, 'node_version_mismatch'):
                bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            self.assertFalse((root/'runtime/artcraft/node/24.21.0').exists())

    def test_existing_corrupt_runtime_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);lock, archive = self.fixture(root)
            first = bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            Path(first['nodeExecutable']).write_text('corrupt')
            with self.assertRaisesRegex(ValueError, 'node_digest_mismatch'):
                bootstrap.install_node(lock, root/'runtime', archive, 'darwin-arm64')
            self.assertEqual(Path(first['nodeExecutable']).read_text(), 'corrupt')

    def test_unsupported_platform_rejects_before_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);lock, archive = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'unsupported_platform'):
                bootstrap.install_node(lock, root/'runtime', archive, 'linux-x64')
            self.assertFalse((root/'runtime').exists())

if __name__ == '__main__':
    unittest.main()
