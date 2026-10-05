"""One exact private provider payload, frozen at preview and revalidated before transmission.

Only explicitly selected journal revisions are read. Source IDs/voice metadata remain local;
ordered context and reflection_state shown by the preview are the actual provider representation.
"""
import json
from uuid import uuid4
from .storage import SafeError,encode,digest,now
from .conversation_contracts import Message
from .deep_session_contracts import DeepContextPreview,ContextBinding
from .local_private_ai import PROFILE_ID
from .local_private_contracts import PrivateContextPreview,PrivateProviderPayload

CANONICAL_VERSION=1


def journal_parts(controller,refs):
 parts=[]
 with controller.store.connect() as c:
  for ref in refs:
   id=str(ref['id']);row=c.execute('SELECT owner_id,revision,payload FROM entries WHERE id=?',(id,)).fetchone()
   if not row or row['owner_id']!=str(controller.store.meta()['owner_id']) or row['revision']!=ref['revision']:raise SafeError('JOURNAL_SELECTION_CHANGED',409)
   payload=json.loads(row['payload'])
   if payload['type']=='creative':raise SafeError('CREATIVE_CONTEXT_NOT_AUTHORIZED',403)
   parts.append({'kind':'JOURNAL_SELECTED','text':payload['raw_text'],'sources':[{'id':id,'revision':row['revision']}],'digest_version':None,'artifact_id':None,'memory_ref':None})
 return parts


def canonical_private_payload(controller,c,conv,user,receipt,parts,purpose,snapshot,refs,*,pending_current=False):
 """Canonical order: scoped base → CURRENT_TURN → explicit journal selection.

 All source aliases/skills/frame/reflection state use the controller's sole assembler.
 Preview and freshness checks call this same constructor; transmission reuses its frozen object.
 """
 payload,skills,aliases=controller.assemble(c,conv,user,receipt,parts,purpose,snapshot,pending_current=pending_current)
 for part in journal_parts(controller,refs):
  source_refs=[]
  for ref in part['sources']:
   aliases.setdefault(ref['id'],'s'+str(len(aliases)))
   source_refs.append(aliases[ref['id']])
  payload['context'].append({'kind':'JOURNAL_SELECTED','text':part['text'],'source_refs':source_refs})
 payload['source_refs_allowed']=list(aliases.values())
 payload=PrivateProviderPayload.model_validate(payload).model_dump(mode='json')
 if len(encode(payload).encode())>48000:raise SafeError('PROVIDER_INPUT_LIMIT',413)
 return payload,skills,aliases


def exact_context_hash(payload):
 return digest(encode({'context':payload['context'],'reflection_state':payload.get('reflection_state')}).encode())


def verify_canonical_receipt(data):
 if data.get('canonical_version')!=CANONICAL_VERSION:raise SafeError('PRIVATE_CONTEXT_PREVIEW_REQUIRED',403)
 signature={k:v for k,v in data.items() if k not in {'preview_hash','deep_selected','deep_preview'}}
 if digest(encode(signature).encode())!=data['preview_hash']:raise SafeError('PRIVATE_PREVIEW_CHANGED',409)
 payload=PrivateProviderPayload.model_validate(data['provider_payload']).model_dump(mode='json')
 if digest(encode(payload).encode())!=data['provider_request_hash'] or exact_context_hash(payload)!=data['context_hash']:
  raise SafeError('PRIVATE_EXACT_CONTEXT_CHANGED',409)
 return payload


def private_preview(controller,id,body):
 body=PrivateContextPreview.model_validate(body)
 gate=controller.private_gate;gate.require()
 with controller.store.connect() as c:
  conv=controller.conversations.row(c,id)
  if conv.revision!=body.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
 mode=conv.mode
 if mode=='DEEP':
  base=controller.preview_context(id,DeepContextPreview(operation_id=body.operation_id,base_revision=body.base_revision,text=body.text,selection=body.selection))
  deep_binding={k:base[k] for k in ('receipt_id','context_hash','preview_hash')}
  context=base['context'];snapshot=base['snapshot'];parent_receipt=base['receipt_id']
 else:
  built=controller.context.build_free(id,body.operation_id)
  context=built['context'];snapshot=None;deep_binding=None;parent_receipt=built['receipt']['id']
 refs=[r.model_dump(mode='json') for r in body.journal_entries]
 selected=journal_parts(controller,refs)
 with controller.store.transaction() as c:
  conv=controller.conversations.row(c,id)
  if conv.revision!=body.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
  row=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(parent_receipt,)).fetchone()
  if not row:raise SafeError('PRIVATE_CONTEXT_SOURCE_CHANGED',409)
  receipt=json.loads(row[0]);preview_source=str(uuid4())
  user=Message(schema_version=1,id=preview_source,conversation_id=conv.id,role='USER',raw_text=body.text,created_utc=now(),revision=1,provenance='USER_AUTHORED',source_reference=None,source_message_id=None,synthetic=False,privacy_class='PRIVATE_PERSONAL')
  ref={'id':preview_source,'revision':1}
  current={'kind':'CURRENT_TURN','text':body.text,'sources':[ref],'digest_version':None,'artifact_id':None,'memory_ref':None}
  ordered=[*context,current];pending=json.loads(encode(receipt));pending['sources'].append(ref)
  if len(encode(ordered).encode())>min(receipt['token_budget'],receipt['byte_budget']) or len(pending['sources'])>50:raise SafeError('CONTEXT_BUDGET_TOO_SMALL',409)
  payload,skills,aliases=canonical_private_payload(controller,c,conv,user,pending,ordered,body.purpose,snapshot,refs,pending_current=True)
  if len(encode(payload['context']).encode())>16000:raise SafeError('PRIVATE_CONTEXT_BUDGET',413)
  data={'private_preview':True,'canonical_version':CANONICAL_VERSION,'profile_id':PROFILE_ID,'provider_profile':gate.settings(mode),
   'conversation_id':str(id),'conversation_revision':body.base_revision,'draft_hash':digest(body.text.encode()),
   'purpose':body.purpose,'gate_generation':gate.generation,'selection':body.selection.model_dump(mode='json'),
   'journal_refs':refs,'journal_context_hash':digest(encode(selected).encode()),'deep_binding':deep_binding,
   'receipt_id':str(uuid4()),'context_hash':exact_context_hash(payload),'created_at':now(),
   'provider_payload':payload,'provider_request_hash':digest(encode(payload).encode()),'selected_skills':skills,
   'source_aliases':aliases,'pending_current_source':preview_source}
  if mode=='FREE':data['free_receipt_id']=parent_receipt
  data['preview_hash']=digest(encode(data).encode())
  receipt['id']=data['receipt_id']
  c.execute('INSERT INTO retrieval_receipts VALUES(?,?,?,?)',(data['receipt_id'],str(uuid4()),data['preview_hash'],encode(receipt)))
  c.execute('INSERT INTO deep_context_previews VALUES(?,?)',(data['receipt_id'],encode(data)))
 # Internal source IDs/receipts stay local; public preview displays exactly the transmitted objects.
 return {k:v for k,v in data.items() if k not in {'provider_payload','source_aliases','pending_current_source'}} | {
  'context':payload['context'],'reflection_state':payload.get('reflection_state'),
  'destination':'OPENAI_EXISTING_CHATGPT_SUBSCRIPTION','raw_audio':'NOT_SENT','journal_default':'OFF','exact_extra_context':True}


def selected_private_context(controller,id,body):
 controller.private_gate.require();binding=body.context_binding
 with controller.store.connect() as c:
  row=c.execute('SELECT payload FROM deep_context_previews WHERE receipt_id=?',(str(binding.receipt_id),)).fetchone()
  if not row:raise SafeError('PRIVATE_CONTEXT_PREVIEW_REQUIRED',403)
  data=json.loads(row[0]);conv=controller.conversations.row(c,id)
 if not data.get('private_preview') or data['conversation_id']!=str(id) or data['conversation_revision']!=body.base_revision or data['draft_hash']!=digest(body.text.encode()) or data['purpose']!=body.purpose or data['preview_hash']!=binding.preview_hash or data['context_hash']!=binding.context_hash:
  raise SafeError('PRIVATE_PREVIEW_CHANGED',409)
 verify_canonical_receipt(data)
 if data['gate_generation']!=controller.private_gate.generation or data['provider_profile']!=controller.private_gate.settings(conv.mode):raise SafeError('PRIVATE_PROVIDER_BINDING_CHANGED',409)
 if digest(encode(journal_parts(controller,data['journal_refs'])).encode())!=data['journal_context_hash']:raise SafeError('JOURNAL_SELECTION_CHANGED',409)
 result=dict(data)
 with controller.store.connect() as c:
  if conv.mode=='FREE':
   row=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(data['free_receipt_id'],)).fetchone()
   if not row:raise SafeError('PRIVATE_CONTEXT_SOURCE_CHANGED',409)
   result['deep_selected']=controller.context.replay_context(c,json.loads(row[0]));result['deep_preview']=None
  else:
   built,preview=controller.selected_context(c,id,body,ContextBinding.model_validate(data['deep_binding']))
   result.update(deep_selected=built,deep_preview=preview)
 return result


def approved_private_payload(controller,c,conv,user,receipt,parts,purpose,snapshot,data):
 """Check freshness against the sole constructor, then return the exact approved frozen payload."""
 controller.private_gate.require()
 if data['gate_generation']!=controller.private_gate.generation:raise SafeError('PRIVATE_AI_CONSENT_CHANGED',409)
 if data['provider_profile']!=controller.private_gate.settings(conv.mode):raise SafeError('PRIVATE_PROVIDER_BINDING_CHANGED',409)
 if digest(user.raw_text.encode())!=data['draft_hash']:raise SafeError('PRIVATE_PREVIEW_CHANGED',409)
 if digest(encode(journal_parts(controller,data['journal_refs'])).encode())!=data['journal_context_hash']:raise SafeError('JOURNAL_SELECTION_CHANGED',409)
 approved=verify_canonical_receipt(data)
 fresh,skills,aliases=canonical_private_payload(controller,c,conv,user,receipt,parts,purpose,snapshot,data['journal_refs'])
 if encode(fresh)!=encode(approved) or skills!=data['selected_skills']:raise SafeError('PRIVATE_EXACT_CONTEXT_CHANGED',409)
 expected_aliases=dict(data['source_aliases']);alias=expected_aliases.pop(data['pending_current_source']);expected_aliases[str(user.id)]=alias
 if aliases!=expected_aliases:raise SafeError('PRIVATE_EXACT_CONTEXT_CHANGED',409)
 return approved,skills,aliases
