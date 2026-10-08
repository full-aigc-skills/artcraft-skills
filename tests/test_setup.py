"""发布包安装的摘要、路径和已有版本保护。"""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts/setup.py'
spec = importlib.util.spec_from_file_location('setup', SCRIPT)
setup = importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)

class BundleTests(unittest.TestCase):
    def test_domain_bundle_keeps_its_own_version_when_artcraft_advances(self):
        self.assertEqual(setup.bundle_version({'version': '0.1.0-dev.1'}, {'version': '0.1.0-dev.0'}), '0.1.0-dev.0')
        self.assertEqual(setup.bundle_version({'version': '0.1.0-dev.0'}, {}), '0.1.0-dev.0')

    def test_invalid_explicit_bundle_version_is_not_replaced_with_parent_version(self):
        for version in ('latest', '', None, 42):
            with self.assertRaisesRegex(ValueError, 'bundle_version_invalid'):
                setup.bundle_version({'version': '0.1.0-dev.1'}, {'version': version})

    def test_immutable_runtime_version_is_accepted_and_unsafe_suffixes_are_rejected(self):
        import json
        lock=json.loads((Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts/distribution.lock.json').read_text())
        setup.validate_distribution(lock)
        self.assertEqual(setup.bundle_version(lock,lock['bundles']['artcraft-runtime']),'0.1.0-dev.128-runtime.1')
        for value in ('0.1.0-dev.113-runtime.', '0.1.0-dev.122-runtime.1/escape', '0.1.0-dev.113-other.1'):
            with self.subTest(version=value), self.assertRaisesRegex(ValueError,'bundle_version_invalid'):
                setup.bundle_version(lock,{'version':value})

    def bundle(self, root, unsafe=False):
        archive = root/'bundle.zip'
        with zipfile.ZipFile(archive, 'w') as zip:
            zip.writestr('LICENSE', 'fixture license');zip.writestr('src/cli.ts', 'fixture runtime')
            if unsafe:zip.writestr('../outside', 'bad')
        hashes = {'LICENSE': hashlib.sha256(b'fixture license').hexdigest(), 'src/cli.ts': hashlib.sha256(b'fixture runtime').hexdigest()}
        return archive, {'filename': archive.name, 'url': 'https://github.com/full-aigc-plugins/artcraft-plugin/releases/download/v0.1.0-dev.0/bundle.zip', 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'bytes': archive.stat().st_size, 'files': hashes}

    def test_git_archive_declared_directory_entries_are_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive,lock=self.bundle(root)
            with zipfile.ZipFile(archive,'a') as zip:zip.writestr('src/',b'')
            lock.update(archiveFormat='git-archive-zip',sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
            installed=setup.install_bundle(lock,root/'installed',archive)
            self.assertEqual((installed/'src/cli.ts').read_text(),'fixture runtime')

    def test_directory_entries_need_explicit_format_and_declared_ancestor(self):
        for entry,format in [('src/',None),('unlisted/','git-archive-zip'),('../outside/','git-archive-zip')]:
            with self.subTest(entry=entry,format=format),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);archive,lock=self.bundle(root)
                with zipfile.ZipFile(archive,'a') as zip:zip.writestr(entry,b'')
                lock.update(sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
                if format:lock['archiveFormat']=format
                with self.assertRaisesRegex(ValueError,'bundle_path_invalid'):
                    setup.install_bundle(lock,root/'installed',archive)
                self.assertFalse((root/'installed').exists())

    def test_install_and_reuse_locked_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive,lock=self.bundle(root)
            first=setup.install_bundle(lock, root/'installed', archive)
            self.assertEqual(first, setup.install_bundle(lock, root/'installed', archive))
            self.assertEqual((first/'src/cli.ts').read_text(), 'fixture runtime')

    def test_corrupt_existing_bundle_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive,lock=self.bundle(root)
            target=setup.install_bundle(lock, root/'installed', archive)
            (target/'src/cli.ts').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'bundle_file_digest_mismatch'):
                setup.install_bundle(lock, root/'installed', archive)
            self.assertEqual((target/'src/cli.ts').read_text(), 'changed')

    def test_bad_archive_hash_and_traversal_do_not_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive,lock=self.bundle(root);lock['sha256']='0'*64
            with self.assertRaisesRegex(ValueError, 'bundle_archive_digest_mismatch'):
                setup.install_bundle(lock, root/'installed', archive)
            archive,lock=self.bundle(root, unsafe=True)
            with self.assertRaisesRegex(ValueError, 'bundle_path_invalid'):
                setup.install_bundle(lock, root/'installed', archive)
            self.assertFalse((root/'installed').exists())

if __name__ == '__main__':unittest.main()
