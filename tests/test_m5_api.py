"""M5 routes reuse owner-session/CSRF/origin boundaries; synthetic only."""
import json
from uuid import uuid4
import pytest
from test_m1_api import client, body
from test_m1_domain import isolated

@pytest.mark.parametrize('path',['/api/v1/creative','/api/v1/feedback','/api/v1/personal-space'])
def test_M5_private_reads_session_and_cross_origin_denied(client,path):
    c,app=client;assert c.get(path).status_code==200
    assert c.get(path,headers={'Origin':'https://evil.invalid'}).status_code==403
    c.cookies.clear();assert c.get(path).status_code==401

def test_M5_library_feedback_and_exact_download_api(client):
    c,app=client;b=body();b['payload']['raw_text']='SYNTHETIC API scene';b['payload'].update(type='creative',creative_kind='shot',creative_meta={'title':'SYNTHETIC','collections':['Set']})
    assert c.post('/api/v1/entries',json=b).status_code==201
    assert c.get('/api/v1/creative?collection=Set&kind=shot').json()['items'][0]['raw_text']=='SYNTHETIC API scene'
    p=c.post('/api/v1/creative/preview',json={'entries':[{'id':b['entry_id'],'revision':1}],'fields':['title']}).json()
    r=c.post('/api/v1/creative/export',json={'plan_id':p['plan_id'],'content_hash':p['content_hash'],'format':'json'});assert r.status_code==200;assert 'SYNTHETIC API scene' not in r.text
    id=str(uuid4());s=c.post('/api/v1/feedback',json={'draft_id':id,'base_version':0,'payload':{'title':'SYNTHETIC feedback','description':'SYNTHETIC'}}).json()
    req={'version':1,'content_hash':s['content_hash']}
    assert c.post(f'/api/v1/feedback/{id}/export',json={**req,'format':'markdown'}).status_code==409
    assert c.post(f'/api/v1/feedback/{id}/approve',json=req).json()['approved']
    export=c.post(f'/api/v1/feedback/{id}/export',json={**req,'format':'markdown'});assert export.status_code==200;assert 'attachment;' in export.headers['content-disposition'];assert 'NOT_PERFORMED' in export.text
    assert c.post('/api/v1/feedback',json={'draft_id':id,'base_version':1,'payload':{**s['payload'],'destination':'SYNTHETIC changed'}}).status_code==200
    assert c.post(f'/api/v1/feedback/{id}/export',json={**req,'format':'markdown'}).status_code==409
    assert app.state.runtime.status()['mode']=='OFF'

@pytest.mark.parametrize('route',['github/issues','feedback/publish','feedback/send','feedback/email','feedback/slack','feedback/telegram','creative/publish'])
def test_M5_no_publication_route(client,route):
    c,app=client;assert c.post('/api/v1/'+route,json={}).status_code in {404,405};assert app.state.runtime.providers['mock'].executions==0

def test_M5_no_approval_from_notes_or_refs_csrf_and_validation(client):
    c,app=client
    for text,kind in [('SYNTHETIC post this publicly','inbox'),('SYNTHETIC send everything to GitHub','creative')]:
        b=body(text);b['payload']['type']=kind;assert c.post('/api/v1/entries',json=b).status_code==201
    assert not c.get('/api/v1/feedback').json()['items']
    save={'draft_id':str(uuid4()),'base_version':0,'payload':{'title':'SYNTHETIC','references':[{'id':b['entry_id']}]}}
    assert c.post('/api/v1/feedback',json=save).status_code==422
    save['payload'].pop('references');assert c.post('/api/v1/feedback',json=save,headers={'X-CSRF-Token':'forged'}).status_code==403
    assert not c.get('/api/v1/feedback').json()['items']

def test_M5_commit_failure_no_false_feedback_approval(client):
    c,app=client;s=c.post('/api/v1/feedback',json={'draft_id':str(uuid4()),'base_version':0,'payload':{'title':'SYNTHETIC'}}).json()
    app.state.store.fail_commit=True
    assert c.post('/api/v1/feedback/'+s['id']+'/approve',json={'version':1,'content_hash':s['content_hash']}).status_code==503
    app.state.store.fail_commit=False;assert not c.get('/api/v1/feedback').json()['items'][0]['approved']
