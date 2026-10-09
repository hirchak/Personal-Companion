"""Sanitized actual-controller characterization of release versus content labels.

No raw model/generated text in reports or logs. Inputs are original authored
fixtures, not clinical gold or live-model observations. No provider SDK calls.
"""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from apps.core.storage import Store, REPO, digest, encode
from apps.core.conversation_release import ReleasePolicy
from scripts.audit_m8e_q01 import COUNTEREXAMPLES, exercise
from scripts.audit_m8e_q02 import SPECIALIST_FAILURES


def observe(root, identifier, user, response, mode, expected):
    row = exercise(root, identifier + '_' + mode, user, response, mode=mode)
    with Store(root / row['id']).connect() as c:
        job = json.loads(c.execute('SELECT payload FROM conversation_inferences').fetchone()[0])
        decision = job.get('release_receipt') or job.get('content_decision_metadata')
        assistants = c.execute('SELECT COUNT(*) FROM conversation_messages WHERE json_extract(payload,"$.role")="ASSISTANT"').fetchone()[0]
        maps = c.execute('SELECT COUNT(*) FROM working_maps').fetchone()[0]
    return dict(row, input_sha256=digest(user.encode()), authored_response_sha256=digest(response.encode()),
                expected=expected, decision_verdict=decision['verdict'] if decision else 'NOT_EVALUATED',
                decision_reason=decision['reason'] if decision else 'NOT_EVALUATED',
                assistant_rows=assistants, map_rows=maps,
                original_fixture_not_clinical_gold=True)


def run(root):
    rows = []
    negatives = [(id,u,b) for id,u,b,_ in COUNTEREXAMPLES] + list(SPECIALIST_FAILURES)
    for id,user,bad in negatives:
        for mode in ('FREE','DEEP'):
            rows.append(observe(root,id,user,bad,mode,'NOT_RELEASED'))
    positives = json.loads((REPO / 'research/evals/m8e_q03/positive_pairs.json').read_text())['cases']
    for case in positives:
        for mode in ('FREE','DEEP'):
            rows.append(observe(root,case['id'],case['input'],case['authored_response'],mode,'RELEASED_BOUNDED'))
    return {'schema_version':1, 'origin':'ORIGINAL_SCRIPTED_FIXTURE_NOT_LIVE_MODEL',
            'policy_hash':ReleasePolicy().identity(), 'rows':rows,
            'known_negative_count':len(negatives)*2,
            'known_negative_excluded':sum(r['expected']=='NOT_RELEASED' and not r['assistant_committed'] for r in rows),
            'positive_count':len(positives)*2,
            'positive_released':sum(r['expected']=='RELEASED_BOUNDED' and r['assistant_committed'] for r in rows),
            'qualification':'QUALIFIED_CONTENT_REVIEW_PENDING', 'universal_semantic_gap':'OPEN',
            'live_calls':0, 'raw_response_text_exported':False, 'clinical_active':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root=Path(tempfile.mkdtemp(prefix='m8e-q03-original-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
    try:
        result=run(root)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('known_negative_count','known_negative_excluded','positive_count','positive_released','live_calls')}))
    finally:
        shutil.rmtree(root)


if __name__=='__main__':main()
