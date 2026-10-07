"""十个独立 Art 技能的公开计划入口必须在安装或输出前拒绝重复键。"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class PublicPlanJsonTests(unittest.TestCase):
    def test_every_independent_gateway_rejects_duplicate_keys_before_side_effects(self):
        plans = [
            '{"schema":"craft-command-plan/v1","schema":"craft-command-plan/v1","operations":[]}',
            '{"schema":"craft-command-plan/v1","operations":[{"command":"x","command":"y","params":{}}]}',
            '{"schema":"craft-command-plan/v1","operations":[{"command":"x","params":{"opacity":1,"opacity":0}}]}'
        ]
        skills = sorted((ROOT / "skills").iterdir())
        self.assertEqual(len(skills), 10)
        for original in skills:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                skill = root / ".agents" / "skills" / original.name
                shutil.copytree(original, skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                before = fingerprint(skill)
                runtime = root / "runtime"
                output = root / "output"
                plan_file = root / "plan.json"
                for domain in ("filmcraft", "effectcraft", "photocraft", "vectorcraft"):
                    for plan in plans:
                        plan_file.write_text(plan)
                        for action in ("check", "run"):
                            argv = [sys.executable, "-I", "-B", str(skill / "scripts/domain_commands.py"),
                                    action, domain, str(plan_file), "--runtime-home", str(runtime)]
                            if action == "run":
                                argv.extend(["--output", str(output)])
                            with self.subTest(skill=original.name, domain=domain, action=action, plan=plan):
                                result = subprocess.run(argv, capture_output=True, text=True, timeout=20)
                                self.assertNotEqual(result.returncode, 0)
                                self.assertIn("duplicate_json_key", result.stdout + result.stderr)
                                self.assertFalse(runtime.exists())
                                self.assertFalse(output.exists())
                self.assertEqual(fingerprint(skill), before)
