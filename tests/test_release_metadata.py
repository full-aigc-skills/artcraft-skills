"""独立技能源的安装身份必须与技能套件版本一致。"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_package_manifest_and_source_readmes_identify_same_suite(self):
        suite = json.loads((ROOT / 'skill-suite.json').read_text())
        manifest = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], suite['pluginId'] + '-skills')
        self.assertEqual(manifest['version'], suite['version'])
        for filename, pattern in (
            ('README.md', r'Current source snapshot: `([^`]+)`'),
            ('README.zh-CN.md', r'当前技能源快照：`([^`]+)`'),
        ):
            with self.subTest(readme=filename):
                match = re.search(pattern, (ROOT / filename).read_text())
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), suite['version'])


if __name__ == '__main__':
    unittest.main()
