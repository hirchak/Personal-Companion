"""Synthetic device transport. Domain writes/receipts/checkpoints commit together."""
import secrets
import threading
import time
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4
from pydantic import Field, model_validator, field_validator, field_serializer
from .models import StrictModel, EntryInput, Create, Patch, Delete
from .storage import SafeError, digest, encode, now

class Pair(StrictModel):
    invitation: str = Field(min_length=1, max_length=128)
    device_id: UUID
    label: str = Field(min_length=1, max_length=64)

class Packet(StrictModel):
    operation_id: UUID
    device_id: UUID
    entry_id: UUID
    base_revision: int = Field(ge=0, strict=True)
    operation_type: Literal['create','edit','delete']
    created_at_utc: datetime
    timezone: str = 'Europe/Warsaw'
    schema_version: Literal[2]
    local_sequence: int = Field(ge=1, strict=True)
    payload: EntryInput | None = None
    confirm_type_change: bool = False
    @field_validator('created_at_utc', mode='before')
    @classmethod
    def no_epoch(cls, v): return EntryInput.no_epoch_coercion(v)
    @field_validator('created_at_utc')
    @classmethod
    def aware(cls, v): return EntryInput.aware(v)
    @field_validator('timezone')
    @classmethod
    def zone(cls, v): return EntryInput.zone(v)
    @field_serializer('payload')
    def payload_wire(self, value):
        return value.payload() if value else None

    @model_validator(mode='after')
    def valid_operation(self):
        if self.operation_type == 'create' and self.base_revision != 0:
            raise ValueError('create revision')
        if self.operation_type != 'create' and self.base_revision < 1:
            raise ValueError('base revision')
        if (self.operation_type == 'delete') != (self.payload is None):
            raise ValueError('payload/action')
        return self

class EpochReset(StrictModel):
    prune_tombstones: bool = False

class SyncService:
    def __init__(self, journal, clock=time.monotonic):
        self.journal, self.store, self.clock = journal, journal.store, clock
        self.invitations, self.attempts = {}, []
        self.lock = threading.Lock()

    def epoch(self, c):
        generation = c.execute('SELECT generation FROM sync_meta WHERE id=1').fetchone()[0]
        restored = c.execute('SELECT restore_epoch FROM vault_meta').fetchone()[0]
        return f'{generation}:{restored}'

    def invite(self):
        with self.store.connect() as c:
            epoch = self.epoch(c)
        with self.lock:
            self.invitations = {k:v for k,v in self.invitations.items() if v['expires'] > self.clock()}
            if len(self.invitations) >= 20: raise SafeError('INVITATION_LIMIT', 429)
            code = secrets.token_urlsafe(24)
            self.invitations[digest(code.encode())] = {'expires':self.clock()+300,'epoch':epoch}
        return {'invitation':code,'expires_in':300,'scope':'JOURNAL_SYNC_SYNTHETIC'}

    def pair(self, request):
        with self.lock:
            t = self.clock(); self.attempts = [x for x in self.attempts if t-x < 60]
            if len(self.attempts) >= 5: raise SafeError('PAIR_RATE_LIMIT', 429)
            self.attempts.append(t)
            key = digest(request.invitation.encode('utf-8', 'surrogatepass'))
            plan = self.invitations.get(key)
            if not plan or plan['expires'] <= t: raise SafeError('PAIR_DENIED', 401)
            token = secrets.token_urlsafe(32)
            with self.store.transaction() as c:
                epoch = self.epoch(c)
                if plan['epoch'] != epoch: raise SafeError('REPAIR_REQUIRED', 409)
                id = str(request.device_id)
                # Re-pair requires a new owner-issued invitation; old token is replaced.
                c.execute("INSERT INTO devices(id,owner_id,label,credential_hash,epoch,created_at_utc,revoked_at_utc,pair_state,pending_until) VALUES(?,?,?,?,?,?,NULL,'PENDING',?) ON CONFLICT(id) DO UPDATE SET label=excluded.label,credential_hash=excluded.credential_hash,epoch=excluded.epoch,created_at_utc=excluded.created_at_utc,revoked_at_utc=NULL,pair_state='PENDING',pending_until=excluded.pending_until",
                          (id,self.journal.owner,request.label,digest(token.encode()),epoch,now(),time.time()+300))
                c.execute('INSERT OR REPLACE INTO sync_checkpoints VALUES(?,?,0)', (id,epoch))
            self.invitations.pop(key, None)  # only after committed pairing
        return {'device_id':id,'credential':token,'epoch':epoch,'scope':'JOURNAL_SYNC_SYNTHETIC','state':'PENDING','expires_in':300}

    def authenticate(self, c, device, token, expected_epoch, allow_pending=False):
        try: id = str(UUID(device))
        except (ValueError, TypeError): raise SafeError('DEVICE_DENIED',401) from None
        d = c.execute('SELECT * FROM devices WHERE id=? AND owner_id=?',(id,self.journal.owner)).fetchone()
        if not d or not secrets.compare_digest(d['credential_hash'],digest(token.encode('utf-8','surrogatepass'))):
            raise SafeError('DEVICE_DENIED',401)
        if d['revoked_at_utc']: raise SafeError('DEVICE_REVOKED',403)
        if d['epoch'] != self.epoch(c) or expected_epoch != self.epoch(c):
            raise SafeError('REPAIR_REQUIRED',409)
        if d['pair_state'] == 'PENDING':
            if not allow_pending or d['pending_until'] <= time.time(): raise SafeError('PAIR_PENDING_RETRY_OR_REVOKE',409)
        return id

    def finalize(self, device, token, epoch):
        with self.store.transaction() as c:
            id = self.authenticate(c,device,token,epoch,allow_pending=True)
            c.execute("UPDATE devices SET pair_state='ACTIVE',pending_until=NULL WHERE id=?",(id,))
        return {'device_id':id,'state':'ACTIVE'}

    def devices(self):
        with self.store.connect() as c:
            return {'items':[{'device_id':r['id'],'label':r['label'],'created_at_utc':r['created_at_utc'],
                             'state':'REVOKED' if r['revoked_at_utc'] else ('PENDING_EXPIRED' if r['pending_until'] <= time.time() else 'PENDING') if r['pair_state']=='PENDING' else 'ACTIVE' if r['epoch']==self.epoch(c) else 'REPAIR_REQUIRED'}
                            for r in c.execute('SELECT * FROM devices WHERE owner_id=? ORDER BY created_at_utc,id',(self.journal.owner,))],
                    'warning':'Відкликання не видаляє офлайн копію на пристрої.'}

    def revoke(self, device):
        with self.store.transaction() as c:
            row = c.execute('SELECT 1 FROM devices WHERE id=? AND owner_id=?',(str(device),self.journal.owner)).fetchone()
            if not row: raise SafeError('NOT_FOUND',404)
            c.execute('UPDATE devices SET revoked_at_utc=? WHERE id=?',(now(),str(device)))
        return {'state':'REVOKED','remote_erase':False}

    def rotate(self, prune=False):
        with self.store.transaction() as c:
            c.execute('UPDATE sync_meta SET generation=?,change_seq=change_seq+1 WHERE id=1',(str(uuid4()),))
            c.execute('UPDATE devices SET revoked_at_utc=COALESCE(revoked_at_utc,?)',(now(),))
            if prune:
                c.execute('DELETE FROM tombstones')  # every old credential/epoch already invalid
            epoch = self.epoch(c)
        return {'epoch':epoch,'state':'REPAIR_REQUIRED','tombstones_pruned':prune}

    def snapshot(self, device, token, epoch):
        with self.store.transaction() as c:
            id = self.authenticate(c,device,token,epoch)
            sequence = c.execute('SELECT change_seq FROM sync_meta WHERE id=1').fetchone()[0]
            entries = [self.journal.view(r) for r in c.execute('SELECT * FROM entries WHERE owner_id=? ORDER BY created DESC,id DESC',(self.journal.owner,))]
            deleted = [{'id':r['entry_id'],'revision':r['revision']} for r in c.execute('SELECT * FROM tombstones WHERE owner_id=?',(self.journal.owner,))]
            c.execute('INSERT OR REPLACE INTO sync_checkpoints VALUES(?,?,?)',(id,epoch,sequence))
            result = {'epoch':epoch,'checkpoint':sequence,'entries':entries,'tombstones':deleted,'schema_version':2}
        return result

    def apply(self, packet, device, token, epoch):
        fp = digest(encode(packet.model_dump(mode='json')).encode())
        with self.store.transaction() as c:
            id = self.authenticate(c,device,token,epoch)
            if str(packet.device_id) != id: raise SafeError('DEVICE_DENIED',403)
            entry, op = str(packet.entry_id), str(packet.operation_id)
            dead = c.execute('SELECT revision FROM tombstones WHERE entry_id=? AND owner_id=?',(entry,self.journal.owner)).fetchone()
            existing = c.execute('SELECT * FROM sync_receipts WHERE operation_id=?',(op,)).fetchone()
            if existing and existing['device_id'] != id: raise SafeError('OPERATION_REUSE',409)
            if dead and packet.operation_type != 'delete':
                return {'state':'CONFLICT','code':'DELETED','operation_id':op,'revision':dead['revision'],'current':None}
            if existing:
                if existing['fingerprint'] != fp: raise SafeError('OPERATION_REUSE',409)
                state, rev = existing['state'], existing['revision']
            else:
                if packet.operation_type == 'create':
                    request = Create(operation_id=packet.operation_id,entry_id=packet.entry_id,base_revision=0,payload=packet.payload)
                elif packet.operation_type == 'edit':
                    request = Patch(operation_id=packet.operation_id,base_revision=packet.base_revision,changes=packet.payload.payload(),confirm_type_change=packet.confirm_type_change)
                else:
                    request = Delete(operation_id=packet.operation_id,base_revision=packet.base_revision)
                try:
                    receipt = self.journal.write_in(c,packet.operation_type,entry,request)
                    state, rev = 'MAC_CONFIRMED', receipt['revision']
                except SafeError as e:
                    if e.status not in (409,410): raise
                    if e.code == 'OPERATION_REUSE': raise
                    state, rev = 'CONFLICT', None
                c.execute('INSERT INTO sync_receipts VALUES(?,?,?,?,?,?,?)',(op,id,entry,packet.operation_type,fp,state,rev))
            current = None
            try: current = self.journal.view(self.journal.row(c,entry))
            except SafeError: pass
            seq = c.execute('SELECT change_seq FROM sync_meta WHERE id=1').fetchone()[0]
            c.execute('INSERT OR REPLACE INTO sync_checkpoints VALUES(?,?,?)',(id,epoch,seq))
            result = {'state':state,'operation_id':op,'revision':rev,'current':current,'checkpoint':seq,'epoch':epoch}
        return result  # never before commit
