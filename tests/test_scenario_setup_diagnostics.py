"""场景公开入口保留安装失败的结构化诊断，不启动领域或伪造任务。"""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ScenarioSetupDiagnostics(unittest.TestCase):
    def arguments(self, entry, root, skill):
        runtime = root/'runtime'
        if entry == 'workflow.py':
            plan = root/'plan.json'
            plan.write_text(json.dumps({'workflowId':'setup-diagnostic','revision':'v1',
                'nodes':[{'id':'logo','pluginId':'vectorcraft','payload':{}}]}))
            return [str(plan),'--output',str(root/'project'),'--authorization','local-scope','--runtime-home',str(runtime)]
        package = root/'existing package';package.mkdir(exist_ok=True)
        return ['verify','--package',str(package),'--sha','a'*64,'--runtime-home',str(runtime)]

    def test_each_single_skill_scenario_preserves_failed_bootstrap_receipt(self):
        for source in sorted((ROOT/'skills').iterdir()):
            if not (source/'SKILL.md').is_file():continue
            for entry in ('workflow.py','package.py'):
                with self.subTest(skill=source.name,entry=entry),tempfile.TemporaryDirectory(prefix='craft 场景安装 ') as temporary:
                    root=Path(temporary);skill=root/'.agents/skills'/source.name
                    shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
                    (skill/'scripts/distribution.lock.json').write_text('null')
                    result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts'/entry),*self.arguments(entry,root,skill)],capture_output=True,text=True,timeout=20)
                    self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                    reply=json.loads(result.stdout)
                    self.assertEqual(reply.get('dependencySetup'),{'skill':'artcraft-cli-setup',
                        'bootstrapScript':str((skill/'scripts/bootstrap.py').resolve()),
                        'runtimeHome':str(root/'runtime'),'automaticRetry':False})
                    self.assertEqual(reply['installationReceipt']['error'],'distribution_lock_invalid')
                    self.assertFalse(reply['installationReceipt']['installed'])
                    self.assertEqual(reply['result'],'failed')
                    self.assertIn('setup_failed:',reply['error'])
                    self.assertNotIn('workflowReceipt',reply)
                    self.assertFalse((root/'runtime').exists())
                    self.assertFalse((root/'project/tasks.sqlite').exists())
                    self.assertNotIn('Traceback',result.stderr)
                    self.assertEqual(list(skill.parent.iterdir()),[skill])

    def test_bootstrap_start_timeout_and_plain_stderr_are_setup_failures(self):
        cases=[OSError('cannot start installer'),subprocess.TimeoutExpired(['bootstrap'],.1),
            SimpleNamespace(returncode=1,stdout='',stderr='download failed'),
            SimpleNamespace(returncode=1,stdout='[]',stderr='installer diagnostic')]
        for entry in ('workflow.py','package.py'):
            path=ROOT/'skills/artcraft-use/scripts'/entry
            spec=importlib.util.spec_from_file_location('scenario_'+entry,path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            for failure in cases:
                with self.subTest(entry=entry,failure=failure),tempfile.TemporaryDirectory() as temporary:
                    root=Path(temporary);output=io.StringIO();argv=[str(path),*self.arguments(entry,root,path.parent.parent)]
                    kwargs={'side_effect':failure} if isinstance(failure,Exception) else {'return_value':failure}
                    with patch.object(sys,'argv',argv),patch.object(module.subprocess,'run',**kwargs) as launch,contextlib.redirect_stdout(output):
                        with self.assertRaises(SystemExit) as stopped:module.main()
                    self.assertEqual(stopped.exception.code,1)
                    reply=json.loads(output.getvalue());self.assertIn('dependencySetup',reply)
                    self.assertEqual(reply['result'],'unknown' if isinstance(failure,subprocess.TimeoutExpired) else 'failed')
                    launch.assert_called_once();self.assertNotIn('workflowReceipt',reply)
                    if not isinstance(failure,Exception):self.assertIn(failure.stdout or failure.stderr,reply['error'])

    def test_success_exit_with_invalid_setup_receipt_stops_before_native_call(self):
        for entry in ('workflow.py','package.py'):
            path=ROOT/'skills/artcraft-use/scripts'/entry
            spec=importlib.util.spec_from_file_location('invalid_setup_'+entry,path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            for payload in ('null','[]','{}','not json',json.dumps({'schema':'wrong','nodeExecutable':'node','entryPoint':'entry'})):
                with self.subTest(entry=entry,payload=payload),tempfile.TemporaryDirectory() as temporary:
                    root=Path(temporary);output=io.StringIO()
                    result=SimpleNamespace(returncode=0,stdout=payload,stderr='')
                    with patch.object(sys,'argv',[str(path),*self.arguments(entry,root,path.parent.parent)]),patch.object(module.subprocess,'run',return_value=result) as launch,contextlib.redirect_stdout(output):
                        with self.assertRaises(SystemExit) as stopped:module.main()
                    self.assertEqual(stopped.exception.code,1)
                    reply=json.loads(output.getvalue());self.assertIn('dependencySetup',reply)
                    self.assertEqual(reply['result'],'failed');launch.assert_called_once()
                    self.assertNotIn('workflowReceipt',reply)

    def test_input_and_native_failure_do_not_get_installation_diagnostics(self):
        for entry in ('workflow.py','package.py'):
            path=ROOT/'skills/artcraft-use/scripts'/entry
            spec=importlib.util.spec_from_file_location('native_setup_'+entry,path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);output=io.StringIO()
                setup={'schema':'artcraft-setup/v1','nodeExecutable':'fixture-node','entryPoint':'fixture-entry',
                    'pythonExecutable':'fixture-python','pythonSha256':'a'*64,'runtimeHome':'fixture-home',
                    'skills':{'vectorcraft':{'runtimeIdentity':{},'skillRoot':'fixture-skill','executable':'fixture-native','files':[]}}}
                installed=SimpleNamespace(returncode=0,stdout=json.dumps(setup),stderr='')
                with patch.object(sys,'argv',[str(path),*self.arguments(entry,root,path.parent.parent)]),patch.object(module.subprocess,'run',side_effect=[installed,OSError('native error')]) as launch,contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit):module.main()
                reply=json.loads(output.getvalue());self.assertEqual(launch.call_count,2)
                self.assertNotIn('dependencySetup',reply);self.assertNotIn('installationReceipt',reply)
                self.assertEqual(reply['error'],'native error')
                output=io.StringIO()
                with patch.object(sys,'argv',[str(path),*self.arguments(entry,root,path.parent.parent)]),patch.object(module,'execute',side_effect=ValueError('input refused')),contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit):module.main()
                self.assertNotIn('dependencySetup',json.loads(output.getvalue()))

if __name__=='__main__':unittest.main()
