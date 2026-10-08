import copy
from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from apps.core.storage import SafeError
from scripts.m8e_q01_budget import EvaluationLedger, NativeAttemptLease, included_usage_gate, ROOT


def eligible():
    return {'ordinaryUsageAllowed':True,'rateLimits':{'planType':'pro','credits':{'hasCredits':False,'unlimited':False,'balance':'0'},'primary':None,'secondary':{'usedPercent':20},'spendControlReached':False,'rateLimitReachedType':None}}


def test_included_usage_requires_authoritative_permission_not_percent_or_reset():
    assert included_usage_gate(eligible(),'gpt-6-luna')['included_usage_allowed']
    for value in (None,False,1,'true'):
        snapshot=eligible();snapshot['ordinaryUsageAllowed']=value
        with pytest.raises(SafeError,match='Q01_INCLUDED_USAGE_UNVERIFIED'):included_usage_gate(snapshot,'gpt-6-luna')
    snapshot=eligible();del snapshot['ordinaryUsageAllowed']
    with pytest.raises(SafeError):included_usage_gate(snapshot,'gpt-6-luna')


@pytest.mark.parametrize('credits',[None,{}, {'hasCredits':True,'unlimited':False,'balance':'1'}, {'hasCredits':False,'unlimited':True}, {'hasCredits':False,'unlimited':False,'balance':'NaN'}, {'hasCredits':False,'unlimited':False,'balance':'0.1'}, {'hasCredits':False,'unlimited':False,'balance':0}])
def test_no_purchased_credits_is_fail_closed(credits):
    snapshot=eligible();snapshot['rateLimits']['credits']=credits
    with pytest.raises(SafeError):included_usage_gate(snapshot,'gpt-6-luna')


@pytest.mark.parametrize('change',[{'planType':'enterprise_cbp_usage_based'},{'planType':'unknown'},{'spendControlReached':True},{'rateLimitReachedType':'workspace_member_credits_depleted'},{'secondary':{'usedPercent':100}},{'secondary':{'usedPercent':False}}])
def test_unknown_or_exhausted_financial_route_cannot_be_inferred_safe(change):
    snapshot=eligible();snapshot['rateLimits'].update(change)
    with pytest.raises(SafeError):included_usage_gate(snapshot,'gpt-6.1-sol')


def test_stricter_applicable_bucket_and_account_fields_are_not_retained():
    snapshot=eligible();snapshot['accountId']='ORIGINAL_SYNTHETIC_ACCOUNT_SENTINEL'
    snapshot['rateLimitsByLimitId']={'codex':copy.deepcopy(snapshot['rateLimits']),'selected':{**copy.deepcopy(snapshot['rateLimits']),'normalModelSlug':'gpt-6-luna','secondary':{'usedPercent':100}}}
    with pytest.raises(SafeError):included_usage_gate(snapshot,'gpt-6-luna')
    del snapshot['rateLimitsByLimitId']
    receipt=included_usage_gate(snapshot,'gpt-6-luna')
    assert 'SENTINEL' not in json.dumps(receipt) and 'balance' not in json.dumps(receipt)


def test_persistent_count_includes_failure_cancel_and_interrupted_attempts(tmp_path):
    path=tmp_path/'ORIGINAL_SYNTHETIC_Q01.sqlite3'
    ledger=EvaluationLedger(path,test_only=True)
    slots=list(ledger.slots)
    first=ledger.begin(slots[0],'a'*64);ledger.finish(first,'FAILED','ORIGINAL_SYNTHETIC_SECRET_LIKE_ERROR')
    second=ledger.begin(slots[1],'b'*64);ledger.finish(second,'CANCELLED')
    ledger.begin(slots[2],'c'*64)
    again=EvaluationLedger(path,test_only=True)
    assert again.summary()['attempts']==3 and again.summary()['remaining']==21
    assert again.summary()['outcomes']=={'FAILED':1,'CANCELLED':1,'STARTED':1}
    with pytest.raises(SafeError):again.begin(slots[0],'a'*64)
    with pytest.raises(SafeError):again.finish(first,'COMPLETED')
    with pytest.raises(SafeError):again.require_live()
    with ledger.connect() as connection:
        assert 'SECRET_LIKE' not in str(connection.execute('SELECT * FROM q01_attempts').fetchall())


def test_concurrent_budget_cannot_exceed_frozen_twenty_four_slots(tmp_path):
    ledger=EvaluationLedger(tmp_path/'ORIGINAL_SYNTHETIC_Q01.sqlite3',test_only=True)
    slots=list(ledger.slots)
    def reserve(slot):
        try:return ledger.begin(slot,'a'*64)
        except SafeError:return None
    with ThreadPoolExecutor(max_workers=8) as pool:ids=list(pool.map(reserve,slots+slots))
    assert len([i for i in ids if i])==24
    assert ledger.summary()['attempts']==24 and ledger.summary()['remaining']==0
    with pytest.raises(SafeError):ledger.begin('UNPLANNED_RETRY','b'*64)


def test_native_transport_and_controller_outcomes_are_separate_and_count_once(tmp_path):
    ledger=EvaluationLedger(tmp_path/'ORIGINAL_SYNTHETIC_Q01.sqlite3',test_only=True)
    identifier=ledger.begin('BASELINE_Q02_FREE_LUNA_HIGH','a'*64)
    lease=NativeAttemptLease(ledger,identifier)
    lease.reserve('ORIGINAL_SYNTHETIC_LOCAL_ATTEMPT','CODEX_SUBSCRIPTION','gpt-6-luna')
    with pytest.raises(SafeError):lease.reserve('SECOND','CODEX_SUBSCRIPTION','gpt-6-luna')
    lease.finish('ORIGINAL_SYNTHETIC_LOCAL_ATTEMPT','COMPLETED')
    ledger.finish(identifier,'FAILED','MODEL_SOURCE_OUT_OF_SCOPE')
    assert ledger.summary()['attempts']==1 and ledger.summary()['outcomes']=={'FAILED':1}
    with ledger.connect() as connection:
        assert connection.execute('SELECT native_outcome FROM q01_attempts').fetchone()[0]=='COMPLETED'


def test_alternate_live_ledger_path_is_refused(tmp_path):
    with pytest.raises(SafeError,match='Q01_CANONICAL_LEDGER_REQUIRED'):
        EvaluationLedger(tmp_path/'would_reset_budget.sqlite3')
