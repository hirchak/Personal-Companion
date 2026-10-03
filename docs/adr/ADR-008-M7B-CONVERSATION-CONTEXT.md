# ADR-008-M7B — Conversation-first longitudinal context, FTS-first retrieval

Date: 2026-10-03. Status: USER_REQUIREMENT; M7B implementation awaits external engineering review.
Owner initial46-section goal + two binding addenda in [goal](../../prompts/M7B_CONVERSATION_HOME.md).
This changes the same active M7B; earlier build/checkpoints interim, new final C/full regression required.

## Decision and alternatives

Primary home Розмова, two modes Free Conversation / Deep Session. Persistent ReflectionGoal is explicitly
user-agreed, editable in ACTIVE/PAUSED/COMPLETED, timestamped and versioned. Deep conversations pin exact
revision. Goal edits preserve history; newly agreed revision requires a new deep session.
This replaces equally prominent module navigation; existing journal/creative/health/practices stay secondary.

Use SQLite/filter/FTS5 first. A mandatory vector DB/embedding path was rejected for M7B: no measured retrieval
gap, additional private-data surface and unavailable model authorization. External embeddings prohibited.
Later vector retrieval needs a measured-gap ADR and explicit scope; no silent fallback.

One Conversation Controller, deterministic typed skills/context gates, one future model voice; no multi-agent
swarm or agent framework. All nine new typed skills are contract-only, no clinical activation.
No automatic conversation→journal/memory. Suggested topics, if added, are MODEL_SUGGESTED nonclinical metadata.

## Data, retrieval and failure behavior

Timestamped raw messages with provenance/revisions are authoritative. Source-bound versioned
DailyConversationDigest / GoalContextDigest equivalents are MODEL_DERIVED, never raw replacements.
M7B generator is a deterministic synthetic excerpt fixture, truthfully tagged NOT_LLM; actual model digest
inference DEFERRED because live provider OFF (test gap: model fidelity/tokenizer/authorized inference).
SQL triggers invalidate source edit/delete/goal change, stale digest text removed; raw expansion refuses drift.

Context order: exact goal revision, six recent current turns, goal digest, daily digests, bounded FTS/filter
raw retrieval; narrow expansion into selected exact message revisions; explicit USER_CONFIRMED memory.
Default time range goal.created_at→now or explicit user range. Never whole-history prompt assembly.
Journal/sleep/health separately authorized narrow tool contracts remain OFF stubs (test gap: consent/runtime
integration on authorized data). Metadata-only local RetrievalReceipt includes IDs/revisions/window/digest
versions/method/budgets; no raw private text in logs. Stable operation retry reconstructs exact selection or
SOURCE_CHANGED. Serialized JSON UTF8 byte upper bound enforces token/size limit; model-specific tokenizer
DEFERRED until provider/version is authorized. No external content leaves this builder.

## Compatibility, privacy and rollback

Envelope schema9 adds isolated domain tables/indexes; entry2/health1/practice1 preserved. Migration/backup/
restore exercised only on fixtures; no old owner demo/vault read or migrated. Backup integrity validates
new domains; restore never enables demo/provider. Delete cascades messages/revisions/index and clears derived
text; metadata tombstones/receipts remain. Historical backups/residual SQLite pages may retain copies,
no secure erase claim. Rollback requires a pre-upgrade synthetic backup; do not downgrade schema9 blindly.

Live provider OFF, clinical active0, real private data OFF. All27 review findings OPEN,16 RAW local manifest
only, bounded primary-source checks unchanged. M6-N01 OPEN (early0.6.0 vs final0.6.1 NOT_RUN).
M7C/M8 NOT_STARTED. Engineering PASS cannot authorize activation/content/rights/deploy.
