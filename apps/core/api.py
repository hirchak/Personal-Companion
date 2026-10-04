"""Loopback-only same-origin HTTP adapter. No provider or credential discovery."""
import secrets
import re
import sqlite3
import threading
import time
from pathlib import Path
from uuid import UUID, uuid4
from datetime import date
from fastapi import FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response, FileResponse
from pydantic import ValidationError
from .models import Create, Patch, Delete, Selector, Export, Unlock, EntryOutput, EntryPage, RevisionPage, Receipt
from .storage import SafeError, Store, digest
from .domain import Journal
from .creative import CreativeLibrary
from .feedback import Feedback, PersonalSpace
from .m5_contracts import CreativeSelection, CreativeDownload, FeedbackSave, FeedbackExact, FeedbackExport, SpaceUpdate
from .health import HealthImport
from .health_contracts import HealthApply, HealthAction
from .conversation_controller import ConversationController
from .conversation_runtime_contracts import InferenceStart,InferenceAction,JournalPointPreview,JournalPointConfirm
from .reflection import Reflection
from .reflection_contracts import GoalCreate, GoalChange, ContextRequest, Expansion, MessageEdit
from .deep_session_contracts import DeepContextPreview,MapAction,SessionAction
from .conversation import Conversations
from .conversation_contracts import NewConversation, SendMessage, ConversationAction
from .practice import PracticeEngine
from .practice_contracts import Start as PracticeStart, Action as PracticeAction
from .runtime import Runtime
from .ai_contracts import PreviewRequest, Approval, Enqueue, RuntimeMode, Empty, MemoryCreate, MemoryChange, SuggestionChange
from .sync import SyncService, Pair, Packet, EpochReset
from .voice import Voice
from .voice_contracts import AudioBegin, AudioChunk, VoiceEmpty, ASRRequest, TranscriptEdit, TranscriptConfirm, AudioDelete
from .root_types import RootKind

CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"

class Auth:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.code = secrets.token_urlsafe(18)
        self.code_until = clock() + 300
        self.attempts, self.sessions = [], {}
        self.lock = threading.Lock()

    def unlock(self, code):
        with self.lock:
            now = self.clock()
            self.attempts = [x for x in self.attempts if now - x < 60]
            if len(self.attempts) >= 5:
                raise SafeError('UNLOCK_RATE_LIMIT', 429)
            self.attempts.append(now)
            if not self.code or now >= self.code_until or not secrets.compare_digest(code.encode('utf-8', 'surrogatepass'), self.code.encode('ascii')):
                raise SafeError('UNLOCK_DENIED', 401)
            self.code = None
            token = secrets.token_urlsafe(32)
            self.sessions[token] = {'csrf': secrets.token_urlsafe(32), 'created': now, 'last': now}
            return token, self.sessions[token]

    def session(self, token):
        with self.lock:
            now = self.clock()
            s = self.sessions.get(token)
            if s is None or now - s['last'] >= 900 or now - s['created'] >= 28800:
                self.sessions.pop(token, None)
                raise SafeError('LOCKED', 401)
            s['last'] = now
            return s


def create_app(root, port=8765, clock=time.monotonic, web=None, m2=False, scheme="http", synthetic_practices=False, synthetic_conversations=False,conversation_provider=None,m7c_synthetic=False,local_asr=None,conversation_timeout=60,release_identity=None,root_kind=RootKind.SYNTHETIC_TEST):
    private = RootKind(root_kind)==RootKind.PRIVATE_LOCAL
    if private and (not release_identity or conversation_provider is not None or local_asr is not None or m2 or synthetic_practices or synthetic_conversations or m7c_synthetic):raise SafeError('PRIVATE_CORE_CAPABILITY_OFF',403)
    if release_identity and (conversation_provider is not None or local_asr is not None or m2 or synthetic_practices):raise SafeError('RELEASE_CAPABILITY_OFF',403)
    if scheme not in {"http","https"}: raise SafeError("UNSUPPORTED_TRANSPORT")
    if (conversation_provider is not None or local_asr is not None) and not m7c_synthetic:raise SafeError('M7C_SYNTHETIC_SCOPE_REQUIRED',403)
    store = Store(root,root_kind=root_kind)
    journal, auth = Journal(store, clock), Auth(clock)
    app = FastAPI(title='M1 Local Journal', version='1.0.0', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store, app.state.journal, app.state.auth = store, journal, auth
    sync = SyncService(journal, clock)
    app.state.sync, app.state.m2 = sync, m2
    runtime = Runtime(journal)
    app.state.runtime = runtime
    voice = Voice(journal, sync)
    app.state.voice = voice
    creative, feedback, space = CreativeLibrary(journal), Feedback(store), PersonalSpace(store)
    app.state.creative, app.state.feedback, app.state.space = creative, feedback, space
    health = HealthImport(store)
    app.state.health = health
    practices = PracticeEngine(store, synthetic_demo=synthetic_practices)
    app.state.practices = practices
    conversations = Conversations(store, synthetic_demo=synthetic_conversations,mock_responses=False if release_identity else None)
    app.state.conversations = conversations
    reflection = Reflection(conversations)
    app.state.reflection = reflection
    controller=ConversationController(conversations,conversation_provider,timeout=conversation_timeout) if m7c_synthetic else None
    app.state.conversation_controller=controller
    if local_asr is not None:
        voice.engines['LOCAL']=local_asr
        voice.timeout=90
    host, origin = f'127.0.0.1:{port}', f'{scheme}://127.0.0.1:{port}'
    web = Path(web) if web else Path(__file__).resolve().parents[1] / 'web/dist'

    def error(code, status):
        return JSONResponse({'code': code, 'request_id': str(uuid4())}, status_code=status, headers={'Cache-Control': 'no-store', 'Content-Security-Policy': CSP})

    @app.middleware('http')
    async def boundary(request: Request, call_next):
        try:
            if request.headers.get('host') != host:
                raise SafeError('HOST_DENIED', 403)
            request_origin = request.headers.get('origin')
            if request_origin is not None and request_origin != origin:
                raise SafeError('ORIGIN_DENIED', 403)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                raise SafeError('ORIGIN_DENIED', 403)
            if request.method not in {'GET', 'HEAD'}:
                if request_origin != origin:
                    raise SafeError('ORIGIN_REQUIRED', 403)
                if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                    raise SafeError('JSON_REQUIRED', 415)
                length = 0
                chunks = []
                async for chunk in request.stream():
                    length += len(chunk)
                    if length > (400000 if '/voice/' in request.url.path else 1048576):
                        raise SafeError('BODY_LIMIT', 413)
                    chunks.append(chunk)
                request._body = b''.join(chunks)
            path = request.url.path
            if release_identity and path.startswith('/api/') and request.headers.get('x-pc-build') != release_identity:
                raise SafeError('FRONTEND_UPDATE_REQUIRED',409)
            if '/voice/' in path and request.url.query:
                raise SafeError('VOICE_QUERY_DENIED',403)
            if path.startswith('/api/v1/device/'):
                if not m2: raise SafeError('M2_DISABLED',403)
                if path != '/api/v1/device/pair':
                    bearer = request.headers.get('authorization','')
                    if not bearer.startswith('Bearer '): raise SafeError('DEVICE_DENIED',401)
                    with store.connect() as connection:
                        sync.authenticate(connection,request.headers.get('x-device-id',''),bearer[7:],request.headers.get('x-sync-epoch',''), allow_pending=path=='/api/v1/device/finalize')
                    request.state.device_token = bearer[7:]
                    request.state.device_id = request.headers['x-device-id']
                    request.state.device_epoch = request.headers.get('x-sync-epoch','')
            elif path.startswith('/api/') and path != '/api/v1/auth/unlock':
                token = request.cookies.get('m1_session', '')
                s = auth.session(token)
                request.state.session = token
                if request.method not in {'GET', 'HEAD'} and not secrets.compare_digest(request.headers.get('x-csrf-token', '').encode('utf-8', 'surrogatepass'), s['csrf'].encode('ascii')):
                    raise SafeError('CSRF_DENIED', 403)
            if private:
                # Explicit allowlist makes future optional routes OFF until a separately reviewed profile.
                allowed = path in {'/api/v1/status','/api/v1/auth/unlock','/api/v1/auth/session','/api/v1/auth/lock','/api/v1/entries','/api/v1/creative','/api/v1/creative/preview','/api/v1/creative/export','/api/v1/exports','/api/v1/exports/preview'} or re.fullmatch(r'/api/v1/entries/[0-9a-fA-F-]{36}(?:/revisions)?',path) is not None
                if path.startswith('/api/') and not allowed:raise SafeError('PRIVATE_CORE_CAPABILITY_OFF',403)
                if path.startswith('/phone'):raise SafeError('PRIVATE_CORE_CAPABILITY_OFF',403)
            response = await call_next(request)
        except SafeError as exc:
            response = error(exc.code, exc.status)
        except (sqlite3.Error, OSError):
            response = error('STORAGE_UNAVAILABLE', 503)
        response.headers.update({'Cache-Control': 'no-store', 'Content-Security-Policy': CSP,
                                 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()' if private else 'camera=(), microphone=(self), geolocation=()'})
        return response

    @app.exception_handler(SafeError)
    async def domain_error(request, exc):
        return error(exc.code, exc.status)

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def invalid(request, exc):
        return error('SCHEMA_INVALID', 422)  # never echo input, paths, SQL or error context

    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(OSError)
    async def storage_error(request, exc):
        return error('STORAGE_UNAVAILABLE', 503)

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        return error('INTERNAL_ERROR', 500)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error('NOT_FOUND' if exc.status_code == 404 else 'REQUEST_DENIED', exc.status_code)

    def voice_auth(request):
        return (request.state.device_id,request.state.device_token,request.state.device_epoch) if request.url.path.startswith('/api/v1/device/') else None

    # Same bounded domain boundary for owner session and already paired phone. No arbitrary paths.
    for prefix in ('/api/v1/voice','/api/v1/device/voice'):
        def voice_list(request: Request): return voice.list(voice_auth(request))
        def voice_begin(body: AudioBegin,request: Request): return voice.begin(body,voice_auth(request))
        def voice_get(audio_id: UUID,request: Request): return voice.get(audio_id,voice_auth(request))
        def voice_chunk(audio_id: UUID,body: AudioChunk,request: Request):return voice.chunk(audio_id,body,voice_auth(request))
        def voice_finish(audio_id: UUID,body: VoiceEmpty,request: Request):return voice.finalize(audio_id,voice_auth(request))
        def voice_cancel(audio_id: UUID,body: VoiceEmpty,request: Request):return voice.cancel_upload(audio_id,voice_auth(request))
        def voice_delete(audio_id: UUID,body: AudioDelete,request: Request):return voice.delete(audio_id,body,voice_auth(request))
        def voice_asr(audio_id: UUID,body: ASRRequest,request: Request):
            auth_args=voice_auth(request);result=voice.enqueue(audio_id,body,auth_args)
            threading.Thread(target=voice.run,args=(result['transcript_id'],body.mode,auth_args),daemon=True).start()
            return result
        def voice_edit(transcript_id: UUID,body: TranscriptEdit,request: Request):return voice.edit(transcript_id,body,voice_auth(request))
        def voice_discard(transcript_id: UUID,body: VoiceEmpty,request: Request):return voice.cancel_transcript(transcript_id,voice_auth(request))
        def voice_confirm(transcript_id: UUID,body: TranscriptConfirm,request: Request):return voice.confirm(transcript_id,body,voice_auth(request))
        for path,endpoint,methods in [
            ('/audio',voice_list,['GET']),('/audio',voice_begin,['POST']),('/audio/{audio_id}',voice_get,['GET']),
            ('/audio/{audio_id}/chunks',voice_chunk,['POST']),('/audio/{audio_id}/finalize',voice_finish,['POST']),
            ('/audio/{audio_id}/cancel',voice_cancel,['POST']),('/audio/{audio_id}/delete',voice_delete,['POST']),
            ('/audio/{audio_id}/transcribe',voice_asr,['POST']),('/transcripts/{transcript_id}/edit',voice_edit,['POST']),
            ('/transcripts/{transcript_id}/cancel',voice_discard,['POST']),('/transcripts/{transcript_id}/confirm',voice_confirm,['POST'])]:
            app.add_api_route(prefix+path,endpoint,methods=methods)

    @app.get('/api/v1/reflection/goals')
    def goals_list(): return reflection.list()

    @app.post('/api/v1/reflection/goals')
    def goals_create(body: GoalCreate): return reflection.create(body)

    @app.get('/api/v1/reflection/goals/{goal_id}')
    def goals_get(goal_id: UUID): return reflection.get(goal_id)

    @app.post('/api/v1/reflection/goals/{goal_id}')
    def goals_change(goal_id: UUID, body: GoalChange): return reflection.change(goal_id,body)

    @app.post('/api/v1/reflection/context')
    def context_build(body: ContextRequest): return reflection.build(body)

    @app.post('/api/v1/reflection/expand')
    def context_expand(body: Expansion): return reflection.expand(body)

    @app.post('/api/v1/conversations/{conversation_id}/messages/{message_id}/edit')
    def conversation_message_edit(conversation_id: UUID,message_id: UUID,body: MessageEdit): return reflection.edit_message(conversation_id,message_id,body)

    @app.get('/api/v1/conversations/status')
    def conversation_status(): return controller.status() if controller else conversations.mode()

    @app.get('/api/v1/conversations')
    def conversation_list(archived: bool = False, offset: int = Query(0,ge=0)): return conversations.list(archived,offset)

    @app.post('/api/v1/conversations')
    def conversation_create(body: NewConversation): return conversations.create(body)

    @app.get('/api/v1/conversations/{conversation_id}')
    def conversation_get(conversation_id: UUID, after: int = Query(0,ge=0)): return controller.page(conversation_id) if controller and after==0 else conversations.get(conversation_id,after)

    @app.post('/api/v1/conversations/{conversation_id}/messages')
    def conversation_send(conversation_id: UUID, body: SendMessage): return conversations.send(conversation_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/actions')
    def conversation_action(conversation_id: UUID, body: ConversationAction): return conversations.action(conversation_id,body)

    def require_deep():
        if not controller:raise SafeError('M7D_RUNTIME_OFF',403)
        return controller.deep

    @app.get('/api/v1/conversations/{conversation_id}/deep-session')
    def deep_session_get(conversation_id:UUID):return require_deep().read(conversation_id)

    @app.post('/api/v1/conversations/{conversation_id}/deep-session/actions')
    def deep_session_action(conversation_id:UUID,body:SessionAction):return require_deep().session_action(conversation_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/working-map/actions')
    def working_map_action(conversation_id:UUID,body:MapAction):return require_deep().action(conversation_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/context-preview')
    def deep_context_preview(conversation_id:UUID,body:DeepContextPreview):
        require_deep()
        return controller.preview_context(conversation_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/inference')
    def conversation_infer(conversation_id:UUID,body:InferenceStart):
        if not controller:raise SafeError('M7C_RUNTIME_OFF',403)
        return controller.send(conversation_id,body)

    @app.get('/api/v1/conversations/{conversation_id}/inference/{job_id}')
    def inference_get(conversation_id:UUID,job_id:UUID):
        if not controller:raise SafeError('M7C_RUNTIME_OFF',403)
        return controller.get(conversation_id,job_id)

    @app.post('/api/v1/conversations/{conversation_id}/inference/{job_id}/actions')
    def inference_action(conversation_id:UUID,job_id:UUID,body:InferenceAction):
        if not controller:raise SafeError('M7C_RUNTIME_OFF',403)
        return controller.action(conversation_id,job_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/journal-point/preview')
    def journal_point_preview(conversation_id:UUID,body:JournalPointPreview):
        if not controller:raise SafeError('M7C_RUNTIME_OFF',403)
        return controller.journal_preview(conversation_id,body)

    @app.post('/api/v1/conversations/{conversation_id}/journal-point/confirm')
    def journal_point_confirm(conversation_id:UUID,body:JournalPointConfirm):
        if not controller:raise SafeError('M7C_RUNTIME_OFF',403)
        return controller.journal_confirm(journal,conversation_id,body)

    @app.get('/api/v1/practices/catalog')
    def practice_catalog(): return practices.catalog()

    @app.get('/api/v1/practices/sessions')
    def practice_history(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
        return practices.history(limit, offset)

    @app.post('/api/v1/practices/sessions')
    def practice_start(body: PracticeStart): return practices.start(body)

    @app.get('/api/v1/practices/sessions/{session_id}')
    def practice_get(session_id: UUID): return practices.get(session_id)

    @app.post('/api/v1/practices/sessions/{session_id}/actions')
    def practice_action(session_id: UUID, body: PracticeAction): return practices.act(session_id, body)

    @app.get('/api/v1/health/status')
    def health_status():return health.status()

    @app.get('/api/v1/device/health/status')
    def phone_health_status():return health.status()

    @app.get('/api/v1/health/records')
    def health_records():return {'items':health.records()}

    @app.post('/api/v1/health/import')
    def health_import(body:HealthApply):return health.apply(body.batch,body.reconnect,body.generation)

    @app.post('/api/v1/health/disconnect')
    def health_disconnect(body:HealthAction):return health.disconnect(generation=body.generation)

    @app.post('/api/v1/health/delete')
    def health_delete(body:HealthAction):return health.disconnect(delete=True,generation=body.generation)

    @app.post('/api/v1/auth/unlock')
    def unlock(body: Unlock):
        token, s = auth.unlock(body.code)
        r = JSONResponse({'csrf_token': s['csrf'], 'idle_seconds': 900, 'absolute_seconds': 28800})
        r.set_cookie('m1_session', token, httponly=True, samesite='strict', path='/', max_age=None if private else 28800, secure=scheme=='https')
        return r

    @app.get('/api/v1/auth/session')
    def session(request: Request):
        s = auth.sessions[request.state.session]
        return {'csrf_token': s['csrf'], 'idle_seconds': 900, 'absolute_seconds': 28800}

    @app.post('/api/v1/auth/lock')
    def lock(request: Request):
        auth.sessions.pop(request.state.session, None)
        runtime.set_mode('OFF')
        with store.transaction() as c:
            c.execute('UPDATE ai_consents SET revoked=1 WHERE session=?',(digest(request.state.session.encode()),))
        journal.plans = {k: v for k, v in journal.plans.items() if v['session'] != request.state.session}
        creative.plans = {k: v for k, v in creative.plans.items() if v['session'] != request.state.session}
        r = JSONResponse({'code': 'LOCKED'}); r.delete_cookie('m1_session', path='/')
        return r

    @app.get('/api/v1/status')
    def status():
        if private:
            from .local_private import PROFILE
            return {'schema_version':store.meta()['schema_version'],'mode':'PRIVATE_LOCAL','root_kind':'PRIVATE_LOCAL','provider':'OFF','storage':'LOCAL_MAC','data':'PRIVATE_PERSONAL','capabilities':PROFILE}
        return {'schema_version': store.meta()['schema_version'], 'mode':'M2_SYNTHETIC_HARNESS' if m2 else 'LOCAL_ONLY', 'provider': 'OFF', 'storage': 'LOCAL_MAC', 'data': 'SYNTHETIC'}

    @app.get('/runtime-mode.json', include_in_schema=False)
    def runtime_mode():
        # Only the mode is public, so the unlock screen can be truthful without disclosing content.
        return {'root_kind':str(RootKind(root_kind))}

    @app.post('/api/v1/entries', status_code=201, response_model=Receipt)
    def create(body: Create):
        return journal.write('create', body.entry_id, body)

    @app.get('/api/v1/entries', response_model=EntryPage, response_model_exclude_unset=True)
    def entries(q: str = Query('', max_length=200), type: str | None = None,
                tag: str | None = Query(None, max_length=64), date_from: date | None = None,
                date_to: date | None = None, limit: int = Query(50, ge=1, le=100), cursor: str | None = Query(None, max_length=1024)):
        if type is not None and type not in {'inbox', 'daily', 'sleep', 'creative'}:
            raise SafeError('SCHEMA_INVALID')
        return journal.list(q, type, tag, date_from.isoformat() if date_from else None, date_to.isoformat() if date_to else None, limit, cursor)

    @app.get('/api/v1/entries/{entry_id}', response_model=EntryOutput, response_model_exclude_unset=True)
    def get(entry_id: UUID):
        return journal.get(str(entry_id))

    @app.get('/api/v1/entries/{entry_id}/revisions', response_model=RevisionPage, response_model_exclude_unset=True)
    def revisions(entry_id: UUID, limit: int = Query(100, ge=1, le=100), after: int = Query(0, ge=0)):
        return journal.history(str(entry_id), limit, after)

    @app.patch('/api/v1/entries/{entry_id}', response_model=Receipt)
    def edit(entry_id: UUID, body: Patch):
        return journal.write('edit', entry_id, body)

    @app.delete('/api/v1/entries/{entry_id}', response_model=Receipt)
    def delete(entry_id: UUID, body: Delete):
        return journal.write('delete', entry_id, body)

    @app.post('/api/v1/exports/preview')
    def preview(body: Selector, request: Request):
        return journal.preview(body, request.state.session)

    @app.post('/api/v1/exports')
    def export(body: Export, request: Request):
        text = journal.export(body.plan_id, body.format, request.state.session)
        ext = 'json' if body.format == 'json' else 'md'
        return Response(text, media_type='application/json' if ext == 'json' else 'text/markdown', headers={'Content-Disposition': f'attachment; filename="selected-journal.{ext}"'})

    def require_m2():
        if not m2: raise SafeError('M2_DISABLED',403)

    @app.get('/api/v1/creative')
    def creative_list(q: str = Query('', max_length=200), kind: str | None = None,
                      tag: str | None = Query(None,max_length=64), collection: str | None = Query(None,max_length=64),
                      archived: bool = False, order: str = 'recent', limit: int = Query(50,ge=1,le=100), offset: int = Query(0,ge=0,le=100000)):
        return creative.list(q,kind,tag,collection,archived,order,limit,offset)

    @app.post('/api/v1/creative/preview')
    def creative_preview(body: CreativeSelection, request: Request): return creative.preview(body,request.state.session)

    @app.post('/api/v1/creative/export')
    def creative_export(body: CreativeDownload, request: Request):
        ext='md' if body.format=='markdown' else 'json'
        return Response(creative.export(body,request.state.session),media_type='text/markdown' if ext=='md' else 'application/json',
                        headers={'Content-Disposition':f'attachment; filename="selected-creative.{ext}"'})

    @app.get('/api/v1/feedback')
    def feedback_list(): return feedback.list()

    @app.post('/api/v1/feedback')
    def feedback_save(body: FeedbackSave): return feedback.save(body)

    @app.post('/api/v1/feedback/{draft_id}/approve')
    def feedback_approve(draft_id: UUID,body: FeedbackExact): return feedback.approve(draft_id,body)

    @app.post('/api/v1/feedback/{draft_id}/export')
    def feedback_export(draft_id: UUID,body: FeedbackExport):
        ext='md' if body.format=='markdown' else 'json'
        return Response(feedback.export(draft_id,body),media_type='text/markdown' if ext=='md' else 'application/json',
                        headers={'Content-Disposition':f'attachment; filename="approved-feedback.{ext}"'})

    @app.post('/api/v1/feedback/{draft_id}/delete')
    def feedback_delete(draft_id: UUID,body: FeedbackExact): return feedback.delete(draft_id,body)

    @app.get('/api/v1/personal-space')
    def space_get(): return space.get()

    @app.post('/api/v1/personal-space')
    def space_update(body: SpaceUpdate): return space.update(body)

    @app.post('/api/v1/sync/invitations')
    def invitation(body: EpochReset):
        require_m2(); return sync.invite()

    @app.get('/api/v1/sync/devices')
    def devices():
        require_m2(); return sync.devices()

    @app.post('/api/v1/sync/devices/{device_id}/revoke')
    def revoke(device_id: UUID, body: EpochReset):
        require_m2(); return sync.revoke(device_id)

    @app.post('/api/v1/sync/epoch')
    def reset_epoch(body: EpochReset):
        require_m2(); return sync.rotate(body.prune_tombstones)

    @app.post('/api/v1/device/pair')
    def pair(body: Pair):
        return sync.pair(body)

    @app.post('/api/v1/device/finalize')
    def finalize(body: Empty, request: Request):
        return sync.finalize(request.state.device_id, request.state.device_token, request.state.device_epoch)

    @app.get('/api/v1/ai/status')
    def ai_status(): return runtime.status()

    @app.post('/api/v1/ai/mode')
    def ai_mode(body: RuntimeMode): return runtime.set_mode(body.mode)

    @app.post('/api/v1/ai/preview')
    def ai_preview(body: PreviewRequest, request: Request): return runtime.preview(body, request.state.session)

    @app.post('/api/v1/ai/consents/{id}/approve')
    def ai_approve(id: UUID, body: Approval, request: Request): return runtime.approve(id, body.context_hash, request.state.session)

    @app.post('/api/v1/ai/consents/{id}/revoke')
    def ai_revoke(id: UUID, body: Empty, request: Request): return runtime.revoke(id, request.state.session)

    @app.get('/api/v1/ai/jobs')
    def ai_jobs(): return runtime.jobs()

    @app.post('/api/v1/ai/jobs', status_code=201)
    def ai_enqueue(body: Enqueue, request: Request): return runtime.enqueue(body, request.state.session)

    @app.post('/api/v1/ai/jobs/{id}/cancel')
    def ai_cancel(id: UUID, body: Empty): return runtime.cancel(id)

    @app.get('/api/v1/ai/memories')
    def ai_memories(q: str = Query('', max_length=200)): return runtime.memories(q)

    @app.post('/api/v1/ai/memories', status_code=201)
    def ai_memory_create(body: MemoryCreate): return runtime.create_memory(body)

    @app.post('/api/v1/ai/memories/{id}')
    def ai_memory_change(id: UUID, body: MemoryChange): return runtime.change_memory(id, body)

    @app.get('/api/v1/ai/suggestions')
    def ai_suggestions(): return runtime.suggestions()

    @app.post('/api/v1/ai/suggestions/{id}')
    def ai_suggestion_change(id: UUID, body: SuggestionChange): return runtime.change_suggestion(id, body)

    @app.get('/api/v1/device/snapshot')
    def pull(request: Request):
        return sync.snapshot(request.state.device_id,request.state.device_token,request.state.device_epoch)

    @app.post('/api/v1/device/operations')
    def apply(body: Packet, request: Request):
        return sync.apply(body,request.state.device_id,request.state.device_token,request.state.device_epoch)

    @app.get('/release.json')
    def release_contract():
        return {'web_contract':2,'git_commit':release_identity or 'DEVELOPMENT','schema_version':store.meta()['schema_version']}

    @app.get('/{path:path}')
    def shell(path: str):
        if path.startswith('api/'):
            raise SafeError('NOT_FOUND', 404)
        if path.startswith('phone') and not m2: raise SafeError('M2_DISABLED',403)
        target = web / ('phone/index.html' if path in ('phone/','phone') else path or 'index.html')
        if not target.resolve().is_relative_to(web.resolve()) or not target.is_file():
            raise SafeError('NOT_FOUND', 404)
        return FileResponse(target)
    return app
