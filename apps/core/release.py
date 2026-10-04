"""M8C local unsigned release lifecycle; distinct synthetic/private profiles. No dependency installation/network."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
from uuid import uuid4
from .storage import Store, SafeError, MARKER, SCHEMA, REPO, safe_path, empty_target, encode, digest
from .voice import durable_write, fsync_dir

from .release_metadata import DEFAULTS,CONTRACT,identity,validate_manifest,check_backup_provenance
from .root_types import RootKind
INSTALL_MARKER = 'M8A_SYNTHETIC_INSTALL_V1'
PRIVATE_INSTALL_MARKER = 'M8C_PRIVATE_LOCAL_INSTALL_V1'

def read_json(path):
    try:
        def unique(items):
            result = {}
            for k, v in items:
                if k in result: raise ValueError()
                result[k] = v
            return result
        value=json.loads(Path(path).read_text(), object_pairs_hook=unique)
        if not isinstance(value,dict): raise ValueError()
        return value
    except (OSError, ValueError, TypeError): raise SafeError('INVALID_METADATA') from None

def file_hashes(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise SafeError('SYMLINK_DENIED')
        if p.is_file() and p != root/'release-manifest.json':
            result[p.relative_to(root).as_posix()] = digest(p.read_bytes())
    return result

def package_path(path):
    p=Path(path).absolute()
    if p.is_relative_to(REPO/'generated/releases') or (p == REPO and (p/'release-manifest.json').is_file() and not (p/'.git').exists()):
        if '..' in p.parts or any(c.is_symlink() for c in (p,*p.parents)):
            raise SafeError('SYMLINK_DENIED')
        if p.exists() and any(x.is_symlink() or x.name=='.git' for x in p.rglob('*')):
            raise SafeError('PACKAGE_SOURCE_INVALID')
        return p
    return safe_path(p)

def validate_package(package, expected_hash):
    package = package_path(package)
    m = read_json(package / 'release-manifest.json')
    validate_manifest(m)
    if m['manifest_hash']!=expected_hash or file_hashes(package)!=m['files']:raise SafeError('RELEASE_INTEGRITY')
    if m['format'] in {2,3}:
        from .pilot_readiness import validate_profile
        validate_profile(package/'packages/pilot/MAC_CORE_PROFILE.json')
    if m['format']==3:
        from .local_private import PROFILE
        if read_json(package/'packages/pilot/MAC_PRIVATE_CORE_PROFILE.json')!=PROFILE:raise SafeError('PILOT_PROFILE_INCOMPATIBLE')
    return m

def prepare(output):
    """Build only the exact clean checkout. Existing node_modules/Python are prerequisites."""
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()
    if git('status', '--porcelain'): raise SafeError('CLEAN_CHECKOUT_REQUIRED')
    commit = git('rev-parse', 'HEAD')
    output = Path(output).absolute()
    # Generated package may live inside ignored generated/, installation/data may never do so.
    if output.is_relative_to(REPO) and not output.is_relative_to(REPO / 'generated/releases'):
        raise SafeError('GENERATED_OUTPUT_REQUIRED')
    if output.exists() or not output.parent.is_dir(): raise SafeError('NEW_OUTPUT_WITH_PARENT_REQUIRED')
    for component in (output, *output.parents):
        if component.is_symlink(): raise SafeError('SYMLINK_DENIED')
    if not (REPO / 'apps/web/node_modules/.bin/vite').is_file(): raise SafeError('BUILD_PREREQUISITE_UNAVAILABLE')
    subprocess.run(['npm', '--prefix', str(REPO/'apps/web'), 'run', 'build'], cwd=REPO,
                   env=dict(os.environ, PC_BUILD_COMMIT=commit), check=True)
    temp = output.with_name(output.name + '.partial-' + str(uuid4()))
    temp.mkdir(mode=0o700)
    try:
        tracked = git('ls-files').splitlines()
        prefixes = ('apps/core/', 'skills/conversation/', 'packages/practices/synthetic/', 'research/admission/')
        specific = {'requirements.lock','requirements.runtime.lock','packages/pilot/MAC_CORE_PROFILE.json','packages/pilot/MAC_PRIVATE_CORE_PROFILE.json', 'apps/web/package-lock.json', 'scripts/m7_admission.py',
                    'apps/web/src/PracticePanel.tsx', 'apps/web/src/practice-model.ts', 'apps/web/src/style.css'}
        for name in tracked:
            if name in specific or name.startswith(prefixes):
                source = REPO/name
                if not source.is_file() or source.is_symlink(): raise SafeError('PACKAGE_SOURCE_INVALID')
                target = temp/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        shutil.copytree(REPO/'apps/web/dist', temp/'apps/web/dist')
        (temp/'launch.py').write_text("import sys\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom apps.core.release import main\nmain()\n")
        files = file_hashes(temp)
        m = {'format': 3, 'release_id': 'M8C-'+commit, 'git_commit': commit, 'schema_version': SCHEMA,
             'python_input_hash': files['requirements.lock'], 'runtime_input_hash': files['requirements.runtime.lock'], 'web_lock_hash': files['apps/web/package-lock.json'],
             'platform': {'os': 'Darwin', 'architecture': 'arm64', 'python': '3.13', 'dependencies': 'EXACT_RUNTIME_LOCK', 'self_contained': False},
             'defaults': DEFAULTS, 'compatibility': {'schema_min': 2, 'schema_max': SCHEMA, 'web_contract': CONTRACT, 'downgrade': 'FRESH_ROOT_BACKUP_ONLY'}, 'files': files}
        m['manifest_hash'] = identity(m)
        (temp/'release-manifest.json').write_text(encode(m))
        if git('rev-parse', 'HEAD') != commit or git('status', '--porcelain'): raise SafeError('CHECKOUT_CHANGED')
        fsync_dir(temp); temp.rename(output); fsync_dir(output.parent)
    except BaseException:
        shutil.rmtree(temp); raise
    return m

def separated(app, data):
    app, data = safe_path(app), safe_path(data)
    if app == data or app.is_relative_to(data) or data.is_relative_to(app): raise SafeError('APP_DATA_OVERLAP')
    return app, data

@contextmanager
def operation_lock(data):
    data = safe_path(data)
    lock = data.with_name(data.name + '.m8a-lock')
    safe_path(lock)
    if not lock.parent.is_dir(): raise SafeError('PARENT_REQUIRED')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise SafeError('DATA_ROOT_BUSY') from None
        yield
    finally: os.close(fd)  # Keep inode; unlink would permit a competing lock inode.

def inspect_data(data, root_kind=RootKind.SYNTHETIC_TEST):
    """Read-only gate; never initializes/migrates/prints rows or private identifiers."""
    data = safe_path(data)
    if not data.exists(): return None
    private = RootKind(root_kind)==RootKind.PRIVATE_LOCAL
    if private:
        from .local_private import validate_root
        validate_root(data)
    else:
        if (data/'private-local.json').exists():raise SafeError('ROOT_KIND_MISMATCH')
        if read_json(data/'synthetic.json') != MARKER: raise SafeError('SYNTHETIC_ROOT_REQUIRED')
    allowed = {'private-local.json' if private else 'synthetic.json', 'journal.sqlite3', 'journal.sqlite3-wal', 'journal.sqlite3-shm', 'preupgrade.sqlite3', 'audio', 'audio-staging'}
    if {p.name for p in data.iterdir()} - allowed: raise SafeError('UNKNOWN_ROOT_CONTENT')
    try:
        with sqlite3.connect((data/'journal.sqlite3').as_uri()+'?mode=ro', uri=True) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute('SELECT schema_version FROM vault_meta').fetchall()
            if len(rows) != 1 or type(rows[0][0]) is not int: raise SafeError('INVALID_METADATA')
            version = rows[0][0]
            if not 2 <= version <= SCHEMA: raise SafeError('UNSUPPORTED_SCHEMA')
            if not private and c.execute("SELECT 1 FROM sqlite_master WHERE name='private_root_identity'").fetchone():raise SafeError('ROOT_KIND_MISMATCH')
            Store.check(c)
            if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': raise SafeError('DATABASE_INTEGRITY')
            if c.execute('PRAGMA foreign_key_check').fetchone(): raise SafeError('DATABASE_INTEGRITY')
            return version
    except sqlite3.Error: raise SafeError('INVALID_METADATA') from None

def runtime_checks(package):
    checks = []
    platform_ok = platform.system() == 'Darwin' and platform.machine() == 'arm64'
    checks.append({'gate': 'platform', 'status': 'PASS' if platform_ok else 'INCOMPATIBLE'})
    checks.append({'gate': 'python', 'status': 'PASS' if sys.version_info[:2] == (3, 13) else 'INCOMPATIBLE', 'version': platform.python_version()})
    manifest=read_json(package/'release-manifest.json')
    dependency_file='requirements.runtime.lock' if manifest['format'] in {2,3} else 'requirements.lock'
    for line in (package/dependency_file).read_text().splitlines():
        name, version = line.split('==')
        try: available = importlib.metadata.version(name) == version
        except importlib.metadata.PackageNotFoundError: available = False
        checks.append({'gate': 'dependency:'+name, 'status': 'PASS' if available else 'INCOMPATIBLE'})
    checks += [{'gate': 'local_asr', 'status': 'OPTIONAL_UNAVAILABLE', 'reason': 'NO_WEIGHTS_OR_ENGINE_PACKAGED'},
               {'gate': 'phone_health_transport', 'status': 'NOT_RUN', 'reason': 'PHONE_TRANSPORT_AND_HEALTH_SEPARATE_GATES'}]
    return checks

def preflight(package, expected_hash, app, data, port=8765):
    package = package_path(package); app, data = separated(app, data)
    m = validate_package(package, expected_hash)
    if package == app or package.is_relative_to(app) or app.is_relative_to(package) or package == data or package.is_relative_to(data) or data.is_relative_to(package): raise SafeError('PACKAGE_PATH_OVERLAP')
    version = inspect_data(data)
    checks = runtime_checks(package)
    if app.exists(): selected(app,data)
    for label, p in [('application_path', app), ('data_path', data)]:
        parent = p if p.exists() else p.parent
        checks.append({'gate': label, 'status': 'PASS' if parent.is_dir() and os.access(parent, os.W_OK) and shutil.disk_usage(parent).free >= 32*1024*1024 else 'INCOMPATIBLE'})
    if not 1024 <= port <= 65535: raise SafeError('INVALID_PORT')
    try:
        with socket.socket() as s: s.bind(('127.0.0.1', port))
        checks.append({'gate': 'loopback_port', 'status': 'PASS'})
    except OSError: checks.append({'gate': 'loopback_port', 'status': 'INCOMPATIBLE'})
    return {'status': 'INCOMPATIBLE' if any(c['status']=='INCOMPATIBLE' for c in checks) else 'PASS',
            'release_id': m['release_id'], 'manifest_hash': expected_hash, 'schema': version,
            'target_schema': SCHEMA, 'checks': checks, 'defaults': DEFAULTS, 'data': 'SYNTHETIC_ONLY'}

def require_preflight(package, expected_hash, app, data, port=8765):
    result = preflight(package, expected_hash, app, data, port)
    if result['status'] != 'PASS': raise SafeError('PREFLIGHT_INCOMPATIBLE')
    return result

def receipt(app, root_kind=RootKind.SYNTHETIC_TEST):
    if RootKind(root_kind)==RootKind.PRIVATE_LOCAL:
        from .local_private import owner_only
        owner_only(app); owner_only(app/'installation.json')
    value = read_json(app/'installation.json')
    if RootKind(root_kind)==RootKind.PRIVATE_LOCAL:
        if set(value)!={'kind','data_root','root_kind','root_id'} or value['kind']!=PRIVATE_INSTALL_MARKER or value['root_kind']!='PRIVATE_LOCAL':raise SafeError('ROOT_KIND_MISMATCH')
        from .local_private import validate_root
        if validate_root(value['data_root'])['root_id']!=value['root_id']:raise SafeError('PRIVATE_ROOT_IDENTITY_MISMATCH')
    elif set(value) != {'kind', 'data_root'} or value['kind'] != INSTALL_MARKER: raise SafeError('UNKNOWN_INSTALLATION')
    separated(app, value['data_root'])
    return value

def selected(app, data, root_kind=RootKind.SYNTHETIC_TEST):
    app, data = separated(app, data)
    if receipt(app,root_kind)['data_root'] != str(data): raise SafeError('DATA_ROOT_MISMATCH')
    if RootKind(root_kind)==RootKind.PRIVATE_LOCAL:
        from .local_private import owner_only
        owner_only(app/'active.json')
    active = read_json(app/'active.json')
    if set(active) != {'release_id', 'manifest_hash'} or not re.fullmatch(r'M8[ABC]-[0-9a-f]{40}', active['release_id']): raise SafeError('INVALID_METADATA')
    package = app/'releases'/active['release_id']
    return package, validate_package(package, active['manifest_hash'])

def stage(package, app, m):
    releases = app/'releases'; releases.mkdir(exist_ok=True)
    target = releases/m['release_id']
    if target.exists():
        validate_package(target, m['manifest_hash']); return target
    temp = releases/(m['release_id']+'.partial-'+str(uuid4()))
    try:
        shutil.copytree(package, temp)
        validate_package(temp, m['manifest_hash']); temp.rename(target); fsync_dir(releases)
    except BaseException:
        if temp.exists(): shutil.rmtree(temp)
        raise
    return target

def activate(app, m):
    durable_write(app/'active.json', encode({'release_id': m['release_id'], 'manifest_hash': m['manifest_hash']}).encode())

def install(package, expected_hash, app, data):
    app, data = separated(app, data)
    with operation_lock(data):
        require_preflight(package, expected_hash, app, data)
        empty_target(app)
        if app.exists() or data.exists(): raise SafeError('FRESH_INSTALL_REQUIRES_NEW_ROOTS')
        m = validate_package(package, expected_hash)
        app.mkdir(mode=0o700)
        durable_write(app/'installation.json', encode({'kind': INSTALL_MARKER, 'data_root': str(data)}).encode())
        stage(package, app, m)
        Store(data)
        activate(app, m)
    return {'status': 'PASS', 'operation': 'CLEAN_SYNTHETIC_ROOT', 'release_id': m['release_id'], 'defaults': DEFAULTS}

def old_store(data, root_kind=RootKind.SYNTHETIC_TEST):
    # Construct a read/backup handle without Store.__init__ (which migrates).
    s = Store.__new__(Store); s.root=safe_path(data); s.db=s.root/'journal.sqlite3'
    s.root_kind=RootKind(root_kind);s._creating_private=False
    s.attachment_lock=threading.RLock(); s.fail_commit=False; s.commit_error=None
    return s

def check_writer(manifest):
    # Attribute producing build to actual writer sources, not just active app labels.
    for name,expected in manifest['files'].items():
        if name.startswith('apps/core/') and name.endswith('.py'):
            if expected!=digest((REPO/name).read_bytes()):raise SafeError('BACKUP_WRITER_RELEASE_MISMATCH')

def verify_backup(backup,expected_producer_hash=None,expected_backup_hash=None,allow_legacy=False):
    backup=safe_path(backup); m=read_json(backup/'manifest.json')
    if not isinstance(m.get('files'),dict) or m['files'].get('snapshot.sqlite3') != digest((backup/'snapshot.sqlite3').read_bytes()): raise SafeError('CHECKSUM_MISMATCH')
    if expected_backup_hash is not None and digest((backup/'manifest.json').read_bytes())!=expected_backup_hash:raise SafeError('BACKUP_MANIFEST_CHECKSUM')
    if m.get('backup_format') not in {3,4} and not allow_legacy:raise SafeError('LEGACY_BACKUP_REQUIRES_EXPLICIT_APPROVAL')
    with sqlite3.connect((backup/'snapshot.sqlite3').as_uri()+'?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row; Store.check(c)
        if m.get('backup_format') in {3,4}:check_backup_provenance(m,c,expected_producer_hash)
        elif 'release_provenance' in m or c.execute("SELECT 1 FROM sqlite_master WHERE name='release_backup_provenance'").fetchone():raise SafeError('BACKUP_RELEASE_PROVENANCE')
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise SafeError('DATABASE_INTEGRITY')
    return m

def upgrade(package, expected_hash, app, data, backup, *, fail_migration=False, root_kind=RootKind.SYNTHETIC_TEST):
    app, data = separated(app, data); backup = safe_path(backup)
    if backup == data or backup.is_relative_to(data) or data.is_relative_to(backup) or backup == app or backup.is_relative_to(app) or app.is_relative_to(backup): raise SafeError('BACKUP_PATH_OVERLAP')
    with operation_lock(data):
        lifecycle_preflight(package, expected_hash, app, data, root_kind)
        if (app/'upgrade-pending.json').exists(): raise SafeError('UPGRADE_RECOVERY_REQUIRED')
        _, previous = selected(app, data, root_kind)
        version = inspect_data(data, root_kind)
        if version is None: raise SafeError('MISSING_DATABASE')
        empty_target(backup)
        if backup.exists(): raise SafeError('TARGET_MUST_BE_NEW')
        m = validate_package(package, expected_hash)
        stage(package, app, m)  # Missing assets/storage failure happens before touching data.
        check_writer(m)
        old_store(data,root_kind).backup(backup,release_context={'producer':m,'source':previous})
        verify_backup(backup,m['manifest_hash'])
        # Durable pending marker precedes migration. Interrupted operation requires explicit recovery.
        durable_write(app/'upgrade-pending.json', encode({'from': previous['release_id'], 'to': m['release_id'], 'backup_verified': True}).encode())
        try:
            Store(data, fail_migration=fail_migration,root_kind=root_kind)
            inspect_data(data, root_kind)
            activate(app, m)
            (app/'upgrade-pending.json').unlink(); fsync_dir(app)
        except BaseException:
            # Transactional migration preserves prior DB; marker and consistent backup remain.
            raise
    return {'status': 'PASS', 'operation': 'UPGRADE', 'schema_from': version, 'schema_to': SCHEMA, 'backup': 'VERIFIED', 'backup_manifest_hash':digest((backup/'manifest.json').read_bytes()), 'defaults': DEFAULTS}

def restore(package, expected_hash, backup, app, data, *, expected_producer_hash=None,expected_backup_hash=None,allow_legacy=False,root_kind=RootKind.SYNTHETIC_TEST,backup_directory=None,confirmation=None,consent=None,acknowledge_no_cloud=False):
    app, data = separated(app, data)
    with operation_lock(data):
        private=RootKind(root_kind)==RootKind.PRIVATE_LOCAL
        if private:
            from .local_private import require_preflight as private_preflight, activation_receipt, owner_only, require_volume
            private_preflight(package,expected_hash,app,data,backup_directory)
            new_receipt=activation_receipt(data,expected_hash,backup_directory,confirmation,consent,acknowledge_no_cloud)
            owner_only(backup,tree=True);require_volume(backup)
        else:require_preflight(package, expected_hash, app, data)
        empty_target(app)
        if app.exists() or data.exists(): raise SafeError('RESTORE_REQUIRES_NEW_ROOTS')
        metadata=verify_backup(backup,expected_producer_hash or expected_hash,expected_backup_hash,allow_legacy)
        if private != (metadata.get('backup_format')==4):raise SafeError('ROOT_KIND_MISMATCH')
        m=validate_package(package, expected_hash)
        app.mkdir(mode=0o700)
        durable_write(app/'installation.json', encode(install_receipt(data,root_kind,new_receipt if private else None)).encode())
        stage(package, app, m)
        Store.restore(backup, data,root_kind=root_kind,private_creation=new_receipt if private else None)
        inspect_data(data,root_kind); activate(app, m)
    return {'status': 'PASS', 'operation': 'FRESH_ROOT_RESTORE_OR_ROLLBACK', 'backup_provenance':'VERIFIED' if metadata['backup_format'] in {3,4} else 'LEGACY_UNKNOWN_PRODUCER', 'defaults': DEFAULTS}

def backup(app, data, target, root_kind=RootKind.SYNTHETIC_TEST):
    with operation_lock(data):
        _,m=selected(app,data,root_kind); inspect_data(data,root_kind);check_writer(m)
        target=safe_path(target)
        for p in (safe_path(app),safe_path(data)):
            if target==p or target.is_relative_to(p) or p.is_relative_to(target): raise SafeError('BACKUP_PATH_OVERLAP')
        old_store(data,root_kind).backup(target,release_context={'producer':m,'source':m}); verify_backup(target,m['manifest_hash'])
    return {'status':'PASS','operation':'BACKUP','release_id':m['release_id'],'producing_manifest_hash':m['manifest_hash'],'backup_manifest_hash':digest((target/'manifest.json').read_bytes())}

def uninstall(app, data, root_kind=RootKind.SYNTHETIC_TEST):
    app, data=separated(app, data)
    with operation_lock(data):
        receipt(app,root_kind)
        if receipt(app,root_kind)['data_root']!=str(data): raise SafeError('DATA_ROOT_MISMATCH')
        inspect_data(data,root_kind)
        if {p.name for p in app.iterdir()}-{'installation.json','releases','active.json','upgrade-pending.json','active.json.writing','upgrade-pending.json.writing'}: raise SafeError('UNKNOWN_INSTALLATION_CONTENT')
        shutil.rmtree(app)
    return {'status': 'PASS', 'operation': 'REMOVE_RUNTIME_KEEP_DATA', 'data_preserved': True, 'backups_preserved': True}

def delete_synthetic_data(data, confirmation):
    data=safe_path(data)
    if confirmation != 'DELETE_SYNTHETIC_DATA:'+str(data): raise SafeError('EXPLICIT_DATA_DELETE_REQUIRED')
    with operation_lock(data):
        inspect_data(data)
        if not data.exists(): raise SafeError('MISSING_DATABASE')
        shutil.rmtree(data)
    return {'status': 'PASS', 'operation': 'EXPLICIT_SYNTHETIC_DATA_DELETE', 'secure_erasure': 'NOT_CLAIMED', 'backups_deleted': False}

def serve(app, data, port, root_kind=RootKind.SYNTHETIC_TEST):
    app, data=separated(app, data)
    with operation_lock(data):
        package,m=selected(app,data,root_kind)
        if (app/'upgrade-pending.json').exists(): raise SafeError('UPGRADE_RECOVERY_REQUIRED')
        if inspect_data(data,root_kind)!=SCHEMA: raise SafeError('EXPLICIT_UPGRADE_REQUIRED')
    # Replace launcher process. Ctrl+C/SIGTERM targets the one foreground server; no orphan child.
    os.execv(sys.executable,[sys.executable,'-I','-B',str(package/'launch.py'),'_serve','--app',str(app),
                            '--package',str(package),'--manifest-hash',m['manifest_hash'],'--data',str(data),'--port',str(port),'--mode',str(root_kind)])

def run_server(package, expected_hash, app_root, data, port, root_kind=RootKind.SYNTHETIC_TEST):
    with operation_lock(data):
        current,m=selected(app_root,data,root_kind)
        if current!=package or m['manifest_hash']!=expected_hash: raise SafeError('RELEASE_CHANGED')
        if (app_root/'upgrade-pending.json').exists(): raise SafeError('UPGRADE_RECOVERY_REQUIRED')
        if inspect_data(data,root_kind)!=SCHEMA: raise SafeError('EXPLICIT_UPGRADE_REQUIRED')
        if not 1024<=port<=65535: raise SafeError('INVALID_PORT')
        if any(c['status']=='INCOMPATIBLE' for c in runtime_checks(package)): raise SafeError('PREFLIGHT_INCOMPATIBLE')
        private=RootKind(root_kind)==RootKind.PRIVATE_LOCAL
        if private:
            from .local_private import validate_root
            validate_root(data,security=True)
            if m['format']!=3:raise SafeError('PRIVATE_RELEASE_REQUIRED')
        from .network import deny_egress
        deny_egress()
        from .api import create_app
        import uvicorn
        application=create_app(data,port=port,web=package/'apps/web/dist',synthetic_conversations=not private,m7c_synthetic=not private,root_kind=root_kind,
                               release_identity=m['git_commit'])
        print(f'Local {"private" if private else "synthetic"} runtime: http://127.0.0.1:{port}',flush=True)
        print('One-time unlock code: '+application.state.auth.code,flush=True)
        print('Stop: Ctrl+C; no daemon/autostart. Restart generates new unlock state.',flush=True)
        uvicorn.run(application,host='127.0.0.1',port=port,access_log=False,log_level='critical')

def install_receipt(data,root_kind,private_receipt=None):
    if RootKind(root_kind)==RootKind.PRIVATE_LOCAL:
        return {'kind':PRIVATE_INSTALL_MARKER,'data_root':str(data),'root_kind':'PRIVATE_LOCAL','root_id':private_receipt['root_id']}
    return {'kind':INSTALL_MARKER,'data_root':str(data)}

def lifecycle_preflight(package,expected_hash,app,data,root_kind):
    if RootKind(root_kind)==RootKind.PRIVATE_LOCAL:
        from .local_private import validate_root,require_preflight as private_preflight
        value=validate_root(data,security=True)
        return private_preflight(package,expected_hash,app,data,value['backup_directory'])
    return require_preflight(package,expected_hash,app,data)

def initialize_private(package,expected_hash,app,data,backup_directory,confirmation,consent,acknowledge_no_cloud):
    from .local_private import require_preflight as private_preflight,activation_receipt
    app,data=separated(app,data)
    with operation_lock(data):
        private_preflight(package,expected_hash,app,data,backup_directory)
        empty_target(app)
        if app.exists():raise SafeError('FRESH_INSTALL_REQUIRES_NEW_ROOTS')
        value=activation_receipt(data,expected_hash,backup_directory,confirmation,consent,acknowledge_no_cloud)
        m=validate_package(package,expected_hash)
        app.mkdir(mode=0o700)
        stage(package,app,m)
        Store(data,root_kind=RootKind.PRIVATE_LOCAL,private_creation=value)
        durable_write(app/'installation.json',encode(install_receipt(data,RootKind.PRIVATE_LOCAL,value)).encode())
        activate(app,m)
    return {'status':'PASS','operation':'EXPLICIT_PRIVATE_LOCAL_INITIALIZATION','root_kind':'PRIVATE_LOCAL','release_id':m['release_id'],'application_level_encryption':'NOT_IMPLEMENTED'}

def delete_private_data(data,confirmation):
    data=safe_path(data)
    if confirmation!='DELETE_PRIVATE_LOCAL_DATA:'+str(data):raise SafeError('EXPLICIT_PRIVATE_DATA_DELETE_REQUIRED')
    with operation_lock(data):
        inspect_data(data,RootKind.PRIVATE_LOCAL)
        if not data.exists():raise SafeError('MISSING_DATABASE')
        shutil.rmtree(data)
    return {'status':'PASS','operation':'EXPLICIT_PRIVATE_LOCAL_DATA_DELETE','secure_erasure':'NOT_CLAIMED','backups_deleted':False}

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    for command in ('prepare','preflight','mac-preflight','private-preflight','initialize-private','install','upgrade','restore','rollback','backup','start','uninstall','delete-synthetic-data','delete-private-data','_serve'):
        s=sub.add_parser(command)
        if command=='prepare': s.add_argument('--output',type=Path,required=True); continue
        if command in {'delete-synthetic-data','delete-private-data'}:
            s.add_argument('--data',type=Path,required=True); s.add_argument('--confirm',required=True); continue
        if command in {'preflight','mac-preflight','private-preflight','initialize-private','install','upgrade','restore','rollback','_serve'}:
            s.add_argument('--package',type=Path,required=True); s.add_argument('--manifest-hash',required=True)
        s.add_argument('--mode',choices=[v.value for v in RootKind],default=RootKind.SYNTHETIC_TEST.value)
        if command in {'private-preflight','initialize-private','restore','rollback'}:s.add_argument('--backup-directory',type=Path)
        if command in {'initialize-private','restore','rollback'}:
            s.add_argument('--confirm');s.add_argument('--data-owner-consent');s.add_argument('--acknowledge-no-cloud-directory',action='store_true')
        s.add_argument('--app',type=Path,required=True)
        s.add_argument('--data',type=Path,required=True)
        if command in {'preflight','mac-preflight','private-preflight','start','_serve'}: s.add_argument('--port',type=int,default=8765)
        if command in {'upgrade','restore','rollback','backup'}: s.add_argument('--backup',type=Path,required=True)
        if command in {'restore','rollback'}:
            s.add_argument('--producer-manifest-hash');s.add_argument('--backup-manifest-hash');s.add_argument('--allow-legacy-backup',action='store_true')
    a=p.parse_args()
    try:
        if getattr(a,'mode',None)=='PRIVATE_LOCAL' and a.command in {'install','preflight','mac-preflight'}:raise SafeError('USE_EXPLICIT_PRIVATE_INITIALIZATION_OR_PREFLIGHT')
        if a.command=='prepare': result=prepare(a.output)
        elif a.command=='preflight': result=preflight(a.package,a.manifest_hash,a.app,a.data,a.port)
        elif a.command=='mac-preflight':
            from .pilot_readiness import reference_mac_preflight
            result=reference_mac_preflight(a.package,a.manifest_hash,a.app,a.data,a.port)
        elif a.command=='private-preflight':
            from .local_private import preflight as private_preflight
            result=private_preflight(a.package,a.manifest_hash,a.app,a.data,a.backup_directory,a.port)
        elif a.command=='initialize-private':result=initialize_private(a.package,a.manifest_hash,a.app,a.data,a.backup_directory,a.confirm,a.data_owner_consent,a.acknowledge_no_cloud_directory)
        elif a.command=='install': result=install(a.package,a.manifest_hash,a.app,a.data)
        elif a.command=='upgrade': result=upgrade(a.package,a.manifest_hash,a.app,a.data,a.backup,root_kind=a.mode)
        elif a.command in {'restore','rollback'}: result=restore(a.package,a.manifest_hash,a.backup,a.app,a.data,expected_producer_hash=a.producer_manifest_hash,expected_backup_hash=a.backup_manifest_hash,allow_legacy=a.allow_legacy_backup,root_kind=a.mode,backup_directory=a.backup_directory,confirmation=a.confirm,consent=a.data_owner_consent,acknowledge_no_cloud=a.acknowledge_no_cloud_directory)
        elif a.command=='backup': result=backup(a.app,a.data,a.backup,root_kind=a.mode)
        elif a.command=='uninstall': result=uninstall(a.app,a.data,root_kind=a.mode)
        elif a.command=='delete-synthetic-data': result=delete_synthetic_data(a.data,a.confirm)
        elif a.command=='delete-private-data':result=delete_private_data(a.data,a.confirm)
        elif a.command=='_serve': run_server(a.package,a.manifest_hash,a.app,a.data,a.port,root_kind=a.mode); return
        else: serve(a.app,a.data,a.port,root_kind=a.mode); return
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result.get('status') in {'INCOMPATIBLE','SECURITY_REQUIREMENT_NOT_MET','BLOCKED_BY_PERMISSION'} or a.command=='private-preflight' and result.get('status')!='PASS': raise SystemExit(1)
    except (SafeError,OSError,ValueError,sqlite3.Error,subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'INCOMPATIBLE','code':exc.code if isinstance(exc,SafeError) else 'LOCAL_OPERATION_FAILED'}))
        raise SystemExit(1)

if __name__=='__main__': main()
