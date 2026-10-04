# ADR-010 — Source-bound working understanding and exact context preview

Status: IMPLEMENTED_AWAITING_REVIEW, 2026-10-04. Owner M7D scope, no clinical authority.

Keep the accepted single ConversationController and extend SQLite to schema11 with deep_sessions,
working_maps, deep_actions and deep_context_previews. Goals remain the accepted versioned domain;
sessions pin exact goal revisions, own editable focus/phase and user-controlled pause/close.

Store every map revision with source revisions, typed provenance and provider/skill/request metadata.
Provider produces compact candidates; controller validates exact aliases and source liveness. USER_STATED
requires a literal quote from a USER_AUTHORED source. USER_CONFIRMED requires an explicit action.
Model text never confirms/rejects, edits a goal or writes journal/memory/practice/health. Historical versions
remain intact; current read views derive STALE when a dependency changes. This map is not M3 memory.

Preview freezes historical retrieval plus bounded map/closure snapshot and the exact draft hash.
InferenceStart binds receipt/context/preview hashes. Its final receipt adds only that explicit current USER
message. Reassembly before execution and before commit checks source revisions, map/session hashes,
goal pin, skill hashes and model/effort/profile. Source edits, focus edits or map corrections require a new
preview. Retry preserves exact context/profile and never falls back. Serialized payload size remains bounded.

No vector retrieval, extra agents, hidden reasoning, clinical scripts or automatic phase changes. Five
specialist packages are metadata-only qualification dependencies outside the runtime prompt loader.
The existing isolated subscription process now validates effort against model/list before turn/start.
Catalog support and completed synthetic inference are distinct evidence. M7D gets a separate persistent48
attempt ledger; M7C ledger is unchanged. Strongest bounded practical comparison uses max on Luna and catalog-supported ultra on Sol,
with120s controller deadline. Unsupported/timeout/tool requests fail closed and remain evidence.

Limits: finite map capacity requires manual relevance review; exact-text rejection suppression is not a
semantic truth oracle. Provider retention/private suitability and human ASR remain separate hard gates.
