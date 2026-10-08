"""跨产物观察必须绑定同一组真实品牌与主体参考，旧审阅合同保持兼容。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ConsistencyTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('review', ROOT / 'skills/artcraft-use/scripts/review.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, root):
        def asset(node):
            return {'nodeId': node, 'assetId': node + '-png', 'version': 'v1',
                    'sha256': hashlib.sha256(node.encode()).hexdigest()}
        references = [{'id': 'logo', 'role': 'brand', 'asset': asset('logo')},
                      {'id': 'product', 'role': 'subject', 'asset': asset('product')}]
        children = [{'nodeId': node, 'runtimeIdentity': {'pluginId': domain, 'cliVersion': 'fixture'},
                     'outputs': [asset(node)]} for node, domain in
                    [('logo', 'vectorcraft'), ('product', 'vectorcraft'), ('poster', 'photocraft'),
                     ('intro', 'effectcraft'), ('film', 'filmcraft')]]
        package = {'sha256': 'b' * 64, 'workflow': {'planSha256': 'c' * 64,
                   'ownerId': 'fixture-user', 'authorizationRef': 'fixture-scope'}, 'children': children}
        checks = []
        for node in ('poster', 'intro', 'film'):
            target = asset(node)
            target.update(region={'x': 0, 'y': 0, 'width': 1, 'height': 1})
            if node != 'poster':
                target['frame'] = 0
            actor = {'kind': 'tool', 'id': 'fixture-comparator', 'version': 'test-1'}
            observation = {'schema': 'craft-consistency-observation/v1', 'checkId': node,
                           'target': target, 'references': references, 'evaluator': actor,
                           'status': 'PASS', 'method': 'unit fixture only, not real media evaluation',
                           'observations': [{'description': 'Reference binding fixture'}]}
            file = root / (node + '.json')
            file.write_text(json.dumps(observation))
            checks.append({'id': node, 'dimension': 'creative', 'status': 'PASS', 'evaluator': actor,
                           'target': target, 'evidence': [{'location': file.name,
                           'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}],
                           'note': 'Unit fixture only, not creative acceptance'})
        value = {'schema': 'craft-review-input/v1', 'packageSha256': package['sha256'],
                 **package['workflow'], 'brandReferences': [asset('logo')], 'checks': checks,
                 'consistency': {'schema': 'craft-consistency/v1', 'references': references,
                                 'assessments': [{'checkId': c['id'], 'referenceIds': ['logo', 'product']}
                                                 for c in checks]}}
        return package, value

    def test_three_outputs_share_fixed_reference_observations_without_human_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); package, value = self.fixture(root)
            result = self.module().evaluate(value, package, root)
            self.assertEqual(result['consistency']['result'], 'PASS')
            self.assertEqual(result['consistency']['domains'], ['effectcraft', 'filmcraft', 'photocraft'])
            self.assertEqual(len(result['consistency']['assessments']), 3)
            self.assertEqual(result['decision'], 'pending')
            self.assertEqual(result['taskState'], 'review_ready')

    def test_missing_observations_or_domain_does_not_claim_consistency_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); package, value = self.fixture(root)
            value['checks'].pop(); value['consistency']['assessments'].pop()
            result = self.module().evaluate(value, package, root)
            self.assertEqual(result['consistency']['result'], 'NOT_RUN')
            self.assertEqual(result['consistency']['missingDomains'], ['filmcraft'])

    def test_rejects_missing_roles_reference_subset_old_versions_and_observation_mismatch(self):
        mutations = [lambda v: v['consistency']['references'].pop(),
                     lambda v: v['consistency']['references'][1].update(role='brand'),
                     lambda v: v['consistency']['references'][0]['asset'].update(version='old'),
                     lambda v: v['consistency']['assessments'][0].update(referenceIds=['logo']),
                     lambda v: v['consistency']['assessments'][0].update(checkId='missing'),
                     lambda v: v['checks'][0]['target'].pop('region'),
                     lambda v: v['checks'][1]['target'].pop('frame')]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); package, value = self.fixture(root); mutation(value)
                with self.assertRaises(ValueError):
                    self.module().evaluate(value, package, root)

    def test_hash_bound_prompt_or_mismatched_observation_is_not_consistency_evidence(self):
        for change in ('prompt', 'target', 'references', 'status', 'actor', 'empty'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); package, value = self.fixture(root)
                file = root / 'poster.json'; observation = json.loads(file.read_text())
                if change == 'prompt': observation = {'prompt': 'make everything consistent'}
                elif change == 'target': observation['target']['sha256'] = '0' * 64
                elif change == 'references': observation['references'].pop()
                elif change == 'status': observation['status'] = 'FAIL'
                elif change == 'actor': observation['evaluator']['id'] = 'other'
                else: observation['observations'] = []
                file.write_text(json.dumps(observation))
                value['checks'][0]['evidence'][0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
                with self.assertRaises(ValueError): self.module().evaluate(value, package, root)

    def test_failure_has_asset_version_and_region_and_does_not_disappear(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); package, value = self.fixture(root)
            value['checks'][0]['status'] = 'FAIL'
            file = root / 'poster.json'; observation = json.loads(file.read_text()); observation['status'] = 'FAIL'
            file.write_text(json.dumps(observation))
            value['checks'][0]['evidence'][0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            result = self.module().evaluate(value, package, root)
            self.assertEqual(result['consistency']['result'], 'FAIL')
            self.assertEqual(result['consistency']['issues'][0]['target'], value['checks'][0]['target'])
            self.assertEqual(result['decision'], 'changes_requested')

    def test_unreviewed_second_poster_and_not_run_observation_prevent_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); package, value = self.fixture(root)
            missing = {**package['children'][2]['outputs'][0], 'assetId': 'cover-png'}
            package['children'][2]['outputs'].append(missing)
            result = self.module().evaluate(value, package, root)['consistency']
            self.assertEqual(result['result'], 'NOT_RUN')
            self.assertEqual(result['missingTargets'], [missing])
            package['children'][2]['outputs'].pop()
            value['checks'][1].update(status='NOT_RUN', evidence=[])
            result = self.module().evaluate(value, package, root)['consistency']
            self.assertEqual(result['result'], 'NOT_RUN')
            self.assertEqual(result['missingDomains'], ['effectcraft'])

    def test_duplicate_refs_and_assessments_are_rejected(self):
        for kind in ('reference', 'assessment', 'asset'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); package, value = self.fixture(root)
                c = value['consistency']
                if kind == 'reference': c['references'].append(c['references'][0])
                elif kind == 'assessment': c['assessments'].append(c['assessments'][0])
                else: c['references'][1]['asset'] = c['references'][0]['asset']
                with self.assertRaises(ValueError): self.module().evaluate(value, package, root)

    def test_moved_record_recomputes_consistency_and_rejects_forged_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); package, value = self.fixture(root); m = self.module()
            source = root / 'input.json'; source.write_text(json.dumps(value))
            delivery = root / 'package'; delivery.mkdir()
            args = Namespace(input=source, output=root/'review', package=delivery)
            with patch.object(m, 'verify_package', return_value=package):
                receipt = m.record(args, package)
            moved = root / 'moved'; args.output.rename(moved)
            args.review, args.review_sha = moved, receipt['sha256']
            self.assertEqual(m.verify_record(args, package)['consistency']['result'], 'PASS')
            # 伪造报告且重新计算外层摘要也不能绕过观察结果复算。
            report_path = moved / 'review.json'
            report = json.loads(report_path.read_text()); report['consistency']['result'] = 'FAIL'
            report_path.write_text(json.dumps(report))
            args.review_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'review_record_result_mismatch'):
                m.verify_record(args, package)
            report.pop('consistency'); report_path.write_text(json.dumps(report))
            args.review_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'review_record_result_mismatch'):
                m.verify_record(args, package)

    def test_stale_reference_or_unbound_target_requires_reevaluation(self):
        for kind in ('reference-version', 'target-digest'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); package, value = self.fixture(root)
                if kind == 'reference-version':
                    value['consistency']['references'][0]['asset']['version'] = 'old'
                else:
                    value['checks'][0]['target'].pop('sha256')
                try:
                    self.module().evaluate(value, package, root)
                except ValueError as error:
                    self.assertEqual(error.diagnostic['consistency']['result'], 'STALE')
                    self.assertEqual(error.diagnostic['consistency']['action'], 'reevaluate')
                else:
                    self.fail('Stale evidence was accepted')
