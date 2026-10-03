"""Fixed first-party app-server RPC; existing ChatGPT auth stays inside Codex.

No credential extraction, developer workspace roots, MCP/tool approvals, persistent threads or fallback.
The CLI's host working-agreement policy is an explicitly recorded client limitation, not application data.
"""
import os,json,time,selectors,signal,subprocess,tempfile,shutil
from pathlib import Path
from uuid import uuid4
from .storage import SafeError,encode,REPO,digest
from .live_evaluation_budget import LiveEvaluationBudget

DISABLED_FEATURES=('shell_tool','unified_exec','code_mode_host','apps','plugins','multi_agent','view_image','computer_use','browser_use','hooks','memories','workspace_dependencies','skill_search','sleep_tool','daemon_auto_start','unbounded_connection_retries')
ALLOWED_MODELS=('gpt-6.1-sol','gpt-6-sol','gpt-6-luna')

class CodexConversationProvider:
    route='CODEX_SUBSCRIPTION'
    live=True
    def __init__(self,model='gpt-6-luna',executable=None,budget=None):
        if model not in ALLOWED_MODELS:raise SafeError('MODEL_NOT_ALLOWLISTED',403)
        self.model=model;self.executable=executable or shutil.which('codex');self.budget=budget or LiveEvaluationBudget()
        if not self.executable:raise SafeError('CODEX_CLI_UNAVAILABLE',503)
    def metadata(self):return {'route':self.route,'model':self.model,'auth_type':'EXISTING_CHATGPT_CLI_ONLY','live':True,'availability':'CAPABILITY_REQUIRES_COMPLETED_INFERENCE','streaming':True,'tools':[],'fallback':False,'payg':False,'host_policy':'SDK_HOST_WORKING_AGREEMENTS_PRESENT; NO_APPLICATION_VAULT_ACCESS'}
    def spec(self,work):
        args=[self.executable,'app-server','--listen','stdio://','-c','project_doc_max_bytes=0','-c','web_search="disabled"','-c','analytics.enabled=false','-c','otel.log_user_prompt=false','-c','default_permissions="m7c_no_data"','-c','permissions.m7c_no_data.filesystem={":root"="deny",":minimal"="read"}','-c','permissions.m7c_no_data.network.enabled=false','-c','model_provider="m7c_existing_chatgpt"','-c','model_providers.m7c_existing_chatgpt.name="Existing ChatGPT subscription"','-c','model_providers.m7c_existing_chatgpt.requires_openai_auth=true','-c','model_providers.m7c_existing_chatgpt.wire_api="responses"','-c','model_providers.m7c_existing_chatgpt.request_max_retries=0','-c','model_providers.m7c_existing_chatgpt.stream_max_retries=0']
        for feature in DISABLED_FEATURES:args+=['--disable',feature]
        args+=['-c','mcp_servers={}']
        # Preserve standard OS values; never inherit parent Codex task, provider/API key, auth or plugin env.
        env={k:os.environ[k] for k in ('PATH','HOME','TMPDIR','SYSTEMROOT') if k in os.environ};env['LANG']='en_US.UTF-8'
        return {'args':args,'cwd':str(work),'env':env,'shell':False}
    def execute(self,payload,response_schema,cancel,deadline,on_delta=None):
        from .conversation_runtime_contracts import ProviderPayload
        body=ProviderPayload.model_validate(payload).model_dump(mode='json');encoded=encode(body)
        if len(encoded.encode())>64000:raise SafeError('PROVIDER_INPUT_LIMIT',413)
        if cancel.is_set():raise SafeError('CANCELLED')
        work=Path(tempfile.mkdtemp(prefix='m7c-provider-synthetic-',dir=Path(tempfile.gettempdir()).resolve()));process=None;selector=selectors.DefaultSelector();buffer=bytearray();seen_bytes=0;attempt=None
        frame_path=REPO/'skills/conversation/controller_frame.json';frame=json.loads(frame_path.read_text());frame_hash=digest(encode(frame).encode())
        if body['controller_frame_hash']!=frame_hash:raise SafeError('CONTROLLER_FRAME_CHANGED',409)
        started=time.monotonic();text='';final_text=None;usage=None;thread_id=None;turn_id=None;profile_verified=False
        def send(id,method,params):
            wire={'method':method,'params':params}
            if id is not None:wire['id']=id
            process.stdin.write((encode(wire)+'\n').encode());process.stdin.flush()
        def incoming():
            nonlocal buffer,seen_bytes
            while True:
                if cancel.is_set():raise SafeError('CANCELLED')
                if time.monotonic()>=deadline:raise SafeError('PROVIDER_TIMEOUT')
                if b'\n' in buffer:
                    line,rest=buffer.split(b'\n',1);buffer=bytearray(rest)
                    try:return json.loads(line)
                    except (ValueError,UnicodeError):raise SafeError('PROVIDER_PROTOCOL_INVALID') from None
                if process.poll() is not None:raise SafeError('PROVIDER_PROCESS_FAILED')
                if selector.select(.05):
                    part=os.read(process.stdout.fileno(),8192);seen_bytes+=len(part)
                    if seen_bytes>262144:raise SafeError('PROVIDER_OUTPUT_LIMIT')
                    buffer.extend(part)
        def reply(id):
            while True:
                message=incoming()
                if message.get('method') and 'id' in message:raise SafeError('PROVIDER_TOOL_REQUEST_DENIED',403)
                if message.get('id')==id:
                    if 'error' in message:raise SafeError('PROVIDER_RPC_FAILED')
                    return message['result']
        try:
            process=subprocess.Popen(**self.spec(work),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
            selector.register(process.stdout,selectors.EVENT_READ)
            send(1,'initialize',{'clientInfo':{'name':'personal_companion_synthetic_evaluation','version':'0.7.0'},'capabilities':{'experimentalApi':True}});reply(1);send(None,'initialized',{})
            # Read auth TYPE through the supported RPC. Discard all account fields immediately.
            send(2,'account/read',{'refreshToken':False});account=reply(2)
            existing_chatgpt=(account.get('account') or {}).get('type')=='chatgpt'
            del account
            if not existing_chatgpt:raise SafeError('EXISTING_CHATGPT_AUTH_REQUIRED',403)
            send(3,'thread/start',{'model':self.model,'cwd':str(work),'ephemeral':True,'permissions':'m7c_no_data','approvalPolicy':'never','baseInstructions':frame['base_instructions'],'developerInstructions':frame['developer_instructions'],'environments':[],'runtimeWorkspaceRoots':[],'selectedCapabilityRoots':[],'dynamicTools':[],'allowProviderModelFallback':False})
            info=reply(3)
            if info.get('model')!=self.model or info.get('runtimeWorkspaceRoots') or info.get('activePermissionProfile',{}).get('id')!='m7c_no_data':raise SafeError('PROVIDER_ISOLATION_UNVERIFIED',403)
            thread_id=info['thread']['id'];profile_verified=True
            attempt=str(uuid4());self.budget.reserve(attempt,self.route,self.model)
            send(4,'turn/start',{'threadId':thread_id,'model':self.model,'effort':'low','environments':[],'runtimeWorkspaceRoots':[],'input':[{'type':'text','text':encoded}],'outputSchema':response_schema})
            while True:
                event=incoming()
                if event.get('id')==4:
                    if 'error' in event:raise SafeError('PROVIDER_RPC_FAILED')
                    turn_id=event.get('result',{}).get('turn',{}).get('id');continue
                method=event.get('method','');params=event.get('params',{})
                if 'id' in event and method:raise SafeError('PROVIDER_TOOL_REQUEST_DENIED',403)
                if method in {'item/started','item/completed'}:
                    item=params.get('item',{});kind=item.get('type')
                    if kind not in {'agentMessage','reasoning','userMessage'}:raise SafeError('PROVIDER_TOOL_REQUEST_DENIED',403)
                    if kind=='agentMessage' and method=='item/completed':final_text=item.get('text',final_text)
                if method=='item/agentMessage/delta':
                    text+=params.get('delta','')
                    if len(text.encode())>24000:raise SafeError('PROVIDER_OUTPUT_LIMIT')
                    if on_delta:on_delta(text) # private ephemeral candidate only, never authoritative persistence
                if method=='thread/tokenUsage/updated':
                    total=params.get('tokenUsage',{}).get('last') or params.get('tokenUsage',{}).get('total') or {}
                    usage={k:v for k,v in total.items() if k in {'inputTokens','cachedInputTokens','outputTokens','totalTokens'} and isinstance(v,int)}
                if method=='turn/completed':
                    status=params.get('turn',{}).get('status')
                    if status!='completed':raise SafeError('PROVIDER_TURN_FAILED')
                    result=final_text if final_text is not None else text
                    self.budget.finish(attempt,'COMPLETED')
                    return {'text':result,'elapsed_ms':round((time.monotonic()-started)*1000,3),'usage':usage,'route':self.route,'model':self.model,'auth_type':'EXISTING_CHATGPT','profile_verified':profile_verified,'streaming_actual':bool(text),'frame_hash':frame_hash}
        except BaseException as exc:
            if attempt:self.budget.finish(attempt,'CANCELLED' if isinstance(exc,SafeError) and exc.code=='CANCELLED' else 'FAILED')
            raise
        finally:
            selector.close()
            if process:
                if process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=2)
                if process.stdin:process.stdin.close()
                if process.stdout:process.stdout.close()
            shutil.rmtree(work)
