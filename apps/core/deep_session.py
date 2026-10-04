"""Persistent versioned working understanding. All writes are deterministic/source checked."""
import json
from uuid import uuid4
from .storage import SafeError, encode, digest, now
from .deep_session_contracts import WorkingMap, MapItem, DeepSession

DEEP_TABLES = (
 'CREATE TABLE IF NOT EXISTS deep_sessions(conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,revision INTEGER NOT NULL,payload TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS working_maps(goal_id TEXT NOT NULL,goal_revision INTEGER NOT NULL,version INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(goal_id,goal_revision,version))',
 'CREATE TABLE IF NOT EXISTS deep_actions(operation_id TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,payload TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS deep_context_previews(receipt_id TEXT PRIMARY KEY REFERENCES retrieval_receipts(id),payload TEXT NOT NULL)',
)

def check_deep(c):
    try:
        for r in c.execute('SELECT * FROM deep_sessions'):
            d=DeepSession.model_validate_json(r['payload'])
            if str(d.conversation_id)!=r['conversation_id'] or d.revision!=r['revision']:raise ValueError()
            conv=c.execute('SELECT payload FROM conversations WHERE id=?',(r['conversation_id'],)).fetchone()
            if not conv or json.loads(conv[0])['goal_binding']!=d.goal.model_dump(mode='json'):raise ValueError()
        for r in c.execute('SELECT * FROM working_maps'):
            m=WorkingMap.model_validate_json(r['payload'])
            if str(m.goal.id)!=r['goal_id'] or m.goal.revision!=r['goal_revision'] or m.version!=r['version']:raise ValueError()
            if len({str(i.id) for i in m.items})!=len(m.items):raise ValueError()
    except (ValueError,KeyError,TypeError):raise SafeError('DEEP_INTEGRITY') from None

class DeepSessions:
    def __init__(self,conversations):self.conversations=conversations;self.store=conversations.store
    def session(self,c,id):
        conv=self.conversations.row(c,id)
        if conv.mode!='DEEP':raise SafeError('DEEP_MODE_REQUIRED',409)
        row=c.execute('SELECT payload FROM deep_sessions WHERE conversation_id=?',(str(id),)).fetchone()
        if row:return json.loads(row[0])
        d=DeepSession(conversation_id=conv.id,goal=conv.goal_binding.model_dump(),created_at=now(),updated_at=now()).model_dump(mode='json')
        c.execute('INSERT INTO deep_sessions VALUES(?,?,?)',(str(id),1,encode(d)))
        return d
    def current(self,c,goal):
        r=c.execute('SELECT payload FROM working_maps WHERE goal_id=? AND goal_revision=? ORDER BY version DESC LIMIT 1',(str(goal['id']),goal['revision'])).fetchone()
        return json.loads(r[0]) if r else None
    def effective(self,c,m):
        if m is None:return None
        m=json.loads(encode(m))
        for item in m['items']:
            if item['state']!='CURRENT':continue
            for s in item['sources']:
                row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(s['id'],)).fetchone()
                if not row or json.loads(row[0])['revision']!=s['revision']:
                    item['state']='STALE';break
        return m
    def read(self,id):
        with self.store.transaction() as c:
            s=self.session(c,id);m=self.current(c,s['goal'])
            history=[json.loads(r[0]) for r in c.execute('SELECT payload FROM working_maps WHERE goal_id=? AND goal_revision=? ORDER BY version DESC LIMIT 20',(s['goal']['id'],s['goal']['revision']))]
            sessions=[json.loads(r[0]) for r in c.execute('SELECT payload FROM deep_sessions WHERE json_extract(payload,"$.goal.id")=? ORDER BY json_extract(payload,"$.created_at")',(s['goal']['id'],))]
            from .reflection import Reflection
            goal=Reflection(self.conversations).row(c,s['goal']['id'],s['goal']['revision']).model_dump(mode='json')
            return {'goal':goal,'session':s,'map':self.effective(c,m),'history':history,'sessions':sessions,'memory_promotion':False}
    def write(self,c,s,items,metadata):
        prior=self.current(c,s['goal']);m={'schema_version':1,'goal':s['goal'],'version':(prior['version'] if prior else 0)+1,'conversation_id':s['conversation_id'],'items':items,'created_at':now(),'provider_model':metadata['provider_model'],'provider_route':metadata['provider_route'],'skills':metadata['selected_skills'],'request_hash':metadata['request_hash'],'provenance':'SOURCE_BOUND_NEUTRAL_REFLECTION'}
        WorkingMap.model_validate(m)
        c.execute('INSERT INTO working_maps VALUES(?,?,?,?)',(s['goal']['id'],s['goal']['revision'],m['version'],encode(m)))
        return m
    def ingest(self,c,id,candidate,aliases,metadata):
        s=self.session(c,id)
        if s['phase'] in {'CLOSED','PAUSED'}:raise SafeError('SESSION_NOT_OPEN',409)
        old=self.effective(c,self.current(c,s['goal']));items=old['items'] if old else []
        normalize=lambda t:' '.join(t.casefold().split())
        # Explicit past rejection/irrelevance remains a tombstone even after bounded compaction.
        retired={normalize(r[0]) for r in c.execute('''SELECT DISTINCT json_extract(i.value,'$.text')
            FROM working_maps m,json_each(json_extract(m.payload,'$.items')) i
            WHERE m.goal_id=? AND m.goal_revision=? AND json_extract(i.value,'$.state') IN ('REJECTED','IRRELEVANT')''',(s['goal']['id'],s['goal']['revision']))}
        for item in candidate.items:
            # Preserve rejected/irrelevant/confirmed entries rather than replacing them with model output.
            if normalize(item.text) in retired or any(normalize(i['text'])==normalize(item.text) and i['state']!='STALE' for i in items):continue
            refs=[]
            for alias in item.source_refs:
                if alias not in aliases:raise SafeError('MODEL_SOURCE_OUT_OF_SCOPE')
                ref=aliases[alias];row=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
                if not row or json.loads(row[0])['revision']!=ref['revision']:raise SafeError('SOURCE_CHANGED',409)
                refs.append(ref)
                if item.provenance=='USER_STATED':
                    source=json.loads(row[0])
                    if source['role']!='USER' or source['provenance']!='USER_AUTHORED' or item.text not in source['raw_text']:raise SafeError('USER_STATEMENT_QUOTE_REQUIRED')
            if len(items)>=40:
                # Never discard confirmed or rejected understanding. Explicitly retired and
                # source-invalid model items remain in immutable historical versions.
                items=[i for i in items if i['state']!='IRRELEVANT' and not (i['state']=='STALE' and i['provenance'] not in {'USER_STATED','USER_CONFIRMED'})]
            if len(items)>=40:raise SafeError('MAP_CAPACITY_REVIEW_REQUIRED',409)
            items.append(MapItem(id=uuid4(),kind=item.kind,text=item.text,provenance=item.provenance,sources=refs).model_dump(mode='json'))
        return self.write(c,s,items,metadata)
    def action(self,id,b):
        fp=digest(encode({'id':str(id),'body':b.model_dump(mode='json')}).encode())
        with self.store.transaction() as c:
            old=c.execute('SELECT * FROM deep_actions WHERE operation_id=?',(str(b.operation_id),)).fetchone()
            if old:
                if old['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                return json.loads(old['payload'])
            s=self.session(c,id);m=self.effective(c,self.current(c,s['goal']))
            if not m or m['version']!=b.base_version:raise SafeError('MAP_VERSION_CHANGED',409)
            item=next((i for i in m['items'] if i['id']==str(b.item_id)),None)
            if not item:raise SafeError('MAP_ITEM_NOT_FOUND',404)
            if b.action=='reject':
                if item['kind']!='HYPOTHESIS':raise SafeError('HYPOTHESIS_REQUIRED')
                item['state']='REJECTED'
            elif b.action=='irrelevant':item['state']='IRRELEVANT'
            else:
                if item['state']!='CURRENT' or item['kind']=='HYPOTHESIS':raise SafeError('MAP_ITEM_REVIEW_REQUIRED',409)
                if b.action=='clarify' and item['provenance']!='USER_CONFIRMED':raise SafeError('CONFIRMED_TAKEAWAY_REQUIRED',409)
                if b.text:item['text']=b.text
                item['kind']='TAKEAWAY';item['provenance']='USER_CONFIRMED'
            result=self.write(c,s,m['items'],{'provider_model':'USER_ACTION','provider_route':'LOCAL_EXPLICIT_USER','selected_skills':[],'request_hash':fp})
            c.execute('INSERT INTO deep_actions VALUES(?,?,?)',(str(b.operation_id),fp,encode(result)))
        return result
    def session_action(self,id,b):
        fp=digest(encode({'id':str(id),'body':b.model_dump(mode='json')}).encode())
        with self.store.transaction() as c:
            old=c.execute('SELECT * FROM deep_actions WHERE operation_id=?',(str(b.operation_id),)).fetchone()
            if old:
                if old['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                return json.loads(old['payload'])
            s=self.session(c,id)
            if s['revision']!=b.base_revision:raise SafeError('SESSION_CHANGED',409)
            if s['phase']=='CLOSED':raise SafeError('SESSION_CLOSED',409)
            if b.action=='focus':
                if not b.focus:raise SafeError('FOCUS_REQUIRED')
                s['focus']=b.focus
            elif b.action=='phase':
                if not b.phase or s['phase']=='PAUSED':raise SafeError('SESSION_TRANSITION_INVALID')
                s['phase']=b.phase
            elif b.action=='pause':s['phase']='PAUSED'
            elif b.action=='resume':
                if s['phase']!='PAUSED':raise SafeError('SESSION_TRANSITION_INVALID')
                s['phase']='EXPLORE'
            elif b.action=='close':
                if c.execute('SELECT 1 FROM conversation_inferences WHERE conversation_id=? AND state IN ("QUEUED","RUNNING")',(str(id),)).fetchone():raise SafeError('INFERENCE_BUSY',409)
                s['phase']='CLOSED';s['closed_at']=now()
                job=c.execute('SELECT id FROM conversation_inferences WHERE conversation_id=? AND state="COMPLETED" AND json_extract(payload,"$.purpose")="CLOSURE" ORDER BY json_extract(payload,"$.created_at") DESC LIMIT 1',(str(id),)).fetchone()
                s['closure_job_id']=job[0] if job else None
            s['revision']+=1;s['updated_at']=now();DeepSession.model_validate(s)
            c.execute('UPDATE deep_sessions SET revision=?,payload=? WHERE conversation_id=?',(s['revision'],encode(s),str(id)))
            c.execute('INSERT INTO deep_actions VALUES(?,?,?)',(str(b.operation_id),fp,encode(s)))
        return s
    def snapshot(self,c,id,receipt):
        s=self.session(c,id);m=self.effective(c,self.current(c,s['goal']))
        bounded=[]
        if m:
            for i in m['items']:
                if i['state']=='STALE':continue
                sources=[]
                for ref in i['sources']:
                    r=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
                    if r:
                        source=json.loads(r[0])
                        if source['revision']==ref['revision'] and receipt['window_start']<=source['created_utc']<=receipt['window_end']:sources.append(ref)
                if len(sources)==len(i['sources']):bounded.append(i)
        closures=[]
        for r in c.execute('SELECT payload FROM conversation_inferences WHERE state="COMPLETED" AND json_extract(payload,"$.purpose")="CLOSURE" AND conversation_id!=? ORDER BY json_extract(payload,"$.created_at") DESC LIMIT 12',(str(id),)):
            d=json.loads(r[0]);v=c.execute('SELECT payload FROM conversations WHERE id=?',(d['conversation_id'],)).fetchone()
            if not v or json.loads(v[0]).get('goal_binding')!=s['goal']:continue
            if not receipt['window_start']<=d['created_at']<=receipt['window_end']:continue
            rr=c.execute('SELECT payload FROM retrieval_receipts WHERE id=?',(d['request_metadata']['retrieval_receipt_id'],)).fetchone()
            if not rr:continue
            refs=json.loads(rr[0])['sources'];valid=True
            for ref in refs:
                sr=c.execute('SELECT payload FROM conversation_messages WHERE id=?',(ref['id'],)).fetchone()
                if not sr or json.loads(sr[0])['revision']!=ref['revision'] or not receipt['window_start']<=json.loads(sr[0])['created_utc']<=receipt['window_end']:valid=False;break
            if valid:closures.append({'conversation_id':d['conversation_id'],'closure':d['candidate']['closure'],'sources':refs})
            if len(closures)>=2:break
        important=[i for i in bounded if i['state']=='REJECTED' or i['provenance']=='USER_CONFIRMED']
        recent=[i for i in bounded if i not in important]
        selected=important[:20]+(recent[-(20-len(important)):] if len(important)<20 else [])
        result={'session':s,'map_version':m['version'] if m else 0,'items':selected,'prior_closures':closures}
        if len(encode(result).encode())>16000:raise SafeError('MAP_CONTEXT_LIMIT',413)
        return result
