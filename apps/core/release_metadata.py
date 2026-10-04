"""Pure exact release/backup provenance validation. Unsigned integrity, no private I/O."""
import re,sqlite3
from datetime import datetime,timezone
from .storage import SCHEMA,SafeError,encode,digest

DEFAULTS = {'provider':'OFF','clinical_active':0,'specialists':'OFF','health_to_ai':'OFF',
            'cloud_asr':'NONE','real_private_provider':'OFF','external_embeddings':'OFF',
            'publication':'NONE','cloud_sync':'NONE','telemetry':'NONE','provider_fallback':'NONE'}
CONTRACT=2

def identity(m):return digest(encode({k:v for k,v in m.items() if k!='manifest_hash'}).encode())

def validate_manifest(m):
    try:
        old=m['format']==1
        keys={'format','release_id','git_commit','schema_version','python_input_hash','web_lock_hash','platform','defaults','compatibility','files','manifest_hash'}
        if not old:keys.add('runtime_input_hash')
        if set(m)!=keys or type(m['format']) is not int or m['format'] not in {1,2}:raise ValueError()
        if m['defaults']!=DEFAULTS or type(m['schema_version']) is not int or m['schema_version']!=SCHEMA:raise ValueError()
        if not re.fullmatch('[0-9a-f]{40}',m['git_commit']):raise ValueError()
        if m['release_id']!=('M8A-' if old else 'M8B-')+m['git_commit']:raise ValueError()
        if m['compatibility']!={'schema_min':2,'schema_max':SCHEMA,'web_contract':CONTRACT,'downgrade':'FRESH_ROOT_BACKUP_ONLY'}:raise ValueError()
        if m['platform']!={'os':'Darwin','architecture':'arm64','python':'3.13','dependencies':'EXACT_REQUIREMENTS_LOCK' if old else 'EXACT_RUNTIME_LOCK','self_contained':False}:raise ValueError()
        if not isinstance(m['files'],dict) or not m['files']:raise ValueError()
        for p,h in m['files'].items():
            if not p or p.startswith('/') or '..' in p.split('/') or not re.fullmatch('[0-9a-f]{64}',h):raise ValueError()
        required={'launch.py','apps/core/release.py','apps/core/storage.py','apps/core/api.py','apps/web/dist/index.html','apps/web/dist/phone/sw.js','requirements.lock','apps/web/package-lock.json'}
        if not old:required|={'requirements.runtime.lock','apps/core/release_metadata.py','packages/pilot/MAC_CORE_PROFILE.json'}
        if not required<=m['files'].keys():raise ValueError()
        if m['python_input_hash']!=m['files']['requirements.lock'] or m['web_lock_hash']!=m['files']['apps/web/package-lock.json']:raise ValueError()
        if not old and m['runtime_input_hash']!=m['files']['requirements.runtime.lock']:raise ValueError()
        if identity(m)!=m['manifest_hash']:raise ValueError()
    except (ValueError,KeyError,TypeError):raise SafeError('RELEASE_INTEGRITY') from None
    return m

def release_reference(m):
    validate_manifest(m)
    return {k:m[k] for k in ('release_id','git_commit','manifest_hash','schema_version')}

def provenance(producer,source,schema,created):
    result={'version':1,'producing_manifest':producer,'source_release':release_reference(source),
            'snapshot_schema':schema,'backup_format':3,'created_at_utc':created}
    validate_provenance(result)
    return result

def validate_provenance(value):
    try:
        if set(value)!={'version','producing_manifest','source_release','snapshot_schema','backup_format','created_at_utc'}:raise ValueError()
        if type(value['version']) is not int or value['version']!=1 or type(value['backup_format']) is not int or value['backup_format']!=3:raise ValueError()
        producer=validate_manifest(value['producing_manifest']);source=value['source_release']
        if set(source)!={'release_id','git_commit','manifest_hash','schema_version'}:raise ValueError()
        if not re.fullmatch('[0-9a-f]{40}',source['git_commit']) or source['release_id'] not in {'M8A-'+source['git_commit'],'M8B-'+source['git_commit']}:raise ValueError()
        if not re.fullmatch('[0-9a-f]{64}',source['manifest_hash']) or type(source['schema_version']) is not int or source['schema_version']!=SCHEMA:raise ValueError()
        schema=value['snapshot_schema']
        if type(schema) is not int or not producer['compatibility']['schema_min']<=schema<=producer['compatibility']['schema_max']:raise ValueError()
        dt=datetime.fromisoformat(value['created_at_utc'])
        if dt.utcoffset()!=timezone.utc.utcoffset(dt):raise ValueError()
    except (KeyError,ValueError,TypeError,SafeError):raise SafeError('BACKUP_RELEASE_PROVENANCE') from None
    return value

def check_backup_provenance(manifest,connection,expected_producer_hash=None):
    try:
        value=validate_provenance(manifest['release_provenance'])
        if manifest['backup_format']!=3 or manifest['schema_version']!=value['snapshot_schema'] or manifest['created_at_utc']!=value['created_at_utc'] or manifest['app_version']!=value['producing_manifest']['release_id']:raise ValueError()
        rows=connection.execute('SELECT payload FROM release_backup_provenance').fetchall()
        if len(rows)!=1 or rows[0][0]!=encode(value):raise ValueError()
        if expected_producer_hash is not None and value['producing_manifest']['manifest_hash']!=expected_producer_hash:raise ValueError()
    except (KeyError,ValueError,TypeError,sqlite3.Error):raise SafeError('BACKUP_RELEASE_PROVENANCE') from None
    return value
