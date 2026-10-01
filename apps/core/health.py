"""Provenance-preserving local health cache. No provider, journal or source write capability."""
import json,os,sqlite3
from pathlib import Path
from contextlib import contextmanager
from uuid import uuid4,UUID
from .storage import SafeError,safe_path,empty_target,encode,now,digest
from .health_contracts import HealthBatch,HealthRecord,instant
HEALTH_TABLES=(
 'CREATE TABLE IF NOT EXISTS health_records(local_id TEXT PRIMARY KEY,type TEXT NOT NULL,source_id TEXT NOT NULL,origin TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,revision INTEGER NOT NULL,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,UNIQUE(type,source_id))',
 'CREATE TABLE IF NOT EXISTS health_revisions(local_id TEXT NOT NULL REFERENCES health_records(local_id) ON DELETE CASCADE,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(local_id,revision))',
 'CREATE TABLE IF NOT EXISTS health_state(id INTEGER PRIMARY KEY CHECK(id=1),generation TEXT NOT NULL,epoch TEXT,sequence INTEGER NOT NULL,batch_hash TEXT,blocked INTEGER NOT NULL,connection TEXT NOT NULL,permissions TEXT NOT NULL,last_import TEXT)',
)
class PrivateHealthStore:
    """Fresh explicit M6 health-only root; never opens a personal journal/vault."""
    def __init__(self,root):
        self.root=safe_path(root);marker=self.root/'m6-private-health.json'
        if self.root.exists() and any(self.root.iterdir()):
            if not marker.is_file() or json.loads(marker.read_text())!={'kind':'M6_PRIVATE_HEALTH_TEST','schema':1}:raise SafeError('UNKNOWN_HEALTH_ROOT')
            if {p.name for p in self.root.iterdir()}-{'m6-private-health.json','health.sqlite3','health.sqlite3-wal','health.sqlite3-shm','health.sqlite3-journal'}:raise SafeError('UNKNOWN_HEALTH_CONTENT')
        else:
            empty_target(self.root);self.root.mkdir(mode=0o700,exist_ok=True);marker.write_text(encode({'kind':'M6_PRIVATE_HEALTH_TEST','schema':1}));marker.chmod(0o600)
        self.root.chmod(0o700);self.db=self.root/'health.sqlite3'
        if not self.db.exists():os.close(os.open(self.db,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600))
        with self.transaction() as c:
            for sql in HEALTH_TABLES:c.execute(sql)
        self.db.chmod(0o600)
    def connect(self):
        c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
    @contextmanager
    def transaction(self):
        c=self.connect()
        try:c.execute('BEGIN IMMEDIATE');yield c;c.commit()
        except BaseException:c.rollback();raise
        finally:c.close()
class HealthImport:
    def __init__(self,store):
        self.store=store
        with store.transaction() as c:
            c.execute("INSERT OR IGNORE INTO health_state VALUES(1,?,NULL,0,NULL,0,'SOURCE_RECONNECT_REQUIRED',?,NULL)",(str(uuid4()),encode({k:'NOT_REQUESTED' for k in ('sleep','steps','exercise')})))
    def apply(self,batch:HealthBatch,reconnect=False,generation=None):
        serialized=encode(batch.model_dump());fingerprint=digest(serialized.encode())
        if len(serialized.encode())>1000000:raise SafeError('HEALTH_BATCH_LIMIT',413)
        with self.store.transaction() as c:
            state=dict(c.execute('SELECT * FROM health_state').fetchone())
            if generation is not None and generation!=state['generation']:raise SafeError('HEALTH_GENERATION_STALE',409)
            if state['blocked'] and not reconnect:raise SafeError('HEALTH_REIMPORT_REQUIRES_EXPLICIT_ACTION',409)
            if state['epoch'] and state['epoch']!=batch.epoch and not reconnect:raise SafeError('SOURCE_RECONNECT_REQUIRED',409)
            if state['epoch']==batch.epoch:
                if batch.sequence<state['sequence']:raise SafeError('HEALTH_STALE_BATCH',409)
                if batch.sequence==state['sequence']:
                    if fingerprint!=state['batch_hash']:raise SafeError('HEALTH_SEQUENCE_CONFLICT',409)
                    return {'result':'IDEMPOTENT_REPLAY','status':self._status(c)}
            imported=now();perms={}
            for scope in batch.scopes:
                perms[scope.type]=scope.permission
                for record in scope.records:
                    old=c.execute('SELECT * FROM health_records WHERE type=? AND source_id=?',(record.type,record.source_id)).fetchone()
                    if old and old['origin']!=record.origin and record.status!='SOURCE_DELETED':raise SafeError('HEALTH_SOURCE_ID_CONFLICT',409)
                    value=record.model_dump();value['provenance']='SOURCE_IMPORTED';value['source_system']='HEALTH_CONNECT';value['schema_version']=1
                    if old and record.status=='SOURCE_DELETED' and not record.origin:value['origin']=old['origin']
                    payload=encode(value)
                    if old:
                        previous=json.loads(old['payload'])
                        # A deleted source cannot return from a stale cumulative export.
                        if old['status']=='SOURCE_DELETED' and record.status!='SOURCE_DELETED':raise SafeError('HEALTH_TOMBSTONE_RECONCILIATION',409)
                        if record.status!='SOURCE_DELETED' and previous.get('modified'):
                            before,after=instant(previous['modified']),instant(record.modified)
                            if after<before:continue
                            if after==before and payload!=old['payload'] and record.status==old['status']:raise SafeError('HEALTH_REVISION_CONFLICT',409)
                        if payload!=old['payload']:
                            rev=old['revision']+1
                            if record.status=='SOURCE_DELETED':c.execute('DELETE FROM health_revisions WHERE local_id=?',(old['local_id'],))
                            c.execute('UPDATE health_records SET status=?,payload=?,revision=?,last_seen=? WHERE local_id=?',(record.status,payload,rev,imported,old['local_id']))
                            c.execute('INSERT INTO health_revisions VALUES(?,?,?)',(old['local_id'],rev,payload))
                        else:c.execute('UPDATE health_records SET last_seen=? WHERE local_id=?',(imported,old['local_id']))
                    else:
                        id=str(uuid4());c.execute('INSERT INTO health_records VALUES(?,?,?,?,?,?,1,?,?)',(id,record.type,record.source_id,record.origin,record.status,payload,imported,imported));c.execute('INSERT INTO health_revisions VALUES(?,1,?)',(id,payload))
            connection='CONNECTED' if all(v=='GRANTED' for v in perms.values()) else 'PARTIAL_OR_DENIED'
            c.execute('UPDATE health_state SET epoch=?,sequence=?,batch_hash=?,blocked=0,connection=?,permissions=?,last_import=? WHERE id=1',(batch.epoch,batch.sequence,fingerprint,connection,encode(perms),imported))
            return {'result':'IMPORTED','status':self._status(c)}
    def _status(self,c):
        state=dict(c.execute('SELECT * FROM health_state').fetchone());perms=json.loads(state['permissions']);availability={}
        for type in ('sleep','steps','exercise'):
            count=c.execute("SELECT count(*) FROM health_records WHERE type=? AND status='VALUE'",(type,)).fetchone()[0]
            availability[type]='PERMISSION_DENIED' if perms[type]=='PERMISSION_DENIED' else 'NOT_REQUESTED' if perms[type]=='NOT_REQUESTED' else 'UNKNOWN' if perms[type]!='GRANTED' else 'VALUE' if count else 'MISSING'
        return {'connection':state['connection'],'permissions':perms,'availability':availability,'last_import':state['last_import'],'generation':state['generation'],'steps_aggregate':'UNRESOLVED','provenance':'SOURCE_IMPORTED','read_only':True}
    def status(self):
        with self.store.connect() as c:return self._status(c)
    def records(self):
        with self.store.connect() as c:
            return [{'local_id':r['local_id'],'revision':r['revision'],'first_seen':r['first_seen'],'last_seen':r['last_seen'],'imported_at':r['last_seen'],**json.loads(r['payload'])} for r in c.execute('SELECT * FROM health_records ORDER BY type,local_id LIMIT 3000')]
    def disconnect(self,delete=False,generation=None):
        with self.store.transaction() as c:
            state=c.execute('SELECT generation FROM health_state').fetchone()
            if generation is not None and generation!=state['generation']:raise SafeError('HEALTH_GENERATION_STALE',409)
            if delete:c.execute('DELETE FROM health_records')
            c.execute("UPDATE health_state SET generation=?,epoch=NULL,sequence=0,batch_hash=NULL,blocked=1,connection='SOURCE_RECONNECT_REQUIRED',permissions=?,last_import=NULL WHERE id=1",(str(uuid4()),encode({k:'NOT_REQUESTED' for k in ('sleep','steps','exercise')})))
        return self.status()
def check_health(c):
    from pydantic import ValidationError
    def validated(payload):
        p=json.loads(payload)
        if not isinstance(p,dict):raise ValueError('HEALTH_PAYLOAD')
        provenance=p.pop('provenance');source=p.pop('source_system');version=p.pop('schema_version')
        if provenance!='SOURCE_IMPORTED' or source!='HEALTH_CONNECT' or type(version) is not int or version!=1:raise ValueError('HEALTH_METADATA')
        return HealthRecord.model_validate(p)
    try:
        for r in c.execute('SELECT * FROM health_records'):
            record=validated(r['payload'])
            UUID(r['local_id']);instant(r['first_seen']);instant(r['last_seen'])
            if r['revision']<1 or record.type!=r['type'] or record.source_id!=r['source_id'] or record.origin!=r['origin'] or record.status!=r['status']:raise ValueError('HEALTH_METADATA')
        for r in c.execute('SELECT r.*,h.type AS parent_type,h.source_id AS parent_source,h.revision AS current_revision FROM health_revisions r JOIN health_records h USING(local_id)'):
            record=validated(r['payload'])
            if r['revision']<1 or r['revision']>r['current_revision'] or record.type!=r['parent_type'] or record.source_id!=r['parent_source']:raise ValueError('HEALTH_REVISION')
        states=c.execute('SELECT * FROM health_state').fetchall()
        if len(states)>1:raise ValueError('HEALTH_STATE')
        for state in states:
            UUID(state['generation'])
            if state['epoch'] is not None:UUID(state['epoch'])
            if state['sequence']<0 or state['blocked'] not in (0,1):raise ValueError('HEALTH_STATE')
            perms=json.loads(state['permissions'])
            if not isinstance(perms,dict) or set(perms)!={'sleep','steps','exercise'} or any(v not in {'GRANTED','PERMISSION_DENIED','READ_FAILED','NOT_AVAILABLE','NOT_REQUESTED'} for v in perms.values()):raise ValueError('HEALTH_PERMISSIONS')
            if state['connection'] not in {'CONNECTED','PARTIAL_OR_DENIED','SOURCE_RECONNECT_REQUIRED'}:raise ValueError('HEALTH_CONNECTION')
            if state['last_import'] is not None:instant(state['last_import'])
    except (ValueError,TypeError,KeyError,ValidationError):raise SafeError('HEALTH_INTEGRITY') from None
