import json
import sys

import pytest

from apps.core.codex_conversation_provider import CodexConversationProvider
from apps.core.storage import SafeError
from scripts.m8e_q01_preflight import preflight


def fake_provider(tmp_path,scenario):
    marker=tmp_path/'ORIGINAL_SYNTHETIC_METHODS.jsonl'
    script=tmp_path/'ORIGINAL_SYNTHETIC_RPC.py'
    script.write_text('''import json,sys,time
scenario=SCENARIO
marker=MARKER
for line in sys.stdin:
 request=json.loads(line);method=request['method'];identifier=request.get('id')
 with open(marker,'a') as output:output.write(json.dumps({'method':method,'params':request.get('params') if method=='account/read' else None})+'\\n')
 if method=='initialized':continue
 result={}
 if method=='initialize' and scenario=='null_initialize':result=None
 elif method=='account/read':
  if scenario=='timeout':time.sleep(1)
  result={'account':None if scenario=='missing_auth' else {'type':'apiKey' if scenario=='api_key' else 'chatgpt','email':'ORIGINAL_SYNTHETIC_ACCOUNT_SENTINEL'}}
 elif method=='model/list':
  result={'data':[{'model':m,'supportedReasoningEfforts':[{'reasoningEffort':e} for e in (['low'] if scenario=='unsupported_effort' else ['high','max'])]} for m in (['gpt-6-luna'] if scenario=='missing_model' else ['gpt-6-luna','gpt-6.1-sol'])]}
  if scenario=='unverifiable_effort':result['data'][0].pop('supportedReasoningEfforts')
 elif method=='account/rateLimits/read':
  result={'accountId':'ORIGINAL_SYNTHETIC_ACCOUNT_SENTINEL','ordinaryUsageAllowed':None if scenario=='unknown_included' else True,'rateLimits':{'planType':'pro','credits':{'hasCredits':scenario=='paid_credits','unlimited':False,'balance':'1' if scenario=='paid_credits' else '0'},'secondary':{'usedPercent':20}}}
 elif method not in {'initialize','account/read','model/list','account/rateLimits/read'}:
  raise RuntimeError('FORBIDDEN_METHOD')
 if method=='account/read' and scenario=='rpc_error':response={'id':identifier,'error':{'code':-32603,'message':'ORIGINAL_SYNTHETIC_RAW_RPC_SECRET'}}
 else:response={'id':identifier,'result':result}
 print(json.dumps(response),flush=True)
'''.replace('SCENARIO',repr(scenario)).replace('MARKER',repr(str(marker))))
    class Fixture:
        supported_settings=staticmethod(CodexConversationProvider.supported_settings)
        def spec(self,work):return {'args':[sys.executable,'-I','-B',str(script)],'cwd':work,'env':{}}
        def stop_transport(self):pass
    return Fixture(),marker


def test_metadata_gate_projects_only_safe_fields_and_never_starts_inference(tmp_path):
    provider,marker=fake_provider(tmp_path,'success')
    receipt=preflight(provider,timeout=2)
    assert receipt['status']=='PASS' and receipt['inference_attempts']==0
    assert not receipt['thread_started'] and not receipt['turn_started']
    assert receipt['verification_source']=='INJECTED_TEST_PROVIDER_NOT_LIVE'
    assert 'SENTINEL' not in json.dumps(receipt)
    methods=[json.loads(line) for line in marker.read_text().splitlines()]
    assert [r['method'] for r in methods]==['initialize','initialized','account/read','model/list','account/rateLimits/read']
    assert methods[2]['params']=={'refreshToken':False}


@pytest.mark.parametrize('scenario,code',[
    ('null_initialize','Q01_PROVIDER_PROTOCOL_INVALID'),
    ('missing_auth','EXISTING_CHATGPT_AUTH_REQUIRED'),
    ('api_key','EXISTING_CHATGPT_AUTH_REQUIRED'),
    ('missing_model','MODEL_CAPABILITY_UNVERIFIED'),
    ('unsupported_effort','PROVIDER_EFFORT_UNSUPPORTED'),
    ('unverifiable_effort','PRIVATE_PROVIDER_PROFILE_UNVERIFIED'),
    ('unknown_included','Q01_INCLUDED_USAGE_UNVERIFIED'),
    ('paid_credits','Q01_NO_PURCHASED_CREDITS_UNVERIFIED'),
    ('rpc_error','Q01_PROVIDER_RPC_FAILED'),
    ('timeout','Q01_PROVIDER_TIMEOUT'),
])
def test_failed_metadata_never_grants_inference_or_leaks_account_values(tmp_path,scenario,code):
    provider,marker=fake_provider(tmp_path,scenario)
    with pytest.raises(SafeError) as failure:preflight(provider,timeout=.25 if scenario=='timeout' else 2)
    assert failure.value.code==code and 'SENTINEL' not in str(failure.value) and 'SECRET' not in str(failure.value)
    assert not any(json.loads(line)['method'] in {'thread/start','turn/start'} for line in marker.read_text().splitlines())
