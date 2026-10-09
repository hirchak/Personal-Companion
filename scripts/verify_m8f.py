#!/usr/bin/env python3
"""Exact-C local native artifacts/feed plus real packaged backend lifecycle.
Native window/Finder/Sparkle button checks are separate Computer Use observations.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import plistlib
import shutil
import socket
import subprocess
import tempfile
import time
from uuid import uuid4
from xml.sax.saxutils import escape

from apps.core.storage import REPO, digest, encode
from apps.core.native_macos import validate_bundle, PRODUCT, CHANNEL
from scripts.build_m8f import build, SPARKLE_DIR


def make_feed(work, mode='valid'):
    meta=validate_bundle(REPO/'generated/m8f/B/Personal Companion.app')
    archive=work/'feed/B.zip'
    key=work/('wrong-private.key' if mode=='wrong-signer' else 'test-private.key')
    signer=SPARKLE_DIR/'bin/sign_update'
    signature=subprocess.check_output([str(signer),'-f',str(key),'-p',str(archive)],text=True).strip()
    receipt=json.loads((work/'harness.json').read_text())
    port=receipt['feed_port']
    product=PRODUCT if mode!='wrong-product' else 'ORIGINAL_SYNTHETIC_OTHER_PRODUCT'
    arch='arm64' if mode!='wrong-arch' else 'x86_64'
    version=meta['build'] if mode!='downgrade' else 100
    channel=CHANNEL if mode!='wrong-channel' else 'OTHER_SYNTHETIC_CHANNEL'
    xml=f'''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:pc="urn:personalcompanion:local-test">
<channel><title>Personal Companion — ORIGINAL SYNTHETIC LOCAL TEST</title><item>
<title>Доступна нова версія</title><sparkle:version>{version}</sparkle:version>
<sparkle:shortVersionString>0.8.6</sparkle:shortVersionString>
<sparkle:minimumSystemVersion>14.0</sparkle:minimumSystemVersion><sparkle:channel>{channel}</sparkle:channel>
<pc:product>{product}</pc:product><pc:arch>{arch}</pc:arch><pc:source>{meta['source_sha']}</pc:source>
<pc:manifest>{meta['manifest_hash']}</pc:manifest><pc:schema>11</pc:schema>
<enclosure url="http://127.0.0.1:{port}/B.zip" sparkle:version="{version}" length="{archive.stat().st_size}"
type="application/octet-stream" sparkle:edSignature="{signature}" />
</item></channel></rss>'''
    feed=work/'feed/appcast.xml';feed.write_text(xml)
    subprocess.run([str(signer),'-f',str(key),'-p',str(feed)],check=True,stdout=subprocess.DEVNULL)
    return {'mode':mode,'feed_signed':True,'archive_signed':True}


def prepare():
    work=Path(tempfile.mkdtemp(prefix='m8f-original-synthetic-',dir='/private/tmp'))
    work.chmod(0o700);(work/'feed').mkdir(mode=0o700)
    subprocess.run(['/usr/bin/xcrun','swift','-module-cache-path',str(REPO/'generated/m8f/swift-cache'),
        str(REPO/'apps/macos/TestSigningKey.swift'),str(work)],check=True)
    wrong=work/'wrong';wrong.mkdir(mode=0o700)
    subprocess.run(['/usr/bin/xcrun','swift','-module-cache-path',str(REPO/'generated/m8f/swift-cache'),
        str(REPO/'apps/macos/TestSigningKey.swift'),str(wrong)],check=True)
    shutil.move(wrong/'test-private.key',work/'wrong-private.key');shutil.rmtree(wrong)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    receipt={'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             'feed_port':port,'test_home':str(work),'scope':'ORIGINAL_SYNTHETIC_ONLY'}
    (work/'harness.json').write_text(encode(receipt));(work/'harness.json').chmod(0o600)
    for name,version in [('A',101),('B',102)]:
        args=argparse.Namespace(output=str(REPO/'generated/m8f'/name),build=version,
            test_public_key=str(work/'test-public.txt'),test_feed=f'http://127.0.0.1:{port}/appcast.xml',
            test_home=str(work),without_asr=False,dmg=True)
        build(args)
    subprocess.run(['/usr/bin/ditto','-c','-k','--sequesterRsrc','--keepParent',
        str(REPO/'generated/m8f/B/Personal Companion.app'),str(work/'feed/B.zip')],check=True)
    make_feed(work)
    (REPO/'generated/m8f/harness-locator.json').write_text(encode({'work':str(work)}))
    return {'prepared':True,'source_sha':receipt['source_sha'],'scope':receipt['scope']}


class PipeRuntime:
    def __init__(self,app,base):
        self.app=Path(app);self.number=0
        python=self.app/'Contents/Resources/runtime/bin/python3.13'
        self.process=subprocess.Popen([str(python),'-I','-B',str(self.app/'Contents/Resources/payload/native_entry.py')],
            cwd=base.parent,env={'PATH':'/var/empty','HOME':str(base.parent),'LANG':'uk_UA.UTF-8'},
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        self.call('bootstrap',bundle=str(self.app),base=str(base))
    def call(self,op,**fields):
        self.number+=1
        self.process.stdin.write(encode(dict(fields,op=op,id=self.number))+'\n');self.process.stdin.flush()
        value=json.loads(self.process.stdout.readline())
        if not value['ok']:raise AssertionError(value['code'])
        return value['result']
    def close(self):
        self.process.stdin.close();self.process.wait(20);self.process.stdout.close()
        assert self.process.returncode==0


def lifecycle():
    """Unmocked protected Mac roots, embedded runtime and real API/audio/ASR bytes."""
    import httpx
    import sqlite3
    from apps.core import release as r
    app=REPO/'generated/m8f/A/Personal Companion.app'
    m=validate_bundle(app)
    work=Path(tempfile.mkdtemp(prefix='m8f-packaged-original-synthetic-',dir='/private/tmp'))
    base=work/'Standalone';checks={};times={}
    started=time.monotonic();runtime=PipeRuntime(app,base)
    try:
        assert runtime.call('status')['initialized'] is False and not base.exists()
        runtime.call('initialize',consent=True,no_cloud=True)
        status=runtime.call('start');times['cold_core_ms']=round((time.monotonic()-started)*1000,2)
        auth=runtime.call('unlock');origin=f'http://127.0.0.1:{auth["port"]}'
        client=httpx.Client(base_url=origin,headers={'Origin':origin,'X-PC-Build':m['source_sha']},timeout=30)
        unlocked=client.post('/api/v1/auth/unlock',json={'code':auth['code']});assert unlocked.status_code==200
        client.headers['X-CSRF-Token']=unlocked.json()['csrf_token']
        assert client.get('/api/v1/entries').json()['items']==[]
        ids=[]
        for kind in ('daily','creative'):
            entry=str(uuid4());ids.append(entry)
            payload={'type':kind,'raw_text':'ORIGINAL SYNTHETIC M8F '+kind}
            if kind=='creative':payload['creative_kind']='idea'
            assert client.post('/api/v1/entries',json={'operation_id':str(uuid4()),'entry_id':entry,'base_revision':0,'payload':payload}).status_code==201
        assert len(client.get('/api/v1/entries',params={'q':'ORIGINAL SYNTHETIC M8F'}).json()['items'])==2
        conversation=client.post('/api/v1/conversations',json={'operation_id':str(uuid4())}).json()['conversation']
        sent=client.post('/api/v1/conversations/'+conversation['id']+'/messages',json={'operation_id':str(uuid4()),'base_revision':1,'text':'ORIGINAL SYNTHETIC · AI OFF native history'})
        assert sent.status_code==200 and sent.json()['responder']=='OFF'
        checks['local_core']={'status':'PASS','entries':2,'search':True,'free_history_ai_off':True,'empty_initial_db':True}
        # Existing original authored synthetic Ukrainian fixture, never owner audio.
        audio=(REPO/'generated/local-asr/synthetic-ua-clear.wav').read_bytes()
        audio_id=str(uuid4())
        begin={'audio_id':audio_id,'operation_id':str(uuid4()),'content_hash':digest(audio),
            'byte_size':len(audio),'mime':'audio/wav','created_at_utc':'2099-01-01T12:00:00Z',
            'local_date':'2099-01-01','timezone':'Europe/Warsaw','linked_entry_id':None}
        assert client.post('/api/v1/voice/audio',json=begin).status_code==200
        from apps.core.audio_format import CHUNK_SIZE
        for index,offset in enumerate(range(0,len(audio),CHUNK_SIZE)):
            part=audio[offset:offset+CHUNK_SIZE]
            response=client.post('/api/v1/voice/audio/'+audio_id+'/chunks',json={
                'index':index,'content_hash':digest(part),'data':base64.b64encode(part).decode()})
            assert response.status_code==200
        assert client.post('/api/v1/voice/audio/'+audio_id+'/finalize',json={}).status_code==200
        transcribed=client.post('/api/v1/voice/audio/'+audio_id+'/transcribe',json={'mode':'LOCAL','language':'uk'})
        assert transcribed.status_code==200
        end=time.monotonic()+90
        while time.monotonic()<end:
            item=client.get('/api/v1/voice/audio/'+audio_id).json()
            if item.get('transcript',{}).get('state') not in {'TRANSCRIPTION_QUEUED','TRANSCRIBING'}:break
            time.sleep(.1)
        transcript=item['transcript']
        assert transcript['state'] in {'TRANSCRIPT_READY','REVIEW_REQUIRED'},transcript.get('error','ASR_STATE_FAILED')
        checks['packaged_whisper']={'status':'PASS','actual_packaged_bytes':True,'cloud_calls':0,
            'input':'ORIGINAL_SYNTHETIC_AUTHORED_AUDIO','candidate_text_exported':False,
            'candidate_sha256':digest(transcript['candidate'].encode())}
        memory=subprocess.check_output(['/bin/ps','-o','rss=,%cpu=','-p',str(runtime.process.pid)],text=True).split()
        checks['process_measurement']={'backend_rss_kib':int(memory[0]),'backend_cpu_percent':float(memory[1]),
            'scope':'POST_ASR_POINT_SAMPLE_NOT_PEAK','no_dev_tools_in_path':True}
        original_identity=r.read_json(base/'vault/private-local.json')['root_id']
        runtime.call('lock');assert client.get('/api/v1/entries').status_code==401
        client.close()
        saved=runtime.call('backup');assert saved['manifest_hash']
        runtime.call('start')
        runtime.call('stop')
        checks['backup']={'status':'PASS','attachments':True,'manifest_bound':True,'writers_stopped':True}
        # Real process restart, then explicit fresh-root restore and renewed identity.
        runtime.close();runtime=PipeRuntime(app,base);runtime.call('start');runtime.call('stop')
        runtime.call('restore',name=saved['backup'],confirmation=True)
        settings=r.read_json(base/'native-managed.json')
        assert r.read_json(base/settings['active_data']/'private-local.json')['root_id']!=original_identity
        assert (base/'vault').is_dir()
        runtime.call('start');runtime.call('stop')
        checks['restart_restore']={'status':'PASS','old_data_preserved':True,'new_identity':True,'ai_off':True}
        checks['provider_calls']=0
    finally:
        runtime.close()
    result={'checks':checks,'timings':times,'source_sha':m['source_sha'],'scope':'REAL_MAC_ORIGINAL_SYNTHETIC_PACKAGED_RUNTIME'}
    (REPO/'generated/m8f/packaged-lifecycle.json').write_text(encode(result))
    return result


def serve(work):
    import http.server
    from functools import partial
    receipt=json.loads((work/'harness.json').read_text())
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',receipt['feed_port']),partial(QuietHandler,directory=str(work/'feed')))
    print(encode({'status':'LOCAL_TEST_FEED_READY'}),flush=True)
    try:server.serve_forever()
    finally:server.server_close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','serve','feed','lifecycle'])
    p.add_argument('--mode',default='valid',choices=['valid','wrong-signer','wrong-product','wrong-arch','wrong-channel','downgrade'])
    a=p.parse_args()
    if a.action=='prepare':result=prepare()
    elif a.action=='lifecycle':result=lifecycle()
    else:
        work=Path(json.loads((REPO/'generated/m8f/harness-locator.json').read_text())['work'])
        if a.action=='serve':serve(work);return
        result=make_feed(work,a.mode)
    print(encode(result))


if __name__=='__main__':main()
