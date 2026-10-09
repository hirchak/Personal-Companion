"""Hash-bound local candidate inspection; never loads a clinical skill into runtime.

Outputs hashes/statuses only. Mechanical consistency is not semantic safety or
clinical approval. No provider, database, app service, XML, exec or network access.
"""
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = {'cbt_reflection', 'worry_rumination', 'sleep_review', 'nightmare_review', 'grounding'}
PRODUCT_BASIS = {'PRODUCT_INTENT', 'PRODUCT_FORMAL_VY', 'PRODUCT_QUESTION_POLICY',
                 'PRODUCT_SOURCE_BINDING', 'PRODUCT_NO_AUTHORITY', 'PRODUCT_CLINICAL_BOUNDARY',
                 'PRODUCT_CRISIS_BOUNDARY', 'PRODUCT_CLOSURE'}
MAX_BYTES = 512 * 1024


class ShadowError(ValueError):
    pass


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def checked(root, name, expected):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ShadowError('Q02_PATH_DENIED')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ShadowError('Q02_PATH_DENIED')
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ShadowError('Q02_FILE_INVALID')
    blob = path.read_bytes()
    if sha(blob) != expected:
        raise ShadowError('Q02_CONTENT_DRIFT')
    return blob


def parsed(blob):
    try:
        return json.loads(blob)
    except (UnicodeError, ValueError):
        raise ShadowError('Q02_JSON_INVALID') from None


def inspect_bundle(root, index, cases):
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or root.resolve().is_relative_to(REPO):
        raise ShadowError('Q02_EXTERNAL_DIRECTORY_REQUIRED')
    local = parsed(checked(root, 'REVIEW_BUNDLE_INDEX.json', index['bundle_index_sha256']))
    if local['bundles'] != index['bundles'] or {x['skill_id'] for x in local['bundles']} != SKILLS:
        raise ShadowError('Q02_INDEX_DRIFT')
    source_map = parsed(checked(root, 'SOURCE_MAP.json', index['source_map_sha256']))
    source_ids = {r['id'] for r in source_map['rows']}
    product_bytes = checked(root, 'PRODUCT_BASIS.json', index['product_basis_sha256'])
    if product_bytes != (REPO / 'research/evals/m8e_q02/product_basis.json').read_bytes():
        raise ShadowError('Q02_PRODUCT_BASIS_DRIFT')
    for record in parsed(product_bytes)['rows']:
        if record['id'] not in PRODUCT_BASIS or sha((REPO / record['file']).read_bytes()) != record['sha256']:
            raise ShadowError('Q02_PRODUCT_BASIS_DRIFT')
    results = []
    authored = {}
    negatives = {}
    for record in index['bundles']:
        skill = record['skill_id']
        expected_names = {skill + '/candidate.json', skill + '/REVIEW.md'}
        if len(record['files']) != 2 or {x['name'] for x in record['files']} != expected_names:
            raise ShadowError('Q02_PATH_DENIED')
        contents = {x['name']: checked(root, x['name'], x['sha256']) for x in record['files']}
        candidate = parsed(contents[skill + '/candidate.json'])
        if (candidate['skill_id'] != skill or candidate['version'] != record['version']
                or candidate['activation_state'] != 'OFF' or candidate['status'] != 'CANDIDATE_OFF'
                or candidate['runtime_instructions'] is not None or candidate['draft_only'] is not True):
            raise ShadowError('Q02_OFF_REQUIRED')
        if (candidate['proposed_output']['writes'] or candidate['proposed_output']['tools']
                or candidate['proposed_output']['practice_reference'] is not None
                or candidate['practice_proposal']['steps'] is not None
                or candidate['practice_proposal']['dose'] is not None
                or candidate['practice_proposal']['activation_allowed'] is not False):
            raise ShadowError('Q02_EXECUTION_DENIED')
        if candidate['human_review']['decision'] is not None:
            raise ShadowError('Q02_UNEXPECTED_REVIEW_CLAIM')
        for rule in candidate['draft_instructions']:
            if not rule['text'] or not rule['basis_refs'] or any(
                    ref not in source_ids and ref not in PRODUCT_BASIS for ref in rule['basis_refs']):
                raise ShadowError('Q02_RULE_BASIS_MISSING')
        expected_cases = {c['id']: c for c in cases if c['skill'] == skill}
        examples = candidate['examples']
        if len(examples) != len(expected_cases) or {e['case_id'] for e in examples} != set(expected_cases):
            raise ShadowError('Q02_CASE_COVERAGE_DRIFT')
        for example in examples:
            if (example['user_turns'] != expected_cases[example['case_id']]['user_turns']
                    or example['provenance'] != 'ORIGINAL_AUTHOR_EXAMPLE_NOT_MODEL_OUTPUT'
                    or not example['authored_candidate_response'] or not example['author_explanation']):
                raise ShadowError('Q02_EXAMPLE_DRIFT')
            authored[example['case_id']] = example
            results.append({'case_id': example['case_id'], 'skill_id': skill,
                            'candidate_sha256': sha(contents[skill + '/candidate.json']),
                            'authored_response_sha256': sha(example['authored_candidate_response'].encode()),
                            'exact_case_binding': True, 'origin': example['provenance'],
                            'semantic_quality': 'NOT_MECHANICALLY_DETERMINED',
                            'independent_review': 'PENDING', 'live_behavior': 'NOT_EVALUATED'})
        for example in candidate['negative_examples']:
            if example['case_id'] not in expected_cases or example['user_turns'] != expected_cases[example['case_id']]['user_turns']:
                raise ShadowError('Q02_EXAMPLE_DRIFT')
            negatives[example['case_id']] = example['unacceptable_authored_response']
    allowed_reviews = {'BLINDED_AUTHOR_PAIRS.json', 'BLIND_MAPPING.json'}
    if len(index['review_files']) != 2 or {x['name'] for x in index['review_files']} != allowed_reviews:
        raise ShadowError('Q02_REVIEW_INDEX_INVALID')
    review = {x['name']: parsed(checked(root, x['name'], x['sha256'])) for x in index['review_files']}
    pairs = review['BLINDED_AUTHOR_PAIRS.json']['pairs']
    mapping = review['BLIND_MAPPING.json']['rows']
    if len(pairs) != 15 or len(mapping) != 15 or {x['pair_id'] for x in pairs} != {x['pair_id'] for x in mapping}:
        raise ShadowError('Q02_REVIEW_COVERAGE_INVALID')
    if len({x['pair_id'] for x in pairs}) != 15:
        raise ShadowError('Q02_REVIEW_COVERAGE_INVALID')
    labels = {x['pair_id']: x['labels'] for x in mapping}
    for pair in pairs:
        case_id = pair['case_id']
        if case_id not in authored or case_id not in negatives or pair['user_turns'] != authored[case_id]['user_turns']:
            raise ShadowError('Q02_REVIEW_BINDING_INVALID')
        expected = {'AUTHOR_CANDIDATE': authored[case_id]['authored_candidate_response'],
                    'AUTHOR_NEGATIVE': negatives[case_id]}
        choices = labels[pair['pair_id']]
        if set(choices) != {'A', 'B'} or set(choices.values()) != set(expected) or set(pair['responses']) != {'A', 'B'}:
            raise ShadowError('Q02_REVIEW_BINDING_INVALID')
        if any(pair['responses'][label] != expected[kind] for label, kind in choices.items()):
            raise ShadowError('Q02_REVIEW_BINDING_INVALID')
    return {'schema_version': 1, 'status': 'SHADOW_MECHANICAL_PASS', 'case_rows': results,
            'bundle_count': 5, 'authored_pairs': 15, 'exact_pair_bindings': True, 'clinical_activation': False,
            'candidate_content_loaded_into_runtime': False, 'provider_calls': 0,
            'semantic_gap': 'OPEN', 'qualified_review': 'PENDING',
            'scope': 'Exact local file/contract/case consistency only; not response generation or clinical content acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        folder = REPO / 'research/evals/m8e_q02'
        result = inspect_bundle(args.bundle_dir, parsed((folder / 'candidate_index.json').read_bytes()),
                                parsed((folder / 'cases.json').read_bytes())['cases'])
    except ShadowError as error:
        print(json.dumps({'status': 'FAIL', 'code': str(error)}))
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'status': 'FAIL', 'code': 'Q02_BUNDLE_INVALID'}))
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'cases': len(result['case_rows']),
                      'content_review': 'PENDING', 'provider_calls': 0}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
