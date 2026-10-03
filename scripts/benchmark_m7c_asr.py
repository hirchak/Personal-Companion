"""Original local Lesya TTS/non-speech corpus; no human/private/cloud audio or production forecast."""
import json,time,subprocess,wave,re,unicodedata,random,struct,threading,hashlib
from pathlib import Path
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.storage import REPO,SafeError

ROOT=REPO/'generated/local-asr/m7c-benchmark'
PHRASES={'clear':'Це вигаданий приклад. Персонаж малює паперовий сад.','short':'Паперовий сад.','reflective':'Вигаданий персонаж хоче почати з маленької чернетки, а не з ідеального макета.'}
def normalize(text):return ' '.join(re.sub(r'[^\w\s]',' ',unicodedata.normalize('NFC',text).casefold()).split())
def distance(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  row=[i]
  for j,y in enumerate(b,1):row.append(min(row[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=row
 return prev[-1]
def run():
 ROOT.mkdir(parents=True,exist_ok=True);e=WhisperLocalASR();rows=[]
 for id,text in PHRASES.items():
  aiff=ROOT/(id+'.aiff');wav=ROOT/(id+'.wav')
  subprocess.run(['/usr/bin/say','-v','Lesya','-o',str(aiff),text],check=True,capture_output=True)
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(aiff),'-ar','16000','-ac','1','-c:a','pcm_s16le',str(wav)],check=True,capture_output=True)
 for id in ('silence','noise'):
  randomizer=random.Random(70003);samples=[0 if id=='silence' else randomizer.randint(-1500,1500) for _ in range(16000*3)]
  with wave.open(str(ROOT/(id+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(struct.pack('<'+'h'*len(samples),*samples))
 for id in [*PHRASES,'silence','noise']:
  wav=ROOT/(id+'.wav');data=wav.read_bytes()
  with wave.open(str(wav)) as w:duration=w.getnframes()/w.getframerate()
  started=time.monotonic();value=e.transcribe(data,'uk',threading.Event(),time.monotonic()+90);elapsed=time.monotonic()-started
  row={'case':id,'provenance':'ORIGINAL_SYNTHETIC_APPLE_LESYA_TTS' if id in PHRASES else 'ORIGINAL_SYNTHETIC_NON_SPEECH','audio_sha256':hashlib.sha256(data).hexdigest(),'audio_bytes':len(data),'duration_seconds':duration,'rate':16000,'channels':1,'wall_seconds':round(elapsed,4),'real_time_factor':round(elapsed/duration,4),'candidate_chars':len(value['text']),'transcription_success':bool(value['text'].strip()),'cloud_asr':False}
  (ROOT/(id+'-candidate-ignored.json')).write_text(json.dumps(value,ensure_ascii=False)+'\n')
  if id in PHRASES:
   ref=normalize(PHRASES[id]);out=normalize(value['text']);row.update(reference_text=PHRASES[id],reference_sha256=hashlib.sha256(PHRASES[id].encode()).hexdigest(),WER=round(distance(ref.split(),out.split())/len(ref.split()),4),CER=round(distance(list(ref),list(out))/len(ref),4),quality_scope='SYNTHETIC_TTS_ONLY_NOT_HUMAN_PRIVATE_HARDWARE')
  else:row.update(WER=None,CER=None,non_speech_output_observed=bool(value['text'].strip()))
  rows.append(row);print(id,'local_wall',row['wall_seconds'],'WER',row['WER'],flush=True)
 result={'status':'PASS_CAPABILITY_WITH_CORPUS_LIMITS','engine':e.metadata(),'new_model_asset_bytes':487601967,'asset_limit':2500000000,'TTS':'Existing local Apple say/Lesya uk_UA; no voice/model download or cloud TTS','normalization':'NFC/casefold, punctuation to space, collapse whitespace; Levenshtein word/character edits divided by reference length','rows':rows,'human_UA_quality':'NOT_RUN','girlfriend_voice_forecast':'NOT_CLAIMED','audio_and_raw_candidates_publication':'IGNORED_LOCAL_ONLY','memory_RSS':'NOT_MEASURED; wall includes verified model/binary and process startup','clinical_outcomes':None}
 (REPO/'generated/local-asr/M7C_ASR_BENCHMARK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':run()
