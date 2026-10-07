"""Explicit M8D owner-bounded gates, separate from core storage and synthetic permission."""
import threading
from typing import Literal
from pydantic import BaseModel,ConfigDict,model_validator
from .storage import SafeError,encode,digest,now
from .root_types import RootKind


PROFILE_ID='MAC_PRIVATE_AI_VOICE_PILOT_V1'
PROFILES={'FREE':{'model':'gpt-6-luna','effort':'high'},'DEEP_ECONOMICAL':{'model':'gpt-6-luna','effort':'max'},'DEEP_QUALITY':{'model':'gpt-6.1-sol','effort':'high'}}
EFFORT_CEILINGS={'gpt-6-luna':('low','medium','high','xhigh','max'),'gpt-6.1-sol':('low','medium','high')}
PROFILE={'profile_id':PROFILE_ID,'profile_version':1,'root_kind':'PRIVATE_LOCAL',
 'journal':'ON','creative':'ON','local_search':'ON','backup_restore':'ON','explicit_local_export':'ON',
 'conversation':'ON','private_ai':'EXPLICIT_OWNER_GATE_DEFAULT_OFF','local_voice':'LOCAL_SESSION_ONLY_NO_AI_CONSENT',
 'local_asr':'PINNED_WHISPER_CPP_LOCAL_ONLY','provider_route':'EXISTING_CODEX_CHATGPT_SUBSCRIPTION_ONLY',
 'profiles':PROFILES,'clinical_active':0,'specialists':'OFF','health_bridge':'OFF','health_to_ai':'OFF',
 'phone':'OFF','external_embeddings':'OFF','cloud_asr':'NONE','cloud_sync':'NONE','telemetry':'NONE',
 'publication':'NONE','automatic_external_sharing':'NONE','provider_fallback':'NONE',
 'journal_context':'EXPLICIT_SELECTION_ONLY','raw_audio_to_provider':'NEVER'}
ACK_KEYS=('text_leaves_mac_for_openai','raw_audio_not_sent','only_exact_approved_context',
          'retention_not_zero_certified','no_provider_fallback','chatgpt_training_off_confirmed','codex_environments_off_confirmed')

class OwnerAcknowledgement(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 profile_id:Literal['MAC_PRIVATE_AI_VOICE_PILOT_V1']
 text_leaves_mac_for_openai:Literal[True]
 raw_audio_not_sent:Literal[True]
 only_exact_approved_context:Literal[True]
 retention_not_zero_certified:Literal[True]
 no_provider_fallback:Literal[True]
 chatgpt_training_off_confirmed:Literal[True]
 codex_environments_off_confirmed:Literal[True]
 @model_validator(mode='before')
 @classmethod
 def exact_bools(cls,value):
  if not isinstance(value,dict) or any(type(value.get(k)) is not bool for k in ACK_KEYS):raise ValueError('Explicit true Boolean acknowledgements required')
  return value

class DeepProfileSelection(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 profile:Literal['DEEP_ECONOMICAL','DEEP_QUALITY']

class LocalVoiceAcknowledgement(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 local_audio_only:Literal[True]
 review_before_send:Literal[True]
 manual_audio_deletion_understood:Literal[True]
 @model_validator(mode='before')
 @classmethod
 def exact_bools(cls,value):
  keys=('local_audio_only','review_before_send','manual_audio_deletion_understood')
  if not isinstance(value,dict) or any(type(value.get(k)) is not bool for k in keys):raise ValueError('Explicit true Boolean acknowledgements required')
  return value

class PrivatePilotGate:
 """Authenticated runtime and versioned local consent; no environment-derived enablement."""
 def __init__(self,store,provider_factory=None,asr_factory=None):
  if getattr(store,'root_kind',None)!=RootKind.PRIVATE_LOCAL:raise SafeError('PRIVATE_LOCAL_ROOT_REQUIRED',403)
  from .local_consent import LocalConsent
  self.consent=LocalConsent(store)
  self.store=store;self.provider_factory=provider_factory;self.asr_factory=asr_factory
  self.deep_profile=(self.consent.read() or {}).get('deep_profile','DEEP_QUALITY')
  self.lock=threading.RLock();self.session=None;self.voice_session=None;self.ack_hash=None;self.adapters={};self.asr=None
  self.revocation_hooks=[];self.voice_suspend_hooks=[];self.profile_change_hooks=[];self.generation=0;self.durable_session=False
 def status(self):
  consent=self.consent.read();contract=self.consent.contract()
  with self.lock:
   return {'profile_id':PROFILE_ID,'state':'PRIVATE_AI_OWNER_CONSENTED' if self.adapters else 'PRIVATE_AI_OFF',
    'local_voice':'ON' if self.asr else 'OFF','profiles':PROFILES,'deep_profile':self.deep_profile,'effort_ceilings':EFFORT_CEILINGS,'external_destination':'OPENAI',
    'scope':'THIS_OWNER_BOUNDED_PILOT_ONLY','retention':'NOT_ZERO_RETENTION_CERTIFIED',
    'journal_context':'EXPLICIT_SELECTION_ONLY','raw_audio_to_provider':'NEVER','fallback':'NONE','payg':'NONE',
    'clinical_active':0,'specialists':'OFF','health':'OFF','phone':'OFF','restore_restart_requires_ack':False,'restart_requires_consent':False,'restore_requires_consent':True,'consent':consent,
    'consent_version':contract['version'],'privacy_version':contract['privacy_version'],
    'external_settings':'NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER','local_asr_available':self.asr is not None}
 def accept_consent(self,session,body):
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  if body.version!=self.consent.contract()['version'] or body.privacy_version!=self.consent.contract()['privacy_version']:raise SafeError('CONSENT_VERSION_CHANGED',409)
  self.consent.accept()
  self.disable()
  return self.resume(session,enable=True)
 def resume(self,session,enable=False):
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  data=self.consent.read()
  if not data:raise SafeError('DURABLE_CONSENT_REQUIRED',403)
  if enable:
   data['ai_enabled']=True;self.consent.write(data)
  try:
   with self.lock:needs_activation=not self.adapters or not self.durable_session or self.session!=digest(session.encode())
   if data['ai_enabled'] and needs_activation:
    self.activate(session,digest(encode(data).encode()),durable=True)
  except SafeError:
   if enable:
    data['ai_enabled']=False;self.consent.write(data)
   raise
  return self.status()
 def user_disable(self):
  self.consent.disable()
  return self.disable()
 def revoke_consent(self):
  self.consent.revoke()
  return self.disable()
 def acknowledge(self,session,body):
  body=OwnerAcknowledgement.model_validate(body)
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  return self.activate(session,digest(encode(body.model_dump()).encode()))
 def activate(self,session,ack_hash,durable=False):
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  if self.provider_factory is None:raise SafeError('PRIVATE_PROVIDER_ROUTE_UNAVAILABLE',503)
  try:candidates={mode:self.provider_factory(mode,**settings) for mode,settings in PROFILES.items()}
  except SafeError as exc:
   if exc.code in {'CODEX_CLI_UNAVAILABLE','PRIVATE_PROVIDER_OS_ISOLATION_UNAVAILABLE','PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE'}:raise SafeError('PRIVATE_PROVIDER_ROUTE_UNAVAILABLE',503) from None
   raise
  except OSError:raise SafeError('PRIVATE_PROVIDER_ROUTE_UNAVAILABLE',503) from None
  for mode,adapter in candidates.items():
   meta=adapter.metadata();p=PROFILES[mode]
   if meta.get('route')!='CODEX_SUBSCRIPTION' or meta.get('model')!=p['model'] or meta.get('effort')!=p['effort'] or meta.get('fallback') is not False or meta.get('payg') is not False:
    raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
  readiness=getattr(candidates['FREE'],'readiness',None)
  if not callable(readiness):raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
  try:proof=readiness()
  except SafeError as exc:
   if exc.code in {'PROVIDER_TIMEOUT','PROVIDER_PROTOCOL_INVALID','PROVIDER_PROCESS_FAILED','PROVIDER_OUTPUT_LIMIT','PROVIDER_RPC_FAILED','PROVIDER_TOOL_REQUEST_DENIED','PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE'}:raise SafeError('PRIVATE_PROVIDER_ROUTE_UNAVAILABLE',503) from None
   raise
  except OSError:raise SafeError('PRIVATE_PROVIDER_ROUTE_UNAVAILABLE',503) from None
  if not isinstance(proof,dict) or proof.get('inference_started') is not False or proof.get('thread_started') is not False or proof.get('fallback') is not False or proof.get('payg') is not False:raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
  if proof.get('account_type')!='chatgpt':raise SafeError('EXISTING_CHATGPT_AUTH_REQUIRED',403)
  supported=proof.get('models')
  if not isinstance(supported,dict):raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
  for mode,p in PROFILES.items():
   efforts=supported.get(p['model'])
   if not isinstance(efforts,list):raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
   if p['effort'] not in efforts:raise SafeError('PROVIDER_EFFORT_UNSUPPORTED',403)
  with self.lock:
   self.session=digest(session.encode());self.ack_hash=ack_hash;self.adapters=candidates;self.durable_session=durable
  return self.status()
 def require(self,session=None):
  if self.durable_session and not self.consent.read():raise SafeError('PRIVATE_AI_CONSENT_CHANGED',409)
  with self.lock:
   if not self.adapters or self.session is None or session is not None and self.session!=digest(session.encode()):raise SafeError('PRIVATE_OWNER_ACK_REQUIRED',403)
 def provider(self,mode):
  self.require()
  key=self.deep_profile if mode=='DEEP' else mode
  if key not in PROFILES:raise SafeError('PRIVATE_PROFILE_NOT_AVAILABLE',403)
  return self.adapters[key]
 def settings(self,mode):
  return dict(PROFILES[self.deep_profile if mode=='DEEP' else mode])
 def select_deep(self,session,profile):
  self.require(session)
  if profile not in ('DEEP_ECONOMICAL','DEEP_QUALITY'):raise SafeError('PRIVATE_PROFILE_NOT_AVAILABLE',403)
  with self.lock:
   changed=profile!=self.deep_profile
   if changed:self.deep_profile=profile;self.generation+=1
   callbacks=list(self.profile_change_hooks) if changed else []
  if not changed:return self.status()
  durable=self.consent.read()
  if durable:durable['deep_profile']=profile;self.consent.write(durable)
  for callback in callbacks:callback()
  return self.status()
 def prepare_local_asr(self,session):
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  if self.asr_factory is None:raise SafeError('LOCAL_ASR_ASSET_UNAVAILABLE',503)
  with self.lock:
   if self.asr is not None and self.voice_session==digest(session.encode()):return self.status()
   if self.voice_session and self.voice_session!=digest(session.encode()):raise SafeError('OWNER_SESSION_CHANGED',403)
  try:engine=self.asr_factory()
  except SafeError:raise
  except (OSError,FileNotFoundError):raise SafeError('LOCAL_ASR_ASSET_UNAVAILABLE',503) from None
  if engine.metadata().get('cloud_asr') is not False or engine.metadata().get('engine')!='whisper.cpp':raise SafeError('LOCAL_ASR_PROFILE_UNVERIFIED',403)
  with self.lock:
   if self.voice_session and self.voice_session!=digest(session.encode()):raise SafeError('OWNER_SESSION_CHANGED',403)
   self.voice_session=digest(session.encode());self.asr=engine
  return self.status()
 def enable_voice(self,session,body=None):
  """Compatibility method: local ASR requires an authenticated session, never a consent checklist."""
  return self.prepare_local_asr(session)
 def require_voice(self,session):
  if not session:raise SafeError('OWNER_SESSION_REQUIRED',401)
  with self.lock:
   if self.voice_session and self.voice_session!=digest(session.encode()):raise SafeError('OWNER_SESSION_CHANGED',403)
 def disable(self):
  with self.lock:
   self.generation+=1
   callbacks=list(self.revocation_hooks)
   self.adapters={};self.session=None;self.ack_hash=None;self.durable_session=False
  for callback in callbacks:callback()
  return self.status()
 def suspend(self):
  with self.lock:
   self.generation+=1
   callbacks=list(self.revocation_hooks)+list(self.voice_suspend_hooks)
   self.adapters={};self.asr=None;self.session=None;self.voice_session=None;self.ack_hash=None;self.durable_session=False
  for callback in callbacks:callback()
  return self.status()
