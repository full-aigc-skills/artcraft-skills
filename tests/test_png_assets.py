"""PNG 内容识别、属性与首次安装前的失败拒绝。"""
import importlib.util,json,struct,tempfile,unittest,zlib
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts/workflow.py'
spec=importlib.util.spec_from_file_location('png_workflow',SCRIPT);workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
def chunk(kind,data):
 return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
def png(raw=b'\0\xff\0\0\x80',width=1,height=1,depth=8,color=6,extra=b''):
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,depth,color,0,0,0))+extra+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
class PngAssetsTests(unittest.TestCase):
 def test_all_standard_depths_colors_and_adam7_scan_layout(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'image.bin'
   for color,depths in {0:[1,2,4,8,16],2:[8,16],3:[1,2,4,8],4:[8,16],6:[8,16]}.items():
    for depth in depths:
     channels={0:1,2:3,3:1,4:2,6:4}[color];raw=b'\0'*(1+(channels*depth+7)//8)
     path.write_bytes(png(raw,depth=depth,color=color,extra=chunk(b'PLTE',b'\0\0\0') if color==3 else b''))
     self.assertEqual(workflow.provided_metadata(path)[1],{'width':1,'height':1,'bitDepth':depth,'alpha':color in (4,6)})
   # Adam7 3x3 RGBA 的五个非空扫描阶段，各行以 filter=0 开始。
   raw=b'\0'*5+b'\0'*5+b'\0'*9+b'\0'*5*2+b'\0'*13
   data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',3,3,8,6,0,0,1))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
   path.write_bytes(data);self.assertEqual(workflow.provided_metadata(path)[1]['width'],3)
 def test_content_signature_and_palette_transparency(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'product.bin';path.write_bytes(png())
   self.assertEqual(workflow.provided_metadata(path),('image/png',{'width':1,'height':1,'bitDepth':8,'alpha':True}))
   path.write_bytes(png(b'\0\0',depth=1,color=3,extra=chunk(b'PLTE',b'\xff\0\0')+chunk(b'tRNS',b'\x80')))
   self.assertEqual(workflow.provided_metadata(path),('image/png',{'width':1,'height':1,'bitDepth':1,'alpha':True}))
 def test_fake_crc_truncation_and_invalid_scan_data_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'product.png'
   broken=bytearray(png());broken[29]^=1
   for data in [b'fake PNG',png()[:-1],bytes(broken),png(b'\0'),png(b'\5\xff\0\0\x80'),png()+b'trailing',png(extra=chunk(b'IHDR',b'\0'*13))]:
    path.write_bytes(data)
    with self.assertRaisesRegex(ValueError,'provided_png_invalid'):workflow.provided_metadata(path)
   path.write_bytes(png(extra=chunk(b'acTL',struct.pack('>II',1,0))))
   with self.assertRaisesRegex(ValueError,'provided_png_animated_unsupported'):workflow.provided_metadata(path)
 def test_bad_png_rejected_before_bootstrap(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);asset=root/'product.png';asset.write_bytes(b'fake');plan=root/'plan.json'
   plan.write_text(json.dumps({'workflowId':'png','revision':'v1','nodes':[{'id':'poster','pluginId':'photocraft','providedAssets':['product'],'payload':{}}]}))
   with patch.object(workflow.subprocess,'run') as launch:
    with self.assertRaisesRegex(ValueError,'provided_png_invalid'):workflow.execute(plan,root/'out','owner','scope',assignments=['product='+str(asset)])
    launch.assert_not_called();self.assertEqual(asset.read_bytes(),b'fake')
