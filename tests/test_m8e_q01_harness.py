import json

import pytest

from apps.core import local_private
from apps.core.storage import SafeError, encode
from scripts.evaluate_m8e_q01 import run_case, require_fresh_proof, verify_baseline_generation, SENTINEL
from scripts.m8e_q01_budget import ROOT


def inputs():
    plan=json.loads((ROOT/'experiment_plan.json').read_text())
    cases={case['id']:case for case in json.loads((ROOT/'cases.json').read_text())['cases']}
    return plan,cases


@pytest.mark.parametrize('slot_id',['BASELINE_Q02_FREE_LUNA_HIGH','BASELINE_Q24_DEEP_LUNA_MAX','BASELINE_Q17_DEEP_SOL_HIGH'])
def test_disposable_private_contract_rehearsal_is_not_live_or_quality_evidence(monkeypatch,slot_id):
    monkeypatch.setattr(local_private,'volume_protection',lambda path:'PASS')
    plan,cases=inputs();slot=next(item for item in plan['slots'] if item['slot_id']==slot_id)
    result=run_case(slot,cases[slot['case_id']],plan['context_seeds'][slot['case_id']],offline=True)
    assert result['state']=='COMPLETED',result['error']
    assert result['origin']=='OFFLINE_SCRIPTED_FIXTURE_NOT_MODEL_QUALITY'
    assert result['quality_assessment']=='NOT_EVALUATED' and result['evaluation_attempt_id'] is None
    assert result['no_downstream_writes'] and not result['real_private_data_used'] and not result['owner_pilot_accessed']
    assert SENTINEL not in encode(result['payload'])
    assert result['payload']['synthetic'] is False and result['payload']['tool_permissions']==[]
    assert result['clinical_active']==0


def test_scripted_context_is_identical_for_matched_deep_profiles_and_arms(monkeypatch):
    monkeypatch.setattr(local_private,'volume_protection',lambda path:'PASS')
    plan,cases=inputs();case=cases['Q24'];results=[]
    for slot_id in ['BASELINE_Q24_DEEP_LUNA_MAX','BASELINE_Q24_DEEP_SOL_HIGH','CANDIDATE_Q24_DEEP_LUNA_MAX']:
        slot=next(item for item in plan['slots'] if item['slot_id']==slot_id)
        results.append(run_case(slot,case,plan['context_seeds']['Q24'],offline=True))
    assert all(row['state']=='COMPLETED' for row in results)
    assert len({row['comparison_context_sha256'] for row in results})==1
    assert all(any(item['state']=='REJECTED' for item in row['payload']['reflection_state']['items']) for row in results)


def test_mock_or_missing_metadata_cannot_authorize_live():
    for proof in [None,{}, {'status':'PASS','verification_source':'INJECTED_TEST_PROVIDER_NOT_LIVE'}]:
        with pytest.raises(SafeError,match='Q01_NATIVE_METADATA_PROOF_REQUIRED'):require_fresh_proof(proof)


def test_frozen_q01_baseline_rejects_new_q03_controller():
    # Q01's frozen audit must not silently relabel the Q03 release controller as
    # its historical baseline or authorize reuse of the old inference allowance.
    with pytest.raises(SafeError,match='Q01_BASELINE_GENERATION_CHANGED'):
        verify_baseline_generation()
