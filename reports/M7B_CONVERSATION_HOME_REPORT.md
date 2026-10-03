# M7B CONVERSATION_HOME — AWAITING_REVIEW

Base `ff13dfe5b1f546c207c60cc3d4456c2fff28522f`.
Final implementation C `f143dc9f82bb356ca10cbb4034cb8126ecf42aa3`, selected **after both binding owner addenda**.
R is the immediate evidence-only successor; its exact SHA and verified origin/main are supplied in the final
response, avoiding recursive self-hash. Earlier checkpoints are interim. This is the same M7B goal.
External [M7A ACCEPT](M7A_ARCHITECT_REVIEW.md) remains synthetic engineering only; M7B ACCEPT not assigned.

## Result

Default Розмова, primary Розмова/Щоденник/Більше. Persistent timestamped Free Conversations and messages,
normal responder OFF with local USER save, explicitly enabled neutral synthetic mock. Create/send/reopen/
archive/delete, CAS/idempotency, lost response and actual two-process HTTP restart verified. No automatic
conversation→journal/memory/health/tasks/feedback, no psychological inference or agent framework.

Deep Session binds exact explicitly agreed ReflectionGoal revision. Goal ACTIVE/PAUSED/COMPLETED,
UTC timestamps, editable text/history and preserved completion time. Deep UX separates current conversation,
agreed revision and relevant past context. Source-bound versioned Daily/Goal digest equivalents have exact
message IDs/revisions/time window/generator version, MODEL_DERIVED and synthetic NOT_LLM tags. Raw messages
remain authoritative; source edit/delete invalidates derived text/index; goal edit invalidates goal digests.

Deterministic Context Builder: exact goal → recent turns → goal/daily digest → bounded local FTS5/filter raw
retrieval → narrow selected-source expansion; explicit USER_CONFIRMED memory scope only. Default window
from goal.created_at through now or explicit range. Metadata-only local RetrievalReceipt, exact retry
selection or SOURCE_CHANGED. Serialized JSON UTF8 byte upper bound enforces token/size budgets; no whole
history prompt, mandatory vectors or external embeddings. One controller +9 inactive typed skill contracts.

Journal internal filters, persisted tiles/list, native detail/editor/history, compact destructive actions;
creative/space/feedback/health/settings preserved secondary. M4 PCMRecorder/VoicePanel/storage reused:
generated recording/cancel/stop, truthful unavailable ASR, demo-only fake composer transcription, edit +
explicit insert + explicit send with exact revision/hash references. No second audio stack/cloud fallback.
Practice access remains explicit M7A admission-controlled click, production clinical0.

Envelope schema9 adds isolated domains/index/triggers/backup integrity. Entry2/health1/practice1 unchanged.
Delete cascades messages/revisions/index, clears derived text, retains minimal metadata; historical backups/
SQLite residual pages may hold copies, no forensic erase claim. Restore never restores provider/demo permission.
Only fresh fixtures migrated; old owner M7A demo root not read or migrated. No PWA recorder, crypto/transport,
provider/auth/billing or Health permissions changes. [Scope audit](evidence/M7B/SCOPE_AUDIT.json).

## Exact-C evidence

[Commands/exit codes/environment/log hashes](evidence/M7B/EXACT_C_CHECKS.json),
[18 acceptance gates](evidence/M7B/ACCEPTANCE_MATRIX.json),
[all46 sections + both addenda](evidence/M7B/COMPLETION_AUDIT.json).

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q --junitxml=/private/tmp/m7b-exact-C.xml` | 539 PASS, including40 actual built Chromium browser tests; failures/errors/skips0 |
| `npm --prefix apps/web run build` / `npm --prefix apps/web test` | build PASS /46 web unit PASS |
| `node scripts/verify_m7a_schemas.mjs` | 7 independent Ajv checks PASS |
| `.venv/bin/python scripts/m7_admission.py` | structural PASS,27 findings OPEN,16 external packets, RAW local0, clinical0 |
| docs / generated context / privacy / diff | PASS in their stated scopes |
| `.venv/bin/python -m scripts.measure_m7b` | original-synthetic25/100 conversations measured |

M7B adds29 tests:7 conversation,11 goal/retrieval/invalidation/integrity,4 API,1 actual CLI HTTP process
restart and6 browser tests. Earlier regression selectors follow the new navigation; persisted/error/backup/
voice/health/admission assertions retained. One upstream Starlette BlockingPortal deprecation warning only.
Clean C at start/end and unchanged SHA confirmed. Environment Darwin arm64, Python3.13.2/Pydantic2.11.3,
Node26.8.2, actual installed current-session gpt-6.1-sol/high, Default execution/Plan OFF.

[Synthetic performance](evidence/M7B/SYNTHETIC_PERFORMANCE.json): create median1.43–1.49ms,
send1.79–1.85ms, history1.35–1.73ms, reopen1.06–1.08ms, store restart4.70–4.84ms,
context2.94–4.28ms,1932/2000 byte/token upper bound; DB growth77,824/344,064 bytes.
These are local service measurements, not physical-phone/provider/ASR latency.
[Grid/list rendering](evidence/M7B/RENDER_METRICS.json): bounded30-card first page,50 fixture records,
desktop1440/mobile390; no clinical metrics or provider cost claims.

## UI review, demo and documentation

[UI full review + named-fix verdict](evidence/M7B/UI_REVIEW.json): one material mobile composer issue found;
M7B-UI-01 resolved, reviewer disposition ship **for that scored fix**. Current paper/ink/sage/Georgia retained.
32 reviewed original synthetic desktop/mobile PNG frozen; byte-identical UI source matches final C. Those
reviewed captures were produced before commit selection, not misrepresented as exact-C captures; exact-C
browser rerun independently passed. Composer geometry <= viewport verified at390x844 and synthetic390x540
resize, without physical virtual-keyboard acceptance. [Documenter evidence](evidence/M7B/DESIGN_DOCUMENTATION.json).
One detector pass found only pre-existing M5 advisory; pre-existing design format drift not repaired.

```sh
./scripts/m7b_demo.sh /private/tmp/personal-companion-m7b-synthetic-demo
```

Rebuilds with existing dependencies, creates/reuses only marked synthetic root, prints loopback URL and
one-time5-minute code. Enter that terminal code; lock/restart requires a new code. No phone needed.
[Actual command verification](evidence/M7B/DEMO_COMMAND_CHECK.json): fresh synthetic root,4 seeded journal
notes/2 messages, agent-browser unlock/home PASS, browser errors0, no provider; owned server stopped and
owned fixture root removed afterwards. Owner UX acceptance is still pending, not inferred from this check.

PRODUCT, DATA_MEMORY, AI_ORCHESTRATION, ARCHITECTURE, DECISIONS, ROADMAP, M7B_CONTRACT and
[ADR008](../docs/adr/ADR-008-M7B-CONVERSATION-CONTEXT.md) reconcile both addenda; DESIGN updated narrowly.
[Snapshot source/output hashes](evidence/M7B/SNAPSHOT_CHECK.json) freeze pre-R construction with final R
source documents and C HEAD metadata. Final local snapshots are refreshed to R HEAD after publication;
source hashes must stay identical, final output hashes are recorded in ignored FINAL_DELIVERY_VERIFY.json. STATE/HANDOFF/devlog/report updated in evidence R.

## Scope limits and publication

DEFERRED genuine model-generated digest inference/provider tokenizer: live permission OFF; model fidelity/
authorized integration NOT_RUN, synthetic generator explicitly NOT_LLM. Separately authorized journal/sleep/
health tools remain narrow deny/stub contracts; consented-data integration NOT_RUN. Clinical skills remain
contract-only because content/rights/admission unresolved. Vectors require later measured retrieval-gap ADR.
No foundation requirement silently omitted. Real local ASR/private audio/conversation/vault, physical phone/
keyboard, live AI, clinical activation and deploy NOT_RUN. Live provider OFF, real private data OFF, clinical0.
M6-N01 OPEN: early hardware0.6.0 PASS does not verify final0.6.1. M7C/M8 NOT_STARTED.

All27 content findings/statuses/dependencies preserved;16 RAW only external manifest locally, originals not
claimed locally received. Content review, rights review, technical PASS and activation permission separate.
[Privacy](evidence/M7B/EXACT_C_PRIVACY.json) scans public tree/generated and all local Git objects; heuristic
scope plus manual staged original-synthetic/material-rights review, not a proof of secure erase or all privacy.

[Publication gate](evidence/M7B/PUBLICATION_GATE.json) records pre-push evidence-only allowlist and scoped
push_main=true; merge/deploy/liveAI/realData false. Normal fast-forward main push follows R; no force push,
branch, tag, release or next milestone. Remote SHA equality is verified after push in final response.
CI: no GitHub workflow configured; remote CI execution NOT_RUN, local exact-C checks above are PASS.
