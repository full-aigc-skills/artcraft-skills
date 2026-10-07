"""单Art技能真实模型下载、五子工程识别、品牌返工与移动包验收。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
@unittest.skipUnless(os.environ.get('CRAFT_ART_MIXED_ASR')=='1','requires public runtimes, model download, speech and retained output')
class MixedAsrTests(unittest.TestCase):
    def test_real_speech_mixed_revision_and_moved_package(self):
        root=Path(os.environ['CRAFT_ART_MIXED_ASR_OUTPUT']).resolve();root.mkdir(parents=True,exist_ok=False)
        original=Path(os.environ.get('CRAFT_ART_ASR_SKILL_ROOT',ROOT/'skills/artcraft-use'))
        skill=root/'.agents/skills/artcraft-use';shutil.copytree(original,skill,ignore=shutil.ignore_patterns('__pycache__'))
        fingerprints={str(p.relative_to(skill)):digest(p) for p in skill.rglob('*') if p.is_file()}
        runtime=root/'fresh-runtime';data=root/'persistent-data';project=root/'project'
        env={k:v for k,v in os.environ.items() if not k.startswith('CRAFT_')};env.update(PATH='/usr/bin:/bin',FILMCRAFT_DATA_DIR=str(data))
        calls=[]
        def run(argv,label):
            reply=subprocess.run(list(map(str,argv)),env=env,capture_output=True,text=True,timeout=900)
            log=root/(label+'.log');log.write_text(reply.stdout+reply.stderr)
            calls.append({'label':label,'exitCode':reply.returncode,'logSha256':digest(log)})
            self.assertEqual(reply.returncode,0,reply.stdout+reply.stderr)
            return json.loads(reply.stdout)
        def art(script,args,label):return run([sys.executable,'-I','-B',skill/'scripts'/script,'--runtime-home',runtime,*args],label)
        setup=art('bootstrap.py',['--plugin','filmcraft'],'setup-film')
        cli=setup['skills']['filmcraft']['executable']
        def native(args,label):return run([cli,*args,'--data-dir',data],label)
        models=native(['exec','transcript.models'],'models-before')
        self.assertTrue(models['available']);self.assertEqual(Path(models['dir']),data/'models')
        self.assertFalse(next(m for m in models['models'] if m['id']=='whisper-tiny')['installed'])
        native(['exec','transcript.downloadModel',json.dumps({'model':'whisper-tiny'})],'download-model')
        expected={'config.json':'ffdccec4f3211f4c63310f2b7098f309fe70f3952cedc5e4d11e43f5b2379b98','generation_config.json':'a5d5325911f16e74001a72fa13d6e208eee51548f994646de1f4b4cc8b35b512','tokenizer.json':'27fc476bfe7f17299480be2273fc0608e4d5a99aba2ab5dec5374b4482d1a566','model.safetensors':'7ebd0e69e78190ffe1438491fa05cc1f5c1aa3a4c4db3bc1723adbb551ea2395'}
        for name,sha in expected.items():self.assertEqual(digest(data/'models/whisper-tiny'/name),sha)
        mtimes={name:(data/'models/whisper-tiny'/name).stat().st_mtime_ns for name in expected}
        speech=root/'speech.aiff';voice=root/'voice.wav'
        reference='Welcome to our creative studio. Today we are making a short film with clear sound and simple captions. Save the project and keep every scene ready for editing.'
        subprocess.run(['/usr/bin/say','-v','Samantha','-r','155','-o',str(speech),reference],check=True)
        subprocess.run(['ffmpeg','-v','error','-i',str(speech),'-ac','1','-ar','48000',str(voice)],check=True)
        voice_sha=digest(voice);plan=json.loads((skill/'examples/brand-token-campaign.json').read_text());plan['workflowId']='real-speech-brand-campaign';plan['revision']='v1'
        nodes={n['id']:n for n in plan['nodes']};intro=nodes['intro']['payload']['plan'];intro['document']['duration']=10
        for op in intro['operations']:
            if op['command']=='layer.addItem':op['params']['duration']=10
        film=nodes['film']['payload']['plan'];film['operations']=[op for op in film['operations'] if not op['command'].startswith('caption')]
        for op in film['operations']:
            if op['command']=='timeline.place':
                if op['params']['track']=='A1':op['params'].pop('duration',None)
                else:op['params']['duration']=str(10*254016000000)
        film['operations'] += [{'command':'native.command','params':{'command':'transcript.generate','params':{'model':'whisper-tiny','language':'en','items':[{'$ref':'voice.item'}]}}},{'command':'native.command','params':{'command':'transcript.createCaptions','params':{'name':'Recognized speech','maxChars':42}}}]
        def workflow(value,label):
            path=root/(label+'.json');path.write_text(json.dumps(value))
            result=art('workflow.py',[path,'--output',project,'--authorization','real-speech-mixed-first-use','--asset','voice='+str(voice)],label)
            self.assertEqual(result['state'],'review_ready');return result
        first=workflow(plan,'initial');originals={name:{str(p.relative_to(node['root'])):digest(p) for p in Path(node['root']).rglob('*') if p.is_file()} for name,node in first['nodes'].items()}
        first_film=Path(first['nodes']['film']['root'])
        transcript=native(['exec','transcript.inspect','--project',first_film/'project.fcproj'],'transcript-reopen')
        self.assertGreaterEqual(len(transcript['words']),15)
        self.assertIn('studio',(first_film/'captions.srt').read_text().lower())
        ops=json.loads((first_film/'operations.json').read_text());generated=next(x['result'] for x in ops if x.get('nativeCommand')=='transcript.generate');self.assertNotEqual(generated['items'][0]['source'],'fixed')
        revised=json.loads(json.dumps(plan));revised['revision']='v2';logo=next(n for n in revised['nodes'] if n['id']=='logo');prior=first['nodes']['logo'];artifact=prior['outputs'][0]
        logo['expectedRevision']=artifact['nativeProjectRef']['sha256'];logo['externalInputs']=[{'root':prior['root'],'artifact':artifact}];logo['payload']['sourceProject']={'assetId':artifact['assetId']};logo['payload']['plan']={'operations':[{'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}}]}
        second=workflow(revised,'revised')
        for name in ['logo','poster','intro','film']:self.assertNotEqual(first['nodes'][name]['taskId'],second['nodes'][name]['taskId'])
        self.assertEqual(first['nodes']['badge']['taskId'],second['nodes']['badge']['taskId'])
        from PIL import Image, ImageChops
        for name, filename in [('poster','design.png'),('intro','frame-0001.png'),('film','frame-0000.png')]:
            with Image.open(Path(first['nodes'][name]['root'])/filename) as before, Image.open(Path(second['nodes'][name]['root'])/filename) as after:
                self.assertIsNotNone(ImageChops.difference(before.convert('RGB'),after.convert('RGB')).getbbox(),name)

        for name,node in first['nodes'].items():
            for path,sha in originals[name].items():self.assertEqual(digest(Path(node['root'])/path),sha)
        self.assertEqual(digest(voice),voice_sha)
        self.assertEqual(mtimes,{name:(data/'models/whisper-tiny'/name).stat().st_mtime_ns for name in expected})
        packed=art('package.py',['create','--project',project,'--workflow',second['runKey'],'--authorization','real-speech-mixed-first-use','--output',root/'package'],'package')
        shutil.move(root/'package',root/'moved-package')
        verified=art('package.py',['verify','--package',root/'moved-package','--sha',packed['sha256']],'verify-package');self.assertEqual(len(verified['children']),5)
        self.assertFalse(any((root/'moved-package').rglob('model.safetensors')))
        for path,sha in fingerprints.items():self.assertEqual(digest(skill/path),sha)
        proof={'result':'PASS','scope':'Single Art source/installed skill, real public model first download and four-domain five-child DAG, brand revision and moved package; human creative quality separate','runtimeIdentity':setup['skills']['filmcraft']['runtimeIdentity'],'modelFiles':expected,'wordCount':len(transcript['words']),'realInference':True,'sourceAndVoicePreserved':True,'modelFilesUnchanged':True,'unrelatedBadgeReused':True,'packageChildren':5,'packageSha256':packed['sha256'],'skillFiles':fingerprints,'calls':calls}
        (root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
