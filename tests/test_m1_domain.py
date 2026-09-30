"""SYNTHETIC only: real SQLite, concurrency, durability and maintenance gates."""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from apps.core.storage import Store, SafeError, MARKER, encode, digest, REPO
from apps.core.domain import Journal, validate_portable
from apps.core.models import EntryInput, Create, Patch, Delete, Selector

@pytest.fixture
def isolated():
    # Resolve the system temp alias BEFORE creating a fresh harness root.
    parent = Path(tempfile.gettempdir()).resolve()
    root = Path(tempfile.mkdtemp(prefix='m1-synthetic-test-', dir=parent))
    yield root
    shutil.rmtree(root)

@pytest.fixture
def journal(isolated):
    return Journal(Store(isolated / 'data'))

def create(journal, kind='inbox', text='SYNTHETIC · Точний текст 🦉\n ', **extra):
    req = Create(operation_id=uuid4(), entry_id=uuid4(), base_revision=0, payload={'type': kind, 'raw_text': text, **extra})
    return req, journal.write('create', req.entry_id, req)

@pytest.mark.parametrize('kind', ['inbox', 'daily', 'sleep', 'creative'])
def test_A01_crud_history_purge(journal, kind):
    req, receipt = create(journal, kind, tags=['Тег'])
    id = str(req.entry_id)
    original = journal.get(id)
    assert original['raw_text'] == req.payload.raw_text
    edit = Patch(operation_id=uuid4(), base_revision=1, changes={'raw_text': 'SYNTHETIC · Змінено', 'type': 'creative', 'creative_kind': 'idea'})
    assert journal.write('edit', id, edit)['revision'] == 2
    assert journal.history(id)['items'] == [original]
    assert len(journal.list(q='Змінено', type='creative', tag='Тег')['items']) == 1
    assert not journal.list(q="' OR 1=1 --")['items']
    delete = Delete(operation_id=uuid4(), base_revision=2)
    journal.write('delete', id, delete)
    with pytest.raises(SafeError, match='DELETED'):
        journal.get(id)
    with pytest.raises(SafeError, match='DELETED'):
        journal.history(id)
    journal.rebuild()
    with journal.store.connect() as c:
        for table in ['entries', 'entry_revisions', 'search_index']:
            assert c.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM operation_receipts WHERE action!='delete' AND fingerprint IS NOT NULL").fetchone()[0] == 0
        assert 'raw_text' not in dict(c.execute('SELECT * FROM tombstones').fetchone())
    assert not journal.list()['items']


def test_A01_type_change_explicit(journal):
    req, _ = create(journal, 'daily', mood_rating=0)
    edit = Patch(operation_id=uuid4(), base_revision=1, changes={'type': 'inbox'})
    with pytest.raises(SafeError, match='CONFIRMATION'):
        journal.write('edit', req.entry_id, edit)
    assert journal.get(str(req.entry_id))['revision'] == 1
    edit.confirm_type_change = True
    journal.write('edit', req.entry_id, edit)
    assert 'mood_rating' not in journal.get(str(req.entry_id))
    assert journal.history(str(req.entry_id))['items'][0]['mood_rating'] == 0


def test_A02_commit_failure_retry_and_restart(journal):
    req = Create(operation_id=uuid4(), entry_id=uuid4(), base_revision=0, payload={'raw_text': 'SYNTHETIC · Retry'})
    journal.store.fail_commit = True
    with pytest.raises(sqlite3.OperationalError):
        journal.write('create', req.entry_id, req)
    with journal.store.connect() as c:
        assert c.execute('SELECT count(*) FROM operation_receipts').fetchone()[0] == 0
        assert c.execute('SELECT count(*) FROM entries').fetchone()[0] == 0
    journal.store.fail_commit = False
    journal.write('create', req.entry_id, req)
    reopened = Journal(Store(journal.store.root))
    assert reopened.get(str(req.entry_id))['raw_text'] == req.payload.raw_text


def test_A02_process_crash_durability(isolated):
    root = isolated / 'crash'
    code = '''
from apps.core.storage import Store
from apps.core.domain import Journal
from apps.core.models import Create
from uuid import uuid4
import os, sys
s=Store(sys.argv[1]); j=Journal(s)
r=Create(operation_id=uuid4(),entry_id=uuid4(),base_revision=0,payload={'raw_text':'SYNTHETIC committed before crash'})
j.write('create',r.entry_id,r)
context=s.connect()
c=context.__enter__()
c.execute('BEGIN IMMEDIATE')
c.execute("UPDATE entries SET payload='uncommitted damage'")
os._exit(17)
'''
    result = subprocess.run([sys.executable, '-c', code, str(root)], cwd=REPO, capture_output=True)
    assert result.returncode == 17
    assert Journal(Store(root)).list()['items'][0]['raw_text'] == 'SYNTHETIC committed before crash'


def test_A03_receipt_reuse_conflict_tombstone(journal):
    req, first = create(journal)
    assert journal.write('create', req.entry_id, req) == first
    req.payload.raw_text = 'SYNTHETIC another payload'
    with pytest.raises(SafeError, match='OPERATION_REUSE'):
        journal.write('create', req.entry_id, req)
    patch = Patch(operation_id=uuid4(), base_revision=1, changes={'tags': ['новий']})
    journal.write('edit', req.entry_id, patch)
    with pytest.raises(SafeError, match='REVISION_CONFLICT'):
        journal.write('edit', req.entry_id, Patch(operation_id=uuid4(), base_revision=1, changes={'raw_text': 'SYNTHETIC stale'}))
    delete = Delete(operation_id=uuid4(), base_revision=2)
    receipt = journal.write('delete', req.entry_id, delete)
    assert journal.write('delete', req.entry_id, delete) == receipt
    with pytest.raises(SafeError, match='DELETED'):
        journal.write('edit', req.entry_id, patch)
    with pytest.raises(SafeError, match='DELETED'):
        journal.write('create', req.entry_id, req)
    with pytest.raises(SafeError, match='OPERATION_REUSE'):
        journal.write('create', uuid4(), req)


def test_A03_concurrent_writes(journal):
    req, _ = create(journal)
    def write(i):
        try:
            return journal.write('edit', req.entry_id, Patch(operation_id=uuid4(), base_revision=1, changes={'raw_text': 'SYNTHETIC race ' + str(i)}))['revision']
        except SafeError as e:
            return e.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, [1, 2]), key=str) == [2, 'REVISION_CONFLICT']
    assert len(journal.history(str(req.entry_id))['items']) == 1


def test_A03_concurrent_duplicate(journal):
    req = Create(operation_id=uuid4(), entry_id=uuid4(), base_revision=0, payload={'raw_text':'SYNTHETIC concurrent'})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: journal.write('create', req.entry_id, req), [1, 2]))
    assert results[0] == results[1]
    assert len(journal.list()['items']) == 1

@pytest.mark.parametrize('bad', [
    {'raw_text': '  '}, {'unknown': 'private'}, {'tags': ['A', 'A']}, {'tags': [' ']},
    {'timezone': 'Unknown/Invalid'}, {'type': 'inbox', 'mood_rating': None},
    {'type': 'daily', 'mood_rating': 11}, {'type': 'daily', 'mood_rating': 1.2},
    {'type': 'daily', 'mood_rating': True}, {'type': 'daily', 'energy_rating': float('nan')},
    {'type': 'creative', 'creative_kind': 'invalid'}, {'occurred_at_utc': '2026-09-30T12:00:00'},
    {'local_date': '2026-09-30'}, {'time_precision': 'instant'}, {'raw_text': 'x'*100001},
    {'tags': ['x'*65]}, {'type':'sleep', 'sleep_start_utc':'2026-09-30T12:00:00+02:00', 'wake_at_utc':'2026-09-30T10:00:00+02:00'},
])
def test_A04_invalid_schema(bad):
    with pytest.raises(ValidationError):
        EntryInput.model_validate({'raw_text':'SYNTHETIC українська 🦉', **bad})


def test_A04_time_unknown_zero_dst(journal):
    req, _ = create(journal, 'daily', mood_rating=0, energy_rating=None)
    e = journal.get(str(req.entry_id)); assert e['mood_rating'] == 0 and e['energy_rating'] is None and e['local_date'] is None
    for start, wake, seconds in [('2026-10-25T02:30:00+02:00', '2026-10-25T02:30:00+01:00', 3600),
                                 ('2026-03-29T01:30:00+01:00', '2026-03-29T03:30:00+02:00', 3600),
                                 ('2026-09-29T23:00:00+02:00', '2026-09-30T07:00:00+02:00', 28800)]:
        req, _ = create(journal, 'sleep', sleep_start_utc=start, wake_at_utc=wake, occurred_at_utc=wake, local_date=wake[:10], time_precision='instant')
        e = journal.get(str(req.entry_id)); assert e['reported_interval_seconds'] == seconds
        assert e['timezone'] == 'Europe/Warsaw' and e['local_date'] == wake[:10]
    req, _ = create(journal, local_date='2026-09-30', time_precision='date')
    assert journal.get(str(req.entry_id))['occurred_at_utc'] is None


def test_A05_live_wal_backup_restore(journal, isolated):
    with journal.store.connect() as live:
        req, _ = create(journal, 'creative', creative_kind='scene')
        assert (journal.store.root / 'journal.sqlite3-wal').stat().st_size > 0
        journal.store.backup(isolated / 'backup')
        restored = Store.restore(isolated / 'backup', isolated / 'restored')
        assert Journal(restored).get(str(req.entry_id)) == journal.get(str(req.entry_id))
        assert restored.meta()['restore_epoch'] == 1
        assert restored.meta()['reconciliation'] == 'RESTORED_REQUIRES_RECONCILIATION'
        assert {p.name for p in (isolated / 'backup').iterdir()} == {'manifest.json','snapshot.sqlite3'}

@pytest.mark.parametrize('fault', ['checksum', 'schema', 'attachment', 'missing', 'partial', 'integrity', 'nonempty'])
def test_A05_bad_backup_does_not_touch_live(journal, isolated, fault):
    req, _ = create(journal)
    b = isolated / ('backup.partial-x' if fault == 'partial' else 'backup')
    journal.store.backup(b)
    m = json.loads((b / 'manifest.json').read_text())
    target = isolated / 'restore'
    if fault == 'checksum': (b / 'snapshot.sqlite3').write_bytes(b'broken')
    if fault == 'schema': m['schema_version'] = 999
    if fault == 'attachment': m['attachments'] = ['unexpected']
    if fault == 'missing': (b / 'snapshot.sqlite3').unlink()
    if fault == 'integrity':
        (b / 'snapshot.sqlite3').write_bytes(b'broken')
        m['files']['snapshot.sqlite3'] = digest(b'broken')
    if fault == 'nonempty': target.mkdir(); (target / 'unrelated').write_text('SYNTHETIC')
    (b / 'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError): Store.restore(b, target)
    assert journal.get(str(req.entry_id))['raw_text'] == req.payload.raw_text
    if fault != 'nonempty': assert not target.exists()


def test_A06_root_paths_permissions(journal, isolated):
    for p in journal.store.root.iterdir():
        assert p.stat().st_mode & 0o777 == 0o600
    assert journal.store.root.stat().st_mode & 0o777 == 0o700
    with pytest.raises(SafeError): Store(REPO / 'generated' / 'test-data')
    unknown = isolated / 'unknown'; unknown.mkdir(); (unknown/'unrelated').write_text('SYNTHETIC')
    with pytest.raises(SafeError, match='UNKNOWN_ROOT'): Store(unknown)
    link = isolated / 'link'; link.symlink_to(journal.store.root)
    with pytest.raises(SafeError, match='SYMLINK'): Store(link)
    with pytest.raises(SafeError): Store(isolated / 'x' / '..' / 'escape')
    gitroot = isolated / 'worktree'; gitroot.mkdir(); (gitroot / '.git').write_text('SYNTHETIC git worktree marker')
    with pytest.raises(SafeError, match='GIT_ROOT'): Store(gitroot / 'data')
    db = journal.store.db; original = db.read_bytes(); db.unlink(); db.symlink_to(unknown / 'unrelated')
    with pytest.raises(SafeError, match='SYMLINK'): journal.get(str(uuid4()))
    db.unlink(); db.write_bytes(original); os.chmod(db, 0o600)


def test_A06_migration_rollback_and_newer(isolated):
    root = isolated / 'legacy'; root.mkdir(); (root/'synthetic.json').write_text(encode(MARKER))
    with sqlite3.connect(root / 'journal.sqlite3') as c:
        c.execute('CREATE TABLE vault_meta(vault_id TEXT,owner_id TEXT,schema_version INTEGER,restore_epoch INTEGER,created_at_utc TEXT,reconciliation TEXT)')
        c.execute('INSERT INTO vault_meta VALUES(?,?,0,0,?,?)',(str(uuid4()),str(uuid4()),'2026-09-30T00:00:00+00:00','NONE'))
    with pytest.raises(sqlite3.OperationalError): Store(root, fail_migration=True)
    with sqlite3.connect(root / 'journal.sqlite3') as c:
        assert c.execute('SELECT schema_version FROM vault_meta').fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM sqlite_master WHERE name='entries'").fetchone()[0] == 0
    assert (root/'preupgrade.sqlite3').is_file()
    Store(root); Store(root)
    with sqlite3.connect(root / 'journal.sqlite3') as c: c.execute('UPDATE vault_meta SET schema_version=999')
    with pytest.raises(SafeError, match='UNSUPPORTED_SCHEMA'): Store(root)
    with sqlite3.connect(root / 'journal.sqlite3') as c: assert c.execute('SELECT schema_version FROM vault_meta').fetchone()[0] == 999


def test_A08_export_bound_roundtrip_escaping(journal):
    req, _ = create(journal, text='SYNTHETIC · <script>alert(1)</script> **текст** 🦉\n ')
    other, _ = create(journal, text='SYNTHETIC not selected')
    journal.write('edit', req.entry_id, Patch(operation_id=uuid4(),base_revision=1,changes={'tags':['тег']}))
    p = journal.preview(Selector(ids=[req.entry_id], include_history=True), 'session')
    text = journal.export(p['plan_id'], 'json', 'session')
    result = validate_portable(text)
    assert result['entries'] == [journal.get(str(req.entry_id))]
    assert result['revisions'] == journal.history(str(req.entry_id))['items']
    md = journal.export(p['plan_id'], 'markdown', 'session')
    assert '<script>' not in md and '\\*\\*текст' in md
    with pytest.raises(SafeError): journal.export(p['plan_id'], 'json', 'foreign')
    journal.write('edit', req.entry_id, Patch(operation_id=uuid4(),base_revision=2,changes={'tags':[]}))
    with pytest.raises(SafeError, match='EXPORT_CHANGED'): journal.export(p['plan_id'], 'json', 'session')
    p = journal.preview(Selector(types=['inbox']), 'session')
    journal.write('delete', req.entry_id, Delete(operation_id=uuid4(),base_revision=3))
    with pytest.raises(SafeError, match='EXPORT_CHANGED'): journal.export(p['plan_id'], 'json', 'session')
    p = journal.preview(Selector(ids=[other.entry_id]), 'session'); journal.clock = lambda: 1e15
    with pytest.raises(SafeError, match='EXPIRED'): journal.export(p['plan_id'], 'json', 'session')
    with pytest.raises(ValidationError): Selector()


def test_literal_search_and_cursor(journal):
    for i in range(3): create(journal, text=f'SYNTHETIC %_ {i}')
    first = journal.list(q='%_', limit=2)
    second = journal.list(q='%_',limit=2,cursor=first['next_cursor'])
    assert len(first['items']) == 2 and len(second['items']) == 1
    assert not set(x['id'] for x in first['items']) & set(x['id'] for x in second['items'])
    with pytest.raises(SafeError): journal.list(q='different',cursor=first['next_cursor'])
    with pytest.raises(SafeError): journal.list(cursor='malformed')
    journal.rebuild(); assert len(journal.list(q='%_')['items']) == 3

@pytest.mark.parametrize('action',['edit','delete'])
def test_A02_failed_edit_delete_leave_original_and_history(journal,action):
    req,_=create(journal)
    original=journal.get(str(req.entry_id))
    journal.store.fail_commit=True
    operation=Patch(operation_id=uuid4(),base_revision=1,changes={'raw_text':'SYNTHETIC must rollback'}) if action=='edit' else Delete(operation_id=uuid4(),base_revision=1)
    with pytest.raises(sqlite3.OperationalError): journal.write(action,req.entry_id,operation)
    assert journal.get(str(req.entry_id))==original
    assert journal.history(str(req.entry_id))['items']==[]
    with journal.store.connect() as c:
        assert c.execute('SELECT count(*) FROM tombstones').fetchone()[0]==0
        assert c.execute('SELECT count(*) FROM operation_receipts').fetchone()[0]==1
        assert c.execute('SELECT raw_text FROM search_index').fetchone()[0]==original['raw_text']


def test_A05_logically_invalid_backup_rejected(journal,isolated):
    create(journal)
    backup=isolated/'logical-backup'; journal.store.backup(backup)
    with sqlite3.connect(backup/'snapshot.sqlite3') as c:
        c.execute("UPDATE entries SET payload=?", (encode({'type':'daily','raw_text':'SYNTHETIC invalid','mood_rating':999}),))
    m=json.loads((backup/'manifest.json').read_text())
    m['files']['snapshot.sqlite3']=digest((backup/'snapshot.sqlite3').read_bytes())
    (backup/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='DOMAIN_INTEGRITY'): Store.restore(backup,isolated/'logical-restore')
    assert not (isolated/'logical-restore').exists()
