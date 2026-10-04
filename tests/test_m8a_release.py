"""Original synthetic release fixtures; no live inference, hardware or private root."""
import json
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4
import pytest
from apps.core import release as r
from apps.core.storage import Store, SafeError, SCHEMA, REPO, encode, digest
from apps.core.domain import Journal
from apps.core.models import Create, Patch, Delete
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation, SendMessage
from apps.core.conversation_controller import ConversationController, main_question_count, verify_address_form
from apps.core.conversation_runtime_contracts import InferenceStart
from test_m1_domain import isolated, create
from test_m7c_controller import FixtureProvider, finish

@pytest.fixture
def package(isolated):
    # Fixture identity is explicitly synthetic, never the reported real release build.
    p=isolated/'ORIGINAL SYNTHETIC package';p.mkdir()
    for directory in ('apps/core','skills/conversation','research/admission','packages/practices/synthetic'):
        shutil.copytree(REPO/directory,p/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('requirements.lock','apps/web/package-lock.json','scripts/m7_admission.py','apps/web/src/PracticePanel.tsx','apps/web/src/practice-model.ts','apps/web/src/style.css'):
        dst=p/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,dst)
    shutil.copytree(REPO/'apps/web/dist',p/'apps/web/dist')
    (p/'launch.py').write_text('ORIGINAL_SYNTHETIC_TEST_ONLY=1\n')
    m={'format':1,'release_id':'M8A-'+'a'*40,'git_commit':'a'*40,'schema_version':SCHEMA,
       'python_input_hash':digest((p/'requirements.lock').read_bytes()),'web_lock_hash':digest((p/'apps/web/package-lock.json').read_bytes()),
       'platform':{'os':'Darwin','architecture':'arm64','python':'3.13','dependencies':'EXACT_REQUIREMENTS_LOCK','self_contained':False},
       'defaults':r.DEFAULTS,'compatibility':{'schema_min':2,'schema_max':SCHEMA,'web_contract':r.CONTRACT,'downgrade':'FRESH_ROOT_BACKUP_ONLY'},'files':r.file_hashes(p)}
    m['manifest_hash']=r.identity(m);(p/'release-manifest.json').write_text(encode(m))
    return p,m['manifest_hash']

def paths(isolated): return isolated/'Застосунок з пробілом', isolated/'Синтетичні дані з пробілом'

def domains(data):
    j=Journal(Store(data)); entry,_=create(j,text='ORIGINAL SYNTHETIC journal')
    j.write('edit',entry.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC journal revision'}))
    creative,_=create(j,'creative',text='ORIGINAL SYNTHETIC creative',creative_kind='idea')
    deleted,_=create(j,text='ORIGINAL SYNTHETIC deleted');j.write('delete',deleted.entry_id,Delete(operation_id=uuid4(),base_revision=1))
    conv=Conversations(j.store,True);page=conv.create(NewConversation(operation_id=uuid4()))
    conv.send(page['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC conversation'),respond=False)
    return str(entry.entry_id),str(creative.entry_id),str(deleted.entry_id),page['conversation']['id']

def assert_domains(data,ids):
    j=Journal(Store(data));assert j.get(ids[0])['raw_text']=='ORIGINAL SYNTHETIC journal revision'
    assert len(j.history(ids[0])['items'])==1 and j.get(ids[1])['creative_kind']=='idea'
    with j.store.connect() as c:
        assert c.execute('SELECT count(*) FROM tombstones WHERE entry_id=?',(ids[2],)).fetchone()[0]==1
        assert c.execute('SELECT count(*) FROM conversation_messages WHERE conversation_id=?',(ids[3],)).fetchone()[0]==1
        assert not c.execute('SELECT count(*) FROM ai_consents WHERE revoked=0 AND approved=1').fetchone()[0]


def test_identity_and_corrupt_hash(package):
    p,h=package;assert r.validate_package(p,h)['schema_version']==11
    with pytest.raises(SafeError,match='RELEASE_INTEGRITY'):r.validate_package(p,'0'*64)
    (p/'apps/web/dist/index.html').write_text('CORRUPT ORIGINAL SYNTHETIC')
    with pytest.raises(SafeError,match='RELEASE_INTEGRITY'):r.validate_package(p,h)

@pytest.mark.parametrize('mutation',['future','duplicate','unsafe_defaults','missing_asset','unknown_file','wrong_lock'])
def test_package_negative_metadata(package,mutation):
    p,h=package;m=r.read_json(p/'release-manifest.json')
    if mutation=='future':m['schema_version']=999
    if mutation=='unsafe_defaults':m['defaults']=dict(r.DEFAULTS,provider='ON')
    if mutation=='missing_asset':(p/'apps/web/dist/index.html').unlink()
    if mutation=='unknown_file':(p/'secret-extra.txt').write_text('ORIGINAL SYNTHETIC')
    if mutation=='wrong_lock':m['python_input_hash']='0'*64
    if mutation=='duplicate':(p/'release-manifest.json').write_text('{"format":1,"format":1}')
    else:
        m['manifest_hash']=r.identity(m);(p/'release-manifest.json').write_text(encode(m));h=m['manifest_hash']
    with pytest.raises(SafeError):r.validate_package(p,h)


def test_fresh_install_backup_restore_uninstall(package,isolated):
    p,h=package;app,data=paths(isolated)
    assert r.preflight(p,h,app,data)['status']=='PASS'
    assert r.install(p,h,app,data)['defaults']==r.DEFAULTS
    ids=domains(data);before=digest((data/'journal.sqlite3').read_bytes())
    assert r.selected(app,data)[1]['manifest_hash']==h
    r.backup(app,data,isolated/'consistent backup')
    assert digest((data/'journal.sqlite3').read_bytes())==before
    app2,data2=isolated/'restored app',isolated/'restored data'
    assert r.restore(p,h,isolated/'consistent backup',app2,data2)['defaults']==r.DEFAULTS
    assert_domains(data2,ids)
    # Runtime replacement/removal cannot erase data or backup.
    r.uninstall(app,data);assert not app.exists() and data.exists()
    assert_domains(data,ids);assert (isolated/'consistent backup').is_dir()
    with pytest.raises(SafeError,match='EXPLICIT_DATA_DELETE'):r.delete_synthetic_data(data,'DELETE')
    r.delete_synthetic_data(data,'DELETE_SYNTHETIC_DATA:'+str(data));assert not data.exists()
    assert (isolated/'consistent backup').exists()

@pytest.mark.parametrize('schema',[2,10,11])
def test_upgrade_backup_then_migration(package,isolated,schema):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    # Synthetic prior schema fixture. 2/10 integrity is validated against accepted Store checks.
    with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=?',(schema,))
    out=r.upgrade(p,h,app,data,isolated/'pre-upgrade')
    assert out['schema_from']==schema and out['schema_to']==11
    assert r.read_json(isolated/'pre-upgrade/manifest.json')['schema_version']==schema
    assert_domains(data,ids);assert not (app/'upgrade-pending.json').exists()
    app2,data2=isolated/'rollback app',isolated/'rollback data'
    r.restore(p,h,isolated/'pre-upgrade',app2,data2)
    assert_domains(data2,ids);assert r.inspect_data(data2)==11


def test_migration_failure_preserves_state_and_backup(package,isolated):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=10')
    before=r.read_json(app/'active.json')
    with pytest.raises(sqlite3.OperationalError):r.upgrade(p,h,app,data,isolated/'failure backup',fail_migration=True)
    assert r.inspect_data(data)==10 and r.read_json(app/'active.json')==before
    assert (app/'upgrade-pending.json').exists()
    with pytest.raises(SafeError,match='UPGRADE_RECOVERY_REQUIRED'):r.serve(app,data,8871)
    r.restore(p,h,isolated/'failure backup',isolated/'safe rollback app',isolated/'safe rollback data')
    assert_domains(isolated/'safe rollback data',ids)

@pytest.mark.parametrize('problem',['future','corrupt','asset','target','wrong_hash'])
def test_upgrade_preflight_never_mutates_data(package,isolated,problem):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data);domains(data)
    if problem=='future':
        with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=999')
    if problem=='corrupt':(data/'synthetic.json').write_text('corrupt')
    if problem=='asset':(p/'apps/web/dist/index.html').unlink()
    target=isolated/'blocked backup'
    if problem=='target':target.write_text('ORIGINAL SYNTHETIC existing target')
    if problem=='wrong_hash':h='0'*64
    before=(data/'journal.sqlite3').read_bytes()
    with pytest.raises((SafeError,OSError)):r.upgrade(p,h,app,data,target)
    assert (data/'journal.sqlite3').read_bytes()==before
    assert not (app/'upgrade-pending.json').exists()


def test_restore_cannot_overwrite_unrelated_root(package,isolated):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data)
    r.backup(app,data,isolated/'backup');other=isolated/'unrelated';other.mkdir();(other/'keep').write_text('ORIGINAL SYNTHETIC')
    with pytest.raises(SafeError):r.restore(p,h,isolated/'backup',isolated/'fresh app',other)
    assert (other/'keep').read_text()=='ORIGINAL SYNTHETIC'
    (isolated/'backup/snapshot.sqlite3').write_bytes(b'corrupt')
    with pytest.raises(SafeError,match='CHECKSUM_MISMATCH'):r.restore(p,h,isolated/'backup',isolated/'another app',isolated/'another data')
    assert not (isolated/'another app').exists() and not (isolated/'another data').exists()


def test_path_separation_busy_lock_optional_runtime(package,isolated):
    p,h=package;app,data=paths(isolated)
    with pytest.raises(SafeError,match='APP_DATA_OVERLAP'):r.install(p,h,app,app/'vault')
    with r.operation_lock(data):
        with pytest.raises(SafeError,match='DATA_ROOT_BUSY'):r.install(p,h,app,data)
    result=r.preflight(p,h,app,data)
    assert {'gate':'local_asr','status':'OPTIONAL_UNAVAILABLE','reason':'NO_WEIGHTS_OR_ENGINE_PACKAGED'} in result['checks']
    assert not app.exists() and not data.exists()

@pytest.mark.parametrize('text,count',[
 ('Варіант 1: «Чи зручно поговорити?» — пряме запрошення.\nВаріант 2: «Чи повернемося до цього завтра?» — відкладена розмова.\nЯкий формат вам ближчий?',1),
 ('Приклад: "Що зараз потрібно?". Можна спершу порівняти обидва варіанти.',0),
 ('«Що потрібно?» «Чого хочете?»',2),
 ('Що потрібно?\nЯкий крок оберете?',2),
 ('Варіант 1: «Чи поговоримо?»\nЩо потрібно? Чого хочете?',2),
 ('Цитата «давно?» з історії. Що змінилося??',1),
 ('> давно?\nЩо змінилося?',1),
 ('> Невідоме питання?\nЩо змінилося?',2),
])
def test_options_and_quoted_question_guard(text,count):
    assert main_question_count(text,{'context':[{'text':'ORIGINAL SYNTHETIC давно?'}]})==count


def test_options_comparison_through_controller_and_register(isolated):
    class Options(FixtureProvider):
        def execute(self,payload,*args):
            self.payload=payload;result=super().execute(payload,*args);value=json.loads(result['text'])
            value['assistant_text']='Варіант 1: «Чи поговоримо зараз?» — прямий.\nВаріант 2: «Чи повернемося завтра?» — дає час.\nЯкий формат вам ближчий?'
            result['text']=encode(value);return result
    provider=Options();c=ConversationController(Conversations(Store(isolated/'options'),True),provider)
    page=c.conversations.create(NewConversation(operation_id=uuid4()))
    turn=c.send(page['conversation']['id'],InferenceStart(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC Порівняйте кілька варіантів розмови, не обираючи за мене.',synthetic_test_ack=True))
    assert finish(c,turn['inference_job']['id'])['state']=='COMPLETED' and provider.payload['address_form']=='FORMAL_VY'
    verify_address_form('Ви сказали «ти можеш». Що вам важливо?',{'context':[{'text':'ти можеш'}]})
    with pytest.raises(SafeError,match='ADDRESS_FORM_MISMATCH'):verify_address_form('Що ти хочеш?',{})
    with pytest.raises(SafeError,match='ADDRESS_FORM_MISMATCH'):verify_address_form('Чого тобі хочеться?',{})


def test_api_compatibility_fails_before_auth_and_mutation(isolated):
    from fastapi.testclient import TestClient
    from apps.core.api import create_app
    app=create_app(isolated/'compatibility',release_identity='a'*40)
    with TestClient(app,base_url='http://127.0.0.1:8765') as client:
        result=client.get('/release.json');assert result.json()['git_commit']=='a'*40
        response=client.post('/api/v1/auth/unlock',json={'code':app.state.auth.code},headers={'Origin':'http://127.0.0.1:8765'})
        assert response.status_code==409 and response.json()['code']=='FRONTEND_UPDATE_REQUIRED'
        assert app.state.auth.code is not None
        response=client.post('/api/v1/auth/unlock',json={'code':app.state.auth.code},headers={'Origin':'http://127.0.0.1:8765','X-PC-Build':'a'*40})
        assert response.status_code==200
        assert not app.state.journal.list()['items']


def test_genuine_schema2_without_newer_tables_upgrades_and_restores(package,isolated):
    from apps.core.storage import TABLES,SYNC_TABLES,MARKER,now
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data)
    (data/'journal.sqlite3').unlink()
    with sqlite3.connect(data/'journal.sqlite3') as c:
        c.execute('CREATE TABLE vault_meta(vault_id TEXT,owner_id TEXT,schema_version INTEGER,restore_epoch INTEGER,created_at_utc TEXT,reconciliation TEXT)')
        c.execute('INSERT INTO vault_meta VALUES(?,?,2,0,?,?)',(str(uuid4()),str(uuid4()),now(),'NONE'))
        for sql in TABLES+SYNC_TABLES:c.execute(sql)
        c.execute('INSERT INTO sync_meta VALUES(1,?,0)',(str(uuid4()),))
    j=Journal(r.old_store(data));entry,_=create(j,text='ORIGINAL SYNTHETIC actual schema2')
    r.upgrade(p,h,app,data,isolated/'genuine old schema backup')
    assert Journal(Store(data)).get(str(entry.entry_id))['raw_text']=='ORIGINAL SYNTHETIC actual schema2'
    r.restore(p,h,isolated/'genuine old schema backup',isolated/'old restored app',isolated/'old restored data')
    assert Journal(Store(isolated/'old restored data')).get(str(entry.entry_id))['raw_text']=='ORIGINAL SYNTHETIC actual schema2'


def test_interrupted_backup_does_not_publish_final_target(package,isolated,monkeypatch):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    from apps.core import voice
    def fail(_):raise OSError('ORIGINAL SYNTHETIC fsync failure')
    monkeypatch.setattr(voice,'fsync_dir',fail)
    with pytest.raises(OSError):r.backup(app,data,isolated/'interrupted backup')
    assert not (isolated/'interrupted backup').exists()
    assert not list(isolated.glob('interrupted backup.partial-*'))
    assert_domains(data,ids)


def test_address_switch_fails_before_assistant_commit(isolated):
    class Switching(FixtureProvider):
        def execute(self,payload,*args):
            result=super().execute(payload,*args);value=json.loads(result['text'])
            value['assistant_text']='Що тобі хотілося б зрозуміти?';result['text']=encode(value);return result
    c=ConversationController(Conversations(Store(isolated/'register'),True),Switching())
    page=c.conversations.create(NewConversation(operation_id=uuid4()))
    result=c.send(page['conversation']['id'],InferenceStart(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC register',synthetic_test_ack=True))
    job=finish(c,result['inference_job']['id'])
    assert job['state']=='FAILED' and job['error']=='ADDRESS_FORM_MISMATCH'
    assert len(c.conversations.get(page['conversation']['id'])['messages'])==1


def test_release_restore_preserves_memory_and_rejected_map_provenance(package,isolated):
    from test_m7d_deep import MapProvider,turn
    from apps.core.reflection_contracts import GoalCreate
    from apps.core.deep_session_contracts import MapAction
    from apps.core.runtime import Runtime
    from apps.core.ai_contracts import MemoryCreate
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data)
    store=Store(data);controller=ConversationController(Conversations(store,True),MapProvider())
    goal=controller.context.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC paper garden',user_agreed=True))
    page=controller.conversations.create(NewConversation(operation_id=uuid4(),goal_id=goal['id'],goal_revision=1))
    result,_,_=turn(controller,page);assert result['state']=='COMPLETED'
    working=controller.deep.read(page['conversation']['id'])['map']
    hypothesis=next(i for i in working['items'] if i['kind']=='HYPOTHESIS')
    controller.deep.action(page['conversation']['id'],MapAction(operation_id=uuid4(),base_version=working['version'],item_id=hypothesis['id'],action='reject',user_confirmed=True))
    original=controller.deep.read(page['conversation']['id'])['map']
    memory=Runtime(Journal(store),autostart=False).create_memory(MemoryCreate(content='ORIGINAL SYNTHETIC preference'))
    original_memory=next(m for m in Runtime(Journal(store),autostart=False).memories()['items'] if m['id']==memory['id'])
    r.backup(app,data,isolated/'provenance backup')
    r.restore(p,h,isolated/'provenance backup',isolated/'provenance app',isolated/'provenance data')
    restored=Store(isolated/'provenance data')
    other=ConversationController(Conversations(restored,True))
    current=other.deep.read(page['conversation']['id'])['map']
    assert current['items']==original['items'] and current['version']==original['version']
    assert any(i['state']=='REJECTED' and i['sources'] for i in current['items'])
    rt=Runtime(Journal(restored),autostart=False)
    saved=next(m for m in rt.memories()['items'] if m['id']==memory['id'])
    assert saved['content']==original_memory['content'] and saved['provenance']==original_memory['provenance']
    assert rt.mode=='OFF' and other.provider is None


def test_stable_address_contract_on_two_turns_and_restart(isolated):
    class TwoTurns(FixtureProvider):
        def __init__(self):super().__init__();self.policies=[]
        def execute(self,payload,*args):
            self.policies.append(payload['address_form'])
            result=super().execute(payload,*args);value=json.loads(result['text'])
            value['assistant_text']='Що вам важливо?' if self.calls==1 else 'Що тобі важливо?'
            result['text']=encode(value);return result
    store=Store(isolated/'stable register');provider=TwoTurns()
    c=ConversationController(Conversations(store,True),provider)
    page=c.conversations.create(NewConversation(operation_id=uuid4()));id=page['conversation']['id']
    for revision,expected in [(1,'COMPLETED'),(3,'FAILED')]:
        result=c.send(id,InferenceStart(operation_id=uuid4(),base_revision=revision,text='ORIGINAL SYNTHETIC register turn',synthetic_test_ack=True))
        assert finish(c,result['inference_job']['id'])['state']==expected
    assert provider.policies==['FORMAL_VY','FORMAL_VY']
    assert len(c.conversations.get(id)['messages'])==3
    restarted=ConversationController(Conversations(Store(store.root),True))
    assert restarted.provider is None and restarted.skills.read('core_reflection')['version']=='2.1.0'


def test_packaged_legacy_messages_never_enable_mock_response(isolated):
    from fastapi.testclient import TestClient
    from apps.core.api import create_app
    app=create_app(isolated/'packaged OFF',release_identity='a'*40,synthetic_conversations=True,m7c_synthetic=True)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Origin':'http://127.0.0.1:8765','X-PC-Build':'a'*40}) as client:
        unlock=client.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});client.headers['X-CSRF-Token']=unlock.json()['csrf_token']
        page=client.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json()
        assert page['responder']=='OFF'
        sent=client.post('/api/v1/conversations/'+page['conversation']['id']+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC no hidden mock response'}).json()
        assert sent['responder']=='OFF' and len(sent['messages'])==1 and sent['messages'][0]['role']=='USER'
        assert client.get('/api/v1/conversations/status').json()['responder']=='OFF'
    with pytest.raises(SafeError,match='RELEASE_CAPABILITY_OFF'):
        create_app(isolated/'denied provider',release_identity='a'*40,conversation_provider=FixtureProvider(),m7c_synthetic=True,synthetic_conversations=True)


def test_application_replacement_then_failed_migration_old_fixture_rollback(package,isolated):
    p,h=package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    next_package=isolated/'ORIGINAL SYNTHETIC second package';shutil.copytree(p,next_package)
    marker=next_package/'SYNTHETIC_VARIANT.txt';marker.write_text('ORIGINAL_SYNTHETIC_INSTALL_SIMULATION_NOT_A_PUBLISHED_COMMIT')
    m=r.read_json(next_package/'release-manifest.json');m['git_commit']='b'*40;m['release_id']='M8A-'+'b'*40;m['files']=r.file_hashes(next_package);m['manifest_hash']=r.identity(m)
    (next_package/'release-manifest.json').write_text(encode(m))
    old_pointer=r.read_json(app/'active.json')
    with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=10')
    with pytest.raises(sqlite3.OperationalError):r.upgrade(next_package,m['manifest_hash'],app,data,isolated/'replacement backup',fail_migration=True)
    assert r.read_json(app/'active.json')==old_pointer and len(list((app/'releases').iterdir()))==2
    assert r.inspect_data(data)==10
    r.restore(p,h,isolated/'replacement backup',isolated/'old application root',isolated/'rollback domain root',expected_producer_hash=m['manifest_hash'])
    assert_domains(isolated/'rollback domain root',ids)
    assert r.selected(isolated/'old application root',isolated/'rollback domain root')[1]['manifest_hash']==h
