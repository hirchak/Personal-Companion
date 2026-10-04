#!/usr/bin/env python3
"""Actual reference Mac PRIVATE_LOCAL_RUNTIME_WITH_SYNTHETIC_CONTENT; no real vault/installs/OS changes."""
import argparse
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
from uuid import uuid4
import httpx
from apps.core import release as r, local_private as p
from apps.core.storage import REPO, SafeError, digest
from scripts.verify_m8b import runtime_only_environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=REPO/'generated/m8c-verification')
    parser.add_argument('--previous-package',type=Path)
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    package=REPO/'generated/releases'/('M8C-'+commit);package.parent.mkdir(parents=True,exist_ok=True)
    m=r.prepare(package) if not package.exists() else r.validate_package(package,r.read_json(package/'release-manifest.json')['manifest_hash'])
    assert m['git_commit']==commit and m['format']==3
    expected=m['manifest_hash']
    (a.output/'RELEASE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
    work=Path(tempfile.mkdtemp(prefix='m8c-original-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
    app,data,backups=work/'Застосунок',work/'PRIVATE_LOCAL_WITH_ORIGINAL_SYNTHETIC_CONTENT',work/'Захищені синтетичні backups'
    backups.mkdir(mode=0o700);port=8883;origin=f'http://127.0.0.1:{port}'
    checks={};timings={}
    def measured(label,fn):
        start=time.monotonic();result=fn();timings[label]=round((time.monotonic()-start)*1000,3);return result
    def command(cmd,*args,manager=None):
        result=subprocess.run([str(runtime_python),'-I','-B',str((manager or package)/'launch.py'),cmd,*map(str,args)],cwd=work,capture_output=True,text=True)
        if result.returncode:
            try:code=json.loads(result.stdout)['code']
            except (ValueError,KeyError):code='PRIVATE_SYNTHETIC_'+cmd.upper().replace('-','_')+'_FAILED'
            raise SafeError(code)
        return json.loads(result.stdout)
    def init_args(root):
        return ['--backup-directory',backups,'--confirm','INITIALIZE_PRIVATE_LOCAL:'+str(root),'--data-owner-consent',p.CONSENT,'--acknowledge-no-cloud-directory']
    def boot(application,root,build_id=None):
        process=subprocess.Popen([str(runtime_python),'-I','-B',str(package/'launch.py'),'start','--mode','PRIVATE_LOCAL','--app',str(application),'--data',str(root),'--port',str(port)],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
            env=dict(os.environ,OPENAI_API_KEY='ORIGINAL_SYNTHETIC_NOT_A_KEY',PC_CONVERSATION_PROVIDER='ON',PC_HEALTH_BRIDGE='ON',PC_LOCAL_ASR='ON'))
        client=None
        try:
            assert select.select([process.stdout],[],[],15)[0],'READINESS_TIMEOUT'
            first=process.stdout.readline()
            if not first.startswith('Local private runtime:'):
                try:code=json.loads(first).get('code','PRIVATE_START_FAILED')
                except ValueError:code='PRIVATE_START_FAILED'
                raise SafeError(code)
            code=process.stdout.readline().strip().split(': ',1)[1]
            client=httpx.Client(base_url=origin,headers={'Origin':origin,'X-PC-Build':build_id or commit},timeout=10)
            for _ in range(100):
                try:
                    assert client.get('/api/v1/entries').status_code==401
                    response=client.post('/api/v1/auth/unlock',json={'code':code});assert response.status_code==200,'UNLOCK_FAILED'
                    client.headers['X-CSRF-Token']=response.json()['csrf_token'];return process,client
                except httpx.ConnectError:time.sleep(.05)
            raise SafeError('READINESS_TIMEOUT')
        except BaseException:
            if client:client.close()
            process.terminate();process.wait(10);process.stdout.close();raise
    def stop(process,client):
        client.close();process.terminate();process.wait(10);process.stdout.close()
        with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
    def defaults(client):
        status=client.get('/api/v1/status').json()
        assert status['mode']=='PRIVATE_LOCAL' and status['data']=='PRIVATE_PERSONAL' and status['capabilities']==p.PROFILE
        for path in ['ai/mode','conversations','health/import','practices/start','voice/audio','sync/invitations','device/pair']:
            assert client.post('/api/v1/'+path,json={'mode':'ON'}).status_code==403
        assert client.get('/phone/').status_code==403
        return {'status':'PASS','profile':p.PROFILE,'provider_environment_cannot_activate':True}
    try:
        runtime_python,checks['runtime_only']=measured('runtime_copy',lambda:runtime_only_environment(work/'runtime-only'))
        report=measured('private_security_preflight',lambda:command('private-preflight','--package',package,'--manifest-hash',expected,'--app',app,'--data',data,'--backup-directory',backups,'--port',port))
        p.PrivatePreflight.model_validate(report);assert report['status']=='PASS'
        (a.output/'MAC_PREFLIGHT.json').write_text(json.dumps(report,indent=2)+'\n')
        checks['explicit_private_initialization']=measured('initialization',lambda:command('initialize-private','--package',package,'--manifest-hash',expected,'--app',app,'--data',data,*init_args(data)))
        process,client=measured('startup',lambda:boot(app,data))
        ids=[]
        try:
            checks['fresh_defaults']=defaults(client)
            for kind,text,extra in [('daily','ORIGINAL SYNTHETIC · M8C journal',{}),('creative','ORIGINAL SYNTHETIC · M8C creative',{'creative_kind':'idea','creative_meta':{'title':'ORIGINAL SYNTHETIC M8C idea'}}),('daily','ORIGINAL SYNTHETIC · M8C deleted',{})]:
                id=str(uuid4());ids.append(id)
                body={'operation_id':str(uuid4()),'entry_id':id,'base_revision':0,'payload':{'type':kind,'raw_text':text,**extra}}
                assert client.post('/api/v1/entries',json=body).status_code==201
            assert client.patch('/api/v1/entries/'+ids[0],json={'operation_id':str(uuid4()),'base_revision':1,'changes':{'raw_text':'ORIGINAL SYNTHETIC · M8C journal revision'}}).status_code==200
            assert client.request('DELETE','/api/v1/entries/'+ids[2],json={'operation_id':str(uuid4()),'base_revision':1}).status_code==200
            entry=client.get('/api/v1/entries/'+ids[0]).json()
            assert entry['privacy_class']=='PRIVATE_PERSONAL' and entry['provenance_type']=='USER_REPORTED'
            assert client.get('/api/v1/entries',params={'q':'journal revision'}).json()['items']
            assert client.get('/api/v1/creative',params={'q':'M8C creative'}).json()['items']
            checks['journal_edit_search_creative_provenance']={'status':'PASS','content':'ORIGINAL_SYNTHETIC_ONLY','privacy':'PRIVATE_PERSONAL','provenance':'USER_REPORTED'}
            from playwright.sync_api import sync_playwright,expect
            from urllib.parse import urlparse
            os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True);ctx=browser.new_context(viewport={'width':1440,'height':1000})
                external=[];errors=[]
                def route(route):
                    if urlparse(route.request.url).hostname!='127.0.0.1':external.append('NONLOOPBACK_BLOCKED');route.abort()
                    else:route.continue_()
                ctx.route('**/*',route)
                page=ctx.new_page();page.on('pageerror',lambda _:errors.append('PAGE_ERROR'))
                page.goto(origin);expect(page.get_by_text('Локальний приватний пілот · лише цей Mac.',exact=False)).to_be_visible()
                expect(page.get_by_text('Synthetic demo',exact=False)).to_have_count(0)
                page.screenshot(path=str(a.output/'private-unlock-synthetic.png'),full_page=True)
                ctx.add_cookies([{'name':'m1_session','value':client.cookies['m1_session'],'url':origin,'httpOnly':True,'sameSite':'Strict'}]);page.reload()
                expect(page.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()
                expect(page.get_by_role('button',name='Розмова',exact=True)).to_have_count(0)
                expect(page.locator('.voice-disclosure,.journal-tools')).to_have_count(0)
                page.get_by_role('button',name='Додати запис',exact=True).click();page.get_by_label('Текст',exact=True).fill('ORIGINAL SYNTHETIC · M8C browser journal')
                page.get_by_role('button',name='Зберегти на Mac').click();expect(page.get_by_text('ORIGINAL SYNTHETIC · M8C browser journal',exact=True)).to_be_visible()
                page.screenshot(path=str(a.output/'private-journal-synthetic.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(a.output/'private-narrow-synthetic.png'),full_page=True)
                page.get_by_role('button',name='Більше',exact=True).click()
                for label in ['Розмова','Практики','Дані з годинника','Відгук']:expect(page.get_by_role('button',name=label,exact=True)).to_have_count(0)
                page.get_by_role('button',name='Заблокувати',exact=True).click();expect(page.get_by_label('Код розблокування')).to_be_visible()
                assert client.get('/api/v1/entries').status_code==401
                assert not external and not errors
                checks['Chromium']={'status':'PASS','scope':'REFERENCE_MAC_CHROMIUM_NOT_GALAXY','nonloopback_requests':0,'page_errors':0,'private_label':True,'journal_landing':True,'unsupported_controls_hidden':True,'lock':True}
                ctx.close();browser.close()
        finally:stop(process,client)
        process,client=boot(app,data)
        try:
            assert client.get('/api/v1/entries/'+ids[0]).json()['raw_text']=='ORIGINAL SYNTHETIC · M8C journal revision'
            assert len(client.get('/api/v1/entries/'+ids[0]+'/revisions').json()['items'])==1
            assert client.get('/api/v1/entries/'+ids[2]).status_code==410
            checks['restart_durability_auth']={'status':'PASS','new_unlock_required':True,'history_tombstones':True,'defaults':defaults(client)}
        finally:stop(process,client)
        target=backups/'verified private snapshot'
        receipt=measured('private_backup',lambda:command('backup','--mode','PRIVATE_LOCAL','--app',app,'--data',data,'--backup',target))
        metadata=r.verify_backup(target,expected,receipt['backup_manifest_hash'])
        assert metadata['backup_format']==4 and metadata['root_kind']=='PRIVATE_LOCAL' and metadata['security_policy']==p.POLICY
        checks['private_backup']={'status':'PASS','backup_format':4,'protection':'VERIFIED_FILEVAULT_VOLUME_OWNER_ONLY','archive_encryption':'NOT_IMPLEMENTED','producing_manifest_hash':expected,'backup_manifest_hash':receipt['backup_manifest_hash']}
        restored_app,restored=work/'restored app',work/'restored private synthetic data'
        restore_flags=['--mode','PRIVATE_LOCAL','--package',package,'--manifest-hash',expected,'--producer-manifest-hash',expected,'--backup-manifest-hash',receipt['backup_manifest_hash'],'--backup',target,'--app',restored_app,'--data',restored,*init_args(restored)]
        checks['restore']=measured('private_restore',lambda:command('restore',*restore_flags))
        process,client=boot(restored_app,restored)
        try:
            assert client.get('/api/v1/entries/'+ids[0]).json()['raw_text']=='ORIGINAL SYNTHETIC · M8C journal revision'
            assert client.get('/api/v1/entries/'+ids[2]).status_code==410
            checks['restore_restart_defaults']=defaults(client)
        finally:stop(process,client)
        # Failed transaction simulation is a disposable schema10 projection, not an old binary claim.
        with sqlite3.connect(restored/'journal.sqlite3') as c:c.execute('UPDATE vault_meta SET schema_version=10')
        before=r.read_json(restored_app/'active.json')
        try:r.upgrade(package,expected,restored_app,restored,backups/'failed upgrade backup',root_kind='PRIVATE_LOCAL',fail_migration=True);raise AssertionError('FAILURE_NOT_INJECTED')
        except sqlite3.OperationalError:pass
        assert r.read_json(restored_app/'active.json')==before and (restored_app/'upgrade-pending.json').is_file()
        assert r.verify_backup(backups/'failed upgrade backup',expected)['schema_version']==10
        checks['failed_upgrade']={'status':'PASS','scope':'DISPOSABLE_SCHEMA10_TRANSACTION_FAILURE_PROJECTION','backup_verified':True,'pointer_preserved':True,'pending_marker':True}
        rollback_app,rollback_data=work/'rollback app',work/'rollback private synthetic data'
        flags=list(restore_flags);flags[flags.index(restored_app)]=rollback_app;flags[flags.index(restored)]=rollback_data
        flags[flags.index('INITIALIZE_PRIVATE_LOCAL:'+str(restored))]='INITIALIZE_PRIVATE_LOCAL:'+str(rollback_data)
        checks['rollback']=measured('private_rollback',lambda:command('rollback',*flags))
        process,client=boot(rollback_app,rollback_data)
        try:
            assert client.get('/api/v1/entries/'+ids[0]).json()['raw_text']=='ORIGINAL SYNTHETIC · M8C journal revision'
            checks['rollback_restart_defaults']=defaults(client)
        finally:stop(process,client)
        checks['upgrade']=measured('private_upgrade',lambda:command('upgrade','--mode','PRIVATE_LOCAL','--package',package,'--manifest-hash',expected,'--app',app,'--data',data,'--backup',backups/'preupgrade backup'))
        process,client=boot(app,data)
        try:checks['upgrade_restart_defaults']=defaults(client)
        finally:stop(process,client)
        if a.previous_package:
            old=r.package_path(a.previous_package);old_m=r.validate_package(old,r.read_json(old/'release-manifest.json')['manifest_hash'])
            assert old_m['format']==3 and old_m['git_commit']!=commit
            old_app,old_data=work/'old real package app',work/'old private synthetic data'
            command('initialize-private','--package',old,'--manifest-hash',old_m['manifest_hash'],'--app',old_app,'--data',old_data,*init_args(old_data),manager=old)
            process,client=boot(old_app,old_data,old_m['git_commit'])
            try:
                id=str(uuid4());body={'entry_id':id,'operation_id':str(uuid4()),'base_revision':0,'payload':{'type':'daily','raw_text':'ORIGINAL SYNTHETIC genuine cross-release fixture'}}
                assert client.post('/api/v1/entries',json=body).status_code==201
            finally:stop(process,client)
            cross_backup=backups/'genuine preupgrade backup'
            cross=command('upgrade','--mode','PRIVATE_LOCAL','--package',package,'--manifest-hash',expected,'--app',old_app,'--data',old_data,'--backup',cross_backup)
            source=r.verify_backup(cross_backup,expected)['release_provenance']['source_release'];assert source['manifest_hash']==old_m['manifest_hash']
            process,client=boot(old_app,old_data)
            try:assert client.get('/api/v1/entries/'+id).json()['raw_text']=='ORIGINAL SYNTHETIC genuine cross-release fixture';defaults(client)
            finally:stop(process,client)
            old_restore_app,old_restore_data=work/'old rollback app',work/'old rollback private synthetic data'
            command('rollback','--mode','PRIVATE_LOCAL','--package',old,'--manifest-hash',old_m['manifest_hash'],'--producer-manifest-hash',expected,'--backup-manifest-hash',cross['backup_manifest_hash'],'--backup',cross_backup,'--app',old_restore_app,'--data',old_restore_data,*init_args(old_restore_data))
            process,client=boot(old_restore_app,old_restore_data,old_m['git_commit'])
            try:assert client.get('/api/v1/entries/'+id).json()['raw_text']=='ORIGINAL SYNTHETIC genuine cross-release fixture';defaults(client)
            finally:stop(process,client)
            checks['genuine_cross_release']={'status':'PASS','previous_release':old_m['release_id'],'previous_manifest_hash':old_m['manifest_hash'],'new_release':m['release_id'],'new_producer_hash':expected,'backup_source_hash':source['manifest_hash'],'old_application_actual_restart':'PASS'}
        checks['uninstall_keep_data']=command('uninstall','--mode','PRIVATE_LOCAL','--app',app,'--data',data)
        assert data.is_dir() and target.is_dir() and not app.exists();p.validate_root(data,security=True)
        checks['explicit_disposable_private_delete']=command('delete-private-data','--data',data,'--confirm','DELETE_PRIVATE_LOCAL_DATA:'+str(data))
        assert not data.exists() and target.exists()
        checks['actual_private_pilot']='NOT_STARTED';checks['actual_private_root']='NOT_CREATED'
    finally:
        shutil.rmtree(work)
    assert not work.exists()
    result={'status':'PASS','scope':'PRIVATE_LOCAL_RUNTIME_WITH_SYNTHETIC_CONTENT','implementation_sha':commit,'release_id':m['release_id'],'manifest_hash':expected,'runtime_lock_hash':m['runtime_input_hash'],'checks':checks,'timings_ms':timings,'cleanup':'COMPLETE','real_private_data_used':0,'live_provider_calls':0,'system_changes':0,'phone_health_audio_activation':0}
    (a.output/'MAC_LIFECYCLE.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'PILOT_READINESS.json').write_text(json.dumps(p.readiness(report,True),indent=2)+'\n')
    print(json.dumps({'status':'PASS','scope':result['scope'],'release_id':m['release_id'],'MAC_CORE_PILOT':p.readiness(report,True)['MAC_CORE_PILOT'],'cleanup':'COMPLETE'}))

if __name__=='__main__':main()
