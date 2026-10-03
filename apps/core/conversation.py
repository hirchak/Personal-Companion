"""Persistent deterministic conversation controller. No provider tools or model inference."""
from uuid import uuid5,UUID
from typing import Protocol
from pydantic import ValidationError
from .storage import SafeError,MARKER,encode,digest,now
from .conversation_contracts import Conversation,Message,NewConversation,SendMessage,ConversationAction,CandidateResponse

CONVERSATION_TABLES=(
 'CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL,updated TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS conversation_messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,sequence INTEGER NOT NULL,payload TEXT NOT NULL,UNIQUE(conversation_id,sequence))',
 'CREATE TABLE IF NOT EXISTS conversation_receipts(operation_id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT,revision INTEGER NOT NULL)',
 'CREATE TABLE IF NOT EXISTS conversation_tombstones(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,deleted_utc TEXT NOT NULL)',
)
NAMESPACE=UUID('70000000-0000-4000-8000-000000000002')

class ConversationResponder(Protocol):
    def candidate(self)->CandidateResponse|None: ...

class DisabledResponder:
    def candidate(self):return None

class SyntheticResponder:
    def candidate(self):
        return CandidateResponse(role='ASSISTANT',text='Це демо-відповідь без AI. Так можна перевірити розмову з кількома повідомленнями. Хочете додати ще один тестовий рядок?',provenance='MOCK_SYNTHETIC',synthetic=True)


def check_conversations(c):
    try:
        for row in c.execute('SELECT * FROM conversations'):
            x=Conversation.model_validate_json(row['payload'])
            if str(x.id)!=row['id'] or x.revision!=row['revision'] or x.updated_utc!=row['updated']:raise ValueError()
        for row in c.execute('SELECT * FROM conversation_messages'):
            m=Message.model_validate_json(row['payload'])
            if str(m.id)!=row['id'] or str(m.conversation_id)!=row['conversation_id']:raise ValueError()
            if m.role=='ASSISTANT' and (m.provenance not in {'MOCK_SYNTHETIC','MODEL_GENERATED'} or not m.synthetic):raise ValueError()
            if m.provenance=='MODEL_GENERATED' and not m.inference_reference:raise ValueError()
    except (ValueError,TypeError,ValidationError):raise SafeError('CONVERSATION_INTEGRITY') from None

class Conversations:
    def __init__(self,store,synthetic_demo=False):
        if type(synthetic_demo) is not bool:raise SafeError('CONVERSATION_CONFIG_INVALID')
        self.store,self.synthetic_demo=store,synthetic_demo
        self.responder:ConversationResponder= SyntheticResponder() if synthetic_demo else DisabledResponder()

    def mode(self):
        # Data marker is independently required before any synthetic adapter call.
        if self.synthetic_demo:
            import json
            if json.loads((self.store.root/'synthetic.json').read_text())!=MARKER:raise SafeError('SYNTHETIC_ROOT_REQUIRED')
        return {'synthetic_demo':self.synthetic_demo,'responder':'MOCK_SYNTHETIC' if self.synthetic_demo else 'OFF',
                'live_provider_calls':False,'clinical_active':0,'actual_asr':'NOT_RUN','privacy':'LOCAL_ONLY'}

    def row(self,c,id):
        r=c.execute('SELECT * FROM conversations WHERE id=?',(str(id),)).fetchone()
        if not r:
            dead=c.execute('SELECT 1 FROM conversation_tombstones WHERE id=?',(str(id),)).fetchone()
            raise SafeError('CONVERSATION_DELETED' if dead else 'CONVERSATION_NOT_FOUND',410 if dead else 404)
        try:
            x=Conversation.model_validate_json(r['payload'])
            if x.revision!=r['revision'] or str(x.id)!=r['id']:raise ValueError()
            return x
        except (ValueError,ValidationError):raise SafeError('CONVERSATION_INTEGRITY',409) from None

    def view(self,c,x,after=0,limit=100):
        rows=c.execute('SELECT payload,sequence FROM conversation_messages WHERE conversation_id=? AND sequence>? ORDER BY sequence LIMIT ?',(str(x.id),after,limit)).fetchall()
        messages=[Message.model_validate_json(r['payload']).model_dump(mode='json') for r in rows]
        return {'conversation':x.model_dump(mode='json'),'messages':messages,'next_after':rows[-1]['sequence'] if len(rows)==limit else None,'responder':self.mode()['responder']}

    def get(self,id,after=0):
        with self.store.connect() as c:return self.view(c,self.row(c,id),after)

    def list(self,archived=False,offset=0):
        with self.store.connect() as c:
            rows=c.execute('SELECT payload FROM conversations WHERE json_extract(payload,"$.state")=? ORDER BY updated DESC,id LIMIT 50 OFFSET ?',('ARCHIVED' if archived else 'ACTIVE',offset)).fetchall()
            return {'items':[Conversation.model_validate_json(r[0]).model_dump(mode='json') for r in rows],'next_offset':offset+50 if len(rows)==50 else None}

    def create(self,body:NewConversation):
        self.mode();op=str(body.operation_id);id=str(uuid5(NAMESPACE,op));fp=digest(encode(body.model_dump(mode='json')).encode())
        with self.store.transaction() as c:
            if c.execute('SELECT 1 FROM conversation_tombstones WHERE id=?',(id,)).fetchone():raise SafeError('CONVERSATION_DELETED',410)
            receipt=c.execute('SELECT * FROM conversation_receipts WHERE operation_id=?',(op,)).fetchone()
            if receipt:
                if receipt['action']!='create' or receipt['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                return self.view(c,self.row(c,id))
            goal_binding=None
            if (body.goal_id is None)!=(body.goal_revision is None):raise SafeError('GOAL_BINDING_REQUIRED')
            if body.goal_id is not None:
                from .reflection import Reflection
                g=Reflection(self).row(c,body.goal_id,body.goal_revision)
                current=Reflection(self).row(c,body.goal_id)
                if current.state!='ACTIVE' or current.revision!=g.revision:raise SafeError('ACTIVE_GOAL_REQUIRED',409)
                goal_binding={'id':str(g.id),'revision':g.revision}
            time=now();x=Conversation(schema_version=1,id=UUID(id),title='Розмова · '+time[:16].replace('T',' '),state='ACTIVE',revision=1,created_utc=time,updated_utc=time,provenance='ORIGINAL_SYNTHETIC' if self.synthetic_demo else 'USER_LOCAL',synthetic=self.synthetic_demo,privacy_class='PRIVATE_PERSONAL',mode='DEEP' if goal_binding else 'FREE',goal_binding=goal_binding)
            c.execute('INSERT INTO conversations VALUES(?,?,?,?)',(id,1,encode(x.model_dump(mode='json')),time))
            c.execute('INSERT INTO conversation_receipts VALUES(?,?,?,?,?)',(op,id,'create',fp,1))
            result=self.view(c,x)
        return result

    def voice_source(self,c,source):
        if source is None:return
        t=c.execute('SELECT * FROM transcripts WHERE id=?',(str(source.transcript_id),)).fetchone()
        if (not t or t['state']!='TRANSCRIPT_READY' or t['revision']!=source.revision
            or t['audio_hash']!=source.audio_hash or digest((t['edited'] if t['edited'] is not None else t['candidate']).encode())!=source.text_hash):
            raise SafeError('VOICE_SOURCE_STALE',409)
        if t['engine']=='deterministic-fake-local' and not self.synthetic_demo:raise SafeError('SYNTHETIC_SOURCE_DENIED',409)

    def send(self,id,body:SendMessage,respond=True):
        mode=self.mode();op=str(body.operation_id);id=str(id);fp=digest(encode({'id':id,'request':body.model_dump(mode='json')}).encode())
        with self.store.transaction() as c:
            x=self.row(c,id);receipt=c.execute('SELECT * FROM conversation_receipts WHERE operation_id=?',(op,)).fetchone()
            if receipt:
                if receipt['conversation_id']!=id or receipt['action']!='send' or receipt['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                return self.view(c,x)
            if x.revision!=body.base_revision:raise SafeError('REVISION_CONFLICT',409)
            if x.state!='ACTIVE':raise SafeError('CONVERSATION_ARCHIVED',409)
            if x.mode=='DEEP':
                from .reflection import Reflection
                current_goal=Reflection(self).row(c,x.goal_binding.id)
                if current_goal.state!='ACTIVE':raise SafeError('GOAL_NOT_ACTIVE',409)
            self.voice_source(c,body.source_reference)
            time=now();uid=uuid5(NAMESPACE,op+':user');seq=c.execute('SELECT COALESCE(MAX(sequence),0) FROM conversation_messages WHERE conversation_id=?',(id,)).fetchone()[0]
            if seq>=2000:raise SafeError('CONVERSATION_MESSAGE_LIMIT',409)
            user=Message(schema_version=1,id=uid,conversation_id=x.id,role='USER',raw_text=body.text,created_utc=time,revision=1,provenance='USER_AUTHORED',source_reference=body.source_reference,source_message_id=None,synthetic=self.synthetic_demo,privacy_class='PRIVATE_PERSONAL')
            c.execute('INSERT INTO conversation_messages VALUES(?,?,?,?)',(str(uid),id,seq+1,encode(user.model_dump(mode='json'))))
            if mode['synthetic_demo'] and respond:
                # The controller chooses the sole allowed adapter; its output is data, not authority.
                candidate=CandidateResponse.model_validate(self.responder.candidate())
                response=Message(schema_version=1,id=uuid5(NAMESPACE,op+':assistant'),conversation_id=x.id,role=candidate.role,raw_text=candidate.text,created_utc=time,revision=1,provenance=candidate.provenance,source_reference=None,source_message_id=uid,synthetic=True,privacy_class='PRIVATE_PERSONAL')
                c.execute('INSERT INTO conversation_messages VALUES(?,?,?,?)',(str(response.id),id,seq+2,encode(response.model_dump(mode='json'))))
            x.revision+=1;x.updated_utc=time
            c.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',(x.revision,encode(x.model_dump(mode='json')),time,id))
            c.execute('INSERT INTO conversation_receipts VALUES(?,?,?,?,?)',(op,id,'send',fp,x.revision));result=self.view(c,x)
        return result

    def action(self,id,body:ConversationAction):
        id=str(id);op=str(body.operation_id);fp=digest(encode({'id':id,'request':body.model_dump(mode='json')}).encode())
        with self.store.transaction() as c:
            receipt=c.execute('SELECT * FROM conversation_receipts WHERE operation_id=?',(op,)).fetchone()
            if receipt:
                if receipt['conversation_id']!=id or receipt['action']!=body.action or receipt['fingerprint']!=fp:raise SafeError('OPERATION_REUSE',409)
                if body.action=='delete':return {'id':id,'state':'DELETED','revision':receipt['revision']}
                return self.view(c,self.row(c,id))
            x=self.row(c,id)
            if x.revision!=body.base_revision:raise SafeError('REVISION_CONFLICT',409)
            revision=x.revision+1;time=now()
            if body.action=='delete':
                c.execute('UPDATE reflection_receipts SET fingerprint="REDACTED" WHERE entity_id IN (SELECT id FROM conversation_messages WHERE conversation_id=?)',(id,));c.execute('DELETE FROM conversations WHERE id=?',(id,));c.execute('UPDATE conversation_receipts SET fingerprint=NULL WHERE conversation_id=?',(id,));c.execute('INSERT INTO conversation_tombstones VALUES(?,?,?)',(id,revision,time));result={'id':id,'state':'DELETED','revision':revision}
            else:
                state='ARCHIVED' if body.action=='archive' else 'ACTIVE'
                if x.state==state:raise SafeError('CONVERSATION_TRANSITION_INVALID',409)
                x.state=state;x.revision=revision;x.updated_utc=time;c.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',(revision,encode(x.model_dump(mode='json')),time,id));result=self.view(c,x)
            c.execute('INSERT INTO conversation_receipts VALUES(?,?,?,?,?)',(op,id,body.action,fp,revision))
        return result
