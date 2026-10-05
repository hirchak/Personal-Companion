"""Device-local versioned consent and explicit Deep scope; never external account verification."""
import json
from .storage import SafeError, encode, digest, now
from .local_private_ai import PROFILE_ID, PROFILES

CONSENT_VERSION = 1
PRIVACY_VERSION = 'M8E_BOUNDED_TEXT_LOCAL_AUDIO_V1'
DESTINATION = 'OPENAI_EXISTING_CHATGPT_SUBSCRIPTION'

class LocalConsent:
    def __init__(self, store):
        self.store = store
        with store.transaction() as c:
            c.execute('CREATE TABLE IF NOT EXISTS local_profile_consents(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS local_deep_scopes(conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,payload TEXT NOT NULL)')

    def contract(self):
        meta = self.store.meta()
        return {'version': CONSENT_VERSION, 'privacy_version': PRIVACY_VERSION, 'destination': DESTINATION,
                'profile_id': PROFILE_ID, 'profiles': PROFILES, 'vault_id': meta['vault_id'], 'restore_epoch': meta['restore_epoch']}

    def read(self):
        with self.store.connect() as c:
            row = c.execute('SELECT payload FROM local_profile_consents WHERE id=1').fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return data if data.get('contract') == self.contract() else None

    def write(self, data):
        with self.store.transaction() as c:
            c.execute('INSERT OR REPLACE INTO local_profile_consents VALUES(1,?)', (encode(data),))

    def accept(self):
        self.write({'contract': self.contract(), 'accepted_at': now(), 'ai_enabled': True, 'voice_enabled': True,
                    'external_settings': 'NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER'})

    def disable(self):
        data = self.read()
        if data:
            data['ai_enabled'] = False
            self.write(data)

    def revoke(self):
        with self.store.transaction() as c:
            c.execute('DELETE FROM local_profile_consents')
            c.execute('DELETE FROM local_deep_scopes')

    def scope(self, controller, id, selection):
        with self.store.transaction() as c:
            conv = controller.conversations.row(c, id)
            session = controller.deep.session(c, id)
            current_goal = controller.context.row(c, conv.goal_binding.id)
            if current_goal.state != 'ACTIVE':
                raise SafeError('GOAL_NOT_ACTIVE', 409)
            goal = controller.context.row(c, conv.goal_binding.id, conv.goal_binding.revision)
            current_map = controller.deep.effective(c, controller.deep.current(c, session['goal']))
            # Model updates are advisory within scope. Explicit map corrections renew consent.
            actions = [r[0] for r in c.execute('SELECT operation_id FROM deep_actions WHERE json_extract(payload,"$.goal.id")=? AND json_extract(payload,"$.goal.revision")=? AND json_type(payload,"$.items")="array" ORDER BY operation_id', (session['goal']['id'],session['goal']['revision']))]
            value = {'conversation_id': str(id), 'goal': session['goal'], 'goal_text': goal.text,
                     'focus': session['focus'], 'phase': session['phase'], 'session_revision': session['revision'],
                     'selection': selection.model_dump(mode='json'), 'map_user_actions': actions,
                     'history': 'THIS_CONVERSATION_ONLY', 'map': 'THIS_GOAL_REVISION_ONLY', 'journal': 'OFF',
                     'prior_closures': 'THIS_GOAL_REVISION_ONLY'}
        return dict(value, scope_hash=digest(encode(value).encode()), working_map=current_map)

    def approve_scope(self, controller, id, selection, expected_hash):
        value = self.scope(controller, id, selection)
        if value['scope_hash'] != expected_hash:
            raise SafeError('DEEP_SCOPE_CHANGED', 409)
        data = {'scope_hash': value['scope_hash'], 'contract': self.contract(), 'accepted_at': now()}
        with self.store.transaction() as c:
            c.execute('INSERT OR REPLACE INTO local_deep_scopes VALUES(?,?)', (str(id), encode(data)))
        return value

    def require_scope(self, controller, id, selection):
        value = self.scope(controller, id, selection)
        with self.store.connect() as c:
            row = c.execute('SELECT payload FROM local_deep_scopes WHERE conversation_id=?', (str(id),)).fetchone()
        if not row or json.loads(row[0]).get('scope_hash') != value['scope_hash'] or json.loads(row[0]).get('contract') != self.contract():
            raise SafeError('DEEP_SCOPE_APPROVAL_REQUIRED', 409)
