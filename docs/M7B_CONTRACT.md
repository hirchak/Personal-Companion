# M7B — Conversation home and longitudinal context contract

Owner [46-section goal + same-goal addenda](../prompts/M7B_CONVERSATION_HOME.md).
Base ff13dfe5b1f546c207c60cc3d4456c2fff28522f; external M7A ACCEPT synthetic engineering.
This is an implementation candidate, independent review pending. [Owner ADR](adr/ADR-008-M7B-CONVERSATION-CONTEXT.md).

## User flows and authoritative data

Default Conversation home; primary Розмова/Щоденник/Більше. Journal internal filters, persisted local
Плитки/Список preference, compact actions/detail sheets; creative/space/feedback/health/practices/settings
preserved secondary. Native dialogs keyboard trap/Escape/focus return; multiline composer sends only button
or Ctrl/Meta+Enter. IDs/preference only in browser localStorage, message/draft content stays out.

Free Conversation persistent UTC/provenance/private messages; Deep Session binds user-agreed ReflectionGoal
ID/exact revision. Goal ACTIVE/PAUSED/COMPLETED, timestamps/history, editable at any time; old sessions keep
their revision. Deep UX distinguishes current conversation, agreed goal revision, relevant past context.
CAS/idempotency supports lost response/stale retry; normal responder OFF stores USER only, no fake AI.
Only explicit marked synthetic root/flag activates neutral deterministic demo response; no model tools.

Raw message authority; source-bound versioned DailyConversationDigest/GoalContextDigest equivalents,
MODEL_DERIVED, source IDs/revisions/date window/generator version. Source edit/delete invalidates summaries
and FTS index, stale digest text=null. Goal edits invalidate goal digests. Actual generator is explicit
synthetic fixture SYNTHETIC_EXCERPT_V1/DETERMINISTIC_FIXTURE_NOT_LLM, not live model inference.
No automatic conversation→journal/memory, no diagnostic topic inference.

## Deterministic Context Builder and receipts

Order: exact active-session goal revision → six recent current turns → goal digest → daily digests →
local FTS5/filter raw conversation selection → narrow raw expansion; USER_CONFIRMED memory only explicit
scope/exact revision. Goal-scoped default window created_at→now or user-selected UTC range.
SQL preselection limits50 rows/20 FTS matches; max_sources1..50, default16; digest sources<=12;
expansion<=8 sources. Whole history is never loaded into every context.

Local RetrievalReceipt stores goal/revision/window/source refs/digest versions/retrieval method and token/size
budget, plus text-free reconstruction metadata. Retry exact operation reuses selection; stale source fails.
Serialized context JSON UTF8 byte upper bound is the conservative token estimator, not a model tokenizer;
128..12000 token budget,512..48000 byte budget. Oversized mandatory goal fails rather than being truncated.
Expansion budget includes serialized exact message payloads. Logs/evidence never use private raw text.
SQLite/filter/FTS5 first; no mandatory embeddings/vector DB, no external embeddings. Later vectors need
measured retrieval-gap ADR. Journal/sleep/health narrowly authorized tools stay deny/stub contracts OFF.

## Skills, voice, practices and storage

One Conversation Controller + deterministic context helper, one future model voice, no multi-agent swarm.
Nine typed future skills: core_reflection, deep_session, goal_setting, cbt_reflection, worry_rumination,
sleep_review, nightmare_review, grounding, session_closure. All CONTRACT_ONLY_NOT_ACTIVE.
M4 PCMRecorder/VoicePanel/storage reused: record/pause/cancel/stop; local ASR unavailable truthful;
explicit demo fake only, edit + explicit insert into composer + explicit send with transcript revision/hashes.
No second audio subsystem/cloud/model download. Actual ASR backend NOT_RUN.
M7A practice launch explicit click, canonical admission unchanged, production clinical active0.

Envelope schema9 only new tables/FTS/triggers; entry2/health1/practice1 unchanged. Backup includes conversations,
goals/history/derived/receipts; integrity rejects malformed state/index. Restore never restores demo/provider
permission. Delete removes conversation/messages/revisions/index/derived text, minimal metadata remains.
Historical backup/pages may retain copies; forensic erase not claimed. Tests use fresh fixtures exclusively.

## Deferred scope and review gate

DEFERRED genuine model digest inference/model tokenizer: live provider OFF, fidelity/integration test gap.
DEFERRED journal/sleep/health context activation: separate consent unavailable, narrow deny contracts tested.
DEFERRED clinical skills/content: all27 findings OPEN/rights/content gates; contract-only tested.
DEFERRED vectors: no measured-gap ADR. Real ASR/private audio/physical mobile keyboard test NOT_RUN.
These do not block independent preparation/engineering tests; no addendum foundation omitted.

Relevant M1–M7A regressions plus M7B domains/API/process/browser/web, scoped performance, 1440px/390px
synthetic screenshots, privacy/staged review. New final C after addenda → full exact-C checks → evidence-only R
→ normal fast-forward main push → origin==R → AWAITING_REVIEW → stop. Never self-ACCEPT.
Live provider OFF; clinical active0; real private data OFF; no auth/billing/transport/crypto/PWA-recorder changes.
All27 findings OPEN,16 RAW manifest-only locally, primary-source/rights limits unchanged.
M6-N01 OPEN: early0.6.0 hardware PASS is not final0.6.1 verification. M7C/M8 NOT_STARTED.
