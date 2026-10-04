# M8A — AWAITING_REVIEW

Base `0eaac55783a8cc9aa400db238f78bafdf91623e7`. Final C `38d3ed69839a8fc876c50b900552ad38d965c5cd` on main.
Evidence-only R follows; its SHA and final origin/main equality are recorded in delivery verification after creation,
not recursively embedded here. Standing normal FF development push is authorized. No release/tag/deploy/pilot.

External M7D **ACCEPT** durable in [M7D_ARCHITECT_REVIEW.md](M7D_ARCHITECT_REVIEW.md), exact
C56b03bd / R0eaac557, scoped live-synthetic engineering + bounded provider quality + synthetic local-ASR guard.
[Preserved objects](evidence/M8A/PRESERVED_M7D_EVIDENCE.json) prove prior reports/evidence unchanged. Ledger48/48;
M8A live application provider calls **0**; no borrowing M7C budget, auth/PAYG/account/system installation.
Active Codex session model/effort `gpt-6.1-sol/high` verified from whitelisted turn metadata; installed0.159.0
catalog supports high (catalog ≠ entitlement). [Sanitized environment](evidence/M8A/MODEL_ENVIRONMENT.json).

## Result and identity

Prerequisite-based unsigned source directory package **M8A-38d3ed69839a8fc876c50b900552ad38d965c5cd**,
schema11, web compatibility contract2. Manifest hash:
`326ef01c1338eac05c3417714edf599255d944382118b30d0eadde3d39d142e4`.
[Full manifest/files/hashes](evidence/M8A/RELEASE_MANIFEST.json). Actual ignored artifact:
`generated/releases/M8A-38d3ed69839a8fc876c50b900552ad38d965c5cd/`.
Clean exact Git commit, Python requirements input, web lock, every built asset and source/contract/default file
are bound. No floating latest, Git metadata, venv/node_modules, private roots/backups/audio/weights/auth bundled.
Hash provides integrity against independently trusted expected hash, not signature/notarization or hostile-OS security.

Supported assumptions: existing Darwin arm64/Python3.13 with every exact requirements.lock version. Build additionally
uses existing Node/npm/node_modules; startup requires neither Node/npm nor repository Git. No install/download fallback.
Final environment: Darwin arm64/Python3.13.2/Node26.8.2. This is not a standalone binary or clean physical Mac test.

[INSTALL](../docs/INSTALL.md), [UPGRADE](../docs/UPGRADE.md), [RECOVERY](../docs/RECOVERY.md),
[UNINSTALL](../docs/UNINSTALL.md), [ADR-011](../docs/adr/ADR-011-M8A-LOCAL-RELEASE.md) are operator authority.
Prepare: `.venv/bin/python -m apps.core.release prepare --output "generated/releases/M8A-$(git rev-parse HEAD)"`.
Start: `.venv/bin/python -m apps.core.release start --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT"`.
Foreground loopback only, stop Ctrl+C; OS data lock held until exit, immediate port rebind verified; no orphan daemon.

## Lifecycle and fail-safe behavior

[LIFECYCLE.json](evidence/M8A/LIFECYCLE.json): actual package copied into fresh synthetic app/data roots with
spaces/Unicode, installed Python executing installed package source (no checkout imports/Git metadata at runtime).
First start/schema/UI/journal/creative/conversation OFF, stop/restart persistence, interrupted foreground inference
FAILED/PROCESS_INTERRUPTED with no auto-resume/duplicate mutation. Queued original synthetic ASR FAILED/
ASR_RESTART_RETRY_REQUIRED; LOCAL unavailable rejects before execution. Package has no ASR assets; checkout
existing native ASR is a separate earlier gate. No cloud fallback/private/human voice used.

App root and data root cannot overlap. Uninstall removes only marked managed runtime, **KEEP DATA** and backups;
explicit synthetic data deletion is another named command requiring exact absolute-root confirmation. No secure-erasure
claim; exports/OS/browser/backups/copies may survive. No generic uninstall deletion flag.

Upgrade verifies current identity, package/hash/schema/platform/dependencies/paths before migration; stages assets,
creates accepted consistent sanitized backup, verifies snapshot, writes durable pending marker, transactionally migrates,
then switches active pointer. Future/corrupt schema/metadata, wrong hashes, missing assets, invalid targets, busy locks,
failed migration and interrupted backup fail safely. Failed migration retains old pointer/DB/backup/pending marker;
start refuses until explicit recovery. Source data is never implicitly migrated merely by start/preflight.

Actual release lifecycle verifies schema11 backup→upgrade→fresh rollback/restore→same journal/creative/conversation state.
36 deterministic M8A tests separately verify genuine minimal schema2→11, schema10 historical projection→11,
transaction failure/backup restoration, two distinct **synthetic manifest** app-replacement fixtures, tombstone/revision
history and M3 memory/rejected M7 map exact provenance. These projections/manifests are installation simulations,
not historical app-binary/physical-hardware evidence. Current packages are schema11; backup schemas2–11 migrate to11.
Rollback = compatible application + pre-upgrade backup restored into **new** roots; no in-place schema downgrade.
Existing/unrelated roots cannot be overwritten; pairing/consent/runtime/practice/health gates reset safely on restore.
Backup is not encrypted at-rest; private storage/encryption/retention requires the separate real-pilot decision.

Packaged frontend supplies exact commit header on all same-origin API requests. Backend rejects mismatch/missing
header409 before auth/domain operations; no stale frontend mutation. Recoverable update UI preserves mounted draft
for copying; reload explicitly warns about unsaved text. Waiting SW activation remains explicit, encrypted phone-store
schema2 unchanged. Chromium desktop1440x1000/mobile390x844 + mismatch state PASS; zero external requests/page errors.
Phone transport/real Android persistence remain separate; packaged phone transport is OFF.

## Exact-C verification

[Command outcomes](evidence/M8A/EXACT_C_CHECKS.json): **648 Python PASS**, including **43 real Chromium tests**;
**50 web tests PASS**, TypeScript/Vite build PASS; M7A7/M7C12/M7D14 independent Ajv checks, canonical admission,
five skill qualification dependencies, documentation/snapshot/privacy PASS. Package lifecycle command exit0.
One existing Starlette/anyio deprecation warning; no test failure. [Visual review](evidence/M8A/VISUAL_REVIEW.json)
and original synthetic PNGs preserve paper/ink/sage design. No actual clean Mac/Galaxy/human claim.
[Acceptance matrix](evidence/M8A/ACCEPTANCE_MATRIX.json): A01–A18 engineering checks satisfied; independent review pending.

[Initial candidate failure](evidence/M8A/INTERIM_FAILURE.json) at bc4bc31 is retained: legacy /messages added a
synthetic mock response although controller reported OFF. Fixed forward at final C by separating synthetic data
labeling from mock-response permission and rejecting forbidden release factory inputs. Final actual package rerun PASS;
no prior failure relabeled. No unsafe external response/provider call occurred.

[Exact-C privacy scan](evidence/M8A/EXACT_C_PRIVACY.json) checks worktree/generated UI/snapshots and all local Git objects,
including unreachable/staged; full tracked-path payload policy extended. Full final evidence-tree privacy review also
runs before R/push. Heuristic scan is not proof of private-provider suitability, encryption or material-rights perfection.
New committed material: original code/docs, reviewed synthetic metadata/screenshots only. Archives/DB/audio/weights/roots ignored.
CI **NOT_CONFIGURED/NOT_RUN** (`gh run list=[]`, no tracked workflows); no fabricated CI success.

Local synthetic timings (ms): preflight19.122, fresh init103.785, startup readiness632.925, backup46.435,
upgrade76.597, rollback restore55.382, fresh restore89.226. No target-device performance guarantee.

## Notes and separate gates

- **M7D-N01 CLOSED_ENGINEERING**: actual controller fixture compares multiple practical options without choosing
  for user; exact source quotes, explicitly labeled quoted options/examples and historical blockquotes do not count
  as extra follow-up. Unlabeled unknown questions/multiple actual questions still fail closed. Deterministic bounded
  convention, not a perfect semantic parser; no new live inference or LLM judge.
- **M7D-N02 OPEN / nonblocking, POLICY_IMPLEMENTED**: incumbent formal «ви» selected as stable FORMAL_VY payload/
  hash/instructions; two-turn drift in informal pronouns fails before assistant commit; restart retains policy.
  User/source quotes are preserved, preference never inferred. Verb-only register drift/naturalness is not generally
  classified or human-verified; no claim that all Ukrainian register problems are solved. No owner-choice blocker.
- M7C-N02 **OPEN HARD PRIVATE-DATA GATE**, provider retention/private-personal suitability NOT_VERIFIED.
- M7C-N03 human Ukrainian ASR **OPEN/NOT_RUN**; M6-N01 final Health0.6.1 **OPEN/hardware NOT_RUN**.
- All27 research findings OPEN, clinical_active0; cbt_reflection/worry_rumination/sleep_review/nightmare_review/
  grounding CANDIDATE/OFF. ProviderOFF, health-to-AIOFF, private providerOFF, external embeddingsOFF,
  cloudASRNONE, automatic publication/cloud-sync/telemetry/fallbackNONE throughout lifecycle.
- FREE Luna/max and DEEP Sol/ultra remain provisional recommendations, never activated.
- Real private journal/health/audio/conversation data used: **NONE**. No system installation/trust/network/hardware changes.

Exact [M8B checklist](../docs/RECOVERY.md) covers real Mac install/runtime, private root/owner consent/migration,
phone pairing, private network/cert/Tailscale, Health/Watch/human UA ASR, provider suitability/activation and exact
cloud context consent. It is a readiness document, not permission request or execution. M8B **NOT_STARTED**.
Stop after evidence R + authorized main FF push and exact origin/main equality. M8A **AWAITING_REVIEW**.
