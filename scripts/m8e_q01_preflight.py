"""Metadata-only Q01 route/funding gate; no thread, turn, prompts or settings writes."""
import argparse
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import time

from apps.core.local_private_provider import PrivateCodexConversationProvider
from apps.core.storage import REPO, SafeError, encode
from scripts.m8e_q01_budget import permission, included_usage_gate, PROFILES

METHODS=frozenset({'initialize','account/read','model/list','account/rateLimits/read'})


class NoInferenceBudget:
    def reserve(self,*args):raise SafeError('Q01_PREFLIGHT_INFERENCE_FORBIDDEN',403)
    def finish(self,*args):raise SafeError('Q01_PREFLIGHT_INFERENCE_FORBIDDEN',403)


class MetadataRPC:
    def __init__(self,process,timeout=30):
        self.process=process
        self.selector=selectors.DefaultSelector()
        self.selector.register(process.stdout,selectors.EVENT_READ)
        self.buffer=bytearray()
        self.total=0
        self.deadline=time.monotonic()+timeout
        self.identifier=0
        self.methods=[]

    def close(self):self.selector.close()

    def send(self,message):
        self.process.stdin.write((encode(message)+'\n').encode())
        self.process.stdin.flush()

    def exchange(self,method,params):
        if method not in METHODS:raise SafeError('Q01_PREFLIGHT_METHOD_DENIED',403)
        self.identifier+=1
        identifier=self.identifier
        self.methods.append(method)
        self.send({'id':identifier,'method':method,'params':params})
        while time.monotonic()<self.deadline:
            if b'\n' in self.buffer:
                line,rest=self.buffer.split(b'\n',1);self.buffer=bytearray(rest)
                try:message=json.loads(line)
                except (ValueError,UnicodeError):raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID') from None
                if not isinstance(message,dict):raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                if 'method' in message:
                    if 'id' in message or not isinstance(message['method'],str):raise SafeError('Q01_PROVIDER_TOOL_REQUEST_DENIED')
                    continue
                if type(message.get('id')) is not int or message['id']!=identifier:
                    raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                if ('result' in message)==('error' in message):raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                if 'error' in message:
                    error=message['error']
                    if not isinstance(error,dict) or type(error.get('code')) is not int or not isinstance(error.get('message'),str):
                        raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                    raise SafeError('Q01_PROVIDER_RPC_FAILED')
                result=message['result']
                if not isinstance(result,dict):raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                return result
            if self.process.poll() is not None:raise SafeError('Q01_PROVIDER_PROCESS_FAILED')
            if self.selector.select(.05):
                chunk=os.read(self.process.stdout.fileno(),8192)
                self.total+=len(chunk)
                if not chunk or self.total>524288:raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
                self.buffer.extend(chunk)
        raise SafeError('Q01_PROVIDER_TIMEOUT')


def preflight(provider=None,timeout=30):
    authorization_hash=permission()
    project=json.loads((REPO/'.project/project.json').read_text())
    if project['permissions']['live_provider_calls'] is not False or project['permissions']['access_real_user_data'] is not False:
        raise SafeError('Q01_GLOBAL_PERMISSION_DRIFT',403)
    provider=provider or PrivateCodexConversationProvider(model='gpt-6-luna',effort='high',budget=NoInferenceBudget())
    work=Path(tempfile.mkdtemp(prefix='m8e-q01-synthetic-preflight-',dir=Path(tempfile.gettempdir()).resolve()))
    process=rpc=None
    try:
        process=subprocess.Popen(**provider.spec(work),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL,start_new_session=True)
        rpc=MetadataRPC(process,timeout)
        rpc.exchange('initialize',{'clientInfo':{'name':'personal_companion_q01_synthetic_metadata','version':'0.1.0'},'capabilities':{'experimentalApi':True}})
        rpc.send({'method':'initialized','params':{}})
        account=rpc.exchange('account/read',{'refreshToken':False})
        if 'account' not in account:raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
        identity=account['account']
        if identity is None:raise SafeError('EXISTING_CHATGPT_AUTH_REQUIRED',403)
        if not isinstance(identity,dict) or not isinstance(identity.get('type'),str) or not identity['type'].strip():
            raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
        if identity['type']!='chatgpt':raise SafeError('EXISTING_CHATGPT_AUTH_REQUIRED',403)
        del account,identity
        catalog=rpc.exchange('model/list',{'includeHidden':False})
        if not isinstance(catalog.get('data'),list) or any(not isinstance(item,dict) for item in catalog['data']):
            raise SafeError('Q01_PROVIDER_PROTOCOL_INVALID')
        capabilities={}
        for name,(_,model,effort) in PROFILES.items():
            matches=[item for item in catalog['data'] if item.get('model')==model or item.get('id')==model]
            if len(matches)!=1:raise SafeError('MODEL_CAPABILITY_UNVERIFIED',403)
            settings_field=matches[0].get('supportedReasoningEfforts')
            if not isinstance(settings_field,list) or any(not isinstance(item,dict) or not isinstance(item.get('reasoningEffort'),str) for item in settings_field):
                raise SafeError('PRIVATE_PROVIDER_PROFILE_UNVERIFIED',403)
            settings=provider.supported_settings(catalog,model)
            if effort not in settings:raise SafeError('PROVIDER_EFFORT_UNSUPPORTED',403)
            capabilities[name]={'model':model,'effort':effort,'verified':True}
        del catalog
        limits=rpc.exchange('account/rateLimits/read',{})
        funding={name:included_usage_gate(limits,model) for name,(_,model,_) in PROFILES.items()}
        del limits
        return {'status':'PASS','permission_sha256':authorization_hash,'profiles':capabilities,'funding':funding,
                'verification_source':'EXISTING_SDK_METADATA' if type(provider) is PrivateCodexConversationProvider else 'INJECTED_TEST_PROVIDER_NOT_LIVE',
                'methods':rpc.methods,'inference_attempts':0,'thread_started':False,'turn_started':False,
                'account_values_retained':False,'settings_changed':False,
                'observed_at_unix':time.time(),'observed_at_monotonic':time.monotonic()}
    finally:
        if rpc:rpc.close()
        if process:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=2)
            process.stdin.close();process.stdout.close()
        provider.stop_transport()
        shutil.rmtree(work)


SAFE_CODES=frozenset({'Q01_INCLUDED_USAGE_UNVERIFIED','Q01_INCLUDED_USAGE_EXHAUSTED',
    'Q01_BILLING_METADATA_INVALID','Q01_INCLUDED_PLAN_UNVERIFIED','Q01_APPLICABLE_QUOTA_UNVERIFIED',
    'Q01_NO_PURCHASED_CREDITS_UNVERIFIED','Q01_PROVIDER_PROTOCOL_INVALID','Q01_PROVIDER_RPC_FAILED',
    'Q01_PROVIDER_TIMEOUT','Q01_PROVIDER_PROCESS_FAILED','Q01_PROVIDER_TOOL_REQUEST_DENIED',
    'EXISTING_CHATGPT_AUTH_REQUIRED','MODEL_CAPABILITY_UNVERIFIED','PRIVATE_PROVIDER_PROFILE_UNVERIFIED','PROVIDER_EFFORT_UNSUPPORTED',
    'Q01_GLOBAL_PERMISSION_DRIFT','Q01_PERMISSION_REQUIRED','Q01_SCOPE_DENIED'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=REPO/'generated/m8e-q01/preflight.json')
    args=parser.parse_args()
    try:result=preflight()
    except Exception as error:
        code=getattr(error,'code',None)
        result={'status':'LIVE_BLOCKED','code':code if code in SAFE_CODES else 'Q01_ROUTE_UNVERIFIED',
                'inference_attempts':0,'thread_started':False,'turn_started':False,'account_values_retained':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
