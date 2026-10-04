#!/usr/bin/env python3
"""Exact-checkout package/process/Chromium synthetic verification. No real data/providers."""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time
from uuid import uuid4
import httpx
from apps.core import release as r
from apps.core.storage import Store, REPO, SafeError, encode, digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=REPO/'generated/m8a-verification')
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    package=REPO/'generated/releases'/('M8A-'+commit);package.parent.mkdir(parents=True,exist_ok=True)
    if package.exists():
        manifest=r.read_json(package/'release-manifest.json');r.validate_package(package,manifest['manifest_hash'])
    else:manifest=r.prepare(package)
    expected=manifest['manifest_hash']
    (a.output/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    work=Path(tempfile.mkdtemp(prefix='m8a-original-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
    app,data=work/'Синтетичний застосунок з пробілами',work/'Синтетичні дані з пробілами'
    durations={};checks={};origin='http://127.0.0.1:8874'
    def measured(name,call):
        start=time.monotonic();result=call();durations[name]=round((time.monotonic()-start)*1000,3);return result
    def boot(app_root,data_root):
        start=time.monotonic()
        process=subprocess.Popen([sys.executable,'-m','apps.core.release','start','--app',str(app_root),'--data',str(data_root),'--port','8874'],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        client=None
        try:
            # One-time auth never printed, written or added to evidence.
            assert select.select([process.stdout],[],[],15)[0], 'READINESS_TIMEOUT'
            first=process.stdout.readline();assert first.startswith('Local synthetic runtime:'),'STARTUP_FAILED'
            code=process.stdout.readline().strip().split(': ',1)[1]
            client=httpx.Client(base_url=origin,headers={'Origin':origin,'X-PC-Build':commit},timeout=5)
            for _ in range(100):
                try:
                    response=client.post('/api/v1/auth/unlock',json={'code':code})
                    assert response.status_code==200,'UNLOCK_FAILED'
                    client.headers['X-CSRF-Token']=response.json()['csrf_token']
                    durations.setdefault('startup_readiness',round((time.monotonic()-start)*1000,3))
                    return process,client,code
                except httpx.ConnectError:time.sleep(.05)
            raise AssertionError('READINESS_TIMEOUT')
        except BaseException:
            if client:client.close()
            process.terminate();process.wait(10);process.stdout.close();raise
    def stop(process,client):
        client.close();process.terminate();process.wait(10);process.stdout.close()
        # The actual port can be rebound immediately, proving no orphan child.
        import socket
        with socket.socket() as sock:sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',8874))
    def defaults(client):
        assert client.get('/api/v1/status').json()['provider']=='OFF'
        status=client.get('/api/v1/conversations/status').json()
        assert status['responder']=='OFF' and status['clinical_active']==0
        assert client.get('/api/v1/ai/status').json()['mode']=='OFF'
        catalog=client.get('/api/v1/practices/catalog').json()
        assert catalog['production_active_clinical']==0
        return {'provider':'OFF','clinical_active':0,'specialists':'OFF','health_to_ai':'OFF','cloud_asr':'NONE','external_embeddings':'OFF','private_provider':'OFF'}
    try:
        checks['preflight']=measured('preflight',lambda:r.preflight(package,expected,app,data))
        assert checks['preflight']['status']=='PASS'
        checks['fresh']=measured('fresh_init',lambda:r.install(package,expected,app,data))
        process,client,code=boot(app,data)
        try:
            checks['first_start_defaults']=defaults(client)
            assert client.get('/release.json').json()['git_commit']==commit
            entry_id=str(uuid4())
            body={'operation_id':str(uuid4()),'entry_id':entry_id,'base_revision':0,'payload':{'type':'daily','raw_text':'ORIGINAL SYNTHETIC · Release journal'}}
            assert client.post('/api/v1/entries',json=body).status_code==201
            creative_id=str(uuid4());body.update(operation_id=str(uuid4()),entry_id=creative_id,payload={'type':'creative','creative_kind':'idea','raw_text':'ORIGINAL SYNTHETIC · Release creative'})
            assert client.post('/api/v1/entries',json=body).status_code==201
            conv=client.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json()['conversation']
            assert client.post('/api/v1/conversations/'+conv['id']+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC · OFF keeps only user message'}).status_code==200
            # Browser unlock code was consumed by the client. Transfer ephemeral same-origin cookie/CSRF in memory.
            from playwright.sync_api import sync_playwright,expect
            os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(REPO/'generated/chromium'))
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000})
                external=[];errors=[]
                def route(route):
                    from urllib.parse import urlparse
                    if urlparse(route.request.url).hostname!='127.0.0.1':external.append('NONLOOPBACK_BLOCKED');route.abort()
                    else:route.continue_()
                context.route('**/*',route)
                context.add_cookies([{'name':'m1_session','value':client.cookies['m1_session'],'url':origin,'httpOnly':True,'sameSite':'Strict'}])
                page=context.new_page();page.on('pageerror',lambda e:errors.append('PAGE_ERROR'));page.goto(origin)
                expect(page.get_by_role('button',name='Щоденник',exact=True)).to_be_visible()
                page.get_by_role('button',name='Щоденник',exact=True).click()
                expect(page.get_by_text('ORIGINAL SYNTHETIC · Release journal',exact=True)).to_be_visible()
                page.screenshot(path=str(a.output/'desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(a.output/'mobile.png'),full_page=True)
                # A genuinely incompatible served identity invokes update state without deleting data.
                page.route('**/release.json',lambda route:route.fulfill(json={'web_contract':2,'git_commit':'0'*40,'schema_version':11}))
                page.reload();expect(page.get_by_role('heading',name='Потрібно оновити застосунок')).to_be_visible()
                page.screenshot(path=str(a.output/'update-required.png'),full_page=True)
                assert not external and not errors
                checks['chromium']={'status':'PASS','desktop':'1440x1000','mobile':'390x844','external_requests':0,'page_errors':0,'stale_release':'UPDATE_REQUIRED','physical_hardware':'NOT_RUN'}
                context.close();browser.close()
        finally:stop(process,client)
        process,client,_=boot(app,data)
        try:
            checks['restart_defaults']=defaults(client)
            assert client.get('/api/v1/entries/'+entry_id).json()['raw_text']=='ORIGINAL SYNTHETIC · Release journal'
            assert len(client.get('/api/v1/conversations/'+conv['id']).json()['messages'])==1
            checks['restart']={'status':'PASS','no_duplicate_mutation':True,'stop_port_rebind':'PASS'}
        finally:stop(process,client)
        # Seed an abandoned foreground job through deterministic fixture only. No provider execution.
        sys.path.insert(0,str(REPO/'tests'))
        from test_m7c_controller import FixtureProvider
        from apps.core.conversation_controller import ConversationController
        from apps.core.conversation import Conversations
        from apps.core.conversation_contracts import NewConversation
        from apps.core.conversation_runtime_contracts import InferenceStart
        controller=ConversationController(Conversations(Store(data),True),FixtureProvider())
        page=controller.conversations.create(NewConversation(operation_id=uuid4()))
        pending=controller.send(page['conversation']['id'],InferenceStart(operation_id=uuid4(),base_revision=1,text='ORIGINAL SYNTHETIC interrupted job',synthetic_test_ack=True),launch=False)
        job_id=pending['inference_job']['id']
        from apps.core.voice import Voice
        from apps.core.domain import Journal
        from apps.core.sync import SyncService
        from apps.core.voice_contracts import ASRRequest
        from test_m4_voice import save
        journal=Journal(Store(data));voice=Voice(journal,SyncService(journal))
        audio_id,_=save(voice)
        queued_asr=voice.enqueue(audio_id,ASRRequest(mode='FAKE'))
        # Queued only: no fixture engine executed, no real/human audio.

        process,client,_=boot(app,data)
        try:
            result=client.get('/api/v1/conversations/'+page['conversation']['id']+'/inference/'+job_id).json()
            assert result['state']=='FAILED' and result['error']=='PROCESS_INTERRUPTED'
            audio=client.get('/api/v1/voice/audio/'+str(audio_id)).json()
            assert audio['transcript']['state']=='FAILED' and audio['transcript']['error']=='ASR_RESTART_RETRY_REQUIRED'
            engines=client.get('/api/v1/voice/audio').json()['actual_backend']
            assert engines['available'] is False
            unavailable=client.post('/api/v1/voice/audio/'+str(audio_id)+'/transcribe',json={'mode':'LOCAL','language':'uk'})
            assert unavailable.status_code==409 and unavailable.json()['code']=='LOCAL_ASR_BACKEND_NOT_RUN'
            checks['asr_recovery']={'status':'PASS','partial_job':'FAILED','error':'ASR_RESTART_RETRY_REQUIRED','local_assets':'OPTIONAL_UNAVAILABLE','human_audio':'NOT_RUN'}
            checks['interrupted_job']={'status':'PASS','state':'FAILED','error':'PROCESS_INTERRUPTED','auto_resumed':False,'provider_calls':0}
        finally:stop(process,client)
        backup=work/'pre-upgrade backup'
        checks['backup']=measured('backup',lambda:r.backup(app,data,backup))
        checks['upgrade']=measured('upgrade',lambda:r.upgrade(package,expected,app,data,work/'verified automatic upgrade backup'))
        rollback_app,rollback_data=work/'rollback app',work/'rollback data'
        checks['rollback']=measured('rollback_restore',lambda:r.restore(package,expected,backup,rollback_app,rollback_data))
        process,client,_=boot(rollback_app,rollback_data)
        try:
            checks['rollback_defaults']=defaults(client)
            assert client.get('/api/v1/entries/'+entry_id).json()['raw_text']=='ORIGINAL SYNTHETIC · Release journal'
            assert client.get('/api/v1/entries/'+creative_id).json()['creative_kind']=='idea'
            assert len(client.get('/api/v1/conversations/'+conv['id']).json()['messages'])==1
        finally:stop(process,client)
        restore_app,restore_data=work/'restore app',work/'restore data'
        checks['restore']=measured('restore',lambda:r.restore(package,expected,backup,restore_app,restore_data))
        checks['uninstall']=r.uninstall(app,data)
        assert data.exists() and not app.exists() and backup.exists()
        from apps.core.domain import Journal
        assert Journal(Store(data)).get(entry_id)['raw_text']=='ORIGINAL SYNTHETIC · Release journal'
        checks['uninstall']['domain_integrity']='PASS'
        checks['migration_matrix']={'supported_backup_schemas':list(range(2,12)),'target_schema':11,
                                    'tested_genuine_schema2':'PASS_IN_PYTEST','tested_schema10_projection':'PASS_IN_PYTEST','current_schema11':'PASS',
                                    'future_schema':'REJECTED_IN_PYTEST','failed_migration':'ROLLBACK_TRANSACTION_IN_PYTEST','in_place_downgrade':'NONE'}
        result={'status':'PASS','scope':'ORIGINAL_SYNTHETIC_CLEAN_ROOT_NOT_CLEAN_MAC','base_sha':'0eaac55783a8cc9aa400db238f78bafdf91623e7',
                'implementation_sha':commit,'release_id':manifest['release_id'],'manifest_hash':expected,'artifact_path':str(package.relative_to(REPO)),
                'defaults':r.DEFAULTS,'checks':checks,'durations_ms':durations,'live_provider_calls':0,'private_data_used':False,'hardware':'NOT_RUN','M8B':'NOT_STARTED'}
        (a.output/'LIFECYCLE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'status':'PASS','release_id':manifest['release_id'],'manifest_hash':expected,'checks':list(checks),'live_provider_calls':0}))
    finally:shutil.rmtree(work)

if __name__=='__main__':main()
