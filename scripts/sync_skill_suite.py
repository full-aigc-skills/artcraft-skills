#!/usr/bin/env python3
"""同步套件资源；执行实现唯一收敛在 artcraft-harness，知识入口与场景指南分别维护，来源仍在本独立仓库。"""
import argparse
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
# harness 从 use 技能字节复制的执行契约清单；文档类参考不再进入 harness。
HARNESS_REFERENCE_FILES=('domain-command-index.json','mode-command-catalog.json')
HARNESS_ENTRY_SCRIPTS=('bootstrap.py','workflow.py','cli.py','domain_commands.py','package.py','review.py','revision.py','brief.py')
def sync(check=False):
 suite=json.loads((ROOT/'skill-suite.json').read_text(encoding='utf-8'));base=ROOT/'skills'/(suite['pluginId']+'-use');errors=[]
 harness=ROOT/'skills'/(suite['pluginId']+'-harness')
 # 执行实现只存在于 harness：入口脚本必须齐备；执行契约 JSON 与 use 技能保持字节一致。
 for name in HARNESS_ENTRY_SCRIPTS:
  if not (harness/'scripts'/name).is_file():errors.append(str((harness/'scripts'/name).relative_to(ROOT)))
 for name in HARNESS_REFERENCE_FILES:
  source=base/'references'/name;destination=harness/'references'/name
  if check:
   if not destination.is_file() or destination.read_bytes()!=source.read_bytes():errors.append(str(destination.relative_to(ROOT)))
  else:destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
 for entry in suite['skills']:
  if entry['name'] in (base.name,harness.name):continue
  target=ROOT/'skills'/entry['name']
  for source in sorted((base/'examples').rglob('*')):
   if not source.is_file() or '__pycache__' in source.parts:continue
   destination=target/'examples'/source.relative_to(base/'examples')
   if check:
    if not destination.is_file() or destination.read_bytes()!=source.read_bytes():errors.append(str(destination.relative_to(ROOT)))
   else:destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
  for source in sorted((base/'references').glob('*')):
   if source.name in {'commands.json','scenario.md'} or not source.is_file():continue
   destination=target/'references'/source.name
   data=source.read_text(encoding='utf-8').replace(base.name,target.name).encode()
   if check:
    if not destination.is_file() or destination.read_bytes()!=data:errors.append(str(destination.relative_to(ROOT)))
   else:destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
 if errors:raise ValueError('skill_resource_drift: '+', '.join(errors))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
 sync(args.check);print('skill suite resources verified' if args.check else 'skill suite resources synchronized')
