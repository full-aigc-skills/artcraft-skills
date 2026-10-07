"""Art 独立分发必须绑定完整命令入口和已修复的协议客户端。"""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class DistributionProtocolTests(unittest.TestCase):
 def test_every_standalone_skill_pins_fixed_complete_domain_helpers(self):
  expected = {"filmcraft": "0.1.0-dev.28", "effectcraft": "0.1.0-dev.29", "photocraft": "0.1.0-dev.29", "vectorcraft": "0.1.0-dev.28"}
  bootstraps = {'filmcraft': '67e2b45008eda54b92172f80d00d0e5abaef3fdaa6463a1ed8b11de462910948', 'effectcraft': '788bb929eb4e3bd84c4245ed8bd0e1e5701926566f292b119818f0af6a74713f', 'photocraft': '9212a3fc41650415584fc373b5cd4877b552e156f066d781d96b20bea5f1402d', 'vectorcraft': '92bdafb23e6199a19640ee90c0f0162c8a8df9f58056e2697b1b61a0d622dcdb'}
  counts = {"filmcraft": 13, "effectcraft": 15, "photocraft": 13, "vectorcraft": 13}
  transport = "ad8a8fb3f84f9fbf814b5a593c96faf3cf9bb476ff32627039975d7f57c86616"
  skills = sorted((ROOT/"skills").iterdir())
  self.assertEqual(len(skills), 10)
  for skill in skills:
   lock = json.loads((skill/"scripts/distribution.lock.json").read_text())
   self.assertEqual(lock["version"], "0.1.0-dev.83")
   self.assertEqual(lock["bundles"]["artcraft-runtime"]["version"], lock["version"])
   for domain, version in expected.items():
    with self.subTest(skill=skill.name,domain=domain):
     bundle = lock["bundles"][domain+"-skills"]
     self.assertEqual(bundle["version"],version)
     self.assertEqual(bundle["archiveFormat"],"git-archive-zip")
     if domain == "effectcraft":
      self.assertEqual(bundle["sha256"], "f1e7040db932a32b3d9df4cefc30279d4c08c5450db1a7b276647c15adaaad2e")
      guides = [value for path, value in bundle["files"].items()
                if path.startswith("skills/") and path.endswith("/references/motion-tracking.md")]
      self.assertEqual(len(guides), 15)
      self.assertEqual(len(set(guides)), 1)
     files = bundle["files"]; prefix = "skills/"+domain+"-use/"
     self.assertEqual(files[prefix+"scripts/mcp_session.py"],transport)
     clients = [value for path,value in files.items() if path.startswith("skills/") and path.endswith("/scripts/mcp_session.py")]
     self.assertEqual(len(clients),counts[domain])
     self.assertEqual(set(clients),{transport})
     preserved = [value for path,value in files.items() if path.startswith("skills/") and path.endswith("/scripts/preserved_stage.py")]
     self.assertEqual(len(preserved),counts[domain])
     self.assertEqual(len(set(preserved)),1)
     self.assertEqual(files[prefix+"scripts/preserved_stage.py"],preserved[0])
     commands = [value for path,value in files.items() if path.startswith("skills/") and path.endswith("/scripts/commands.py")]
     self.assertEqual(len(commands),counts[domain])
     self.assertEqual(set(commands),{{'filmcraft': 'b055d20f64347ead10d940a331f9d1aff929d4f8e1ddc96fb4ede8fcddc02b28', 'effectcraft': '532754b53af61432eca6fb9401528ce2f52ebc3950d9e3545b23e46470ddc00c', 'photocraft': '62169f51086f05a46bdf98ea0007b296f7948bf6853b985e0e13c57ce12dfd8e', 'vectorcraft': 'a3da9d5c5167a0195163596a9aa5b318f7d29838497f74c7956391d053f7548f'}[domain]})
     installers = [value for path,value in files.items() if path.startswith("skills/") and path.endswith("/scripts/bootstrap.py")]
     self.assertEqual(len(installers), counts[domain])
     self.assertEqual(set(installers), {bootstraps[domain]})
     for resource in ["scripts/native_workflow.py","references/command-coverage.json","examples/native-workflow.json","scripts/commands.py","references/command-reference.md","references/command-usage.md","examples/commands-revision.json","scripts/desktop.py","scripts/desktop_session.py","scripts/desktop.lock.json","examples/desktop-first-use.json"]:
      self.assertIn(prefix+resource,files)
