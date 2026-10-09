# ADR-017 — Deferred text and bounded content release

Status: implemented candidate for owner-issued M8E-Q03; independent review pending.
Supersedes the pre-validation text preview behavior of ADR-009, not its provider,
source, consent or clinical admission contracts.

Provider transport may stream internally; ConversationController passes no delta
consumer. Public job projections retain partial_candidate:null for wire compatibility.
QUEUED/RUNNING stay unchanged; additive release_status distinguishes GENERATING,
AWAITING_VALIDATION, RELEASED, FAILED and CANCELLED. UI displays neutral progress only.

After structural validation, serialize the complete candidate once, including goal,
closure and map prose. An internal release adapter receives immutable serialized
input and returns a typed decision. No model field, request body or API caller can
provide a decision. The default adapter is local finite contextual rules, not an LLM.
It handles tested attribution/negation, explicit refusals and known claim classes;
universal semantics and qualified content review remain OPEN.

Pin config/version, reviewer class, assessor and controller implementation hashes.
The decision binds request, complete candidate, request metadata (context receipt,
goal/source/skills/profile), attempt and bounded monotonic lifetime. Missing, invalid,
stale, failed or timed-out decisions deny release. Explicit detected current danger
cannot be opened by an injected ALLOW decision: that generated route stays OFF.
Approved crisis resources/qualified routing need a separate content gate; no new
clinical text, contact list, assessor call or therapeutic protocol is activated.

Final publication is one transaction after source/context/profile/policy checks,
with cancellation and private-gate locks ordering release against cancel/revocation.
Recheck the decision immediately before persistence. Message, map and final receipt
commit together or roll back together. Retry is explicit, same-context and same-policy;
attempt binding prevents an old worker/decision from winning a resumed attempt.
Restart fails pending jobs, never reconstructs or releases partial text.

Successful historical receipts are immutable evidence, not reusable authorization
for a later response. Legacy completed rows remain readable and are not represented
as retrospectively assessed by Q03. Restore validates new final receipt hashes.
No storage schema or real-vault migration is introduced; receipt fields live in the
existing typed inference payload. No five-skill admission or source authority changes.

Failure metadata is bounded and sanitized. Unreleased content is never stored in
the job, message, map or closure, and never emitted through polling/page/UI or error
text. Temporary private generation/review memory is unavoidable; adapter timeouts
discard late results. Production adapters are trusted backend code, not user plugins.

Alternatives rejected: CSS-only hiding leaves API leakage; final-only DB validation
still permits streamed disclosure; a safe=true model field is self-approval; a blanket
ban on all conversational content makes the companion unusable; paid model judges or
clinical resources are outside this goal's permissions. Current finite rules have
false-positive/negative limits and must not be called a universal safety classifier.
