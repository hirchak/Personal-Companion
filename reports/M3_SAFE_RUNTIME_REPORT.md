# M3 — Safe AI runtime foundation, memory & organization

Status: **AWAITING_REVIEW**, synthetic engineering candidate. External M2 ACCEPT source is owner M3 goal;
reviewed M2 C `67cb03969d344fe37f45f1d97d021405bea6b126`, reviewed R/base/main
`e437de0f41872cbb0c9b0e5b6b940dd781de0735`. Actual initial local/remote main matched; clean worktree.
Implementation C: pending creation; evidence-only R will record exact C. Report commit: next evidence-only R,
resolved by final user receipt (no recursive self-hash). Push checkpoint: PRE_PUSH; CI: NOT_RUN.
Owner permits normal fast-forward main push; permissions.push_main=true separately from merge_main=false.

## Delivered behavior

Provider-independent data-only runtime and deterministic mock; default OFF on startup/restart. Codex is
an unconditionally disabled candidate, no model invocation, CLI auth/secret access, quota or billing change.
Three working neutral tasks: capture_classify, organize_selected and memory_propose. They produce bounded
allowlisted proposals, not narrative diagnosis/therapy or arbitrary commands. All provider output is data.

Exact inspectable canonical context includes selected ID/revision/raw text/type/tags, explicitly selected
confirmed preferences, mandatory constraints, schema/model/destination/retention and 5-minute single-job
consent reference/hash. No journal/memory/creative dump, ratings/health/research/history. Consent and source
revisions checked before approve/enqueue/dispatch/retry/result/accept; SQLite triggers cancel stale work.
User sees bytes/characters approximate size, never fake tokens. Budget overflow asks for narrower selection.

Persistent single foreground jobs: QUEUED/RUNNING/DONE/FAILED/CANCELLED/WAITING_PROVIDER/PROVIDER_DISABLED;
2-second total timeout, max3 transient-only attempts; no fallback. Restart fails interrupted work and
requires fresh approval. Jobs persist metadata/code/unknown usage only, never raw prompts/responses.
Trusted fake subprocess tests pin fixture hash, exact argv/no shell, sanitized env/temp cwd, capped output,
process-group kill/cancel/timeout/nonzero/path/tool-output rejection. Real OS isolation remains UNVERIFIED.

User-visible memory separates MODEL_SUGGESTED status/provenance from explicit confirmation. Confirmation
retains model-origin provenance, source refs and job/adapter identity. Edit becomes USER_EDITED with explicit
owner restatement, historical origin via immutable job/suggestion; reject/delete invalidates dependencies.
Source edits mark unedited model memory REVIEW_REQUIRED. Creative memory proposals denied deterministically.
Classification accept/edit/reject/ignore/undo never alters raw text; accepted structure uses domain revision
transactions. Reviewed same-source/model/version rejected proposals do not reappear. Organization retains refs.

Existing Ukrainian UI gains inline synthetic assistant/context/jobs/suggestions/memory; no console/therapist
or fake health features. OFF save/edit/search/sync still work. Phone device credentials cannot reach AI owner
APIs; offline and Mac-confirmed capture do not automatically invoke AI. Browser/IndexedDB tests remain real.

M2-N01 fixed forward: server commits PENDING credential; phone commits encrypted IndexedDB before idempotent
finalize. Local write failure leaves unusable, visible/revocable pending state, fresh-owner-invite retry.
Lost confirmation response retries from encrypted state on foreground sync. Replay/expiry/revocation/epoch
remain enforced. Tests simulate server commit→actual browser write failure→fresh retry, plus native crypto
lost-response/restart and server revocation/expiry. No secrets printed or committed.

SQLite schema3 transactional synthetic migration/preupgrade copy, schema2 backup restoration then migration;
journal/phone sync wire stays2. All M1/M2 tests retained; migration compatibility assertions updated to schema3.
Contracts/API generated from actual FastAPI. [ADR-003](../docs/adr/ADR-003-M3-RUNTIME.md) records decisions/limits.

## Verification

Full PRE_C target ` .venv/bin/python scripts/verify_m3.py --scope PRE_C --output reports/evidence/M3/PRE_C_CHECKS.json`
(exit0). Commands below all exit0, working directory `<source-root>`, Python project `.venv`:

| Command | Result |
|---|---|
| npm --prefix apps/web run build | TypeScript and built React/PWA PASS |
| npm --prefix apps/web test | 13 tests PASS (M2 kept + pairing regressions) |
| .venv/bin/python -m pytest -q | 198 tests PASS including 10 real-browser scenarios |
| .venv/bin/python scripts/check_docs.py | PASS |
| .venv/bin/python scripts/build_chatgpt_context.py | PASS, ignored snapshots regenerated |
| .venv/bin/python scripts/check_privacy.py --include-generated | PASS, worktree/all local Git objects incl staged/unreachable/generated context/built UI |
| git diff --check | PASS |

Environment: Python3.13.2, Node v26.8.2, npm11.19.1, Darwin27.0.0 arm64. One existing Starlette/AnyIO
DeprecationWarning; no failing/skipped acceptance test. Collector records timestamps/exits/versions/durations.
M3-A01…A13 assertions synthetic PASS at contract scope. **M3-A14 NOT_RUN / PROVIDER_DISABLED**, not mock PASS.
Actual Galaxy/Tailscale/private rollout A12 HARDWARE_UNVERIFIED / NOT_RUN. CI NOT_RUN.
Exact C full target and final R evidence/checks will be appended before authorized publication.

UI bounded inspection: desktop1440 and mobile390, real keyboard/consent/jobs/cancel/suggestions/memory/phone
flows, no unexpected browser errors or external requests. Independent Impeccable UI review requested two fixes:
truthful external-AI-OFF footer and wrapping/44px checkbox labels. Recaptures including350-char memory + pending
classification passed resolution review (ship for these two fixes only, not architect ACCEPT). No design-world
or token change; incumbent design preserved. Read-only documenter verified actual tokens/components
and all three captures. Historical PRODUCT.md M0 baseline / DESIGN.md M1–M2 scope remain intact;
current M3 behavior is documented in current contract/ADR/runtime/memory/provider/sync docs. Detector findings []. Screenshots are explicitly synthetic.

Privacy evidence: `reports/evidence/M3/ARTIFACT_REVIEW.json`, synthetic UI hashes/screenshots and heuristic
Git/generated/build scan. No real vault, R01_RAW/R02_RAW/R03_RAW.docx, auth credentials or paid provider accessed.
Allowed materials are original code/docs/synthetic fixtures/captured synthetic app UI. No research/media ingestion.
Heuristic scan and visual inspection are bounded evidence, not proof of secure erasure/all personal-data absence.

## Local synthetic overhead

`PYTHONPATH=. .venv/bin/python scripts/measure_m3.py` exit0, 30 actual-SQLite iterations; evidence
`reports/evidence/M3/PERFORMANCE.json`. Median context1.518ms, enqueue1.565ms, mock execute+validate+commit4.432ms,
memory list/search1.065ms, structured validation0.026ms. Empty schema3 DB139264 bytes; after30 jobs229376 bytes
(growth90112); logical context/refs/suggestion/memory48818 bytes. Own process idle CPU0.005% in0.25s sample,
0 idle workers. These are short local synthetic observations, not SLO or provider/Galaxy performance claims.
No real token/latency/cost numbers; usage unknown.

## Remaining boundaries and next step

No M4+, actual provider inference/account/auth/billing/PAYG, OS provider sandbox, private data/vault migration,
Tailscale/HTTPS/certs/Keychain/autostart/LAN/deploy/release/tag/Vercel, clinical/research protocol/watch/voice.
Mac context/suggestion data live in private synthetic SQLite; backup retains context but strips device
credentials/revokes approvals. No browser storage as Android hardware-security claim. Deterministic mock only;
real provider activation requires separate scoped gate. M3 is not accepted by Codex; next is external architect
review of exact pushed C/R. No next milestone authorized.
