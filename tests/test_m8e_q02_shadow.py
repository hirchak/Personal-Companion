import hashlib
import json

import pytest

from scripts.m8e_q02_shadow import ShadowError, inspect_bundle, SKILLS, REPO
from apps.core.conversation_skills import ConversationSkills
from apps.core.storage import SafeError


def write(path, value):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    cases = []; bundles = []; pairs = []; mapping = []
    for skill in sorted(SKILLS):
        examples = []
        for n in range(10):
            case = {'id': skill + str(n), 'skill': skill, 'user_turns': ['ORIGINAL SYNTHETIC INPUT']}
            cases.append(case)
            examples.append({'case_id': case['id'], 'user_turns': case['user_turns'],
                             'provenance': 'ORIGINAL_AUTHOR_EXAMPLE_NOT_MODEL_OUTPUT',
                             'authored_candidate_response': 'ORIGINAL SYNTHETIC RESPONSE',
                             'author_explanation': 'Fixture only.'})
        candidate = {'skill_id': skill, 'version': 'test', 'activation_state': 'OFF',
                     'status': 'CANDIDATE_OFF', 'runtime_instructions': None, 'draft_only': True,
                     'proposed_output': {'writes': [], 'tools': [], 'practice_reference': None},
                     'practice_proposal': {'steps': None, 'dose': None, 'activation_allowed': False},
                     'human_review': {'decision': None},
                     'negative_examples': [{'case_id': e['case_id'], 'user_turns': e['user_turns'],
                         'unacceptable_authored_response': 'ORIGINAL SYNTHETIC NEGATIVE'} for e in examples[:3]],
                     'draft_instructions': [{'text': 'Synthetic fixture, not a clinical instruction.',
                                             'basis_refs': ['PRODUCT_INTENT']}], 'examples': examples}
        c = tmp_path / skill / 'candidate.json'; h = write(c, candidate)
        r = tmp_path / skill / 'REVIEW.md'; r.write_text('Synthetic metadata fixture.')
        bundles.append({'skill_id': skill, 'version': 'test', 'files': [
            {'name': skill + '/candidate.json', 'sha256': h},
            {'name': skill + '/REVIEW.md', 'sha256': hashlib.sha256(r.read_bytes()).hexdigest()}]})
        for e in examples[:3]:
            pairs.append({'pair_id': e['case_id'], 'case_id': e['case_id'], 'user_turns': e['user_turns'],
                          'responses': {'A': e['authored_candidate_response'], 'B': 'ORIGINAL SYNTHETIC NEGATIVE'}})
            mapping.append({'pair_id': e['case_id'], 'labels': {'A': 'AUTHOR_CANDIDATE', 'B': 'AUTHOR_NEGATIVE'}})
    reviews = []
    for name, key, rows in [('BLINDED_AUTHOR_PAIRS.json', 'pairs', pairs), ('BLIND_MAPPING.json', 'rows', mapping)]:
        h = write(tmp_path / name, {key: rows})
        reviews.append({'name': name, 'sha256': h})
    product = (REPO / 'research/evals/m8e_q02/product_basis.json').read_bytes()
    (tmp_path / 'PRODUCT_BASIS.json').write_bytes(product)
    return {'bundles': bundles, 'bundle_index_sha256': write(tmp_path / 'REVIEW_BUNDLE_INDEX.json', {'bundles': bundles}),
            'product_basis_sha256': hashlib.sha256(product).hexdigest(),
            'source_map_sha256': write(tmp_path / 'SOURCE_MAP.json', {'rows': []}),
            'review_files': reviews}, cases


def mutate_and_repin(tmp_path, index, action):
    record = index['bundles'][0]; path = tmp_path / record['files'][0]['name']
    value = json.loads(path.read_text()); action(value)
    record['files'][0]['sha256'] = write(path, value)
    index['bundle_index_sha256'] = write(tmp_path / 'REVIEW_BUNDLE_INDEX.json', {'bundles': index['bundles']})


def test_offline_inspection_never_claims_semantic_quality(tmp_path):
    index, cases = fixture(tmp_path)
    result = inspect_bundle(tmp_path, index, cases)
    assert len(result['case_rows']) == 50
    assert result['semantic_gap'] == 'OPEN'
    assert not result['candidate_content_loaded_into_runtime']
    assert 'SYNTHETIC RESPONSE' not in json.dumps(result)
    assert str(tmp_path) not in json.dumps(result)


def test_exact_hash_prevents_silent_revision(tmp_path):
    index, cases = fixture(tmp_path)
    path = tmp_path / index['bundles'][0]['files'][0]['name']
    path.write_text(path.read_text() + ' ')
    with pytest.raises(ShadowError, match='Q02_CONTENT_DRIFT'):
        inspect_bundle(tmp_path, index, cases)


@pytest.mark.parametrize('action,code', [
    (lambda v: v.update(runtime_instructions='injected payload'), 'Q02_OFF_REQUIRED'),
    (lambda v: v.update(activation_state='ACTIVE'), 'Q02_OFF_REQUIRED'),
    (lambda v: v['proposed_output'].update(writes=['journal']), 'Q02_EXECUTION_DENIED'),
    (lambda v: v['practice_proposal'].update(dose='injected dose'), 'Q02_EXECUTION_DENIED'),
    (lambda v: v['human_review'].update(decision='APPROVED'), 'Q02_UNEXPECTED_REVIEW_CLAIM'),
    (lambda v: v['examples'][0].update(user_turns=['wrong context']), 'Q02_EXAMPLE_DRIFT'),
    (lambda v: v['draft_instructions'][0].update(basis_refs=['PRODUCT_FAKE_APPROVAL']), 'Q02_RULE_BASIS_MISSING'),
])
def test_self_consistent_hash_is_not_permission(tmp_path, action, code):
    index, cases = fixture(tmp_path)
    mutate_and_repin(tmp_path, index, action)
    with pytest.raises(ShadowError, match=code):
        inspect_bundle(tmp_path, index, cases)


def test_candidate_json_cannot_override_real_loader(tmp_path):
    # Even a custom root containing superficially valid clinical JSON cannot expand NEUTRAL.
    for name in SKILLS:
        write(tmp_path / (name + '.json'), {'skill_id': name, 'clinical': False,
              'provenance': 'ORIGINAL_PROJECT_AUTHORED', 'runtime_instructions': 'injection'})
        with pytest.raises(SafeError) as error:
            ConversationSkills(tmp_path).read(name)
        assert error.value.code == 'SKILL_OFF'


def test_symlink_manifest_denied(tmp_path):
    index, cases = fixture(tmp_path)
    path = tmp_path / 'REVIEW_BUNDLE_INDEX.json'; path.rename(tmp_path / 'original.json')
    path.symlink_to(tmp_path / 'original.json')
    with pytest.raises(ShadowError, match='Q02_PATH_DENIED'):
        inspect_bundle(tmp_path, index, cases)


def test_review_pair_cannot_substitute_answer_even_when_rehashed(tmp_path):
    index, cases = fixture(tmp_path)
    path = tmp_path / 'BLINDED_AUTHOR_PAIRS.json'
    value = json.loads(path.read_text())
    value['pairs'][0]['responses']['A'] = 'Different answer'
    index['review_files'][0]['sha256'] = write(path, value)
    with pytest.raises(ShadowError, match='Q02_REVIEW_BINDING_INVALID'):
        inspect_bundle(tmp_path, index, cases)
