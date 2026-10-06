"""配音真实格式、精确采样信息及安装前错误拒绝。"""
import importlib.util,json,struct,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'skills/artcraft-use/scripts/workflow.py'
spec=importlib.util.spec_from_file_location('wav_workflow',SCRIPT);workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
class WavAssetsTests(unittest.TestCase):
 def test_signature_not_extension_and_exact_audio_metadata(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'voice.bin'
   with wave.open(str(path),'wb') as out:
    out.setnchannels(2);out.setsampwidth(2);out.setframerate(48000);out.writeframes(struct.pack('<h',700)*8)
   self.assertEqual(workflow.provided_metadata(path),('audio/wav',{'audio':{'sampleRate':48000,'channels':2},'bitDepth':16,'durationTicks':'4','timeBase':{'num':1,'den':48000}}))
   path.write_bytes(b'ordinary binary');self.assertEqual(workflow.provided_metadata(path),('application/octet-stream',{}))
 def test_false_wav_extension_or_truncation_is_rejected_before_install(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);path=root/'voice.wav';path.write_bytes(b'not WAV');plan=root/'plan.json';plan.write_text(json.dumps({'workflowId':'audio','revision':'v1','nodes':[{'id':'film','pluginId':'filmcraft','providedAssets':['voice'],'payload':{}}]}))
   with patch.object(workflow.subprocess,'run') as launch:
    with self.assertRaisesRegex(ValueError,'provided_wav_invalid'):workflow.execute(plan,root/'output','owner','scope',assignments=['voice='+str(path)])
    launch.assert_not_called()
   with wave.open(str(path),'wb') as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(48000);out.writeframes(b'\0'*8)
   path.write_bytes(path.read_bytes()[:-1])
   with self.assertRaisesRegex(ValueError,'provided_wav_invalid'):workflow.provided_metadata(path)
