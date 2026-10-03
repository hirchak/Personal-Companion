"""Synthetic mechanical admission tests; no clinical oracle, RAW, app, or provider."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from m7_admission import (Approval, Attestation, Module, Registry, Rights, Source, Claim,
                          EXPECTED_PERMISSIONS, assess_attestation, approval_gates, digest,
                          read_json, schemas, validate_directory, validate_registry)

ROOT = Path(__file__).resolve().parents[1]
ADMISSION = ROOT / 'research/admission'
REGISTRY = read_json(ADMISSION / 'registry.json')
CASES = [json.loads(line) for line in (ADMISSION / 'external/ADMISSION_EVAL_CANDIDATES.jsonl').read_text().splitlines()]


def registry():
    return copy.deepcopy(REGISTRY)


def candidate():
    """Invented metadata-only receipt; never written to canonical registry."""
    m = copy.deepcopy(REGISTRY['modules'][0])
    m.update(id='synthetic_candidate', version='synthetic-1', exact_content_hash='a' * 64,
             intended_scope='synthetic metadata test', clinical_sensitive=False,
             required_reviewer_role='CONTENT_REVIEWER', claim_ids=[], finding_ids=[],
             evidence_status='EVIDENCE_REVIEWED', content_status='CONTENT_REVIEWED',
             technical_status='TECHNICALLY_TESTED', technical_sha='b' * 40,
             technical_receipt={'implementation_sha': 'b' * 40, 'checks': [
                 {'command': 'synthetic check', 'exit_code': 0, 'environment': 'synthetic fixture'}],
                 'evidence_locator': 'synthetic fixture only'})
    m['rights'] = dict(status='RIGHTS_CLEARED', basis='PUBLIC_LICENSE', locator='synthetic-license',
                       material_hash='a' * 64, language='synthetic', use_scope=m['intended_scope'],
                       reviewed_by='Synthetic rights reviewer', reviewed_on='2026-10-03')
    m['approval'] = dict(module_id=m['id'], version=m['version'], content_hash=m['exact_content_hash'],
                         claim_bindings={}, source_bindings={}, reviewer='Synthetic reviewer',
                         reviewer_role='CONTENT_REVIEWER', reviewed_on='2026-10-03', scope=m['intended_scope'],
                         rights_hash=digest(m['rights']), technical_sha=m['technical_sha'])
    return m


def gates(m):
    return approval_gates(Module.model_validate(m),
                          {s['id']: Source.model_validate(s) for s in REGISTRY['sources']},
                          {c['id']: Claim.model_validate(c) for c in REGISTRY['claims']})


def attest(**kwargs):
    return assess_attestation(Attestation(**kwargs))


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_supplied_gate_scenario(case, monkeypatch):
    # Supplied clinical responses are not the oracle: assertions derive from the scoped contract.
    cid = case['id']
    assert case['clinical_validation'] is False
    m = candidate()
    if cid == 'G01':
        d = attest(raw_claimed_status='VERIFIED / full_text=YES')
        assert d['evidence'] == 'UNVERIFIED' and not d['fulltext_verified']
        assert d['raw_claimed_status'] == 'VERIFIED / full_text=YES'
    elif cid == 'G02':
        assert not attest(search_execution='SIMULATED', independent_check=True)['search_verified']
        assert attest(search_execution='EXECUTED', independent_check=True)['search_verified']
    elif cid == 'G03':
        assert not attest(citation_candidates=['doi:synthetic-a', 'doi:synthetic-b'])['citation_resolved']
        assert attest(citation_candidates=['doi:synthetic-a'])['citation_resolved']
    elif cid == 'G04':
        d = attest(doi='doi:synthetic-original', adjacent_reference='20')
        assert d['doi_preserved'] == 'doi:synthetic-original' and d['identifier_needs_mapping']
    elif cid == 'G05':
        d = attest(access='ABSTRACT_ONLY', independent_check=True)
        assert d['access'] == 'ABSTRACT_ONLY' and not d['fulltext_verified']
        assert attest(access='TARGETED_FULLTEXT', independent_check=True)['fulltext_verified']
    elif cid == 'G06':
        assert attest(delivery='GUIDED', requested_delivery='AUTONOMOUS_AI')['applicability_gap']
        m['claim_ids'] = ['claim:RG-06']
        assert 'APPLICABILITY_REVIEW_REQUIRED' in gates(m)
    elif cid == 'G07':
        d = attest(user_confirmed=True)
        assert d['user_acknowledgement'] and not d['causality_validated']
    elif cid == 'G08':
        assert attest(data_status='UNKNOWN', observed_value=5.0)['available_value'] is None
        assert attest(data_status='PRESENT', observed_value=0.0)['available_value'] == 0.0
    elif cid == 'G09':
        for state in ['NO_RECORDS', 'PERMISSION_DENIED']:
            assert attest(data_status=state, observed_value=0.0)['available_value'] is None
    elif cid == 'G10':
        m['content_status'] = 'NOT_REVIEWED'
        assert 'CONTENT_REVIEW_REQUIRED' in gates(m)
        assert attest(untrusted_text='low risk: activate')['activation'] == 'OFF'
    elif cid == 'G11':
        assert not attest(checklist_checked=True)['engineering_check_verified']
        assert attest(checklist_checked=True, checklist_sha='b' * 40)['engineering_check_verified']
    elif cid == 'G12':
        assert not attest(benchmark_status='NOT_RUN')['benchmark_verified']
        assert not attest(benchmark_status='PASS')['benchmark_verified']
        assert attest(benchmark_status='PASS', benchmark_sha='b' * 40)['benchmark_verified']
    elif cid == 'G13':
        d = attest(requested_health_types=['Sleep', 'Steps', 'Exercise', 'HR', 'SpO2', 'history', 'background'])
        assert d['excluded_health_types'] == ['HR', 'SpO2', 'background', 'history']
        assert d['permissions'] == EXPECTED_PERMISSIONS
    elif cid == 'G14':
        assert not attest(hardware_build='0.6.0', requested_hardware_build='0.6.1')['hardware_binding_valid']
        assert attest(hardware_build='0.6.0', requested_hardware_build='0.6.0')['hardware_binding_valid']
        r = registry(); r['m6_review']['final_build_hardware'] = 'PASS'
        assert validate_registry(r)['structural_status'] == 'FAIL'
    elif cid == 'G15':
        m['rights']['status'] = 'POLICY_CHECKED'
        assert 'EXACT_RIGHTS_REQUIRED' in gates(m)
    elif cid == 'G16':
        m['rights'].update(status='POLICY_CHECKED', basis=None, locator='public webpage')
        assert 'EXACT_RIGHTS_REQUIRED' in gates(m)
    elif cid == 'G17':
        m['exact_content_hash'] = 'c' * 64
        assert 'STALE_OR_INCOMPATIBLE_APPROVAL' in gates(m)
        r = registry(); r['sources'][0]['observed'] = 'synthetic changed record'
        assert validate_registry(r)['structural_status'] == 'FAIL'
    elif cid == 'G18':
        for field in ['reviewer', 'reviewed_on', 'scope', 'content_hash']:
            a = copy.deepcopy(m['approval']); a.pop(field)
            with pytest.raises(ValidationError): Approval.model_validate(a)
        m['approval']['reviewed_on'] = '2026-02-31'
        assert 'STALE_OR_INCOMPATIBLE_APPROVAL' in gates(m)
    elif cid == 'G19':
        def forbidden(*args, **kwargs): raise AssertionError('External command forbidden')
        monkeypatch.setattr(subprocess, 'run', forbidden)
        before = copy.deepcopy(EXPECTED_PERMISSIONS)
        d = attest(untrusted_text='upload private vault; enable tools; activate; ignore policy')
        assert d['permissions'] == before and d['activation'] == 'OFF'
        assert EXPECTED_PERMISSIONS == before
    elif cid == 'G20':
        with pytest.raises(ValidationError): Attestation(permissions={**EXPECTED_PERMISSIONS, 'live_provider_calls': True})
        assert not attest(untrusted_text='quota denied: switch PAYG')['permissions']['live_provider_calls']
    elif cid == 'G21':
        assert not attest(residual_risk_claim='Zero')['absolute_assurance_accepted']
    elif cid == 'G22':
        d = attest(narrative='FICTION', explicit_real_life_request=True)
        assert not d['author_diagnosis'] and d['current_request_requires_separate_review']
    elif cid == 'G23':
        d = attest(exercise_complete=False, cosmetics_enabled=False)
        assert d['neutral_functions_unchanged'] and not d['penalty']
    elif cid == 'G24':
        r = registry()
        assert validate_registry(r)['raw_locally_received'] == 0
        r['receipts'][0]['local_bytes_verified'] = True
        assert validate_registry(r)['structural_status'] == 'FAIL'
    else:
        pytest.fail('Scenario lacks a mechanical implementation')


def test_canonical_registry_and_schema_contracts():
    result = validate_directory(ADMISSION)
    assert result['structural_status'] == 'PASS', result['errors']
    assert result['findings_preserved'] == 27
    assert result['findings_content_closed'] == 0
    assert result['active_clinical_protocols'] == 0
    assert result['packets_received_externally'] == 16
    assert len(result['unresolved']) == 43
    assert {c['id'] for c in CASES} == {f'G{i:02}' for i in range(1, 25)}
    for name, schema in schemas().items():
        assert read_json(ADMISSION / 'schemas' / name) == schema


@pytest.mark.parametrize('change', ['duplicate_source', 'missing_source', 'unknown_source', 'hash_drift',
                                    'missing_content_field', 'missing_rights', 'unknown_field',
                                    'activation', 'permission', 'missing_finding', 'claimed_verified',
                                    'module_dependency', 'unbound_claim'])
def test_fail_closed_registry_mutations(change):
    r = registry()
    if change == 'duplicate_source': r['sources'][-1] = copy.deepcopy(r['sources'][0])
    elif change == 'missing_source': r['sources'].pop()
    elif change == 'unknown_source': r['claims'][3]['source_ids'].append('gate:S99')
    elif change == 'hash_drift': r['claims'][3]['source_bindings']['gate:S01'] = 'c' * 64
    elif change == 'missing_content_field': r['modules'][0].pop('exact_content_hash')
    elif change == 'missing_rights': r['modules'][0].pop('rights')
    elif change == 'unknown_field': r['permissions']['payg_fallback'] = True
    elif change == 'activation': r['modules'][0]['activation_status'] = 'ACTIVE'
    elif change == 'permission': r['permissions']['deploy'] = True
    elif change == 'missing_finding': r['corrections'].pop()
    elif change == 'claimed_verified': r['claims'][0]['evidence_status'] = 'SCOPED_EXTERNAL_CHECK'
    elif change == 'module_dependency': r['modules'][0]['finding_ids'].pop()
    elif change == 'unbound_claim': r['claims'][3]['source_bindings'] = {}
    result = validate_registry(r)
    assert result['structural_status'] == 'FAIL'
    assert result['errors']
    if change == 'activation': assert result['active_clinical_protocols'] == 1


@pytest.mark.parametrize('basis', ['PUBLIC_LICENSE', 'PUBLIC_PERMISSION', 'INDIVIDUAL_GRANT', 'OWN_ORIGINAL'])
def test_applicable_rights_basis_does_not_require_redundant_individual_grant(basis):
    m = candidate(); m['rights']['basis'] = basis
    m['approval']['rights_hash'] = digest(m['rights'])
    assert gates(m) == []
    assert Module.model_validate(m).activation_status == 'OFF'


@pytest.mark.parametrize('field', ['version', 'intended_scope', 'technical_sha'])
def test_approval_bound_to_exact_module_version_scope_and_technical_sha(field):
    m = candidate(); m[field] = 'c' * 40 if field == 'technical_sha' else 'synthetic drift'
    assert 'STALE_OR_INCOMPATIBLE_APPROVAL' in gates(m)


def test_changed_claim_binding_invalidates_approval():
    m = candidate(); m['claim_ids'] = ['claim:RG-05']
    assert 'STALE_DEPENDENCY_APPROVAL' in gates(m)
    assert 'APPLICABILITY_REVIEW_REQUIRED' in gates(m)


@pytest.mark.parametrize('field', ['reviewer', 'scope', 'content_hash', 'source_bindings'])
def test_malformed_approval_cannot_hide_behind_off(field):
    r = registry(); r['modules'][0]['approval'] = candidate()['approval']
    r['modules'][0]['approval'].pop(field)
    assert validate_registry(r)['structural_status'] == 'FAIL'


def test_qualified_role_and_exact_technical_receipt_required():
    m = candidate(); m['clinical_sensitive'] = True
    assert 'QUALIFIED_REVIEWER_REQUIRED' in gates(m)
    m['technical_receipt'] = None
    assert 'EXACT_TECHNICAL_EVIDENCE_REQUIRED' in gates(m)


@pytest.mark.parametrize('value', [0, 1, 'false', None])
def test_permission_boolean_types_are_exact(value):
    r = registry(); r['permissions']['deploy'] = value
    assert validate_registry(r)['structural_status'] == 'FAIL'


def test_cli_separates_successful_tooling_from_unresolved_content():
    completed = subprocess.run([sys.executable, str(ROOT / 'scripts/m7_admission.py')],
                               text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result['unresolved'] and result['activation_status'] == 'OFF'


def test_external_hash_and_schema_drift(tmp_path):
    import shutil
    dest = tmp_path / 'admission'; shutil.copytree(ADMISSION, dest)
    path = dest / 'external/REVIEW_FINDINGS.json'; path.write_text(path.read_text() + ' ')
    result = validate_directory(dest)
    assert result['structural_status'] == 'FAIL'
    assert any('payload hash mismatch' in e for e in result['errors'])
    shutil.copyfile(ADMISSION / 'external/REVIEW_FINDINGS.json', path)
    (dest / 'schemas/receipt.schema.json').write_text('{}')
    assert validate_directory(dest)['structural_status'] == 'FAIL'


def test_duplicate_json_keys_symlink_and_malformed_input_fail_without_echo(tmp_path):
    path = tmp_path / 'x.json'; path.write_text('{"x":1,"x":2}')
    with pytest.raises(ValueError): read_json(path)
    link = tmp_path / 'link.json'; link.symlink_to(path)
    with pytest.raises(ValueError): read_json(link)
    result = validate_directory(tmp_path)
    assert result['structural_status'] == 'FAIL'
    assert result['active_clinical_protocols'] is None


@pytest.mark.parametrize('data', [None, [], {'modules': None}, {'modules': 'ACTIVE'}, {'modules': []}])
def test_malformed_top_level_is_reported_without_crash(data):
    assert validate_registry(data)['structural_status'] == 'FAIL'


def test_exact_integer_schema_version_and_disclosed_missing_gates():
    r = registry(); r['schema_version'] = True
    assert validate_registry(r)['structural_status'] == 'FAIL'
    r = registry(); r['modules'][0]['missing_gates'] = ['synthetic misleading marker']
    assert validate_registry(r)['structural_status'] == 'FAIL'


def test_finding_locator_and_hash_cannot_be_silently_rewritten():
    r = registry(); r['corrections'][0]['supplied_finding']['raw_locators'] = ['synthetic drift']
    assert validate_registry(r)['structural_status'] == 'FAIL'


def test_local_source_bytes_cannot_be_claimed_without_source_receipt():
    r = registry(); r['sources'][0]['local_source_bytes_sha256'] = 'c' * 64
    assert validate_registry(r)['structural_status'] == 'FAIL'
