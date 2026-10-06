"""JPEG 结构登记；真实解码单独验收，不以标记检查代替。"""
import base64,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('jpeg_workflow',ROOT/'skills/artcraft-use/scripts/workflow.py')
workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
IMAGES=json.loads((ROOT/'tests/fixtures/jpeg-images.json').read_text())['images']
class JpegAssetsTests(unittest.TestCase):
 def test_real_baseline_progressive_gray_cmyk_by_content(self):
  with tempfile.TemporaryDirectory() as directory:
   for name,value in IMAGES.items():
    for filename in ['product.bin','product.png','product.jpeg']:
     with self.subTest(name=name,filename=filename):
      path=Path(directory)/filename;path.write_bytes(base64.b64decode(value))
      self.assertEqual(workflow.provided_metadata(path),('image/jpeg',{'width':7,'height':5,'bitDepth':8,'alpha':False}))
 def test_bad_jpeg_rejected_before_install(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);path=root/'product.jpg';plan=root/'plan.json'
   plan.write_text(json.dumps({'workflowId':'jpeg','revision':'v1','nodes':[{'id':'poster','pluginId':'photocraft','providedAssets':['product']}]}))
   data=base64.b64decode(IMAGES['rgb'])
   for broken in [b'fake',data[:-1],data[:20],data+b'trailing',b'\xff\xd8\xff\xd9']:
    path.write_bytes(broken)
    with patch.object(workflow.subprocess,'run') as launch:
     with self.assertRaisesRegex(ValueError,'provided_jpeg_invalid'):workflow.execute(plan,root/'out','owner','scope',assignments=['product='+str(path)])
     launch.assert_not_called();self.assertEqual(path.read_bytes(),broken)
 def test_unsupported_precision_and_process(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'product.jpg';data=bytearray(base64.b64decode(IMAGES['rgb']));offset=data.index(b'\xff\xc0')
   for changed in [bytes(data[:offset+1])+b'\xc3'+bytes(data[offset+2:]),bytes(data[:offset+4])+b'\x0c'+bytes(data[offset+5:])]:
    path.write_bytes(changed)
    with self.assertRaisesRegex(ValueError,'provided_jpeg_unsupported'):workflow.provided_metadata(path)
