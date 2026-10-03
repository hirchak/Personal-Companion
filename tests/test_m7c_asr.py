"""ASR source/argv/M4 integration mechanics, offline fixture; genuine model benchmark is separate."""
from pathlib import Path
from uuid import uuid4
import json,threading,time
import pytest
from apps.core.storage import SafeError,digest
from apps.core.api import create_app
from apps.core.voice_contracts import ASRRequest,TranscriptEdit
from apps.core.whisper_local_asr import WhisperLocalASR
from apps.core.conversation import Conversations
from apps.core.conversation_controller import ConversationController
from apps.core.conversation_contracts import NewConversation,VoiceSource
from apps.core.conversation_runtime_contracts import InferenceStart
from test_m1_domain import isolated
from test_m4_voice import save
from test_m7c_controller import FixtureProvider

class TrustedLocalFixture:
 def metadata(self):return {'engine':'ORIGINAL_SYNTHETIC_LOCAL_FIXTURE','version':'1','model':'NO_REAL_MODEL','model_hash':'a'*64,'available':True,'scope':'M7C_SYNTHETIC_ONLY','cloud_asr':False}
 def transcribe(self,data,language,cancel,deadline):return {'text':'ORIGINAL SYNTHETIC fixture transcript','language':'uk'}


def test_local_scope_cannot_activate_on_normal_app(isolated):
 with pytest.raises(SafeError,match='M7C_SYNTHETIC_SCOPE_REQUIRED'):create_app(isolated/'normal',local_asr=TrustedLocalFixture())


def test_m4_local_candidate_edit_insert_source_send_text_only(isolated):
 provider=FixtureProvider();app=create_app(isolated/'voice-local',synthetic_conversations=True,m7c_synthetic=True,conversation_provider=provider,local_asr=TrustedLocalFixture());voice=app.state.voice
 audio,_=save(voice);job=voice.enqueue(audio,ASRRequest(mode='LOCAL'));voice.run(job['transcript_id'],'LOCAL');t=voice.get(audio)['transcript'];assert t['state']=='TRANSCRIPT_READY'
 voice.edit(t['id'],TranscriptEdit(revision=t['revision'],text='ORIGINAL SYNTHETIC explicit edited text'));t=voice.get(audio)['transcript']
 source=VoiceSource(kind='VOICE_TRANSCRIPT',transcript_id=t['id'],revision=t['revision'],audio_hash=t['audio_hash'],text_hash=digest(t['edited'].encode()))
 assert not app.state.journal.list()['items'] and not app.state.conversations.list()['items']
 p=app.state.conversations.create(NewConversation(operation_id=uuid4()));r=app.state.conversation_controller.send(p['conversation']['id'],InferenceStart(operation_id=uuid4(),base_revision=1,text=t['edited'],source_reference=source,synthetic_test_ack=True));id=r['inference_job']['id'];app.state.conversation_controller.workers[id].join(2)
 with app.state.store.connect() as c:
  d=app.state.conversation_controller.row(c,id);assert d['state']=='COMPLETED';assert t['audio_hash'] not in json.dumps(d['request_metadata']);assert 'audio' not in d['request_metadata']
 assert not app.state.journal.list()['items']


def test_profile_fixed_file_data_and_network_exec_denials():
 # Static contract complements the actual synthetic sentinel execution receipt, not an OS PASS by itself.
 e=object.__new__(WhisperLocalASR);e.binary=Path('/private/tmp/ORIGINAL_SYNTHETIC_BINARY');e.model=Path('/private/tmp/ORIGINAL_SYNTHETIC_MODEL');p=e.profile(Path('/private/tmp/ORIGINAL_SYNTHETIC_WORK'))
 assert '(deny network*)' in p and '(deny file-read-data)' in p and '(deny file-write*)' in p and '(deny process-exec)' in p
 assert 'subpath "/Users"' not in p and 'subpath "/private/tmp"' not in p
