"""Native managed-root mechanisms, deterministic ORIGINAL SYNTHETIC fixtures.
Actual bundle/Sparkle/LaunchServices checks are separate exact-C Mac receipts.
"""
import json
import shutil
from pathlib import Path
import pytest
from apps.core import native_macos as n, release as r
from apps.core.storage import SafeError, encode, digest, Store
from apps.core.domain import Journal
from apps.core.root_types import RootKind
from test_m1_domain import isolated, create
from test_m8a_release import package
from test_m8b_readiness import runtime_package
from test_m8c_private import private_package, protected
from test_m8d_private import private_ai_package


@pytest.fixture
def native(private_ai_package, isolated, protected, monkeypatch):
    pkg, _ = private_ai_package
    bundle = isolated/'ORIGINAL SYNTHETIC.app'
    destination = bundle/'Contents/Resources/payload'
    destination.parent.mkdir(parents=True);shutil.copytree(pkg,destination)
    pm=r.read_json(destination/'release-manifest.json')
    meta={'format':1,'product':n.PRODUCT,'arch':'arm64','build':101,'source_sha':pm['git_commit'],
          'profile':'LOCAL_TEST','production_updates':'DISABLED','payload_manifest_hash':pm['manifest_hash'],'asr':None}
    meta['files'],meta['symlinks']=n.bundle_files(bundle);meta['manifest_hash']=r.identity(meta)
    (bundle/'Contents/Resources/native-manifest.json').write_text(encode(meta))
    session=n.NativeSession(bundle,isolated/'Standalone')
    yield session
    session.close()


def target(session, **changes):
    return dict({'product':n.PRODUCT,'channel':n.CHANNEL,'arch':'arm64','build':102,
                 'source_sha':session.native['source_sha'],'manifest_hash':'b'*64,'schema':11},**changes)


def test_first_run_needs_exact_consent_and_never_reinitializes(native):
    assert not native.base.exists() and not native.status()['initialized']
    for args in [(False,True),(True,False),(1,True)]:
        with pytest.raises(SafeError,match='CONSENT_REQUIRED'):native.initialize(*args)
        assert not native.base.exists()
    native.initialize(True,True)
    assert Journal(Store(native.data,root_kind=RootKind.PRIVATE_LOCAL)).list()['items']==[]
    with pytest.raises(SafeError,match='ROOT_INVALID'):native.initialize(True,True)


def test_root_unknown_and_existing_permissions_are_not_repaired(native):
    native.base.mkdir(mode=0o755)
    native.base.chmod(0o755)  # Process umask may already be 077 after other private fixtures.
    (native.base/'ORIGINAL_SYNTHETIC_UNKNOWN.txt').write_text('ORIGINAL SYNTHETIC')
    with pytest.raises(SafeError,match='PERMISSIONS_REQUIRED'):n.NativeSession(native.bundle,native.base)
    assert native.base.stat().st_mode & 0o777 == 0o755


def test_initialization_never_scans_application_support_siblings(native):
    sibling=native.base.parent/'OTHER_ORIGINAL_SYNTHETIC_APP';sibling.mkdir()
    (sibling/'legitimate-code-link').symlink_to(native.bundle)
    native.initialize(True,True)
    assert r.inspect_data(native.data,RootKind.PRIVATE_LOCAL)==11


def test_empty_failed_volume_setup_can_retry_with_new_explicit_consent(native,monkeypatch):
    from apps.core import local_private as p
    monkeypatch.setattr(p,'volume_protection',lambda _: 'SECURITY_REQUIREMENT_NOT_MET')
    with pytest.raises(SafeError,match='VOLUME_PROTECTION_REQUIRED'):native.initialize(True,True)
    assert not (native.base/'vault').exists()
    native.close()
    reopened=n.NativeSession(native.bundle,native.base)
    try:
        with pytest.raises(SafeError,match='CONSENT_REQUIRED'):reopened.initialize(False,True)
        monkeypatch.setattr(p,'volume_protection',lambda _: 'PASS')
        reopened.initialize(True,True)
        assert reopened.status()['initialized']
    finally:reopened.close()


@pytest.mark.parametrize('change',[{'product':'other'},{'channel':'production'},{'arch':'x86_64'},
    {'build':100},{'build':101},{'build':True},{'schema':12},{'source_sha':'moving-main'},
    {'manifest_hash':'unknown'}])
def test_wrong_update_identity_downgrade_replay_fail_before_backup(native,change):
    native.initialize(True,True)
    with pytest.raises(SafeError,match='UPDATE_IDENTITY_INVALID'):native.prepare_update(target(native,**change))
    assert not list((native.base/'backups').iterdir())
    assert not (native.base/'native-update.json').exists()


def test_disk_full_is_refused_before_quiescence(native,monkeypatch):
    native.initialize(True,True)
    monkeypatch.setattr(n.shutil,'disk_usage',lambda _:shutil._ntuple_diskusage(1,1,0))
    with pytest.raises(SafeError,match='SPACE_REQUIRED'):native.prepare_update(target(native))
    assert not list((native.base/'backups').iterdir())


def test_real_backup_restore_copy_precedes_update_and_preserves_data(native):
    native.initialize(True,True)
    journal=Journal(Store(native.data,root_kind=RootKind.PRIVATE_LOCAL))
    req,_=create(journal,text='ORIGINAL SYNTHETIC M8F note')
    original_id=r.read_json(native.data/'private-local.json')['root_id']
    result=native.prepare_update(target(native))
    assert result['restore_copy_verified'] and result['backup_verified']
    assert journal.get(str(req.entry_id))['raw_text']=='ORIGINAL SYNTHETIC M8F note'
    assert r.read_json(native.data/'private-local.json')['root_id']==original_id
    pending=r.read_json(native.base/'native-update.json')
    assert pending['restore_verified']
    r.verify_backup(native.base/'backups'/pending['backup'],native.manifest['manifest_hash'],pending['backup_manifest'])
    assert n.validate_bundle(native.base.with_name(native.base.name+'-code-recovery')/'previous-code.app')['build']==101
    # Code's contained framework links never enter the private managed root.
    native.close();reopened=n.NativeSession(native.bundle,native.base);reopened.close()


def test_restore_requires_consent_keeps_prior_root_and_renews_identity(native):
    native.initialize(True,True)
    create(Journal(Store(native.data,root_kind=RootKind.PRIVATE_LOCAL)),text='ORIGINAL SYNTHETIC restore')
    old_data=native.data;old_id=r.read_json(old_data/'private-local.json')['root_id']
    saved=native.backup()
    with pytest.raises(SafeError,match='CONSENT_REQUIRED'):native.restore(saved['backup'],False)
    native.restore(saved['backup'],True)
    current=r.read_json(native.base/'native-managed.json')
    assert old_data.is_dir() and current['active_data']!=old_data.name
    assert r.read_json(native.base/current['active_data']/'private-local.json')['root_id']!=old_id


def test_interrupted_preparation_never_commits_pending_target(native,monkeypatch):
    native.initialize(True,True)
    def fail(*args):raise OSError('ORIGINAL SYNTHETIC DISK FULL')
    monkeypatch.setattr(native,'restore_copy',fail)
    with pytest.raises(OSError):native.prepare_update(target(native))
    assert not (native.base/'native-update.json').exists()
    assert r.inspect_data(native.data,RootKind.PRIVATE_LOCAL)==11
    assert list((native.base/'backups').iterdir())


def test_bundle_file_tamper_and_escaping_symlink_refused(native):
    original=native.bundle/'Contents/Resources/payload/launch.py'
    original.write_text('ORIGINAL SYNTHETIC tampered')
    with pytest.raises(SafeError,match='MANIFEST_INVALID'):n.validate_bundle(native.bundle)
    (native.bundle/'escape').symlink_to('/etc')
    with pytest.raises(SafeError,match='MANIFEST_INVALID'):n.bundle_files(native.bundle)


def test_concurrent_native_instance_fails_without_writer_changes(native):
    native.initialize(True,True)
    with pytest.raises(SafeError,match='ALREADY_RUNNING'):n.NativeSession(native.bundle,native.base)
    assert r.inspect_data(native.data,RootKind.PRIVATE_LOCAL)==11
