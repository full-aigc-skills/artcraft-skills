"""只有安装器和锁文件的干净目录安装实际官方 Node；不是完整 ArtCraft 验收。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts'

@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST') == '1' and os.environ.get('CRAFT_NODE_ARCHIVE'), 'requires verified official archive')
class FirstUseTests(unittest.TestCase):
    def test_clean_copy_installs_real_node_without_global_node(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);skill = root/'single-skill/scripts';skill.mkdir(parents=True)
            for name in ('bootstrap.py', 'node.lock.json'):
                shutil.copy2(SOURCE/name, skill/name)
            argv = [os.path.realpath(os.sys.executable), str(skill/'bootstrap.py'), '--runtime-home', str(root/'runtime'), '--node-archive', os.environ['CRAFT_NODE_ARCHIVE'], '--node-only']
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            first = json.loads(subprocess.run(argv, check=True, capture_output=True, text=True, env=environment, timeout=120).stdout)
            actual = subprocess.run([first['nodeExecutable'], '--version'], check=True, capture_output=True, text=True, env=environment, timeout=10).stdout.strip()
            self.assertEqual(actual, 'v24.21.0')
            self.assertEqual(first, json.loads(subprocess.run(argv, check=True, capture_output=True, text=True, env=environment, timeout=30).stdout))
            self.assertTrue(Path(first['nodeExecutable']).is_relative_to(root.resolve()))

if __name__ == '__main__':
    unittest.main()
