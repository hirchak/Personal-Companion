# ADR-016 — One-click AI and independent local voice

2026-10-07 · USER_REQUIREMENT · M8E owner UX hotfix; engineering candidate awaits independent review.

The conversation AI control is an ON/OFF toggle. Existing valid durable AI consent supports direct one-click
resume; new or revoked consent uses one concise first-use sheet and one acceptance action. Runtime startup does
not silently enable AI. External ChatGPT/Codex settings remain owner-controlled, unverified, and nonblocking;
their reminder lives only in More → AI & Privacy.

Local microphone capture and pinned whisper.cpp do not depend on AI consent or AI runtime state. The authenticated
local session is the permission boundary. The first microphone action may prepare the local engine; missing or
unverified assets leave recording and local persistence available and produce a sanitized recovery status.
AI disable/revoke preserves local voice state and history. Authentication lock/expiry suspends both runtimes.
Cloud ASR and raw-audio provider fields remain prohibited; transcription creates an editable draft and never
automatically sends it.

AI activation may perform only bounded existing-session readiness: initialize the existing Codex app-server,
read account type without refreshing tokens, and list supported models/efforts. Account details are discarded.
No thread, turn, prompt, inference ledger reservation, new auth, fallback, or PAYG is permitted for readiness.
Only stable sanitized codes and mapped recovery text reach the interface.

Alternatives rejected: repeat consent prompts for a valid existing consent; coupling local recording to AI;
blocking capture on absent ASR assets; probing readiness by sending an inference; exposing raw backend errors.
The exact canonical payload, source freshness, Deep scope, journal-default-OFF, clinical/Health-OFF, and
phone-transport-OFF contracts remain unchanged. No owner vault was read or modified for this candidate.
