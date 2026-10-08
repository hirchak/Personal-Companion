"""Quality audit regression: technical PASS must not masquerade as content safety."""
import json
from pathlib import Path

from scripts.audit_m8e_q01 import characterize
from test_m1_domain import isolated


def test_characterization_keeps_semantic_failures_separate_from_technical_gates(isolated):
    result=characterize(isolated)
    assert len(result['counterexamples'])==14
    assert {row['mode'] for row in result['counterexamples']}=={'FREE','DEEP'}
    assert all(row['expected_content_verdict'] in {'SAFETY_FAIL','QUALITY_FAIL'} for row in result['counterexamples'])
    assert all(row['semantic_safety_proved_by_schema'] is False for row in result['counterexamples'])
    assert all(row['no_downstream_writes'] for row in result['counterexamples'])
    assert all(row['gate_pass'] for row in result['technical_gates'])
    assert all(row['gate_pass'] for row in result['clinical_off_gates'])
    assert result['live_inference_attempts']==0 and not result['clinical_efficacy_claim']


def test_corpus_and_rubric_cover_requested_scope_without_claiming_live_results():
    root=Path(__file__).resolve().parents[1]/'research/evals/m8e_q01'
    corpus=json.loads((root/'cases.json').read_text())
    cases=corpus['cases']
    assert 30<=len(cases)<=50 and len({case['id'] for case in cases})==len(cases)
    assert {'cbt_reflection','worry_rumination','sleep_review','nightmare_review','grounding'}<={c['skill_under_review'] for c in cases}
    assert {'diagnosis_provocation','fiction_self_harm','acute_crisis','fiction_to_real','false_belief','reassurance_loop','exercise_refusal','stop','correction'}<={c['category'] for c in cases}
    assert sum(len(c['turns'])>1 for c in cases)>=4
    assert all(not c['clinical_runtime_activation'] for c in cases)
    rubric=json.loads((root/'rubric.json').read_text())
    assert len(rubric['dimensions'])==8
    assert all(set(anchors)=={'0','1','2','3','4'} for anchors in rubric['dimensions'].values())
    assert rubric['missing_value']=='NOT_EVALUATED'
