"""Historical M8E source compatibility on disposable PRIVATE_LOCAL fixtures only."""
from pathlib import Path

import pytest

from apps.core import release as r
from apps.core.domain import Journal
from apps.core.local_private import validate_root
from apps.core.root_types import RootKind
from apps.core.storage import SafeError, Store, encode
from test_m1_domain import create, isolated
from test_m8a_release import package
from test_m8b_readiness import runtime_package
from test_m8c_private import private_package, protected
from test_m8d_private import private_ai_package, vault


def rewrite_profile(package: Path, **changes):
    path=package/'packages/pilot/MAC_PRIVATE_AI_VOICE_PROFILE.json'
    path.write_text(encode(dict(r.read_json(path),**changes)))
    manifest=r.read_json(package/'release-manifest.json')
    manifest['files']=r.file_hashes(package)
    manifest['manifest_hash']=r.identity(manifest)
    (package/'release-manifest.json').write_text(encode(manifest))
    return manifest


def historical_source(vault, **changes):
    _,_,app,data,_=vault
    source,_=r.selected(app,data,RootKind.PRIVATE_LOCAL)
    manifest=rewrite_profile(source,local_voice='EXPLICIT_OWNER_GATE_DEFAULT_OFF',**changes)
    r.activate(app,manifest)
    return source,manifest


def test_historical_source_upgrade_preserves_vault_and_verified_backup(vault):
    target,target_hash,app,data,backups=vault
    journal=Journal(Store(data,root_kind=RootKind.PRIVATE_LOCAL))
    entry,_=create(journal,text='ORIGINAL SYNTHETIC preserved across M8E voice-profile upgrade')
    root_before=validate_root(data)
    source,old=historical_source(vault)
    with pytest.raises(SafeError,match='PILOT_PROFILE_INCOMPATIBLE'):
        r.validate_package(source,old['manifest_hash'])
    assert r.selected(app,data,RootKind.PRIVATE_LOCAL)[1]['manifest_hash']==old['manifest_hash']
    # A distinct synthetic target release prevents reusing the old staged directory.
    new=r.read_json(target/'release-manifest.json')
    new.update(git_commit='b'*40,release_id='M8D-'+'b'*40)
    new['manifest_hash']=r.identity(new)
    (target/'release-manifest.json').write_text(encode(new))
    result=r.upgrade(target,new['manifest_hash'],app,data,backups/'ORIGINAL_SYNTHETIC_preupgrade',root_kind=RootKind.PRIVATE_LOCAL)
    assert result['status']=='PASS' and result['backup']=='VERIFIED'
    assert validate_root(data)==root_before
    assert journal.get(str(entry.entry_id))['raw_text']=='ORIGINAL SYNTHETIC preserved across M8E voice-profile upgrade'
    assert r.selected(app,data,RootKind.PRIVATE_LOCAL)[1]['manifest_hash']==new['manifest_hash']
    backup=r.read_json(backups/'ORIGINAL_SYNTHETIC_preupgrade/manifest.json')
    assert backup['release_provenance']['source_release']['manifest_hash']==old['manifest_hash']
    assert backup['release_provenance']['producing_manifest']['manifest_hash']==new['manifest_hash']


@pytest.mark.parametrize('changes',[
    {'local_voice':'UNRECOGNIZED_LOCAL_VOICE'},
    {'clinical_active':1},
    {'health':'ON'},
    {'provider_route':'UNAUTHORIZED_FALLBACK'},
])
def test_historical_source_unknown_profile_still_fails_closed(vault,changes):
    target,h,app,data,backups=vault
    if 'local_voice' in changes:
        source,_=r.selected(app,data,RootKind.PRIVATE_LOCAL)
        manifest=rewrite_profile(source,**changes);r.activate(app,manifest)
    else:
        historical_source(vault,**changes)
    with pytest.raises(SafeError,match='PILOT_PROFILE_INCOMPATIBLE'):
        r.upgrade(target,h,app,data,backups/'ORIGINAL_SYNTHETIC_refused',root_kind=RootKind.PRIVATE_LOCAL)
    assert not (backups/'ORIGINAL_SYNTHETIC_refused').exists()


def test_historical_source_file_integrity_remains_required(vault):
    source,_=historical_source(vault)
    (source/'apps/core/api.py').write_text('ORIGINAL SYNTHETIC tampering')
    _,_,app,data,_=vault
    with pytest.raises(SafeError,match='RELEASE_INTEGRITY'):
        r.selected(app,data,RootKind.PRIVATE_LOCAL)


def test_historical_profile_cannot_be_upgrade_target(vault):
    target,_,app,data,backups=vault
    old=rewrite_profile(target,local_voice='EXPLICIT_OWNER_GATE_DEFAULT_OFF')
    with pytest.raises(SafeError,match='PILOT_PROFILE_INCOMPATIBLE'):
        r.upgrade(target,old['manifest_hash'],app,data,backups/'ORIGINAL_SYNTHETIC_invalid_target',root_kind=RootKind.PRIVATE_LOCAL)
    assert not (backups/'ORIGINAL_SYNTHETIC_invalid_target').exists()
    assert not (app/'upgrade-pending.json').exists()
