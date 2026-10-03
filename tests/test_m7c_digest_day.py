"""N01/N02 exact data invariants; no model or private records."""
from datetime import datetime
from uuid import uuid4
import json,sqlite3
import pytest
from apps.core.storage import Store,SafeError,encode
from apps.core.logical_day import logical_day,day_window,scope_key,validate_timezone
from apps.core.reflection import Reflection
from apps.core.conversation import Conversations
from apps.core.reflection_contracts import ContextRequest,GoalCreate,GoalRef
from apps.core.conversation_contracts import NewConversation,SendMessage
from test_m1_domain import isolated

@pytest.fixture
def fixture(isolated):
 r=Reflection(Conversations(Store(isolated/'digest-day'),True));g=r.create(GoalCreate(operation_id=uuid4(),text='ORIGINAL SYNTHETIC garden',user_agreed=True));free=r.conversations.create(NewConversation(operation_id=uuid4()));free=r.conversations.send(free['conversation']['id'],SendMessage(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC garden note'))
 deep=r.conversations.create(NewConversation(operation_id=uuid4(),goal_id=g['id'],goal_revision=1));return r,g,free,deep

def build(fixture,**values):
 r,g,free,deep=fixture
 return r.build(ContextRequest(operation_id=uuid4(),goal=GoalRef(id=g['id'],revision=1),conversation_id=deep['conversation']['id'],prepare_synthetic_digests=True,**values))

def test_single_current_supersession_purges_text_and_invalidates_old_receipt(fixture):
 r,g,free,deep=fixture;first=build(fixture);second=build(fixture)
 with r.store.connect() as c:
  assert not c.execute('SELECT 1 FROM conversation_digests WHERE status="CURRENT" GROUP BY kind,scope_key HAVING count(*)>1').fetchone()
  stale=[json.loads(row[0]) for row in c.execute('SELECT payload FROM conversation_digests WHERE status="STALE"')];assert stale and all(d['text'] is None for d in stale)
  assert c.execute('SELECT count(*) FROM conversation_digests WHERE kind="GOAL" AND status="CURRENT"').fetchone()[0]==1
 with r.store.transaction() as c:
  with pytest.raises(SafeError,match='SOURCE_CHANGED'):r.replay_context(c,first['receipt'])
 assert second['receipt']['digest_versions']


def test_unique_index_blocks_multiple_current_even_bypassing_service(fixture):
 r,*_=fixture;build(fixture)
 with r.store.connect() as c:
  row=c.execute('SELECT * FROM conversation_digests WHERE kind="GOAL" AND status="CURRENT"').fetchone();d=json.loads(row['payload']);d['id']=str(uuid4());d['version']+=1
  with pytest.raises(sqlite3.IntegrityError):c.execute('INSERT INTO conversation_digests VALUES(?,?,?,?,?,?)',(d['id'],d['kind'],d['scope_key'],d['version'],encode(d),'CURRENT'))


def test_failed_commit_keeps_previous_current_authority(fixture):
 r,*_=fixture;build(fixture)
 with r.store.connect() as c:before=[dict(row) for row in c.execute('SELECT * FROM conversation_digests')]
 r.store.fail_commit=True
 with pytest.raises(sqlite3.OperationalError):build(fixture)
 r.store.fail_commit=False
 with r.store.connect() as c:assert [dict(row) for row in c.execute('SELECT * FROM conversation_digests')]==before


@pytest.mark.parametrize('utc,day',[('2026-02-05T12:00:00Z','2026-02-05'),('2026-10-03T22:30:00Z','2026-10-04'),('2026-03-29T00:30:00Z','2026-03-29'),('2026-03-29T01:30:00Z','2026-03-29'),('2026-10-25T00:30:00Z','2026-10-25'),('2026-10-25T01:30:00Z','2026-10-25')])
def test_warsaw_normal_midnight_dst_utc_preserved(utc,day):
 assert logical_day(utc,'Europe/Warsaw')==day
 start,end=day_window(day,'Europe/Warsaw');source=datetime.fromisoformat(utc.replace('Z','+00:00'));assert datetime.fromisoformat(start)<=source<=datetime.fromisoformat(end)


@pytest.mark.parametrize('day,hours',[('2026-02-05',24),('2026-03-29',23),('2026-10-25',25)])
def test_dst_day_window_actual_length(day,hours):
 start,end=day_window(day,'Europe/Warsaw');assert (datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()==pytest.approx(hours*3600,abs=.00001)


def test_timezone_change_preserves_historical_identity_and_builder_filter(fixture):
 r,*_=fixture;first=build(fixture,timezone='Europe/Warsaw');build(fixture,timezone='UTC')
 with r.store.connect() as c:
  daily=[json.loads(row[0]) for row in c.execute('SELECT payload FROM conversation_digests WHERE kind="DAILY" AND status="CURRENT"')]
  assert {d['timezone'] for d in daily}=={'Europe/Warsaw','UTC'}
  assert all(d['scope_key']==scope_key(d['logical_local_date'],d['timezone']) for d in daily)
  assert all(d['day_identity_version']=='IANA_LOCAL_V1' for d in daily)
 assert first['receipt']['timezone']=='Europe/Warsaw'
 with pytest.raises(ValueError):validate_timezone('../private')


def test_schema9_legacy_duplicate_current_migration_fixture_only(fixture):
 r,*_=fixture;build(fixture)
 with r.store.connect() as c:
  c.execute('DROP INDEX digest_one_current');row=c.execute('SELECT * FROM conversation_digests WHERE kind="GOAL" AND status="CURRENT"').fetchone();d=json.loads(row['payload']);d['id']=str(uuid4());d['version']+=1;c.execute('INSERT INTO conversation_digests VALUES(?,?,?,?,?,?)',(d['id'],d['kind'],d['scope_key'],d['version'],encode(d),'CURRENT'))
  c.execute('UPDATE conversation_digests SET payload=json_remove(payload,"$.day_identity_version","$.timezone","$.logical_local_date") WHERE kind="DAILY"')
  c.execute('UPDATE vault_meta SET schema_version=9')
 restored=Store(r.store.root)
 with restored.connect() as c:
  assert c.execute('SELECT count(*) FROM conversation_digests WHERE kind="GOAL" AND status="CURRENT"').fetchone()[0]==1
  assert c.execute('SELECT count(*) FROM conversation_digests WHERE kind="DAILY" AND status="CURRENT"').fetchone()[0]==0
  assert all(json.loads(row[0])['text'] is None for row in c.execute('SELECT payload FROM conversation_digests WHERE status="STALE"'))
