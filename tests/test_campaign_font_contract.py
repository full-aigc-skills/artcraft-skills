"""所有随包默认混合示例应满足锁定原生字体检查。"""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class CampaignFontContractTests(unittest.TestCase):
 def test_every_single_skill_default_vector_wordmark_uses_bundled_font(self):
  for skill in sorted((ROOT/'skills').iterdir()):
   if not (skill/'SKILL.md').is_file():continue
   for name in ('brand-campaign.json','chinese-brand-campaign.json','brand-token-campaign.json'):
    plan=json.loads((skill/'examples'/name).read_text());count=0
    for node in plan['nodes']:
     if node['pluginId']!='vectorcraft':continue
     for operation in node['payload']['plan']['operations']:
      if operation['command']=='text.create':
       count+=1
       self.assertEqual(operation['params']['font'],'Source Sans 3',skill.name+'/'+name)
    self.assertGreater(count,0)
if __name__=='__main__':unittest.main()
