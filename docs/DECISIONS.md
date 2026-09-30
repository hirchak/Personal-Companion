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
| ADR-009 | PROPOSED_BASELINE | Native Android bridge для автоматичного Health Connect | PWA не обіцяє прямий доступ |
| ADR-010 | PROPOSED_BASELINE | Локальний ASR на Mac, phone audio queue | Mac asleep → transcript later |
| ADR-011 | PROPOSED_BASELINE | Private ideas ≠ public product feedback | Exact-payload approval перед export/publication |
| ADR-012 | PROPOSED_BASELINE | Reviewed self-help і optional game layer | Без medical claims, штрафів і dependence design |
| ADR-013 | PROPOSED_BASELINE | C implementation + R evidence commit | Перевірювані SHA без self-hash recursion |
| ADR-014 | USER_REQUIREMENT · 2026-09-30 | Для test-stage explicit `/goal` власник дозволив normal fast-forward direct pushes у `main` після local checks і privacy scan; review branch optional. Project metadata schema v2 adds an explicit `push_main` permission | `push_main` відокремлений від `merge_main`; force push/rewrite, merge, deploy, paid calls/private data окремо заборонені; architect review відбувається після push; наступна milestone вимагає нової goal |

Для зміни baseline створити ADR із альтернативами, impact на data/safety/compatibility,
rollback і явним рішенням власника, коли змінюються межі або приватність.
Routine internal refactor без зміни контрактів не потребує нового ADR.
