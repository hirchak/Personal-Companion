"""Exact private preview receipts. Never query journal unless explicit bounded references are supplied."""
import json
from uuid import uuid4
from .storage import SafeError,encode,digest,now
from .deep_session_contracts import DeepContextPreview
from .local_private_ai import PROFILE_ID,PROFILES
from .local_private_contracts import PrivateContextPreview,PrivateProviderPayload

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

def private_preview(controller,id,body):
 body=PrivateContextPreview.model_validate(body)
 gate=controller.private_gate;gate.require()
 with controller.store.connect() as c:
  conv=controller.conversations.row(c,id)
  if conv.revision!=body.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
 mode=conv.mode
 if mode=='DEEP':
  base=controller.preview_context(id,DeepContextPreview(operation_id=body.operation_id,base_revision=body.base_revision,text=body.text,selection=body.selection))
  deep_binding={'receipt_id':base['receipt_id'],'context_hash':base['context_hash'],'preview_hash':base['preview_hash']}
  context=base['context'];snapshot=base['snapshot']
 else:
  # Existing Free builder is bounded to the current conversation; only six recent sources.
  built=controller.context.build_free(id,body.operation_id)
  context=built['context'];snapshot=None;deep_binding=None
  free_receipt_id=built['receipt']['id']
 refs=[r.model_dump(mode='json') for r in body.journal_entries]
 selected=journal_parts(controller,refs)
 visible=[*context,*selected,{'kind':'CURRENT_TURN','text':body.text,'sources':[]}]
 if len(encode(visible).encode())>16000:raise SafeError('PRIVATE_CONTEXT_BUDGET',413)
 data={'private_preview':True,'profile_id':PROFILE_ID,'provider_profile':gate.settings(mode),
  'conversation_id':str(id),'conversation_revision':body.base_revision,'draft_hash':digest(body.text.encode()),
  'purpose':body.purpose,'gate_generation':gate.generation,'selection':body.selection.model_dump(mode='json'),
  'journal_refs':refs,'journal_context_hash':digest(encode(selected).encode()),'deep_binding':deep_binding,
  'receipt_id':str(uuid4()),'context_hash':digest(encode({'context':visible,'snapshot':snapshot}).encode()),'created_at':now()}
 if mode=='FREE':data['free_receipt_id']=free_receipt_id
 data['preview_hash']=digest(encode(data).encode())
 with controller.store.transaction() as c:
  parent_receipt=base['receipt_id'] if mode=='DEEP' else free_receipt_id
  row=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(parent_receipt,)).fetchone()
  receipt=json.loads(row[0]);receipt['id']=data['receipt_id']
  c.execute('INSERT INTO retrieval_receipts VALUES(?,?,?,?)',(data['receipt_id'],str(uuid4()),data['preview_hash'],encode(receipt)))
  c.execute('INSERT INTO deep_context_previews VALUES(?,?)',(data['receipt_id'],encode(data)))
 return dict(data,context=visible,reflection_state=snapshot,destination='OPENAI_EXISTING_CHATGPT_SUBSCRIPTION',raw_audio='NOT_SENT',journal_default='OFF',exact_extra_context=True)

def selected_private_context(controller,id,body):
 controller.private_gate.require()
 binding=body.context_binding
 with controller.store.connect() as c:
  row=c.execute('SELECT payload FROM deep_context_previews WHERE receipt_id=?',(str(binding.receipt_id),)).fetchone()
  if not row:raise SafeError('PRIVATE_CONTEXT_PREVIEW_REQUIRED',403)
  data=json.loads(row[0]);conv=controller.conversations.row(c,id)
 if not data.get('private_preview') or data['conversation_id']!=str(id) or data['conversation_revision']!=body.base_revision or data['draft_hash']!=digest(body.text.encode()) or data['purpose']!=body.purpose or data['preview_hash']!=binding.preview_hash or data['context_hash']!=binding.context_hash:
  raise SafeError('PRIVATE_PREVIEW_CHANGED',409)
 if data['gate_generation']!=controller.private_gate.generation or data['provider_profile']!=controller.private_gate.settings(conv.mode):raise SafeError('PRIVATE_PROVIDER_BINDING_CHANGED',409)
 current=journal_parts(controller,data['journal_refs'])
 if digest(encode(current).encode())!=data['journal_context_hash']:raise SafeError('JOURNAL_SELECTION_CHANGED',409)
 result=dict(data)
 if conv.mode=='FREE':
  with controller.store.connect() as c:
   row=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(data['free_receipt_id'],)).fetchone()
   if not row:raise SafeError('PRIVATE_CONTEXT_SOURCE_CHANGED',409)
   result['deep_selected']=controller.context.replay_context(c,json.loads(row[0]))
   result['deep_preview']=None
 if conv.mode=='DEEP':
  from .deep_session_contracts import ContextBinding
  with controller.store.connect() as c:built,preview=controller.selected_context(c,id,body,ContextBinding.model_validate(data['deep_binding']))
  result.update(deep_selected=built,deep_preview=preview)
 return result

def add_selected_journal(controller,payload,aliases,data):
 controller.private_gate.require()
 if data['gate_generation']!=controller.private_gate.generation:raise SafeError('PRIVATE_AI_CONSENT_CHANGED',409)
 parts=journal_parts(controller,data['journal_refs'])
 if digest(encode(parts).encode())!=data['journal_context_hash']:raise SafeError('JOURNAL_SELECTION_CHANGED',409)
 payload=json.loads(encode(payload));aliases=dict(aliases)
 for part in parts:
  refs=[]
  for ref in part['sources']:
   if ref['id'] not in aliases:aliases[ref['id']]='s'+str(len(aliases))
   refs.append(aliases[ref['id']])
  payload['context'].append({'kind':'JOURNAL_SELECTED','text':part['text'],'source_refs':refs})
 payload['source_refs_allowed']=list(aliases.values())
 payload=PrivateProviderPayload.model_validate(payload).model_dump(mode='json')
 if len(encode(payload).encode())>48000:raise SafeError('PROVIDER_INPUT_LIMIT',413)
 return payload,aliases
