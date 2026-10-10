"""Native-shell pipe protocol. Managed standalone roots only; no pilot discovery.

stdout is an inherited anonymous IPC pipe, never a console or persisted log.
Credentials appear only in an unlock reply after a native user action.
"""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import socket
import sys
import tempfile
import threading
import time
from uuid import uuid4

from . import release as r
from .root_types import RootKind
from .storage import Store, SafeError, digest, encode, safe_path
from .voice import durable_write, fsync_dir

PRODUCT = 'org.personalcompanion.standalone'
CHANNEL = 'M8F_LOCAL_TEST'
ERRORS = {
    'ALREADY_RUNNING', 'NATIVE_INITIALIZATION_REQUIRED', 'NATIVE_CONSENT_REQUIRED',
    'NATIVE_ROOT_INVALID', 'NATIVE_MANIFEST_INVALID', 'UPDATE_IDENTITY_INVALID',
    'UPDATE_SPACE_REQUIRED', 'UPDATE_MIGRATION_PLAN_REQUIRED', 'UPDATE_RECOVERY_REQUIRED',
    'OWNER_ONLY_PERMISSIONS_REQUIRED', 'EXTENDED_ACL_DENIED', 'VOLUME_PROTECTION_REQUIRED',
    'BLOCKED_BY_PERMISSION', 'BACKUP_RELEASE_PROVENANCE', 'LOCKED', 'LOCAL_ASR_ISOLATION_UNAVAILABLE',
    'NATIVE_OPERATION_FAILED', 'PREFLIGHT_INCOMPATIBLE', 'UPGRADE_RECOVERY_REQUIRED',
}


def native_code_hash(path):
    """Hash executable bytes without its resource-dependent outer code signature.

    Apple codesign, rather than a bespoke Mach-O parser, removes the seal on a
    disposable copy. The bundle's actual seal is independently verified at build
    and runtime; this avoids a recursive native-manifest/resource-seal self hash.
    """
    with tempfile.TemporaryDirectory(prefix='m8f-code-inventory-',dir='/private/tmp') as work:
        copy=Path(work)/'native-code';shutil.copyfile(path,copy)
        subprocess.run(['/usr/bin/codesign','--remove-signature',str(copy)],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return digest(copy.read_bytes())


def bundle_files(bundle):
    """Record regular-file bytes and contained symlinks, excluding the outer seal."""
    bundle = Path(bundle)
    files, links = {}, {}
    for p in sorted(bundle.rglob('*')):
        name = p.relative_to(bundle).as_posix()
        if name == 'Contents/Resources/native-manifest.json' or name.startswith('Contents/_CodeSignature/'):
            continue
        if p.is_symlink():
            if not p.resolve().is_relative_to(bundle.resolve()):
                raise SafeError('NATIVE_MANIFEST_INVALID')
            links[name] = os.readlink(p)
        elif p.is_file():
            files[name] = native_code_hash(p) if name == 'Contents/MacOS/PersonalCompanion' else digest(p.read_bytes())
    return files, links


def validate_bundle(bundle):
    bundle = Path(bundle).resolve()
    m = r.read_json(bundle/'Contents/Resources/native-manifest.json')
    if (m.get('format') != 1 or m.get('product') != PRODUCT or m.get('arch') != 'arm64'
            or m.get('production_updates') != 'DISABLED' or type(m.get('build')) is not int
            or m.get('build', 0) < 1 or m.get('profile') not in {'LOCAL_TEST', 'DEVELOPMENT'}):
        raise SafeError('NATIVE_MANIFEST_INVALID')
    files, links = bundle_files(bundle)
    if files != m.get('files') or links != m.get('symlinks') or r.identity(m) != m.get('manifest_hash'):
        raise SafeError('NATIVE_MANIFEST_INVALID')
    payload = bundle/'Contents/Resources/payload'
    pm = r.validate_package(payload, m['payload_manifest_hash'])
    if pm['git_commit'] != m['source_sha']:
        raise SafeError('NATIVE_MANIFEST_INVALID')
    return m


class BundledWhisper:
    """Use the accepted bounded transcriber with pinned relocated assets."""
    def __new__(cls, bundle, private):
        from .whisper_local_asr import WhisperLocalASR
        m = validate_bundle(bundle)
        root = Path(bundle)/'Contents/Resources/asr'
        receipt = r.read_json(root/'bundle-receipt.json')
        original = r.read_json(root/'M7C_ASR_MODEL_RECEIPT.json')
        if (m['asr'] != receipt or receipt['engine_original_sha256'] !=
                '54d1e7bf2e36ec29bdf70b87a45e26158396d5004909d16d5ad76e51920b566c'
                or original.get('model_checksum_verified') is not True
                or receipt['model_sha256'] != '1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b'):
            raise SafeError('LOCAL_ASR_MODEL_INTEGRITY')
        engine = WhisperLocalASR.__new__(WhisperLocalASR)
        engine.private_scope = private
        engine.root = root
        engine.binary = root/'build-v1.9.4-cpu/bin/whisper-cli'
        engine.model = root/'models/ggml-small.bin'
        engine.sandbox = Path('/usr/bin/sandbox-exec')
        engine.executions = 0
        engine.last_spec = None
        engine.version = '1.9.4-dev'
        engine.binary_hash = receipt['engine_sha256']
        engine.model_hash = receipt['model_sha256']
        if not engine.sandbox.is_file():
            raise SafeError('LOCAL_ASR_ISOLATION_UNAVAILABLE')
        engine.validate()
        return engine


class NativeSession:
    def __init__(self, bundle, base):
        self.bundle = Path(bundle).resolve()
        self.native = validate_bundle(self.bundle)
        self.package = self.bundle/'Contents/Resources/payload'
        self.manifest = r.read_json(self.package/'release-manifest.json')
        self.base = safe_path(base)
        self.kind = RootKind.PRIVATE_LOCAL
        self.settings = None
        self.fresh_setup = False
        self.server = self.thread = self.application = None
        self.data_lock = self.instance = None
        self.port = None
        if self.base.exists():
            self._open()

    def _open(self):
        from .local_private import owner_only
        owner_only(self.base)
        if not (self.base/'native-managed.json').exists() and (self.base/'native-initializing.json').is_file():
            marker=r.read_json(self.base/'native-initializing.json')
            names={p.name for p in self.base.iterdir()}
            if (marker!={'format':1,'root_kind':'PRIVATE_LOCAL','empty_setup_only':True}
                    or names-{'native-initializing.json','native-instance.lock','backups'}
                    or ((self.base/'backups').exists() and any((self.base/'backups').iterdir()))):
                raise SafeError('NATIVE_ROOT_INVALID')
            self.fresh_setup=True;self._instance_lock();return
        s = r.read_json(self.base/'native-managed.json')
        if set(s) != {'format', 'root_kind', 'active_app', 'active_data', 'highwater'} or s['format'] != 1:
            raise SafeError('NATIVE_ROOT_INVALID')
        self.kind = RootKind(s['root_kind'])
        # LOCAL_TEST exercises a distinct PRIVATE_LOCAL root with original synthetic
        # records, preserving the actual FileVault/permissions path.
        if self.kind != RootKind.PRIVATE_LOCAL:
            raise SafeError('NATIVE_ROOT_INVALID')
        for key in ('active_app', 'active_data'):
            if not isinstance(s[key], str) or '/' in s[key] or s[key] in {'', '.', '..'}:
                raise SafeError('NATIVE_ROOT_INVALID')
        if type(s['highwater']) is not int or s['highwater'] < 1:
            raise SafeError('NATIVE_ROOT_INVALID')
        if self.native['build'] < s['highwater']:
            # A preserved code bundle can open after a failed install only if no
            # successful higher-version activation was committed.
            raise SafeError('UPDATE_IDENTITY_INVALID')
        self.settings = s
        self.app, self.data = self.base/s['active_app'], self.base/s['active_data']
        self._instance_lock()
        r.selected(self.app, self.data, self.kind)

    def _instance_lock(self):
        if self.instance is not None:
            return
        fd = os.open(self.base/'native-instance.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        self.instance = os.fdopen(fd, 'r+')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.instance.close(); self.instance = None
            raise SafeError('ALREADY_RUNNING') from None

    def initialize(self, consent=False, no_cloud=False):
        if consent is not True or no_cloud is not True:
            raise SafeError('NATIVE_CONSENT_REQUIRED')
        if self.settings is not None or (self.base.exists() and not self.fresh_setup):
            raise SafeError('NATIVE_ROOT_INVALID')
        from .local_private import CONSENT, require_volume, owner_only
        parent = self.base.parent
        if not parent.is_dir():
            raise SafeError('NATIVE_ROOT_INVALID')
        # Check only this explicitly created, empty managed container. Passing
        # shared Application Support/the test home to safe_path would traverse
        # unrelated siblings and legitimate installed-code symlinks.
        if not self.base.exists():
            self.base.mkdir(mode=0o700)
            durable_write(self.base/'native-initializing.json',encode({
                'format':1,'root_kind':'PRIVATE_LOCAL','empty_setup_only':True}).encode())
        self._instance_lock()
        require_volume(self.base)
        backups = self.base/'backups'
        if not backups.exists():backups.mkdir(mode=0o700)
        self.app, self.data = self.base/'runtime', self.base/'vault'
        try:
            r.initialize_private(self.package, self.manifest['manifest_hash'], self.app, self.data,
                backups, 'INITIALIZE_PRIVATE_LOCAL:'+str(self.data), CONSENT, True, port=self._free_port())
            self.settings = {'format':1, 'root_kind':'PRIVATE_LOCAL', 'active_app':'runtime',
                             'active_data':'vault', 'highwater':self.native['build']}
            self._save_settings()
            (self.base/'native-initializing.json').unlink();fsync_dir(self.base)
            self.fresh_setup=False
            owner_only(self.base)
        except BaseException:
            # No existing root is deleted or permissions repaired. A failed fresh
            # setup is recoverable evidence and requires selecting a new container.
            raise
        return {'initialized':True, 'empty':True, 'provider_calls':0}

    def _save_settings(self):
        durable_write(self.base/'native-managed.json', encode(self.settings).encode())

    @staticmethod
    def _free_port():
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    def _pending_upgrade(self):
        _, active = r.selected(self.app, self.data, self.kind)
        if active['manifest_hash'] == self.manifest['manifest_hash'] and self.native['build'] == self.settings['highwater']:
            return
        pending = r.read_json(self.base/'native-update.json')
        if (pending.get('source_manifest') != active['manifest_hash']
                or pending.get('target_source') != self.native['source_sha']
                or pending.get('target_build') != self.native['build']
                or pending.get('target_manifest') != self.native['manifest_hash']):
            raise SafeError('UPDATE_RECOVERY_REQUIRED')
        if self.manifest['schema_version'] != active['schema_version']:
            raise SafeError('UPDATE_MIGRATION_PLAN_REQUIRED')
        # Accepted migration is executed only under its existing lock/provenance
        # manager. Native pre-install proof has already restored a copy.
        if active['manifest_hash'] != self.manifest['manifest_hash']:
            target = self.base/'backups'/('activation-'+str(uuid4()))
            r.upgrade(self.package, self.manifest['manifest_hash'], self.app, self.data, target,
                      root_kind=self.kind, port=self._free_port())
        self.settings['highwater'] = self.native['build']; self._save_settings()
        (self.base/'native-update.json').unlink(); fsync_dir(self.base)

    def start(self):
        if self.settings is None:
            raise SafeError('NATIVE_INITIALIZATION_REQUIRED')
        if self.server is not None:
            return self.status()
        self._pending_upgrade()
        self.port = self._free_port()
        r.lifecycle_preflight(self.package, self.manifest['manifest_hash'], self.app, self.data, self.kind, self.port)
        if (self.app/'upgrade-pending.json').exists():
            raise SafeError('UPGRADE_RECOVERY_REQUIRED')
        self.data_lock = r.operation_lock(self.data); self.data_lock.__enter__()
        try:
            from .network import deny_egress
            from .api import create_app
            import uvicorn
            deny_egress()
            factory = (lambda: BundledWhisper(self.bundle, True)) if self.native['asr'] else None
            self.application = create_app(self.data, port=self.port, web=self.package/'apps/web/dist',
                root_kind=self.kind, release_identity=self.native['source_sha'], m8d_private=True,
                private_provider_factory=None, private_asr_factory=factory, conversation_timeout=120)
            self.server = uvicorn.Server(uvicorn.Config(self.application, host='127.0.0.1', port=self.port,
                                       access_log=False, log_level='critical'))
            self.thread = threading.Thread(target=self.server.run, daemon=False); self.thread.start()
            deadline = time.monotonic()+15
            while not self.server.started:
                if not self.thread.is_alive() or time.monotonic()>deadline:
                    raise SafeError('NATIVE_OPERATION_FAILED')
                time.sleep(.02)
        except BaseException:
            self.stop(); raise
        return self.status()

    def status(self):
        return {'initialized':self.settings is not None, 'running':self.server is not None,
                'port':self.port if self.server else None, 'build':self.native['build'],
                'source_sha':self.native['source_sha'], 'asr':'BUNDLED_LOCAL' if self.native['asr'] else 'ASR_BUNDLE_BLOCKED',
                'ai':'AI_UNAVAILABLE', 'provider_calls':0, 'production_updates':'DISABLED'}

    def unlock(self):
        if self.application is None:
            raise SafeError('LOCKED')
        auth = self.application.state.auth
        with auth.lock:
            # Native reauthorization creates one fresh bounded code without
            # reviving expired sessions or resetting rate limiting.
            auth.code = secrets.token_urlsafe(18); auth.code_until = auth.clock()+300
            return {'code':auth.code, 'port':self.port, 'source_sha':self.native['source_sha']}

    def lock(self):
        if self.application is not None:
            self.application.state.auth.sessions.clear()
            self.application.state.private_gate.disable()
        return {'locked':True}

    def stop(self):
        if self.server is not None:
            self.lock()
            # Cancel local work before waiting for the server thread.
            for event in list(self.application.state.voice.cancel_events.values()):
                event.set()
            deadline=time.monotonic()+10
            while self.application.state.voice.cancel_events and time.monotonic()<deadline:
                time.sleep(.02)
            if self.application.state.voice.cancel_events:
                raise SafeError('NATIVE_OPERATION_FAILED')
            self.server.should_exit = True
            self.thread.join(15)
            if self.thread.is_alive():
                raise SafeError('NATIVE_OPERATION_FAILED')
            self.server = self.thread = self.application = None
        if self.data_lock is not None:
            self.data_lock.__exit__(None, None, None); self.data_lock = None
        return {'stopped':True}

    def backup(self):
        self.stop()
        target = self.base/'backups'/('manual-'+str(uuid4()))
        result = r.backup(self.app, self.data, target, self.kind)
        return {'backup':target.name, 'manifest_hash':result['backup_manifest_hash']}

    def restore_copy(self, backup, producer_hash, backup_hash):
        from .local_private import CONSENT
        target_app = self.base/('recovery-runtime-'+str(uuid4()))
        target_data = self.base/('recovery-vault-'+str(uuid4()))
        r.restore(self.package, self.manifest['manifest_hash'], backup, target_app, target_data,
            expected_producer_hash=producer_hash, expected_backup_hash=backup_hash,
            root_kind=self.kind, backup_directory=self.base/'backups',
            confirmation='INITIALIZE_PRIVATE_LOCAL:'+str(target_data), consent=CONSENT,
            acknowledge_no_cloud=True, port=self._free_port())
        return target_app, target_data

    def prepare_update(self, target):
        if self.native['profile'] != 'LOCAL_TEST' or self.settings is None:
            raise SafeError('UPDATE_IDENTITY_INVALID')
        required = {'product','channel','arch','build','source_sha','manifest_hash','schema'}
        if (set(target) != required or target['product'] != PRODUCT or target['channel'] != CHANNEL
                or target['arch'] != 'arm64' or type(target['build']) is not int
                or target['build'] <= max(self.native['build'], self.settings['highwater'])
                or target['schema'] != self.manifest['schema_version']):
            raise SafeError('UPDATE_IDENTITY_INVALID')
        import re
        if not re.fullmatch('[0-9a-f]{40}', target['source_sha']) or not re.fullmatch('[0-9a-f]{64}', target['manifest_hash']):
            raise SafeError('UPDATE_IDENTITY_INVALID')
        size = sum(p.stat().st_size for p in self.bundle.rglob('*') if p.is_file())
        if shutil.disk_usage(self.base).free < 3*size+128*1024**2:
            raise SafeError('UPDATE_SPACE_REQUIRED')
        self.stop()
        target_backup = self.base/'backups'/('pre-update-'+str(uuid4()))
        result = r.backup(self.app, self.data, target_backup, self.kind)
        # Real SQLite/attachments restore into a fresh copy, not a checksum-only claim.
        restored_app, restored_data = self.restore_copy(target_backup,
            self.manifest['manifest_hash'], result['backup_manifest_hash'])
        r.inspect_data(restored_data, self.kind)
        # Signed versioned frameworks contain legitimate contained symlinks.
        # Keep code outside the private managed data container so existing
        # safe_path/private-root no-symlink policy remains unchanged.
        recovery_dir=self.base.with_name(self.base.name+'-code-recovery')
        if not recovery_dir.exists():recovery_dir.mkdir(mode=0o700)
        if recovery_dir.is_symlink() or recovery_dir.stat().st_uid!=os.getuid() or recovery_dir.stat().st_mode & 0o777!=0o700:
            raise SafeError('NATIVE_ROOT_INVALID')
        if set(p.name for p in recovery_dir.iterdir())-{'previous-code.app'}:
            raise SafeError('NATIVE_ROOT_INVALID')
        recovery = recovery_dir/'previous-code.app'
        if recovery.exists():
            validate_bundle(recovery)
            shutil.rmtree(recovery)  # Only this app's previously verified managed code.
        shutil.copytree(self.bundle, recovery, symlinks=True)
        validate_bundle(recovery)
        pending = {'source_manifest':self.manifest['manifest_hash'],
            'target_source':target['source_sha'], 'target_build':target['build'],
            'target_manifest':target['manifest_hash'], 'backup':target_backup.name,
            'backup_manifest':result['backup_manifest_hash'], 'restore_verified':True}
        durable_write(self.base/'native-update.json', encode(pending).encode())
        return {'prepared':True, 'backup_verified':True, 'restore_copy_verified':True,
                'code_recovery_available':True}

    def restore(self, name, confirmation=False):
        if confirmation is not True or not isinstance(name, str) or '/' in name or name in {'','.', '..'}:
            raise SafeError('NATIVE_CONSENT_REQUIRED')
        self.stop()
        backup = self.base/'backups'/name
        meta = r.verify_backup(backup)
        producer = meta['release_provenance']['producing_manifest']['manifest_hash']
        app, data = self.restore_copy(backup, producer, digest((backup/'manifest.json').read_bytes()))
        self.settings.update(active_app=app.name, active_data=data.name)
        self._save_settings()
        self.app, self.data = app, data
        return {'restored':True, 'old_data_preserved':True, 'new_identity':True}

    def close(self):
        self.stop()
        if self.instance is not None:
            self.instance.close(); self.instance = None


def main():
    session = None
    try:
        for raw in iter(lambda: sys.stdin.buffer.readline(32769), b''):
            if len(raw)>32768 or not raw.endswith(b'\n'):
                break
            request_id = None
            try:
                command = json.loads(raw); request_id = command.get('id')
                op = command['op']
                if session is None:
                    if op != 'bootstrap': raise SafeError('NATIVE_ROOT_INVALID')
                    session = NativeSession(command['bundle'], command['base'])
                    result = session.status()
                elif op == 'initialize': result = session.initialize(command.get('consent'), command.get('no_cloud'))
                elif op == 'start': result = session.start()
                elif op == 'status': result = session.status()
                elif op == 'unlock': result = session.unlock()
                elif op == 'lock': result = session.lock()
                elif op == 'stop': result = session.stop()
                elif op == 'backup': result = session.backup()
                elif op == 'prepare-update': result = session.prepare_update(command['target'])
                elif op == 'restore': result = session.restore(command['name'], command.get('confirmation'))
                elif op == 'quit': break
                else: raise SafeError('NATIVE_OPERATION_FAILED')
                reply = {'id':request_id, 'ok':True, 'result':result}
            except Exception as error:
                code = error.code if isinstance(error, SafeError) and error.code in ERRORS else 'NATIVE_OPERATION_FAILED'
                reply = {'id':request_id, 'ok':False, 'code':code}
            sys.stdout.write(encode(reply)+'\n'); sys.stdout.flush()
    finally:
        if session is not None:
            session.close()


if __name__ == '__main__':
    main()
