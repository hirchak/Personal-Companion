"""Journal-backed creative library and minimized exact local exports. No second text store."""
import json
from uuid import uuid4
from .storage import SafeError, encode, digest, now

EXPORT_FIELDS = {'raw_text','title','creative_kind','tags','collections','related_ids','timestamps','provenance'}

def selected_item(e, fields):
    meta=e.get('creative_meta') or {}
    values={'raw_text':e['raw_text'],'title':meta.get('title',''), 'creative_kind':e.get('creative_kind'),
            'tags':e['tags'],'collections':meta.get('collections',[]),'related_ids':meta.get('related_ids',[]),
            'timestamps':{'created':e['created_at_utc'],'updated':e['updated_at_utc']},
            'provenance':{'source':'USER_REPORTED','entry_id':e['id'],'revision':e['revision']}}
    return {'id':e['id'],'revision':e['revision'],**{key:values[key] for key in fields}}

def markdown(items):
    # Code fences longer than anything in the selected data keep user text literal, not active HTML.
    blocks=['# Вибрана творчість','Локальний файл · приватний авторський матеріал · пов’язані записи не включені.']
    for item in items:
        blocks.append('## Вибраний запис '+item['id'])
        for key,value in item.items():
            if key in {'id','revision'}:continue
            text=value if isinstance(value,str) else encode(value)
            fence='`'*(max([len(x) for x in __import__('re').findall(r'`+',text)]+[2])+1)
            blocks.append(key+'\n\n'+fence+'text\n'+text+'\n'+fence)
    return '\n\n'.join(blocks)+'\n'

class CreativeLibrary:
    def __init__(self,journal): self.journal=journal;self.store=journal.store;self.plans={}
    def list(self,q='',kind=None,tag=None,collection=None,archived=False,order='recent',limit=50,offset=0):
        if len(q)>200 or limit<1 or limit>100 or offset<0 or offset>100000 or order not in {'recent','newest'}:
            raise SafeError('QUERY_LIMIT')
        where=["json_extract(payload,'$.type')='creative'","json_extract(payload,'$.creative_meta.library')=1",
               "instr(json_extract(payload,'$.raw_text')||COALESCE(json_extract(payload,'$.creative_meta.title'),''),?)>0",
               "COALESCE(json_extract(payload,'$.creative_meta.archived'),0)=?"]
        args=[q,int(archived)]
        for path,value in [('creative_kind',kind)]:
            if value is not None:where.append(f"json_extract(payload,'$.{path}')=?");args.append(value)
        for path,value in [('tags',tag),('creative_meta.collections',collection)]:
            if value is not None:where.append(f"EXISTS(SELECT 1 FROM json_each(payload,'$.{path}') WHERE value=?)");args.append(value)
        with self.store.connect() as c:
            rows=c.execute('SELECT * FROM entries WHERE '+' AND '.join(where)+' ORDER BY '+('updated' if order=='recent' else 'created')+' DESC,id DESC LIMIT ? OFFSET ?',[*args,limit+1,offset]).fetchall()
            return {'items':[self.journal.view(r) for r in rows[:limit]],'next_offset':offset+limit if len(rows)>limit else None}
    def items(self,c,refs):
        items=[]
        for ref in refs:
            e=self.journal.view(self.journal.row(c,str(ref['id'])))
            if e['type']!='creative' or not e.get('creative_meta') or e['revision']!=ref['revision']:
                raise SafeError('CREATIVE_SELECTION_CHANGED',409)
            items.append(e)
        return items
    def preview(self,body,session):
        refs=[r.model_dump(mode='json') for r in body.entries]
        with self.store.connect() as c:
            c.execute('BEGIN');items=[selected_item(e,body.fields) for e in self.items(c,refs)]
        content={'schema_version':1,'destination':'local_file','include_related':False,'fields':body.fields,'items':items}
        canonical=encode(content).encode()
        if len(canonical)>2097152:raise SafeError('CREATIVE_EXPORT_SIZE_LIMIT',422)
        sha=digest(canonical);plan_id=str(uuid4());clock=self.journal.clock
        self.plans={k:v for k,v in self.plans.items() if v['expires']>clock()}
        if len(self.plans)>=100:raise SafeError('PLAN_LIMIT',429)
        self.plans[plan_id]={'session':session,'expires':clock()+300,'refs':refs,'fields':body.fields,'hash':sha}
        return {'plan_id':plan_id,'content_hash':sha,'content':content,'markdown':markdown(items),
                'warning':'Це приватний авторський матеріал. Перевірте точний вміст перед збереженням локального файлу.'}
    def export(self,body,session):
        p=self.plans.get(str(body.plan_id))
        if not p or p['session']!=session or p['expires']<=self.journal.clock() or body.content_hash!=p['hash']:
            raise SafeError('EXPORT_PLAN_EXPIRED',409)
        with self.store.connect() as c:
            c.execute('BEGIN');items=[selected_item(e,p['fields']) for e in self.items(c,p['refs'])]
        content={'schema_version':1,'destination':'local_file','include_related':False,'fields':p['fields'],'items':items}
        if digest(encode(content).encode())!=p['hash']:raise SafeError('EXPORT_CHANGED',409)
        return markdown(items) if body.format=='markdown' else encode({'content':content,'content_hash':p['hash'],'exported_at_utc':now()})
