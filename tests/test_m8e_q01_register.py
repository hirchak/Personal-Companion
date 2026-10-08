"""Observed verb-only register gap; quoted speech is not a user-address rewrite."""
import json
from pathlib import Path

import pytest

from apps.core.conversation_controller import verify_address_form
from apps.core.storage import SafeError
from scripts.audit_m8e_q01 import exercise
from test_m1_domain import isolated


def historical_text():
    root=Path(__file__).resolve().parents[1]
    history=json.loads((root/'reports/evidence/M7D/SOL_ULTRA_REVIEW.json').read_text())
    row=next(row for row in history['rows'] if row['scenario_id']=='RANGE' and row['turn']==1)
    return row['assistant_candidate']['assistant_text']


def test_observed_unquoted_singular_verb_no_longer_passes_formal_policy():
    text=historical_text()
    with pytest.raises(SafeError,match='ADDRESS_FORM_MISMATCH'):
        verify_address_form(text,{'address_form':'FORMAL_VY','context':[]})
    verify_address_form(text.replace('хочеш','хочете'),{'address_form':'FORMAL_VY','context':[]})


@pytest.mark.parametrize('text,context',[
    ('Ви навели репліку «Який фрагмент хочеш розібрати?».', [{'text':'Він написав: «Який фрагмент хочеш розібрати?».'}]),
    ('Приклад: «Хочеш позичити парасолю?»', []),
    ('Репліка: «Якщо хочеш, залишайся».', []),
    ('Ви можете обрати, який фрагмент хочете розібрати.', []),
])
def test_source_quotes_fiction_examples_and_formal_language_remain_allowed(text,context):
    verify_address_form(text,{'address_form':'FORMAL_VY','context':context})


def test_real_controller_rejects_observed_register_violation_without_downstream_write(isolated):
    result=exercise(isolated,'REGISTER_VERB','ORIGINAL SYNTHETIC · Хочу обговорити один фрагмент.',historical_text())
    assert result['state']=='FAILED' and result['error']=='ADDRESS_FORM_MISMATCH'
    assert not result['assistant_committed'] and result['no_downstream_writes']
    corrected=exercise(isolated,'REGISTER_FORMAL','ORIGINAL SYNTHETIC · Хочу обговорити один фрагмент.',historical_text().replace('хочеш','хочете'))
    assert corrected['state']=='COMPLETED' and corrected['assistant_committed'] and corrected['no_downstream_writes']
