"""每个独立技能必须同时携带固定升级入口、旧状态语义及显式回退边界。"""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class RuntimeUpgradeGuidanceTests(unittest.TestCase):
 def test_all_independent_skills_explain_public_upgrade_receipt_and_safe_compatibility(self):
  for skill in sorted((ROOT/'skills').iterdir()):
   if not (skill/'SKILL.md').is_file():continue
   with self.subTest(skill=skill.name):
    text=(skill/'references/runtime-upgrade.md').read_text()
    self.assertIn('upgrade --database "$DATABASE"',text)
    self.assertIn('snapshot',text)
    self.assertIn('migrated',text)
    self.assertIn('untracked-legacy-schema',text)
    self.assertIn('兼容',text)
    self.assertIn('不重放',text)
    version=json.loads((skill/'scripts/distribution.lock.json').read_text())['bundles']['artcraft-runtime']['version']
    self.assertIn(version,text)
    self.assertIn('references/runtime-upgrade.md',(skill/'SKILL.md').read_text())
if __name__=='__main__':unittest.main()
