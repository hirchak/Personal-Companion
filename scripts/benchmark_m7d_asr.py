"""Existing original Lesya TTS only. No model download, cloud, real human audio."""
import json,io,wave,struct,threading,time,hashlib
from pathlib import Path
from apps.core.storage import REPO,SafeError
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.speech_presence import speech_presence
from scripts.benchmark_m7c_asr import normalize,distance,PHRASES

ROOT=REPO/'generated/local-asr/m7d-benchmark'
def transform(data,scale=1,padding=0):
 with wave.open(io.BytesIO(data)) as w:rate=w.getframerate();raw=w.readframes(w.getnframes())
 samples=[round(v*scale) for v in struct.unpack('<'+'h'*(len(raw)//2),raw)];samples=[0]*int(rate*padding)+samples+[0]*int(rate*padding)
 out=io.BytesIO()
 with wave.open(out,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(struct.pack('<'+'h'*len(samples),*samples))
 return out.getvalue()
def run():
 ROOT.mkdir(parents=True,exist_ok=True);old=REPO/'generated/local-asr/m7c-benchmark';e=WhisperLocalASR();rows=[]
 cases=[('silence','silence',1,0,False),('noise','noise',1,0,False),('quiet_speech','clear',.025,0,True),('normal_speech','clear',1,0,True),('short_speech','short',1,0,True),('padded_speech','clear',1,1,True)]
 for name,source,scale,pad,is_speech in cases:
  data=transform((old/(source+'.wav')).read_bytes(),scale,pad);(ROOT/(name+'.wav')).write_bytes(data);guard=speech_presence(data);started=time.monotonic();error=None;value=None;before=e.executions
  try:value=e.transcribe(data,'uk',threading.Event(),time.monotonic()+90)
  except SafeError as exc:error=exc.code
  text=value['text'] if value else '';ref=normalize(PHRASES.get(source,''));out=normalize(text)
  row={'case':name,'expected_speech':is_speech,'guard':guard,'whisper_invoked':e.executions>before,'error':error,'candidate_text':text,'candidate_sendable_without_review':bool(text) and guard['state']=='SPEECH_DETECTED','latency_seconds':round(time.monotonic()-started,4),'audio_sha256':hashlib.sha256(data).hexdigest(),'audio_bytes':len(data),'WER':round(distance(ref.split(),out.split())/len(ref.split()),4) if ref else None,'CER':round(distance(list(ref),list(out))/len(ref),4) if ref else None};rows.append(row);print(name,guard['state'],error,'seconds',row['latency_seconds'],flush=True)
 result={'scope':'BOUNDED_ORIGINAL_SYNTHETIC_TTS_ONLY','engine':e.metadata(),'new_model_download_bytes':0,'cloud_ASR':'NONE','human_UA_quality':'NOT_RUN','raw_audio':'IGNORED_LOCAL_ONLY','guard_version':'PCM_SIGNAL_V1','false_normal_acceptances':sum(not r['expected_speech'] and r['candidate_sendable_without_review'] for r in rows),'false_rejections':sum(r['expected_speech'] and r['guard']['state']=='NO_SPEECH' for r in rows),'speech_review_required':sum(r['expected_speech'] and r['guard']['state']=='UNCERTAIN' for r in rows),'rows':rows,'limits':'Energy/crossing/modulation heuristic. Complex noise, music, tones, microphone conditions unverified. No perfect VAD claim.'}
 (ROOT/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':run()
