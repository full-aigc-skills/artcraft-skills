"""Art 独立分发必须绑定完整命令入口和已修复的协议客户端。"""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class DistributionProtocolTests(unittest.TestCase):
 def test_every_standalone_skill_pins_fixed_complete_domain_helpers(self):
  expected = {"filmcraft": "0.1.0-dev.14", "effectcraft": "0.1.0-dev.13", "photocraft": "0.1.0-dev.13", "vectorcraft": "0.1.0-dev.13"}
  transport = "40f31e45cf21d237f0df2bdcf09cf5a880309616d44b9b7a1b58c952b181ec7d"
  skills = sorted((ROOT/"skills").iterdir())
  self.assertEqual(len(skills), 10)
  for skill in skills:
   lock = json.loads((skill/"scripts/distribution.lock.json").read_text())
   for domain, version in expected.items():
    with self.subTest(skill=skill.name,domain=domain):
     bundle = lock["bundles"][domain+"-skills"]
     self.assertEqual(bundle["version"],version)
     self.assertEqual(bundle["archiveFormat"],"git-archive-zip")
     files = bundle["files"]; prefix = "skills/"+domain+"-use/"
     self.assertEqual(files[prefix+"scripts/mcp_session.py"],transport)
     for resource in ["scripts/commands.py","references/command-reference.md","references/command-usage.md","examples/commands-revision.json"]:
      self.assertIn(prefix+resource,files)
