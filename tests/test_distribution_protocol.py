"""Art 独立分发必须绑定完整命令入口和已修复的协议客户端。"""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class DistributionProtocolTests(unittest.TestCase):
 def test_every_standalone_skill_pins_fixed_complete_domain_helpers(self):
  expected = {"filmcraft": "0.1.0-dev.38", "effectcraft": "0.1.0-dev.34", "photocraft": "0.1.0-dev.34", "vectorcraft": "0.1.0-dev.33"}
  bootstraps = {'filmcraft': 'bd0c370eace07fe88ae63d4be08374d9b1845b68f0cd43ab0e23a444504623fe', 'effectcraft': 'ad89838b5fd4452685c8cbcfb4394e93597624825356e134e0b809a6a0b3606b', 'photocraft': 'a6e3e9f7b3ab4898b88ecac46fdfa72b32338fcd51d540dde1280882b6813179', 'vectorcraft': '78d5bdf16bf08e9abc96b4b23e5d071da72b648698b888b85fa1b90f81cf32a9'}
  counts = {"filmcraft": 13, "effectcraft": 15, "photocraft": 13, "vectorcraft": 13}
  transport = "ad8a8fb3f84f9fbf814b5a593c96faf3cf9bb476ff32627039975d7f57c86616"
  skills = sorted((ROOT/"skills").iterdir())
  self.assertEqual(len(skills), 10)
  for skill in skills:
   lock = json.loads((skill/"scripts/distribution.lock.json").read_text())
   self.assertEqual(lock["version"], "0.1.0-dev.136-runtime.1")
   self.assertEqual(lock["bundles"]["artcraft-runtime"]["version"], lock["version"])
   for domain, version in expected.items():
    with self.subTest(skill=skill.name,domain=domain):
     bundle = lock["bundles"][domain+"-skills"]
     self.assertEqual(bundle["version"],version)
     self.assertEqual(bundle["archiveFormat"],"git-archive-zip")
     if domain == "photocraft":
      self.assertEqual(bundle['archivePrefix'],'photocraft-skills-0.1.0-dev.34/')
      helpers=[value for path,value in bundle['files'].items() if path.startswith('skills/') and path.endswith('/scripts/delivery.py')]
      self.assertEqual(len(helpers),13);self.assertEqual(len(set(helpers)),1)
     if domain == "vectorcraft":
      self.assertEqual(bundle['archivePrefix'],'vectorcraft-skills-v0.1.0-dev.33/')
      self.assertEqual(bundle['sourceCommit'],'f0b34915172f484e0a39238e9afb56586f1d65d1')
      self.assertEqual(bundle['sha256'],'9583f937fedf25887ead25bb09b19af6aff58125ddeac2aa2866a8ac7fed56be')
      helpers=[value for path,value in bundle['files'].items() if path.startswith('skills/') and path.endswith('/scripts/brand_variants.py')]
      self.assertEqual(len(helpers),13)
      self.assertEqual(set(helpers),{'a600e765e8d2dccbae5c048e70e28e4272844c45fbc0d2eb9d43ca076559daa5'})
     if domain == "filmcraft":
      self.assertEqual(bundle["sourceCommit"], "7d0f68dba98a4a4cbfaaf1f17544be0061735a1d")
      self.assertEqual(bundle["sha256"], "7e39386e9d70f0c552e786d71a26e96bf9e1f86f6bd0c7464e5b7ec4b510949a")
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

 def test_all_skills_trust_gateway_export_inheritance_workflow(self):
  for skill in sorted((ROOT/'skills').iterdir()):
   if not (skill/'SKILL.md').is_file():continue
   lock=json.loads((skill/'scripts/distribution.lock.json').read_text())
   bundle=lock['bundles']['vectorcraft-skills']
   workflows=[value for path,value in bundle['files'].items() if path.startswith('skills/') and path.endswith('/scripts/workflow.py')]
   self.assertEqual(len(workflows),13)
   self.assertEqual(set(workflows),{'5c6b72d061afce38e7bc95bb0d2d250443215c39674cdfc16850c6e1358362a1'})
