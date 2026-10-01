import json,xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from scripts.m6_evidence import sanitize_probe
ROOT=Path(__file__).resolve().parents[1]

def test_android_manifest_minimal_and_no_source_write_api():
    manifest=ET.parse(ROOT/'apps/android-health/app/src/main/AndroidManifest.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
    assert {n.get(ns+'name') for n in manifest.findall('uses-permission')}=={'android.permission.health.READ_SLEEP','android.permission.health.READ_STEPS','android.permission.health.READ_EXERCISE'}
    assert manifest.find('application').get(ns+'allowBackup')=='false';assert not manifest.findall('.//service') and not manifest.findall('.//receiver') and not manifest.findall('.//provider')
    code='\n'.join(p.read_text() for p in (ROOT/'apps/android-health/app/src/main').rglob('*.kt'))
    for forbidden in ('insertRecords(', 'updateRecords(', 'deleteRecords(', 'getWritePermission(', 'WorkManager','HeartRateRecord','ExerciseRouteRequest','Log.d(', 'println(', 'WebView','http://','https://'):
        assert forbidden not in code
    assert 'getChangesToken(' in code and 'getChanges(' in code and 'getGrantedPermissions()' in code
    assert 'filesDir' in code
    assert 'importJob?.cancel();val cleared=BridgeFiles.clear(filesDir)' in code

def probe():return {'schema_version':1,'api_level':36,'health_connect':'AVAILABLE','bridge_version':'0.6.0-debug','permissions':{k:'GRANTED' for k in ('sleep','steps','exercise')}}
@pytest.mark.parametrize('key,value',[('record_id','SYNTHETIC-PRIVATE'),('count',42),('sleep_start','2025-01-01T01:00:00Z'),('device_serial','SYNTHETIC-PRIVATE'),('payload_hash','SYNTHETIC-private'),('record_availability',{'sleep':42,'steps':'YES','exercise':'NO'}),('source_classes',['synthetic.private.package']),('health_connect','2025-01-01T01:00:00Z'),('bridge_version','SYNTHETIC-private')])
def test_public_probe_refuses_values_and_identifiers(key,value):
    p=probe();p[key]=value
    with pytest.raises(ValueError):sanitize_probe(p)
def test_public_probe_accepts_only_structural_data():
    p=probe();p['record_availability']={'sleep':'YES','steps':'YES','exercise':'NO'};assert sanitize_probe(p)==p

def test_handoff_refuses_old_staging_after_failed_or_unfinished_import(monkeypatch,tmp_path,capsys):
    import scripts.m6_hardware as hw
    monkeypatch.setattr(hw,'connected',lambda:None)
    monkeypatch.setattr(hw,'probe',probe)
    monkeypatch.setattr(hw,'adb',lambda *args:pytest.fail('STALE_PRIVATE_PAYLOAD_MUST_NOT_BE_READ'))
    root=tmp_path/'private-hardware'
    monkeypatch.setattr('sys.argv',['m6_hardware.py','capture','--root',str(root)])
    with pytest.raises(SystemExit) as exc:hw.main()
    assert exc.value.code==1 and 'BRIDGE_EXPORT_NOT_READY' in capsys.readouterr().out and not root.exists()
