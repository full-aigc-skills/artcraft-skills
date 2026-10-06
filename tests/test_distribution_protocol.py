"""Art 独立分发必须绑定完整命令入口和已修复的协议客户端。"""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class DistributionProtocolTests(unittest.TestCase):
 def test_every_standalone_skill_pins_fixed_complete_domain_helpers(self):
  expected = {"filmcraft": "0.1.0-dev.19", "effectcraft": "0.1.0-dev.18", "photocraft": "0.1.0-dev.18", "vectorcraft": "0.1.0-dev.19"}
  bootstraps = {'filmcraft': '4ccde613d5bb41ef6889ea7c0f240d7e11844c4e0bdc0b23ff4e548094c31478', 'effectcraft': '29d147df9357059024a5a6a8df1b5971a669343be96b1df18c16da4fc85576e6', 'photocraft': '2f6d9b94f456593870ca2eafcfafd4e02d69b04597d5d3e42e3e651d29f43133', 'vectorcraft': '594af69f53e2df5accba79e0b611e46fdbe2adb1aa172cd7bc983f50e78f255e'}
  counts = {"filmcraft": 11, "effectcraft": 13, "photocraft": 12, "vectorcraft": 12}
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
     self.assertEqual(set(commands),{'d402df57f920ebb87ea852d5dcd2eb87caa1e0103dd44d098aa720e465593583'})
     installers = [value for path,value in files.items() if path.startswith("skills/") and path.endswith("/scripts/bootstrap.py")]
     self.assertEqual(len(installers), counts[domain])
     self.assertEqual(set(installers), {bootstraps[domain]})
     for resource in ["scripts/native_workflow.py","references/command-coverage.json","examples/native-workflow.json","scripts/commands.py","references/command-reference.md","references/command-usage.md","examples/commands-revision.json"]:
      self.assertIn(prefix+resource,files)
