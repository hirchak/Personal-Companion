"""SYNTHETIC pairing/device/epoch transport with actual SQLite domain transactions."""
import json
from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import pytest
from apps.core.api import create_app
from apps.core.models import Create, Patch, Delete
from apps.core.sync import Pair, Packet
from apps.core.storage import Store, SafeError
from test_m1_domain import isolated, journal, create

ORIGIN='http://127.0.0.1:8765'

@pytest.fixture
def app(isolated): return create_app(isolated/'mac',m2=True)


def pairing(app,label='SYNTHETIC phone'):
    invitation=app.state.sync.invite()
    p = app.state.sync.pair(Pair(invitation=invitation['invitation'],device_id=uuid4(),label=label))
    app.state.sync.finalize(p['device_id'],p['credential'],p['epoch'])
    return p


def packet(p, kind='create', id=None, revision=0, text='SYNTHETIC offline note', **changes):
    return Packet(operation_id=uuid4(),device_id=p['device_id'],entry_id=id or uuid4(),base_revision=revision,
        operation_type=kind,created_at_utc='2099-01-01T00:00:00Z',timezone='Europe/Warsaw',schema_version=2,
        local_sequence=1,payload=None if kind=='delete' else {'raw_text':text,**changes})


def apply(app,p,body): return app.state.sync.apply(body,p['device_id'],p['credential'],p['epoch'])


def test_M2_A02_commit_retry_and_transaction_failure(app):
    p=pairing(app); body=packet(p)
    first=apply(app,p,body)
    assert first['state']=='MAC_CONFIRMED' and first['revision']==1
    assert apply(app,p,body)['revision']==1
    with app.state.store.connect() as c:
        assert c.execute('SELECT count(*) FROM entries').fetchone()[0]==1
        assert c.execute('SELECT count(*) FROM operation_receipts').fetchone()[0]==1
        assert c.execute('SELECT count(*) FROM sync_receipts').fetchone()[0]==1
    failed=packet(p);app.state.store.fail_commit=True
    import sqlite3
    with pytest.raises(sqlite3.OperationalError): apply(app,p,failed)
    app.state.store.fail_commit=False
    with app.state.store.connect() as c:
        assert not c.execute('SELECT 1 FROM sync_receipts WHERE operation_id=?',(str(failed.operation_id),)).fetchone()
    assert apply(app,p,failed)['state']=='MAC_CONFIRMED'


def test_M2_A03_two_devices_and_resolution_new_operation(app):
    a,b=pairing(app,'SYNTHETIC A'),pairing(app,'SYNTHETIC B')
    original=packet(a);apply(app,a,original)
    one=packet(a,'edit',original.entry_id,1,'SYNTHETIC A variant')
    stale=packet(b,'edit',original.entry_id,1,'SYNTHETIC B variant')
    assert apply(app,a,one)['state']=='MAC_CONFIRMED'
    conflict=apply(app,b,stale);assert conflict['state']=='CONFLICT' and conflict['current']['raw_text']=='SYNTHETIC A variant'
    assert apply(app,b,stale)['state']=='CONFLICT'
    chosen=packet(b,'edit',original.entry_id,conflict['current']['revision'],'SYNTHETIC explicit merged')
    assert apply(app,b,chosen)['revision']==3
    assert app.state.journal.get(str(original.entry_id))['raw_text']=='SYNTHETIC explicit merged'


def test_M2_A04_mac_delete_stale_packet_and_phone_delete_retry(app):
    p=pairing(app);body=packet(p);apply(app,p,body)
    app.state.journal.write('delete',body.entry_id,Delete(operation_id=uuid4(),base_revision=1))
    stale=packet(p,'edit',body.entry_id,1,'SYNTHETIC must not resurrect')
    assert apply(app,p,stale)['code']=='DELETED'
    assert apply(app,p,body)['code']=='DELETED'
    with app.state.store.connect() as c:
        assert c.execute('SELECT count(*) FROM entries').fetchone()[0]==0
        assert c.execute("SELECT count(*) FROM sync_receipts WHERE action!='delete' AND fingerprint IS NOT NULL").fetchone()[0]==0
    other=packet(p);apply(app,p,other);deleted=packet(p,'delete',other.entry_id,1)
    assert apply(app,p,deleted)['state']=='MAC_CONFIRMED'
    assert apply(app,p,deleted)['revision']==2
    assert not app.state.journal.list()['items']


def test_M2_A05_wrong_clock_not_authoritative_and_newest_cursor(app,monkeypatch):
    p=pairing(app);from apps.core import domain
    monkeypatch.setattr(domain,'now',lambda:'2026-10-01T00:01:00+00:00')
    first=packet(p); apply(app,p,first)
    monkeypatch.setattr(domain,'now',lambda:'2026-10-01T00:02:00+00:00')
    later=packet(p,text='SYNTHETIC later committed'); later.created_at_utc=datetime(1900,1,1,tzinfo=timezone.utc);apply(app,p,later)
    page=app.state.journal.list(limit=1)
    assert page['items'][0]['id']==str(later.entry_id)
    assert app.state.journal.list(limit=1,cursor=page['next_cursor'])['items'][0]['id']==str(first.entry_id)


def test_M2_A06_invitation_ttl_rate_replay_revocation_identity(app):
    invite=app.state.sync.invite(); r=Pair(invitation=invite['invitation'],device_id=uuid4(),label='SYNTHETIC')
    p=app.state.sync.pair(r)
    app.state.sync.finalize(p['device_id'],p['credential'],p['epoch'])
    with pytest.raises(SafeError,match='PAIR_DENIED'):app.state.sync.pair(r)
    with app.state.store.connect() as c:
        with pytest.raises(SafeError,match='DEVICE_DENIED'):app.state.sync.authenticate(c,str(uuid4()),p['credential'],p['epoch'])
    app.state.sync.revoke(p['device_id'])
    with pytest.raises(SafeError,match='DEVICE_REVOKED'):apply(app,p,packet(p))
    t=[0];app.state.sync.clock=lambda:t[0];invite=app.state.sync.invite();t[0]=301
    with pytest.raises(SafeError,match='PAIR_DENIED'):app.state.sync.pair(Pair(invitation=invite['invitation'],device_id=uuid4(),label='SYNTHETIC'))
    app.state.sync.attempts=[]
    for _ in range(5):
        with pytest.raises(SafeError,match='PAIR_DENIED'):app.state.sync.pair(Pair(invitation='SYNTHETIC invalid',device_id=uuid4(),label='SYNTHETIC'))
    with pytest.raises(SafeError,match='PAIR_RATE_LIMIT'):app.state.sync.pair(Pair(invitation='SYNTHETIC invalid',device_id=uuid4(),label='SYNTHETIC'))


def test_M2_A10_backup_restore_epoch_and_retention(app,isolated):
    p=pairing(app); body=packet(p);apply(app,p,body)
    backup=isolated/'backup';app.state.store.backup(backup)
    restored=Store.restore(backup,isolated/'restored')
    other=create_app(restored.root,m2=True)
    with pytest.raises(SafeError):apply(other,p,packet(p,'edit',body.entry_id,1))
    assert other.state.store.meta()['restore_epoch']==1
    with other.state.store.connect() as c:
        assert all(not x[0] for x in c.execute('SELECT credential_hash FROM devices'))
    app.state.journal.write('delete',body.entry_id,Delete(operation_id=uuid4(),base_revision=1))
    app.state.sync.rotate(prune=True)
    with app.state.store.connect() as c:assert c.execute('SELECT count(*) FROM tombstones').fetchone()[0]==0
    with pytest.raises(SafeError):apply(app,p,body)
    assert not app.state.journal.list()['items']


def test_M2_A11_device_routes_host_origin_owner_csrf_default_off(app,isolated):
    p=pairing(app); headers={'Authorization':'Bearer '+p['credential'],'X-Device-ID':p['device_id'],'X-Sync-Epoch':p['epoch'],'Origin':ORIGIN}
    with TestClient(app,base_url=ORIGIN,raise_server_exceptions=False) as c:
        b=packet(p).model_dump(mode='json')
        response=c.post('/api/v1/device/operations',json=b,headers=headers)
        assert response.status_code==200
        response=c.get('/api/v1/device/snapshot',headers=headers)
        assert response.headers['cache-control']=='no-store'
        response=c.post('/api/v1/device/operations',json=b,headers={**headers,'Origin':'https://evil.invalid'})
        assert response.status_code==403
        response=c.post('/api/v1/device/operations',json=b,headers={**headers,'X-Device-ID':str(uuid4())})
        assert response.status_code==401
        response=c.post('/api/v1/sync/invitations',json={},headers={'Origin':ORIGIN})
        assert response.status_code==401
    default=create_app(isolated/'default')
    with TestClient(default,base_url=ORIGIN) as c:
        assert c.post('/api/v1/device/pair',headers={'Origin':ORIGIN},json={'invitation':'SYNTHETIC','device_id':str(uuid4()),'label':'SYNTHETIC'}).status_code==403
        assert c.get('/phone/').status_code==403


def test_M2_A02_restart_and_cross_device_operation_reuse(app):
    p=pairing(app);body=packet(p);apply(app,p,body)
    restarted=create_app(app.state.store.root,m2=True)
    assert apply(restarted,p,body)['revision']==1
    other=pairing(restarted)
    from uuid import UUID
    body.device_id=UUID(other['device_id'])
    with pytest.raises(SafeError,match='OPERATION_REUSE'):apply(restarted,other,body)


def test_M2_A06_pair_failure_never_consumes_invite_or_persists_credential(app):
    import sqlite3
    invite=app.state.sync.invite();req=Pair(invitation=invite['invitation'],device_id=uuid4(),label='SYNTHETIC rollback')
    app.state.store.fail_commit=True
    with pytest.raises(sqlite3.OperationalError):app.state.sync.pair(req)
    with app.state.store.connect() as c:assert c.execute('SELECT count(*) FROM devices').fetchone()[0]==0
    app.state.store.fail_commit=False
    result=app.state.sync.pair(req)
    assert result['device_id']==str(req.device_id)


def test_M2_A08_mac_schema1_migration_rollback_and_preservation(isolated):
    import sqlite3
    from apps.core.storage import MARKER,encode
    root=isolated/'schema1';root.mkdir();(root/'synthetic.json').write_text(encode(MARKER))
    with sqlite3.connect(root/'journal.sqlite3') as c:
        c.execute('CREATE TABLE vault_meta(vault_id TEXT,owner_id TEXT,schema_version INTEGER,restore_epoch INTEGER,created_at_utc TEXT,reconciliation TEXT)')
        c.execute('INSERT INTO vault_meta VALUES(?,?,1,0,?,?)',(str(uuid4()),str(uuid4()),'2026-10-01T00:00:00Z','NONE'))
        c.execute('CREATE TABLE entries(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL)')
        meta=c.execute('SELECT owner_id FROM vault_meta').fetchone()[0]
        id=str(uuid4());c.execute('INSERT INTO entries VALUES(?,?,1,?,?,?)',(id,meta,encode({'type':'inbox','raw_text':'SYNTHETIC migrated','timezone':'Europe/Warsaw','tags':[],'local_date':None,'occurred_at_utc':None,'time_precision':'unknown'}),'2026-10-01T00:00:00Z','2026-10-01T00:00:00Z'))
    with pytest.raises(sqlite3.OperationalError):Store(root,fail_migration=True)
    with sqlite3.connect(root/'journal.sqlite3') as c:
        assert c.execute('SELECT schema_version FROM vault_meta').fetchone()[0]==1
        assert c.execute("SELECT count(*) FROM sqlite_master WHERE name='devices'").fetchone()[0]==0
    store=Store(root)
    assert store.meta()['schema_version']==6
    from apps.core.domain import Journal
    assert Journal(store).get(id)['raw_text']=='SYNTHETIC migrated'
    assert (root/'preupgrade.sqlite3').is_file()
