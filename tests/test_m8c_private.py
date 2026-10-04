"""Production PRIVATE_LOCAL semantics exercised only with ORIGINAL SYNTHETIC content.
Native volume handling is deterministic here; actual-Mac evidence uses unmocked probes.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from apps.core import release as r, local_private as p
from apps.core.root_types import RootKind
from apps.core.storage import Store, SafeError, REPO, encode, digest
from apps.core.domain import Journal
from apps.core.models import Patch, Delete
from apps.core.api import create_app
from test_m1_domain import isolated, create
from test_m8a_release import package
from test_m8b_readiness import runtime_package

KIND=RootKind.PRIVATE_LOCAL

@pytest.fixture
def private_package(runtime_package):
    pkg,_=runtime_package
    shutil.copyfile(REPO/'packages/pilot/MAC_PRIVATE_CORE_PROFILE.json',pkg/'packages/pilot/MAC_PRIVATE_CORE_PROFILE.json')
    m=r.read_json(pkg/'release-manifest.json');m.update(format=3,release_id='M8C-'+m['git_commit'])
    m['files']=r.file_hashes(pkg);m['manifest_hash']=r.identity(m)
    (pkg/'release-manifest.json').write_text(encode(m))
    return pkg,m['manifest_hash']

@pytest.fixture
def protected(monkeypatch):
    monkeypatch.setattr(p,'volume_protection',lambda path:'PASS')


def args(root, backup_dir):
    return dict(root_kind=KIND,backup_directory=backup_dir,confirmation='INITIALIZE_PRIVATE_LOCAL:'+str(root),consent=p.CONSENT,acknowledge_no_cloud=True)

@pytest.fixture
def vault(private_package,isolated,protected):
    pkg,h=private_package; app,data,backups=isolated/'app',isolated/'PRIVATE_LOCAL_WITH_SYNTHETIC_CONTENT',isolated/'protected backups'
    backups.mkdir(mode=0o700)
    r.initialize_private(pkg,h,app,data,backups,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True)
    return pkg,h,app,data,backups


def test_distinct_kind_durable_binding_and_provenance(vault):
    pkg,h,app,data,b=vault
    assert not (data/'synthetic.json').exists()
    assert p.validate_root(data)['root_kind']=='PRIVATE_LOCAL'
    for _ in range(2):
        store=Store(data,root_kind=KIND);j=Journal(store)
        req,_=create(j,text='ORIGINAL SYNTHETIC M8C personal-path fixture')
        assert j.get(str(req.entry_id))['privacy_class']=='PRIVATE_PERSONAL'
        assert j.get(str(req.entry_id))['provenance_type']=='USER_REPORTED'
    with pytest.raises(SafeError):Store(data)
    with pytest.raises(SafeError):r.inspect_data(data)
    with pytest.raises(SafeError):r.selected(app,data)
    # One loose marker/flag cannot relabel the DB as synthetic.
    (data/'private-local.json').unlink();(data/'synthetic.json').write_text(encode(r.MARKER));os.chmod(data/'synthetic.json',0o600)
    with pytest.raises(SafeError,match='ROOT_KIND_MISMATCH'):Store(data)

@pytest.mark.parametrize('mutation',['kind','uuid','consent','profile','duplicate','db','unknown'])
def test_corrupt_receipt_fail_closed(vault,mutation):
    _,_,_,data,_=vault
    marker=data/'private-local.json';v=r.read_json(marker)
    if mutation=='kind':v['root_kind']='SYNTHETIC_TEST'
    if mutation=='uuid':v['root_id']='bad'
    if mutation=='consent':v['data_owner_acknowledged']=False
    if mutation=='profile':v['profile_id']='AI_ON'
    if mutation=='unknown':v['unknown']=True
    if mutation=='duplicate':marker.write_text('{"format":1,"format":1}')
    elif mutation=='db':
        with sqlite3.connect(data/'journal.sqlite3') as c:c.execute("UPDATE private_root_identity SET payload='{}'")
    else:marker.write_text(encode(v))
    with pytest.raises(SafeError):Store(data,root_kind=KIND)

@pytest.mark.parametrize('confirmation,consent,ack',[('no',p.CONSENT,True),(None,p.CONSENT,True),('exact','no',True),('exact',p.CONSENT,False)])
def test_explicit_init_required(private_package,isolated,protected,confirmation,consent,ack):
    pkg,h=private_package;data=isolated/'new data';b=isolated/'backups';b.mkdir(mode=0o700)
    if confirmation=='exact':confirmation='INITIALIZE_PRIVATE_LOCAL:'+str(data)
    with pytest.raises(SafeError,match='CONSENT_REQUIRED'):r.initialize_private(pkg,h,isolated/'app',data,b,confirmation,consent,ack)
    assert not data.exists() and not (isolated/'app').exists()
    with pytest.raises(SafeError,match='EXPLICIT_PRIVATE_INITIALIZATION_REQUIRED'):Store(data,root_kind=KIND)


def test_empty_existing_target_and_unknown_root(private_package,isolated,protected):
    pkg,h=private_package;b=isolated/'backups';b.mkdir(mode=0o700)
    root=isolated/'empty';root.mkdir(mode=0o700)
    r.initialize_private(pkg,h,isolated/'app',root,b,'INITIALIZE_PRIVATE_LOCAL:'+str(root),p.CONSENT,True)
    unknown=isolated/'unknown';unknown.mkdir(mode=0o700);(unknown/'content').write_text('ORIGINAL SYNTHETIC UNKNOWN')
    with pytest.raises(SafeError):r.initialize_private(pkg,h,isolated/'app2',unknown,b,'INITIALIZE_PRIVATE_LOCAL:'+str(unknown),p.CONSENT,True)
    assert not (isolated/'app2').exists()

@pytest.mark.parametrize('target',['data','backup'])
@pytest.mark.parametrize('status',['NOT_RUN','BLOCKED_BY_PERMISSION','SECURITY_REQUIREMENT_NOT_MET'])
def test_unverified_volume_fails_before_init(private_package,isolated,monkeypatch,target,status):
    pkg,h=private_package;data=isolated/'data';b=isolated/'backup';b.mkdir(mode=0o700)
    monkeypatch.setattr(p,'volume_protection',lambda path:status if str(path)==str(data if target=='data' else b) else 'PASS')
    report=p.preflight(pkg,h,isolated/'app',data,b);assert report['status']==status
    assert p.readiness(report,True)['MAC_CORE_PILOT']=='NOT_READY'
    with pytest.raises(SafeError):r.initialize_private(pkg,h,isolated/'app',data,b,'INITIALIZE_PRIVATE_LOCAL:'+str(data),p.CONSENT,True)
    assert not data.exists() and not (isolated/'app').exists()

@pytest.mark.parametrize('mode',[0o770,0o777,0o750])
def test_permissions_not_silently_fixed(vault,mode):
    _,_,_,data,_=vault;os.chmod(data,mode)
    with pytest.raises(SafeError,match='OWNER_ONLY_PERMISSIONS'):Store(data,root_kind=KIND)
    assert data.stat().st_mode & 0o777==mode
    os.chmod(data,0o700)


def test_unsafe_paths_and_wrong_synthetic_root(private_package,isolated,protected):
    pkg,h=private_package;b=isolated/'b';b.mkdir(mode=0o700)
    s=isolated/'synthetic';Store(s)
    with pytest.raises(SafeError):Store(s,root_kind=KIND)
    with pytest.raises(SafeError):p.preflight(pkg,h,isolated/'app',s,b)
    link=isolated/'link';link.symlink_to(s,target_is_directory=True)
    for path in [link,REPO/'private-test-forbidden',isolated/'x/../unsafe',isolated/'CloudStorage/vault']:
        with pytest.raises(SafeError):p.preflight(pkg,h,isolated/'app',path,b)


def test_preflight_schema_rejects_identifiers_and_receipt_not_public(vault):
    pkg,h,app,data,b=vault;report=p.preflight(pkg,h,app,data,b)
    assert report['status']=='PASS' and report['application_level_backup_encryption']=='NOT_IMPLEMENTED'
    assert not any(x in encode(report) for x in [str(data),str(b),'username','account','root_id'])
    for k in ['username','private_path','serial','consent']:
        with pytest.raises(ValidationError):p.PrivatePreflight.model_validate(dict(report,**{k:'ORIGINAL_SYNTHETIC'}))


def client_for(data, clock=None):
    app=create_app(data,root_kind=KIND,release_identity='a'*40,**({'clock':clock} if clock else {}))
    client=TestClient(app,base_url='http://127.0.0.1:8765',raise_server_exceptions=False)
    client.headers.update({'Origin':'http://127.0.0.1:8765','X-PC-Build':'a'*40})
    return app,client


def unlock(app,c):
    response=c.post('/api/v1/auth/unlock',json={'code':app.state.auth.code});assert response.status_code==200
    cookie=response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie and 'max-age' not in cookie and 'expires=' not in cookie
    c.headers['X-CSRF-Token']=response.json()['csrf_token']


def test_private_crud_search_auth_lock_restart(vault):
    _,_,_,data,_=vault;t=[0];app,c=client_for(data,lambda:t[0])
    with c:
        assert c.get('/api/v1/entries').status_code==401
        assert c.get('/runtime-mode.json').json()=={'root_kind':'PRIVATE_LOCAL'}
        unlock(app,c)
        req,_=create(app.state.journal,'creative',text='ORIGINAL SYNTHETIC private creative',creative_kind='idea',creative_meta={'title':'ORIGINAL SYNTHETIC idea'})
        id=str(req.entry_id)
        assert c.get('/api/v1/creative',params={'q':'private creative'}).json()['items']
        assert c.get('/api/v1/entries/'+id).json()['privacy_class']=='PRIVATE_PERSONAL'
        assert c.patch('/api/v1/entries/'+id,json={'operation_id':str(uuid4()),'base_revision':1,'changes':{'raw_text':'ORIGINAL SYNTHETIC revision'}}).status_code==200
        assert c.get('/api/v1/entries',params={'q':'revision'}).json()['items']
        assert c.get('/api/v1/status').json()['capabilities']==p.PROFILE
        token=c.cookies['m1_session']; t[0]=900
        assert c.get('/api/v1/entries').status_code==401
        app2,c2=client_for(data)
        with c2:
            c2.cookies.set('m1_session',token)
            assert c2.get('/api/v1/entries').status_code==401
            c2.cookies.clear();unlock(app2,c2)
            assert c2.get('/api/v1/entries/'+id).json()['raw_text']=='ORIGINAL SYNTHETIC revision'
            assert c2.post('/api/v1/auth/lock',json={}).status_code==200
            assert c2.get('/api/v1/entries').status_code==401
    assert token.encode() not in (data/'journal.sqlite3').read_bytes()

@pytest.mark.parametrize('path',['ai/mode','conversations','health/import','practices/start','sync/invitations','device/pair','voice/audio','feedback','external-embeddings','future-optional-capability','entries/future-optional-capability'])
def test_forbidden_capability_requests_with_provider_env(vault,monkeypatch,path):
    for name in ['OPENAI_API_KEY','MINIMAX_API_KEY','PC_CONVERSATION_PROVIDER','PC_LOCAL_ASR','PC_HEALTH_BRIDGE']:
        monkeypatch.setenv(name,'ORIGINAL_SYNTHETIC_NOT_A_KEY_OR_AUTH')
    _,_,_,data,_=vault;app,c=client_for(data)
    with c:
        unlock(app,c);response=c.post('/api/v1/'+path,json={'mode':'ON'})
        assert response.status_code==403
        assert app.state.runtime.mode=='OFF' and app.state.conversation_controller is None
        assert c.get('/phone/').status_code==403
        with pytest.raises(SafeError,match='PRIVATE_CORE_CAPABILITY_OFF'):app.state.runtime.set_mode('mock')

@pytest.mark.parametrize('capability',['conversation_provider','local_asr','m2','synthetic_practices','synthetic_conversations','m7c_synthetic'])
def test_private_factory_cannot_activate_optional_modules(vault,capability):
    _,_,_,data,_=vault
    with pytest.raises(SafeError,match='PRIVATE_CORE_CAPABILITY_OFF'):create_app(data,root_kind=KIND,release_identity='a'*40,**{capability:object()})


def test_backup_restore_upgrade_rollback_keep_data(vault,isolated):
    pkg,h,app,data,b=vault;j=Journal(Store(data,root_kind=KIND));req,_=create(j,text='ORIGINAL SYNTHETIC durable private test')
    j.write('edit',req.entry_id,Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'ORIGINAL SYNTHETIC durable revision'}))
    deleted,_=create(j);j.write('delete',deleted.entry_id,Delete(operation_id=uuid4(),base_revision=1))
    target=b/'backup';receipt=r.backup(app,data,target,root_kind=KIND)
    metadata=r.verify_backup(target,h,receipt['backup_manifest_hash'])
    assert metadata['backup_format']==4 and metadata['security_policy']==p.POLICY
    assert metadata['release_provenance']['private_identity']['root_kind']=='PRIVATE_LOCAL'
    restored=isolated/'restored';a2=isolated/'restored app'
    r.restore(pkg,h,target,a2,restored,**args(restored,b))
    assert p.validate_root(restored)['root_id']!=p.validate_root(data)['root_id']
    j2=Journal(Store(restored,root_kind=KIND));assert j2.get(str(req.entry_id))['raw_text']=='ORIGINAL SYNTHETIC durable revision'
    assert len(j2.history(str(req.entry_id))['items'])==1
    with j2.store.connect() as c:assert c.execute('SELECT count(*) FROM tombstones').fetchone()[0]==1
    r.upgrade(pkg,h,a2,restored,b/'upgrade backup',root_kind=KIND)
    rolled=isolated/'rollback';r.restore(pkg,h,target,isolated/'rollback app',rolled,**args(rolled,b))
    assert Journal(Store(rolled,root_kind=KIND)).get(str(req.entry_id))['provenance_type']=='USER_REPORTED'
    r.uninstall(app,data,root_kind=KIND);assert data.exists() and target.exists() and not app.exists()
    with pytest.raises(SafeError):r.delete_private_data(data,'DELETE')
    with pytest.raises(SafeError):r.delete_synthetic_data(data,'DELETE_SYNTHETIC_DATA:'+str(data))
    r.delete_private_data(data,'DELETE_PRIVATE_LOCAL_DATA:'+str(data));assert not data.exists() and target.exists()

@pytest.mark.parametrize('direction',['private_to_synthetic','synthetic_to_private'])
def test_cross_mode_restore_before_target_creation(vault,isolated,direction):
    pkg,h,app,data,b=vault
    if direction=='private_to_synthetic':
        target=b/'backup';r.backup(app,data,target,root_kind=KIND);kwargs={}
    else:
        sa,sd=isolated/'synthetic app',isolated/'synthetic data';r.install(pkg,h,sa,sd)
        target=isolated/'synthetic backup';r.backup(sa,sd,target);kwargs=args(isolated/'new data',b)
    with pytest.raises(SafeError,match='ROOT_KIND_MISMATCH'):r.restore(pkg,h,target,isolated/'new app',isolated/'new data',**kwargs)
    assert not (isolated/'new app').exists() and not (isolated/'new data').exists()

@pytest.mark.parametrize('mutation',['kind','policy','producer','root_receipt','snapshot_identity'])
def test_tampered_private_backup_before_roots(vault,isolated,mutation):
    pkg,h,app,data,b=vault;target=b/'backup';r.backup(app,data,target,root_kind=KIND)
    m=r.read_json(target/'manifest.json')
    if mutation=='kind':m['root_kind']='SYNTHETIC_TEST'
    if mutation=='policy':m['security_policy']='NONE'
    if mutation=='producer':m['release_provenance']['producing_manifest']['manifest_hash']='0'*64
    if mutation=='root_receipt':m['release_provenance']['private_identity']['root_id']=str(uuid4())
    if mutation=='snapshot_identity':
        with sqlite3.connect(target/'snapshot.sqlite3') as c:c.execute("UPDATE private_root_identity SET payload='{}'")
        m['files']['snapshot.sqlite3']=digest((target/'snapshot.sqlite3').read_bytes())
    (target/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError):r.restore(pkg,h,target,isolated/'rejected app',isolated/'rejected data',**args(isolated/'rejected data',b))
    assert not (isolated/'rejected app').exists() and not (isolated/'rejected data').exists()


def test_backup_protection_rechecked_and_directory_explicit(vault,isolated,monkeypatch):
    _,_,app,data,b=vault
    with pytest.raises(SafeError,match='EXPLICIT_BACKUP_DIRECTORY'):r.backup(app,data,isolated/'elsewhere',root_kind=KIND)
    monkeypatch.setattr(p,'volume_protection',lambda path:'NOT_RUN' if str(path)==str(b) else 'PASS')
    with pytest.raises(SafeError,match='VOLUME_PROTECTION'):r.backup(app,data,b/'denied',root_kind=KIND)
    assert not (b/'denied').exists()
    with pytest.raises(SafeError):Store(data,root_kind=KIND).backup(b/'generic denied')


def test_failed_upgrade_keeps_pointer_backup_and_transaction(vault):
    pkg,h,app,data,b=vault;before=r.read_json(app/'active.json')
    with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=10')
    with pytest.raises(sqlite3.Error):r.upgrade(pkg,h,app,data,b/'failure backup',root_kind=KIND,fail_migration=True)
    assert r.read_json(app/'active.json')==before and (app/'upgrade-pending.json').exists()
    assert r.verify_backup(b/'failure backup',h)['schema_version']==10
    with sqlite3.connect(data/'journal.sqlite3') as c:assert c.execute('SELECT schema_version FROM vault_meta').fetchone()[0]==10


def test_native_probe_status_sanitization(monkeypatch,isolated):
    import plistlib
    monkeypatch.setattr(p.platform,'system',lambda:'Darwin')
    def probe(value):
        return lambda *a,**k:subprocess.CompletedProcess(a,0,stdout=plistlib.dumps(value),stderr=b'')
    value={'FileVault':True,'Encryption':True,'EncryptionThisVolumeProper':True,'FilesystemType':'apfs','VolumeUUID':'NEVER_PUBLIC'}
    monkeypatch.setattr(p.subprocess,'run',probe(value));assert p.volume_protection(isolated)=='PASS'
    for key in ['FileVault','Encryption','EncryptionThisVolumeProper']:
        monkeypatch.setattr(p.subprocess,'run',probe(dict(value,**{key:False})))
        assert p.volume_protection(isolated)=='SECURITY_REQUIREMENT_NOT_MET'
    monkeypatch.setattr(p.subprocess,'run',probe(dict(value,FilesystemType='smbfs')))
    assert p.volume_protection(isolated)=='SECURITY_REQUIREMENT_NOT_MET'
    monkeypatch.setattr(p.subprocess,'run',lambda *a,**k:subprocess.CompletedProcess(a,1,stdout=b'',stderr=b'PRIVATE NEVER PUBLIC'))
    assert p.volume_protection(isolated)=='BLOCKED_BY_PERMISSION'


def test_private_runtime_deny_egress_subprocess():
    code='from apps.core.network import deny_egress\nimport socket\ndeny_egress()\nfor f in [lambda:socket.getaddrinfo("example.com",443),lambda:socket.socket().connect(("192.0.2.1",443)),lambda:socket.socket().bind(("0.0.0.0",8765))]:\n try:f();raise AssertionError("egress bypass")\n except PermissionError:pass\nprint("PASS")'
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
    assert result.returncode==0 and result.stdout.strip()=='PASS'


def test_owner_uid_and_extended_acl_fail_closed(vault,monkeypatch):
    from types import SimpleNamespace
    _,_,_,data,b=vault
    original=p.Path.stat
    def other_owner(path,*a,**kw):
        if path==data:
            s=original(path,*a,**kw);return SimpleNamespace(st_uid=os.getuid()+1,st_mode=s.st_mode)
        return original(path,*a,**kw)
    monkeypatch.setattr(p.Path,'stat',other_owner)
    with pytest.raises(SafeError,match='OWNER_ONLY_PERMISSIONS'):p.owner_only(data)
    monkeypatch.setattr(p.Path,'stat',original)
    monkeypatch.setattr(p.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a,0,stdout=b'directory\n 0: synthetic ACL grant\n',stderr=b''))
    with pytest.raises(SafeError,match='EXTENDED_ACL_DENIED'):p.owner_only(b)


def test_private_restore_renewed_consent_and_security_before_targets(vault,isolated,monkeypatch):
    pkg,h,app,data,b=vault;target=b/'backup';r.backup(app,data,target,root_kind=KIND)
    new=isolated/'new private';newapp=isolated/'new app';kw=args(new,b);kw['consent']='NO'
    with pytest.raises(SafeError,match='CONSENT_REQUIRED'):r.restore(pkg,h,target,newapp,new,**kw)
    assert not newapp.exists() and not new.exists()
    kw=args(new,b);monkeypatch.setattr(p,'volume_protection',lambda path:'NOT_RUN' if str(path)==str(new) else 'PASS')
    with pytest.raises(SafeError):r.restore(pkg,h,target,newapp,new,**kw)
    assert not newapp.exists() and not new.exists()


def test_private_delete_refuses_unknown_and_synthetic_root(isolated):
    unknown=isolated/'unknown';unknown.mkdir(mode=0o700)
    synthetic=isolated/'synthetic';Store(synthetic)
    for root in [unknown,synthetic]:
        with pytest.raises(SafeError):r.delete_private_data(root,'DELETE_PRIVATE_LOCAL_DATA:'+str(root))
        assert root.exists()


@pytest.mark.parametrize('mutation',['profile','protection','gate','duplicate','false_pass'])
def test_security_report_inconsistent_ready_rejected(vault,mutation):
    pkg,h,app,data,b=vault;report=p.preflight(pkg,h,app,data,b)
    if mutation=='profile':report['runtime_profile']=dict(p.PROFILE,private_ai='ON')
    if mutation=='protection':report['storage_protection']='UNVERIFIED'
    if mutation=='gate':report['checks']=[c for c in report['checks'] if c['gate']!='data_volume']
    if mutation=='duplicate':report['checks'].append(report['checks'][0])
    if mutation=='false_pass':
        next(c for c in report['checks'] if c['gate']=='data_volume')['status']='NOT_RUN';report['storage_protection']='UNVERIFIED'
    with pytest.raises(ValidationError):p.PrivatePreflight.model_validate(report)


def test_private_application_permission_change_refused(vault):
    _,_,app,data,_=vault;os.chmod(app,0o777)
    with pytest.raises(SafeError,match='OWNER_ONLY_PERMISSIONS'):r.selected(app,data,KIND)
    os.chmod(app,0o700)
    os.chmod(app/'active.json',0o644)
    with pytest.raises(SafeError,match='OWNER_ONLY_PERMISSIONS'):r.selected(app,data,KIND)


def test_private_profile_cannot_enable_provider_even_after_rehash(private_package):
    pkg,_=private_package;profile=r.read_json(pkg/'packages/pilot/MAC_PRIVATE_CORE_PROFILE.json')
    profile['private_ai']='ON';(pkg/'packages/pilot/MAC_PRIVATE_CORE_PROFILE.json').write_text(encode(profile))
    m=r.read_json(pkg/'release-manifest.json');m['files']=r.file_hashes(pkg);m['manifest_hash']=r.identity(m)
    (pkg/'release-manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='PILOT_PROFILE_INCOMPATIBLE'):r.validate_package(pkg,m['manifest_hash'])
