"""One deterministic synthetic conversation controller; model output has no write/tool authority."""
import json,threading,time,re
from uuid import UUID,uuid4,uuid5
from .storage import SafeError,encode,digest,now,REPO
from .conversation_contracts import SendMessage,Message
from .conversation_runtime_contracts import ConversationRequest,ConversationCandidate,ProviderPayload,InferenceStart,InferenceAction
from .conversation_skills import ConversationSkills
from .reflection import Reflection
from .reflection_contracts import ContextRequest,GoalRef
from .deep_session import DeepSessions,DEEP_TABLES
from .deep_session_contracts import DeepContextPreview,ContextSelection
from datetime import datetime,timedelta,timezone
from contextlib import nullcontext
from .conversation_release import ReleasePolicy, ReleaseRejected, valid_receipt

NAMESPACE=UUID('70000000-0000-4000-8000-000000000004')
RUNTIME_TABLES=(
 'CREATE TABLE IF NOT EXISTS conversation_inferences(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,operation_id TEXT UNIQUE NOT NULL,fingerprint TEXT NOT NULL,state TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL)',
 'CREATE UNIQUE INDEX IF NOT EXISTS conversation_one_foreground ON conversation_inferences(conversation_id) WHERE state IN ("QUEUED","RUNNING")',
 'CREATE TABLE IF NOT EXISTS inference_actions(operation_id TEXT PRIMARY KEY,job_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT NOT NULL)',
)

SAFE_FAILURE_CODES = frozenset('''ADDRESS_FORM_UNSUPPORTED ADDRESS_FORM_MISMATCH CANCELLED
MODEL_OUTPUT_INVALID PROVIDER_FAILED PROVIDER_UNAVAILABLE PROVIDER_TIMEOUT PROVIDER_BINDING_CHANGED
PROVIDER_TURN_FAILED PROVIDER_PROTOCOL_INVALID PROVIDER_RPC_FAILED PROVIDER_PROCESS_FAILED
PROVIDER_TOOL_REQUEST_DENIED PROVIDER_OUTPUT_LIMIT PROVIDER_INPUT_LIMIT CONTROLLER_FRAME_CHANGED
PRIVATE_PROVIDER_ROUTE_UNAVAILABLE PRIVATE_PROVIDER_PROFILE_UNVERIFIED PROVIDER_EFFORT_UNSUPPORTED
EXISTING_CHATGPT_AUTH_REQUIRED MODEL_CAPABILITY_UNVERIFIED PRIVATE_PROVIDER_TRANSPORT_UNAVAILABLE
PRIVATE_AI_DISABLED PRIVATE_AI_NOT_ENABLED PRIVATE_AI_CONSENT_CHANGED PRIVATE_ATTEMPT_LIMIT
PRIVATE_OWNER_ACK_REQUIRED PRIVATE_PROFILE_NOT_AVAILABLE CODEX_CLI_UNAVAILABLE
PRIVATE_PROVIDER_OS_ISOLATION_UNAVAILABLE PROVIDER_ISOLATION_UNVERIFIED
CONVERSATION_CHANGED SOURCE_CHANGED SKILL_CHANGED SKILL_OFF CONTEXT_CHANGED MAP_CHANGED
GOAL_NOT_ACTIVE GOAL_NOT_FOUND GOAL_REVISION_NOT_FOUND SESSION_NOT_OPEN
PRIVATE_CONTEXT_SOURCE_CHANGED PRIVATE_EXACT_CONTEXT_CHANGED PRIVATE_PREVIEW_CHANGED
PRIVATE_PROVIDER_BINDING_CHANGED JOURNAL_SELECTION_CHANGED PRIVATE_LOCAL_ROOT_REQUIRED
MODEL_SOURCE_OUT_OF_SCOPE FREE_MAP_CANDIDATE_DENIED UNREQUESTED_GOAL_CANDIDATE
CLOSURE_SCHEMA_REQUIRED MAIN_QUESTION_LIMIT USER_STATEMENT_QUOTE_REQUIRED MAP_CAPACITY_REVIEW_REQUIRED
CONTENT_POLICY_INVALID CONTENT_POLICY_CHANGED CONTENT_DECISION_TIMEOUT CONTENT_DECISION_INVALID
CONTENT_DECISION_BINDING_CHANGED CONTENT_DECISION_STALE CONTENT_RELEASE_REJECTED CONTENT_REVIEW_REQUIRED
INFERENCE_PERSISTENCE_FAILED
PROCESS_INTERRUPTED'''.split())

def safe_result_metadata(result):
    value={k:result[k] for k in ('route','model','effort','profile') if k in result}
    if type(result.get('streaming_actual')) is bool:value['streaming_actual']=result['streaming_actual']
    if type(result.get('elapsed_ms')) in (int,float) and 0<=result['elapsed_ms']<10**9:value['elapsed_ms']=result['elapsed_ms']
    if isinstance(result.get('auth_type'),str) and result['auth_type'] in {'NONE','EXISTING_CHATGPT','EXISTING_CHATGPT_CLI_ONLY'}:value['auth_type']=result['auth_type']
    if isinstance(result.get('frame_hash'),str) and re.fullmatch('[0-9a-f]{64}',result['frame_hash']):value['frame_hash']=result['frame_hash']
    usage=result.get('usage')
    if isinstance(usage,dict):value['usage']={k:v for k,v in usage.items() if k in {'inputTokens','outputTokens','totalTokens','cachedInputTokens','reasoningTokens'} and type(v) is int and 0<=v<10**12}
    if isinstance(result.get('attempt_id'),str):
        try:value['attempt_id']=str(UUID(result['attempt_id']))
        except ValueError:pass
    return value

def safe_provider_failure(value):
    result={'category':'UNCLASSIFIED_PROVIDER_TURN_FAILURE'}
    if isinstance(value,dict):
        if isinstance(value.get('category'),str) and value['category'] in {'UNCLASSIFIED_PROVIDER_TURN_FAILURE','INVALID_STRUCTURED_SCHEMA','REASONING_EFFORT_REJECTED','SUBSCRIPTION_LIMIT_REACHED','EXISTING_AUTH_ROUTE_UNAVAILABLE'}:result['category']=value['category']
        if type(value.get('http_status')) is int and 100<=value['http_status']<=599:result['http_status']=value['http_status']
    return result

def check_inferences(c):
    """Typed snapshot validation; restore never grants provider activation or resumes work."""
    from pydantic import ValidationError
    from .conversation_runtime_contracts import ConversationRequest
    try:
        for row in c.execute('SELECT * FROM conversation_inferences'):
            d=json.loads(row['payload'])
            if d['id']!=row['id'] or d['conversation_id']!=row['conversation_id'] or d['state']!=row['state'] or d['revision']!=row['revision']:raise ValueError()
            if d['state'] not in {'QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED'} or d['revision']<1:raise ValueError()
            UUID(d['id']);UUID(d['source_message_id'])
            request_type=ConversationRequest
            private=d['request_metadata'].get('schema_version')==2
            if private:
                from .local_private_contracts import PrivateConversationRequest
                request_type=PrivateConversationRequest
            request_type.model_validate(dict(d['request_metadata'],payload={
                'mode':d['request_metadata']['mode'],'purpose':d['purpose'],'synthetic':not private,'language':'uk',
                'skills':[],'context':[],'current_message_ref':'s0','source_refs_allowed':['s0'],
                'goal_revision':None,'tool_permissions':[],'controller_frame_hash':'0'*64}))
            if not re.fullmatch('[0-9a-f]{64}',d['request_hash']):raise ValueError()
            if d['state']=='COMPLETED':
                ConversationCandidate.model_validate(d['candidate'])
                if 'release_policy_hash' in d and not valid_receipt(d):raise ValueError()
            elif 'release_policy_hash' in d and (d['candidate'] is not None or d.get('release_receipt') is not None):raise ValueError()
    except (KeyError,ValueError,TypeError,ValidationError):raise SafeError('INFERENCE_INTEGRITY') from None

QUOTE_PATTERN = r'«([^«»]{1,1000})»|“([^“”]{1,1000})”|"([^"\n]{1,1000})"'

def generated_text(text, payload, examples=False):
    """Remove source quotations, and explicitly labeled comparison/example quotations.

    Unlabeled/standalone quoted questions remain follow-ups. Ambiguous language counts;
    this is a bounded deterministic convention, not a general semantic classifier.
    """
    normalized = lambda value: ' '.join(value.casefold().split())
    known = [normalized(p['text']) for p in payload.get('context', [])]
    known += [normalized(i['text']) for i in (payload.get('reflection_state') or {}).get('items', [])]
    def replace(match):
        quote = next(v for v in match.groups() if v is not None)
        prefix = text[max(0, text.rfind('\n', 0, match.start()) + 1):match.start()]
        labeled = examples and re.search(
            r'(?:варіант|опція|приклад|репліка|формулювання)\b[^?\n]{0,100}[:—–-]\s*$',
            prefix, re.IGNORECASE)
        if any(normalized(quote) in source for source in known) or labeled:
            return ' ' * len(match.group())
        return match.group()
    result = re.sub(QUOTE_PATTERN, replace, text)
    # Explicit historical blockquotes must still match actual supplied source text.
    for match in list(re.finditer(r'^\s*>\s*([^\n]+)',result,re.MULTILINE))[::-1]:
        if any(normalized(match.group(1)) in source for source in known):
            result=result[:match.start()]+' '*len(match.group())+result[match.end():]
    return result

def main_question_count(text, payload):
    return len(re.findall(r'\?+', generated_text(text, payload, examples=True)))

def verify_address_form(text, payload):
    """Bounded formal-register guard, not a complete Ukrainian morphology checker.

    Include the observed verb-only address violation; source and labeled fictional
    quotations retain their original register through the existing quote handling.
    """
    if payload.get('address_form', 'FORMAL_VY') != 'FORMAL_VY':
        raise SafeError('ADDRESS_FORM_UNSUPPORTED')
    if re.search(r"\b(?:ти|тебе|тобі|тобою|твій|твоя|твоє|твої|твого|твоєї|твоїх|твоїм|твоїми|твою|твоєму|хочеш)\b",
                 generated_text(text, payload, examples=True), re.IGNORECASE):
        raise SafeError('ADDRESS_FORM_MISMATCH')

class ConversationController:
    def __init__(self,conversations,provider=None,skills=None,timeout=60,private_gate=None,release_policy=None):
        self.conversations=conversations;self.store=conversations.store;self.context=Reflection(conversations);self.deep=DeepSessions(conversations);self.provider=provider;self.skills=skills or ConversationSkills();self.timeout=timeout
        self.private_gate=private_gate
        self.release_policy=release_policy or ReleasePolicy()
        if not conversations.synthetic_demo and private_gate is None:raise SafeError('M7C_SYNTHETIC_SCOPE_REQUIRED',403)
        if private_gate is not None:
            from .root_types import RootKind
            if conversations.synthetic_demo or self.store.root_kind!=RootKind.PRIVATE_LOCAL:raise SafeError('PRIVATE_LOCAL_ROOT_REQUIRED',403)
        self.lock=threading.RLock();self.events={};self.previews={};self.workers={};self.failure_notices={}
        with self.store.transaction() as c:
            for sql in RUNTIME_TABLES:c.execute(sql)
            for sql in DEEP_TABLES:c.execute(sql)
            # A restarted server never resumes an old external request or assumes a partial result is final.
            c.execute('UPDATE conversation_inferences SET state="FAILED",revision=revision+1,payload=json_set(payload,"$.state","FAILED","$.error","PROCESS_INTERRUPTED","$.revision",revision+1) WHERE state IN ("QUEUED","RUNNING")')
    def provider_for(self,mode):
        if self.private_gate is not None:
            return self.private_gate.provider(mode) if self.private_gate.adapters else None
        return self.provider
    def revoke_private(self):
        with self.lock:
            for event in self.events.values():event.set()
            with self.store.transaction() as c:
                c.execute('UPDATE conversation_inferences SET state="CANCELLED",revision=revision+1,payload=json_set(payload,"$.state","CANCELLED","$.error","PRIVATE_AI_DISABLED","$.revision",revision+1) WHERE state IN ("QUEUED","RUNNING")')
    def private_preview(self,id,body):
        from .local_private_context import private_preview
        return private_preview(self,id,body)
    def status(self):
        if self.private_gate is not None:
            return dict(self.private_gate.status(),synthetic_demo=False,responder='PRIVATE_OWNER_CONSENTED' if self.private_gate.adapters else 'OFF',live_provider_calls=any(a.metadata().get('live') is True for a in self.private_gate.adapters.values()),clinical_active=0,real_private_data=True,normal_user_mode=True,skills=self.skills.catalog(),provider_profiles=__import__('apps.core.local_private_ai',fromlist=['PROFILES']).PROFILES,**({'mode':'PRIVATE_OWNER_CONSENTED'} if self.private_gate.adapters else {}))
        metadata=self.provider.metadata() if self.provider else None
        return {'synthetic_demo':True,'mode':'LIVE_SYNTHETIC' if metadata and metadata.get('live') else 'OFFLINE_FIXTURE' if self.provider else 'OFF','responder':'LIVE_SYNTHETIC' if metadata and metadata.get('live') else 'OFFLINE_FIXTURE' if self.provider else 'OFF','live_provider_calls':bool(metadata and metadata.get('live')),'clinical_active':0,'real_private_data':False,'actual_asr':'SEPARATE_LOCAL_GATE','provider':metadata,'skills':self.skills.catalog(),'normal_user_mode':False}
    def row(self,c,id,conversation_id=None):
        r=c.execute('SELECT * FROM conversation_inferences WHERE id=?',(str(id),)).fetchone()
        if not r or conversation_id is not None and r['conversation_id']!=str(conversation_id):raise SafeError('INFERENCE_NOT_FOUND',404)
        d=json.loads(r['payload']);d.update(state=r['state'],revision=r['revision']);return d
    def public(self,d):
        value={k:d[k] for k in ('id','conversation_id','state','revision','purpose','error','created_at','updated_at','candidate','request_metadata','provider_result')}
        if value['error'] is not None and (not isinstance(value['error'],str) or value['error'] not in SAFE_FAILURE_CODES):value['error']='PROVIDER_FAILED'
        if isinstance(value['provider_result'],dict):
            observed=value['provider_result'];safe=safe_result_metadata(observed)
            for k,field in [('route','provider_route'),('model','provider_model'),('effort','provider_effort'),('profile','provider_profile')]:
                if k in safe and safe[k]!=d['request_metadata'].get(field):safe.pop(k)
            if 'provider_failure' in observed:safe['provider_failure']=safe_provider_failure(observed['provider_failure'])
            value['provider_result']=safe
        elif value['provider_result'] is not None:value['provider_result']=None
        released=d['state']=='COMPLETED' and ('release_policy_hash' not in d or valid_receipt(d))
        if not released:value['candidate']=None
        value['partial_candidate']=None  # retained wire field; never carries generated text
        value['release_status']='RELEASED' if released else 'AWAITING_VALIDATION' if d.get('validation_started') and d['state']=='RUNNING' else 'GENERATING' if d['state'] in {'QUEUED','RUNNING'} else d['state']
        if d['state']=='COMPLETED' and not released:
            value.update(state='FAILED',error='CONTENT_RECEIPT_INVALID',release_status='FAILED')
        if d['state'] in {'QUEUED','RUNNING'} and d['id'] in self.failure_notices:
            value.update(state='FAILED',error='INFERENCE_PERSISTENCE_FAILED',release_status='FAILED',candidate=None)
        return value
    def get(self,conversation_id,id):
        with self.store.connect() as c:d=self.row(c,id,conversation_id)
        return self.public(d)
    def page(self,conversation_id):
        with self.store.connect() as c:
            c.execute('BEGIN')
            page=self.conversations.view(c,self.conversations.row(c,conversation_id))
            r=c.execute('SELECT id FROM conversation_inferences WHERE conversation_id=? ORDER BY json_extract(payload,"$.created_at") DESC LIMIT 1',(str(conversation_id),)).fetchone()
            job=self.public(self.row(c,r['id'],conversation_id)) if r else None
        return dict(page,inference_job=job,responder=self.status()['responder'])
    def journal_point(self,c,conversation_id,body):
        self.conversations.row(c,conversation_id)
        row=c.execute('SELECT payload FROM conversation_messages WHERE id=? AND conversation_id=?',(str(body.message_id),str(conversation_id))).fetchone()
        if not row:raise SafeError('SOURCE_CHANGED',409)
        source=Message.model_validate_json(row[0])
        if source.role!='USER' or source.provenance!='USER_AUTHORED' or source.synthetic!=self.conversations.synthetic_demo:raise SafeError('USER_AUTHORED_SOURCE_REQUIRED',403)
        if source.revision!=body.source_revision:raise SafeError('SOURCE_CHANGED',409)
        point={'conversation_id':str(conversation_id),'message_id':str(source.id),'source_revision':source.revision,'created_utc':source.created_utc,'provenance':'USER_AUTHORED','raw_text':source.raw_text}
        return dict(point,preview_hash=digest(encode(point).encode()))
    def journal_preview(self,conversation_id,body):
        with self.store.connect() as c:return self.journal_point(c,conversation_id,body)
    def journal_confirm(self,journal,conversation_id,body):
        from .models import Create,EntryInput
        # Explicit user action only. One transaction rechecks the source and writes through
        # the accepted journal domain; source text/assistant candidates never become commands.
        with self.store.transaction() as c:
            point=self.journal_point(c,conversation_id,body)
            if point['preview_hash']!=body.preview_hash:raise SafeError('PREVIEW_CHANGED',409)
            entry_id=uuid5(NAMESPACE,str(body.operation_id)+':journal-point')
            request=Create(operation_id=body.operation_id,entry_id=entry_id,base_revision=0,payload=EntryInput(type='inbox',raw_text=point['raw_text']))
            fingerprint=digest(encode({'conversation_id':str(conversation_id),'confirmation':body.model_dump(mode='json')}).encode())
            return journal.write_in(c,'create',entry_id,request,fingerprint)
    def preview_context(self,id,b:DeepContextPreview):
        with self.store.transaction() as c:
            conv=self.conversations.row(c,id)
            if conv.revision!=b.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
            session=self.deep.session(c,id)
            if session['phase'] in {'CLOSED','PAUSED'}:raise SafeError('SESSION_NOT_OPEN',409)
            goal=self.context.row(c,conv.goal_binding.id,conv.goal_binding.revision)
        selection=b.selection.model_dump(mode='json');end=now()
        if selection['type']=='CUSTOM':start,end=selection['window_start'],selection['window_end']
        elif selection['type']=='GOAL_START':start=goal.created_at
        else:start=(datetime.fromisoformat(end)-timedelta(days=7 if selection['type']=='LAST_7_DAYS' else 30)).isoformat()
        built=self.context.build(ContextRequest(operation_id=b.operation_id,goal=GoalRef(id=conv.goal_binding.id,revision=conv.goal_binding.revision),conversation_id=id,window_start=start,window_end=end,selection_type=selection['type'],timezone=selection['timezone'],token_budget=8000,byte_budget=16000,max_sources=30,prepare_synthetic_digests=False))
        with self.store.transaction() as c:
            conv=self.conversations.row(c,id)
            if conv.revision!=b.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
            snapshot=self.deep.snapshot(c,id,built['receipt'])
            refs={r['id']:r for r in built['receipt']['sources']}
            for item in snapshot['items']+snapshot['prior_closures']:
                for r in item['sources']:refs[r['id']]=r
            if len(refs)>50:raise SafeError('CONTEXT_SOURCE_LIMIT',413)
            built['receipt']['sources']=list(refs.values())
            c.execute('UPDATE retrieval_receipts SET payload=? WHERE id=?',(encode(built['receipt']),built['receipt']['id']))
            context_hash=digest(encode({'context':built['context'],'snapshot':snapshot}).encode())
            data={'conversation_id':str(id),'conversation_revision':b.base_revision,'text_hash':digest(b.text.encode()),'selection':dict(selection,window_start=start,window_end=end),'receipt_id':built['receipt']['id'],'context_hash':context_hash,'snapshot':snapshot}
            data['preview_hash']=digest(encode(data).encode())
            old=c.execute('SELECT payload FROM deep_context_previews WHERE receipt_id=?',(data['receipt_id'],)).fetchone()
            if old and json.loads(old[0])!=data:raise SafeError('PREVIEW_CHANGED',409)
            c.execute('INSERT OR IGNORE INTO deep_context_previews VALUES(?,?)',(data['receipt_id'],encode(data)))
        return dict(data,context=built['context'],sources=built['receipt']['sources'])
    def selected_context(self,c,id,body,binding):
        row=c.execute('SELECT payload FROM deep_context_previews WHERE receipt_id=?',(str(binding.receipt_id),)).fetchone()
        if not row:raise SafeError('CONTEXT_PREVIEW_REQUIRED',409)
        data=json.loads(row[0])
        if data['conversation_id']!=str(id) or data['conversation_revision']!=body.base_revision or data['text_hash']!=digest(body.text.encode()) or data['preview_hash']!=binding.preview_hash or data['context_hash']!=binding.context_hash:raise SafeError('PREVIEW_CHANGED',409)
        receipt=json.loads(c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(str(binding.receipt_id),)).fetchone()[0])
        built=self.context.replay_context(c,receipt);snapshot=self.deep.snapshot(c,id,receipt)
        if digest(encode({'context':built['context'],'snapshot':snapshot}).encode())!=binding.context_hash:raise SafeError('CONTEXT_CHANGED',409)
        conv=self.conversations.row(c,id)
        if conv.revision!=body.base_revision:raise SafeError('CONVERSATION_CHANGED',409)
        return built,data
    def assemble(self,c,conversation,user_message,receipt,parts,purpose,snapshot=None,*,pending_current=False):
        private=self.private_gate is not None
        if private:
            self.private_gate.require()
            if user_message.synthetic or conversation.synthetic:raise SafeError('PRIVATE_PROVENANCE_REQUIRED',403)
        elif not user_message.synthetic or not conversation.synthetic:raise SafeError('REAL_PRIVATE_DATA_OFF',403)
        if receipt['confirmed_memory_refs']:raise SafeError('PRIVATE_MEMORY_SCOPE_NOT_AUTHORIZED' if private else 'SYNTHETIC_MEMORY_SCOPE_UNVERIFIED',403)
        if conversation.mode=='DEEP':
            goal=self.context.row(c,conversation.goal_binding.id,conversation.goal_binding.revision)
            current=self.context.row(c,conversation.goal_binding.id)
            if goal.synthetic!=self.conversations.synthetic_demo:raise SafeError('CONVERSATION_SCOPE_MISMATCH',403)
            if current.state!='ACTIVE':raise SafeError('GOAL_NOT_ACTIVE',409)
        aliases={s['id']:'s'+str(i) for i,s in enumerate(receipt['sources'])}
        if str(user_message.id) not in aliases:raise SafeError('CURRENT_MESSAGE_NOT_IN_RECEIPT',409)
        if pending_current and not private:raise SafeError('PRIVATE_REQUEST_REQUIRED',403)
        for ref in receipt['sources']:
            if pending_current and ref['id']==str(user_message.id):continue
            row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
            if not row or json.loads(row[0])['synthetic']!=self.conversations.synthetic_demo:raise SafeError('CONVERSATION_SCOPE_MISMATCH',403)
        selected=self.skills.select(conversation.mode,purpose)
        payload={'mode':conversation.mode,'purpose':purpose,'synthetic':not private,'language':'uk','address_form':'FORMAL_VY','skills':[{k:s[k] for k in ('skill_id','version','content_hash','instructions')} for s in selected],'context':[{'kind':p['kind'],'text':p['text'],'source_refs':[aliases[s['id']] for s in p['sources']]} for p in parts],'current_message_ref':aliases[str(user_message.id)],'source_refs_allowed':list(aliases.values()),'goal_revision':conversation.goal_binding.revision if conversation.goal_binding else None,'tool_permissions':[],'controller_frame_hash':digest(encode(json.loads((REPO/('skills/conversation/local_private_controller_frame.json' if private else 'skills/conversation/controller_frame.json')).read_text())).encode())}
        if snapshot:
            payload['reflection_state']={'focus':snapshot['session']['focus'],'phase':snapshot['session']['phase'],'map_version':snapshot['map_version'],'items':[{'kind':i['kind'],'text':i['text'],'provenance':i['provenance'],'state':i['state'],'source_refs':[aliases[r['id']] for r in i['sources']]} for i in snapshot['items']],'prior_closures':[{'closure':i['closure'],'source_refs':[aliases[r['id']] for r in i['sources']]} for i in snapshot['prior_closures']]}
        if private:
            from .local_private_contracts import PrivateProviderPayload
            payload=PrivateProviderPayload.model_validate(payload).model_dump(mode='json')
        else:payload=ProviderPayload.model_validate(payload).model_dump(mode='json')
        if len(encode(payload).encode())>48000:raise SafeError('PROVIDER_INPUT_LIMIT',413)
        return payload,self.skills.binding(selected),aliases
    def send(self,id,body:InferenceStart,launch=True):
        id=str(id);op=str(body.operation_id);fingerprint=digest(encode({'id':id,'body':body.model_dump(mode='json')}).encode())
        with self.lock:
            with self.store.connect() as c:
                prior=c.execute('SELECT id,fingerprint FROM conversation_inferences WHERE operation_id=?',(op,)).fetchone()
                if prior:
                    if prior['fingerprint']!=fingerprint:raise SafeError('OPERATION_REUSE',409)
                    return self.page(id)
                if c.execute('SELECT 1 FROM conversation_inferences WHERE conversation_id=? AND state IN ("QUEUED","RUNNING")',(id,)).fetchone():raise SafeError('INFERENCE_BUSY',409)
            selected=None;preview=None
            with self.store.connect() as c:before=self.conversations.row(c,id)
            private=self.private_gate is not None
            provider=self.provider_for(before.mode)
            private_preview_data=None
            if private:
                from .local_private_contracts import PrivateInferenceStart
                if not isinstance(body,PrivateInferenceStart):raise SafeError('PRIVATE_REQUEST_REQUIRED',403)
                if provider is not None and body.context_binding is None and body.standard_send:
                    if not self.private_gate.consent.read():raise SafeError('DURABLE_CONSENT_REQUIRED',403)
                    if before.mode=='DEEP':self.private_gate.consent.require_scope(self,id,body.selection)
                    from .local_private_contracts import PrivateContextPreview
                    from .deep_session_contracts import ContextBinding
                    exact=self.private_preview(id,PrivateContextPreview(operation_id=uuid5(NAMESPACE,op+':private-preview'),base_revision=body.base_revision,text=body.text,purpose=body.purpose,selection=body.selection))
                    body=body.model_copy(update={'context_binding':ContextBinding(receipt_id=exact['receipt_id'],context_hash=exact['context_hash'],preview_hash=exact['preview_hash'])})
                if provider is not None and body.context_binding is None:raise SafeError('PRIVATE_EXACT_CONTEXT_PREVIEW_REQUIRED',403)
                if body.context_binding:
                    from .local_private_context import selected_private_context
                    private_preview_data=selected_private_context(self,id,body)
                    selected,preview=private_preview_data['deep_selected'],private_preview_data['deep_preview']
            if before.mode=='FREE' and body.context_binding and not private:raise SafeError('DEEP_MODE_REQUIRED',409)
            if before.mode=='DEEP' and not private:
                binding=body.context_binding
                if binding is None:
                    # Compatibility callers use a deterministic preview; UI always binds its explicit preview.
                    preview=self.preview_context(id,DeepContextPreview(operation_id=uuid5(NAMESPACE,op+':preview'),base_revision=body.base_revision,text=body.text,selection=ContextSelection()))
                    from .deep_session_contracts import ContextBinding
                    binding=ContextBinding(receipt_id=preview['receipt_id'],context_hash=preview['context_hash'],preview_hash=preview['preview_hash'])
                with self.store.connect() as c:selected,preview=self.selected_context(c,id,body,binding)
            # User source persists even if provider is OFF or later fails; never fake a live response.
            request=SendMessage(operation_id=body.operation_id,base_revision=body.base_revision,text=body.text,source_reference=getattr(body,'source_reference',None))
            page=self.conversations.send(id,request,respond=False)
            if provider is None:return dict(page,inference_job=None,responder='OFF')
            with self.store.connect() as c:conv=self.conversations.row(c,id)
            source_id=str(uuid5(__import__('apps.core.conversation',fromlist=['NAMESPACE']).NAMESPACE,op+':user'))
            snapshot=preview['snapshot'] if preview else None
            if conv.mode=='DEEP' or private_preview_data:
                # Freeze exactly previewed history/map; current draft is a separate explicit source.
                built=json.loads(encode(selected));receipt=built['receipt'];receipt['id']=str(uuid5(NAMESPACE,op+':context'))
                with self.store.transaction() as c:
                    current=Message.model_validate_json(c.execute('SELECT payload FROM conversation_messages WHERE id=?',(source_id,)).fetchone()[0])
                    ref={'id':source_id,'revision':current.revision}
                    part={'kind':'CURRENT_TURN','text':current.raw_text,'sources':[ref],'digest_version':None,'artifact_id':None,'memory_ref':None}
                    built['context'].append(part);receipt['parts_meta'].append({k:v for k,v in part.items() if k!='text'});receipt['sources'].append(ref)
                    used=len(encode(built['context']).encode())
                    if used>min(receipt['token_budget'],receipt['byte_budget']) or len(receipt['sources'])>50:raise SafeError('CONTEXT_BUDGET_TOO_SMALL',409)
                    receipt['used_tokens_upper_bound']=used;receipt['used_bytes_estimate']=used
                    c.execute('INSERT INTO retrieval_receipts VALUES(?,?,?,?)',(receipt['id'],str(uuid5(NAMESPACE,op+':context')),fingerprint,encode(receipt)))
            else:built=self.context.build_free(id,uuid5(NAMESPACE,op+':context'))
            with self.store.connect() as c:
                user=Message.model_validate_json(c.execute('SELECT payload FROM conversation_messages WHERE id=?',(source_id,)).fetchone()[0])
                if private_preview_data:
                    from .local_private_context import approved_private_payload
                    payload,bindings,aliases=approved_private_payload(self,c,conv,user,built['receipt'],built['context'],body.purpose,snapshot,private_preview_data)
                else:payload,bindings,aliases=self.assemble(c,conv,user,built['receipt'],built['context'],body.purpose,snapshot)
            request_hash=digest(encode(payload).encode());job_id=str(uuid5(NAMESPACE,op+':job'));metadata=provider.metadata()
            context_hash=private_preview_data['context_hash'] if private_preview_data else digest(encode(built['context']).encode())
            request_type=ConversationRequest
            if private:
                from .local_private_contracts import PrivateConversationRequest
                request_type=PrivateConversationRequest
            r=request_type(schema_version=2 if private else 1,request_id=UUID(job_id),mode=conv.mode,purpose=body.purpose,selected_skills=bindings,context_hash=context_hash,retrieval_receipt_id=UUID(built['receipt']['id']),provider_route=metadata['route'],provider_model=metadata['model'],provider_effort=metadata.get('effort','low'),provider_profile=metadata.get('profile','M7C_COMPAT_LOW'),selection_type=preview['selection']['type'] if preview else 'FREE_RECENT',selection_timezone=built['receipt']['timezone'],selected_window_start=built['receipt']['window_start'],selected_window_end=built['receipt']['window_end'],selected_receipt_id=UUID(preview['receipt_id']) if preview else None,selected_context_hash=preview['context_hash'] if preview else None,map_snapshot_hash=digest(encode(snapshot).encode()) if snapshot else None,consent_scope='M8D_THIS_OWNER_EXACT_APPROVED_PRIVATE_CONTEXT' if private else 'M7D_OWNER_AUTHORIZED_ORIGINAL_SYNTHETIC_ONLY',synthetic=not private,clinical_active=0,tools=[],timeout_seconds=self.timeout,input_byte_budget=48000,response_schema='M7C_CONVERSATION_CANDIDATE_V1',payload=payload)
            meta=r.model_dump(mode='json');meta.pop('payload')
            d={'id':job_id,'conversation_id':id,'purpose':body.purpose,'state':'QUEUED','revision':1,'error':None,'created_at':now(),'updated_at':now(),'candidate':None,'request_metadata':meta,'provider_result':None,'request_hash':request_hash,'source_message_id':source_id,'conversation_revision':conv.revision,'aliases':aliases,'attempt':0,'deep_snapshot':snapshot}
            d['release_policy_hash']=self.release_policy.identity();d['release_receipt']=None
            if private_preview_data:d['private_context']=private_preview_data
            with self.store.transaction() as c:c.execute('INSERT INTO conversation_inferences VALUES(?,?,?,?,?,?,?)',(job_id,id,op,fingerprint,'QUEUED',1,encode(d)))
            self.events[job_id]=threading.Event()
            if launch:self.launch(job_id)
            return self.page(id)
    def launch(self,id):
        t=threading.Thread(target=self.run,args=(str(id),),daemon=True);self.workers[str(id)]=t;t.start()
    def request_for(self,c,d):
        if 'release_policy_hash' in d and d['release_policy_hash']!=self.release_policy.identity():raise SafeError('CONTENT_POLICY_CHANGED',409)
        conv=self.conversations.row(c,d['conversation_id'])
        if conv.revision!=d['conversation_revision'] or conv.state!='ACTIVE':raise SafeError('CONVERSATION_CHANGED',409)
        self.skills.verify(d['request_metadata']['selected_skills'])
        receipt=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()
        if not receipt:raise SafeError('SOURCE_CHANGED',409)
        built=self.context.replay_context(c,json.loads(receipt[0]));row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(d['source_message_id'],)).fetchone()
        if not row:raise SafeError('SOURCE_CHANGED',409)
        snapshot=d.get('deep_snapshot')
        if snapshot:
            fresh=self.deep.snapshot(c,d['conversation_id'],built['receipt'])
            if digest(encode(fresh).encode())!=d['request_metadata']['map_snapshot_hash']:raise SafeError('MAP_CHANGED',409)
        provider=self.provider_for(conv.mode)
        metadata=provider.metadata() if provider else {}
        if metadata.get('route')!=d['request_metadata']['provider_route'] or metadata.get('model')!=d['request_metadata']['provider_model'] or metadata.get('effort','low')!=d['request_metadata']['provider_effort'] or metadata.get('profile','M7C_COMPAT_LOW')!=d['request_metadata']['provider_profile']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
        if d.get('private_context'):
            from .local_private_context import approved_private_payload,exact_context_hash
            payload,bindings,aliases=approved_private_payload(self,c,conv,Message.model_validate_json(row[0]),built['receipt'],built['context'],d['purpose'],snapshot,d['private_context'])
            context_hash=exact_context_hash(payload)
        else:
            payload,bindings,aliases=self.assemble(c,conv,Message.model_validate_json(row[0]),built['receipt'],built['context'],d['purpose'],snapshot)
            context_hash=digest(encode(built['context']).encode())
        if digest(encode(payload).encode())!=d['request_hash'] or context_hash!=d['request_metadata']['context_hash']:raise SafeError('CONTEXT_CHANGED',409)
        return payload
    def persist(self,c,d):
        d['updated_at']=now();c.execute('UPDATE conversation_inferences SET state=?,revision=?,payload=? WHERE id=?',(d['state'],d['revision'],encode(d),d['id']))
    def run(self,id):
        cancel=self.events.setdefault(id,threading.Event());started=time.monotonic();deadline=started+self.timeout
        result_metadata=None;attempt=None
        try:
            with self.store.transaction() as c:
                d=self.row(c,id)
                if d['state']!='QUEUED':return
                payload=self.request_for(c,d);d['state']='RUNNING';d['revision']+=1;d['attempt']+=1;self.persist(c,d)
                attempt=d['attempt']
            # Provider deltas never enter a cache, API or DOM. The final object is
            # the only review input, and is serialized once before the release decision.
            result=self.provider_for(payload['mode']).execute(payload,ConversationCandidate.model_json_schema(),cancel,deadline,None)
            if time.monotonic()>=deadline:raise SafeError('PROVIDER_TIMEOUT')
            if result.get('route')!=d['request_metadata']['provider_route'] or result.get('model')!=d['request_metadata']['provider_model']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
            if result.get('effort','low')!=d['request_metadata']['provider_effort'] or result.get('profile','M7C_COMPAT_LOW')!=d['request_metadata']['provider_profile']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
            result_metadata=safe_result_metadata(result)
            candidate=ConversationCandidate.model_validate_json(result['text'])
            if candidate.working_map and d['request_metadata']['mode']!='DEEP':raise SafeError('FREE_MAP_CANDIDATE_DENIED')
            if any(s not in payload['source_refs_allowed'] for s in candidate.source_refs):raise SafeError('MODEL_SOURCE_OUT_OF_SCOPE')
            if candidate.goal_suggestion is not None and d['purpose']!='GOAL_PROPOSAL':raise SafeError('UNREQUESTED_GOAL_CANDIDATE')
            if (candidate.closure is not None)!=(d['purpose']=='CLOSURE'):raise SafeError('CLOSURE_SCHEMA_REQUIRED')
            if main_question_count(candidate.assistant_text,payload)>1:raise SafeError('MAIN_QUESTION_LIMIT')
            verify_address_form(candidate.assistant_text,payload)
            candidate_json=encode(candidate.model_dump(mode='json'))
            with self.store.transaction() as c:
                fresh=self.row(c,id)
                if cancel.is_set() or fresh['state']!='RUNNING' or fresh['attempt']!=attempt:return
                self.request_for(c,fresh)
                fresh['validation_started']=True;fresh['revision']+=1;self.persist(c,fresh)
            decision,review_input=self.release_policy.evaluate(payload,candidate_json,d,deadline,cancel)
            with self.lock,(self.private_gate.lock if self.private_gate else nullcontext()),self.store.transaction() as c:
                d=self.row(c,id)
                if d['attempt']!=attempt:return
                if cancel.is_set() or d['state']!='RUNNING':
                    if result_metadata:d['provider_result']=result_metadata;d['revision']+=1;self.persist(c,d)
                    return
                self.request_for(c,d)
                if time.monotonic()>=deadline:raise SafeError('CONTENT_DECISION_TIMEOUT')
                self.release_policy.verify(decision,review_input)
                if candidate_json!=encode(candidate.model_dump(mode='json')):raise SafeError('CONTENT_DECISION_BINDING_CHANGED')
                if candidate.working_map:
                    rr=json.loads(c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()[0])
                    refs={r['id']:r for r in rr['sources']}
                    if d.get('private_context'):refs.update({r['id']:r for r in d['private_context']['journal_refs']})
                    inverse={alias:refs[sid] for sid,alias in d['aliases'].items()}
                    self.deep.ingest(c,d['conversation_id'],candidate.working_map,inverse,dict(d['request_metadata'],request_hash=d['request_hash']))
                conv=self.conversations.row(c,d['conversation_id']);seq=c.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM conversation_messages WHERE conversation_id=?',(d['conversation_id'],)).fetchone()[0]
                message=Message(schema_version=1,id=uuid5(NAMESPACE,id+':assistant'),conversation_id=conv.id,role='ASSISTANT',raw_text=candidate.assistant_text,created_utc=now(),revision=1,provenance='MODEL_GENERATED',source_reference=None,source_message_id=UUID(d['source_message_id']),synthetic=self.conversations.synthetic_demo,privacy_class='PRIVATE_PERSONAL',inference_reference={'job_id':id,'request_hash':d['request_hash'],'provider_route':result['route'],'model':result['model'],'response_hash':digest(encode(candidate.model_dump(mode='json')).encode())})
                c.execute('INSERT INTO conversation_messages VALUES(?,?,?,?)',(str(message.id),d['conversation_id'],seq,encode(message.model_dump(mode='json'))));conv.revision+=1;conv.updated_utc=now();c.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',(conv.revision,encode(conv.model_dump(mode='json')),conv.updated_utc,d['conversation_id']))
                self.release_policy.verify(decision,review_input)
                if cancel.is_set():raise SafeError('CANCELLED')
                d.pop('content_decision_metadata',None)
                d['candidate']=json.loads(candidate_json);d['release_receipt']=self.release_policy.receipt(decision);d['provider_result']=result_metadata;d['state']='COMPLETED';d['revision']+=1;self.persist(c,d)
        except Exception as exc:
            error=exc.code if isinstance(exc,SafeError) and isinstance(exc.code,str) and exc.code in SAFE_FAILURE_CODES else 'MODEL_OUTPUT_INVALID' if isinstance(exc,ValueError) and not isinstance(exc,SafeError) else 'PROVIDER_FAILED'
            try:
                with self.store.transaction() as c:
                    row=c.execute('SELECT 1 FROM conversation_inferences WHERE id=?',(id,)).fetchone()
                    if row:
                        d=self.row(c,id)
                        if attempt is not None and d['attempt']!=attempt:return
                        if isinstance(exc,ReleaseRejected):
                            d['content_decision_metadata']={k:getattr(exc.decision,k) for k in ('verdict','reason','policy_hash','candidate_hash')}
                        if result_metadata:d['provider_result']=result_metadata
                        elif getattr(exc,'inference_attempt_id',None):
                            metadata=safe_result_metadata({'attempt_id':exc.inference_attempt_id})
                            if getattr(exc,'provider_failure',None):metadata['provider_failure']=safe_provider_failure(exc.provider_failure)
                            d['provider_result']=metadata
                        if d['state'] in {'QUEUED','RUNNING'}:d['state']='CANCELLED' if cancel.is_set() else 'FAILED';d['error']=error;d['candidate']=None;d['release_receipt']=None;d['revision']+=1;self.persist(c,d)
                        elif result_metadata or getattr(exc,'inference_attempt_id',None):d['revision']+=1;self.persist(c,d)
            except Exception:
                # A failed error-write must not print the original rejected JSON
                # through Python's chained worker traceback. No text is cached here.
                self.failure_notices[id]=True
        finally:self.previews.pop(id,None)
    def action(self,conversation_id,id,body:InferenceAction):
        fingerprint=digest(encode({'id':str(id),'body':body.model_dump(mode='json')}).encode());op=str(body.operation_id);retry=False
        with self.lock,self.store.transaction() as c:
            d=self.row(c,id,conversation_id);old=c.execute('SELECT * FROM inference_actions WHERE operation_id=?',(op,)).fetchone()
            if old:
                if old['job_id']!=str(id) or old['fingerprint']!=fingerprint:raise SafeError('OPERATION_REUSE',409)
                return self.public(d)
            if d['revision']!=body.base_revision:raise SafeError('REVISION_CONFLICT',409)
            if body.action=='cancel':
                if d['state'] not in {'QUEUED','RUNNING'}:raise SafeError('INFERENCE_TRANSITION_INVALID',409)
                self.events.setdefault(str(id),threading.Event()).set();d['state']='CANCELLED';d['error']='CANCELLED'
            else:
                if d['state'] not in {'FAILED','CANCELLED'}:raise SafeError('INFERENCE_TRANSITION_INVALID',409)
                if str(id) in self.workers and self.workers[str(id)].is_alive():raise SafeError('INFERENCE_STOPPING',409)
                self.request_for(c,d)
                if 'release_policy_hash' not in d:d['release_policy_hash']=self.release_policy.identity()
                d.pop('content_decision_metadata',None)
                self.failure_notices.pop(str(id),None)
                d['state']='QUEUED';d['error']=None;d['candidate']=None;d['release_receipt']=None;d['validation_started']=False;retry=True
            d['revision']+=1;self.persist(c,d);c.execute('INSERT INTO inference_actions VALUES(?,?,?,?)',(op,str(id),body.action,fingerprint))
        if retry:self.events[str(id)]=threading.Event();self.launch(str(id))
        return self.get(conversation_id,id)
