"""只复制规划技能的公开 Brief CLI；不安装 Node 或原生运行时。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class FilmBriefCli(unittest.TestCase):
 def test_public_assess_accepts_precise_timeline_and_refuses_false_document_duration(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);skill=root/'only-plan';shutil.copytree(ROOT/'skills/artcraft-cli-plan',skill,ignore=shutil.ignore_patterns('__pycache__'))
   brief=json.loads((skill/'examples/brand-brief.json').read_text());brief['brand']=None;brief['subjects']=[];item=next(d for d in brief['deliverables'] if d['id']=='film');item.update(dependsOn=[],durationSeconds=1);brief['deliverables']=[item]
   plan=json.loads((skill/'examples/brand-campaign.json').read_text());node=next(n for n in plan['nodes'] if n['id']=='film');node['dependsOn']=[];plan['nodes']=[node]
   original=root/'input.json';original.write_text(json.dumps(brief));record=root/'brief'
   def run(args):return subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/brief.py'),*map(str,args)],env={**os.environ,'PATH':'/usr/bin:/bin'},capture_output=True,text=True,timeout=30)
   result=run(['create','--input',original,'--output',record]);self.assertEqual(result.returncode,0,result.stdout+result.stderr);receipt=json.loads(result.stdout)
   file=root/'plan.json';file.write_text(json.dumps(plan));args=['assess','--brief',record,'--sha',receipt['sha256'],'--plan',file,'--owner',brief['ownerId'],'--authorization',brief['authorizationRef']]
   result=run(args);self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertEqual(json.loads(result.stdout)['state'],'ready')
   before={p.name:p.read_bytes() for p in record.iterdir()};node['payload']['plan']['document']['duration']=1
   for operation in node['payload']['plan']['operations']:
    if operation['command']=='timeline.place' and operation['params']['track']=='A1':operation['params']['duration']='508032000000'
   file.write_text(json.dumps(plan));result=run(args);self.assertEqual(result.returncode,0,result.stdout+result.stderr);report=json.loads(result.stdout);self.assertEqual(report['state'],'blocked');self.assertIn('duration_mismatch',report['blocked'][0]['reasons'])
   self.assertEqual(before,{p.name:p.read_bytes() for p in record.iterdir()});self.assertFalse(list(skill.rglob('*.pyc')))
if __name__=='__main__':unittest.main()
