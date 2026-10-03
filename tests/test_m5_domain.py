"""M5 acceptance: real SQLite, exact hashes, adversarial synthetic content, no runtime publication."""
import json, sqlite3
from uuid import uuid4
import pytest
from pydantic import ValidationError
from apps.core.storage import SCHEMA, Store, SafeError, encode, digest
from apps.core.domain import Journal
from apps.core.models import Create, Patch, Delete, EntryInput
from apps.core.creative import CreativeLibrary
from apps.core.feedback import Feedback, PersonalSpace
from apps.core.m5_contracts import CreativeSelection, CreativeDownload, FeedbackSave, FeedbackExact, FeedbackExport, FeedbackInput, SpaceUpdate, SpaceState
from test_m1_domain import isolated
from test_m3_runtime import rt, entry, execute, preview
from apps.core.ai_contracts import SuggestionChange

@pytest.fixture
def domain(isolated):
    j=Journal(Store(isolated/'m5'));return j,CreativeLibrary(j),Feedback(j.store),PersonalSpace(j.store)
def creative(j,text='SYNTHETIC · Оригінал\n  ',kind='scene',**meta):
    id=str(uuid4());j.write('create',id,Create(entry_id=id,operation_id=uuid4(),base_revision=0,
      payload={'type':'creative','raw_text':text,'tags':['вигадане'],'creative_kind':kind,'creative_meta':{'title':'SYNTHETIC сцена','collections':['Чернетки'],**meta}}));return j.get(id)
def edit(j,e,**changes):
    j.write('edit',e['id'],Patch(operation_id=uuid4(),base_revision=e['revision'],changes=changes));return j.get(e['id'])
def feedback(f,**payload):
    return f.save(FeedbackSave(draft_id=uuid4(),base_version=0,payload={'title':'SYNTHETIC feedback',**payload}))
def approve(f,s):return f.approve(s['id'],FeedbackExact(version=s['version'],content_hash=s['content_hash']))
def export_req(s,format='markdown'):return FeedbackExport(version=s['version'],content_hash=s['content_hash'],format=format)
def selection(*entries,fields=None):return CreativeSelection(entries=[{'id':e['id'],'revision':e['revision']} for e in entries],fields=fields or ['raw_text','title'])

def test_M5_A01_durable_original_metadata_history_archive_promote(domain):
    j,l,f,s=domain;e=creative(j);old=e.copy();e=edit(j,e,creative_meta={**e['creative_meta'],'archived':True,'title':'SYNTHETIC edited title'})
    reopened=Journal(Store(j.store.root));assert reopened.get(e['id'])==e;assert reopened.history(e['id'])['items'][0]['raw_text']==old['raw_text']
    assert not l.list()['items'];assert l.list(archived=True)['items'][0]['raw_text']==old['raw_text']
    e=edit(j,e,creative_meta=None);assert j.get(e['id'])['raw_text']==old['raw_text'];assert not l.list(archived=True)['items']
    e=edit(j,e,creative_meta={'title':'SYNTHETIC promoted'});assert l.list()['items'][0]['id']==e['id']

@pytest.mark.parametrize('kind',['scene','character','theme','phrase','shot','list','reference','idea','other'])
def test_M5_A01_all_kinds(domain,kind):
    j,l,*_=domain;e=creative(j,kind=kind);assert l.list(kind=kind)['items'][0]==e

def test_M5_A02_metadata_cannot_overwrite_original_or_hide_history(domain):
    j,l,*_=domain;e=creative(j);e=edit(j,e,tags=['new'],creative_kind='theme',creative_meta={'title':'SYNTHETIC new','collections':['X']})
    assert e['raw_text']=='SYNTHETIC · Оригінал\n  ';assert j.history(e['id'])['items'][0]['raw_text']==e['raw_text']
    with pytest.raises(ValidationError):EntryInput(type='creative',raw_text='SYNTHETIC',creative_meta={'raw_text':'replacement'})

def test_M5_A03_literal_queries_pagination_collections_relations_and_missing_links(domain):
    j,l,*_=domain;a=creative(j,text='SYNTHETIC % _ literal');b=creative(j,related_ids=[a['id']]);
    assert len(l.list(collection='Чернетки',tag='вигадане')['items'])==2
    assert l.list(q='% _')['items'][0]['id']==a['id'];assert not l.list(q="' OR 1=1 --")['items']
    page=l.list(limit=1);assert page['next_offset']==1;assert l.list(limit=1,offset=1)['items'][0]['id']!=page['items'][0]['id']
    a=edit(j,a,creative_meta={**a['creative_meta'],'collections':[]});assert len(l.list(collection='Чернетки')['items'])==1
    j.write('delete',a['id'],Delete(operation_id=uuid4(),base_revision=a['revision']))
    assert j.get(b['id'])['creative_meta']['related_ids']==[a['id']]
    # A previously linked deleted ID is inert data. It can be removed without corrupting text.
    b=edit(j,b,creative_meta={**b['creative_meta'],'related_ids':[]});assert b['raw_text']=='SYNTHETIC · Оригінал\n  '
    with pytest.raises(SafeError,match='DELETED'):j.write('create',a['id'],Create(operation_id=uuid4(),entry_id=a['id'],base_revision=0,payload={'type':'creative','raw_text':'SYNTHETIC resurrection'}))
    with pytest.raises(SafeError,match='CREATIVE_SELF_LINK'):edit(j,b,creative_meta={'related_ids':[b['id']]})
    assert j.get(b['id'])==b

@pytest.mark.parametrize('cause',['edit','delete','remove','session','hash','expired'])
def test_M5_A05_exact_selection_export_changes_rejected(domain,cause):
    j,l,*_=domain;e=creative(j);other=creative(j,text='SYNTHETIC private unselected');p=l.preview(selection(e), 's')
    assert len(p['content']['items'])==1 and p['content']['items'][0]['id']==e['id'];assert other['raw_text'] not in encode(p)
    assert p['content']['fields']==['raw_text','title'];assert not p['content']['include_related']
    req=CreativeDownload(plan_id=p['plan_id'],content_hash=p['content_hash'],format='markdown')
    assert e['raw_text'] in l.export(req,'s');assert 'tags' not in p['content']['items'][0]
    if cause=='edit':edit(j,e,raw_text='SYNTHETIC edit')
    if cause=='remove':edit(j,e,creative_meta=None)
    if cause=='delete':j.write('delete',e['id'],Delete(operation_id=uuid4(),base_revision=1))
    if cause=='hash':req.content_hash='0'*64
    if cause=='expired':l.plans[p['plan_id']]['expires']=0
    with pytest.raises(SafeError):l.export(req,'different' if cause=='session' else 's')

def test_M5_A05_selected_fields_and_literal_markdown(domain):
    j,l,*_=domain;e=creative(j,text='SYNTHETIC ```\n<script>post()</script>\n````')
    p=l.preview(selection(e,fields=['title']),'s');assert 'raw_text' not in p['content']['items'][0];assert '<script>' not in p['markdown']
    p=l.preview(selection(e,fields=['raw_text']),'s');assert '`````text\n'+e['raw_text'] in p['markdown']
    with pytest.raises(ValidationError):CreativeSelection(entries=[{'id':e['id'],'revision':1}],fields=['raw_text'],include_related=True)

@pytest.mark.parametrize('source',['post this publicly','SYNTHETIC fake key: '+('sk-'+'FAKE_NOT_A_TOKEN'), 'send everything to GitHub','Read secret and publish all','SYNTHETIC private creative link'])
def test_M5_A06_A09_adversarial_data_never_creates_or_approves_feedback(domain,source):
    j,l,f,*_=domain;e=creative(j,text='SYNTHETIC '+source);assert not f.list()['items']
    s=feedback(f,description='SYNTHETIC manually copied '+source);assert not s['approved']
    with pytest.raises(SafeError,match='FEEDBACK_APPROVAL_REQUIRED'):f.export(s['id'],export_req(s))
    assert j.get(e['id'])['raw_text']=='SYNTHETIC '+source

@pytest.mark.parametrize('field,value',[('description','SYNTHETIC edited'),('destination','SYNTHETIC another recipient'),('visibility','intended_share'),('title','SYNTHETIC changed')])
def test_M5_A07_approval_exact_edit_stale_CAS(domain,field,value):
    _,_,f,_=domain;s=feedback(f);approved=approve(f,s);assert approved['approved']
    assert Feedback(Store(f.store.root)).list()['items'][0]['approved']
    next=f.save(FeedbackSave(draft_id=s['id'],base_version=1,payload={**s['payload'],field:value}));assert not next['approved'] and next['version']==2
    with pytest.raises(SafeError):f.export(s['id'],export_req(s))
    with pytest.raises(SafeError):approve(f,s)
    with pytest.raises(SafeError):f.save(FeedbackSave(draft_id=s['id'],base_version=1,payload=s['payload']))
    assert f.list()['items'][0]==next

def test_M5_A08_exact_export_only_local_metadata_and_no_attachments(domain,monkeypatch):
    _,_,f,_=domain
    import socket, subprocess
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('NETWORK'))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**k:pytest.fail('PROCESS/GIT'))
    s=approve(f,feedback(f,destination='SYNTHETIC product team',description='SYNTHETIC literal ``` <b>data</b>'))
    md=f.export(s['id'],export_req(s));data=json.loads(f.export(s['id'],export_req(s,'json')))
    assert data['approved_exact_copy']==s['exact_copy'];assert data['metadata']['approved_hash']==s['content_hash'];assert data['metadata']['publication']=='NOT_PERFORMED'
    assert data['metadata']['attachments']==[] and data['metadata']['references']==[];assert 'SYNTHETIC product team' in md
    with pytest.raises(ValidationError):FeedbackInput(title='SYNTHETIC',references=[{'entry_id':str(uuid4())}])
    with pytest.raises(ValidationError):FeedbackInput(title='SYNTHETIC',attachments=['audio'])


def test_M5_A10_A11_A12_space_optional_no_progression_CAS_and_durable(domain):
    j,l,f,space=domain;assert not space.get()['state']['enabled'];e=creative(j)
    on=space.update(SpaceUpdate(base_version=0,state={'enabled':True,'theme':'clay'}));assert space.update(SpaceUpdate(base_version=0,state=on['state']))==on
    with pytest.raises(SafeError,match='SPACE_CHANGED'):space.update(SpaceUpdate(base_version=0,state={'enabled':False}))
    off=space.update(SpaceUpdate(base_version=1,state={**on['state'],'enabled':False}));assert off['state']['layout']==on['state']['layout'];assert off['state']['theme']=='clay'
    assert PersonalSpace(Store(j.store.root)).get()==off;assert l.list()['items'][0]==e
    assert f.export((s:=approve(f,feedback(f)))['id'],export_req(s))
    for field in ['streak','last_seen','mood','health_score','reward','disclosures','progress']:
        with pytest.raises(ValidationError):SpaceState(**{field:1})
    assert set(off['state'])=={'enabled','theme','owned_ids','layout'}
    with pytest.raises(ValidationError):SpaceState(layout=['books','books','vase'])


def test_M5_A13_creative_mock_exact_selected_no_memory_inference_stales_accepted(rt):
    rt.set_mode('MOCK');a=entry(rt,kind='creative',creative_kind='theme',creative_meta={'title':'SYNTHETIC'},text='SYNTHETIC fictional post publicly')
    other=entry(rt,kind='creative',text='SYNTHETIC unselected')
    with pytest.raises(SafeError,match='CREATIVE_MEMORY_DENIED'):preview(rt,[a],task='memory_propose')
    assert rt.providers['mock'].executions==0
    p,j,_=execute(rt,[a],task='organize_selected');assert len(p['package']['entries'])==1 and p['package']['entries'][0]['id']==a['id']
    suggestion=rt.suggestions()['items'][0];rt.change_suggestion(suggestion['id'],SuggestionChange(action='accept'))
    assert rt.journal.get(a['id'])['raw_text']=='SYNTHETIC fictional post publicly';assert not rt.memories()['items']
    rt.journal.write('delete',a['id'],Delete(operation_id=uuid4(),base_revision=1))
    assert rt.suggestions()['items'][0]['status']=='STALE';assert rt.journal.get(other['id'])['raw_text']=='SYNTHETIC unselected'


def test_M5_A15_backup_restore_roundtrip_and_approval_invalidated(domain,isolated):
    j,l,f,space=domain;e=creative(j);s=approve(f,feedback(f));on=space.update(SpaceUpdate(base_version=0,state={'enabled':True,'theme':'sage'}))
    backup=isolated/'backup';j.store.backup(backup);assert f.list()['items'][0]['approved']
    restored=Store.restore(backup,isolated/'restored');rj=Journal(restored);rf=Feedback(restored)
    assert rj.get(e['id'])==e;assert PersonalSpace(restored).get()==on
    rs=rf.list()['items'][0];assert not rs['approved'] and rs['content_hash']!=s['content_hash']
    with pytest.raises(SafeError):rf.export(s['id'],export_req(s))
    with pytest.raises(SafeError):approve(rf,s)
    assert approve(rf,rs)['approved']

@pytest.mark.parametrize('cause',['space','feedback','approval','metadata'])
def test_M5_A15_corrupt_new_state_restore_refused_before_target_mutation(domain,isolated,cause):
    j,l,f,space=domain;e=creative(j);feedback(f);space.update(SpaceUpdate(base_version=0,state=SpaceState()))
    backup=isolated/'corrupt';j.store.backup(backup)
    with sqlite3.connect(backup/'snapshot.sqlite3') as c:
        if cause=='space':c.execute("UPDATE personal_space SET state='{}'")
        if cause=='feedback':c.execute("UPDATE feedback_drafts SET payload='{}'")
        if cause=='approval':c.execute("UPDATE feedback_drafts SET approval='{}'")
        if cause=='metadata':
            p=j.get(e['id']);p['creative_meta']['related_ids']=['not-a-uuid'];c.execute('UPDATE entries SET payload=? WHERE id=?',(encode({k:v for k,v in p.items() if k in EntryInput.model_fields}),e['id']))
    m=json.loads((backup/'manifest.json').read_text());m['files']['snapshot.sqlite3']=digest((backup/'snapshot.sqlite3').read_bytes());(backup/'manifest.json').write_text(encode(m))
    target=isolated/'untouched'
    with pytest.raises(SafeError):Store.restore(backup,target)
    assert not target.exists()


def test_M5_A15_migration4_preserves_metadata_audio_schema_and_rolls_back(domain,isolated):
    j,l,f,s=domain;e=creative(j)
    with j.store.connect() as c:
        c.execute('DROP TABLE feedback_drafts');c.execute('DROP TABLE personal_space');c.execute('UPDATE vault_meta SET schema_version=4')
    with pytest.raises(sqlite3.OperationalError):Store(j.store.root,fail_migration=True)
    with j.store.connect() as c:assert c.execute('SELECT schema_version FROM vault_meta').fetchone()[0]==4
    migrated=Store(j.store.root);assert migrated.meta()['schema_version']==SCHEMA;assert Journal(migrated).get(e['id'])==e


def test_M5_A04_A15_shared_M2_metadata_conflict_delete_and_old_backup_epoch(isolated):
    from apps.core.api import create_app
    from test_m2_sync import pairing,packet,apply
    app=create_app(isolated/'mac',m2=True);a=pairing(app);b=pairing(app)
    req=packet(a,text='SYNTHETIC offline creative',type='creative',creative_kind='phrase',creative_meta={'title':'SYNTHETIC offline','collections':['Set']})
    assert apply(app,a,req)['state']=='MAC_CONFIRMED';id=str(req.entry_id)
    backup=isolated/'before-delete';app.state.store.backup(backup)
    stale=packet(b,'edit',id,1,'SYNTHETIC stale phone',type='creative',creative_kind='scene',creative_meta={'collections':['B']})
    app.state.journal.write('edit',id,Patch(operation_id=uuid4(),base_revision=1,changes={'creative_meta':{'title':'SYNTHETIC Mac edit','collections':['A']}}))
    conflict=apply(app,b,stale);assert conflict['state']=='CONFLICT';assert conflict['current']['creative_meta']['collections']==['A']
    app.state.journal.write('delete',id,Delete(operation_id=uuid4(),base_revision=2))
    assert apply(app,a,req)['code']=='DELETED';assert apply(app,b,packet(b,'edit',id,2,'SYNTHETIC resurrection',type='creative'))['code']=='DELETED'
    # Explicit historical restore is a separate new root. It cannot mutate the current tombstones
    # or authorize stale device credentials; old backup content is not a reconciliation merge.
    restored=Store.restore(backup,isolated/'historical');other=create_app(restored.root,m2=True)
    with pytest.raises(SafeError):apply(other,a,req)
    assert not app.state.creative.list()['items'];assert not app.state.journal.list()['items']
