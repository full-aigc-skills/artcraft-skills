"""Art 独立分发必须绑定完整命令入口和已修复的协议客户端。"""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class DistributionProtocolTests(unittest.TestCase):
 def test_every_standalone_skill_pins_fixed_complete_domain_helpers(self):
  expected = {"filmcraft": "0.1.0-dev.36", "effectcraft": "0.1.0-dev.34", "photocraft": "0.1.0-dev.33", "vectorcraft": "0.1.0-dev.31"}
  bootstraps = {'filmcraft': 'bd0c370eace07fe88ae63d4be08374d9b1845b68f0cd43ab0e23a444504623fe', 'effectcraft': 'ad89838b5fd4452685c8cbcfb4394e93597624825356e134e0b809a6a0b3606b', 'photocraft': 'a6e3e9f7b3ab4898b88ecac46fdfa72b32338fcd51d540dde1280882b6813179', 'vectorcraft': '78d5bdf16bf08e9abc96b4b23e5d071da72b648698b888b85fa1b90f81cf32a9'}
  counts = {"filmcraft": 13, "effectcraft": 15, "photocraft": 13, "vectorcraft": 13}
  transport = "ad8a8fb3f84f9fbf814b5a593c96faf3cf9bb476ff32627039975d7f57c86616"
  skills = sorted((ROOT/"skills").iterdir())
  self.assertEqual(len(skills), 10)
  for skill in skills:
   lock = json.loads((skill/"scripts/distribution.lock.json").read_text())
   self.assertEqual(lock["version"], "0.1.0-dev.113-runtime.1")
   self.assertEqual(lock["bundles"]["artcraft-runtime"]["version"], lock["version"])
   for domain, version in expected.items():
    with self.subTest(skill=skill.name,domain=domain):
     bundle = lock["bundles"][domain+"-skills"]
     self.assertEqual(bundle["version"],version)
     self.assertEqual(bundle["archiveFormat"],"git-archive-zip")
     if domain == "filmcraft":
      self.assertEqual(bundle["sourceCommit"], "b65c2675cdb6cce9da0ee5a07dae50e5c819e73e")
      self.assertEqual(bundle["sha256"], "201e522b0356e32cf12f897be337ff61abb42be8556147631d82029856a67fd7")
     for suffix in ["/scripts/output_guard.py", "/references/output-execution.md"]:
      guards = [value for path, value in bundle["files"].items()
                if path.startswith("skills/") and path.endswith(suffix)]
      self.assertEqual(len(guards), counts[domain])
      self.assertEqual(len(set(guards)), 1)
     if domain == "effectcraft":
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
