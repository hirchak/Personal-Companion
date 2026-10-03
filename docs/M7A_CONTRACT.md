# M7A — deterministic practice/session contract

Full goal: prompts/M7A_GENERIC_PRACTICE_ENGINE.md, base9b3d8c7171920074fb9b755274d5879a0972c4ff.
Contract/gates are pending final acceptance evidence; no self ACCEPT.

Canonical M7_PREP registry remains authority, OFF, all27 content findings OPEN. Structural hardening
closes constrained JSON-schema maps with additionalProperties=false; independent Ajv negative tests.
Runtime boundaries are typed explicit receipts, not an alternative research/status table.
Current production candidates cannot run; no real production activation receipt exists. Synthetic
receipt only applies to original neutral synthetic:walkthrough and explicit --synthetic-practices
on the existing marked SYNTHETIC_M1 root. This flag cannot admit real OFF candidates.

Finite linear package schema1: supported static/ack/text/choice/completion primitives, exact normalized
content hash (exclude content_hash), bounded plain text/size, unique IDs/entry/declared next targets,
terminal completion; no branches/eval/scripts/actions/paths/imports/HTTP/providers.
Responses are plain user text. They never enter journal/memory/health/tasks/feedback.

Vault envelope schema7 adds separate sessions/revisions/receipts/minimal tombstones, preserving entry
schema2 and health import schema1. BEGIN IMMEDIATE/CAS/operation IDs enforce idempotency and no stale
writes. New session IDs deterministic per operation ID. Editing current response retains its previous
explicit value as revision. No inferred meanings/diagnosis/risk routing/rewards/reminders/weekly analytics.
Runtime admission revalidated before new transitions; invalidation pins BLOCKED_BY_ADMISSION, keeps
responses, and cannot replace package version. Stop/delete remain possible. Terminal sessions never
resume; new start means a separate session. Neutral journal functions do not depend on admission.

Backup is existing SQLite consistent vault snapshot, no new storage/sync. Restore blocks ACTIVE/PAUSED
sessions, preserves all user responses/terminal sessions and invalidates old operation fingerprints;
activation config/receipt is not restored. Revalidation occurs independently against current package/
registry/implementation/config/restore epoch. No automatic resume, permission or provider restoration.
Current selected-entry journal exports exclude practice responses. Practice session data participates
in explicit backup only; API exact-session read is local/authenticated. No auto-export/share/upload.
Delete cascades response revision rows and clears receipt fingerprints; minimal id/revision/time and
operation IDs retained solely to prevent duplicate resurrection. Old backups/SQLite residual pages can
contain historical copies: no forensic secure-erase claim. Journal notes are never deleted by practice delete.

Primary Mac/local web, responsive narrow viewport. Practice cross-device sync is M7A-deferred for separately
authorized M8/pilot integration: current M2 phone contract handles journal domains, adding practice sync
would enlarge scope. No second sync/cloud/Tailscale/phone prerequisite.

## Acceptance gates (exact-C evidence recorded in successor R)

A01…A18 follow section35 of owner goal; full mapping will be recorded with tests/commands in
reports/evidence/M7A/ACCEPTANCE_MATRIX.json. Required proof includes actual built browser UX,
actual server restart, standalone schema validation, backup/invalidation/privacy/full regressions.

| Gate | Required result | Evidence/test anchor |
|---|---|---|
| M7A-A01 | Production clinical active0; normal catalog excludes synthetic | test_normal_runtime_and_demo_namespace_cannot_activate_real_off; built normal catalog |
| M7A-A02 | Exact module/version/package/admission/runtime receipt binding | API auth/hash tests; invalidation matrix; typed RuntimeReceipt production requirements |
| M7A-A03 | Explicit flag + marked root; valid real OFF shadow package cannot run | test_demo_requires_boolean_flag_and_marked_root; normal/demo OFF candidate test |
| M7A-A04 | Finite strict data packages, no executable structure | 14 package mutation cases + blank/inert text tests |
| M7A-A05 | Exact response/step/state across actual restart | five process restart states; test_server_termination_restart_resume_saved_exact_step |
| M7A-A06 | Valid transitions, terminal state never resumes | test_full_state_machine_edits_idempotency_stop_delete; response/skip rules |
| M7A-A07 | Pause/resume, optional skip, manual stop/exit; no penalty | built complete/pause/refresh/resume/skip flow; stopped/blocked browser |
| M7A-A08 | Durable operation receipts/CAS, duplicate races/loss/stale writes | duplicate operation race; browser lost response + stale input; blocked receipt replay |
| M7A-A09 | Exact package pin; new version creates separate session | test_package_pin_new_version_creates_separate_session |
| M7A-A10 | Registry/package/source/claim/rights/technical/owner/expiry drift blocks | 11 invalidation cases; real implementation identity drift; preserve/read/delete text |
| M7A-A11 | No AI authority/provider/model/commands | inert package + response tests; SQL ai_jobs/memories empty; mock executions0 |
| M7A-A12 | Other sections independent of practice errors | API broken-admission/storage tests, journal independent deletion, full M1–M6 regression |
| M7A-A13 | No downstream journal/memory/health/task/feedback writes | domain/API SQL counts; demo seed count unchanged; browser journal remains empty |
| M7A-A14 | Whole-vault session backup/restore; activation not restored | four-state backup matrix + revoked backup; invalid UTC backup denied |
| M7A-A15 | No RAW/private material/runtime DB in Git | public/staged paths + existing privacy/all-local-object/generated scan and manual content review |
| M7A-A16 | Standalone constrained maps key-closed | node scripts/verify_m7a_schemas.mjs — independent Ajv2020, seven positive/negative checks |
| M7A-A17 | Relevant M1–M6 + prep regressions, built React green | full Python/Chromium suite, npm build/test, prep validator; native unchanged diff |
| M7A-A18 | Real owner-runnable local demo UX | scripts/m7a_demo.sh fresh-root proof; built browser5; 24 captures + finish review |

Action retries return current safe state rather than replaying earlier mutations; deleting content
redacts fingerprints and keeps minimal tombstone/operation metadata to prohibit resurrection.
Admission-invalid action commits a BLOCKED receipt, so response loss cannot duplicate that transition.
UTC/end-state/provenance invariants validated for persisted sessions and backups.
Runtime technical identity pins engine/contracts/validator + storage/models/API + practice UI/CSS source
bytes, not the evidence-only Git report SHA. R docs never silently change a running package/receipt.
The production receipt schema establishes future exact boundaries; current prep schema0.1 is OFF-only,
so supporting future ACTIVE production admissions needs a separate explicitly authorized evolution.
No inactive candidate or synthetic receipt can supply that evolution itself.

## Local demo and limits

```sh
./scripts/m7a_demo.sh /private/tmp/personal-companion-m7a-synthetic-demo
```

Existing installed dependencies required; command rebuilds UI locally, uses explicit demo flag,
prints loopback URL and disposable one-time code. No downloads/providers/phone/real user root.
Normal `serve` without --synthetic-practices never exposes a runnable fixture. All practice data is
synthetic in this milestone. Source-content/rights/qualified-clinical review remains absent, all27 OPEN.
M7A concludes AWAITING_REVIEW only after full exact-C checks, evidence-only R and verified main push.
M6-N01 final0.6.1 hardware NOT_RUN remains OPEN; M7B/M8 not started.
