"""制品只读下载重试必须有界、清理半包且不放宽校验。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError, HTTPError
ROOT=Path(__file__).resolve().parents[1]
class Response:
 def __init__(self,fail=False):self.fail=fail;self.reads=0;self.headers={}
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def read(self,size):
  self.reads+=1
  if self.fail and self.reads==2:raise URLError('private TLS interruption')
  return b'partial' if self.fail and self.reads==1 else b'good' if self.reads==1 else b''
class DownloadRetryTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('download',ROOT/'skills/artcraft-use/scripts/download.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_interrupted_read_discards_partial_archive_and_retries(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as temp,patch.object(m.urllib.request,'urlopen',side_effect=[Response(True),Response()]) as fetch,patch.object(m.time,'sleep'):
   p=Path(temp)/'archive';m.download('https://example.invalid',p,100,'size_limit');self.assertEqual(p.read_bytes(),b'good');self.assertEqual(fetch.call_count,2)
 def test_http_denial_size_and_filesystem_errors_are_not_retried(self):
  m=self.module()
  for error in [HTTPError('https://example.invalid',403,'denied',{},None),PermissionError('disk')]:
   with tempfile.TemporaryDirectory() as temp,patch.object(m.urllib.request,'urlopen',side_effect=error) as fetch:
    with self.assertRaises(type(error)):m.download('https://example.invalid',Path(temp)/'archive',100,'size_limit')
    self.assertEqual(fetch.call_count,1)
  with tempfile.TemporaryDirectory() as temp,patch.object(m.urllib.request,'urlopen',return_value=Response()) as fetch:
   with self.assertRaisesRegex(ValueError,'size_limit'):m.download('https://example.invalid',Path(temp)/'archive',2,'size_limit')
   self.assertEqual(fetch.call_count,1)
 def test_network_exhaustion_is_three_attempts_and_leaves_no_archive(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as temp,patch.object(m.urllib.request,'urlopen',side_effect=URLError('private TLS reason')) as fetch,patch.object(m.time,'sleep'):
   p=Path(temp)/'archive'
   with self.assertRaisesRegex(ValueError,'artifact_download_failed'):m.download('https://example.invalid',p,100,'size_limit')
   self.assertEqual(fetch.call_count,3);self.assertFalse(p.exists())
