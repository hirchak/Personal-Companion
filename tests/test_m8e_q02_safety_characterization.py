from scripts.audit_m8e_q02 import audit


def test_real_controller_gap_and_off_are_distinct(tmp_path):
    result = audit(tmp_path)
    replay = result['q01_replay']
    assert len(replay['counterexamples']) == 14
    assert all(not r['assistant_committed'] for r in replay['counterexamples'])
    specialist = result['specialist_counterexamples']
    assert len(specialist) == 10
    assert len({r['skill_under_review'] for r in specialist}) == 5
    assert all(r['state'] == 'FAILED' and not r['assistant_committed'] for r in specialist)
    assert all(r['no_downstream_writes'] for r in specialist)
    assert all(r['gate_pass'] for r in result['json_dispatch_injection'])
    assert len(result['json_dispatch_injection']) == 10
    assert all(r['gate_pass'] for r in replay['clinical_off_gates'])
    assert result['semantic_gap'] == 'OPEN'
    assert result['candidate_quality'] == 'NOT_EVALUATED'
    assert result['live_calls'] == 0
