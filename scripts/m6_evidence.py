"""Allowlist public hardware evidence before serialization; no real payloads or fingerprints."""
import json,re
from pathlib import Path
CAPABILITY_FIELDS={'schema_version','health_connect','api_level','bridge_version','write_permissions','background_history_location_permissions','permissions','record_availability','source_classes','hardware_origin','import_duration_bucket','export_ready','private_import','idempotent_reimport','checkpoint_persisted','incremental_mode','read_only_code'}
ENUMS={'health_connect':{'AVAILABLE','UPDATE_REQUIRED','UNAVAILABLE'},'bridge_version':{'0.6.0-debug','0.6.1-debug'},'write_permissions':{'NONE'},'background_history_location_permissions':{'NONE'},'hardware_origin':{'NOT_VERIFIED','HARDWARE_ORIGIN_NOT_EXPOSED'},'import_duration_bucket':{'LT_1S','GE_1S'},'private_import':{'PASS','FAIL'},'idempotent_reimport':{'PASS','FAIL'},'checkpoint_persisted':{'PASS','FAIL'},'incremental_mode':{'OBSERVED','NOT_YET_RUN'},'read_only_code':{'NO_SOURCE_WRITE_CAPABILITY'}}
def sanitize_probe(p):
    if not isinstance(p,dict) or set(p)-CAPABILITY_FIELDS:raise ValueError('PUBLIC_EVIDENCE_FIELD_DENIED')
    if type(p.get('schema_version')) is not int or p['schema_version']!=1:raise ValueError('EVIDENCE_SCHEMA')
    if type(p.get('api_level')) is not int or not 28<=p['api_level']<=99:raise ValueError('EVIDENCE_API')
    for key,values in ENUMS.items():
        if key in p and (not isinstance(p[key],str) or p[key] not in values):raise ValueError('EVIDENCE_VALUE_DENIED')
    for key,values in [('permissions',{'GRANTED','PERMISSION_DENIED'}),('record_availability',{'YES','NO','NOT_READ'})]:
        if key in p:
            if not isinstance(p[key],dict) or set(p[key])!={'sleep','steps','exercise'} or any(not isinstance(v,str) or v not in values for v in p[key].values()):raise ValueError('EVIDENCE_SCOPE_DENIED')
    if 'permissions' not in p:raise ValueError('EVIDENCE_PERMISSION_REQUIRED')
    if 'export_ready' in p and type(p['export_ready']) is not bool:raise ValueError('EVIDENCE_VALUE_DENIED')
    if 'source_classes' in p and (not isinstance(p['source_classes'],list) or any(not isinstance(v,str) or v not in {'SOURCE_APP_SAMSUNG_HEALTH','OTHER_SOURCE_APP'} for v in p['source_classes'])):raise ValueError('EVIDENCE_ORIGIN_DENIED')
    return json.loads(json.dumps(p,allow_nan=False))
def main():
    folder=Path(__file__).resolve().parents[1]/'reports/evidence/M6'
    for file in folder.glob('EARLY_*.json'):
        p=json.loads(file.read_text())
        if 'health_connect' in p:sanitize_probe(p)
        elif file.name=='EARLY_OBSERVED_FIELDS.json':
            if set(p)!={'source','observed_field_types'} or p['source']!='ACTUAL_EARLY_NORMALIZED_API_SUBSET' or set(p['observed_field_types'])!={'sleep','steps','exercise'}:raise ValueError('FIELD_EVIDENCE_SCHEMA')
            allowed={'modified','start','end','start_offset','end_offset','fields.stages','fields.stages_state','fields.count','fields.unit','fields.exercise_type','fields.classification'}
            if not all(isinstance(fields,dict) and set(fields)<=allowed and all(v in {'string','integer','array','null'} for v in fields.values()) for fields in p['observed_field_types'].values()):raise ValueError('FIELD_EVIDENCE_VALUE')
        elif file.name=='EARLY_DEVICE_METADATA.json':
            if set(p)!={'android','api','one_ui','samsung_health','health_connect_system'}:raise ValueError('DEVICE_METADATA_FIELDS')
            for key in ('android','api','one_ui'):
                if not isinstance(p[key],str) or not re.fullmatch(r'[0-9.]{1,12}',p[key]):raise ValueError('DEVICE_METADATA_VALUE')
            for key in ('samsung_health','health_connect_system'):
                if not isinstance(p[key],list) or not all(isinstance(x,str) and re.fullmatch(r'(?:versionName=[0-9.]{1,30}|versionCode=[0-9]+ minSdk=[0-9]+ targetSdk=[0-9]+)',x) for x in p[key]):raise ValueError('DEVICE_VERSION_VALUE')
        elif file.name=='EARLY_LOG_REDACTION_CHECK.json':
            if p!={'own_bridge_pid_logcat_only':True,'health_payload_markers_found':False,'raw_logs_persisted':False,'source_mutations_performed':False}:raise ValueError('LOG_CHECK_DENIED')
        elif file.name=='EARLY_INSTALLED_MANIFEST.json':
            if p!={'installed_health_permissions_exact':True,'health_write_permissions':'NONE','background_history_location_permissions':'NONE','internet_permission':'NONE','command':'.venv/bin/python scripts/m6_probe_permissions.py','exit_code':0}:raise ValueError('MANIFEST_CHECK_DENIED')
        else:raise ValueError('UNKNOWN_EARLY_ARTIFACT')
    print('M6_PUBLIC_HARDWARE_EVIDENCE_ALLOWLIST_PASS')
if __name__=='__main__':main()
