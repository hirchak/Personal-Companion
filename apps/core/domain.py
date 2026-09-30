"""One domain service shared by HTTP, demo and maintenance."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from uuid import uuid4
from pydantic import ValidationError
from .models import EntryInput, FIELDS, TYPED, Selector
from .storage import SafeError, encode, digest, now

class Journal:
    def __init__(self, store, clock=time.monotonic):
        self.store, self.clock = store, clock
        self.owner = store.meta()['owner_id']
        self.plans = {}
        self.cursor_key = secrets.token_bytes(32)

    def row(self, c, entry_id):
        if c.execute('SELECT 1 FROM tombstones WHERE entry_id=? AND owner_id=?', (entry_id, self.owner)).fetchone():
            raise SafeError('DELETED', 410)
        row = c.execute('SELECT * FROM entries WHERE id=? AND owner_id=?', (entry_id, self.owner)).fetchone()
        if not row:
            raise SafeError('NOT_FOUND', 404)
        return row

    def view(self, row):
        p = json.loads(row['payload'])
        result = dict(p, id=row['id'], owner_id=row['owner_id'], revision=row['revision'],
                      created_at_utc=row['created'], updated_at_utc=row['updated'], schema_version=1,
                      privacy_class='PRIVATE_PERSONAL', provenance_type='USER_REPORTED')
        if p['type'] == 'sleep':
            from datetime import datetime
            a, b = p.get('sleep_start_utc'), p.get('wake_at_utc')
            result['reported_interval_seconds'] = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() if a and b else None
        return result

    def get(self, entry_id):
        with self.store.connect() as c:
            return self.view(self.row(c, entry_id))

    @staticmethod
    def revision_view(payload):
        entry = json.loads(payload)
        # Never invent recording times for pre-correction synthetic history.
        entry.setdefault('recorded_at_utc', None)
        return entry

    def history(self, entry_id, limit=100, after=0):
        with self.store.connect() as c:
            self.row(c, entry_id)
            rows = c.execute('SELECT payload FROM entry_revisions WHERE entry_id=? AND revision>? ORDER BY revision LIMIT ?', (entry_id, after, limit)).fetchall()
            items = [self.revision_view(r[0]) for r in rows]
            return {'items': items, 'next_after': items[-1]['revision'] if len(items) == limit else None}

    def write(self, action, entry_id, request):
        entry_id, op = str(entry_id), str(request.operation_id)
        try:
            data = request.model_dump(mode='json')
            fp = digest(encode({'entry_id': entry_id, 'action': action, 'request': data}).encode())
        except (ValueError, TypeError):
            raise SafeError('SCHEMA_INVALID', 422) from None
        with self.store.transaction() as c:
            dead = c.execute('SELECT * FROM tombstones WHERE entry_id=? AND owner_id=?', (entry_id, self.owner)).fetchone()
            existing = c.execute('SELECT * FROM operation_receipts WHERE operation_id=?', (op,)).fetchone()
            if dead and action != 'delete':
                raise SafeError('DELETED', 410)
            if existing:
                if existing['owner_id'] != self.owner or existing['entry_id'] != entry_id or existing['action'] != action or existing['fingerprint'] != fp:
                    raise SafeError('OPERATION_REUSE', 409)
                return {'entry_id': entry_id, 'revision': existing['revision'], 'result_code': existing['result_code'], 'operation_id': op}
            if dead:
                # A new operation on an already deleted entry still needs a receipt:
                # otherwise its operation ID could be reused for another action.
                c.execute('INSERT INTO operation_receipts VALUES(?,?,?,?,?,?,?)',
                          (op, self.owner, entry_id, action, fp, dead['revision'], 'DELETED'))
                return {'entry_id': entry_id, 'revision': dead['revision'], 'result_code': 'DELETED', 'operation_id': op}
            timestamp = now()
            if action == 'create':
                if c.execute('SELECT 1 FROM entries WHERE id=?', (entry_id,)).fetchone():
                    raise SafeError('REVISION_CONFLICT', 409)
                rev, payload = 1, request.payload.payload()
                c.execute('INSERT INTO entries VALUES(?,?,?,?,?,?)', (entry_id, self.owner, rev, encode(payload), timestamp, timestamp))
            else:
                old = self.row(c, entry_id)
                if old['revision'] != request.base_revision:
                    raise SafeError('REVISION_CONFLICT', 409)
                rev = old['revision'] + 1
                if action == 'delete':
                    c.execute('DELETE FROM entries WHERE id=? AND owner_id=?', (entry_id, self.owner))
                    c.execute('UPDATE operation_receipts SET fingerprint=NULL WHERE entry_id=?', (entry_id,))
                    c.execute('INSERT INTO tombstones VALUES(?,?,?,?,?)', (entry_id, self.owner, rev, timestamp, self.store.meta()['restore_epoch']))
                else:
                    p = json.loads(old['payload'])
                    target = request.changes.get('type', p['type'])
                    if not isinstance(target, str) or target not in FIELDS:
                        raise SafeError('SCHEMA_INVALID', 422)
                    if target != p['type']:
                        removed = {k for k in FIELDS[p['type']] if p.get(k) is not None}
                        if removed and not request.confirm_type_change:
                            raise SafeError('TYPE_CHANGE_CONFIRMATION_REQUIRED', 409)
                        p = {k: v for k, v in p.items() if k not in TYPED}
                    p.update(request.changes)
                    try:
                        payload = EntryInput.model_validate(p).payload()
                    except ValidationError:
                        raise SafeError('SCHEMA_INVALID', 422) from None
                    c.execute('INSERT INTO entry_revisions VALUES(?,?,?)', (entry_id, old['revision'], encode(dict(self.view(old), recorded_at_utc=timestamp))))
                    c.execute('UPDATE entries SET revision=?,payload=?,updated=? WHERE id=? AND owner_id=?', (rev, encode(payload), timestamp, entry_id, self.owner))
            if action != 'delete':
                c.execute('INSERT OR REPLACE INTO search_index VALUES(?,?)', (entry_id, payload['raw_text']))
            code = 'DELETED' if action == 'delete' else 'MAC_SAVED'
            c.execute('INSERT INTO operation_receipts VALUES(?,?,?,?,?,?,?)', (op, self.owner, entry_id, action, fp, rev, code))
            result = {'entry_id': entry_id, 'revision': rev, 'result_code': code, 'operation_id': op}
        return result  # reached only AFTER successful commit

    def rebuild(self):
        with self.store.transaction() as c:
            c.execute('DELETE FROM search_index')
            c.execute("INSERT INTO search_index SELECT id,json_extract(payload,'$.raw_text') FROM entries")

    def list(self, q='', type=None, tag=None, date_from=None, date_to=None, limit=50, cursor=None):
        if len(q) > 200 or not 1 <= limit <= 100:
            raise SafeError('QUERY_LIMIT')
        filters = encode([q, type, tag, date_from, date_to])
        params, where = [self.owner, q], ['e.owner_id=?', 'instr(s.raw_text,?)>0']
        for key, value, operator in [('type', type, '='), ('local_date', date_from, '>='), ('local_date', date_to, '<=')]:
            if value is not None:
                where.append(f"json_extract(e.payload,'$.{key}') {operator} ?")
                params.append(value)
        if tag is not None:
            where.append("EXISTS (SELECT 1 FROM json_each(e.payload,'$.tags') WHERE value=?)")
            params.append(tag)
        if cursor:
            try:
                if len(cursor) > 1024:
                    raise ValueError()
                body, sig = cursor.split('.')
                if not hmac.compare_digest(hmac.new(self.cursor_key, body.encode(), hashlib.sha256).hexdigest(), sig):
                    raise ValueError()
                created, id, bound = json.loads(base64.urlsafe_b64decode(body))
                if bound != filters:
                    raise ValueError()
                where.append('(e.created,e.id)>(?,?)'); params.extend([created, id])
            except (ValueError, TypeError):
                raise SafeError('INVALID_CURSOR') from None
        with self.store.connect() as c:
            rows = c.execute('SELECT e.* FROM entries e JOIN search_index s ON s.entry_id=e.id WHERE ' + ' AND '.join(where) + ' ORDER BY e.created,e.id LIMIT ?', [*params, limit + 1]).fetchall()
            page = rows[:limit]
            token = None
            if len(rows) > limit:
                last = page[-1]
                body = base64.urlsafe_b64encode(encode([last['created'], last['id'], filters]).encode()).decode()
                token = body + '.' + hmac.new(self.cursor_key, body.encode(), hashlib.sha256).hexdigest()
            return {'items': [self.view(row) for row in page], 'next_cursor': token}

    def preview(self, selector: Selector, session):
        criteria = selector.model_dump(mode='json')
        with self.store.connect() as c:
            entries = [self.view(r) for r in c.execute('SELECT * FROM entries WHERE owner_id=? ORDER BY created,id', (self.owner,))]
        items = [x for x in entries if (criteria['ids'] is None or x['id'] in criteria['ids'])
                 and (criteria['types'] is None or x['type'] in criteria['types'])
                 and (criteria['date_from'] is None or x['local_date'] is not None and x['local_date'] >= criteria['date_from'])
                 and (criteria['date_to'] is None or x['local_date'] is not None and x['local_date'] <= criteria['date_to'])]
        # Bound memory and discard expired plans; invalid plans never broaden selection.
        self.plans = {k: v for k, v in self.plans.items() if v['expires'] > self.clock()}
        if len(self.plans) >= 100:
            raise SafeError('PLAN_LIMIT', 429)
        plan_id = str(uuid4())
        refs = [{'id': x['id'], 'revision': x['revision']} for x in items]
        self.plans[plan_id] = {'session': session, 'expires': self.clock() + 300, 'selector': criteria, 'refs': refs}
        return {'plan_id': plan_id, 'count': len(items), 'refs': refs, 'sections': sorted({x['type'] for x in items}), 'expires_in': 300, 'warning': 'Файл містить текст вибраних записів. Зберігайте його обережно.'}

    def export(self, plan_id, format, session):
        p = self.plans.get(str(plan_id))
        if not p or p['session'] != session or p['expires'] <= self.clock():
            raise SafeError('EXPORT_PLAN_EXPIRED', 409)
        # A single read transaction captures exact currents AND history consistently.
        with self.store.connect() as c:
            c.execute('BEGIN')
            items, history = [], []
            for ref in p['refs']:
                try:
                    entry = self.view(self.row(c, ref['id']))
                except SafeError:
                    raise SafeError('EXPORT_CHANGED', 409) from None
                if entry['revision'] != ref['revision']:
                    raise SafeError('EXPORT_CHANGED', 409)
                items.append(entry)
                if p['selector']['include_history']:
                    history += [self.revision_view(r[0]) for r in c.execute('SELECT payload FROM entry_revisions WHERE entry_id=? ORDER BY revision', (entry['id'],))]
            vault_id = c.execute('SELECT vault_id FROM vault_meta').fetchone()[0]
        if format == 'json':
            content = {'entries': items, 'revisions': history}
            return encode({'manifest': {'export_schema_version': 1, 'source_vault_id': vault_id, 'exported_at_utc': now(), 'selector': p['selector'], 'record_counts': {'entries': len(items), 'revisions': len(history)}, 'content_sha256': digest(encode(content).encode())}, **content})
        import html, re
        def escape(text):
            return re.sub(r'([\\`*_{}\[\]()#+.!|>~-])', r'\\\1', html.escape(text, quote=True))
        return '# Вибрані записи\n\n' + '\n\n'.join(f"## {x['id']} · {x['type']}\n\n{escape(x['raw_text'])}" for x in items + history)


def validate_portable(text):
    """Standalone synthetic round-trip validator, NOT an import or merge endpoint."""
    x = json.loads(text)
    m = x['manifest']
    content = {'entries': x['entries'], 'revisions': x['revisions']}
    if m['export_schema_version'] != 1 or m['content_sha256'] != digest(encode(content).encode()):
        raise SafeError('INVALID_EXPORT')
    if m['record_counts'] != {'entries': len(x['entries']), 'revisions': len(x['revisions'])}:
        raise SafeError('INVALID_EXPORT')
    for entry in x['entries'] + x['revisions']:
        p = {k: v for k, v in entry.items() if k in EntryInput.model_fields}
        EntryInput.model_validate(p)
    return content
