"""Explicit synthetic roots and transactional SQLite persistence; no home discovery."""
import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

SCHEMA = 1
MARKER = {'kind': 'SYNTHETIC_M1', 'format': 1}
REPO = Path(__file__).resolve().parents[2]

class SafeError(Exception):
    def __init__(self, code, status=422):
        self.code, self.status = code, status
        super().__init__(code)

def now():
    return datetime.now(timezone.utc).isoformat()

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(path):
    p = Path(path).absolute()
    if '..' in p.parts:
        raise SafeError('UNSAFE_PATH')
    for component in (p, *p.parents):
        if component.is_symlink():
            raise SafeError('SYMLINK_DENIED')
        if (component / '.git').exists():
            raise SafeError('GIT_ROOT_DENIED')
    if p == REPO or p.is_relative_to(REPO):
        raise SafeError('REPO_ROOT_DENIED')
    if p.exists() and p.is_dir():
        # Traverse only the supplied synthetic root, never its siblings/ancestors.
        for directory, dirs, files in os.walk(p, followlinks=False):
            if '.git' in dirs or '.git' in files:
                raise SafeError('GIT_ROOT_DENIED')
            for name in dirs + files:
                if (Path(directory) / name).is_symlink():
                    raise SafeError('SYMLINK_DENIED')
    return p

def empty_target(path):
    p = safe_path(path)
    if p.exists() and (not p.is_dir() or any(p.iterdir())):
        raise SafeError('TARGET_NOT_EMPTY')
    if not p.parent.is_dir():
        raise SafeError('PARENT_REQUIRED')
    return p

def private_files(root):
    for p in root.iterdir():
        os.chmod(p, 0o700 if p.is_dir() else 0o600)

TABLES = (
    'CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,revision INTEGER NOT NULL,payload TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS entry_revisions(entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(entry_id,revision))',
    'CREATE TABLE IF NOT EXISTS tombstones(entry_id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,revision INTEGER NOT NULL,deleted_at_utc TEXT NOT NULL,restore_epoch INTEGER NOT NULL)',
    'CREATE TABLE IF NOT EXISTS operation_receipts(operation_id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,entry_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT,revision INTEGER NOT NULL,result_code TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS search_index(entry_id TEXT PRIMARY KEY REFERENCES entries(id) ON DELETE CASCADE,raw_text TEXT NOT NULL)',
)

class Store:
    def __init__(self, root, fail_migration=False):
        self.root = safe_path(root)
        self.commit_error = None
        self.fail_commit = False  # controlled test injection, never an HTTP/config switch
        manifest = self.root / 'synthetic.json'
        if self.root.exists() and any(self.root.iterdir()):
            if not manifest.is_file() or json.loads(manifest.read_text()) != MARKER:
                raise SafeError('UNKNOWN_ROOT')
            allowed = {'synthetic.json', 'journal.sqlite3', 'journal.sqlite3-wal', 'journal.sqlite3-shm', 'preupgrade.sqlite3'}
            if any(p.name not in allowed for p in self.root.iterdir()):
                raise SafeError('UNKNOWN_ROOT_CONTENT')
            if not (self.root / 'journal.sqlite3').is_file():
                raise SafeError('MISSING_DATABASE')
            # Version refusal precedes permission changes or migration transactions.
            probe = sqlite3.connect(f'file:{self.root / "journal.sqlite3"}?mode=ro', uri=True)
            try:
                version = probe.execute('SELECT schema_version FROM vault_meta').fetchone()[0]
                if version > SCHEMA or version < 0:
                    raise SafeError('UNSUPPORTED_SCHEMA')
            finally:
                probe.close()
        else:
            empty_target(self.root)
            self.root.mkdir(mode=0o700, exist_ok=True)
            manifest.write_text(encode(MARKER))
        os.chmod(self.root, 0o700)
        self.db = self.root / 'journal.sqlite3'
        # Create mode before SQLite opens it, including under permissive caller umask.
        if not self.db.exists():
            fd = os.open(self.db, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        private_files(self.root)
        with self.connect() as c:
            exists = c.execute("SELECT 1 FROM sqlite_master WHERE name='vault_meta'").fetchone()
            if exists:
                version = c.execute('SELECT schema_version FROM vault_meta').fetchone()[0]
                if version > SCHEMA or version < 0:
                    raise SafeError('UNSUPPORTED_SCHEMA')
                if version == SCHEMA:
                    self.check(c)
                    return
                snap = sqlite3.connect(self.root / 'preupgrade.sqlite3')
                c.backup(snap); snap.close()
                os.chmod(self.root / 'preupgrade.sqlite3', 0o600)
            c.execute('BEGIN IMMEDIATE')
            try:
                if not exists:
                    c.execute('CREATE TABLE vault_meta(vault_id TEXT,owner_id TEXT,schema_version INTEGER,restore_epoch INTEGER,created_at_utc TEXT,reconciliation TEXT)')
                    c.execute('INSERT INTO vault_meta VALUES(?,?,?,0,?,?)', (str(uuid4()), str(uuid4()), SCHEMA, now(), 'NONE'))
                for sql in TABLES:
                    c.execute(sql)
                if fail_migration:
                    raise sqlite3.OperationalError('synthetic migration failure')
                c.execute('UPDATE vault_meta SET schema_version=?', (SCHEMA,))
                c.commit()
            except BaseException:
                c.rollback()
                raise
            self.check(c)
        private_files(self.root)

    @contextmanager
    def connect(self):
        # Revalidate all children on every operation to reject post-start path swaps.
        safe_path(self.root)
        c = sqlite3.connect(self.db, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA synchronous=FULL')
        private_files(self.root)
        try:
            yield c
        finally:
            c.close()

    @contextmanager
    def transaction(self):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            try:
                yield c
                if self.commit_error:
                    raise self.commit_error
                if self.fail_commit:
                    raise sqlite3.OperationalError('synthetic commit failure')
                c.commit()
            except BaseException:
                c.rollback()
                raise

    @staticmethod
    def check(c):
        if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or c.execute('PRAGMA foreign_key_check').fetchall():
            raise SafeError('DATABASE_INTEGRITY')
        if c.execute('SELECT count(*) FROM vault_meta').fetchone()[0] != 1:
            raise SafeError('INVALID_METADATA')
        tables = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'vault_meta', 'entries', 'entry_revisions', 'tombstones', 'operation_receipts', 'search_index'} <= tables:
            raise SafeError('INCOMPLETE_SCHEMA')
        # SQLite integrity alone cannot establish the typed domain schema.
        from .models import EntryInput, EntryOutput, EntryRevisionOutput, VaultMetadata
        from pydantic import ValidationError
        try:
            metadata = VaultMetadata.model_validate(dict(c.execute('SELECT * FROM vault_meta').fetchone()))
            owner = str(metadata.owner_id)
            for table in ('entries', 'tombstones', 'operation_receipts'):
                if c.execute(f'SELECT count(*) FROM {table} WHERE owner_id IS NULL OR owner_id!=?', (owner,)).fetchone()[0]:
                    raise SafeError('METADATA_INTEGRITY')
        except (ValueError, TypeError, ValidationError):
            raise SafeError('METADATA_INTEGRITY') from None
        try:
            for row in c.execute('SELECT * FROM entries'):
                payload = json.loads(row['payload'])
                EntryInput.model_validate(payload)
                EntryOutput.model_validate(dict(payload, id=row['id'], owner_id=row['owner_id'],
                    revision=row['revision'], created_at_utc=row['created'], updated_at_utc=row['updated'],
                    schema_version=1, privacy_class='PRIVATE_PERSONAL', provenance_type='USER_REPORTED'))
            for row in c.execute('SELECT entry_id,revision,payload FROM entry_revisions'):
                entry = json.loads(row['payload'])
                historical = EntryRevisionOutput.model_validate(entry)
                if str(historical.owner_id) != owner or str(historical.id) != row['entry_id'] or historical.revision != row['revision']:
                    raise SafeError('DOMAIN_INTEGRITY')
        except (ValueError, TypeError, ValidationError):
            raise SafeError('DOMAIN_INTEGRITY') from None

    def meta(self):
        with self.connect() as c:
            return dict(c.execute('SELECT * FROM vault_meta').fetchone())

    def backup(self, target):
        p = empty_target(target)
        if p.exists():
            raise SafeError('TARGET_MUST_BE_NEW')
        temp = p.with_name(p.name + '.partial-' + str(uuid4()))
        temp.mkdir(mode=0o700)
        try:
            with self.connect() as source:
                dest = sqlite3.connect(temp / 'snapshot.sqlite3')
                dest.row_factory = sqlite3.Row
                try:
                    source.backup(dest)
                    dest.execute('PRAGMA journal_mode=DELETE')
                    self.check(dest)
                    meta = dict(dest.execute('SELECT * FROM vault_meta').fetchone())
                finally:
                    dest.close()
            manifest = {'backup_format': 1, 'schema_version': meta['schema_version'], 'created_at_utc': now(),
                        'attachments': [], 'files': {'snapshot.sqlite3': digest((temp / 'snapshot.sqlite3').read_bytes())}}
            (temp / 'manifest.json').write_text(encode(manifest))
            private_files(temp)
            temp.rename(p)
        except BaseException:
            # Only the directory created by this operation is removed.
            import shutil
            shutil.rmtree(temp)
            raise
        return manifest

    @classmethod
    def restore(cls, backup, target):
        b, p = safe_path(backup), empty_target(target)
        if '.partial-' in b.name or not b.is_dir() or {x.name for x in b.iterdir()} != {'manifest.json', 'snapshot.sqlite3'}:
            raise SafeError('INVALID_BACKUP')
        try:
            m = json.loads((b / 'manifest.json').read_text())
            if m['backup_format'] != 1 or m['schema_version'] != SCHEMA or m['attachments'] != [] or set(m['files']) != {'snapshot.sqlite3'}:
                raise SafeError('UNSUPPORTED_BACKUP')
            if m['files']['snapshot.sqlite3'] != digest((b / 'snapshot.sqlite3').read_bytes()):
                raise SafeError('CHECKSUM_MISMATCH')
            with sqlite3.connect(f'file:{b / "snapshot.sqlite3"}?mode=ro&immutable=1', uri=True) as source:
                source.row_factory = sqlite3.Row
                cls.check(source)
                if source.execute('SELECT schema_version FROM vault_meta').fetchone()[0] != SCHEMA:
                    raise SafeError('UNSUPPORTED_SCHEMA')
        except (KeyError, ValueError, sqlite3.Error):
            raise SafeError('INVALID_BACKUP') from None
        temp = p.with_name(p.name + '.partial-' + str(uuid4()))
        temp.mkdir(mode=0o700)
        try:
            import shutil
            shutil.copyfile(b / 'snapshot.sqlite3', temp / 'journal.sqlite3')
            (temp / 'synthetic.json').write_text(encode(MARKER))
            with sqlite3.connect(temp / 'journal.sqlite3') as c:
                c.execute("UPDATE vault_meta SET restore_epoch=restore_epoch+1,reconciliation='RESTORED_REQUIRES_RECONCILIATION'")
            private_files(temp)
            if p.exists():
                p.rmdir()  # was verified empty; refuses if changed
            temp.rename(p)
        except BaseException:
            import shutil
            shutil.rmtree(temp)
            raise
        return cls(p)
