#!/usr/bin/env python3
"""Owner-controlled fixed bridge handoff only. Never prints device/record IDs or health values."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.core.health import PrivateHealthStore,HealthImport
from apps.core.health_contracts import HealthBatch
from apps.core.storage import SafeError
from scripts.m6_evidence import sanitize_probe
ROOT=Path(__file__).resolve().parents[1]
ADB=ROOT/'generated/android-tools/sdk/platform-tools/adb'
PACKAGE='ua.companion.health'
def adb(*args):
    r=subprocess.run([str(ADB),*args],capture_output=True)
    if r.returncode:raise SafeError('ADB_OPERATION_FAILED')
    return r.stdout
def connected():
    rows=[x.split()[-1] for x in adb('devices').decode().splitlines()[1:] if x.strip()]
    if rows!=['device']:raise SafeError('ONE_AUTHORIZED_USB_DEVICE_REQUIRED')
def probe():
    # Only two fixed handoff artifacts produced by this bridge; never dump other app files.
    p=json.loads(adb('exec-out','run-as',PACKAGE,'cat','files/bridge-probe.json'))
    allowed={'schema_version','health_connect','api_level','bridge_version','write_permissions','background_history_location_permissions','permissions','record_availability','source_classes','hardware_origin','import_duration_bucket','export_ready'}
    if set(p)-allowed:raise SafeError('PROBE_FIELDS_DENIED')
    if set(p.get('permissions',{}))!={'sleep','steps','exercise'}:raise SafeError('PROBE_SCOPE_INVALID')
    for v in p['permissions'].values():
        if v not in {'GRANTED','PERMISSION_DENIED'}:raise SafeError('PROBE_VALUE_DENIED')
    if p.get('record_availability'):
        if set(p['record_availability'])!={'sleep','steps','exercise'} or any(v not in {'YES','NO','NOT_READ'} for v in p['record_availability'].values()):raise SafeError('PROBE_VALUE_DENIED')
    if any(v not in {'SOURCE_APP_SAMSUNG_HEALTH','OTHER_SOURCE_APP'} for v in p.get('source_classes',[])):raise SafeError('PROBE_VALUE_DENIED')
    return sanitize_probe(p)
def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['connection','install','open','permissions','import','capture','probe']);p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path);a=p.parse_args()
    try:
        connected()
        if a.command=='connection':print('USB_DEVICE_AUTHORIZED');return
        if a.command=='install':adb('install','-r',str(ROOT/'apps/android-health/app/build/outputs/apk/debug/app-debug.apk'));print('DEBUG_BRIDGE_INSTALLED');return
        if a.command=='open':adb('shell','am','start','-n',PACKAGE+'/.MainActivity');print('BRIDGE_OPEN');return
        if a.command=='permissions':
            # Present normal UI; permissions are granted solely by the owner.
            adb('shell','am','start','-n',PACKAGE+'/.MainActivity');print('OWNER_TAP_PERMISSION_BUTTON_REQUIRED');return
        if a.command=='import':
            adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-a','ua.companion.health.IMPORT');print('FOREGROUND_IMPORT_REQUESTED');return
        result=probe()
        if a.command=='capture':
            if result.get('export_ready') is not True:raise SafeError('BRIDGE_EXPORT_NOT_READY')
            if a.root is None:raise SafeError('EXPLICIT_PRIVATE_ROOT_REQUIRED')
            raw=adb('exec-out','run-as',PACKAGE,'cat','files/bridge-export.json')
            if len(raw)>1000000:raise SafeError('HEALTH_BATCH_LIMIT')
            batch=HealthBatch.model_validate_json(raw)
            importer=HealthImport(PrivateHealthStore(a.root))
            first=importer.apply(batch,reconnect=True);before=importer.records();second=importer.apply(batch)
            result['private_import']='PASS';result['idempotent_reimport']='PASS' if second['result']=='IDEMPOTENT_REPLAY' and importer.records()==before else 'FAIL'
            result['checkpoint_persisted']='PASS' if HealthImport(PrivateHealthStore(a.root)).status()==importer.status() else 'FAIL'
            result['incremental_mode']='OBSERVED' if any(s.mode=='INCREMENTAL' and s.permission=='GRANTED' for s in batch.scopes) else 'NOT_YET_RUN'
            result['read_only_code']='NO_SOURCE_WRITE_CAPABILITY'
        result=sanitize_probe(result)
        if a.evidence:
            if not a.evidence.resolve().is_relative_to(ROOT/'reports/evidence/M6'):raise SafeError('EVIDENCE_PATH_DENIED')
            a.evidence.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
    except Exception as exc:
        print(exc.code if isinstance(exc,SafeError) else 'HARDWARE_OPERATION_FAILED_INPUT_WITHHELD');raise SystemExit(1) from None
if __name__=='__main__':main()
