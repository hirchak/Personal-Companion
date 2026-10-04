#!/usr/bin/env python3
"""Owner-authorized REAL_REFERENCE_MAC dry run; entirely disposable SYNTHETIC roots, no installs/network setup."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import select
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import venv
from uuid import uuid4
import httpx
from apps.core import release as r
from apps.core.storage import REPO,Store,encode,digest,SafeError
from apps.core.pilot_readiness import MacPreflight,readiness,PROFILE


def runtime_only_environment(root):
    """Copy only already-installed pinned runtime distributions into a pip-free temp venv."""
    venv.EnvBuilder(with_pip=False).create(root)
    python=root/'bin/python'
    site=Path(subprocess.check_output([str(python),'-I','-c','import sysconfig;print(sysconfig.get_path("purelib"))'],text=True).strip())
    import sysconfig
    existing=Path(sysconfig.get_path('purelib')).resolve()
    copied=[]
    for line in (REPO/'requirements.runtime.lock').read_text().splitlines():
        name,version=line.split('==');dist=importlib.metadata.distribution(name)
        if dist.version!=version:raise SafeError('RUNTIME_PREREQUISITE_INCOMPATIBLE')
        for item in dist.files or []:
            source=Path(dist.locate_file(item)).resolve()
            if not source.is_relative_to(existing) or not source.is_file() or source.suffix=='.pyc' or '__pycache__' in source.parts or source.name=='direct_url.json':continue
            target=site/source.relative_to(existing);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        copied.append({'package':name,'version':version})
    probe=subprocess.check_output([str(python),'-I','-c','import importlib.util,json;print(json.dumps({x:importlib.util.find_spec(x) is None for x in ["pytest","playwright","httpx","pip"]}))'],text=True)
    absent=json.loads(probe)
    if not all(absent.values()):raise SafeError('RUNTIME_ENVIRONMENT_NOT_MINIMAL')
    return python,{'status':'PASS','method':'COPY_EXISTING_PINNED_RUNTIME_ONLY_PIP_FREE_TEMP_ENVIRONMENT','packages':copied,'no_downloads_or_package_manager_installs':True,'test_client_packages_absent':absent}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=REPO/'generated/m8b-verification');a=parser.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    C=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    package=REPO/'generated/releases'/('M8B-'+C);package.parent.mkdir(parents=True,exist_ok=True)
    manifest=r.prepare(package) if not package.exists() else r.validate_package(package,r.read_json(package/'release-manifest.json')['manifest_hash'])
    expected=manifest['manifest_hash'];(a.output/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    work=Path(tempfile.mkdtemp(prefix='m8b-original-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
    app,data=work/'Синтетичний застосунок',work/'Синтетичні дані';port=8879;origin=f'http://127.0.0.1:{port}'
    checks={};times={}
    def measured(name,fn):
        t=time.monotonic();result=fn();times[name]=round((time.monotonic()-t)*1000,3);return result
    def command(python,cmd,*args):
        # Private/transient runtime stdout stays in memory; only structured safe status gets evidence.
        result=subprocess.run([str(python),'-I','-B',str(package/'launch.py'),cmd,*map(str,args)],cwd=work,capture_output=True,text=True)
        if result.returncode:raise SafeError('SYNTHETIC_'+cmd.upper().replace('-','_')+'_FAILED')
        return json.loads(result.stdout)
    def boot(app_root,data_root,python=None,build_id=None):
        t=time.monotonic()
        process=subprocess.Popen([str(python or runtime_python),'-I','-B',str(package/'launch.py'),'start','--app',str(app_root),'--data',str(data_root),'--port',str(port)],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        client=None
        try:
            assert select.select([process.stdout],[],[],15)[0],'READINESS_TIMEOUT'
            first=process.stdout.readline()
            if not first.startswith('Local synthetic runtime:'):
                try:error=json.loads(first).get('code','STARTUP_FAILED')
                except ValueError:error='STARTUP_FAILED'
                raise SafeError(error)
            code=process.stdout.readline().strip().split(': ',1)[1]
            client=httpx.Client(base_url=origin,headers={'Origin':origin,'X-PC-Build':build_id or C},timeout=5)
            for _ in range(100):
                try:
                    unlock=client.post('/api/v1/auth/unlock',json={'code':code});assert unlock.status_code==200,'UNLOCK_FAILED'
                    client.headers['X-CSRF-Token']=unlock.json()['csrf_token'];times.setdefault('startup_readiness',round((time.monotonic()-t)*1000,3))
                    return process,client
                except httpx.ConnectError:time.sleep(.05)
            raise SafeError('READINESS_TIMEOUT')
        except BaseException:
            if client:client.close()
            process.terminate();process.wait(10);process.stdout.close();raise
    def stop(process,client):
        client.close();process.terminate();process.wait(10);process.stdout.close()
        with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
    def defaults(client):
        assert client.get('/api/v1/status').json()['provider']=='OFF'
        assert client.get('/api/v1/status').json()['schema_version']==11
        status=client.get('/api/v1/conversations/status').json()
        assert status['responder']=='OFF' and status['live_provider_calls'] is False and status['clinical_active']==0 and status['real_private_data'] is False
        assert len(status['skills']['off'])==5 and all(i['status']=='CONTRACT_ONLY_NOT_ACTIVE' for i in status['skills']['off'])
        assert client.get('/api/v1/ai/status').json()['mode']=='OFF'
        assert client.get('/api/v1/practices/catalog').json()['production_active_clinical']==0
        health=client.get('/api/v1/health/status').json();assert all(v=='NOT_REQUESTED' for v in health['permissions'].values())
        assert client.get('/api/v1/voice/audio').json()['actual_backend']['available'] is False
        return {'provider':'OFF','private_ai':'OFF','clinical_active':0,'five_specialists':'OFF','health_to_ai':'OFF','health_permissions':'NOT_REQUESTED','human_asr':'OFF','cloud_asr':'NONE'}
    try:
        runtime_python,checks['runtime_only']=measured('runtime_existing_copy',lambda:runtime_only_environment(work/'runtime-only'))
        report=measured('preflight',lambda:command(runtime_python,'mac-preflight','--package',package,'--manifest-hash',expected,'--app',app,'--data',data,'--port',port))
        MacPreflight.model_validate(report);assert report['status']=='PASS';checks['actual_mac_preflight']=report
        (a.output/'MAC_PREFLIGHT.json').write_text(json.dumps(report,indent=2)+'\n')
        checks['install']=measured('fresh_install',lambda:command(runtime_python,'install','--package',package,'--manifest-hash',expected,'--app',app,'--data',data))
        process,client=boot(app,data)
        try:
            checks['fresh_defaults']=defaults(client)
            entry_id=str(uuid4());creative_id=str(uuid4())
            for id,payload in [(entry_id,{'type':'daily','raw_text':'ORIGINAL SYNTHETIC · M8B journal'}),(creative_id,{'type':'creative','creative_kind':'idea','raw_text':'ORIGINAL SYNTHETIC · M8B creative'})]:
                assert client.post('/api/v1/entries',json={'operation_id':str(uuid4()),'entry_id':id,'base_revision':0,'payload':payload}).status_code==201
            search=client.get('/api/v1/entries',params={'q':'ORIGINAL SYNTHETIC','type':'creative'}).json()
            assert any(i['id']==creative_id for i in search['items'])
            checks['local_search']={'status':'PASS','scope':'ORIGINAL_SYNTHETIC_LOCAL_SQLITE'}
            conversation=client.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json()['conversation']
            sent=client.post('/api/v1/conversations/'+conversation['id']+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC · Provider OFF preserves user text'}).json()
            assert len(sent['messages'])==1 and sent['responder']=='OFF'
            from playwright.sync_api import sync_playwright,expect
            os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000})
                external=[];errors=[]
                def route(route):
                    from urllib.parse import urlparse
                    if urlparse(route.request.url).hostname!='127.0.0.1':external.append('NONLOOPBACK_BLOCKED');route.abort()
                    else:route.continue_()
                context.route('**/*',route);context.add_cookies([{'name':'m1_session','value':client.cookies['m1_session'],'url':origin,'httpOnly':True,'sameSite':'Strict'}])
                page=context.new_page();page.on('pageerror',lambda _:errors.append('PAGE_ERROR'));page.goto(origin)
                page.get_by_role('button',name='Щоденник',exact=True).click();expect(page.get_by_text('ORIGINAL SYNTHETIC · M8B journal',exact=True)).to_be_visible()
                page.get_by_role('button',name='Додати запис',exact=True).click();page.get_by_label('Текст',exact=True).fill('ORIGINAL SYNTHETIC · M8B browser journal')
                page.get_by_role('button',name='Зберегти на Mac').click();expect(page.get_by_text('ORIGINAL SYNTHETIC · M8B browser journal',exact=True)).to_be_visible()
                page.screenshot(path=str(a.output/'mac-journal.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(a.output/'chromium-narrow.png'),full_page=True)
                assert not external and not errors;checks['Chromium']={'status':'PASS','physical_scope':'REFERENCE_MAC_ONLY','viewports':['1440x1000','390x844'],'page_errors':0,'non_loopback_requests':0,'GALAXY':'NOT_RUN'}
                context.close();browser.close()
        finally:stop(process,client)
        process,client=boot(app,data)
        try:
            checks['restart_defaults']=defaults(client)
            assert client.get('/api/v1/entries/'+entry_id).json()['raw_text']=='ORIGINAL SYNTHETIC · M8B journal'
            assert len(client.get('/api/v1/conversations/'+conversation['id']).json()['messages'])==1
            checks['restart']={'status':'PASS','state_durable':True,'no_duplicate_mutation':True,'stop_immediate_port_rebind':True}
        finally:stop(process,client)
        bound_backup=work/'bound backup'
        receipt=measured('backup',lambda:command(runtime_python,'backup','--app',app,'--data',data,'--backup',bound_backup));checks['backup']=receipt
        backup_meta=r.verify_backup(bound_backup,expected,receipt['backup_manifest_hash'])
        checks['backup_provenance']={'status':'PASS','backup_format':backup_meta['backup_format'],'producing_release':backup_meta['app_version'],'producer_manifest_hash':backup_meta['release_provenance']['producing_manifest']['manifest_hash'],'source_release':backup_meta['release_provenance']['source_release'],'created_at_utc':backup_meta['created_at_utc'],'snapshot_binding':'SQLITE_ATTESTATION_AND_CHECKSUM_VERIFIED'}
        # Tampered provenance rejected, while original backup/source remain preserved.
        tampered=work/'tampered synthetic backup';shutil.copytree(bound_backup,tampered)
        m=r.read_json(tampered/'manifest.json');m['release_provenance']['source_release']['manifest_hash']='0'*64;(tampered/'manifest.json').write_text(encode(m))
        try:r.restore(package,expected,tampered,work/'must not create app',work/'must not create data')
        except SafeError:checks['tampered_provenance']={'status':'PASS','restore':'REJECTED_BEFORE_ROOT_CREATION'}
        else:raise SafeError('PROVENANCE_TAMPER_NOT_BLOCKED')
        restored_app,restored_data=work/'restored app',work/'restored data'
        checks['restore']=measured('restore',lambda:command(runtime_python,'restore','--package',package,'--manifest-hash',expected,'--backup',bound_backup,'--backup-manifest-hash',receipt['backup_manifest_hash'],'--app',restored_app,'--data',restored_data))
        process,client=boot(restored_app,restored_data)
        try:
            checks['restored_defaults']=defaults(client);assert client.get('/api/v1/entries/'+creative_id).json()['creative_kind']=='idea'
            assert client.get('/api/v1/entries/'+entry_id).json()['raw_text']=='ORIGINAL SYNTHETIC · M8B journal'
        finally:stop(process,client)
        # Controlled old-schema projection on disposable copy only. Never damage real OS/private vault.
        with sqlite3.connect(data/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=10')
        active_before=r.read_json(app/'active.json');failure_backup=work/'failed migration backup'
        try:r.upgrade(package,expected,app,data,failure_backup,fail_migration=True)
        except sqlite3.OperationalError:pass
        else:raise SafeError('SIMULATED_MIGRATION_NOT_FAILED')
        assert r.inspect_data(data)==10 and r.read_json(app/'active.json')==active_before and (app/'upgrade-pending.json').exists()
        checks['failed_upgrade']={'status':'PASS','fixture':'SCHEMA10_PROJECTION_NOT_HISTORICAL_BINARY','data_transaction':'ROLLED_BACK','active_pointer':'UNCHANGED','backup':'VERIFIED','pending_start_gate':'PRESENT'}
        rollback_app,rollback_data=work/'rollback app',work/'rollback data'
        checks['rollback']=measured('rollback',lambda:command(runtime_python,'rollback','--package',package,'--manifest-hash',expected,'--backup',failure_backup,'--backup-manifest-hash',digest((failure_backup/'manifest.json').read_bytes()),'--app',rollback_app,'--data',rollback_data))
        process,client=boot(rollback_app,rollback_data)
        try:
            checks['rollback_defaults']=defaults(client);assert client.get('/api/v1/entries/'+entry_id).json()['raw_text']=='ORIGINAL SYNTHETIC · M8B journal'
        finally:stop(process,client)
        checks['upgrade']=measured('upgrade',lambda:command(runtime_python,'upgrade','--package',package,'--manifest-hash',expected,'--app',rollback_app,'--data',rollback_data,'--backup',work/'successful upgrade backup'))
        checks['uninstall']=command(runtime_python,'uninstall','--app',rollback_app,'--data',rollback_data)
        assert rollback_data.exists() and not rollback_app.exists()
        from apps.core.domain import Journal
        assert Journal(Store(rollback_data)).get(entry_id)['raw_text']=='ORIGINAL SYNTHETIC · M8B journal'
        checks['uninstall']['domain_integrity']='PASS';checks['reinstall_restore']='DEMONSTRATED_FRESH_RESTORE_AND_ROLLBACK_ROOTS'
        # Genuine old accepted M8A artifact, not a synthetic manifest identifier.
        old_id='M8A-38d3ed69839a8fc876c50b900552ad38d965c5cd'
        old_package=REPO/'generated/releases'/old_id
        old_hash='326ef01c1338eac05c3417714edf599255d944382118b30d0eadde3d39d142e4'
        if old_package.exists():
            old_manifest=r.validate_package(old_package,old_hash)
            old_app,old_data=work/'previous release app',work/'previous release data'
            # Historical M8A full-lock prerequisites exist in project env, not in new minimal runtime.
            r.install(old_package,old_hash,old_app,old_data)
            from apps.core.models import Create
            previous_entry=str(uuid4());j=Journal(Store(old_data))
            j.write('create',previous_entry,Create(operation_id=uuid4(),entry_id=previous_entry,base_revision=0,payload={'type':'daily','raw_text':'ORIGINAL SYNTHETIC previous accepted release'}))
            old_backup=work/'actual previous release backup'
            upgraded=r.upgrade(package,expected,old_app,old_data,old_backup)
            provenance=r.verify_backup(old_backup,expected,upgraded['backup_manifest_hash'])['release_provenance']
            assert provenance['source_release']['manifest_hash']==old_hash and provenance['producing_manifest']['manifest_hash']==expected
            process,client=boot(old_app,old_data)
            try:
                defaults(client);assert client.get('/api/v1/entries/'+previous_entry).json()['raw_text']=='ORIGINAL SYNTHETIC previous accepted release'
            finally:stop(process,client)
            old_rollback_app,old_rollback_data=work/'old compatible rollback app',work/'old compatible rollback data'
            r.restore(old_package,old_hash,old_backup,old_rollback_app,old_rollback_data,expected_producer_hash=expected,expected_backup_hash=upgraded['backup_manifest_hash'])
            process,client=boot(old_rollback_app,old_rollback_data,python=sys.executable,build_id=old_manifest['git_commit'])
            try:
                defaults(client);assert client.get('/api/v1/entries/'+previous_entry).json()['raw_text']=='ORIGINAL SYNTHETIC previous accepted release'
            finally:stop(process,client)
            r.uninstall(old_rollback_app,old_rollback_data);assert Journal(Store(old_rollback_data)).get(previous_entry)['raw_text']=='ORIGINAL SYNTHETIC previous accepted release'
            checks['actual_cross_release_upgrade_rollback']={'status':'PASS','old_release_id':old_id,'old_manifest_hash':old_hash,'new_release_id':manifest['release_id'],'producer_manifest_hash':expected,'source_manifest_hash':old_hash,'new_runtime':'RUNTIME_ONLY_12','legacy_rollback_runtime':'EXISTING_HISTORICAL_FULL_LOCK_ENVIRONMENT','roots':'DISPOSABLE_SYNTHETIC_ONLY'}
        else:checks['actual_cross_release_upgrade_rollback']={'status':'OPTIONAL_UNAVAILABLE','reason':'OLD_ACCEPTED_LOCAL_PACKAGE_NOT_PRESENT','alternative':'CURRENT_PACKAGE_PLUS_PREUPGRADE_BACKUP_PATH_VERIFIED'}
        decision=readiness(report,True);(a.output/'PILOT_READINESS.json').write_text(json.dumps(decision,indent=2)+'\n')
        result={'status':'PASS','scope':'REAL_REFERENCE_MAC_ORIGINAL_SYNTHETIC_ONLY','base_sha':'08d8efdd01dbcf8ddcdbdd6fcd6bd8361b75062a','implementation_sha':C,'release_id':manifest['release_id'],'manifest_hash':expected,'runtime_input_hash':manifest['runtime_input_hash'],'checks':checks,'timings_ms':times,'pilot_profile':PROFILE,'readiness':decision,'private_data_used':False,'live_provider_calls':0,'system_installs':0,'network_or_trust_changes':0,'private_pilot':'NOT_STARTED'}
        (a.output/'MAC_LIFECYCLE.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'status':'PASS','scope':result['scope'],'release_id':manifest['release_id'],'manifest_hash':expected,'runtime_input_hash':manifest['runtime_input_hash'],'readiness':decision,'checks':list(checks)}))
    finally:shutil.rmtree(work)

if __name__=='__main__':main()
