"""Explicit synthetic roots and transactional SQLite persistence; no home discovery."""
import hashlib
import json
import os
import sqlite3
import threading
import re
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from .root_types import RootKind

SCHEMA = 11
_ROOT_LOCKS = {}
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

SYNC_TABLES = (
    'CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,label TEXT NOT NULL,credential_hash TEXT NOT NULL,epoch TEXT NOT NULL,created_at_utc TEXT NOT NULL,revoked_at_utc TEXT)',
    'CREATE TABLE IF NOT EXISTS sync_meta(id INTEGER PRIMARY KEY CHECK(id=1),generation TEXT NOT NULL,change_seq INTEGER NOT NULL)',
    'CREATE TABLE IF NOT EXISTS sync_receipts(operation_id TEXT PRIMARY KEY,device_id TEXT NOT NULL REFERENCES devices(id),entry_id TEXT NOT NULL,action TEXT NOT NULL,fingerprint TEXT,state TEXT NOT NULL,revision INTEGER)',
    'CREATE TABLE IF NOT EXISTS sync_checkpoints(device_id TEXT PRIMARY KEY REFERENCES devices(id),epoch TEXT NOT NULL,change_seq INTEGER NOT NULL)',
)

AI_TABLES = (
    'CREATE TABLE IF NOT EXISTS ai_consents(id TEXT PRIMARY KEY,session TEXT NOT NULL,package TEXT NOT NULL,context_hash TEXT NOT NULL,expires_at REAL NOT NULL,approved INTEGER NOT NULL,revoked INTEGER NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ai_jobs(id TEXT PRIMARY KEY,operation_id TEXT UNIQUE NOT NULL,consent_id TEXT UNIQUE NOT NULL REFERENCES ai_consents(id),task TEXT NOT NULL,provider TEXT NOT NULL,model TEXT,protocol TEXT NOT NULL,context_hash TEXT NOT NULL,source_refs TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,error TEXT,usage TEXT)',
    'CREATE UNIQUE INDEX IF NOT EXISTS ai_one_foreground ON ai_jobs((1)) WHERE state IN ("QUEUED","RUNNING")',
    'CREATE TABLE IF NOT EXISTS suggestions(id TEXT PRIMARY KEY,job_id TEXT UNIQUE NOT NULL REFERENCES ai_jobs(id),status TEXT NOT NULL,output TEXT NOT NULL,fingerprint TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,accepted TEXT,before_structure TEXT)',
    'CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY,scope TEXT NOT NULL,content TEXT NOT NULL,status TEXT NOT NULL,provenance TEXT NOT NULL,sources TEXT NOT NULL,revision INTEGER NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,expires_at REAL,job_id TEXT REFERENCES ai_jobs(id),suggestion_id TEXT REFERENCES suggestions(id))',
)

def ai_triggers(c):
    for table, refs in (('entries','entry_refs'), ('memories','memory_refs')):
        for action in ('UPDATE','DELETE'):
            c.execute(f"""CREATE TRIGGER IF NOT EXISTS ai_invalidate_{table}_{action.lower()} AFTER {action} ON {table}
            BEGIN
              UPDATE ai_consents SET revoked=1 WHERE EXISTS
                (SELECT 1 FROM json_each(json_extract(package,'$.{refs}')) WHERE json_extract(value,'$.id')=OLD.id);
              UPDATE ai_jobs SET state='CANCELLED',error='SOURCE_CHANGED',updated=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE state IN ('QUEUED','RUNNING') AND consent_id IN (SELECT id FROM ai_consents WHERE revoked=1);
              UPDATE suggestions SET status='STALE' WHERE status IN ('PENDING','ACCEPTED') AND job_id IN
                (SELECT id FROM ai_jobs WHERE consent_id IN (SELECT id FROM ai_consents WHERE revoked=1));
            END""")
    for action in ('UPDATE','DELETE'):
        c.execute(f"""CREATE TRIGGER IF NOT EXISTS ai_memory_source_{action.lower()} AFTER {action} ON entries
        BEGIN
          UPDATE memories SET status='REVIEW_REQUIRED',revision=revision+1,updated=strftime('%Y-%m-%dT%H:%M:%fZ','now')
          WHERE status IN ('MODEL_SUGGESTED','USER_CONFIRMED') AND EXISTS
            (SELECT 1 FROM json_each(sources) WHERE json_extract(value,'$.id')=OLD.id);
        END""")

class Store:
    def __init__(self, root, fail_migration=False, *, root_kind=RootKind.SYNTHETIC_TEST, private_creation=None):
        self.root = safe_path(root)
        self.root_kind = RootKind(root_kind)
        self._creating_private = private_creation is not None
        self.attachment_lock = _ROOT_LOCKS.setdefault(str(self.root), threading.RLock())
        self.commit_error = None
        self.fail_commit = False  # controlled test injection, never an HTTP/config switch
        private = self.root_kind == RootKind.PRIVATE_LOCAL
        manifest = self.root / ('private-local.json' if private else 'synthetic.json')
        if self.root.exists() and any(self.root.iterdir()):
            if private:
                from .local_private import validate_root
                validate_root(self.root, security=True)
            elif (self.root/'private-local.json').exists():
                raise SafeError('ROOT_KIND_MISMATCH')
            elif not manifest.is_file() or json.loads(manifest.read_text()) != MARKER:
                raise SafeError('UNKNOWN_ROOT')
            allowed = {manifest.name, 'journal.sqlite3', 'journal.sqlite3-wal', 'journal.sqlite3-shm', 'preupgrade.sqlite3', 'audio', 'audio-staging'}
            if any(p.name not in allowed for p in self.root.iterdir()):
                raise SafeError('UNKNOWN_ROOT_CONTENT')
            for folder, pattern in [('audio', r'[0-9a-f-]{36}\.wav(?:\.writing)?'), ('audio-staging', r'[0-9a-f-]{36}')]:
                path=self.root/folder
                if path.exists():
                    if not path.is_dir() or any(not re.fullmatch(pattern,x.name) for x in path.iterdir()):raise SafeError('UNKNOWN_ROOT_CONTENT')
                    if folder=='audio-staging':
                        for x in path.iterdir():
                            if not x.is_dir() or any(not re.fullmatch(r'[0-9]{3}\.part(?:\.writing)?',y.name) or not y.is_file() for y in x.iterdir()):raise SafeError('UNKNOWN_ROOT_CONTENT')
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
            if private:
                from .local_private import RootReceipt, owner_only, require_volume
                if private_creation is None: raise SafeError('EXPLICIT_PRIVATE_INITIALIZATION_REQUIRED')
                private_creation = RootReceipt.model_validate(private_creation).model_dump()
                owner_only(self.root if self.root.exists() else self.root.parent)
                require_volume(self.root)
                owner_only(private_creation['backup_directory']); require_volume(private_creation['backup_directory'])
            empty_target(self.root)
            self.root.mkdir(mode=0o700, exist_ok=True)
            fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as handle: handle.write(encode(private_creation if private else MARKER))
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
                    if private:
                        c.execute('CREATE TABLE private_root_identity(payload TEXT NOT NULL)')
                        c.execute('INSERT INTO private_root_identity VALUES(?)', (encode(private_creation),))
                for sql in TABLES:
                    c.execute(sql)
                for sql in SYNC_TABLES:
                    c.execute(sql)
                for sql in AI_TABLES:
                    c.execute(sql)
                from .voice import VOICE_TABLES
                for sql in VOICE_TABLES:
                    c.execute(sql)
                from .health import HEALTH_TABLES
                for sql in HEALTH_TABLES:
                    c.execute(sql)
                from .reflection import REFLECTION_TABLES,reflection_triggers
                from .conversation import CONVERSATION_TABLES
                for sql in CONVERSATION_TABLES:
                    c.execute(sql)
                for sql in REFLECTION_TABLES:
                    c.execute(sql)
                reflection_triggers(c)
                from .conversation_controller import RUNTIME_TABLES
                for sql in RUNTIME_TABLES:c.execute(sql)
                from .deep_session import DEEP_TABLES
                for sql in DEEP_TABLES:c.execute(sql)
                from .practice import PRACTICE_TABLES
                for sql in PRACTICE_TABLES:
                    c.execute(sql)
                from .feedback import M5_TABLES
                for sql in M5_TABLES:
                    c.execute(sql)
                columns = {r[1] for r in c.execute('PRAGMA table_info(devices)')}
                if 'pair_state' not in columns:
                    c.execute("ALTER TABLE devices ADD COLUMN pair_state TEXT NOT NULL DEFAULT 'ACTIVE'")
                    c.execute('ALTER TABLE devices ADD COLUMN pending_until REAL')
                for trigger in ('ai_invalidate_entries_update','ai_invalidate_entries_delete','ai_invalidate_memories_update','ai_invalidate_memories_delete'):
                    c.execute(f'DROP TRIGGER IF EXISTS {trigger}')
                ai_triggers(c)
                c.execute('INSERT OR IGNORE INTO sync_meta VALUES(1,?,0)', (str(uuid4()),))
                for table in ('entries','tombstones'):
                    for action in ('INSERT','UPDATE','DELETE'):
                        c.execute(f'CREATE TRIGGER IF NOT EXISTS seq_{table}_{action.lower()} AFTER {action} ON {table} BEGIN UPDATE sync_meta SET change_seq=change_seq+1 WHERE id=1; END')
                if fail_migration:
                    raise sqlite3.OperationalError('synthetic migration failure')
                c.execute('UPDATE vault_meta SET schema_version=?', (SCHEMA,))
                c.commit()
            except BaseException:
                c.rollback()
                raise
            self.check(c)
        private_files(self.root)
        self._creating_private = False

    @contextmanager
    def connect(self):
        # Revalidate all children on every operation to reject post-start path swaps.
        safe_path(self.root)
        if getattr(self, 'root_kind', RootKind.SYNTHETIC_TEST) == RootKind.PRIVATE_LOCAL:
            from .local_private import validate_root
            if not getattr(self, '_creating_private', False): validate_root(self.root)
        elif (self.root/'private-local.json').exists():
            raise SafeError('ROOT_KIND_MISMATCH')
        c = sqlite3.connect(self.db, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        if getattr(self, 'root_kind', RootKind.SYNTHETIC_TEST) == RootKind.SYNTHETIC_TEST and c.execute("SELECT 1 FROM sqlite_master WHERE name='private_root_identity'").fetchone():
            c.close()
            raise SafeError('ROOT_KIND_MISMATCH')
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
        if not {'vault_meta', 'entries', 'entry_revisions', 'tombstones', 'operation_receipts', 'search_index', 'devices', 'sync_meta', 'sync_receipts', 'sync_checkpoints'} <= tables:
            raise SafeError('INCOMPLETE_SCHEMA')
        # SQLite integrity alone cannot establish the typed domain schema.
        from .models import EntryInput, EntryOutput, EntryRevisionOutput, VaultMetadata
        from pydantic import ValidationError
        try:
            metadata = VaultMetadata.model_validate(dict(c.execute('SELECT * FROM vault_meta').fetchone()))
            if metadata.schema_version >= 3 and not {'ai_consents','ai_jobs','suggestions','memories'} <= tables:
                raise SafeError('INCOMPLETE_SCHEMA')
            if metadata.schema_version >= 4 and not {'audio','audio_chunks','transcripts'} <= tables:
                raise SafeError('INCOMPLETE_SCHEMA')
            if metadata.schema_version >= 5:
                if not {'feedback_drafts','personal_space'} <= tables: raise SafeError('INCOMPLETE_SCHEMA')
                from .feedback import check_m5
                check_m5(c)
            if metadata.schema_version >= 6:
                if not {'health_records','health_revisions','health_state'} <= tables:raise SafeError('INCOMPLETE_SCHEMA')
                from .health import check_health
                check_health(c)
            if metadata.schema_version>=11:
                if not {'deep_sessions','working_maps','deep_actions','deep_context_previews'} <= tables:raise SafeError('INCOMPLETE_SCHEMA')
                from .deep_session import check_deep
                check_deep(c)
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
                    schema_version=2, privacy_class='PRIVATE_PERSONAL', provenance_type='USER_REPORTED'))
            for row in c.execute('SELECT entry_id,revision,payload FROM entry_revisions'):
                entry = json.loads(row['payload'])
                historical = EntryRevisionOutput.model_validate(entry)
                if str(historical.owner_id) != owner or str(historical.id) != row['entry_id'] or historical.revision != row['revision']:
                    raise SafeError('DOMAIN_INTEGRITY')
        except (ValueError, TypeError, ValidationError):
            raise SafeError('DOMAIN_INTEGRITY') from None

    @staticmethod
    def check_audio(c):
        from .voice_contracts import AudioBegin
        from pydantic import ValidationError
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'audio' not in tables: return []
        required = []
        try:
            for r in c.execute('SELECT * FROM audio'):
                from uuid import UUID
                if str(UUID(r['id'])) != r['id'] or not re.fullmatch(r'[0-9a-f]{64}',r['content_hash']): raise ValueError()
                if r['state'] not in {'UPLOADING','MAC_AUDIO_CONFIRMED','CANCELLED','FAILED','DELETE_PENDING','DELETED'}: raise ValueError()
                if r['state'] != 'DELETED':
                    m=AudioBegin.model_validate(json.loads(r['metadata']))
                    if str(m.audio_id)!=r['id'] or m.content_hash!=r['content_hash'] or m.byte_size!=r['byte_size']:raise ValueError()
                if r['state']=='MAC_AUDIO_CONFIRMED':
                    required.append({'audio_id':r['id'],'file':r['id']+'.wav','content_hash':r['content_hash'],'byte_size':r['byte_size']})
            for t in c.execute('SELECT * FROM transcripts'):
                audio=c.execute('SELECT * FROM audio WHERE id=?',(t['audio_id'],)).fetchone()
                if not audio or audio['content_hash']!=t['audio_hash']:raise ValueError()
                if t['state'] not in {'TRANSCRIPTION_QUEUED','TRANSCRIBING','TRANSCRIPT_READY','REVIEW_REQUIRED','CONFIRMED','FAILED','CANCELLED'}:raise ValueError()
                # A confirmed note can subsequently be edited/deleted normally; historical provenance
                # must refer to its matching current/revision/tombstone, never an unrelated entry.
                if t['state']=='CONFIRMED':
                    entry=c.execute('SELECT revision FROM entries WHERE id=?',(t['entry_id'],)).fetchone()
                    dead=c.execute('SELECT revision FROM tombstones WHERE entry_id=?',(t['entry_id'],)).fetchone()
                    if not (entry or dead) or (entry or dead)[0]<t['entry_revision']:raise ValueError()
            return sorted(required,key=lambda x:x['audio_id'])
        except (ValueError,TypeError,ValidationError):raise SafeError('AUDIO_REFERENCE_INTEGRITY') from None

    def meta(self):
        with self.connect() as c:
            return dict(c.execute('SELECT * FROM vault_meta').fetchone())

    def backup(self, target, *, release_context=None):
        with self.attachment_lock:
            return self._backup(target, release_context=release_context)

    def _backup(self, target, *, release_context=None):
        private = getattr(self, 'root_kind', RootKind.SYNTHETIC_TEST) == RootKind.PRIVATE_LOCAL
        root_identity = None
        if private:
            from .local_private import backup_gate
            if release_context is None: raise SafeError('PRIVATE_RELEASE_BACKUP_REQUIRED')
            root_identity = backup_gate(self.root, target)
        p = empty_target(target)
        created=now();release_info=None
        if release_context is not None:
            from .release_metadata import validate_manifest
            if set(release_context)!={'producer','source'}:raise SafeError('BACKUP_RELEASE_PROVENANCE')
            validate_manifest(release_context['producer']);validate_manifest(release_context['source'])
        if p.exists(): raise SafeError('TARGET_MUST_BE_NEW')
        temp = p.with_name(p.name + '.partial-' + str(uuid4()))
        temp.mkdir(mode=0o700)
        try:
            with self.connect() as source:
                dest = sqlite3.connect(temp / 'snapshot.sqlite3');dest.row_factory = sqlite3.Row
                try:
                    source.backup(dest)
                    version = dest.execute('SELECT schema_version FROM vault_meta').fetchone()[0]
                    tables = {r[0] for r in dest.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if 'devices' in tables:
                        dest.execute("UPDATE devices SET credential_hash='',revoked_at_utc=COALESCE(revoked_at_utc,?)", (now(),))
                    if 'ai_consents' in tables: dest.execute('UPDATE ai_consents SET revoked=1')
                    if 'feedback_drafts' in tables: dest.execute('UPDATE feedback_drafts SET approval=NULL')
                    if 'health_state' in tables:
                        dest.execute("UPDATE health_state SET generation=?,epoch=NULL,sequence=0,batch_hash=NULL,connection='SOURCE_RECONNECT_REQUIRED',blocked=1,permissions=?",(str(uuid4()),encode({k:'NOT_REQUESTED' for k in ('sleep','steps','exercise')})))
                    if 'ai_jobs' in tables:
                        dest.execute("UPDATE ai_jobs SET state='CANCELLED',error='BACKUP_REAPPROVAL_REQUIRED' WHERE state IN ('QUEUED','RUNNING')")
                    if 'conversation_inferences' in tables:
                        dest.execute('UPDATE conversation_inferences SET state="FAILED",revision=revision+1,payload=json_set(payload,"$.state","FAILED","$.error","BACKUP_REAPPROVAL_REQUIRED","$.revision",revision+1) WHERE state IN ("QUEUED","RUNNING")')
                    if 'transcripts' in tables:
                        dest.execute("UPDATE transcripts SET state='FAILED',error='ASR_RESTORE_RETRY_REQUIRED' WHERE state IN ('TRANSCRIPTION_QUEUED','TRANSCRIBING')")
                    if 'audio' in tables: dest.execute("UPDATE audio SET state='CANCELLED' WHERE state='UPLOADING'")
                    if 'audio_chunks' in tables: dest.execute('DELETE FROM audio_chunks')
                    if 'release_backup_provenance' in tables:dest.execute('DROP TABLE release_backup_provenance')
                    if release_context is not None:
                        from .release_metadata import provenance
                        release_info=provenance(release_context['producer'],release_context['source'],version,created,private_identity=root_identity)
                        dest.execute('CREATE TABLE release_backup_provenance(payload TEXT NOT NULL)')
                        dest.execute('INSERT INTO release_backup_provenance VALUES(?)',(encode(release_info),))
                    dest.commit();dest.execute('PRAGMA journal_mode=DELETE')
                    self.check(dest)
                    if version >= 7:
                        from .practice import check_sessions
                        check_sessions(dest)
                    if version >= 8:
                        from .conversation import check_conversations
                        check_conversations(dest)
                    if version >= 9:
                        from .reflection import check_reflection
                        check_reflection(dest, enforce_current_unique=version >= 10)
                    if version >= 10:
                        from .conversation_controller import check_inferences
                        check_inferences(dest)
                    if version >= 11:
                        from .deep_session import check_deep
                        check_deep(dest)
                    attachments=self.check_audio(dest) if version >= 4 else []
                    meta = dict(dest.execute('SELECT * FROM vault_meta').fetchone())
                finally: dest.close()
            if attachments:
                folder=temp/'audio';folder.mkdir(mode=0o700)
                for a in attachments:
                    source=self.root/'audio'/a['file']
                    if not source.is_file() or source.stat().st_size!=a['byte_size'] or digest(source.read_bytes())!=a['content_hash']:
                        raise SafeError('AUDIO_CHECKSUM')
                    import shutil
                    shutil.copyfile(source,folder/a['file']);os.chmod(folder/a['file'],0o600)
                    if (folder/a['file']).stat().st_size!=a['byte_size'] or digest((folder/a['file']).read_bytes())!=a['content_hash']:raise SafeError('AUDIO_CHECKSUM')
                    with (folder/a['file']).open('rb') as file:os.fsync(file.fileno())
            manifest = {'backup_format': 2, 'schema_version': meta['schema_version'], 'app_version':'M7D',
                        'created_at_utc': created, 'attachments': attachments,
                        'files': {'snapshot.sqlite3': digest((temp / 'snapshot.sqlite3').read_bytes())}}
            if release_info is not None:
                manifest.update(backup_format=4 if private else 3,app_version=release_info['producing_manifest']['release_id'],release_provenance=release_info)
                if private:
                    from .local_private import POLICY
                    manifest.update(root_kind='PRIVATE_LOCAL',security_policy=POLICY)
            (temp / 'manifest.json').write_text(encode(manifest));private_files(temp)
            from .voice import fsync_dir
            for file in (temp/'snapshot.sqlite3',temp/'manifest.json'):
                with file.open('rb') as handle:os.fsync(handle.fileno())
            if attachments:fsync_dir(temp/'audio')
            fsync_dir(temp);temp.rename(p);fsync_dir(p.parent)
        except BaseException:
            import shutil
            shutil.rmtree(temp)
            raise
        return manifest

    @classmethod
    def restore(cls, backup, target, *, root_kind=RootKind.SYNTHETIC_TEST, private_creation=None):
        b, p = safe_path(backup), empty_target(target)
        private = RootKind(root_kind) == RootKind.PRIVATE_LOCAL
        if '.partial-' in b.name or not b.is_dir():raise SafeError('INVALID_BACKUP')
        try:
            m=json.loads((b/'manifest.json').read_text())
            if private != (m.get('backup_format')==4):raise SafeError('ROOT_KIND_MISMATCH')
            if private:
                from .local_private import RootReceipt, owner_only, require_volume
                if private_creation is None:raise SafeError('EXPLICIT_PRIVATE_INITIALIZATION_REQUIRED')
                private_creation=RootReceipt.model_validate(private_creation).model_dump()
                owner_only(b,tree=True);require_volume(b)
                owner_only(p if p.exists() else p.parent);require_volume(p)
                owner_only(private_creation['backup_directory']);require_volume(private_creation['backup_directory'])
            if m['backup_format'] not in {1,2,3,4} or m['schema_version'] not in {2,3,4,5,6,7,8,9,10,SCHEMA} or set(m['files'])!={'snapshot.sqlite3'}:raise SafeError('UNSUPPORTED_BACKUP')
            if m['backup_format'] not in {3,4} and 'release_provenance' in m:raise SafeError('BACKUP_RELEASE_PROVENANCE')
            attachments=m['attachments']
            if not isinstance(attachments,list) or m['backup_format']==1 and attachments:raise SafeError('UNSUPPORTED_BACKUP')
            expected={'manifest.json','snapshot.sqlite3'}|({'audio'} if attachments else set())
            if {x.name for x in b.iterdir()}!=expected:raise SafeError('INVALID_BACKUP')
            if m['files']['snapshot.sqlite3']!=digest((b/'snapshot.sqlite3').read_bytes()):raise SafeError('CHECKSUM_MISMATCH')
            with sqlite3.connect(f'file:{b / "snapshot.sqlite3"}?mode=ro&immutable=1',uri=True) as source:
                source.row_factory=sqlite3.Row;cls.check(source)
                if source.execute('SELECT schema_version FROM vault_meta').fetchone()[0]!=m['schema_version']:raise SafeError('UNSUPPORTED_SCHEMA')
                if m['backup_format'] in {3,4}:
                    from .release_metadata import check_backup_provenance
                    check_backup_provenance(m,source)
                elif source.execute("SELECT 1 FROM sqlite_master WHERE name='release_backup_provenance'").fetchone():raise SafeError('BACKUP_RELEASE_PROVENANCE')
                if m['schema_version']>=7:
                    from .practice import check_sessions
                    check_sessions(source)
                if m['schema_version']>=8:
                    from .conversation import check_conversations
                    check_conversations(source)
                if m['schema_version']>=9:
                    from .reflection import check_reflection
                    check_reflection(source,enforce_current_unique=m['schema_version']>=10)
                if m['schema_version']>=10:
                    from .conversation_controller import check_inferences
                    check_inferences(source)
                if m['schema_version']>=11:
                    from .deep_session import check_deep
                    check_deep(source)
                required=cls.check_audio(source)
                if attachments!=required:raise SafeError('AUDIO_REFERENCE_INTEGRITY')
            if attachments:
                if not (b/'audio').is_dir() or {x.name for x in (b/'audio').iterdir()}!={a['file'] for a in attachments}:raise SafeError('INVALID_BACKUP')
                from .audio_format import PCMConverter
                for a in attachments:
                    # Filename is derived solely from typed DB UUIDs; manifest cannot select arbitrary paths.
                    file=b/'audio'/a['file']
                    if not file.is_file() or file.stat().st_size!=a['byte_size'] or digest(file.read_bytes())!=a['content_hash']:raise SafeError('AUDIO_CHECKSUM')
                    PCMConverter().normalize(file.read_bytes(),'audio/wav')
        except (KeyError,ValueError,TypeError,sqlite3.Error,OSError):raise SafeError('INVALID_BACKUP') from None
        temp=p.with_name(p.name+'.partial-'+str(uuid4()));temp.mkdir(mode=0o700)
        try:
            import shutil
            shutil.copyfile(b/'snapshot.sqlite3',temp/'journal.sqlite3')
            if attachments:shutil.copytree(b/'audio',temp/'audio')
            marker_name = 'private-local.json' if private else 'synthetic.json'
            (temp/marker_name).write_text(encode(private_creation if private else MARKER))
            with sqlite3.connect(temp/'journal.sqlite3') as c:
                if m['backup_format'] in {3,4}:c.execute('DROP TABLE release_backup_provenance')
                if private:c.execute('UPDATE private_root_identity SET payload=?',(encode(private_creation),))
                elif c.execute("SELECT 1 FROM sqlite_master WHERE name='private_root_identity'").fetchone():raise SafeError('ROOT_KIND_MISMATCH')
                c.execute("UPDATE vault_meta SET restore_epoch=restore_epoch+1,reconciliation='RESTORED_REQUIRES_RECONCILIATION'")
            with sqlite3.connect(temp/'journal.sqlite3') as c:
                if m['schema_version']>=5:c.execute('UPDATE feedback_drafts SET approval=NULL')
                if m['schema_version']>=8:
                    c.execute('UPDATE conversation_receipts SET fingerprint=NULL')
                if m['schema_version']>=7:
                    # Restore never resumes sessions or restores runtime activation decisions.
                    c.execute("UPDATE practice_sessions SET revision=revision+1,payload=json_set(payload,'$.state','BLOCKED_BY_ADMISSION','$.blocked_reason','RESTORE_REVALIDATION_REQUIRED','$.revision',revision+1) WHERE json_extract(payload,'$.state') IN ('ACTIVE','PAUSED')")
                    c.execute('UPDATE practice_receipts SET fingerprint=NULL')
                if m['schema_version']>=6:
                    c.execute("UPDATE health_records SET status='UNKNOWN',payload=json_set(payload,'$.status','UNKNOWN') WHERE status='VALUE'")
                    c.execute("UPDATE health_state SET generation=?,epoch=NULL,sequence=0,batch_hash=NULL,connection='SOURCE_RECONNECT_REQUIRED',blocked=1,permissions=?",(str(uuid4()),encode({k:'NOT_REQUESTED' for k in ('sleep','steps','exercise')})))
            private_files(temp)
            if attachments:
                for f in (temp/'audio').iterdir():os.chmod(f,0o600)
            from .voice import fsync_dir
            for f in (temp/'journal.sqlite3',temp/marker_name):
                with f.open('rb') as h:os.fsync(h.fileno())
            fsync_dir(temp)
            if p.exists():p.rmdir()
            temp.rename(p);fsync_dir(p.parent)
        except BaseException:
            import shutil
            shutil.rmtree(temp);raise
        return cls(p, root_kind=root_kind)
