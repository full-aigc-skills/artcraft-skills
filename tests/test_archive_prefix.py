"""固定 Git ZIP 前缀只改变布局，不能放宽摘要与路径规则。"""
import hashlib,importlib.util,json,stat,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('setup_prefix',ROOT/'skills/artcraft-use/scripts/setup.py');setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
class PrefixTests(unittest.TestCase):
 def fixture(self,root,extra=None,prefix='photocraft-skills/'):
  archive=root/'bundle.zip'
  with zipfile.ZipFile(archive,'w') as z:
   z.writestr(prefix,b'');z.writestr(prefix+'LICENSE',b'license');z.writestr(prefix+'skills/',b'');z.writestr(prefix+'skills/item.txt',b'fixed')
   if extra:
    name,kind=extra
    if kind=='symlink':
     info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,b'outside')
    else:z.writestr(name,b'fixed')
  lock={'filename':'bundle.zip','url':'https://github.com/full-aigc-skills/photocraft-skills/releases/download/v1.0.0/bundle.zip','version':'1.0.0','archiveFormat':'git-archive-zip','archivePrefix':prefix,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':{'LICENSE':hashlib.sha256(b'license').hexdigest(),'skills/item.txt':hashlib.sha256(b'fixed').hexdigest()}}
  return archive,lock
 def test_prefixed_zip_installs_root_files_and_reuses_exact_identity(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);archive,lock=self.fixture(root);target=setup.install_bundle(lock,root/'installed',archive)
   self.assertEqual((target/'skills/item.txt').read_bytes(),b'fixed');self.assertFalse((target/'photocraft-skills').exists());self.assertEqual(setup.install_bundle(lock,target,archive),target)
 def test_exact_versioned_prefix_installs_but_wrong_version_is_refused(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);archive,lock=self.fixture(root,prefix='photocraft-skills-1.0.0/');target=setup.install_bundle(lock,root/'installed',archive)
   self.assertEqual((target/'skills/item.txt').read_bytes(),b'fixed')
   lock['archivePrefix']='photocraft-skills-1.0.1/'
   with self.assertRaisesRegex(ValueError,'bundle_prefix_invalid'):setup.install_bundle(lock,root/'wrong',archive)
   self.assertFalse((root/'wrong').exists())
 def test_exact_v_tag_prefix_installs_and_mismatched_tag_never_writes(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);archive,lock=self.fixture(root,prefix='photocraft-skills-v1.0.0/')
   target=setup.install_bundle(lock,root/'installed',archive)
   self.assertEqual((target/'skills/item.txt').read_bytes(),b'fixed')
   for prefix,url in [('photocraft-skills-v1.0.1/',lock['url']),('photocraft-skills-v1.0.0/',lock['url'].replace('/v1.0.0/','/v1.0.1/'))]:
    with self.subTest(prefix=prefix,url=url):
     bad=dict(lock,archivePrefix=prefix,url=url)
     with self.assertRaisesRegex(ValueError,'bundle_prefix_invalid'):setup.install_bundle(bad,root/'wrong/installed',archive)
     self.assertFalse((root/'wrong').exists())
 def test_bad_prefix_is_rejected_before_creating_directories(self):
  for prefix in ('../','other/','photocraft-skills','photocraft-skills//','',None,42):
   with self.subTest(prefix=prefix),tempfile.TemporaryDirectory() as t:
    root=Path(t);archive,lock=self.fixture(root);lock['archivePrefix']=prefix
    with self.assertRaisesRegex(ValueError,'bundle_prefix_invalid'):setup.install_bundle(lock,root/'parent/installed',archive)
    self.assertFalse((root/'parent').exists())
 def test_prefix_requires_git_format_and_domain_source(self):
  for field,bad in [('archiveFormat','canonical-skills-zip'),('url','https://github.com/full-aigc-plugins/artcraft-plugin/releases/download/v1.0.0/bundle.zip')]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as t:
    root=Path(t);archive,lock=self.fixture(root);lock[field]=bad
    with self.assertRaisesRegex(ValueError,'bundle_prefix_invalid'):setup.install_bundle(lock,root/'installed',archive)
    self.assertFalse((root/'installed').exists())
 def test_escape_mixed_root_duplicate_and_symlink_never_publish(self):
  for item in [('LICENSE','file'),('photocraft-skills/../outside','file'),('photocraft-skills/skills/item.txt','file'),('photocraft-skills/link','symlink')]:
   with self.subTest(item=item),tempfile.TemporaryDirectory() as t:
    root=Path(t);archive,lock=self.fixture(root,item)
    with self.assertRaisesRegex(ValueError,'bundle_path_invalid'):setup.install_bundle(lock,root/'installed',archive)
    self.assertFalse((root/'installed').exists());self.assertFalse((root/'outside').exists())
 def test_prefix_does_not_relax_archive_or_file_digest(self):
  for field in ('archive','file'):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t);archive,lock=self.fixture(root)
    if field=='archive':lock['sha256']='0'*64
    else:lock['files']['skills/item.txt']='0'*64
    with self.assertRaisesRegex(ValueError,'bundle_(archive|file)_digest_mismatch'):setup.install_bundle(lock,root/'installed',archive)
    self.assertFalse((root/'installed').exists())
