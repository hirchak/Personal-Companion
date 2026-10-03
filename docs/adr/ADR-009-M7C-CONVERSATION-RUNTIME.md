# ADR-009 — neutral conversation controller and bounded synthetic inference

Date2026-10-04. USER_REQUIREMENT, implementation candidate awaits independent review.
Authority: prompts/M7C_LIVE_CONVERSATION_CONTROLLER.md. No real-user/clinical activation.

Retain accepted M7B conversation-first goal/raw/context domains and SQLite/filter/FTS5 retrieval.
Use one deterministic controller plus original versioned typed neutral skills and one model voice.
Do not add autonomous agents, embeddings, clinical protocol execution or broad journal/health context.
Exact goal revision, receipt, selected source revisions, context/skill/frame hashes bind each request;
replay before/after inference fails closed on drift. Models supply bounded inert candidates, never commands.
Explicit user preview/agreement changes goals; closure review and USER-authored journal preview/confirm
are separate deterministic actions. No auto promotion. Source changes invalidate summaries.

Use installed first-party Codex app-server existing ChatGPT auth only for this bounded synthetic goal.
Fixed stdio, deny-root/minimal-read, empty roots/tools, sanitized env, no shell/Git/network tools,
ephemeral thread, bounded IO/timeout/process-group cancellation, strict final schema; no implicit retry.
A persistent max100 ledger includes ALL attempted turns, all models and interim/final checks.
SDK host working agreements remain present; document that limitation. Account TYPE is read via supported
RPC and other account fields discarded; credentials never leave the installed CLI. No new auth/PAYG.
MiniMax requires a safe eligible existing route plus included-quota proof; absent here, route stays OFF.

Local ASR is project-local pinned MIT whisper.cpp small multilingual, CPU/Accelerate, <=2.5GB new models,
no cloud. M4 PCM/candidate/edit/insert/explicit send is retained. Filesystem/network own-sentinel tests
and original synthetic Lesya UA TTS benchmark prove only their measured capability, not human quality.
Model/binary/source/audio/assets remain ignored; sanitized checksums/license/metrics may be public.

Alternatives: continuing only mock cannot prove live behavior; unrestricted Codex repository agent
violates data/tool boundaries; new API credentials/PAYG/global ASR install lack authorization;
vector DB adds complexity without measured retrieval gap. Streaming uses actual transport deltas and
never persists partial text; invalid final output fails. Explicit same-context retry never selects another route.

Compatibility: vault schema9→10 migration repairs digest uniqueness/purges legacy UTC derived text;
journal2/health1/practice1 unchanged. Pending inference is FAILED on restart/backup, never auto resumed.
Rollback: defaults remain OFF; disable scoped CLI flags without erasing history or downgrading schema.
Reversal or expansion needs a new owner goal/review. Technical PASS is not activation or clinical acceptance.
M6-N01 and27 content findings remain OPEN; M7D/M8 NOT_STARTED.
