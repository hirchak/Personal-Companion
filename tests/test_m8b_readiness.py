"""Synthetic release/runtime/provenance guards. Real Mac dry-run is separately bound to final C."""
import json
import sqlite3
import shutil
from pathlib import Path
import pytest
from pydantic import ValidationError
from apps.core import release as r
from apps.core.storage import Store,SafeError,REPO,encode,digest
from apps.core.pilot_readiness import PROFILE,validate_profile,MacPreflight,readiness,reference_mac_preflight
from test_m1_domain import isolated
from test_m8a_release import package,paths,domains,assert_domains

@pytest.fixture
def runtime_package(package):
    p,_=package
    for name in ('requirements.runtime.lock','packages/pilot/MAC_CORE_PROFILE.json'):
        target=p/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
    m=r.read_json(p/'release-manifest.json');m['format']=2;m['release_id']='M8B-'+m['git_commit']
    m['runtime_input_hash']=digest((p/'requirements.runtime.lock').read_bytes());m['platform']['dependencies']='EXACT_RUNTIME_LOCK'
    m['files']=r.file_hashes(p);m['manifest_hash']=r.identity(m);(p/'release-manifest.json').write_text(encode(m))
    return p,m['manifest_hash']


def test_release_backup_binds_exact_producer_and_snapshot(runtime_package,isolated):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    target=isolated/'bound backup';receipt=r.backup(app,data,target)
    m=r.verify_backup(target,h,receipt['backup_manifest_hash'])
    assert m['backup_format']==3 and m['app_version']=='M8B-'+'a'*40
    value=m['release_provenance'];assert value['producing_manifest']['manifest_hash']==h
    assert value['snapshot_schema']==11 and value['created_at_utc']==m['created_at_utc']
    assert value['source_release']['manifest_hash']==h
    with sqlite3.connect(target/'snapshot.sqlite3') as c:assert c.execute('SELECT payload FROM release_backup_provenance').fetchone()[0]==encode(value)
    r.restore(p,h,target,isolated/'restored app',isolated/'restored data',expected_backup_hash=receipt['backup_manifest_hash'])
    assert_domains(isolated/'restored data',ids)
    with sqlite3.connect(isolated/'restored data/journal.sqlite3') as c:assert not c.execute("SELECT 1 FROM sqlite_master WHERE name='release_backup_provenance'").fetchone()

@pytest.mark.parametrize('change',['release_id','git_commit','manifest_hash','schema','timestamp','format','source','missing','legacy_relabel','producer_rehashed'])
def test_provenance_tampering_fails_before_creating_roots(runtime_package,isolated,change):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data)
    target=isolated/'bound backup';r.backup(app,data,target);m=r.read_json(target/'manifest.json');v=m['release_provenance']
    if change in {'release_id','git_commit','manifest_hash'}:v['producing_manifest'][change]='0'*40 if change=='git_commit' else 'tampered'
    if change=='schema':v['snapshot_schema']=10
    if change=='timestamp':m['created_at_utc']='2099-01-01T00:00:00Z'
    if change=='format':m['backup_format']=2
    if change=='source':v['source_release']['manifest_hash']='0'*64
    if change=='missing':del m['release_provenance']
    if change=='legacy_relabel':m['app_version']='M7D'
    if change=='producer_rehashed':
        v['producing_manifest']['git_commit']='b'*40;v['producing_manifest']['release_id']='M8B-'+'b'*40;v['producing_manifest']['manifest_hash']=r.identity(v['producing_manifest'])
    (target/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError):r.restore(p,h,target,isolated/'reject app',isolated/'reject data')
    assert not (isolated/'reject app').exists() and not (isolated/'reject data').exists()


def test_wrong_producer_hash_and_optional_backup_trust_anchor(runtime_package,isolated):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data);target=isolated/'backup'
    receipt=r.backup(app,data,target)
    with pytest.raises(SafeError,match='BACKUP_RELEASE_PROVENANCE'):r.verify_backup(target,'0'*64)
    with pytest.raises(SafeError,match='BACKUP_MANIFEST_CHECKSUM'):r.verify_backup(target,h,'0'*64)
    assert r.verify_backup(target,h,receipt['backup_manifest_hash'])['backup_format']==3


def test_generic_historical_backup_not_retroactively_attributed(runtime_package,isolated):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data);ids=domains(data)
    legacy=isolated/'historical generic';Store(data).backup(legacy)
    m=r.read_json(legacy/'manifest.json');assert m['backup_format']==2 and m['app_version']=='M7D' and 'release_provenance' not in m
    with pytest.raises(SafeError,match='LEGACY_BACKUP_REQUIRES_EXPLICIT_APPROVAL'):r.restore(p,h,legacy,isolated/'blocked app',isolated/'blocked data')
    result=r.restore(p,h,legacy,isolated/'approved legacy app',isolated/'approved legacy data',allow_legacy=True)
    assert result['backup_provenance']=='LEGACY_UNKNOWN_PRODUCER';assert_domains(isolated/'approved legacy data',ids)
    Store.restore(legacy,isolated/'generic compatible restore');assert_domains(isolated/'generic compatible restore',ids)


def test_runtime_preflight_does_not_require_test_or_http_client_packages(runtime_package,monkeypatch,isolated):
    p,h=runtime_package;lookups=[];original=r.importlib.metadata.version
    def available(name):
        lookups.append(name)
        if name in {'pytest','playwright','httpx','greenlet','pyee','pluggy','iniconfig','packaging','httpcore','certifi'}:raise r.importlib.metadata.PackageNotFoundError(name)
        return original(name)
    monkeypatch.setattr(r.importlib.metadata,'version',available)
    result=r.preflight(p,h,*paths(isolated))
    assert result['status']=='PASS' and len(lookups)==12
    assert not {'pytest','playwright','httpx','greenlet','pyee','pluggy','iniconfig','packaging','httpcore','certifi'} & set(lookups)
    runtime=dict(line.split('==') for line in (p/'requirements.runtime.lock').read_text().splitlines())
    development=dict(line.split('==') for line in (p/'requirements.lock').read_text().splitlines())
    assert all(development[k]==v for k,v in runtime.items())


def test_runtime_identity_and_profile_tampering(runtime_package):
    p,h=runtime_package;assert r.validate_package(p,h)['runtime_input_hash']==digest((p/'requirements.runtime.lock').read_bytes())
    assert validate_profile(p/'packages/pilot/MAC_CORE_PROFILE.json')==PROFILE
    (p/'requirements.runtime.lock').write_text('pytest==8.3.5\n')
    with pytest.raises(SafeError,match='RELEASE_INTEGRITY'):r.validate_package(p,h)


def test_profile_inactive_and_optional_modules_do_not_block_core(runtime_package,isolated,isolated_preflight_port):
    p,h=runtime_package;report=reference_mac_preflight(p,h,*paths(isolated),port=isolated_preflight_port)
    assert report['scope']=='REAL_REFERENCE_MAC_SYNTHETIC_ONLY' and report['status']=='PASS'
    assert not any(k in encode(report).lower() for k in ('/users/','username','account','token','auth'))
    decision=readiness(report,True)
    assert decision['MAC_CORE_PILOT']=='NOT_READY' and decision['MAC_SYNTHETIC_DRY_RUN']=='READY' and decision['PHONE_PILOT']=='NEEDS_TRANSPORT_GATE'
    assert decision['actual_private_pilot']=='NOT_STARTED' and PROFILE['private_ai']=='OFF'
    assert decision['PRIVATE_AI']=='BLOCKED_M7C_N02' and PROFILE['health_to_ai']=='OFF' and PROFILE['clinical_self_help']=='OFF'
    assert readiness(report,False)['MAC_SYNTHETIC_DRY_RUN']=='NOT_READY'
    assert decision['blocking_core_gate']=='PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED'
    with pytest.raises(ValidationError):MacPreflight.model_validate(dict(report,username='ORIGINAL_SYNTHETIC_REJECTED'))
    with pytest.raises(ValidationError):MacPreflight.model_validate(dict(report,private_data_used=True))


def test_generic_format3_restore_also_checks_provenance(runtime_package,isolated):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data);target=isolated/'backup';r.backup(app,data,target)
    m=r.read_json(target/'manifest.json');m['release_provenance']['snapshot_schema']=10;(target/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='BACKUP_RELEASE_PROVENANCE'):Store.restore(target,isolated/'generic rejected')
    assert not (isolated/'generic rejected').exists()


def test_snapshot_attestation_missing_and_rehashed_receipt_are_rejected(runtime_package,isolated):
    p,h=runtime_package;app,data=paths(isolated);r.install(p,h,app,data);target=isolated/'backup';receipt=r.backup(app,data,target)
    m=r.read_json(target/'manifest.json')
    with sqlite3.connect(target/'snapshot.sqlite3') as c:c.execute('DROP TABLE release_backup_provenance')
    m['files']['snapshot.sqlite3']=digest((target/'snapshot.sqlite3').read_bytes());(target/'manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='BACKUP_RELEASE_PROVENANCE'):r.verify_backup(target,h)
    with pytest.raises(SafeError,match='BACKUP_MANIFEST_CHECKSUM'):r.verify_backup(target,h,receipt['backup_manifest_hash'])


def test_inactive_profile_cannot_enable_optional_capabilities_even_after_rehash(runtime_package):
    p,h=runtime_package;profile=r.read_json(p/'packages/pilot/MAC_CORE_PROFILE.json');profile['private_ai']='ON'
    (p/'packages/pilot/MAC_CORE_PROFILE.json').write_text(encode(profile))
    m=r.read_json(p/'release-manifest.json');m['files']=r.file_hashes(p);m['manifest_hash']=r.identity(m);(p/'release-manifest.json').write_text(encode(m))
    with pytest.raises(SafeError,match='PILOT_PROFILE_INCOMPATIBLE'):r.validate_package(p,m['manifest_hash'])
