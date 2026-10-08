"""真实占锁进程下的 Art 首用安装等待、超时与重试。"""
import contextlib
import io
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import test_bootstrap as fixtures

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/artcraft-use/scripts'


@contextlib.contextmanager
def held_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    code = "import fcntl,sys; f=open(sys.argv[1],'a+b'); fcntl.flock(f,fcntl.LOCK_EX); print('ready',flush=True); sys.stdin.read()"
    process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code, str(path)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        if process.stdout.readline().strip() != 'ready':
            raise AssertionError('holder failed to acquire lock')
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=3)


class InstallMutexTests(unittest.TestCase):
    def call_with_busy_lock(self, script, home, lock_path, args):
        lock_file = home/'fixture-lock.json'
        lock_file.write_text(args[2])
        args = [*args[:2], str(lock_file), *args[3:]]
        code = """import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('installer',sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.LOCK_WAIT_SECONDS=0.15
try:
 if sys.argv[2]=='node': m.install_node(json.loads(Path(sys.argv[4]).read_text()),sys.argv[3],sys.argv[5],'darwin-arm64')
 else: m.setup(json.loads(Path(sys.argv[4]).read_text()),sys.argv[3],{},plugins=[])
except Exception as e: print(json.dumps({'type':type(e).__name__,'error':str(e)}))
else: print(json.dumps({'type':'unexpected success'}))
"""
        with held_lock(lock_path):
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(SCRIPTS/script), *args],
                                    capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        reply = json.loads(result.stdout)
        self.assertEqual(reply['type'], 'TimeoutError')
        self.assertIn('runtime_install_busy', reply['error'])

    def test_node_busy_timeout_preserves_install_and_retry_after_holder_dies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root/'runtime'
            lock, archive = fixtures.BootstrapTests().fixture(root)
            first = fixtures.bootstrap.install_node(lock, home, archive, 'darwin-arm64')
            binary = Path(first['nodeExecutable']); original = binary.read_bytes()
            self.call_with_busy_lock('bootstrap.py', home, home/'.artcraft-node-install.lock',
                                     ['node', str(home), json.dumps(lock), str(archive)])
            self.assertEqual(binary.read_bytes(), original)
            archive.unlink()
            self.assertEqual(fixtures.bootstrap.install_node(lock, home, archive, 'darwin-arm64'), first)

    def test_bundle_busy_timeout_precedes_download_and_preserves_user_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary); sentinel = home/'user-project.fcproj'; sentinel.write_bytes(b'user project')
            lock = json.loads((SCRIPTS/'distribution.lock.json').read_text())
            self.call_with_busy_lock('setup.py', home, home/'.artcraft-setup.lock',
                                     ['setup', str(home), json.dumps(lock)])
            self.assertEqual(sentinel.read_bytes(), b'user project')
            self.assertFalse((home/'artcraft/bundles').exists())

    def test_node_waits_then_reuses_install_after_owner_exits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root/'runtime'
            lock, archive = fixtures.BootstrapTests().fixture(root)
            first = fixtures.bootstrap.install_node(lock, home, archive, 'darwin-arm64')
            archive.unlink()
            with held_lock(home/'.artcraft-node-install.lock') as holder:
                timer = threading.Timer(.1, holder.kill); timer.start()
                try:
                    with patch.object(fixtures.bootstrap, 'LOCK_WAIT_SECONDS', 2):
                        result = fixtures.bootstrap.install_node(lock, home, archive, 'darwin-arm64')
                finally:
                    timer.join()
            self.assertEqual(result, first)

    def test_public_bootstrap_timeout_keeps_own_setup_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary); output = io.StringIO()
            with held_lock(home/'.artcraft-node-install.lock'), \
                    patch.object(fixtures.bootstrap, 'LOCK_WAIT_SECONDS', .1), \
                    patch.object(sys, 'argv', [str(SCRIPTS/'bootstrap.py'), '--runtime-home', str(home), '--node-only']), \
                    contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as failure:
                    fixtures.bootstrap.main()
            self.assertEqual(failure.exception.code, 1)
            reply = json.loads(output.getvalue())
            self.assertFalse(reply['installed'])
            self.assertIn('runtime_install_busy', reply['error'])
            self.assertEqual(reply['dependencySetup']['skill'], 'artcraft-cli-setup')
            self.assertFalse((home/'artcraft').exists())


if __name__ == '__main__':
    unittest.main()
