# Рішення (ADR register)

Формат: ID, статус, причина, наслідок, що змінює рішення. Дата bootstrap: 2026-09-30.
`USER_REQUIREMENT` — явно заданий напрям. `PROPOSED_BASELINE` — пропозиція для M0,
не твердження, що рішення вже реалізовано або технічно доведено.

| ID | Статус | Рішення | Наслідок |
|---|---|---|---|
| ADR-001 | USER_REQUIREMENT | Local-first, приватні дані відокремлені від коду | Public repo без vault |
| ADR-002 | PROPOSED_BASELINE | Модульний моноліт Python/React/SQLite | Просте розгортання, без Redis/vector DB |
| ADR-003 | USER_REQUIREMENT | ChatGPT architect/reviewer; Codex виконує /goal | State/reports/Git замість залежності від чату |
| ADR-004 | PROPOSED_BASELINE | Phone local outbox, Mac vault, явний sync | Не називати phone save «вже на Mac» |
| ADR-005 | PROPOSED_BASELINE | Private-origin PWA; Vercel спочатку demo/static public | Hosted personal shell потребує окремого gate |
| ADR-006 | USER_REQUIREMENT | Початковий AI route — власна Codex-підписка | Без автоматичного PAYG |
| ADR-007 | PROPOSED_BASELINE | MiniMax optional, public research first | Перевірка plan/seat/credits/consent |
| ADR-008 | PROPOSED_BASELINE | Один agent voice, typed skills і deterministic gates | Немає autonomous treatment swarm |
| ADR-009 | M6_IMPLEMENTED_AWAITING_REVIEW | Minimal foreground/manual read-only Health Connect bridge | See [ADR-006-M6](adr/ADR-006-M6-HEALTH-BRIDGE.md); PWA remains primary, no background sync |
| ADR-010 | PROPOSED_BASELINE | Локальний ASR на Mac, phone audio queue | Mac asleep → transcript later |
| ADR-011 | PROPOSED_BASELINE | Private ideas ≠ public product feedback | Exact-payload approval перед export/publication |
| ADR-012 | PROPOSED_BASELINE | Reviewed self-help і optional game layer | Без medical claims, штрафів і dependence design |
| ADR-013 | PROPOSED_BASELINE | C implementation + R evidence commit | Перевірювані SHA без self-hash recursion |
| ADR-014 | USER_REQUIREMENT · 2026-09-30 | Для test-stage explicit `/goal` власник дозволив normal fast-forward direct pushes у `main` після local checks і privacy scan; review branch optional. Project metadata schema v2 adds an explicit `push_main` permission | `push_main` відокремлений від `merge_main`; force push/rewrite, merge, deploy, paid calls/private data окремо заборонені; architect review відбувається після push; наступна milestone вимагає нової goal |
| ADR-015 | USER_REQUIREMENT · 2026-10-05 | M8E durable local consent and canonical exact Send | Exact payload freshness and Deep/journal approval remain backend-bound; see [ADR-015](adr/ADR-015-M8E-CONSENT-AND-CONVERSATION-UX.md) |
| ADR-016 | USER_REQUIREMENT · 2026-10-07 | M8E AI is a one-click toggle after valid local consent; local voice is independent of AI consent/state; activation readiness is non-inference and bounded | One first-use acceptance, local-only ASR, sanitized activation codes; external account settings remain unverified/nonblocking; see [ADR-016](adr/ADR-016-M8E-ONE-CLICK-AI-INDEPENDENT-LOCAL-VOICE.md) |

Для зміни baseline створити ADR із альтернативами, impact на data/safety/compatibility,
rollback і явним рішенням власника, коли змінюються межі або приватність.
Routine internal refactor без зміни контрактів не потребує нового ADR.

## M7B owner decisions — 2026-10-03

[ADR-008-M7B-CONVERSATION-CONTEXT](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md): USER_REQUIREMENT,
implementation candidate awaits independent review. Free Conversation + Deep Session; persistent
explicit versioned editable ReflectionGoal exact revision binding; timestamped conversations/raw messages
authority; goal-scoped longitudinal retrieval, source-bound DailyConversationDigest/GoalContextDigest,
source edit/delete invalidation, metadata-only local RetrievalReceipt, deterministic budget.
SQLite/filter/FTS5 first, NO mandatory embeddings/vector DB, NO external embeddings;
measured retrieval-gap ADR required later. One Conversation Controller + typed skills/one model voice,
no swarm, no automatic conversation→journal/memory. Live provider OFF, clinical active0,
real private data OFF; M7C/M8 NOT_STARTED. Earlier M7B checkpoints are interim; late addenda
belong to the same goal and require new final C/full regression before evidence-only R.


## M7C owner scope — 2026-10-04

[ADR-009-M7C-CONVERSATION-RUNTIME](adr/ADR-009-M7C-CONVERSATION-RUNTIME.md) implements the explicit owner synthetic-only goal: one controller/voice, neutral versioned skills, exact goal/context/source bindings, strict inert output, cancellable validated streaming, explicit closure/journal-point confirmation, FTS-first retrieval and bounded existing-auth provider evaluation. Scoped maximum100 total inference attempts includes failed/cancelled/interim/final requests. Broad project live/private permissions remain false. Existing-auth subscription proof is not a public service/retention/legal claim. Project-local whisper.cpp small model under2.5GB authorized; no cloud ASR or global install. M7B external ACCEPT is synthetic engineering only; N01/N02 closure requires exact-C evidence. M7D/M8 NOT_STARTED.
