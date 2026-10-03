M7B — CONVERSATION HOME, VOICE COMPOSER & SIMPLIFIED PRODUCT UX

Repository:
https://github.com/hirchak/Personal-Companion.git

Current verified main/base:
ff13dfe5b1f546c207c60cc3d4456c2fff28522f

Reviewed M7A:
C = a68ca709874a6efeb2ec848ec0e246c7264351b7
R = ff13dfe5b1f546c207c60cc3d4456c2fff28522f

External architect verdict:
M7A = ACCEPT — synthetic engineering scope.

M7_PREP remains ACCEPT preparation/tooling scope.
All 27 content/research findings remain OPEN.
Production clinical modules active = 0.

M6-N01 remains OPEN:
final 0.6.1 Health bridge exact hardware smoke NOT_RUN.

==================================================
1. PRODUCT DECISION
==================================================

The current application has grown technically coherent but the user experience is too fragmented.

The primary user need is NOT to navigate a collection of separate modules.

The product should feel like:

“A private place where I can talk, write what is on my mind,
reflect, receive thoughtful questions, and explicitly choose a
reviewed exercise when useful.”

The home experience must therefore be centered around ONE primary screen:

Розмова

Do NOT label the AI “Терапевт”, “Психотерапевт”, “Психолог” or imply professional clinical care.

The interaction may eventually support therapist-like reflective conversation,
but the UI must remain truthful about the system’s role.

Suitable product language:

Розмова
Поговорити
Простір для розмови
Саморефлексія

Avoid medical positioning.

==================================================
2. RECORD PREVIOUS REVIEW
==================================================

At start:

- fetch/verify actual origin/main;
- clean worktree;
- preserve history;
- record external M7A review durably:

  ACCEPT — synthetic engineering scope

  C:
  a68ca709874a6efeb2ec848ec0e246c7264351b7

  R:
  ff13dfe5b1f546c207c60cc3d4456c2fff28522f

- M7A engineering ACCEPT does NOT mean content/clinical validation.
- active clinical remains 0.
- all 27 M7_PREP content findings stay OPEN.
- activate only M7B.

Do not self-assign M7B ACCEPT.

==================================================
3. MAIN UX — ONE SCREEN
==================================================

On normal application launch the main destination should be “Розмова”.

Remove the feeling of a left-side admin dashboard with many independent products.

Primary screen should contain roughly:

top bar
conversation history/action
main conversation area
composer fixed near bottom

Suggested empty state:

“Про що хочеться поговорити?”

Supporting text may communicate that the user can:

- просто виговоритися;
- розібрати думку;
- подивитися на ситуацію з іншого боку;
- пізніше вибрати перевірену практику.

Do not promise therapy, treatment, diagnosis or guaranteed psychological improvement.

Suggested optional starting chips:

Просто поговорити
Розібрати думку
Подивитися з іншого боку
Практики

These are interaction intents, not clinical diagnoses.

==================================================
4. NAVIGATION SIMPLIFICATION
==================================================

Remove the current persistent long list from the primary UX:

Усі записи
Думки
День
Сон
Творчість
Творча полиця
Відгук
Практики
Дані з годинника

Do NOT delete their underlying implementation/data.

New top-level information architecture should be approximately:

Розмова
Щоденник
(optional) Мій простір
Більше / Налаштування

Exact visual solution is autonomous.

Desktop may use:
- compact rail,
- drawer,
- menu button,
- or another clean pattern.

Mobile should use a compact drawer/bottom navigation as appropriate.

The main objective:
the user should NOT be confronted with 8–10 equally important destinations.

==================================================
5. SECONDARY FEATURE PLACEMENT
==================================================

Reorganize existing functionality:

Думки / День / Сон
→ filters inside Щоденник.

Творчість / Творча полиця
→ remove from primary navigation.
Preserve implementation/data and make accessible only through “Більше” or another secondary surface if useful.

Відгук
→ Settings / About / Feedback.
Never primary navigation.

Практики
→ available from conversation + secondary menu.
M7A admission rules remain authoritative.

Дані з годинника
→ Settings / Підключення / Health Connect.
Do not expose technical permission/import screen as a primary daily destination.

Device/technical developer controls
→ secondary settings/developer details.

==================================================
6. CONVERSATION DOMAIN
==================================================

Create a persistent conversation/session domain separate from journal and practice sessions.

Logical entities:

Conversation
Message

Conversation fields should include equivalents of:

- conversation ID;
- created UTC;
- updated UTC;
- title or deterministic short display label;
- state ACTIVE / ARCHIVED / DELETED;
- revision/CAS;
- synthetic/production provenance.

Message fields should include:

- message ID;
- conversation ID;
- role USER / ASSISTANT;
- raw text;
- created UTC;
- revision;
- provenance;
- optional source reference;
- synthetic marker where applicable.

No psychological labels.

No inferred diagnosis.

No hidden “mental state”.

==================================================
7. CONVERSATION PERSISTENCE
==================================================

Support:

- new conversation;
- send message;
- append response;
- reload;
- process restart;
- reopen conversation;
- archive if useful;
- delete conversation;
- list recent conversations.

Use existing transaction/CAS/idempotency principles.

Lost response / duplicate request must not duplicate user messages.

Stale mutation must fail safely.

==================================================
8. SYNTHETIC MOCK DIALOGUE ONLY
==================================================

M7B does NOT authorize live AI.

Implement a deterministic mock/synthetic conversation adapter for UX and engineering tests.

The mock must be clearly non-clinical.

It may:

- acknowledge a synthetic message;
- ask one neutral synthetic follow-up question;
- show how a future conversation feels.

It must NOT pretend to understand psychology.

Do not create a complex rules chatbot.

Example class of fixture response:

“Це тестова відповідь у демо-режимі.
У реальній версії тут буде відповідь помічника.”

or another natural but truthful synthetic response.

Synthetic mode should allow multi-turn UX testing.

Normal production runtime without a provider must truthfully show that conversational AI is unavailable/off,
rather than secretly using the demo responder.

==================================================
9. FUTURE PROVIDER BOUNDARY
==================================================

Design a clean ConversationResponder / provider interface or equivalent.

Future flow:

user message
→ deterministic permission/context controller
→ provider adapter
→ structured candidate response
→ validation
→ display.

But in M7B:

live_provider_calls = false.

No OpenAI.
No Codex runtime.
No MiniMax.
No external LLM.
No local model download.

Do not build an agent framework.

Do not build a multi-agent orchestrator.

Do not let a model choose its own permissions or tools.

==================================================
10. REFLECTIVE CONVERSATION FUTURE CONTRACT
==================================================

The architecture should support future behavior such as:

- reflect what the user said;
- ask a relevant question;
- help separate facts / interpretations / feelings;
- offer another perspective;
- suggest a reviewed practice after explicit consent.

But M7B mock content is not a clinical implementation of these behaviors.

Do not hardcode therapeutic scripts from R01–R16.

Do not copy CBT/IRT/clinical content.

Future reflective behaviors remain gated through M7C/content review.

==================================================
11. COMPOSER
==================================================

The bottom composer is the central control.

Include:

- multiline text input;
- Send button;
- microphone button;
- obvious recording state;
- cancel;
- stop recording.

Keyboard:
Enter behavior should be intentional and accessible.
Do not accidentally send multiline text if Shift+Enter etc. is expected.

On mobile, composer must remain comfortable with virtual keyboard.

==================================================
12. MICROPHONE — USE EXISTING VOICE FOUNDATION
==================================================

Do NOT create a second audio/ASR subsystem.

Reuse M4 voice boundaries/components/storage where practical.

Desired future UX:

tap microphone
→ record locally
→ stop
→ transcript candidate
→ user can edit
→ user explicitly inserts/sends text.

Important:

M7B does NOT authorize real private audio testing by Codex.

Tests must use generated/synthetic audio fixtures.

Actual local ASR backend remains NOT_RUN unless already available under existing authorized environment.

No engine/model download.

No cloud ASR.

No provider fallback.

No remote speech service.

==================================================
13. MICROPHONE UX WHEN ASR IS UNAVAILABLE
==================================================

Do not make microphone button fake.

If recording capability exists but local transcription backend is unavailable:

- record using existing approved local voice path;
- clearly show:
  “Локальне розпізнавання ще не налаштовано”
  or equivalent;
- allow delete/cancel recording;
- do not silently upload it.

If synthetic fake ASR exists in existing test boundaries,
it may be used only in explicit synthetic demo mode and clearly marked.

Never label fake transcript as real transcription.

==================================================
14. NO AUTOMATIC MESSAGE → MEMORY
==================================================

Conversation messages must NOT automatically become long-term memory.

No silent memory extraction.

If future M3 memory proposal integration is added, it requires:

candidate
→ exact source reference
→ user preview
→ explicit confirm.

M7B may show no memory UI at all if cleaner.

==================================================
15. NO AUTOMATIC MESSAGE → JOURNAL
==================================================

Conversation is separate from the journal.

Do not automatically save chat messages as journal entries.

Optionally implement an EXPLICIT user action:

“Зберегти в щоденник”

for a selected user-authored message or explicitly selected text.

If implemented:

- exact preview;
- user initiates it;
- resulting journal entry provenance clearly records user action;
- assistant text is never silently represented as user-authored text.

No automatic daily summary.

==================================================
16. PRACTICE INTEGRATION
==================================================

Reuse the accepted M7A practice engine.

Conversation screen may expose a button/link:

Практики

or:

Спробувати практику

But:

- real clinical modules active = 0;
- only M7A synthetic demo can run in explicit synthetic mode;
- model cannot activate a practice;
- mock conversation cannot activate a practice;
- practice launch requires explicit user click.

Future reviewed assistant suggestion should be:

assistant suggestion
→ user clicks
→ deterministic admission check
→ practice start.

Not:

assistant text → automatic execution.

==================================================
17. JOURNAL UX SIMPLIFICATION
==================================================

Rework Journal into one secondary screen.

Filters inside:

Усі
Думки
День
Сон

Do not keep these as separate global navigation destinations.

==================================================
18. JOURNAL LIST / TILE MODE
==================================================

Add:

Плитки | Список

Remember the local UI preference.

Desktop tiles:
2–3 columns depending on available width.

Mobile:
single column.

Each card should show only useful summary:

- type;
- date;
- short text excerpt;
- optional tags.

Do not permanently expose:

Редагувати
Історія
Видалити

under every card.

Move secondary actions behind:
⋯
or an equivalent compact menu.

==================================================
19. JOURNAL ENTRY DETAIL
==================================================

Clicking a journal item should open a pleasant detailed view.

Prefer:

large side sheet / drawer
or near-fullscreen modal

rather than navigating to a completely unrelated-looking screen.

Show:

- full text;
- metadata;
- edit;
- history;
- delete.

Keep delete protected by confirmation.

Mobile may use full-screen detail.

==================================================
20. HIDE TECHNICAL STATUS FROM DAILY UX
==================================================

Do not repeat technical messages such as:

“AI вимкнено”
“Synthetic demo”
permission implementation details
import internals

across every normal user screen.

Truthfulness remains mandatory, but move technical status to a compact status/settings surface.

Synthetic demo itself must still be obviously marked as demo.

Health permission states remain visible in the Health settings screen where relevant.

==================================================
21. PERSONAL SPACE / GAME LAYER
==================================================

Do not expand gamification in M7B.

Existing personal-space foundation remains intact.

It may appear as:

Мій простір

only if this does not distract from the one-screen conversation redesign.

No streaks.
No penalties.
No health-based reward.
No practice-completion reward.

A fuller cozy/game layer is later.

==================================================
22. CREATIVE FEATURES
==================================================

Do not delete creative domain/data.

Do not redesign it deeply in M7B.

Remove it from primary navigation.

Keep it reachable from “Більше” if necessary for preserving feature access.

No automatic creative analysis from conversations.

==================================================
23. HEALTH
==================================================

Do not expand Health Connect permissions.

Current authorized categories remain:

Sleep
Steps
Exercise

No HR.
No SpO2.
No location.
No history/background expansion.
No health-to-AI context.

Health screen becomes a secondary Connections/Settings destination.

M6-N01 remains OPEN.

==================================================
24. FEEDBACK
==================================================

Move app feedback out of primary navigation.

Suggested:

Налаштування
→ Про застосунок
→ Відгук

Preserve existing exact-preview/private-draft safety boundary.

No automatic sending.

==================================================
25. CONVERSATION DELETE
==================================================

Explicit delete conversation must remove:

- messages;
- revisions;
- indexes;
- session metadata as defined.

Old backups may contain historical copies.

Do not claim forensic secure erase.

Deletion must not affect journal entries explicitly saved earlier.

==================================================
26. BACKUP / RESTORE
==================================================

Conversation sessions/messages must participate coherently in backup/restore.

Test:

- active conversation;
- multiple messages;
- deleted conversation;
- synthetic conversation.

After restore:

- messages preserved where applicable;
- no provider authorization restored;
- no live provider becomes enabled;
- synthetic mode not enabled implicitly.

==================================================
27. SEARCH
==================================================

Do not build semantic vector/RAG search.

If conversation-history search is included, use deterministic local literal/FTS search.

Search never changes memory/provenance.

No embeddings.

==================================================
28. PRIVACY
==================================================

Conversation content is PRIVATE_PERSONAL.

In M7B:

real user data in development = false.

Tests and screenshots:
synthetic only.

Do not log message text.

Do not put conversation text in telemetry/devlogs/evidence.

Logs may contain:

conversation ID
operation ID
status
duration
error category

without payload.

==================================================
29. CONVERSATION UI VISUAL DIRECTION
==================================================

The product should feel:

- quiet;
- private;
- warm;
- minimal;
- not clinical;
- not like an admin panel.

Preserve the existing calm palette if useful, but improve hierarchy and density.

Main conversation should use much more of the available viewport than the current narrow column.

Avoid giant empty desktop margins.

Suggested max readable message width can remain bounded,
but the main application container should feel intentionally centered rather than accidentally narrow.

==================================================
30. MESSAGE PRESENTATION
==================================================

Avoid stereotypical bright chat bubbles if they fight the product aesthetic.

Possible pattern:

USER
subtle aligned block

ASSISTANT
clean readable response block

Do not anthropomorphize excessively.

Do not show avatar pretending to be a doctor/therapist.

Assistant name could simply be:

Помічник

or remain visually unlabeled where clear.

==================================================
31. EMPTY CONVERSATION STATE
==================================================

This is important.

The first screen should immediately explain what to do without a manual.

Possible structure:

Про що хочеться поговорити?

[ text composer ]

Просто виговоритися
Розібрати думку
Подивитися з іншого боку
Спробувати практику

Small privacy line:

“Ваші записи залишаються локально. AI зараз працює лише у демо-режимі.”

In production/provider-OFF mode phrase truthfully according to actual state.

Do not claim AI is active when it is not.

==================================================
32. CONVERSATION HISTORY UX
==================================================

Do not clutter the main view with permanent history sidebar unless it genuinely improves UX.

Preferred:

button/icon
“Розмови”

opens drawer/sheet with recent conversations.

Allow:

- open;
- new;
- delete/archive.

Use simple autogenerated local labels for synthetic demo,
or “Розмова · дата”.

Do not let a mock AI infer sensitive conversation titles.

==================================================
33. RESPONSIVE DESIGN
==================================================

Desktop:
comfortable central conversation + bottom composer.

Mobile:
conversation occupies the screen,
composer stays reachable above virtual keyboard,
menu becomes drawer/bottom sheet.

Test 390px viewport.

No horizontal overflow.

Controls >= appropriate touch size.

==================================================
34. ACCESSIBILITY
==================================================

Keyboard navigation.

Visible focus.

ARIA for:

- menu/drawer;
- composer;
- mic recording state;
- send;
- conversation history;
- journal tile/list switch;
- dialogs/sheets.

Reduced motion.

Do not rely on color alone.

==================================================
35. SYNTHETIC DEMO
==================================================

Provide one command such as:

./scripts/m7b_demo.sh /private/tmp/personal-companion-m7b-synthetic-demo

It should launch:

- synthetic journal records;
- synthetic conversation;
- deterministic mock responder;
- synthetic M7A practice;
- no provider;
- no cloud;
- no real user data;
- no phone requirement.

Demo should make it possible to inspect the intended product UX end-to-end.

==================================================
36. M7B ACCEPTANCE MATRIX
==================================================

Create docs/M7B_CONTRACT.md.

At minimum:

M7B-A01
Default landing destination is the simplified Conversation home.

M7B-A02
Primary global navigation is materially simplified; Day/Thought/Sleep become Journal filters.

M7B-A03
Conversation create/send/reopen/delete/restart persistence works.

M7B-A04
Synthetic responder is explicit/demo-only; normal runtime never pretends it is live AI.

M7B-A05
live provider calls remain zero.

M7B-A06
Conversation does not auto-write journal/memory/health/tasks/feedback.

M7B-A07
Mic UI integrates through existing M4 boundary, with no second audio pipeline/cloud fallback.

M7B-A08
Unavailable ASR is represented truthfully; no fake production transcript.

M7B-A09
Practice launch requires explicit click and M7A admission; clinical active remains zero.

M7B-A10
Journal tile/list switch works and persists locally.

M7B-A11
Journal card opens detail sheet/modal and destructive controls are de-cluttered.

M7B-A12
Creative/feedback/health functionality preserved but removed from primary navigation.

M7B-A13
Conversation backup/restore preserves data without restoring provider/synthetic activation.

M7B-A14
Duplicate/lost/stale message mutations remain idempotent/CAS-safe.

M7B-A15
No message payloads in public evidence/logs.

M7B-A16
Desktop/mobile visual review passes.

M7B-A17
Relevant M1–M7A regressions pass.

M7B-A18
Owner can launch one local synthetic demo and understand the product without navigating technical screens.

==================================================
37. TESTING
==================================================

Run appropriate full regressions because application/UI/storage change.

Include:

- conversation domain tests;
- API auth/CSRF/origin;
- create/send/reopen/delete;
- idempotency;
- stale revision;
- response-loss retry;
- server restart;
- backup/restore;
- provider-OFF truthfulness;
- synthetic responder isolation;
- no downstream mutation;
- mic UI state;
- synthetic audio only;
- ASR unavailable UI;
- journal tile/list;
- journal filters;
- journal detail drawer/modal;
- simplified navigation;
- M7A practice regression;
- M7_PREP validator;
- existing journal/creative/voice/health regression;
- React build/unit;
- Chromium desktop/mobile.

No real private audio.

No real private conversation.

==================================================
38. VISUAL EVIDENCE
==================================================

Capture synthetic-only screenshots:

Desktop + 390px mobile:

- empty conversation;
- conversation with several messages;
- microphone idle;
- recording state;
- ASR unavailable state;
- conversation history drawer;
- simplified menu;
- journal tile view;
- journal list view;
- journal detail;
- practice entry from conversation;
- settings/connections secondary navigation.

Review hierarchy/spacing,
not merely absence of overflow.

==================================================
39. PERFORMANCE
==================================================

Measure synthetic local:

- conversation create;
- append message;
- history list;
- reopen;
- restart;
- journal grid/list render where practical;
- DB growth.

No clinical outcome metrics.

No provider tokens/cost.

==================================================
40. NO MULTI-AGENT / ORCHESTRATOR EXPANSION
==================================================

Do not build:

- agent manager;
- therapist agent;
- journal agent;
- health agent;
- multi-agent routing;
- autonomous planning agent.

Current need is a coherent product shell and deterministic boundaries.

Future orchestration can be introduced only when a real capability requires it.

==================================================
41. CURRENT SAFETY BOUNDARY
==================================================

Do not call the system a therapist.

Do not diagnose.

Do not prescribe.

Do not provide medication guidance.

Do not create autonomous crisis classifier.

Do not infer trauma.

Do not infer hidden psychological state.

Do not activate R01–R16 clinical candidates.

Synthetic conversation is UX engineering only.

==================================================
42. DURABLE DOCS
==================================================

Create/update:

reports/M7A_ARCHITECT_REVIEW.md
with external verdict:

M7A = ACCEPT — synthetic engineering scope

C:
a68ca709874a6efeb2ec848ec0e246c7264351b7

R:
ff13dfe5b1f546c207c60cc3d4456c2fff28522f

Then:

- docs/M7B_CONTRACT.md
- relevant ADR
- reports/M7B_CONVERSATION_HOME_REPORT.md
- reports/evidence/M7B/*
- STATE.md
- HANDOFF.md
- ROADMAP.md
- TESTING docs
- append-only devlog
- regenerated context.

Carry:

all27 research findings OPEN.
clinical active0.
M6-N01 OPEN.

==================================================
43. PERMISSIONS
==================================================

Remain unchanged:

live_provider_calls = false
access_real_user_data = false
deploy = false

No private vault.
No real girlfriend data.
No real therapy conversations.
No provider/auth/billing changes.
No ASR model download.
No Health expansion.
No Tailscale.
No deploy/release/publication.

==================================================
44. GIT WORKFLOW
==================================================

Standing owner direct-main workflow:

implementation/fixes
→ final C
→ exact-C tests
→ evidence-only R
→ privacy/public-tree review
→ normal fast-forward push main
→ verify origin/main == R
→ STOP.

No review branch.
No force push.
No M7C.
No M8.

==================================================
45. DEFINITION OF DONE
==================================================

M7B is ready for independent review when:

- M7A external ACCEPT durably recorded;
- app opens into one clear Conversation home;
- persistent sidebar complexity materially reduced;
- text conversation flow works end-to-end with synthetic mock;
- mic button and recording states are integrated through existing voice boundary;
- no second ASR/audio stack exists;
- normal runtime never fakes live AI;
- journal uses internal filters instead of separate top-level screens;
- tile/list toggle works;
- journal details open cleanly;
- creative/feedback/Health are secondary but preserved;
- practice access remains explicit/admission-controlled;
- production clinical modules = 0;
- live provider calls = 0;
- regressions/build/browser/privacy PASS;
- local M7B synthetic demo works;
- C/R pushed to main;
- M7C/M8 NOT_STARTED.

==================================================
46. FINAL RESPONSE
==================================================

Return:

Base SHA
final C
R
origin/main
M7B status
Python/web/browser counts
Conversation tests
Journal UX tests
Voice/mic status
ASR real backend status
live provider calls
production clinical active count
synthetic conversation mode
practice integration
privacy
demo command
CI status
NOT_RUN items
M6-N01
M7C/M8 status

Do not start next goal.

# Binding owner addenda — same M7B goal (2026-10-03)

LONGITUDINAL CONTEXT & DEEP SESSION GOALS and LATE OWNER ADDENDUM HANDLING are
binding extensions of this same goal. No restart or second milestone. Earlier code/build/checkpoints
are interim; final C must include the addenda, followed by affected tests and full M7B regression,
then evidence/docs-only R, normal fast-forward main push, origin==R, AWAITING_REVIEW, stop.

1. Persistent explicit user-agreed DeepSessionGoal/ReflectionGoal: ACTIVE/PAUSED/COMPLETED,
created_at/updated_at/completed_at, immutable revision history, user edit at any time;
goal changes never rewrite history; deep conversations bind exact goal revision.
2. Free conversations/messages persist exact timestamps/provenance; no automatic journal copy.
Optional MODEL_SUGGESTED nonclinical topic metadata is neither confirmed memory nor diagnosis.
3. Deterministic token-budget Context Builder: exact goal revision, recent/current session turns,
goal digest, daily digests, local FTS/filter raw conversation retrieval, narrow exact source expansion,
USER_CONFIRMED memory only within explicit scope. Journal/sleep/health require separately
authorized narrow tools. Default longitudinal range goal.created_at through now or explicit user range.
Never load the whole history into every prompt.
4. Versioned DailyConversationDigest / GoalContextDigest equivalents bind message IDs/revisions,
date range and generator version. Edit/delete/source revision invalidates dependent artifacts.
MODEL_DERIVED digests never replace authoritative raw conversation messages.
5. Local RetrievalReceipt binds goal/revision, time window, exact sources/revisions, digest versions,
retrieval method and token/size budgets. Never log raw private text.
6. SQLite/filter/FTS5 first; no mandatory embeddings/vector DB in M7B. No external embeddings.
Later vector retrieval requires measured retrieval-gap ADR.
7. One Conversation Controller and one model voice; typed skills compose one future request, no
multi-agent swarm. Contract-only future skills: core_reflection, deep_session, goal_setting,
cbt_reflection, worry_rumination, sleep_review, nightmare_review, grounding, session_closure.
Clinical content must not be activated.
8. Deep UX visibly distinguishes current conversation, current agreed goal/exact revision and relevant
past context; goal edit/pause/complete/history/new must be accessible.
9. Reconcile PRODUCT, DATA_MEMORY, AI_ORCHESTRATION, ARCHITECTURE, DECISIONS, ROADMAP,
M7B_CONTRACT and conversation-first longitudinal/FTS-first ADR; regenerate context snapshots.
10. Keep live provider OFF, clinical active0, real private data OFF, M7C/M8 NOT_STARTED.

If unsafe work would materially expand M7B, implement its safe foundation and mark the exact remainder
DEFERRED with a concrete reason/test gap. Do not silently omit an owner requirement.
