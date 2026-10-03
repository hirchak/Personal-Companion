"""Deterministic admission controller and transactional finite practice sessions."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5
from pydantic import ValidationError
from scripts.m7_admission import Registry, approval_gates, digest as identity, read_json, validate_directory
from .practice_contracts import Package, RuntimeReceipt, Start, Action, Session, UserResponse
from .storage import MARKER, REPO, SafeError, encode, digest, now

PRACTICE_TABLES = (
 'CREATE TABLE IF NOT EXISTS practice_sessions(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL,updated TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS practice_response_revisions(session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,step_id TEXT NOT NULL,revision INTEGER NOT NULL,value TEXT NOT NULL,PRIMARY KEY(session_id,step_id,revision))',
 'CREATE TABLE IF NOT EXISTS practice_receipts(operation_id TEXT PRIMARY KEY,session_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT,revision INTEGER NOT NULL,result_code TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS practice_tombstones(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,deleted_utc TEXT NOT NULL)',
)
NAMESPACE = UUID('70000000-0000-4000-8000-000000000001')
RUNNABLE = {'ACTIVE', 'PAUSED'}


def package_hash(package):
    d = package.model_dump() if isinstance(package, Package) else dict(package)
    d.pop('content_hash', None)
    return digest(encode(d).encode())


def load_package(path):
    try:
        raw = read_json(Path(path))
        p = Package.model_validate(raw)
        if len(encode(p.model_dump()).encode()) > 40000 or p.content_hash != package_hash(p):
            raise ValueError('Package hash/size mismatch')
        return p
    except (ValueError, UnicodeError, OSError, ValidationError):
        raise SafeError('PRACTICE_PACKAGE_INVALID') from None


def check_sessions(c):
    """Backup integrity only: broken practice metadata never gates journal startup."""
    try:
        for row in c.execute('SELECT * FROM practice_sessions'):
            s = Session.model_validate_json(row['payload'])
            if str(s.id) != row['id'] or s.revision != row['revision'] or s.updated_utc != row['updated']:
                raise ValueError()
        for row in c.execute('SELECT * FROM practice_response_revisions'):
            value = json.loads(row['value'])
            if not isinstance(value, (str, bool)):
                raise ValueError()
    except (ValueError, TypeError, ValidationError):
        raise SafeError('PRACTICE_SESSION_INTEGRITY') from None


class PracticeEngine:
    def __init__(self, store, synthetic_demo=False, registry_root=None):
        if type(synthetic_demo) is not bool:
            raise SafeError('SYNTHETIC_CONFIG_INVALID')
        self.store, self.synthetic_demo = store, synthetic_demo
        self.registry_root = Path(registry_root) if registry_root else REPO / 'research/admission'
        self.package_paths = {'synthetic:walkthrough': REPO / 'packages/practices/synthetic/walkthrough.json'}
        # Explicit internal test seams, not package fields, HTTP controls or persisted permissions.
        self.receipt_override = None
        self.revoked = False

    def technical_identity(self):
        files = ('apps/core/practice.py', 'apps/core/practice_contracts.py', 'scripts/m7_admission.py',
                 'apps/core/storage.py', 'apps/core/models.py', 'apps/core/api.py',
                 'apps/web/src/PracticePanel.tsx', 'apps/web/src/practice-model.ts', 'apps/web/src/style.css')
        return identity({p: digest((REPO / p).read_bytes()) for p in files})

    def preparation(self):
        if validate_directory(self.registry_root)['structural_status'] != 'PASS':
            raise SafeError('ADMISSION_REGISTRY_INVALID', 409)
        return Registry.model_validate(read_json(self.registry_root / 'registry.json'))

    def admitted(self, module_id):
        registry = self.preparation()
        if module_id not in self.package_paths:
            raise SafeError('PRACTICE_UNAVAILABLE', 409)
        package = load_package(self.package_paths[module_id])
        if package.module_id != module_id:
            raise SafeError('PRACTICE_PACKAGE_INVALID')
        meta = self.store.meta()
        synthetic = module_id.startswith('synthetic:')
        if synthetic:
            if (not self.synthetic_demo or package.provenance != 'ORIGINAL_SYNTHETIC'
                    or read_json(self.store.root / 'synthetic.json') != MARKER or self.revoked):
                raise SafeError('PRACTICE_NOT_ADMITTED', 409)
            receipt = RuntimeReceipt(schema_version=1, kind='SYNTHETIC_ENGINEERING_ONLY',
                module_id=module_id, module_version=package.module_version, content_hash=package.content_hash,
                admission_identity=identity({'config':'EXPLICIT_SYNTHETIC_LAUNCH','registry':registry.model_dump()}),
                technical_identity=self.technical_identity(), technical_evidence='EXACT_IMPLEMENTATION_SOURCE_SHA256',
                review_scope='ORIGINAL_NEUTRAL_SYNTHETIC_UX_ONLY', owner_activation_decision='EXPLICIT_SYNTHETIC_LAUNCH',
                activation_epoch=meta['restore_epoch'], created_at=meta['created_at_utc'], expires_at=None,
                re_review_status='CURRENT', approval_identity=None, rights_hash=None, source_claim_identity=None)
        else:
            candidate = next((m for m in registry.modules if m.id == module_id), None)
            # M7_PREP never supplies ACTIVE production admission. No flag can override its OFF status.
            if candidate is None or candidate.activation_status == 'OFF' or candidate.approval is None:
                raise SafeError('PRACTICE_NOT_ADMITTED', 409)
            if approval_gates(candidate, {s.id:s for s in registry.sources}, {c.id:c for c in registry.claims}):
                raise SafeError('PRACTICE_NOT_ADMITTED', 409)
            raise SafeError('PRODUCTION_ACTIVATION_RECEIPT_ABSENT', 409)
        if self.receipt_override is not None:
            try:
                supplied = RuntimeReceipt.model_validate(self.receipt_override)
            except ValidationError:
                raise SafeError('RUNTIME_RECEIPT_INVALID', 409) from None
            if supplied != receipt:
                raise SafeError('RUNTIME_RECEIPT_STALE', 409)
            receipt = supplied
        if receipt.re_review_status != 'CURRENT' or (receipt.expires_at and datetime.fromisoformat(receipt.expires_at) <= datetime.now(timezone.utc)):
            raise SafeError('RUNTIME_RECEIPT_STALE', 409)
        return package, receipt

    def catalog(self):
        try:
            registry = self.preparation()
            items = [{'module_id':m.id,'title':'Модуль очікує перевірки','available':False,'synthetic':False}
                     for m in registry.modules if m.clinical_sensitive]
            if self.synthetic_demo:
                try:
                    p, r = self.admitted('synthetic:walkthrough')
                    items.insert(0,{'module_id':p.module_id,'module_version':p.module_version,
                        'content_hash':p.content_hash,'title':p.title,'description':p.description,
                        'synthetic':True,'available':True})
                except SafeError:
                    pass
            return {'items':items,'production_active_clinical':0,'synthetic_demo':self.synthetic_demo,
                    'synthetic_runnable':sum(x['available'] and x['synthetic'] for x in items), 'admission_valid':True}
        except (SafeError, ValueError, OSError):
            return {'items':[],'production_active_clinical':0,'synthetic_demo':self.synthetic_demo,
                    'synthetic_runnable':0,'admission_valid':False}

    def row(self, c, id):
        id = str(id)
        r = c.execute('SELECT * FROM practice_sessions WHERE id=?',(id,)).fetchone()
        if not r:
            dead=c.execute('SELECT 1 FROM practice_tombstones WHERE id=?',(id,)).fetchone()
            raise SafeError('PRACTICE_DELETED' if dead else 'PRACTICE_NOT_FOUND',410 if dead else 404)
        try:
            s=Session.model_validate_json(r['payload'])
            if str(s.id)!=r['id'] or s.revision!=r['revision']:
                raise ValueError()
            return s
        except (ValueError, ValidationError):
            raise SafeError('PRACTICE_SESSION_INVALID',409) from None

    def write_session(self,c,s):
        c.execute('UPDATE practice_sessions SET revision=?,payload=?,updated=? WHERE id=?',
                  (s.revision,encode(s.model_dump(mode='json')),s.updated_utc,str(s.id)))

    def validate_binding(self,s):
        p,r=self.admitted(s.module_id)
        if (p.module_version != s.module_version or p.content_hash != s.package_hash
                or identity(r.model_dump()) != s.admission_binding or r.activation_epoch!=s.activation_epoch):
            raise SafeError('PRACTICE_BINDING_STALE',409)
        return p

    def revalidate(self,c,s):
        if s.state in RUNNABLE:
            try:
                self.validate_binding(s)
            except (SafeError,ValueError,OSError):
                s.state='BLOCKED_BY_ADMISSION';s.blocked_reason='VERSION_OR_ADMISSION_CHANGED'
                s.revision+=1;s.updated_utc=now();self.write_session(c,s)
        return s

    def view(self,s):
        d=s.model_dump(mode='json');d['current_step_definition']=None;d['step_number']=None;d['step_count']=None
        try:
            p=self.validate_binding(s)
            step=next(x for x in p.steps if x.id==s.current_step)
            d.update(current_step_definition=step.model_dump(),step_number=p.steps.index(step)+1,step_count=len(p.steps))
        except (SafeError,ValueError,StopIteration,OSError):
            pass
        return d

    def get(self,id):
        with self.store.transaction() as c:
            s=self.revalidate(c,self.row(c,id))
        return self.view(s)

    def history(self,limit=50,offset=0):
        with self.store.transaction() as c:
            rows=c.execute('SELECT id FROM practice_sessions ORDER BY updated DESC,id LIMIT ? OFFSET ?',(limit,offset)).fetchall()
            values=[self.revalidate(c,self.row(c,r['id'])) for r in rows]
        # History does not inline response values. They require selecting the exact session.
        keys=('id','title','module_id','module_version','state','revision','started_utc','updated_utc','provenance')
        return {'items':[{k:s.model_dump(mode='json')[k] for k in keys} for s in values],
                'next_offset':offset+limit if len(rows)==limit else None}

    def start(self,body:Start):
        op=str(body.operation_id);id=str(uuid5(NAMESPACE,op))
        fp=identity(body.model_dump(mode='json'))
        with self.store.transaction() as c:
            if c.execute('SELECT 1 FROM practice_tombstones WHERE id=?',(id,)).fetchone():
                raise SafeError('PRACTICE_DELETED',410)
            existing=c.execute('SELECT * FROM practice_receipts WHERE operation_id=?',(op,)).fetchone()
            if existing:
                if existing['action']!='start' or existing['fingerprint']!=fp:
                    raise SafeError('OPERATION_REUSE',409)
                s=self.revalidate(c,self.row(c,existing['session_id']))
            else:
                p,r=self.admitted(body.module_id)
                if body.module_version!=p.module_version or body.content_hash!=p.content_hash:
                    raise SafeError('PRACTICE_BINDING_STALE',409)
                timestamp=now()
                s=Session(schema_version=1,id=UUID(id),module_id=p.module_id,module_version=p.module_version,
                    package_hash=p.content_hash,package_schema_version=p.schema_version,title=p.title,provenance=p.provenance,
                    admission_binding=identity(r.model_dump()),activation_epoch=r.activation_epoch,started_utc=timestamp,
                    updated_utc=timestamp,current_step=p.entry_step,state='ACTIVE',revision=1,responses={},skipped_steps=[],
                    completed_utc=None,stopped_utc=None,blocked_reason=None)
                c.execute('INSERT INTO practice_sessions VALUES(?,?,?,?)',(id,1,encode(s.model_dump(mode='json')),timestamp))
                c.execute('INSERT INTO practice_receipts VALUES(?,?,?,?,?,?)',(op,id,'start',fp,1,'STARTED'))
        return self.view(s)

    def act(self,id,body:Action):
        id=str(id);op=str(body.operation_id);fp=identity({'id':id,'request':body.model_dump(mode='json')})
        deleted=False
        with self.store.transaction() as c:
            existing=c.execute('SELECT * FROM practice_receipts WHERE operation_id=?',(op,)).fetchone()
            if existing:
                if existing['session_id']!=id or existing['action']!=body.action or existing['fingerprint']!=fp:
                    raise SafeError('OPERATION_REUSE',409)
                if body.action=='delete':return {'id':id,'state':'DELETED','revision':existing['revision']}
                s=self.revalidate(c,self.row(c,id))
            else:
                s=self.row(c,id)
                if s.revision!=body.base_revision:
                    raise SafeError('REVISION_CONFLICT',409)
                if body.action not in {'stop','delete'}:
                    s=self.revalidate(c,s)
                if s.state=='BLOCKED_BY_ADMISSION' and body.action not in {'stop','delete'}:
                    # Persist a receipt too: response-loss retry cannot advance or duplicate the block.
                    c.execute('INSERT INTO practice_receipts VALUES(?,?,?,?,?,?)',
                              (op,id,body.action,fp,s.revision,'BLOCKED'))
                    return self.view(s)
                timestamp=now();revision=s.revision+1
                if body.action=='delete':
                    c.execute('DELETE FROM practice_sessions WHERE id=?',(id,))
                    c.execute('UPDATE practice_receipts SET fingerprint=NULL,result_code="DELETED" WHERE session_id=?',(id,))
                    c.execute('INSERT INTO practice_tombstones VALUES(?,?,?)',(id,revision,timestamp));deleted=True
                else:
                    if body.action=='stop':
                        if s.state not in RUNNABLE|{'BLOCKED_BY_ADMISSION'}:raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                        s.state='STOPPED';s.stopped_utc=timestamp
                    elif body.action=='pause':
                        if s.state!='ACTIVE':raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                        s.state='PAUSED'
                    elif body.action=='resume':
                        if s.state!='PAUSED':raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                        s.state='ACTIVE'
                    else:
                        if s.state!='ACTIVE':raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                        p=self.validate_binding(s);step=next(x for x in p.steps if x.id==s.current_step)
                        if body.step_id!=s.current_step:raise SafeError('PRACTICE_STEP_MISMATCH',409)
                        if body.action=='save':
                            self.validate_response(step,body.response)
                            old=s.responses.get(step.id)
                            if old:
                                c.execute('INSERT INTO practice_response_revisions VALUES(?,?,?,?)',
                                          (id,step.id,old.revision,encode(old.value)))
                            s.responses[step.id]=UserResponse(value=body.response,revision=old.revision+1 if old else 1,updated_utc=timestamp)
                        elif body.action=='skip':
                            if not step.optional:raise SafeError('PRACTICE_SKIP_DENIED',409)
                            s.skipped_steps.append(step.id);s.current_step=step.next_step
                        elif body.action=='complete':
                            if step.kind!='completion':raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                            s.state='COMPLETED';s.completed_utc=timestamp
                        elif body.action=='next':
                            if step.kind=='completion':raise SafeError('PRACTICE_TRANSITION_INVALID',409)
                            if step.kind!='information' and step.id not in s.responses:
                                raise SafeError('PRACTICE_RESPONSE_REQUIRED',409)
                            s.current_step=step.next_step
                    s.revision=revision;s.updated_utc=timestamp;self.write_session(c,s)
                c.execute('INSERT INTO practice_receipts VALUES(?,?,?,?,?,?)',(op,id,body.action,fp,revision,'DELETED' if deleted else 'SAVED'))
        return {'id':id,'state':'DELETED','revision':revision} if deleted else self.view(s)

    @staticmethod
    def validate_response(step,value):
        valid=False
        if step.kind=='acknowledgement':valid=value is True
        elif step.kind in {'short_text','long_text'}:
            valid=isinstance(value,str) and bool(value.strip()) and len(value)<= (500 if step.kind=='short_text' else 12000)
        elif step.kind=='single_choice':valid=isinstance(value,str) and value in {x.id for x in step.choices}
        if not valid:raise SafeError('PRACTICE_RESPONSE_INVALID')
