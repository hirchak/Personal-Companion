"""Mac private core security gates. Native read-only probes, no custom cryptography."""
from __future__ import annotations
import json
import os
from pathlib import Path
import platform
import plistlib
import sqlite3
import stat
import subprocess
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .root_types import RootKind
from .storage import SafeError, safe_path, empty_target, encode, now

PROFILE = {
    'profile_id':'MAC_PRIVATE_LOCAL_CORE_V1','profile_version':1,
    'journal':'ON','creative':'ON','local_search':'ON','backup_restore':'ON','explicit_local_export':'ON',
    'private_ai':'OFF','conversation_inference':'OFF','specialists':'OFF','clinical_active':0,
    'health_to_ai':'OFF','health_bridge':'OFF','human_voice_asr':'OFF','cloud_asr':'NONE',
    'external_embeddings':'OFF','phone':'OFF','cloud_sync':'NONE','telemetry':'NONE','publication':'NONE',
    'automatic_external_sharing':'NONE','provider_fallback':'NONE',
}
POLICY = 'VERIFIED_FILEVAULT_VOLUME_OWNER_ONLY_NO_ARCHIVE_ENCRYPTION_V1'
CONSENT = 'I_AM_THE_DATA_OWNER_AND_CONSENT_TO_LOCAL_STORAGE_AND_PROTECTED_LOCAL_BACKUPS'
MARKER_NAME = 'private-local.json'
Status = Literal['PASS','OPTIONAL_UNAVAILABLE','NOT_RUN','BLOCKED_BY_PERMISSION','INCOMPATIBLE','SECURITY_REQUIREMENT_NOT_MET']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class RootReceipt(Strict):
    format: Literal[1]
    root_kind: Literal['PRIVATE_LOCAL']
    root_id: str
    profile_id: Literal['MAC_PRIVATE_LOCAL_CORE_V1']
    initialized_release_hash: str = Field(pattern='^[0-9a-f]{64}$')
    backup_directory: str
    backup_policy: Literal['VERIFIED_FILEVAULT_VOLUME_OWNER_ONLY_NO_ARCHIVE_ENCRYPTION_V1']
    data_owner_acknowledged: Literal[True]
    no_cloud_directory_acknowledged: Literal[True]
    created_at_utc: str

    @field_validator('root_id')
    @classmethod
    def valid_id(cls,value):
        UUID(value)
        return value

    @field_validator('created_at_utc')
    @classmethod
    def valid_time(cls,value):
        parsed=datetime.fromisoformat(value)
        if parsed.utcoffset()!=timezone.utc.utcoffset(parsed):raise ValueError('UTC required')
        return value

class SecurityCheck(Strict):
    gate: str
    status: Status

class PrivatePreflight(Strict):
    format: Literal[1]
    scope: Literal['PRIVATE_LOCAL_SECURITY_TESTED_MAC_ONLY']
    status: Status
    release_id: str
    manifest_hash: str = Field(pattern='^[0-9a-f]{64}$')
    runtime_input_hash: str = Field(pattern='^[0-9a-f]{64}$')
    os: str
    architecture: str
    python: str
    root_kind: Literal['PRIVATE_LOCAL']
    checks: list[SecurityCheck]
    storage_protection: Literal['VERIFIED_FILEVAULT_VOLUME','UNVERIFIED']
    backup_protection: Literal['VERIFIED_FILEVAULT_VOLUME','UNVERIFIED']
    application_level_database_encryption: Literal['NOT_IMPLEMENTED']
    application_level_backup_encryption: Literal['NOT_IMPLEMENTED']
    runtime_profile: dict

    @field_validator('runtime_profile')
    @classmethod
    def exact_profile(cls,value):
        if value!=PROFILE:raise ValueError('profile mismatch')
        return value

    @model_validator(mode='after')
    def consistent_security(self):
        gates={c.gate:c.status for c in self.checks}
        if len(gates)!=len(self.checks):raise ValueError('duplicate gate')
        required={'data_volume','backup_volume','application_owner_only_permissions','data_owner_only_permissions','backup_owner_only_permissions','writable_space','loopback','exact_release_and_private_profile','path_safety_app_data_separation','runtime_off_defaults','platform','python'}
        if not required<=gates.keys():raise ValueError('missing gate')
        if (self.storage_protection=='VERIFIED_FILEVAULT_VOLUME')!=(gates['data_volume']=='PASS'):raise ValueError('storage mismatch')
        if (self.backup_protection=='VERIFIED_FILEVAULT_VOLUME')!=(gates['backup_volume']=='PASS'):raise ValueError('backup mismatch')
        if self.status=='PASS' and (any(gates[k]!='PASS' for k in required) or self.os!='Darwin' or self.architecture!='arm64'):raise ValueError('invalid ready state')
        return self


def read_receipt(path):
    from .release import read_json
    try:
        value = read_json(path)
        receipt = RootReceipt.model_validate(value)
        UUID(receipt.root_id)
        return receipt.model_dump()
    except (ValueError, TypeError):
        raise SafeError('PRIVATE_ROOT_METADATA_INVALID') from None


def local_path(path):
    p = safe_path(path)
    denied = {'cloudstorage','mobile documents','dropbox','icloud','google drive','onedrive'}
    if any(part.casefold() in denied or part.casefold().startswith(('com~apple~clouddocs','dropbox (','onedrive -')) for part in p.parts):
        raise SafeError('CLOUD_PATH_DENIED')
    return p


def owner_only(path, *, tree=False):
    p = local_path(path)
    if not p.exists(): raise SafeError('PRIVATE_PATH_REQUIRED')
    items = [p, *p.rglob('*')] if tree and p.is_dir() else [p]
    for item in items:
        s = item.stat()
        expected = 0o700 if item.is_dir() else 0o600
        if s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != expected:
            raise SafeError('OWNER_ONLY_PERMISSIONS_REQUIRED')
        # POSIX mode alone does not rule out extended macOS ACL grants.
        if platform.system() == 'Darwin':
            result = subprocess.run(['/bin/ls','-lde',str(item)],capture_output=True,timeout=5)
            if result.returncode: raise SafeError('PERMISSION_CHECK_UNAVAILABLE')
            if len(result.stdout.splitlines()) != 1: raise SafeError('EXTENDED_ACL_DENIED')
    return p


def volume_protection(path):
    """Match the supplied existing directory to its actual mount/device. Never emit plist IDs/paths."""
    if platform.system() != 'Darwin': return 'INCOMPATIBLE'
    try:
        p = local_path(path)
        if not p.exists(): p = p.parent
        device = p.stat().st_dev
        mount = p
        while mount.parent != mount and mount.parent.stat().st_dev == device:
            mount = mount.parent
        # APFS firmlinks place /private and /Users on Data without an ordinary mount boundary.
        data_mount = Path('/System/Volumes/Data')
        if data_mount.is_dir() and data_mount.stat().st_dev == device: mount = data_mount
        result = subprocess.run(['/usr/sbin/diskutil','info','-plist',str(mount)],capture_output=True,timeout=10)
        if result.returncode: return 'BLOCKED_BY_PERMISSION'
        value = plistlib.loads(result.stdout)
        # Hardware encryption without credential-bound FileVault is insufficient.
        protected = value.get('FileVault') is True and value.get('Encryption') is True and value.get('EncryptionThisVolumeProper') is True
        local_apfs = value.get('FilesystemType') == 'apfs'
        return 'PASS' if protected and local_apfs else 'SECURITY_REQUIREMENT_NOT_MET'
    except (OSError, ValueError, subprocess.SubprocessError):
        return 'BLOCKED_BY_PERMISSION'


def require_volume(path):
    status = volume_protection(path)
    if status != 'PASS': raise SafeError('BLOCKED_BY_PERMISSION' if status == 'BLOCKED_BY_PERMISSION' else 'VOLUME_PROTECTION_REQUIRED')


def validate_root(root, *, security=False):
    p = owner_only(root, tree=True)
    if (p/'synthetic.json').exists(): raise SafeError('ROOT_KIND_MISMATCH')
    value = read_receipt(p/MARKER_NAME)
    try:
        with sqlite3.connect((p/'journal.sqlite3').as_uri()+'?mode=ro', uri=True) as c:
            rows = c.execute('SELECT payload FROM private_root_identity').fetchall()
            if len(rows) != 1 or rows[0][0] != encode(value): raise SafeError('PRIVATE_ROOT_IDENTITY_MISMATCH')
    except sqlite3.Error: raise SafeError('PRIVATE_ROOT_IDENTITY_MISMATCH') from None
    if security:
        require_volume(p)
        owner_only(value['backup_directory'])
        require_volume(value['backup_directory'])
    return value


def activation_receipt(data, release_hash, backup_directory, confirmation, consent, acknowledge_no_cloud):
    p = local_path(data)
    if confirmation != 'INITIALIZE_PRIVATE_LOCAL:'+str(p) or consent != CONSENT or acknowledge_no_cloud is not True:
        raise SafeError('EXPLICIT_PRIVATE_INITIALIZATION_AND_CONSENT_REQUIRED')
    empty_target(p)
    owner_only(p if p.exists() else p.parent)
    require_volume(p)
    b = owner_only(backup_directory)
    if not b.is_dir(): raise SafeError('BACKUP_DIRECTORY_REQUIRED')
    if b == p or b.is_relative_to(p) or p.is_relative_to(b): raise SafeError('BACKUP_PATH_OVERLAP')
    require_volume(b)
    return RootReceipt(format=1, root_kind='PRIVATE_LOCAL', root_id=str(uuid4()), profile_id=PROFILE['profile_id'],
        initialized_release_hash=release_hash, backup_directory=str(b), backup_policy=POLICY,
        data_owner_acknowledged=True, no_cloud_directory_acknowledged=True, created_at_utc=now()).model_dump()


def backup_gate(root, target):
    receipt = validate_root(root, security=True)
    p = local_path(target); directory = owner_only(receipt['backup_directory'])
    if p.parent != directory: raise SafeError('EXPLICIT_BACKUP_DIRECTORY_REQUIRED')
    empty_target(p)
    if p.exists(): raise SafeError('TARGET_MUST_BE_NEW')
    require_volume(directory)
    return receipt


def preflight(package, expected_hash, app, data, backup_directory, port=8765):
    from . import release as r
    package=r.package_path(package); app,data=r.separated(app,data)
    m=r.validate_package(package,expected_hash)
    if m['format'] != 3: raise SafeError('PRIVATE_RELEASE_REQUIRED')
    for p in (app,data,local_path(backup_directory)):
        if p == package or p.is_relative_to(package) or package.is_relative_to(p): raise SafeError('PACKAGE_PATH_OVERLAP')
    b=local_path(backup_directory)
    if any(b==p or b.is_relative_to(p) or p.is_relative_to(b) for p in (app,data)):raise SafeError('BACKUP_PATH_OVERLAP')
    if data.exists() and any(data.iterdir()):
        value=validate_root(data)
        if value['backup_directory']!=str(b):raise SafeError('BACKUP_DIRECTORY_MISMATCH')
        r.inspect_data(data,RootKind.PRIVATE_LOCAL)
    if app.exists():
        r.selected(app,data,RootKind.PRIVATE_LOCAL)
    checks=[{'gate':c['gate'],'status':c['status']} for c in r.runtime_checks(package)]
    for label,p in [('application',app),('data',data),('backup',b)]:
        owner_only(p if p.exists() else p.parent)
        checks.append({'gate':label+'_owner_only_permissions','status':'PASS'})
    data_volume=volume_protection(data); backup_volume=volume_protection(b)
    for label,status in [('data_volume',data_volume),('backup_volume',backup_volume)]:checks.append({'gate':label,'status':status})
    import shutil,socket
    checks.append({'gate':'writable_space','status':'PASS' if all(os.access(p if p.exists() else p.parent,os.W_OK) and shutil.disk_usage(p if p.exists() else p.parent).free>=32*1024*1024 for p in (app,data,b)) else 'INCOMPATIBLE'})
    if not 1024<=port<=65535:raise SafeError('INVALID_PORT')
    try:
        with socket.socket() as s:s.bind(('127.0.0.1',port))
        checks.append({'gate':'loopback','status':'PASS'})
    except OSError:checks.append({'gate':'loopback','status':'INCOMPATIBLE'})
    checks += [{'gate':'exact_release_and_private_profile','status':'PASS'},{'gate':'path_safety_app_data_separation','status':'PASS'},{'gate':'runtime_off_defaults','status':'PASS'}]
    failed=[c['status'] for c in checks if c['status'] not in {'PASS','OPTIONAL_UNAVAILABLE','NOT_RUN'} or c['gate'] in {'data_volume','backup_volume'} and c['status']!='PASS']
    status='PASS' if not failed else ('BLOCKED_BY_PERMISSION' if 'BLOCKED_BY_PERMISSION' in failed else failed[0])
    return PrivatePreflight(format=1,scope='PRIVATE_LOCAL_SECURITY_TESTED_MAC_ONLY',status=status,
        release_id=m['release_id'],manifest_hash=expected_hash,runtime_input_hash=m['runtime_input_hash'],
        os=platform.system(),architecture=platform.machine(),python=platform.python_version(),root_kind='PRIVATE_LOCAL',
        checks=checks,storage_protection='VERIFIED_FILEVAULT_VOLUME' if data_volume=='PASS' else 'UNVERIFIED',
        backup_protection='VERIFIED_FILEVAULT_VOLUME' if backup_volume=='PASS' else 'UNVERIFIED',
        application_level_database_encryption='NOT_IMPLEMENTED',application_level_backup_encryption='NOT_IMPLEMENTED',runtime_profile=PROFILE).model_dump()


def require_preflight(*args):
    report=preflight(*args)
    if report['status'] != 'PASS':raise SafeError(report['status'])
    return report


def readiness(report, lifecycle_pass):
    report=PrivatePreflight.model_validate(report)
    storage=report.storage_protection=='VERIFIED_FILEVAULT_VOLUME' and report.status=='PASS'
    backup=report.backup_protection=='VERIFIED_FILEVAULT_VOLUME' and storage and lifecycle_pass
    core=storage and backup and lifecycle_pass
    return {'MAC_CORE_PILOT':'READY' if core else 'NOT_READY','PRIVATE_STORAGE_SECURITY':'READY' if storage else 'NOT_READY',
        'PRIVATE_BACKUP':'READY' if backup else 'NOT_READY','ACTIVATION_PROCEDURE':'READY' if core else 'NOT_READY',
        'decision_scope':'ENGINEERING_ONLY_REQUIRES_INDEPENDENT_ACCEPT_AND_OWNER_DATA_OWNER_ACTIVATION',
        'PHONE_PILOT':'NEEDS_TRANSPORT_GATE','phone_gate':'PHONE_PRIVATE_TRANSPORT_REQUIRED',
        'PRIVATE_AI':'BLOCKED_M7C_N02','HUMAN_UA_ASR':'NOT_RUN_M7C_N03','HEALTH_WATCH':'NOT_RUN_M6_N01',
        'CLINICAL_SELF_HELP':'OFF_27_FINDINGS_OPEN','M7D_N02':'OPEN_HUMAN_LANGUAGE_REVIEW',
        'ACTUAL_PRIVATE_PILOT':'NOT_STARTED','actual_private_root':'NOT_CREATED'}
