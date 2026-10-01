import json,sqlite3
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from apps.core.storage import Store,SafeError,SCHEMA,encode
from apps.core.health import HealthImport,PrivateHealthStore
from apps.core.health_contracts import HealthBatch,HealthRecord
from apps.core.domain import Journal
from apps.core.models import Create
from test_m1_domain import isolated
from m6_fixtures import record,batch

@pytest.fixture
def health(isolated):return HealthImport(Store(isolated/'data'))

def test_provenance_and_self_report_separate(health):
    j=Journal(health.store);req=Create(operation_id=uuid4(),entry_id=uuid4(),base_revision=0,payload={'type':'sleep','raw_text':'SYNTHETIC own estimate 7h'});j.write('create',req.entry_id,req)
    b=batch(record('sleep'));health.apply(b)
    r=health.records()[0];assert r['provenance']=='SOURCE_IMPORTED' and r['source_system']=='HEALTH_CONNECT';assert r['first_seen'] and r['last_seen'] and r['imported_at'];assert str(uuid4())!=r['local_id']
    assert j.list()['items'][0]['raw_text']==req.payload.raw_text
    assert r['source_id']==b.scopes[0].records[0].source_id and r['start_offset'] is None

def test_duplicate_restart_replay_update_and_history(health):
    b=batch(record());health.apply(b);before=health.records();assert health.apply(b)['result']=='IDEMPOTENT_REPLAY';assert health.records()==before
    h=HealthImport(Store(health.store.root));assert h.apply(b)['result']=='IDEMPOTENT_REPLAY'
    newer=record(modified='2025-01-02T12:00:00Z',fields={'count':99,'unit':'count'})
    h.apply(batch(newer,sequence=2,epoch=b.epoch,mode='INCREMENTAL'));assert len(h.records())==1 and h.records()[0]['revision']==2
    with h.store.connect() as c:assert c.execute('SELECT count(*) FROM health_revisions').fetchone()[0]==2
    stale=record();h.apply(batch(stale,sequence=3,epoch=b.epoch));assert h.records()[0]['fields']['count']==99

def test_source_delete_no_resurrection_and_minimal_revision_audit(health):
    b=batch(record());health.apply(b);r=health.records()[0]
    d={'type':'steps','source_id':record()['source_id'],'origin':'synthetic.origin','status':'SOURCE_DELETED'}
    health.apply(batch(d,sequence=2,epoch=b.epoch));assert health.records()[0]['status']=='SOURCE_DELETED';assert health.records()[0]['fields'] is None
    assert health.status()['availability']['steps']=='MISSING'
    with health.store.connect() as c:assert c.execute('SELECT count(*) FROM health_revisions').fetchone()[0]==1
    with pytest.raises(SafeError,match='TOMBSTONE'):health.apply(batch(record(),sequence=3,epoch=b.epoch))
    assert health.records()[0]['local_id']==r['local_id']

def test_deny_revoke_partial_failure_retains_prior_copy(health):
    b=batch(record('sleep'),record());health.apply(b)
    health.apply(batch(record(),sequence=2,epoch=b.epoch,permissions={'sleep':'PERMISSION_DENIED','exercise':'READ_FAILED'}))
    assert len(health.records())==2;assert health.status()['availability']=={'sleep':'PERMISSION_DENIED','steps':'VALUE','exercise':'UNKNOWN'}
    assert health.status()['permissions']['exercise']=='READ_FAILED'

@pytest.mark.parametrize('permission',['NOT_REQUESTED','PERMISSION_DENIED','READ_FAILED','NOT_AVAILABLE'])
def test_missing_never_zero(health,permission):
    health.apply(batch(permissions={'steps':permission}));assert health.status()['availability']['steps']!='VALUE';assert health.records()==[]
    assert health.status()['steps_aggregate']=='UNRESOLVED'

def test_overlap_different_origins_no_total(health):
    health.apply(batch(record(id='SYNTHETIC-A'),record(id='SYNTHETIC-B',origin='synthetic.other')))
    assert len(health.records())==2;assert health.status()['steps_aggregate']=='UNRESOLVED';assert 'total' not in health.status()

def test_stale_epoch_sequence_and_conflicting_revision(health):
    b=batch(record());health.apply(b)
    with pytest.raises(SafeError,match='RECONNECT'):health.apply(batch(record(),epoch=str(uuid4()),sequence=2))
    with pytest.raises(SafeError,match='SEQUENCE_CONFLICT'):health.apply(batch(record(fields={'count':91,'unit':'count'}),epoch=b.epoch))
    health.apply(batch(record(),sequence=3,epoch=b.epoch))
    with pytest.raises(SafeError,match='STALE_BATCH'):health.apply(batch(record(),sequence=2,epoch=b.epoch))
    with pytest.raises(SafeError,match='SOURCE_ID_CONFLICT'):health.apply(batch(record(origin='synthetic.other'),sequence=4,epoch=b.epoch))
    with pytest.raises(SafeError,match='REVISION_CONFLICT'):health.apply(batch(record(fields={'count':92,'unit':'count'}),sequence=4,epoch=b.epoch))

def test_atomic_batch_conflict_does_not_advance_checkpoint(health):
    b=batch(record());health.apply(b);before=health.records();state=health.status()
    with pytest.raises(SafeError):health.apply(batch(record(id='SYNTHETIC-new'),record(origin='synthetic.conflict'),epoch=b.epoch,sequence=2))
    assert before==health.records() and state==health.status()

def test_delete_disconnect_generation_and_explicit_reimport(health):
    b=batch(record());health.apply(b);generation=health.status()['generation'];health.disconnect(delete=True,generation=generation);assert not health.records()
    with pytest.raises(SafeError,match='GENERATION_STALE'):health.apply(b,True,generation)
    with pytest.raises(SafeError,match='EXPLICIT_ACTION'):health.apply(b)
    health.apply(b,reconnect=True,generation=health.status()['generation']);assert len(health.records())==1
    health.disconnect();assert len(health.records())==1
    with pytest.raises(SafeError,match='EXPLICIT_ACTION'):health.apply(b)

def test_restore_reconnect_no_token_reuse_update_delete(health,isolated):
    b=batch(record());health.apply(b);health.store.backup(isolated/'backup')
    restored=HealthImport(Store.restore(isolated/'backup',isolated/'restored'))
    assert restored.status()['connection']=='SOURCE_RECONNECT_REQUIRED';assert restored.records()[0]['status']=='UNKNOWN'
    with pytest.raises(SafeError,match='EXPLICIT_ACTION'):restored.apply(b)
    updated=record(modified='2025-01-02T12:00:00Z',fields={'count':60,'unit':'count'})
    restored.apply(batch(updated,epoch=b.epoch,sequence=2),reconnect=True);assert len(restored.records())==1 and restored.records()[0]['fields']['count']==60
    restored.apply(batch({'type':'steps','source_id':updated['source_id'],'origin':updated['origin'],'status':'SOURCE_DELETED'},epoch=b.epoch,sequence=3))
    assert restored.records()[0]['status']=='SOURCE_DELETED'
    with restored.store.connect() as c:
        state=dict(c.execute('SELECT * FROM health_state').fetchone());assert 'token' not in state

def test_corrupt_health_backup_refused(health,isolated):
    health.apply(batch(record()));health.store.backup(isolated/'backup');p=isolated/'backup'/'snapshot.sqlite3'
    with sqlite3.connect(p) as c:c.execute("UPDATE health_records SET payload='{}'")
    from apps.core.storage import digest
    m=json.loads((isolated/'backup'/'manifest.json').read_text());m['files']['snapshot.sqlite3']=digest(p.read_bytes());(isolated/'backup'/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='HEALTH_INTEGRITY'):Store.restore(isolated/'backup',isolated/'restored')
    assert not (isolated/'restored').exists()

@pytest.mark.parametrize('start,end,so,eo',[('2025-01-01T23:00:00Z','2025-01-02T07:00:00Z',None,None),('2025-03-30T01:30:00+01:00','2025-03-30T03:30:00+02:00',3600,7200),('2025-10-26T02:30:00+02:00','2025-10-26T02:30:00+01:00',7200,3600),('2025-01-01T10:00:00Z','2025-01-01T11:00:00Z',0,0)])
def test_utc_dst_cross_midnight_and_offset_unknown(health,start,end,so,eo):
    health.apply(batch(record('sleep',start=start,end=end,start_offset=so,end_offset=eo)))
    r=health.records()[0];assert r['start']==start and r['end']==end and r['start_offset']==so and r['end_offset']==eo

@pytest.mark.parametrize('kind',['sleep','exercise'])
def test_unknown_source_codes_and_missing_optional(health,kind):
    fields={'stages':[{'start':'2025-01-01T10:00:00Z','end':'2025-01-01T11:00:00Z','stage':12345,'classification':'SOURCE_UNKNOWN'}],'stages_state':'VALUE'} if kind=='sleep' else {'exercise_type':12345,'classification':'SOURCE_CODE'}
    health.apply(batch(record(kind,fields=fields)));assert health.records()[0]['fields']==fields

@pytest.mark.parametrize('change',[{'schema_version':True},{'schema_version':1.0},{'schema_version':9},{'shell':'SYNTHETIC command'},{'sequence':False},{'source_system':'SAMSUNG_PRIVATE'}])
def test_bad_batch_schema(change):
    p=batch().model_dump();p.update(change)
    with pytest.raises(ValidationError):HealthBatch.model_validate(p)

@pytest.mark.parametrize('change',[{'start':'bad'},{'start':'2025-01-01T10:00:00'},{'end':'2025-01-01T09:00:00Z'},{'fields':{'count':float('nan'),'unit':'count'}},{'fields':{'count':float('inf'),'unit':'count'}},{'fields':{'count':5,'unit':'km'}},{'fields':{'count':True,'unit':'count'}},{'fields':{'count':-1,'unit':'count'}},{'route':[]},{'fields':None},{'start_offset':999999},{'source_id':''}])
def test_malformed_records(change):
    r=record();r.update(change)
    with pytest.raises(ValidationError):HealthRecord.model_validate(r)

def test_stage_validation_duplicates_partial_permissions_and_batch_bounds():
    with pytest.raises(ValidationError):batch(record(),record())
    with pytest.raises(ValidationError):batch(record(),permissions={'steps':'PERMISSION_DENIED'})
    with pytest.raises(ValidationError):batch(*[record(id=f'SYNTHETIC-{i}') for i in range(1001)])
    r=record('sleep',fields={'stages':[],'stages_state':'VALUE'})
    with pytest.raises(ValidationError):HealthRecord.model_validate(r)
    r=record('sleep',fields={'stages':[{'start':'2025-01-01T09:00:00Z','end':'2025-01-01T11:00:00Z','stage':1,'classification':'SDK_KNOWN'}],'stages_state':'VALUE'})
    with pytest.raises(ValidationError):HealthRecord.model_validate(r)

def test_private_health_root_not_real_journal_or_repository(isolated):
    p=PrivateHealthStore(isolated/'private-test');h=HealthImport(p);h.apply(batch(record()));assert HealthImport(PrivateHealthStore(p.root)).records()==h.records()
    assert (p.root.stat().st_mode&0o777)==0o700 and (p.db.stat().st_mode&0o777)==0o600
    with pytest.raises(SafeError,match='GIT_ROOT|REPO_ROOT'):PrivateHealthStore(Path.cwd()/'SYNTHETIC_BAD_ROOT')
    with pytest.raises(SafeError,match='UNKNOWN_HEALTH_ROOT'):PrivateHealthStore(Store(isolated/'journal').root)

def test_deletion_id_only_preserves_last_known_origin(health):
    b=batch(record());health.apply(b)
    health.apply(batch({'type':'steps','source_id':record()['source_id'],'origin':'','status':'SOURCE_DELETED'},epoch=b.epoch,sequence=2))
    assert health.records()[0]['origin']=='synthetic.origin'
    assert HealthImport(Store(health.store.root)).records()[0]['status']=='SOURCE_DELETED'
