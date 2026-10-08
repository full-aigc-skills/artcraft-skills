"""同一需求样本核对独立 Python 技能与 TypeScript 运行时，避免入口约束漂移。"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def scenarios():
    budget = dict(currency='USD', maxMinorUnits=0, maxRevisions=2, maxExternalCalls=0)
    deliverables = [dict(id=name, nativeFormat=fmt, width=320, height=180,
                         dependsOn=parents, execution='local')
                    for name, fmt, parents in [('logo', '.vectorcraft', []),
                                               ('poster', '.pcraft', ['logo']),
                                               ('icon', '.vectorcraft', [])]]
    brief = dict(schema='craft-brief/v1', workflowId='brand', revision='brief-v1',
                 ownerId='user', authorizationRef='scope', budget=budget,
                 brand=dict(name='NOVA', colors=['#ef5b36'], fonts=['Arial'],
                            appliesTo=['logo'], referenceAssets=[]),
                 subjects=[], dataPolicy=dict(allowUpload=False), ambiguities=[],
                 deliverables=deliverables)
    plan = dict(workflowId='brand', ownerId='user', authorizationRef='scope', budget=budget,
                nodes=[dict(id=d['id'], pluginId=plugin, dependsOn=d['dependsOn'],
                            payload=dict(plan=dict(document=dict(width=320, height=180), operations=[])))
                       for d, plugin in zip(deliverables, ['vectorcraft', 'photocraft', 'vectorcraft'])])
    cases = []

    def add(name, mutate, ready, reasons=None, error=None):
        b, p = copy.deepcopy((brief, plan))
        mutate(b, p)
        cases.append(dict(name=name, brief=b, plan=p, ready=ready,
                          reasons=reasons or {}, error=error))

    add('ready', lambda b, p: None, ['logo', 'poster', 'icon'])
    add('ambiguity', lambda b, p: b['ambiguities'].append(
        dict(id='title', question='Confirm title', affects=['logo'])), ['icon'],
        {'logo': ['ambiguity:title'], 'poster': ['dependency_blocked']})
    add('upload-forbidden', lambda b, p: b['deliverables'][0].update(execution='cloud'), ['icon'],
        {'logo': ['upload_forbidden'], 'poster': ['dependency_blocked']})
    add('cloud-unavailable', lambda b, p: (b['dataPolicy'].update(allowUpload=True),
        b['deliverables'][0].update(execution='cloud')), ['icon'],
        {'logo': ['cloud_executor_missing'], 'poster': ['dependency_blocked']})
    ref = dict(assetId='brand-reference', version='v2', sha256='a' * 64)

    def reference(b, p, version='v2', digest='a' * 64):
        b['brand']['referenceAssets'] = [ref]
        p['nodes'][0]['externalInputs'] = [dict(artifact=dict(ref, version=version, sha256=digest))]

    add('exact-reference', reference, ['logo', 'poster', 'icon'])
    add('stale-reference-version', lambda b, p: reference(b, p, version='v1'), ['icon'],
        {'logo': ['reference_asset_missing_or_stale'], 'poster': ['dependency_blocked']})
    add('stale-reference-bytes', lambda b, p: reference(b, p, digest='b' * 64), ['icon'],
        {'logo': ['reference_asset_missing_or_stale'], 'poster': ['dependency_blocked']})
    add('nested-brand-font', lambda b, p: p['nodes'][0]['payload']['plan']['operations'].append(
        dict(params=dict(style=[dict(font='Other')]))), ['icon'],
        {'logo': ['brand_font_mismatch'], 'poster': ['dependency_blocked']})
    add('native-format-substitution', lambda b, p: p['nodes'][0].update(pluginId='photocraft'), ['icon'],
        {'logo': ['native_format_mismatch'], 'poster': ['dependency_blocked']})
    add('size-conflict', lambda b, p: p['nodes'][0]['payload']['plan']['document'].update(width=321), ['icon'],
        {'logo': ['document_size_mismatch'], 'poster': ['dependency_blocked']})
    def subject(b, p, supplied):
        b['subjects'] = [dict(id='product', role='hero', description='Product reference',
                              appliesTo=['poster'], referenceAssets=[ref])]
        if supplied:
            p['nodes'][1]['externalInputs'] = [dict(artifact=ref)]

    add('subject-reference-present', lambda b, p: subject(b, p, True), ['logo', 'poster', 'icon'])
    add('subject-reference-missing', lambda b, p: subject(b, p, False), ['logo', 'icon'],
        {'poster': ['reference_asset_missing_or_stale']})
    def film(b, p, duration):
        b['deliverables'][0].update(nativeFormat='.fcproj', durationSeconds=1)
        p['nodes'][0]['pluginId'] = 'filmcraft'
        p['nodes'][0]['payload']['plan']['operations'] = [dict(command='timeline.place', params=dict(
            time='0', duration='254016000000', insert=False, track='V1')), dict(command='timeline.place',
            params=dict(time='0', duration=duration, insert=False, track='A1'))]

    add('film-all-tracks-match', lambda b, p: film(b, p, '254016000000'), ['logo', 'poster', 'icon'])
    add('film-long-audio', lambda b, p: film(b, p, '508032000000'), ['icon'],
        {'logo': ['duration_mismatch'], 'poster': ['dependency_blocked']})
    add('owner-conflict', lambda b, p: b.update(ownerId='other'), [], error='brief_authorization_mismatch')
    add('authorization-conflict', lambda b, p: b.update(authorizationRef='other'), [], error='brief_authorization_mismatch')
    add('budget-conflict', lambda b, p: p.update(budget=dict(b['budget'], maxMinorUnits=1)), [],
        error='brief_budget_mismatch')
    add('workflow-conflict', lambda b, p: p.update(workflowId='other'), [], error='brief_workflow_mismatch')
    add('missing-deliverable', lambda b, p: p['nodes'].pop(), [], error='brief_plan_deliverable_missing')
    return cases


@unittest.skipUnless(os.environ.get('CRAFT_BRIEF_PARITY_RUNTIME') and os.environ.get('CRAFT_BRIEF_PARITY_NODE'),
                     'requires explicit Art runtime source and Node executable; does not install tools')
class BriefContractParityTests(unittest.TestCase):
    def test_both_entrypoints_enforce_the_same_observable_contract(self):
        runtime = Path(os.environ['CRAFT_BRIEF_PARITY_RUNTIME']).resolve()
        script = ROOT / 'skills/artcraft-use/scripts/brief.py'
        spec = importlib.util.spec_from_file_location('brief_parity', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        values = scenarios()
        javascript = '''
          import {readFileSync} from 'node:fs';
          const {assessBrief}=await import(process.argv[1]);
          const result=JSON.parse(readFileSync(0,'utf8')).map(({brief,plan})=>{
            try{return {assessment:assessBrief(brief,plan)}}
            catch(error){return {error:error.message}}
          });
          process.stdout.write(JSON.stringify(result));
        '''
        command = [os.environ['CRAFT_BRIEF_PARITY_NODE'], '--input-type=module', '-e', javascript,
                   (runtime / 'src/planning/project_brief.ts').as_uri()]
        completed = subprocess.run(command, input=json.dumps(values), capture_output=True,
                                   text=True, timeout=60, check=True)
        actual = json.loads(completed.stdout)
        self.assertEqual(len(actual), len(values))
        for case, node_result in zip(values, actual):
            with self.subTest(scenario=case['name']):
                try:
                    python_result = dict(assessment=module.assess(case['brief'], case['plan'], 'user', 'scope'))
                except ValueError as error:
                    python_result = dict(error=str(error))
                self.assertEqual(python_result, node_result)
                if case['error']:
                    self.assertEqual(python_result, dict(error=case['error']))
                else:
                    assessment = python_result['assessment']
                    self.assertEqual(assessment['ready'], case['ready'])
                    self.assertEqual({row['nodeId']: row['reasons'] for row in assessment['blocked']}, case['reasons'])
                    self.assertEqual(assessment['state'], 'blocked' if case['reasons'] else 'ready')
        proof_path = os.environ.get('CRAFT_BRIEF_PARITY_PROOF')
        if proof_path:
            files = [script, runtime / 'src/planning/project_brief.ts', Path(__file__)]
            Path(proof_path).write_text(json.dumps(dict(
                schema='craft-brief-contract-parity/v1', result='PASS',
                cases=[case['name'] for case in values],
                files={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                inputSha256=hashlib.sha256(json.dumps(values).encode()).hexdigest(),
                stdoutSha256=hashlib.sha256(completed.stdout.encode()).hexdigest(),
                scope='declared constraint parity only; not native or installed-host acceptance'
            ), indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
