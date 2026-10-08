"""Goal-scoped evaluation accounting and conservative included-usage gate.

No SDK calls here. This never enables the normal runtime or edits billing/settings.
"""
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from apps.core.storage import REPO, SafeError, digest, encode

GOAL='M8E_Q01_OWNER_2026_10_08'
MAXIMUM=24
ROOT=REPO/'research/evals/m8e_q01'
CANONICAL_LEDGER=REPO/'generated/m8e-q01/inference-attempts.sqlite3'
PROFILES={
    'FREE_LUNA_HIGH':('FREE','gpt-6-luna','high'),
    'DEEP_LUNA_MAX':('DEEP','gpt-6-luna','max'),
    'DEEP_SOL_HIGH':('DEEP','gpt-6.1-sol','high'),
}


def permission():
    path=ROOT/'permission_receipt.json'
    value=json.loads(path.read_text())
    if (value.get('goal')!=GOAL or value.get('authorized') is not True
            or value.get('scope')!='ORIGINAL_SYNTHETIC_ONLY'
            or type(value.get('maximum_inference_attempts')) is not int
            or value['maximum_inference_attempts']!=MAXIMUM
            or value.get('routes')!=['CODEX_SUBSCRIPTION']
            or value.get('count_fail_cancel_retry') is not True):
        raise SafeError('Q01_PERMISSION_REQUIRED',403)
    for field in ('purchased_credits_allowed','payg_allowed','new_auth_or_keys_allowed',
                  'model_provider_fallback_allowed','clinical_activation_allowed',
                  'private_owner_data_allowed','owner_pilot_access_or_install_allowed',
                  'global_live_provider_calls','global_permissions_changed'):
        if value.get(field) is not False:raise SafeError('Q01_SCOPE_DENIED',403)
    if type(value.get('additional_money_budget')) is not int or value['additional_money_budget']!=0:
        raise SafeError('Q01_SPEND_DENIED',403)
    expected={key:{'model':model,'effort':effort} for key,(_,model,effort) in zip(
        ('FREE','DEEP_ECONOMICAL','DEEP_QUALITY'),PROFILES.values())}
    if value.get('profiles')!=expected:raise SafeError('Q01_PROFILE_DENIED',403)
    return digest(path.read_bytes())


def included_usage_gate(snapshot, model):
    """Project only a boolean eligibility receipt; never retain account/credit values.

    ordinaryUsageAllowed is the SDK's account-validated included-usage permission.
    Null/absent is unknown. Percentages or reset clocks cannot manufacture permission.
    Credit-based/unknown plans and any available/unlimited credits fail closed here.
    """
    if not isinstance(snapshot,dict) or snapshot.get('ordinaryUsageAllowed') is not True:
        raise SafeError('Q01_INCLUDED_USAGE_UNVERIFIED',403)
    buckets=snapshot.get('rateLimitsByLimitId')
    if buckets is None:
        selected=[snapshot.get('rateLimits')]
    elif isinstance(buckets,dict) and buckets:
        if any(not isinstance(value,dict) for value in buckets.values()):
            raise SafeError('Q01_BILLING_METADATA_INVALID',403)
        selected=[value for value in buckets.values()
                  if value.get('normalModelSlug') in (None,model)]
    else:raise SafeError('Q01_BILLING_METADATA_INVALID',403)
    if not selected:raise SafeError('Q01_APPLICABLE_QUOTA_UNVERIFIED',403)
    for bucket in selected:
        if not isinstance(bucket,dict):raise SafeError('Q01_BILLING_METADATA_INVALID',403)
        if bucket.get('planType') not in {'plus','pro','prolite','promax'}:
            raise SafeError('Q01_INCLUDED_PLAN_UNVERIFIED',403)
        credits=bucket.get('credits')
        if not isinstance(credits,dict) or credits.get('hasCredits') is not False or credits.get('unlimited') is not False:
            raise SafeError('Q01_NO_PURCHASED_CREDITS_UNVERIFIED',403)
        balance=credits.get('balance')
        if balance is not None:
            try:
                if not isinstance(balance,str):raise ValueError()
                amount=Decimal(balance)
                if not amount.is_finite() or amount!=0:raise ValueError()
            except (InvalidOperation,ValueError):raise SafeError('Q01_NO_PURCHASED_CREDITS_UNVERIFIED',403) from None
        if bucket.get('spendControlReached') is True or bucket.get('rateLimitReachedType') is not None:
            raise SafeError('Q01_INCLUDED_USAGE_EXHAUSTED',429)
        for field in ('primary','secondary'):
            window=bucket.get(field)
            if window is None:continue
            if not isinstance(window,dict) or type(window.get('usedPercent')) is not int or not 0<=window['usedPercent']<=100:
                raise SafeError('Q01_BILLING_METADATA_INVALID',403)
            if window['usedPercent']>=100:raise SafeError('Q01_INCLUDED_USAGE_EXHAUSTED',429)
    return {'included_usage_allowed':True,'available_credits_absent':True,
            'included_plan_verified':True,'account_values_retained':False,
            'scope':'CURRENT_SDK_SNAPSHOT_ONLY_RECHECK_BEFORE_EACH_ATTEMPT'}


class EvaluationLedger:
    """One persistent goal counter; no refund, reset, alternate live path or retry slot."""
    def __init__(self,path=None,*,test_only=False):
        self.path=Path(path or CANONICAL_LEDGER).resolve()
        self.test_only=test_only
        if not test_only and self.path!=CANONICAL_LEDGER.resolve():
            raise SafeError('Q01_CANONICAL_LEDGER_REQUIRED',403)
        self.permission_hash=permission()
        plan_path=ROOT/'experiment_plan.json'
        self.plan=json.loads(plan_path.read_text())
        self.plan_hash=digest(plan_path.read_bytes())
        if self.plan.get('maximum_attempts')!=MAXIMUM or len(self.plan.get('slots',[]))>MAXIMUM:
            raise SafeError('Q01_PLAN_LIMIT_INVALID',403)
        if self.plan.get('profiles')!={name:{'mode':mode,'model':model,'effort':effort} for name,(mode,model,effort) in PROFILES.items()}:
            raise SafeError('Q01_PROFILE_DENIED',403)
        for name,expected in self.plan['frozen_inputs'].items():
            if Path(name).name!=name or digest((ROOT/name).read_bytes())!=expected:
                raise SafeError('Q01_FROZEN_INPUT_CHANGED',409)
        self.slots={slot['slot_id']:slot for slot in self.plan['slots']}
        if len(self.slots)!=len(self.plan['slots']):raise SafeError('Q01_DUPLICATE_PLAN_SLOT',409)
        if any(slot['phase'] not in {'BASELINE','CANDIDATE'} or slot['profile_id'] not in PROFILES for slot in self.slots.values()):
            raise SafeError('Q01_PROFILE_DENIED',403)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS q01_scope(id INTEGER PRIMARY KEY CHECK(id=1), goal TEXT NOT NULL, maximum INTEGER NOT NULL, permission_hash TEXT NOT NULL, plan_hash TEXT NOT NULL, test_only INTEGER NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS q01_attempts(id TEXT PRIMARY KEY, slot TEXT UNIQUE NOT NULL, profile TEXT NOT NULL, phase TEXT NOT NULL, payload_hash TEXT NOT NULL, started REAL NOT NULL, outcome TEXT NOT NULL, native_attempt_hash TEXT UNIQUE, native_outcome TEXT, final_error TEXT)')
            expected=(GOAL,MAXIMUM,self.permission_hash,self.plan_hash,int(test_only))
            existing=connection.execute('SELECT goal,maximum,permission_hash,plan_hash,test_only FROM q01_scope WHERE id=1').fetchone()
            if existing is None:connection.execute('INSERT INTO q01_scope VALUES(1,?,?,?,?,?)',expected)
            elif tuple(existing)!=expected:raise SafeError('Q01_LEDGER_SCOPE_CHANGED',409)

    def connect(self):
        return sqlite3.connect(self.path,timeout=10)

    def require_live(self):
        if self.test_only or self.path!=CANONICAL_LEDGER.resolve():raise SafeError('Q01_TEST_LEDGER_CANNOT_AUTHORIZE_LIVE',403)

    def begin(self,slot,payload_hash):
        if slot not in self.slots:raise SafeError('Q01_UNPLANNED_ATTEMPT',403)
        entry=self.slots[slot]
        if entry['profile_id'] not in PROFILES:raise SafeError('Q01_PROFILE_DENIED',403)
        if len(payload_hash)!=64 or any(c not in '0123456789abcdef' for c in payload_hash):
            raise SafeError('Q01_PAYLOAD_HASH_REQUIRED',403)
        identifier=str(uuid4())
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            if connection.execute('SELECT 1 FROM q01_attempts WHERE slot=?',(slot,)).fetchone():
                raise SafeError('Q01_SLOT_ALREADY_ATTEMPTED_NO_AUTOMATIC_RETRY',409)
            if connection.execute('SELECT COUNT(*) FROM q01_attempts').fetchone()[0]>=MAXIMUM:
                raise SafeError('Q01_ATTEMPT_LIMIT',429)
            connection.execute('INSERT INTO q01_attempts VALUES(?,?,?,?,?,?,?,?,?,?)',
                (identifier,slot,entry['profile_id'],entry['phase'],payload_hash,time.time(),'STARTED',None,None,None))
        return identifier

    def bind_native(self,identifier,native_id,route,model):
        if route!='CODEX_SUBSCRIPTION':raise SafeError('Q01_ROUTE_DENIED',403)
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row=connection.execute('SELECT profile,outcome,native_attempt_hash FROM q01_attempts WHERE id=?',(identifier,)).fetchone()
            if not row or row[1]!='STARTED' or row[2] is not None:raise SafeError('Q01_NATIVE_ATTEMPT_REUSE',409)
            if PROFILES[row[0]][1]!=model:raise SafeError('Q01_PROFILE_DENIED',403)
            connection.execute('UPDATE q01_attempts SET native_attempt_hash=? WHERE id=?',(digest(native_id.encode()),identifier))

    def native_finish(self,identifier,native_id,outcome):
        if outcome not in {'COMPLETED','FAILED','CANCELLED'}:raise SafeError('Q01_OUTCOME_INVALID')
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row=connection.execute('SELECT native_attempt_hash,native_outcome,outcome FROM q01_attempts WHERE id=?',(identifier,)).fetchone()
            if not row or row[0]!=digest(native_id.encode()) or row[1] is not None or row[2]!='STARTED':
                raise SafeError('Q01_NATIVE_ATTEMPT_REUSE',409)
            connection.execute('UPDATE q01_attempts SET native_outcome=? WHERE id=?',(outcome,identifier))

    def finish(self,identifier,outcome,error=None):
        if outcome not in {'COMPLETED','FAILED','CANCELLED'}:raise SafeError('Q01_OUTCOME_INVALID')
        # Keep failure provenance in the reviewed case record; the ledger never
        # accepts arbitrary error strings, account fields or raw provider text.
        code='EVALUATION_FAILED' if error is not None else None
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            changed=connection.execute('UPDATE q01_attempts SET outcome=?,final_error=? WHERE id=? AND outcome=?',(outcome,code,identifier,'STARTED'))
            if changed.rowcount!=1:raise SafeError('Q01_ATTEMPT_ALREADY_FINAL',409)

    def summary(self):
        with self.connect() as connection:
            total=connection.execute('SELECT COUNT(*) FROM q01_attempts').fetchone()[0]
            outcomes=dict(connection.execute('SELECT outcome,COUNT(*) FROM q01_attempts GROUP BY outcome'))
        return {'goal':GOAL,'maximum':MAXIMUM,'attempts':total,'remaining':MAXIMUM-total,'outcomes':outcomes,
                'test_only':self.test_only,'payloads_or_account_values_in_ledger':False}


class NativeAttemptLease:
    """Adapter's native reserve binds an already counted outer evaluation attempt."""
    def __init__(self,ledger,identifier):self.ledger=ledger;self.identifier=identifier
    def reserve(self,native_id,route,model):self.ledger.bind_native(self.identifier,native_id,route,model)
    def finish(self,native_id,outcome):self.ledger.native_finish(self.identifier,native_id,outcome)
