"""公开工作流必须先拒绝未知执行器，安装边界必须仅接收任务所需领域。"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get('CRAFT_ROUTING_SCRIPT_SOURCE', ROOT / 'skills/artcraft-use/scripts/workflow.py'))


class RoutingBoundaryTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('routing_boundary', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self):
        value = json.loads((ROOT / 'skills/artcraft-use/examples/brand-campaign.json').read_text())
        value['nodes'] = [value['nodes'][0]]
        return value

    def test_vector_plan_requests_only_vector_at_installation_boundary(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / 'plan.json'
            plan.write_text(json.dumps(self.fixture()))
            calls = []

            def stop_at_installation(command, **kwargs):
                calls.append(command)
                raise ValueError('installation_boundary_probe')

            with patch.object(module.subprocess, 'run', side_effect=stop_at_installation):
                with self.assertRaisesRegex(ValueError, 'installation_boundary_probe'):
                    module.execute(plan, root / 'project', 'owner', 'authority', runtime_home=root / 'runtime')
            self.assertEqual(len(calls), 1)
            command = calls[0]
            self.assertEqual([command[index + 1] for index, value in enumerate(command) if value == '--plugin'],
                             ['vectorcraft'])
            self.assertFalse((root / 'runtime').exists())

    def test_jianying_is_refused_before_any_installer(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = self.fixture()
            value['nodes'][0]['pluginId'] = 'jianying'
            plan = root / 'plan.json'
            plan.write_text(json.dumps(value))
            with patch.object(module.subprocess, 'run', side_effect=AssertionError('installer reached')) as process:
                with self.assertRaisesRegex(ValueError, 'capability_missing: jianying'):
                    module.execute(plan, root / 'project', 'owner', 'authority', runtime_home=root / 'runtime')
                process.assert_not_called()
            self.assertFalse((root / 'runtime').exists())

    def test_conflicting_runtime_identity_cannot_select_another_domain(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = self.fixture()
            value['nodes'][0]['runtimeIdentity'] = {'pluginId': 'filmcraft'}
            plan = root / 'plan.json'
            plan.write_text(json.dumps(value))
            with patch.object(module.subprocess, 'run', side_effect=AssertionError('installer reached')) as process:
                with self.assertRaisesRegex(ValueError, 'runtime_identity_mismatch'):
                    module.execute(plan, root / 'project', 'owner', 'authority', runtime_home=root / 'runtime')
                process.assert_not_called()
            self.assertFalse((root / 'runtime').exists())


if __name__ == '__main__':
    unittest.main()
