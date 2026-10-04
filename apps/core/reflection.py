"""One deterministic goal/context controller. Raw messages stay authoritative and private."""
import json,re
from uuid import uuid4,uuid5,UUID
from .storage import SafeError,encode,digest,now
from .logical_day import logical_day,day_window,scope_key
from .conversation_contracts import Conversation,Message
from .reflection_contracts import ReflectionGoal,GoalCreate,GoalChange,ContextRequest,Expansion,MessageEdit,SKILLS,DerivedDigest,RetrievalReceipt

NAMESPACE=UUID('70000000-0000-4000-8000-000000000003')
REFLECTION_TABLES=(
 'CREATE TABLE IF NOT EXISTS reflection_goals(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS reflection_goal_revisions(goal_id TEXT NOT NULL REFERENCES reflection_goals(id),revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(goal_id,revision))',
 'CREATE TABLE IF NOT EXISTS reflection_receipts(operation_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS conversation_message_revisions(message_id TEXT NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(message_id,revision))',
 'CREATE VIRTUAL TABLE IF NOT EXISTS conversation_fts USING fts5(message_id UNINDEXED,conversation_id UNINDEXED,raw_text,tokenize="unicode61")',
 'CREATE TABLE IF NOT EXISTS conversation_digests(id TEXT PRIMARY KEY,kind TEXT NOT NULL,scope_key TEXT NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,UNIQUE(kind,scope_key,version))',
 'CREATE TABLE IF NOT EXISTS retrieval_receipts(id TEXT PRIMARY KEY,operation_id TEXT UNIQUE NOT NULL,fingerprint TEXT NOT NULL,payload TEXT NOT NULL)',
)

def reflection_triggers(c):
    c.execute('''CREATE TRIGGER IF NOT EXISTS conversation_index_insert AFTER INSERT ON conversation_messages BEGIN
    INSERT INTO conversation_fts(message_id,conversation_id,raw_text) VALUES(NEW.id,NEW.conversation_id,json_extract(NEW.payload,'$.raw_text')); END''')
    for action in ('UPDATE','DELETE'):
        suffix=('INSERT INTO conversation_fts(message_id,conversation_id,raw_text) VALUES(NEW.id,NEW.conversation_id,json_extract(NEW.payload,"$.raw_text"));' if action=='UPDATE' else '')
        c.execute(f'''CREATE TRIGGER IF NOT EXISTS conversation_index_{action.lower()} AFTER {action} ON conversation_messages BEGIN
        DELETE FROM conversation_fts WHERE message_id=OLD.id;
        UPDATE conversation_digests SET status='STALE',payload=json_set(payload,'$.status','STALE','$.text',NULL) WHERE EXISTS
        (SELECT 1 FROM json_each(json_extract(payload,'$.sources')) WHERE json_extract(value,'$.id')=OLD.id);
        {suffix} END''')
    c.execute('''CREATE TRIGGER IF NOT EXISTS goal_digest_stale AFTER UPDATE ON reflection_goals BEGIN
      UPDATE conversation_digests SET status='STALE',payload=json_set(payload,'$.status','STALE','$.text',NULL)
      WHERE kind='GOAL' AND json_extract(payload,'$.goal.id')=OLD.id; END''')
    # Repair legacy multiple-current scopes atomically before enforcing N01.
    c.execute('''UPDATE conversation_digests SET status='STALE',payload=json_set(payload,'$.status','STALE','$.text',NULL)
      WHERE status='CURRENT' AND version < (SELECT MAX(newer.version) FROM conversation_digests newer
      WHERE newer.kind=conversation_digests.kind AND newer.scope_key=conversation_digests.scope_key AND newer.status='CURRENT')''')
    # UTC-sliced legacy daily identities require explicit rebuild, never silent local reinterpretation.
    c.execute('''UPDATE conversation_digests SET status='STALE',payload=json_set(payload,'$.status','STALE','$.text',NULL)
      WHERE kind='DAILY' AND status='CURRENT' AND COALESCE(json_extract(payload,'$.day_identity_version'),'LEGACY_UTC_V0')!='IANA_LOCAL_V1' ''')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS digest_one_current ON conversation_digests(kind,scope_key) WHERE status="CURRENT"')
    # Idempotent index reconstruction for existing synthetic schema8 rows.
    c.execute('INSERT INTO conversation_fts(message_id,conversation_id,raw_text) SELECT id,conversation_id,json_extract(payload,"$.raw_text") FROM conversation_messages WHERE id NOT IN (SELECT message_id FROM conversation_fts)')


def check_reflection(c,enforce_current_unique=True):
    try:
        for r in c.execute('SELECT * FROM reflection_goals'):
            g=ReflectionGoal.model_validate_json(r['payload'])
            if str(g.id)!=r['id'] or g.revision!=r['revision']:raise ValueError()
        for r in c.execute('SELECT * FROM reflection_goal_revisions'):
            g=ReflectionGoal.model_validate_json(r['payload'])
            if str(g.id)!=r['goal_id'] or g.revision!=r['revision']:raise ValueError()
        for r in c.execute('SELECT * FROM conversation_digests'):
            d=DerivedDigest.model_validate_json(r['payload'])
            if str(d.id)!=r['id'] or d.version!=r['version'] or d.kind!=r['kind'] or d.status!=r['status'] or d.scope_key!=r['scope_key']:raise ValueError()
            if d.status=='STALE' and d.text is not None:raise ValueError()
            if d.status=='CURRENT':
                for ref in d.sources:
                    source=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(str(ref.id),)).fetchone()
                    if not source or json.loads(source[0])['revision']!=ref.revision:raise ValueError()
        if enforce_current_unique and c.execute('SELECT 1 FROM conversation_digests WHERE status="CURRENT" GROUP BY kind,scope_key HAVING count(*)>1').fetchone():raise ValueError()
        for r in c.execute('SELECT * FROM retrieval_receipts'):
            receipt=RetrievalReceipt.model_validate_json(r['payload'])
            if str(receipt.id)!=r['id'] or receipt.used_bytes_estimate>receipt.byte_budget or receipt.used_tokens_upper_bound>receipt.token_budget:raise ValueError()
        for r in c.execute('SELECT * FROM conversation_message_revisions'):
            m=Message.model_validate_json(r['payload'])
            if str(m.id)!=r['message_id'] or m.revision!=r['revision']:raise ValueError()
        mismatch=c.execute('SELECT count(*) FROM conversation_fts f LEFT JOIN conversation_messages m ON m.id=f.message_id WHERE m.id IS NULL OR f.conversation_id!=m.conversation_id OR f.raw_text!=json_extract(m.payload,"$.raw_text")').fetchone()[0]
        if mismatch or c.execute('SELECT count(*) FROM conversation_fts').fetchone()[0]!=c.execute('SELECT count(*) FROM conversation_messages').fetchone()[0]:raise ValueError()
    except (ValueError,TypeError):raise SafeError('GOAL_INTEGRITY') from None

class Reflection:
    def __init__(self,conversations):self.conversations=conversations;self.store=conversations.store
    def row(self,c,id,revision=None):
        r=c.execute('SELECT payload FROM reflection_goals WHERE id=?',(str(id),)).fetchone()
        if not r:raise SafeError('GOAL_NOT_FOUND',404)
        g=ReflectionGoal.model_validate_json(r['payload'])
        if revision is not None and g.revision!=revision:
            old=c.execute('SELECT payload FROM reflection_goal_revisions WHERE goal_id=? AND revision=?',(str(id),revision)).fetchone()
            if not old:raise SafeError('GOAL_REVISION_NOT_FOUND',404)
            g=ReflectionGoal.model_validate_json(old['payload'])
        return g
    def list(self):
        with self.store.connect() as c:return {'items':[ReflectionGoal.model_validate_json(r[0]).model_dump(mode='json') for r in c.execute('SELECT payload FROM reflection_goals ORDER BY json_extract(payload,"$.updated_at") DESC LIMIT 50')],'skills':SKILLS}
    def get(self,id):
        with self.store.connect() as c:
            g=self.row(c,id);history=[json.loads(r[0]) for r in c.execute('SELECT payload FROM reflection_goal_revisions WHERE goal_id=? ORDER BY revision',(str(id),))]
            return {'goal':g.model_dump(mode='json'),'history':history}
    def create(self,b:GoalCreate):
        op=str(b.operation_id);id=str(uuid5(NAMESPACE,op));fp=digest(encode(b.model_dump(mode='json')).encode())
        with self.store.transaction() as c:
            r=c.execute('SELECT * FROM reflection_receipts WHERE operation_id=?',(op,)).fetchone()
            if r:
                if r['fingerprint']!=fp or r['action']!='create':raise SafeError('OPERATION_REUSE',409)
                return self.row(c,id).model_dump(mode='json')
            time=now();g=ReflectionGoal(id=UUID(id),text=b.text,state='ACTIVE',revision=1,user_agreed=True,created_at=time,updated_at=time,completed_at=None,synthetic=self.conversations.synthetic_demo,privacy_class='PRIVATE_PERSONAL')
            c.execute('INSERT INTO reflection_goals VALUES(?,?,?)',(id,1,encode(g.model_dump(mode='json'))));c.execute('INSERT INTO reflection_receipts VALUES(?,?,?,?)',(op,id,'create',fp))
        return g.model_dump(mode='json')
    def change(self,id,b:GoalChange):
        id=str(id);op=str(b.operation_id);fp=digest(encode({'id':id,'body':b.model_dump(mode='json')}).encode())
        if b.text is None and b.state is None:raise SafeError('GOAL_CHANGE_REQUIRED')
        with self.store.transaction() as c:
            g=self.row(c,id);r=c.execute('SELECT * FROM reflection_receipts WHERE operation_id=?',(op,)).fetchone()
            if r:
                if r['entity_id']!=id or r['fingerprint']!=fp or r['action']!='change':raise SafeError('OPERATION_REUSE',409)
                return g.model_dump(mode='json')
            if g.revision!=b.base_revision:raise SafeError('REVISION_CONFLICT',409)
            c.execute('INSERT INTO reflection_goal_revisions VALUES(?,?,?)',(id,g.revision,encode(g.model_dump(mode='json'))))
            if b.text is not None:g.text=b.text
            if b.state is not None:g.state=b.state
            g.completed_at=(g.completed_at or now()) if g.state=='COMPLETED' else None;g.revision+=1;g.updated_at=now()
            c.execute('UPDATE reflection_goals SET revision=?,payload=? WHERE id=?',(g.revision,encode(g.model_dump(mode='json')),id));c.execute('INSERT INTO reflection_receipts VALUES(?,?,?,?)',(op,id,'change',fp))
        return g.model_dump(mode='json')
    def edit_message(self,id,message_id,b:MessageEdit):
        id=str(id);mid=str(message_id);op=str(b.operation_id);fp=digest(encode({'id':id,'message':mid,'body':b.model_dump(mode='json')}).encode())
        with self.store.transaction() as c:
            conv=self.conversations.row(c,id);row=c.execute('SELECT * FROM conversation_messages WHERE id=? AND conversation_id=?',(mid,id)).fetchone()
            if not row:raise SafeError('MESSAGE_NOT_FOUND',404)
            m=Message.model_validate_json(row['payload']);receipt=c.execute('SELECT * FROM reflection_receipts WHERE operation_id=?',(op,)).fetchone()
            if receipt:
                if receipt['fingerprint']!=fp or receipt['entity_id']!=mid or receipt['action']!='message_edit':raise SafeError('OPERATION_REUSE',409)
                return self.conversations.view(c,conv)
            if m.role!='USER':raise SafeError('ONLY_USER_MESSAGE_EDITABLE',409)
            if conv.revision!=b.base_conversation_revision or m.revision!=b.base_message_revision:raise SafeError('REVISION_CONFLICT',409)
            c.execute('INSERT INTO conversation_message_revisions VALUES(?,?,?)',(mid,m.revision,encode(m.model_dump(mode='json'))));m.raw_text=b.text;m.revision+=1;m.source_reference=None
            c.execute('UPDATE conversation_messages SET payload=? WHERE id=?',(encode(m.model_dump(mode='json')),mid));conv.revision+=1;conv.updated_utc=now();c.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',(conv.revision,encode(conv.model_dump(mode='json')),conv.updated_utc,id))
            c.execute('INSERT INTO reflection_receipts VALUES(?,?,?,?)',(op,mid,'message_edit',fp));result=self.conversations.view(c,conv)
        return result
    def digest(self,c,kind,scope,refs,start,end,goal=None,timezone=None,local_date=None):
        if not self.conversations.synthetic_demo:raise SafeError('DIGEST_GENERATOR_OFF',409)
        current=c.execute('SELECT payload FROM conversation_digests WHERE kind=? AND scope_key=? AND status="CURRENT" ORDER BY version DESC LIMIT 1',(kind,scope)).fetchone()
        if current:
            d=json.loads(current[0])
            if d['sources']==refs and d['goal']==goal and d['window_start']==start and d['window_end']==end and d.get('timezone')==timezone:return d
        version=c.execute('SELECT COALESCE(MAX(version),0)+1 FROM conversation_digests WHERE kind=? AND scope_key=?',(kind,scope)).fetchone()[0]
        excerpts=[]
        for ref in refs[:12]:
            m=json.loads(c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()[0]);excerpts.append(m['raw_text'][:180])
        d={'id':str(uuid4()),'kind':kind,'scope_key':scope,'version':version,'status':'CURRENT','provenance':'MODEL_DERIVED','synthetic':True,'generator_version':'SYNTHETIC_EXCERPT_V1','generator_kind':'DETERMINISTIC_FIXTURE_NOT_LLM','goal':goal,'sources':refs,'window_start':start,'window_end':end,'text':'\n'.join(excerpts),'created_at':now()}
        d.update(timezone=timezone,logical_local_date=local_date,day_identity_version='IANA_LOCAL_V1' if kind=='DAILY' else 'LEGACY_UTC_V0')
        DerivedDigest.model_validate(d)
        c.execute('UPDATE conversation_digests SET status="STALE",payload=json_set(payload,"$.status","STALE","$.text",NULL) WHERE kind=? AND scope_key=? AND status="CURRENT"',(kind,scope))
        c.execute('INSERT INTO conversation_digests VALUES(?,?,?,?,?,?)',(d['id'],kind,scope,version,encode(d),'CURRENT'));return d
    def valid_digest(self,c,d):
        if d['status']!='CURRENT' or d['text'] is None:return False
        for s in d['sources']:
            row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(s['id'],)).fetchone()
            if not row or json.loads(row[0])['revision']!=s['revision']:return False
        return True
    def build(self,b:ContextRequest):
        # Byte token upper bound: one token per UTF8 byte, stricter than an unverified model tokenizer.
        op=str(b.operation_id);fp=digest(encode(b.model_dump(mode='json')).encode())
        with self.store.transaction() as c:
            prior=c.execute('SELECT payload,fingerprint FROM retrieval_receipts WHERE operation_id=?',(op,)).fetchone()
            if prior:
                if prior['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                receipt=json.loads(prior['payload']);return self.replay_context(c,receipt)
            goal=self.row(c,b.goal.id,b.goal.revision);conv=self.conversations.row(c,b.conversation_id)
            if conv.mode!='DEEP' or conv.goal_binding is None or conv.goal_binding.id!=goal.id or conv.goal_binding.revision!=goal.revision:raise SafeError('DEEP_GOAL_BINDING_MISMATCH',409)
            start=b.window_start or goal.created_at;end=b.window_end or now()
            if start>end:raise SafeError('CONTEXT_WINDOW_INVALID')
            parts=[];selected={};digest_versions=[];used=2
            def add(kind,text,refs=None,version=None,artifact_id=None,memory_ref=None):
                nonlocal used
                refs=refs or []
                if any(s['id'] not in selected for s in refs) and len(set(selected)|{s['id'] for s in refs})>b.max_sources:return False
                part={'kind':kind,'text':text,'sources':refs,'digest_version':version,'artifact_id':artifact_id,'memory_ref':memory_ref}
                size=len(encode(part).encode('utf-8'))+2
                if used+size>min(b.token_budget,b.byte_budget):return False
                parts.append(part);used+=size
                for s in refs:selected[s['id']]=s
                return True
            if not add('GOAL_REVISION',goal.text):raise SafeError('CONTEXT_BUDGET_TOO_SMALL',409)
            current=c.execute('SELECT payload FROM conversation_messages WHERE conversation_id=? ORDER BY sequence DESC LIMIT 6',(str(conv.id),)).fetchall()
            for row in reversed(current):
                m=json.loads(row[0])
                if b.selection_type!='LEGACY' and not start<=m['created_utc']<=end:continue
                add('CURRENT_TURN',m['raw_text'],[{'id':m['id'],'revision':m['revision']}])
            rows=c.execute('SELECT m.payload FROM conversation_messages m JOIN conversations v ON v.id=m.conversation_id WHERE json_extract(v.payload,"$.mode")="FREE" AND json_extract(m.payload,"$.created_utc")>=? AND json_extract(m.payload,"$.created_utc")<=? ORDER BY json_extract(m.payload,"$.created_utc") DESC LIMIT 50',(start,end)).fetchall()
            refs=[{'id':(m:=json.loads(r[0]))['id'],'revision':m['revision']} for r in rows]
            goalref={'id':str(goal.id),'revision':goal.revision}
            if b.prepare_synthetic_digests:
                self.digest(c,'GOAL',str(goal.id)+':'+str(goal.revision),refs[:12],start,end,goalref)
                byday={}
                for r in rows:
                    m=json.loads(r[0]);byday.setdefault(logical_day(m['created_utc'],b.timezone),[]).append({'id':m['id'],'revision':m['revision']})
                for day,dr in list(byday.items())[:3]:
                    ds,de=day_window(day,b.timezone)
                    self.digest(c,'DAILY',scope_key(day,b.timezone),dr[:12],max(start,ds),min(end,de),None,b.timezone,day)
            for kind in ('GOAL','DAILY'):
                ds=c.execute('SELECT payload FROM conversation_digests WHERE kind=? AND status="CURRENT" ORDER BY version DESC LIMIT 10',(kind,)).fetchall()
                for row in ds:
                    d=json.loads(row[0])
                    if (kind=='GOAL' and d['goal']!=goalref) or (kind=='DAILY' and d.get('timezone')!=b.timezone) or d['window_start']<start or d['window_end']>end or not self.valid_digest(c,d):continue
                    if add(kind+'_DIGEST',d['text'],d['sources'],d['version'],d['id']):digest_versions.append({'id':d['id'],'version':d['version'],'kind':kind})
            query=b.query or goal.text;terms=re.findall(r'\w{2,40}',query.lower())[:8]
            match=' OR '.join('"'+t.replace('"','""')+'"' for t in terms)
            candidates=[]
            if match:
                candidates=c.execute('SELECT m.payload FROM conversation_fts f JOIN conversation_messages m ON m.id=f.message_id JOIN conversations v ON v.id=m.conversation_id WHERE conversation_fts MATCH ? AND json_extract(v.payload,"$.mode")="FREE" AND json_extract(m.payload,"$.created_utc")>=? AND json_extract(m.payload,"$.created_utc")<=? ORDER BY rank LIMIT 20',(match,start,end)).fetchall()
            for r in candidates:
                m=json.loads(r[0]);ref={'id':m['id'],'revision':m['revision']}
                if m['id'] not in selected:add('FTS_RAW',m['raw_text'],[ref])
            if not match:
                for r in rows:
                    m=json.loads(r[0]);ref={'id':m['id'],'revision':m['revision']}
                    if m['id'] not in selected:add('FILTER_RAW',m['raw_text'],[ref])
            if b.confirmed_memories:
                if b.memory_scope!='USER_CONFIRMED_EXPLICIT':raise SafeError('MEMORY_SCOPE_REQUIRED',409)
                for ref in b.confirmed_memories:
                    row=c.execute('SELECT * FROM memories WHERE id=?',(str(ref.id),)).fetchone()
                    if not row or row['status']!='USER_CONFIRMED' or row['revision']!=ref.revision:raise SafeError('CONFIRMED_MEMORY_BINDING_INVALID',409)
                    add('CONFIRMED_MEMORY',row['content'],memory_ref=ref.model_dump(mode='json'))
            receipt={'id':str(uuid4()),'goal':goalref,'conversation_id':str(conv.id),'timezone':b.timezone,'window_start':start,'window_end':end,'sources':list(selected.values()),'digest_versions':digest_versions,'retrieval_method':'GOAL_CURRENT_DIGEST_FTS5_FILTER_V1','token_budget':b.token_budget,'byte_budget':b.byte_budget,'used_tokens_upper_bound':used,'used_bytes_estimate':used,'budget_scope':'SERIALIZED_CONTEXT_PARTS_UTF8_JSON','token_estimator':'UTF8_BYTE_UPPER_BOUND_V1_NOT_MODEL_TOKENIZER','confirmed_memory_refs':[r.model_dump(mode='json') for r in b.confirmed_memories],'created_at':now(),'raw_text_logged':False,'parts_meta':[{k:v for k,v in p.items() if k!='text'} for p in parts]}
            RetrievalReceipt.model_validate(receipt)
            prior=c.execute('SELECT payload,fingerprint FROM retrieval_receipts WHERE operation_id=?',(op,)).fetchone()
            if prior and prior['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
            if prior:receipt=json.loads(prior['payload'])
            else:c.execute('INSERT INTO retrieval_receipts VALUES(?,?,?,?)',(receipt['id'],op,fp,encode(receipt)))
        return {'receipt':receipt,'context':parts,'authority':'RAW_MESSAGES_AND_USER_GOAL; DIGESTS_DERIVED_ONLY','narrow_tools':{'journal':'SEPARATE_AUTHORIZATION_REQUIRED','sleep':'SEPARATE_AUTHORIZATION_REQUIRED','health':'SEPARATE_AUTHORIZATION_REQUIRED'},'live_provider_calls':False}
    def build_free(self,conversation_id,operation_id,token_budget=8000,byte_budget=16000,max_sources=16):
        op=str(operation_id);fp=digest(encode({'conversation':str(conversation_id),'token_budget':token_budget,'byte_budget':byte_budget,'max_sources':max_sources}).encode())
        with self.store.transaction() as c:
            prior=c.execute('SELECT payload,fingerprint FROM retrieval_receipts WHERE operation_id=?',(op,)).fetchone()
            if prior:
                if prior['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                return self.replay_context(c,json.loads(prior['payload']))
            conv=self.conversations.row(c,conversation_id)
            if conv.mode!='FREE':raise SafeError('FREE_CONTEXT_MODE_REQUIRED')
            rows=c.execute('SELECT payload FROM conversation_messages WHERE conversation_id=? ORDER BY sequence DESC LIMIT 6',(str(conv.id),)).fetchall()
            parts=[];refs=[];used=2
            for row in rows:
                m=json.loads(row[0]);ref={'id':m['id'],'revision':m['revision']};part={'kind':'CURRENT_TURN','text':m['raw_text'],'sources':[ref],'digest_version':None,'artifact_id':None,'memory_ref':None};size=len(encode(part).encode())+2
                if used+size>min(token_budget,byte_budget):
                    if not parts:raise SafeError('CONTEXT_BUDGET_TOO_SMALL',409)
                    continue
                parts.append(part);refs.append(ref);used+=size
            parts.reverse()
            receipt={'id':str(uuid4()),'goal':None,'conversation_id':str(conv.id),'timezone':'Europe/Warsaw','window_start':conv.created_utc,'window_end':now(),'sources':refs,'digest_versions':[],'retrieval_method':'FREE_RECENT_V1','token_budget':token_budget,'byte_budget':byte_budget,'used_tokens_upper_bound':used,'used_bytes_estimate':used,'budget_scope':'SERIALIZED_CONTEXT_PARTS_UTF8_JSON','token_estimator':'UTF8_BYTE_UPPER_BOUND_V1_NOT_MODEL_TOKENIZER','confirmed_memory_refs':[],'created_at':now(),'raw_text_logged':False,'parts_meta':[{k:v for k,v in p.items() if k!='text'} for p in parts]}
            RetrievalReceipt.model_validate(receipt)
            c.execute('INSERT INTO retrieval_receipts VALUES(?,?,?,?)',(receipt['id'],op,fp,encode(receipt)))
        return {'receipt':receipt,'context':parts,'authority':'RAW_MESSAGES_ONLY','live_provider_calls':False}
    def replay_context(self,c,receipt):
        goal=self.row(c,receipt['goal']['id'],receipt['goal']['revision']) if receipt['goal'] else None;parts=[]
        for metadata in receipt['parts_meta']:
            kind=metadata['kind'];value=None
            if kind=='GOAL_REVISION':value=goal.text
            elif kind.endswith('DIGEST'):
                row=c.execute('SELECT payload FROM conversation_digests WHERE id=?',(metadata['artifact_id'],)).fetchone()
                if not row:raise SafeError('SOURCE_CHANGED',409)
                d=json.loads(row[0])
                if d['version']!=metadata['digest_version'] or not self.valid_digest(c,d):raise SafeError('SOURCE_CHANGED',409)
                value=d['text']
            elif kind=='CONFIRMED_MEMORY':
                ref=metadata['memory_ref'];row=c.execute('SELECT * FROM memories WHERE id=?',(ref['id'],)).fetchone()
                if not row or row['revision']!=ref['revision'] or row['status']!='USER_CONFIRMED':raise SafeError('SOURCE_CHANGED',409)
                value=row['content']
            else:
                ref=metadata['sources'][0];row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
                if not row:raise SafeError('SOURCE_CHANGED',409)
                m=json.loads(row[0])
                if m['revision']!=ref['revision']:raise SafeError('SOURCE_CHANGED',409)
                value=m['raw_text']
            parts.append(dict(metadata,text=value))
        return {'receipt':receipt,'context':parts,'authority':'RAW_MESSAGES_AND_USER_GOAL; DIGESTS_DERIVED_ONLY','narrow_tools':{'journal':'SEPARATE_AUTHORIZATION_REQUIRED','sleep':'SEPARATE_AUTHORIZATION_REQUIRED','health':'SEPARATE_AUTHORIZATION_REQUIRED'},'live_provider_calls':False}
    def expand(self,b:Expansion):
        with self.store.connect() as c:
            r=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(str(b.receipt_id),)).fetchone()
            if not r:raise SafeError('RETRIEVAL_RECEIPT_NOT_FOUND',404)
            receipt=json.loads(r[0]);allowed={(s['id'],s['revision']) for s in receipt['sources']};parts=[];used=2
            for s in b.sources:
                if (str(s.id),s.revision) not in allowed:raise SafeError('SOURCE_EXPANSION_OUT_OF_SCOPE',409)
                row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(str(s.id),)).fetchone()
                if not row:raise SafeError('SOURCE_CHANGED',409)
                m=json.loads(row[0])
                if m['revision']!=s.revision:raise SafeError('SOURCE_CHANGED',409)
                size=len(encode(m).encode())+2
                if used+size>min(b.token_budget,b.byte_budget):raise SafeError('CONTEXT_BUDGET_TOO_SMALL',409)
                used+=size;parts.append(m)
            return {'messages':parts,'used_tokens_upper_bound':used,'source_authority':'EXACT_RAW_MESSAGE_REVISIONS','receipt_id':str(b.receipt_id)}
