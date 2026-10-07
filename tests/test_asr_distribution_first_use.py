"""独立Art技能冷安装选择Film领域，并确认真实Whisper及模型目录。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_ART_ASR_DISTRIBUTION')=='1','requires retained public cold installation')
class AsrDistributionTests(unittest.TestCase):
    def test_single_art_skill_installs_whisper_capable_film(self):
        output=Path(os.environ['CRAFT_ART_ASR_OUTPUT']).resolve();output.mkdir(parents=True,exist_ok=False)
        skill=output/'.agents/skills/artcraft-use'
        shutil.copytree(ROOT/'skills/artcraft-use',skill,ignore=shutil.ignore_patterns('__pycache__'))
        runtime=output/'fresh-runtime';data=output/'declared-data'
        env={k:v for k,v in os.environ.items() if not k.startswith('CRAFT_')};env['PATH']='/usr/bin:/bin';env['FILMCRAFT_DATA_DIR']=str(data)
        setup=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/bootstrap.py'),'--runtime-home',str(runtime),'--plugin','filmcraft'],env=env,capture_output=True,text=True,timeout=600)
        (output/'setup.log').write_text(setup.stdout+setup.stderr);self.assertEqual(setup.returncode,0,setup.stdout+setup.stderr)
        receipt=json.loads(setup.stdout);self.assertEqual(set(receipt['skills']),{'filmcraft'})
        cli=receipt['skills']['filmcraft']['executable']
        query=subprocess.run([cli,'exec','transcript.models','--data-dir',str(data)],env=env,capture_output=True,text=True,timeout=60)
        (output/'models.log').write_text(query.stdout+query.stderr);self.assertEqual(query.returncode,0,query.stdout+query.stderr)
        models=json.loads(query.stdout);self.assertTrue(models['available'],'Art distribution must install actual Whisper runtime')
        self.assertEqual(Path(models['dir']),data/'models');self.assertFalse(any(m['installed'] for m in models['models']))
        self.assertFalse(any((runtime/d).exists() for d in ['effectcraft','photocraft','vectorcraft']))
        proof={'result':'PASS','scope':'Public Art runtime and selected Film distribution cold setup; real inference/mixed DAG separate','runtimeIdentity':receipt['skills']['filmcraft']['runtimeIdentity'],'bundleHashes':receipt['bundleHashes'],'modelsDirCorrect':True,'unusedDomainsAbsent':True,'skillFiles':{str(p.relative_to(skill)):hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()}}
        (output/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
