"""Bounded local release decisions; no universal semantic or clinical safety claim.

Finite contextual/attribution rules cover known classes and tested variants. They
are neither a clinical classifier nor a model judge. High-risk unverified routes
fail closed. The controller owns the decision and never accepts one from a model.
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import queue
import re
import threading
import time
import unicodedata

from .storage import REPO, SafeError, digest, encode

POLICY = REPO / 'apps/core/policies/conversation_release.json'
REASONS = {'ORDINARY_BOUNDED', 'USER_BOUNDARY', 'DIAGNOSTIC_OR_TREATMENT_CLAIM',
           'ROLE_CLAIM', 'GUARANTEE_OR_REASSURANCE', 'FALSE_BELIEF_ENDORSEMENT',
           'UNREQUESTED_EXERCISE', 'INVENTED_SLEEP_MEASUREMENT', 'FICTION_PATHOLOGIZED',
           'IMMEDIATE_DANGER_REVIEW_REQUIRED', 'AMBIGUOUS_RISK_REVIEW_REQUIRED',
           'AMBIGUOUS_CLARIFICATION', 'FICTION_OR_QUOTATION'}


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().replace('’', "'").split())


def matches(pattern, text):
    return re.search(pattern, text, re.IGNORECASE) is not None


def candidate_texts(candidate, payload):
    # Cover every visible/persisted prose field, including maps and closures.
    yield candidate['assistant_text']
    if candidate.get('goal_suggestion'):
        yield candidate['goal_suggestion']
    if candidate.get('closure'):
        closure = candidate['closure']
        yield from closure['discussed']
        yield closure['clearer']; yield closure['unresolved']
        yield from closure['possible_steps']
    for item in (candidate.get('working_map') or {}).get('items', []):
        if (item.get('provenance') == 'USER_STATED'
                and item.get('source_refs') == [payload['current_message_ref']]
                and any(item['text'] in p['text'] for p in payload['context']
                        if p['source_refs'] == [payload['current_message_ref']] and p['kind'] == 'CURRENT_TURN')):
            continue  # literal user-authored content; final Deep ingestion still verifies provenance
        yield item['text']


def authored_clauses(text, payload):
    """Strip exact supplied quotations, not arbitrary quote-marked prescriptions.

Fiction attribution is allowed only with a fictional current context. Negation
is evaluated per clause below. Unquoted endorsement after a quote still counts.
"""
    current = current_text(payload)
    sources = [normalized(p['text']) for p in payload['context']]
    fiction = matches(r'художн|персонаж|у романі|вигадан|історію|цитат', current)
    def remove_quote(match):
        quote = normalized(match.group(1) or match.group(2) or match.group(3))
        if any(quote in source for source in sources):
            return ' '
        prefix = normalized(text[max(0, match.start() - 80):match.start()])
        if fiction and matches(r'(?:репліка|слова|цитата) (?:персонажа|героя|героїні)\s*:\s*$', prefix):
            return ' '
        return match.group()
    clean = re.sub(r'«([^«»]{1,1000})»|“([^“”]{1,1000})”|"([^"\n]{1,1000})"', remove_quote, text)
    clean = re.sub(r'^\s*>\s*([^\n]+)', lambda m: ' ' if any(normalized(m.group(1)) in source for source in sources) else m.group(), clean, flags=re.MULTILINE)
    return [normalized(c) for c in re.split(r'[.!?\n]+|\b(?:але|проте|однак)\b', clean) if c.strip()]


def current_text(payload):
    return normalized(' '.join(p['text'] for p in payload['context']
        if p['source_refs'] == [payload['current_message_ref']] and p['kind'] == 'CURRENT_TURN'))


def current_route(payload):
    text = current_text(payload)
    fiction = matches(r'художн|персонаж|у романі|вигадан|історію|цитат', text)
    unquoted = re.sub(r'«[^«»]*»|“[^“”]*”|"[^"\n]*"', ' ', text)
    pattern = r'\bя (?:(?:зараз|сьогодні|тепер) )?(?:можу|збираюся|планую|хочу).{0,45}(?:завдати собі шкоди|нашкодити собі|самоушкодження|вбити себе)|\bя (?:зараз )?(?:у|в) безпосередній небезпеці'
    clauses = [c for c in re.split(r'[.!?]+|\b(?:але|проте|однак)\b', unquoted)
               if not matches(r'(?:персонаж|герой|героїня).{0,30}(?:говорить|каже|репліка)', c)]
    immediate = any(matches(pattern, c) for c in clauses) or (not fiction and matches(pattern, text))
    return text, fiction, immediate


def is_denial(clause, subject):
    patterns = {
        'role': r'\b(?:не є|не являюсь|не психолог|не лікар|не ваш психолог|не ваш лікар|не можу бути)',
        'diagnosis': r'\b(?:не (?:можу |буду |маю права )?(?:визнач|діагност|ствердж|признач)|не (?:є |дає )?(?:доказ|підстав)|не означає)',
        'guarantee': r'\b(?:не (?:можу |буду )?(?:гарант|обіц)|неможливо гарантувати)',
        'exercise': r'\b(?:не (?:буду |будемо |потрібно |треба |маєте )?(?:викон|робити|почин|закрив|дихати|продовж|пропон)|не хочете вправ|без вправ)',
    }
    return matches(patterns[subject], clause)


@dataclass(frozen=True)
class ReviewInput:
    payload_json: str
    candidate_json: str
    request_hash: str
    metadata_hash: str
    policy_hash: str
    attempt: int


@dataclass(frozen=True)
class Decision:
    verdict: str
    reason: str
    request_hash: str
    metadata_hash: str
    candidate_hash: str
    policy_hash: str
    attempt: int
    issued: float
    expires: float


class ReleaseRejected(SafeError):
    def __init__(self, decision):
        super().__init__('CONTENT_REVIEW_REQUIRED' if decision.verdict == 'REQUIRE_REVIEW' else 'CONTENT_RELEASE_REJECTED')
        self.decision = decision


class BoundedReviewer:
    def review(self, item):
        payload = json.loads(item.payload_json); candidate = json.loads(item.candidate_json)
        current, fiction, immediate = current_route(payload)
        clauses = [c for text in candidate_texts(candidate, payload) for c in authored_clauses(text, payload)]
        prose = ' '.join(clauses)
        refusal = matches(r'не хочу вправ|не пропонуйте вправ|без вправ|не хочу.{0,45}(?:дихан|спростов|уявляти|міняти сюжет)', current)
        stop = matches(r'\bстоп\b|зупинімося|зупинитися|досить[.! ]|зупиняємо|закінчимо тут', current)
        no_questions = matches(r'без (?:нового )?(?:питань|запитань|питання)|не (?:ставте|задавайте).{0,10}(?:питань|запитань)', current)
        reason = 'ORDINARY_BOUNDED'; verdict = 'ALLOW'
        if immediate:
            verdict, reason = 'REQUIRE_REVIEW', 'IMMEDIATE_DANGER_REVIEW_REQUIRED'
        else:
            for clause in clauses:
                if matches(r'\bя (?:ваш |ваша )?(?:ліцензований |ліцензована )?(?:психолог|лікар|психотерапевт)', clause) and not is_denial(clause, 'role'):
                    verdict, reason = 'REJECT', 'ROLE_CLAIM'; break
                diagnosis = matches(r'\bу вас (?:є |саме |точно )?(?:депресія|птср|психічний розлад|тривожний розлад|апное)|\b(?:призначаю|призначу) (?:вам )?лікування|\b(?:приховану?|пригнічену?) травм', clause)
                if diagnosis and not is_denial(clause, 'diagnosis'):
                    verdict, reason = 'REJECT', 'FICTION_PATHOLOGIZED' if fiction else 'DIAGNOSTIC_OR_TREATMENT_CLAIM'; break
                treatment = matches(r'приймайте.{0,35}(?:мг|таблет|ліки|препарат)|(?:збільште|зменште|змініть) дозу|скасуйте препарат|лягайте о \d{1,2}[:.]\d{2}', clause)
                denied_treatment = matches(r'не (?:приймайте|збільште|зменште|змініть|скасуйте|лягайте)|не (?:можу |буду )?признач', clause)
                if treatment and not denied_treatment:
                    verdict, reason = 'REJECT', 'DIAGNOSTIC_OR_TREATMENT_CLAIM'; break
                if matches(r'\bгарантую\b|\bобіцяю.{0,50}(?:ніколи|все)|\bточно (?:все буде добре|нічого.{0,15}не станеться)', clause) and not is_denial(clause, 'guarantee'):
                    verdict, reason = 'REJECT', 'GUARANTEE_OR_REASSURANCE'; break
                exercise = matches(r'\b(?:вправ|релаксац|спростув|перепишіть сюжет|закрийте очі|дихайте)', clause)
                forced = matches(r'\b(?:мусите|зобов.язані|повинні|потрібно виконати|потрібно.{0,15}спрост|все одно потрібно|попри відмов|попри небажан|не можна зупин)', clause)
                unreviewed_steps = matches(r'закрийте очі|дихайте|почніть (?:вправ|релаксац)', clause)
                if exercise and (forced or refusal or unreviewed_steps) and not is_denial(clause, 'exercise'):
                    verdict, reason = 'REJECT', 'UNREQUESTED_EXERCISE'; break
                if not fiction and matches(r'сусіди.{0,35}(?:читають|керують).{0,20}думк', current) and matches(r'(?:так|точно|справді).{0,30}сусіди|сусіди (?:точно|справді)|це (?:правда|справді так)|ви (?:цілком |повністю )?праві', clause):
                    verdict, reason = 'REJECT', 'FALSE_BELIEF_ENDORSEMENT'; break
                if matches(r'не знаю|невідом', current) and matches(r'ви спали (?:рівно )?\w+ годин без пробуджень|(?:waso|васо)\s*[:=]\s*0', clause):
                    verdict, reason = 'REJECT', 'INVENTED_SLEEP_MEASUREMENT'; break
            if verdict == 'ALLOW' and (stop or no_questions):
                from .conversation_controller import generated_text, main_question_count
                example_requested = matches(r'формулювання|уточнення для|складіть репліку', current)
                questions = main_question_count(candidate['assistant_text'], payload) if example_requested and not stop else any(
                    '?' in generated_text(text, payload, examples=False) for text in candidate_texts(candidate, payload))
                if questions or (stop and matches(r'продовжимо|ще трохи|все одно|давайте продовж', prose)):
                    verdict, reason = 'REJECT', 'USER_BOUNDARY'
            if verdict == 'ALLOW' and matches(r'без завдань|не призначайте|нічого не обираю', current):
                if (candidate.get('closure') or {}).get('possible_steps'):
                    verdict, reason = 'REJECT', 'USER_BOUNDARY'
            if verdict == 'ALLOW' and not fiction and matches(r'хочеться зникнути|все скоро закінчиться', current):
                if matches(r'що ви маєте на увазі|йдеться про.{0,40}(?:теперішн|безпек)|це про.{0,40}(?:теперішн|безпек)', prose):
                    reason = 'AMBIGUOUS_CLARIFICATION'
                else:
                    verdict, reason = 'REQUIRE_REVIEW', 'AMBIGUOUS_RISK_REVIEW_REQUIRED'
            elif verdict == 'ALLOW' and fiction:
                reason = 'FICTION_OR_QUOTATION'
        stamp = time.monotonic()
        return Decision(verdict, reason, item.request_hash, item.metadata_hash,
                        digest(item.candidate_json.encode()), item.policy_hash,
                        item.attempt, stamp, stamp + 30)


class ReleasePolicy:
    def __init__(self, reviewer=None):
        self.reviewer = reviewer or BoundedReviewer()

    def identity(self):
        try:
            config = json.loads(POLICY.read_text())
            if (set(config) != {'schema_version','version','assessor','maximum_decision_age_seconds',
                    'ordinary_bounded_release','immediate_danger_generated_release','qualified_content_review',
                    'universal_semantic_safety','unknown_high_risk_decision','provider_calls'}
                    or type(config['schema_version']) is not int or config['schema_version'] != 1
                    or config['version'] != '1.0.0-bounded' or config['assessor'] != 'LOCAL_COMPOSITIONAL_RULES'
                    or config['immediate_danger_generated_release'] is not False
                    or config['ordinary_bounded_release'] is not True
                    or config['maximum_decision_age_seconds'] != 30
                    or config['qualified_content_review'] != 'PENDING'
                    or config['universal_semantic_safety'] != 'NOT_ESTABLISHED'
                    or config['unknown_high_risk_decision'] != 'REQUIRE_REVIEW'
                    or type(config['provider_calls']) is not int or config['provider_calls'] != 0):
                raise ValueError()
            return digest(encode({'config': config, 'implementation': digest(Path(__file__).read_bytes()),
                                  'controller_implementation': digest(Path(__file__).with_name('conversation_controller.py').read_bytes()),
                                  'reviewer_type': type(self.reviewer).__module__ + ':' + type(self.reviewer).__qualname__}).encode())
        except (OSError, ValueError, KeyError, TypeError):
            raise SafeError('CONTENT_POLICY_INVALID') from None

    def evaluate(self, payload, candidate_json, job, deadline, cancel):
        item = ReviewInput(encode(payload), candidate_json, job['request_hash'],
                           digest(encode(job['request_metadata']).encode()),
                           job['release_policy_hash'], job['attempt'])
        result = queue.Queue(maxsize=1)
        def work():
            try: result.put(self.reviewer.review(item))
            except Exception: result.put(None)  # exception text is never retained or emitted
        threading.Thread(target=work, daemon=True).start()
        while True:
            if cancel.is_set(): raise SafeError('CANCELLED')
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise SafeError('CONTENT_DECISION_TIMEOUT')
            try: decision = result.get(timeout=min(remaining, .02)); break
            except queue.Empty: pass
        self.verify(decision, item)
        if decision.verdict != 'ALLOW':
            raise ReleaseRejected(decision)
        return decision, item

    def verify(self, decision, item):
        if (type(decision) is not Decision or not isinstance(decision.reason, str) or not isinstance(decision.verdict, str)
                or type(decision.attempt) is not int or decision.attempt < 1
                or decision.reason not in REASONS or decision.verdict not in {'ALLOW', 'REJECT', 'REQUIRE_REVIEW'}
                or type(decision.issued) not in (float, int) or type(decision.expires) not in (float, int)
                or not math.isfinite(decision.issued) or not math.isfinite(decision.expires)):
            raise SafeError('CONTENT_DECISION_INVALID')
        if decision.verdict == 'ALLOW' and decision.reason not in {'ORDINARY_BOUNDED','AMBIGUOUS_CLARIFICATION','FICTION_OR_QUOTATION'}:
            raise SafeError('CONTENT_DECISION_INVALID')
        if (decision.request_hash, decision.metadata_hash, decision.candidate_hash, decision.policy_hash, decision.attempt) != (
                item.request_hash, item.metadata_hash, digest(item.candidate_json.encode()), item.policy_hash, item.attempt):
            raise SafeError('CONTENT_DECISION_BINDING_CHANGED')
        stamp = time.monotonic()
        if not decision.issued <= stamp < decision.expires <= decision.issued + 30:
            raise SafeError('CONTENT_DECISION_STALE')
        if self.identity() != item.policy_hash: raise SafeError('CONTENT_POLICY_CHANGED')
        if decision.verdict == 'ALLOW' and current_route(json.loads(item.payload_json))[2]:
            raise SafeError('CONTENT_REVIEW_REQUIRED')  # clinical/crisis release remains OFF, even for an injected adapter

    def receipt(self, decision):
        value = {k: getattr(decision, k) for k in ('request_hash','metadata_hash','candidate_hash','policy_hash','attempt','reason')}
        return dict(value, schema_version=1, verdict='ALLOW', policy_version='1.0.0-bounded',
                    receipt_hash=digest(encode(value).encode()))


def valid_receipt(job):
    """Historical release integrity; current policy upgrades do not rewrite history."""
    try:
        r = job['release_receipt']
        fields = {k: r[k] for k in ('request_hash','metadata_hash','candidate_hash','policy_hash','attempt','reason')}
        return (type(r['schema_version']) is int and r['schema_version'] == 1 and r['verdict'] == 'ALLOW'
                and r['policy_version'] == '1.0.0-bounded'
                and type(r['attempt']) is int and r['attempt'] > 0
                and isinstance(r['policy_hash'],str) and re.fullmatch('[0-9a-f]{64}',r['policy_hash']) is not None
                and r['reason'] in REASONS and r['receipt_hash'] == digest(encode(fields).encode())
                and r['request_hash'] == job['request_hash']
                and r['policy_hash'] == job['release_policy_hash']
                and r['metadata_hash'] == digest(encode(job['request_metadata']).encode())
                and r['candidate_hash'] == digest(encode(job['candidate']).encode())
                and r['attempt'] == job['attempt'])
    except (KeyError, TypeError, ValueError):
        return False
