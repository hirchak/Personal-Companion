from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from apps.core.live_evaluation_budget import LiveEvaluationBudget
from apps.core.storage import SafeError
from test_m1_domain import isolated


def test_goal_wide_limit_concurrency_failed_cancelled_and_restart(isolated):
 path=isolated/'ledger.sqlite3';budget=LiveEvaluationBudget(path)
 def attempt(i):
  id=str(uuid4())
  try:budget.reserve(id,'CODEX_SUBSCRIPTION','original-synthetic-fixture');budget.finish(id,'FAILED' if i%2 else 'CANCELLED');return True
  except SafeError as e:assert e.code=='LIVE_EVAL_LIMIT';return False
 with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(attempt,range(110)))
 assert sum(results)==100 and budget.summary()['total_requests']==100 and budget.summary()['remaining']==0
 restored=LiveEvaluationBudget(path)
 with pytest.raises(SafeError,match='LIVE_EVAL_LIMIT'):restored.reserve(str(uuid4()),'MINIMAX_TOKEN_PLAN','original-synthetic-fixture')
 assert not restored.summary()['raw_payload_logged']


def test_reusing_attempt_never_sends_again(isolated):
 b=LiveEvaluationBudget(isolated/'ledger.sqlite3');id=str(uuid4());b.reserve(id,'CODEX_SUBSCRIPTION','original-synthetic-fixture')
 with pytest.raises(SafeError,match='LIVE_ATTEMPT_REUSE'):b.reserve(id,'CODEX_SUBSCRIPTION','original-synthetic-fixture')
 assert b.summary()['total_requests']==1
