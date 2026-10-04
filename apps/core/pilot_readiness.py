"""Non-sensitive reference-Mac facts and an INACTIVE future pilot profile."""
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from .storage import SafeError

PROFILE={'profile_id':'MAC_CORE_PILOT_V1','profile_version':1,'activation':'NOT_STARTED_REQUIRES_SEPARATE_OWNER_GOAL',
         'journal':'ON','creative':'ON','local_search':'ON','backup_restore':'ON','private_ai':'OFF','clinical_self_help':'OFF',
         'health_to_ai':'OFF','health_bridge':'OFF','human_voice_asr':'OFF','cloud_asr':'NONE','external_embeddings':'OFF',
         'telemetry':'NONE','cloud_sync':'NONE','publication':'NONE','phone':'REQUIRES_SEPARATE_PRIVATE_TRANSPORT_GATE','private_data_root':'NOT_CREATED'}
Status=Literal['PASS','OPTIONAL_UNAVAILABLE','NOT_RUN','BLOCKED_BY_PERMISSION','INCOMPATIBLE']
class Check(BaseModel):
    model_config=ConfigDict(extra='forbid')
    gate:str
    status:Status
    reason:str|None=None
    version:str|None=None
class MacFacts(BaseModel):
    model_config=ConfigDict(extra='forbid')
    os:Literal['Darwin']
    macos_version:str
    architecture:Literal['arm64']
    python:str
    hardware_model:str
    chip:str
class MacPreflight(BaseModel):
    model_config=ConfigDict(extra='forbid')
    format:Literal[1]
    scope:Literal['REAL_REFERENCE_MAC_SYNTHETIC_ONLY']
    status:Status
    release_id:str
    manifest_hash:str=Field(pattern='^[0-9a-f]{64}$')
    runtime_input_hash:str=Field(pattern='^[0-9a-f]{64}$')
    facts:MacFacts
    data_schema_version:int|None
    target_schema:int
    disk_space_class:Literal['BELOW_32_MIB','32_MIB_TO_1_GIB','1_TO_10_GIB','AT_LEAST_10_GIB']
    checks:list[Check]
    private_data_used:Literal[False]
    live_provider_calls:Literal[0]
    hardware_generalization:Literal['TESTED_MACHINE_ONLY_NOT_ALL_MACS']

def validate_profile(path):
    try:
        data=json.loads(Path(path).read_text())
        if data!=PROFILE:raise ValueError()
    except (OSError,ValueError,TypeError):raise SafeError('PILOT_PROFILE_INCOMPATIBLE') from None
    return data

def reference_mac_preflight(package,expected_hash,app,data,port=8765):
    from .release import preflight,validate_package
    result=preflight(package,expected_hash,app,data,port);manifest=validate_package(package,expected_hash)
    if manifest['format']!=2:raise SafeError('M8B_RUNTIME_MANIFEST_REQUIRED')
    def fact(argv):
        return subprocess.check_output(argv,text=True,stderr=subprocess.DEVNULL,timeout=3).strip()
    if platform.system()!='Darwin' or platform.machine()!='arm64':raise SafeError('REFERENCE_MAC_INCOMPATIBLE')
    facts={'os':platform.system(),'macos_version':platform.mac_ver()[0],'architecture':platform.machine(),
           'python':platform.python_version(),'hardware_model':fact(['sysctl','-n','hw.model']),
           'chip':fact(['sysctl','-n','machdep.cpu.brand_string'])}
    free=shutil.disk_usage(Path(data).parent).free
    space='BELOW_32_MIB' if free<32*1024**2 else '32_MIB_TO_1_GIB' if free<1024**3 else '1_TO_10_GIB' if free<10*1024**3 else 'AT_LEAST_10_GIB'
    report=MacPreflight(format=1,scope='REAL_REFERENCE_MAC_SYNTHETIC_ONLY',status=result['status'],
                        release_id=result['release_id'],manifest_hash=expected_hash,runtime_input_hash=manifest['runtime_input_hash'],
                        facts=facts,data_schema_version=result['schema'],target_schema=result['target_schema'],disk_space_class=space,
                        checks=result['checks'],private_data_used=False,live_provider_calls=0,
                        hardware_generalization='TESTED_MACHINE_ONLY_NOT_ALL_MACS')
    result=report.model_dump(mode='json',exclude_none=True)
    result['data_schema_version']=report.data_schema_version
    return result

def readiness(preflight,lifecycle_pass):
    valid=MacPreflight.model_validate(preflight)
    return {'MAC_CORE_PILOT':'NOT_READY',
            'MAC_SYNTHETIC_DRY_RUN':'READY' if valid.status=='PASS' and lifecycle_pass else 'NOT_READY',
            'blocking_core_gate':'PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED',
            'decision_scope':'ENGINEERING_HANDOFF_ONLY_NOT_PRIVATE_PILOT_AUTHORIZATION',
            'PHONE_PILOT':'NEEDS_TRANSPORT_GATE','phone_gate':'PHONE_PRIVATE_TRANSPORT_REQUIRED',
            'PRIVATE_AI':'BLOCKED_M7C_N02','HUMAN_UA_ASR':'NOT_RUN_M7C_N03','HEALTH_WATCH':'NOT_RUN_M6_N01',
            'CLINICAL_SELF_HELP':'OFF_27_FINDINGS_OPEN','actual_private_pilot':'NOT_STARTED','profile_activation':'NOT_STARTED',
            'private_data_root':'NOT_CREATED','requirements_before_activation':['EXPLICIT_OWNER_PILOT_GOAL','DATA_OWNER_CONSENT','PRIVATE_ROOT_RUNTIME_PROFILE_AND_STORAGE_APPROVAL','BACKUP_STORAGE_AND_RETENTION_DECISION']}
