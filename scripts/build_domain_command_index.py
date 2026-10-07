#!/usr/bin/env python3
"""从Art分发锁的不可变领域标签提取目录与实例，不读取浮动工作树。"""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=('filmcraft','effectcraft','photocraft','vectorcraft')
def build(repositories,check=False):
 lock=json.loads((ROOT/'skills/artcraft-use/scripts/distribution.lock.json').read_text());domains={}
 for domain in NAMES:
  bundle=lock['bundles'][domain+'-skills'];repo=repositories/(domain+'-skills');tag='v'+bundle['version'];commit=subprocess.check_output(['git','rev-parse',tag+'^{commit}'],cwd=repo,text=True).strip()
  if commit!=bundle['sourceCommit']:raise ValueError('source_commit_mismatch')
  prefix='skills/'+domain+'-use/';relative=prefix+'references/command-coverage.json';raw=subprocess.check_output(['git','show',tag+':'+relative],cwd=repo)
  if hashlib.sha256(raw).hexdigest()!=bundle['files'][relative]:raise ValueError('catalog_identity_mismatch')
  domains[domain]={'version':bundle['version'],'sourceCommit':commit,'bundleSha256':bundle['sha256'],'catalogText':raw.decode()}
  relative=prefix+'references/native-command-snapshot.json';snapshot=subprocess.check_output(['git','show',tag+':'+relative],cwd=repo)
  if hashlib.sha256(snapshot).hexdigest()!=bundle['files'][relative]:raise ValueError('snapshot_identity_mismatch')
  domains[domain]['snapshotText']=snapshot.decode()
  relative=prefix+'references/bridge-tools.json'
  if relative in bundle['files']:
   bridge=subprocess.check_output(['git','show',tag+':'+relative],cwd=repo)
   if hashlib.sha256(bridge).hexdigest()!=bundle['files'][relative]:raise ValueError('bridge_snapshot_identity_mismatch')
   domains[domain]['bridgeSnapshotText']=bridge.decode()
  for old,new in [('commands-revision-create.json','create'),('commands-revision.json','revise')]:
   relative=prefix+'examples/'+old;data=subprocess.check_output(['git','show',tag+':'+relative],cwd=repo)
   if hashlib.sha256(data).hexdigest()!=bundle['files'][relative]:raise ValueError('example_identity_mismatch')
   destination=ROOT/'skills/artcraft-use/examples'/('domain-'+domain+'-'+new+'.json')
   if check:
    if not destination.is_file() or destination.read_bytes()!=data:raise ValueError('example_drift')
   else:destination.write_bytes(data)
 return {'schema':'artcraft-domain-command-index/v1','domains':domains}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repositories',type=Path,default=ROOT.parent);parser.add_argument('--check',action='store_true');args=parser.parse_args();data=(json.dumps(build(args.repositories,args.check),ensure_ascii=False,indent=2)+'\n').encode();target=ROOT/'skills/artcraft-use/references/domain-command-index.json'
 if args.check:
  if not target.is_file() or target.read_bytes()!=data:raise ValueError('index_drift')
 else:target.write_bytes(data)
 print('fixed domain index verified' if args.check else 'fixed domain index built')
