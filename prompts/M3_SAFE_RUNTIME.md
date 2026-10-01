# M3 — Safe AI runtime foundation, memory & organization

Owner execution goal 2026-10-01; base e437de0f41872cbb0c9b0e5b6b940dd781de0735.
Complete coherent synthetic implementation, tests/fixes/docs and normal fast-forward main push.
M2 external synthetic ACCEPT recorded in reports/M2_ARCHITECT_REVIEW.md. M3 ends AWAITING_REVIEW.

## Required scope
- Provider-independent narrow metadata/execute/cancel interface; deterministic mock; Codex candidate
  disabled with immutable live gate. AI starts OFF. No runtime tools/shell/files/git/SQL/browser/HTTP.
- capture_classify (type/tags), organize_selected (summary with IDs/revisions), memory_propose
  (MODEL_SUGGESTED until user confirms). Neutral organization only; no clinical inference/protocols.
- Exact explicit context preview: purpose, provider/model/destination/retention, fields/text, selected
  IDs/revisions, creative flag, rough size (never exact tokens), approval expiry/scope/hash. Recheck
  source/memory revisions and consent at dispatch/result/accept. Missing/revoked/expired/stale blocks.
- Deterministic minimized inspectable/hashable package; selected confirmed relevant memories only;
  no whole journal/research/health/chat dump, no silent truncation, fail budget overflow.
- Persistent jobs: queue/run/done/fail/cancel/disabled/wait-provider; one foreground job; timeout,
  bounded transient-only retry, restart recovery, idempotent effects, no fallback, no late apply.
  Persist minimum audit metadata; generic logs never contain raw prompts/responses/credentials.
- Untrusted output: strict per-task schemas and size/source/action/domain checks before transaction.
  No command dispatch. Malformed/adversarial output never mutates journal/memory.
- User-visible memory: opaque ID/scope/content/provenance/source refs/status/revisions/timestamps/
  optional expiry; confirm/edit/reject/delete; dependency invalidation; no fiction-derived facts.
- Reversible proposals separate from raw text and user accepted structure; explicit accept/edit/reject/
  ignore; creator model/version visible; rejected same-context proposal not endlessly resurfaced.
- Adversarial fixtures: ignore rules/read ~/.ssh/run shell/send data; deterministic denial.
- Future subprocess boundary: exact argv/no shell/sanitized env/controlled cwd/no credentials;
  fake-only tests for timeout/cancel/malformed/nonzero/path/tool abuse. Real adapter OFF if OS
  isolation unproven. No inference to inspect metadata.
- Existing Ukrainian neutral React UI: OFF/mock status, selection/preview/approval, jobs/cancel,
  proposals, What system remembers CRUD. Synthetic marked. No therapist/health/voice UI.
- M1/M2 capture/search/offline/sync independent of AI/availability/quota. No automatic AI on sync;
  phone no cloud action or background guarantee. Galaxy/private route still unverified.
- Close M2-N01 with pending/finalized or equivalent: local encrypted persistence failure after server
  pairing response leaves no usable orphan; explicit retry/recovery/revoke; one-use/replay/epoch intact.

## Acceptance and verification
Contract docs/M3_CONTRACT.md must map M3-A01..A14: OFF, exact consent, validated output, lifecycle,
no fallback, minimization, provenance, reversible structure, injection, process boundary, cross-device,
cancel/stale, privacy/logging, live gate. A14 NOT_RUN/PROVIDER_DISABLED; mocks do not prove live.
Keep all M1/M2 tests. Add domain/API/job/memory/consent/fake subprocess/injection/browser/phone tests,
actual SQLite and built React. Full target frontend build, Python/web/browser suites, docs/regenerated
context/privacy incl Git objects/generated artifacts/diff check. Record commands/versions/exits/SHAs.
Measure local synthetic overhead/context/jobs/memory/validation/DB/idle; no real latency/cost/hardware.
Durable STATE/HANDOFF/roadmap/append-only devlog/report/snapshot; ADR for runtime decisions; C/R
workflow, evidence-only R, publication exact diff/privacy scan, normal fast-forward main. CI NOT_RUN
allowed. Last reviewed C stays M2. No self-ACCEPT, no M4+.

## Hard stops
live_provider_calls=false. Synthetic only; no real vault/data migration, provider inference/quota,
MiniMax/PAYG/fallback/accounts/auth/billing/credentials, private backend routes, LAN/Tailscale/certs/
Keychain/deploy/release/tag/Vercel/health/microphone/ASR. Do not read R01_RAW.docx/R02_RAW.docx/
R03_RAW.docx or activate R04+ therapy/diagnosis/medication/CBT-I/IRT/mental scoring/hormone inference.
Public repo receives code/synthetic fixtures/sanitized evidence only. No force push/history rewrite.
Owner message ends at documentation bullet “provider/runtime ADR if”; remaining docs follow AGENTS.
