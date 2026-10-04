"""Synthetic budget/config/admission/signal guards, no live provider or clinical activation."""
import io,random,struct,wave,json,threading
from uuid import uuid4
import pytest
from apps.core.storage import SafeError
from apps.core.speech_presence import speech_presence
from apps.core.live_evaluation_budget import M7DEvaluationBudget
from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.conversation_skills import ConversationSkills
from scripts.qualify_m7d_skills import packages,run
from test_m1_domain import isolated

def wav(samples):
 b=io.BytesIO()
 with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(struct.pack('<'+'h'*len(samples),*samples))
 return b.getvalue()

def test_silence_seeded_noise_and_uncertain_tone():
 import math
 rng=random.Random(70004)
 assert speech_presence(wav([0]*48000))['state']=='NO_SPEECH'
 assert speech_presence(wav([rng.randint(-1500,1500) for _ in range(48000)]))['state']=='NO_SPEECH'
 assert speech_presence(wav([int(400*math.sin(i*.08)) for i in range(16000)]))['state']=='UNCERTAIN'


def test_m7d_persistent_48_counts_all_outcomes_no_reset(isolated):
 path=isolated/'m7d-budget.sqlite3';budget=M7DEvaluationBudget(path)
 for i in range(48):
  id=str(uuid4());budget.reserve(id,'CODEX_SUBSCRIPTION','original-synthetic-fixture');budget.finish(id,['COMPLETED','FAILED','CANCELLED'][i%3])
 assert M7DEvaluationBudget(path).summary()['total_requests']==48
 with pytest.raises(SafeError,match='LIVE_EVAL_LIMIT'):M7DEvaluationBudget(path).reserve(str(uuid4()),'CODEX_SUBSCRIPTION','original-synthetic-fixture')
 assert budget.goal!='M7C_OWNER_2026_10_03'


def test_supported_effort_catalog_exact_model_and_no_invention():
 catalog={'data':[{'model':'gpt-6-luna','supportedReasoningEfforts':[{'reasoningEffort':'low'},{'reasoningEffort':'max'}]}]}
 assert CodexConversationProvider.supported_settings(catalog,'gpt-6-luna')==['low','max']
 with pytest.raises(SafeError,match='MODEL_CAPABILITY_UNVERIFIED'):CodexConversationProvider.supported_settings(catalog,'gpt-6-sol')
 p=CodexConversationProvider(effort='max');assert p.metadata()['effort']=='max' and p.metadata()['profile']=='gpt-6-luna:max' and not p.metadata()['payg'] and not p.metadata()['fallback']


def test_specialist_packages_canonical_OFF_and_runtime_denial():
 run(True);p=packages();assert len(p)==5
 for name,value in p.items():
  assert value['activation_state']=='OFF' and value['runtime_instructions'] is None and value['unresolved_finding_ids'] and value['qualified_content_review_required']
  with pytest.raises(SafeError,match='SKILL_OFF'):ConversationSkills().read(name)
 assert 'health_connect_access' in p['sleep_review']['forbidden_behaviors']
 assert 'IRT_runtime_content' in p['nightmare_review']['forbidden_behaviors']
 assert 'improvised_practice' in p['grounding']['forbidden_behaviors']


def test_uncertain_voice_requires_explicit_review_before_insertion(isolated):
 from apps.core.api import create_app
 from apps.core.voice_contracts import ASRRequest,TranscriptEdit
 from apps.core.conversation_contracts import VoiceSource
 from apps.core.storage import digest
 from test_m4_voice import save,wav as tone
 class Engine:
  def metadata(self):return {'engine':'ORIGINAL_SYNTHETIC_GUARD_FIXTURE','model':'NONE','model_hash':'a'*64,'available':True,'cloud_asr':False,'speech_guard':'PCM_SIGNAL_V1'}
  def transcribe(self,data,language,cancel,deadline):return {'text':'ORIGINAL SYNTHETIC review candidate','language':'uk','speech_state':speech_presence(data)['state']}
 app=create_app(isolated/'guard-voice',synthetic_conversations=True,m7c_synthetic=True,local_asr=Engine());v=app.state.voice
 id,_=save(v,tone());job=v.enqueue(id,ASRRequest(mode='LOCAL'));v.run(job['transcript_id'],'LOCAL');t=v.get(id)['transcript'];assert t['state']=='REVIEW_REQUIRED'
 source=VoiceSource(kind='VOICE_TRANSCRIPT',transcript_id=t['id'],revision=t['revision'],audio_hash=t['audio_hash'],text_hash=digest(t['candidate'].encode()))
 with app.state.store.connect() as db:
  with pytest.raises(SafeError,match='VOICE_SOURCE'):app.state.conversations.voice_source(db,source)
 v.edit(t['id'],TranscriptEdit(revision=t['revision'],text=t['candidate']));assert v.get(id)['transcript']['state']=='TRANSCRIPT_READY'
 assert not app.state.journal.list()['items'] and not app.state.conversations.list()['items']
 id,_=save(v,tone(signal='silence'));job=v.enqueue(id,ASRRequest(mode='LOCAL'));v.run(job['transcript_id'],'LOCAL');t=v.get(id)['transcript'];assert t['state']=='FAILED' and t['error']=='NO_SPEECH' and t['candidate'] is None


def test_strict_provider_schema_requires_nullable_map_and_error_redaction():
 from apps.core.codex_conversation_provider import strict_response_schema,safe_failure
 from apps.core.conversation_runtime_contracts import ConversationCandidate
 schema=ConversationCandidate.model_json_schema();strict=strict_response_schema(schema)
 assert 'working_map' not in schema['required'] and 'working_map' in strict['required']
 assert strict['additionalProperties'] is False and 'default' not in strict['properties']['working_map']
 assert 'null' in str(strict['properties']['working_map'])
 error={'message':'Invalid schema: required must include working_map ORIGINAL_SYNTHETIC_ACCOUNT_SENTINEL','codexErrorInfo':'badRequest'}
 assert safe_failure(error)=={'category':'INVALID_STRUCTURED_SCHEMA','rpc_error_kind':'badRequest'} and 'SENTINEL' not in json.dumps(safe_failure(error))

@pytest.mark.parametrize('text,expected',[
 ('Він сказав «ще не готово?». Що саме зачепило?',1),
 ('Він сказав "ще не готово?". Що саме зачепило?',1),
 ('Він сказав «ще не готово?». Що зачепило? Чого хочеш?',2),
 ('Можна спитати «чому я нездатний?». Що думаєш?',2),
])
def test_main_question_guard_does_not_count_exact_context_quotes(text,expected):
 from apps.core.conversation_controller import main_question_count
 payload={'context':[{'text':'ORIGINAL SYNTHETIC · Колега сказав «ще не готово?».'}],'reflection_state':None}
 assert main_question_count(text,payload)==expected
