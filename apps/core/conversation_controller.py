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

NAMESPACE=UUID('70000000-0000-4000-8000-000000000004')
RUNTIME_TABLES=(
 'CREATE TABLE IF NOT EXISTS conversation_inferences(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,operation_id TEXT UNIQUE NOT NULL,fingerprint TEXT NOT NULL,state TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL)',
 'CREATE UNIQUE INDEX IF NOT EXISTS conversation_one_foreground ON conversation_inferences(conversation_id) WHERE state IN ("QUEUED","RUNNING")',
 'CREATE TABLE IF NOT EXISTS inference_actions(operation_id TEXT PRIMARY KEY,job_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT NOT NULL)',
)

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
            ConversationRequest.model_validate(dict(d['request_metadata'],payload={
                'mode':d['request_metadata']['mode'],'purpose':d['purpose'],'synthetic':True,'language':'uk',
                'skills':[],'context':[],'current_message_ref':'s0','source_refs_allowed':['s0'],
                'goal_revision':None,'tool_permissions':[],'controller_frame_hash':'0'*64}))
            if not re.fullmatch('[0-9a-f]{64}',d['request_hash']):raise ValueError()
            if d['state']=='COMPLETED':ConversationCandidate.model_validate(d['candidate'])
    except (KeyError,ValueError,TypeError,ValidationError):raise SafeError('INFERENCE_INTEGRITY') from None

class ConversationController:
    def __init__(self,conversations,provider=None,skills=None,timeout=60):
        self.conversations=conversations;self.store=conversations.store;self.context=Reflection(conversations);self.deep=DeepSessions(conversations);self.provider=provider;self.skills=skills or ConversationSkills();self.timeout=timeout
        if not conversations.synthetic_demo:raise SafeError('M7C_SYNTHETIC_SCOPE_REQUIRED',403)
        self.lock=threading.RLock();self.events={};self.previews={};self.workers={}
        with self.store.transaction() as c:
            for sql in RUNTIME_TABLES:c.execute(sql)
            for sql in DEEP_TABLES:c.execute(sql)
            # A restarted server never resumes an old external request or assumes a partial result is final.
            c.execute('UPDATE conversation_inferences SET state="FAILED",revision=revision+1,payload=json_set(payload,"$.state","FAILED","$.error","PROCESS_INTERRUPTED","$.revision",revision+1) WHERE state IN ("QUEUED","RUNNING")')
    def status(self):
        metadata=self.provider.metadata() if self.provider else None
        return {'synthetic_demo':True,'mode':'LIVE_SYNTHETIC' if metadata and metadata.get('live') else 'OFFLINE_FIXTURE' if self.provider else 'OFF','responder':'LIVE_SYNTHETIC' if metadata and metadata.get('live') else 'OFFLINE_FIXTURE' if self.provider else 'OFF','live_provider_calls':bool(metadata and metadata.get('live')),'clinical_active':0,'real_private_data':False,'actual_asr':'SEPARATE_LOCAL_GATE','provider':metadata,'skills':self.skills.catalog(),'normal_user_mode':False}
    def row(self,c,id,conversation_id=None):
        r=c.execute('SELECT * FROM conversation_inferences WHERE id=?',(str(id),)).fetchone()
        if not r or conversation_id is not None and r['conversation_id']!=str(conversation_id):raise SafeError('INFERENCE_NOT_FOUND',404)
        d=json.loads(r['payload']);d.update(state=r['state'],revision=r['revision']);return d
    def public(self,d):
        return {k:d[k] for k in ('id','conversation_id','state','revision','purpose','error','created_at','updated_at','candidate','request_metadata','provider_result')}
    def get(self,conversation_id,id):
        with self.store.connect() as c:d=self.row(c,id,conversation_id)
        return dict(self.public(d),partial_candidate=self.previews.get(str(id)))
    def page(self,conversation_id):
        with self.store.connect() as c:
            c.execute('BEGIN')
            page=self.conversations.view(c,self.conversations.row(c,conversation_id))
            r=c.execute('SELECT id FROM conversation_inferences WHERE conversation_id=? ORDER BY json_extract(payload,"$.created_at") DESC LIMIT 1',(str(conversation_id),)).fetchone()
            job=self.public(self.row(c,r['id'],conversation_id)) if r else None
            if job:job['partial_candidate']=self.previews.get(job['id'])
        return dict(page,inference_job=job,responder=self.status()['responder'])
    def journal_point(self,c,conversation_id,body):
        self.conversations.row(c,conversation_id)
        row=c.execute('SELECT payload FROM conversation_messages WHERE id=? AND conversation_id=?',(str(body.message_id),str(conversation_id))).fetchone()
        if not row:raise SafeError('SOURCE_CHANGED',409)
        source=Message.model_validate_json(row[0])
        if source.role!='USER' or source.provenance!='USER_AUTHORED' or not source.synthetic:raise SafeError('USER_AUTHORED_SOURCE_REQUIRED',403)
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
    def assemble(self,c,conversation,user_message,receipt,parts,purpose,snapshot=None):
        if not user_message.synthetic or not conversation.synthetic:raise SafeError('REAL_PRIVATE_DATA_OFF',403)
        if receipt['confirmed_memory_refs']:raise SafeError('SYNTHETIC_MEMORY_SCOPE_UNVERIFIED',403)
        if conversation.mode=='DEEP':
            goal=self.context.row(c,conversation.goal_binding.id,conversation.goal_binding.revision)
            current=self.context.row(c,conversation.goal_binding.id)
            if not goal.synthetic:raise SafeError('REAL_PRIVATE_DATA_OFF',403)
            if current.state!='ACTIVE':raise SafeError('GOAL_NOT_ACTIVE',409)
        aliases={s['id']:'s'+str(i) for i,s in enumerate(receipt['sources'])}
        if str(user_message.id) not in aliases:raise SafeError('CURRENT_MESSAGE_NOT_IN_RECEIPT',409)
        for ref in receipt['sources']:
            row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
            if not row or not json.loads(row[0])['synthetic']:raise SafeError('REAL_PRIVATE_DATA_OFF',403)
        selected=self.skills.select(conversation.mode,purpose)
        payload={'mode':conversation.mode,'purpose':purpose,'synthetic':True,'language':'uk','skills':[{k:s[k] for k in ('skill_id','version','content_hash','instructions')} for s in selected],'context':[{'kind':p['kind'],'text':p['text'],'source_refs':[aliases[s['id']] for s in p['sources']]} for p in parts],'current_message_ref':aliases[str(user_message.id)],'source_refs_allowed':list(aliases.values()),'goal_revision':conversation.goal_binding.revision if conversation.goal_binding else None,'tool_permissions':[],'controller_frame_hash':digest(encode(json.loads((REPO/'skills/conversation/controller_frame.json').read_text())).encode())}
        if snapshot:
            payload['reflection_state']={'focus':snapshot['session']['focus'],'phase':snapshot['session']['phase'],'map_version':snapshot['map_version'],'items':[{'kind':i['kind'],'text':i['text'],'provenance':i['provenance'],'state':i['state'],'source_refs':[aliases[r['id']] for r in i['sources']]} for i in snapshot['items']],'prior_closures':[{'closure':i['closure'],'source_refs':[aliases[r['id']] for r in i['sources']]} for i in snapshot['prior_closures']]}
        payload=ProviderPayload.model_validate(payload).model_dump(mode='json')
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
            if before.mode=='FREE' and body.context_binding:raise SafeError('DEEP_MODE_REQUIRED',409)
            if before.mode=='DEEP':
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
            if self.provider is None:return dict(page,inference_job=None,responder='OFF')
            with self.store.connect() as c:conv=self.conversations.row(c,id)
            source_id=str(uuid5(__import__('apps.core.conversation',fromlist=['NAMESPACE']).NAMESPACE,op+':user'))
            snapshot=preview['snapshot'] if preview else None
            if conv.mode=='DEEP':
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
                user=Message.model_validate_json(c.execute('SELECT payload FROM conversation_messages WHERE id=?',(source_id,)).fetchone()[0]);payload,bindings,aliases=self.assemble(c,conv,user,built['receipt'],built['context'],body.purpose,snapshot)
            request_hash=digest(encode(payload).encode());job_id=str(uuid5(NAMESPACE,op+':job'));metadata=self.provider.metadata()
            context_hash=digest(encode(built['context']).encode())
            r=ConversationRequest(schema_version=1,request_id=UUID(job_id),mode=conv.mode,purpose=body.purpose,selected_skills=bindings,context_hash=context_hash,retrieval_receipt_id=UUID(built['receipt']['id']),provider_route=metadata['route'],provider_model=metadata['model'],provider_effort=metadata.get('effort','low'),provider_profile=metadata.get('profile','M7C_COMPAT_LOW'),selection_type=preview['selection']['type'] if preview else 'FREE_RECENT',selection_timezone=built['receipt']['timezone'],selected_window_start=built['receipt']['window_start'],selected_window_end=built['receipt']['window_end'],selected_receipt_id=UUID(preview['receipt_id']) if preview else None,selected_context_hash=preview['context_hash'] if preview else None,map_snapshot_hash=digest(encode(snapshot).encode()) if snapshot else None,consent_scope='M7D_OWNER_AUTHORIZED_ORIGINAL_SYNTHETIC_ONLY',synthetic=True,clinical_active=0,tools=[],timeout_seconds=self.timeout,input_byte_budget=48000,response_schema='M7C_CONVERSATION_CANDIDATE_V1',payload=payload)
            meta=r.model_dump(mode='json');meta.pop('payload')
            d={'id':job_id,'conversation_id':id,'purpose':body.purpose,'state':'QUEUED','revision':1,'error':None,'created_at':now(),'updated_at':now(),'candidate':None,'request_metadata':meta,'provider_result':None,'request_hash':request_hash,'source_message_id':source_id,'conversation_revision':conv.revision,'aliases':aliases,'attempt':0,'deep_snapshot':snapshot}
            with self.store.transaction() as c:c.execute('INSERT INTO conversation_inferences VALUES(?,?,?,?,?,?,?)',(job_id,id,op,fingerprint,'QUEUED',1,encode(d)))
            self.events[job_id]=threading.Event()
            if launch:self.launch(job_id)
            return self.page(id)
    def launch(self,id):
        t=threading.Thread(target=self.run,args=(str(id),),daemon=True);self.workers[str(id)]=t;t.start()
    def request_for(self,c,d):
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
        metadata=self.provider.metadata() if self.provider else {}
        if metadata.get('model')!=d['request_metadata']['provider_model'] or metadata.get('effort','low')!=d['request_metadata']['provider_effort'] or metadata.get('profile','M7C_COMPAT_LOW')!=d['request_metadata']['provider_profile']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
        payload,bindings,aliases=self.assemble(c,conv,Message.model_validate_json(row[0]),built['receipt'],built['context'],d['purpose'],snapshot)
        if digest(encode(payload).encode())!=d['request_hash'] or digest(encode(built['context']).encode())!=d['request_metadata']['context_hash']:raise SafeError('CONTEXT_CHANGED',409)
        return payload
    def persist(self,c,d):
        d['updated_at']=now();c.execute('UPDATE conversation_inferences SET state=?,revision=?,payload=? WHERE id=?',(d['state'],d['revision'],encode(d),d['id']))
    def run(self,id):
        cancel=self.events.setdefault(id,threading.Event());started=time.monotonic()
        result_metadata=None
        try:
            with self.store.transaction() as c:
                d=self.row(c,id)
                if d['state']!='QUEUED':return
                payload=self.request_for(c,d);d['state']='RUNNING';d['revision']+=1;d['attempt']+=1;self.persist(c,d)
            def preview(raw):
                # Never log/store partial JSON/reasoning; text remains an explicitly ephemeral candidate.
                m=re.search(r'"assistant_text"\s*:\s*"((?:[^"\\]|\\.)*)',raw)
                if m:
                    try:self.previews[id]=json.loads('"'+m.group(1)+'"')[:4000]
                    except ValueError:pass
            result=self.provider.execute(payload,ConversationCandidate.model_json_schema(),cancel,started+self.timeout,preview)
            if result.get('route')!=d['request_metadata']['provider_route'] or result.get('model')!=d['request_metadata']['provider_model']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
            result_metadata={k:result[k] for k in ('route','model','effort','profile','elapsed_ms','usage','auth_type','streaming_actual','frame_hash','attempt_id') if k in result}
            if result.get('effort','low')!=d['request_metadata']['provider_effort'] or result.get('profile','M7C_COMPAT_LOW')!=d['request_metadata']['provider_profile']:raise SafeError('PROVIDER_BINDING_CHANGED',409)
            candidate=ConversationCandidate.model_validate_json(result['text'])
            if candidate.working_map and d['request_metadata']['mode']!='DEEP':raise SafeError('FREE_MAP_CANDIDATE_DENIED')
            if any(s not in payload['source_refs_allowed'] for s in candidate.source_refs):raise SafeError('MODEL_SOURCE_OUT_OF_SCOPE')
            if candidate.goal_suggestion is not None and d['purpose']!='GOAL_PROPOSAL':raise SafeError('UNREQUESTED_GOAL_CANDIDATE')
            if (candidate.closure is not None)!=(d['purpose']=='CLOSURE'):raise SafeError('CLOSURE_SCHEMA_REQUIRED')
            if candidate.assistant_text.count('?')>1:raise SafeError('MAIN_QUESTION_LIMIT')
            with self.store.transaction() as c:
                d=self.row(c,id)
                if cancel.is_set() or d['state']!='RUNNING':
                    if result_metadata:d['provider_result']=result_metadata;d['revision']+=1;self.persist(c,d)
                    return
                self.request_for(c,d)
                if candidate.working_map:
                    rr=json.loads(c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()[0])
                    refs={r['id']:r for r in rr['sources']};inverse={alias:refs[sid] for sid,alias in d['aliases'].items()}
                    self.deep.ingest(c,d['conversation_id'],candidate.working_map,inverse,dict(d['request_metadata'],request_hash=d['request_hash']))
                conv=self.conversations.row(c,d['conversation_id']);seq=c.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM conversation_messages WHERE conversation_id=?',(d['conversation_id'],)).fetchone()[0]
                message=Message(schema_version=1,id=uuid5(NAMESPACE,id+':assistant'),conversation_id=conv.id,role='ASSISTANT',raw_text=candidate.assistant_text,created_utc=now(),revision=1,provenance='MODEL_GENERATED',source_reference=None,source_message_id=UUID(d['source_message_id']),synthetic=True,privacy_class='PRIVATE_PERSONAL',inference_reference={'job_id':id,'request_hash':d['request_hash'],'provider_route':result['route'],'model':result['model'],'response_hash':digest(encode(candidate.model_dump(mode='json')).encode())})
                c.execute('INSERT INTO conversation_messages VALUES(?,?,?,?)',(str(message.id),d['conversation_id'],seq,encode(message.model_dump(mode='json'))));conv.revision+=1;conv.updated_utc=now();c.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',(conv.revision,encode(conv.model_dump(mode='json')),conv.updated_utc,d['conversation_id']))
                d['candidate']=candidate.model_dump(mode='json');d['provider_result']=result_metadata;d['state']='COMPLETED';d['revision']+=1;self.persist(c,d)
        except Exception as exc:
            error=exc.code if isinstance(exc,SafeError) else 'MODEL_OUTPUT_INVALID' if isinstance(exc,ValueError) else 'PROVIDER_FAILED'
            with self.store.transaction() as c:
                row=c.execute('SELECT 1 FROM conversation_inferences WHERE id=?',(id,)).fetchone()
                if row:
                    d=self.row(c,id)
                    if result_metadata:d['provider_result']=result_metadata
                    elif getattr(exc,'inference_attempt_id',None):d['provider_result']={'attempt_id':exc.inference_attempt_id,**({'provider_failure':exc.provider_failure} if getattr(exc,'provider_failure',None) else {})}
                    if d['state'] in {'QUEUED','RUNNING'}:d['state']='CANCELLED' if cancel.is_set() else 'FAILED';d['error']=error;d['revision']+=1;self.persist(c,d)
                    elif result_metadata or getattr(exc,'inference_attempt_id',None):d['revision']+=1;self.persist(c,d)
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
                self.request_for(c,d);d['state']='QUEUED';d['error']=None;retry=True
            d['revision']+=1;self.persist(c,d);c.execute('INSERT INTO inference_actions VALUES(?,?,?,?)',(op,str(id),body.action,fingerprint))
        if retry:self.events[str(id)]=threading.Event();self.launch(str(id))
        return self.get(conversation_id,id)
