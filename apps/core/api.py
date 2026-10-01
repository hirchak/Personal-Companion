"""Loopback-only same-origin HTTP adapter. No provider or credential discovery."""
import secrets
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
from .runtime import Runtime
from .ai_contracts import PreviewRequest, Approval, Enqueue, RuntimeMode, Empty, MemoryCreate, MemoryChange, SuggestionChange
from .sync import SyncService, Pair, Packet, EpochReset

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


def create_app(root, port=8765, clock=time.monotonic, web=None, m2=False, scheme="http"):
    if scheme not in {"http","https"}: raise SafeError("UNSUPPORTED_TRANSPORT")
    store = Store(root)
    journal, auth = Journal(store, clock), Auth(clock)
    app = FastAPI(title='M1 Local Journal', version='1.0.0', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store, app.state.journal, app.state.auth = store, journal, auth
    sync = SyncService(journal, clock)
    app.state.sync, app.state.m2 = sync, m2
    runtime = Runtime(journal)
    app.state.runtime = runtime
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
                    if length > 1048576:
                        raise SafeError('BODY_LIMIT', 413)
                    chunks.append(chunk)
                request._body = b''.join(chunks)
            path = request.url.path
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
            response = await call_next(request)
        except SafeError as exc:
            response = error(exc.code, exc.status)
        except (sqlite3.Error, OSError):
            response = error('STORAGE_UNAVAILABLE', 503)
        response.headers.update({'Cache-Control': 'no-store', 'Content-Security-Policy': CSP,
                                 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'})
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

    @app.post('/api/v1/auth/unlock')
    def unlock(body: Unlock):
        token, s = auth.unlock(body.code)
        r = JSONResponse({'csrf_token': s['csrf'], 'idle_seconds': 900, 'absolute_seconds': 28800})
        r.set_cookie('m1_session', token, httponly=True, samesite='strict', path='/', max_age=28800, secure=scheme=='https')
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
        r = JSONResponse({'code': 'LOCKED'}); r.delete_cookie('m1_session', path='/')
        return r

    @app.get('/api/v1/status')
    def status():
        return {'schema_version': 3, 'mode':'M2_SYNTHETIC_HARNESS' if m2 else 'LOCAL_ONLY', 'provider': 'OFF', 'storage': 'LOCAL_MAC', 'data': 'SYNTHETIC'}

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
