"""Private manual drafts, exact epoch-bound approval and local files. No source reader or sender."""
import json
import re
from .m5_contracts import FeedbackInput, SpaceState
from .storage import SafeError, now, encode, digest

M5_TABLES=(
    'CREATE TABLE IF NOT EXISTS feedback_drafts(id TEXT PRIMARY KEY,version INTEGER NOT NULL,payload TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,approval TEXT)',
    'CREATE TABLE IF NOT EXISTS personal_space(id INTEGER PRIMARY KEY CHECK(id=1),version INTEGER NOT NULL,state TEXT NOT NULL)',
)

def exact_copy(row,epoch):
    return {'draft_id':row['id'],'version':row['version'],'restore_epoch':epoch,
            'content':json.loads(row['payload']),'export_destination':'local_file'}
def exact_hash(row,epoch):return digest(encode(exact_copy(row,epoch)).encode())
def render_feedback(exact):
    p=exact['content'];lines=['# Відгук · точна копія для локального експорту']
    labels={'title':'Назва','type':'Тип','expected':'Очікуваний результат','actual':'Що незручно / фактичний результат',
            'steps':'Кроки відтворення','description':'Опис','visibility':'Видимість','destination':'Запланований отримувач'}
    for k,label in labels.items():
        text=p[k];fence='`'*(max([len(x) for x in re.findall(r'`+',text)]+[2])+1)
        lines.append('## '+label+'\n\n'+fence+'text\n'+text+'\n'+fence)
    lines.append('Вкладення: відсутні. Посилання на приватні джерела: відсутні.\nЕкспорт лише у локальний файл; публікація не виконана.')
    return '\n\n'.join(lines)+'\n'

class Feedback:
    def __init__(self,store):self.store=store
    def row(self,c,id):
        r=c.execute('SELECT * FROM feedback_drafts WHERE id=?',(str(id),)).fetchone()
        if not r:raise SafeError('NOT_FOUND',404)
        return r
    def view(self,c,r):
        epoch=c.execute('SELECT restore_epoch FROM vault_meta').fetchone()[0]
        exact=exact_copy(r,epoch);sha=exact_hash(r,epoch)
        approval=json.loads(r['approval']) if r['approval'] else None
        approved=bool(approval and approval=={'content_hash':sha,'version':r['version'],'epoch':epoch})
        return {'id':r['id'],'version':r['version'],'payload':exact['content'],'created':r['created'],'updated':r['updated'],
                'exact_copy':exact,'content_hash':sha,'approved':approved,'markdown':render_feedback(exact)}
    def list(self):
        with self.store.connect() as c:return {'items':[self.view(c,r) for r in c.execute('SELECT * FROM feedback_drafts ORDER BY updated DESC LIMIT 100')]}
    def save(self,body):
        with self.store.transaction() as c:
            old=c.execute('SELECT * FROM feedback_drafts WHERE id=?',(str(body.draft_id),)).fetchone()
            if (old['version'] if old else 0)!=body.base_version:raise SafeError('FEEDBACK_CHANGED',409)
            if not old:
                c.execute('INSERT INTO feedback_drafts VALUES(?,?,?,?,?,NULL)',(str(body.draft_id),1,encode(body.payload.model_dump(mode='json')),now(),now()))
            else:
                c.execute('UPDATE feedback_drafts SET version=version+1,payload=?,updated=?,approval=NULL WHERE id=?',
                          (encode(body.payload.model_dump(mode='json')),now(),str(body.draft_id)))
            result=self.view(c,self.row(c,body.draft_id))
        return result
    def approve(self,id,body):
        with self.store.transaction() as c:
            r=self.row(c,id);epoch=c.execute('SELECT restore_epoch FROM vault_meta').fetchone()[0]
            if r['version']!=body.version or exact_hash(r,epoch)!=body.content_hash:raise SafeError('FEEDBACK_APPROVAL_STALE',409)
            c.execute('UPDATE feedback_drafts SET approval=? WHERE id=?',
                      (encode({'content_hash':body.content_hash,'version':body.version,'epoch':epoch}),str(id)))
            result=self.view(c,self.row(c,id))
        return result
    def delete(self,id,body):
        with self.store.transaction() as c:
            r=self.row(c,id)
            if r['version']!=body.version:raise SafeError('FEEDBACK_CHANGED',409)
            c.execute('DELETE FROM feedback_drafts WHERE id=?',(str(id),))
        return {'code':'DELETED'}
    def export(self,id,body):
        with self.store.connect() as c:
            c.execute('BEGIN');r=self.row(c,id);view=self.view(c,r)
            if not view['approved'] or view['version']!=body.version or view['content_hash']!=body.content_hash:
                raise SafeError('FEEDBACK_APPROVAL_REQUIRED',409)
        meta={'approved_version':view['version'],'approved_hash':view['content_hash'],'draft_id':view['id'],
              'intended_destination':view['payload']['destination'],'visibility':view['payload']['visibility'],
              'exported_at_utc':now(),'attachments':[],'references':[],'publication':'NOT_PERFORMED','destination':'local_file'}
        return encode({'metadata':meta,'approved_exact_copy':view['exact_copy']}) if body.format=='json' else view['markdown']+'\n## Метадані експорту\n\n```json\n'+encode(meta)+'\n```\n'

class PersonalSpace:
    def __init__(self,store):self.store=store
    def get_in(self,c):
        r=c.execute('SELECT * FROM personal_space WHERE id=1').fetchone()
        return {'version':r['version'],'state':json.loads(r['state']),'scope':'this_device'} if r else {'version':0,'state':SpaceState().model_dump(mode='json'),'scope':'this_device'}
    def get(self):
        with self.store.connect() as c:return self.get_in(c)
    def update(self,body):
        state=body.state.model_dump(mode='json')
        with self.store.transaction() as c:
            old=self.get_in(c)
            # Identical retry is idempotent; a different stale update is rejected.
            if old['version']!=body.base_version:
                if old['version']==body.base_version+1 and old['state']==state:return old
                raise SafeError('SPACE_CHANGED',409)
            c.execute('INSERT OR REPLACE INTO personal_space VALUES(1,?,?)',(old['version']+1,encode(state)))
            result=self.get_in(c)
        return result


def check_m5(c):
    """Typed validation on reopen/backup/restore, before activating damaged state."""
    from uuid import UUID
    try:
        epoch=c.execute('SELECT restore_epoch FROM vault_meta').fetchone()[0]
        for r in c.execute('SELECT * FROM feedback_drafts'):
            if str(UUID(r['id']))!=r['id'] or type(r['version']) is not int or r['version']<1:raise ValueError()
            FeedbackInput.model_validate(json.loads(r['payload']))
            from datetime import datetime
            for k in ('created','updated'):
                if datetime.fromisoformat(r[k]).tzinfo is None:raise ValueError()
            if r['approval']:
                a=json.loads(r['approval'])
                if a!={'content_hash':exact_hash(r,epoch),'version':r['version'],'epoch':epoch}:raise ValueError()
        for r in c.execute('SELECT * FROM personal_space'):
            if r['id']!=1 or type(r['version']) is not int or r['version']<1:raise ValueError()
            data=json.loads(r['state'])
            if SpaceState.model_validate(data).model_dump(mode='json')!=data:raise ValueError()
    except (ValueError,TypeError,KeyError):raise SafeError('M5_STATE_INTEGRITY') from None
