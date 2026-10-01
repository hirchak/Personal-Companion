#!/usr/bin/env python3
"""Inspect only this bridge's installed permission declaration; redact all dumpsys identifiers."""
import json,re,subprocess
from pathlib import Path
adb=Path(__file__).resolve().parents[1]/'generated/android-tools/sdk/platform-tools/adb'
r=subprocess.run([str(adb),'shell','dumpsys','package','ua.companion.health'],capture_output=True,text=True)
if r.returncode:raise SystemExit('PACKAGE_INSPECTION_FAILED')
match=re.search(r'requested permissions:\n(.*?)(?:install permissions:|User \d+:)',r.stdout,re.S)
if not match:raise SystemExit('REQUESTED_PERMISSIONS_NOT_FOUND')
permissions=set(re.findall(r'^\s+(android\.permission\.[A-Z_]+)\s*$',match.group(1),re.M))
allowed={'android.permission.health.READ_SLEEP','android.permission.health.READ_STEPS','android.permission.health.READ_EXERCISE'}
# Health permissions contain a lowercase namespace; separately match exact lines.
permissions.update(re.findall(r'^\s+(android\.permission\.health\.[A-Z_]+)\s*$',match.group(1),re.M))
health={p for p in permissions if '.health.' in p}
result={'installed_health_permissions_exact':health==allowed,'health_write_permissions':'NONE' if not any('.WRITE_' in p for p in permissions) else 'FOUND','background_history_location_permissions':'NONE' if not any(any(x in p for x in ('BACKGROUND','HISTORY','LOCATION','ROUTE')) for p in permissions) else 'FOUND','internet_permission':'NONE' if 'android.permission.INTERNET' not in permissions else 'FOUND'}
print(json.dumps(result,indent=2))
if not result['installed_health_permissions_exact'] or any(v=='FOUND' for v in result.values()):raise SystemExit(1)
