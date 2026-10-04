# M8B — AWAITING_REVIEW

Base `08d8efdd01dbcf8ddcdbdd6fcd6bd8361b75062a`. Final C `434b1cd5ad857776bbfd9b3799a0abddec2858f6` on main.
Evidence-only R follows; its actual SHA/push/origin equality belongs to delivery verification after creation,
not a recursive self-hash. Standing normal FF development push is authorized; no release/tag/deploy/pilot.
M8A external **ACCEPT** durable in [M8A_ARCHITECT_REVIEW.md](M8A_ARCHITECT_REVIEW.md), exact C38d3ed6/R08d8efdd,
synthetic release/personal-pilot readiness engineering only. [Frozen history](evidence/M8B/PRESERVED_HISTORY.json)
proves prior M8A/M7D reports/evidence unchanged; M7D ledger remains48/48. No new application provider attempts.

## Outcome and independent readiness

**Actual reference Mac synthetic engineering dry run PASS/READY. Actual private MAC_CORE_PILOT NOT_READY.**
Core blocker: **PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED**. The current Store/launcher deliberately accept only
synthetic roots; an authorized private local profile/data labeling/storage/consent flow is not implemented or
activated. Do not relabel a real vault as synthetic to start a pilot. This is a core runtime gate, independent of
optional AI/phone/ASR/Health/clinical modules. Separate owner goal + data-owner consent/storage decision required.
M8B completes the requested bounded engineering dry run/handoff, not that next private-mode implementation.

[Machine readiness](evidence/M8B/PILOT_READINESS.json), [operator handoff](../docs/PILOT_HANDOFF.md):

| Independent result | Exact status |
|---|---|
| MAC_SYNTHETIC_DRY_RUN | READY on tested reference Mac only |
| MAC_CORE_PILOT | NOT_READY / PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED |
| PHONE_PILOT | NEEDS_TRANSPORT_GATE / PHONE_PRIVATE_TRANSPORT_REQUIRED |
| PRIVATE_AI | BLOCKED_M7C_N02 |
| HUMAN_UA_ASR | NOT_RUN_M7C_N03 |
| HEALTH_WATCH | NOT_RUN_M6_N01 |
| CLINICAL_SELF_HELP | OFF_27_FINDINGS_OPEN |
| Actual private pilot/profile/private root | NOT_STARTED / NOT_CREATED |

Future inactive MAC_CORE_PILOT_V1: journal/creative/local search/backup restoreON; private AI/clinical/specialists/
health-to-AI/Health bridge/human voice ASR/embeddingsOFF; cloudASRNONE/telemetry/cloud sync/publicationNONE.
Profile is a defined contract, not activation. No real private root/journal/migration/audio/health/phone data used.

## Exact release and dependencies

**M8B-434b1cd5ad857776bbfd9b3799a0abddec2858f6**, manifest format2, schema11/web contract2.
Manifest hash `8abf581164f1d6984f71f28394994f54ca738d62136ddca41c71da6759cc7cbb`.
Runtime lock hash `f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`.
[Full manifest/file hashes](evidence/M8B/RELEASE_MANIFEST.json). Actual package is ignored at
`generated/releases/M8B-434b1cd5ad857776bbfd9b3799a0abddec2858f6/`; no binary/archive/runtime roots committed.

**M8A-N02 CLOSED_ENGINEERING:** new manifest binds requirements.runtime.lock separately from full development
requirements.lock/web lock. Preflight/start require only12 exact pinned runtime libraries: annotated-types/anyio/
click/fastapi/h11/idna/pydantic/pydantic_core/starlette/typing-inspection/typing_extensions/uvicorn.
No pip/npm/Homebrew/global/system installation or download. Driver creates disposable pip-free venv and copies
only existing pinned runtime distributions. Actual start/install/backup/restore/rollback CLI ran there with
**pytest/Playwright/httpx/pip absent**. Parent test driver/browser use existing development environment separately.
App startup does not need Git/node_modules or repository cwd. Historical M8A format1 explicitly retains old
full-lock prerequisites; legacy rollback used that existing full environment, not falsely labeled runtime-only.

## Backup provenance

**M8A-N01 CLOSED_ENGINEERING:** release-aware backup format3 binds exact producing full manifest/release/Git/hash,
old/current source release reference, snapshot schema/format/creation timestamp. Actual producer manager core
sources must match supplied release manifest. During upgrade the new M8B manager creates the backup while
source release may be old M8A; both identities are distinct and preserved.

Snapshot-only SQLite release_backup_provenance attestation is written before snapshot checksum. Restore validates
exact JSON/attestation equality, producing manifest/independent expected producer hash, schema/time/app_version
and optional independently retained backup manifest hash **before creating target roots**. Negative tests include
altered/rehashed producer/source/schema/time/format/missing attestation and mismatched receipt hash. Snapshot-only
attestation is removed from restored live copy; no live schema/domain change or lost journal/map/memory history.

Generic historical Store backup1/2 compatibility and historical app_version M7D remain explicit/unchanged.
Release restore needs deliberate --allow-legacy-backup and reports LEGACY_UNKNOWN_PRODUCER, never inferred
provenance. Across-release restore/rollback supplies --producer-manifest-hash; strongest unsigned receipt binding
also supplies --backup-manifest-hash. Checksums are not signatures: fully rewritten artifacts with recomputed hashes
are not authenticated without separately retained trusted hash. Backup remains unencrypted at-rest.
[ADR-012](../docs/adr/ADR-012-M8B-BACKUP-RUNTIME-HANDOFF.md), [UPGRADE](../docs/UPGRADE.md).

## Actual Mac evidence and lifecycle

[MAC_PREFLIGHT.json](evidence/M8B/MAC_PREFLIGHT.json): Darwin/macOS **27.0**, arm64, Python **3.13.2**,
hardware model **Mac14,15**, chip **Apple M2**. No username/home/account/serial/private filenames recorded.
Runtime12 PASS; app/data paths writable, loopback port8879 available, available disk classAT_LEAST_10_GIB;
fresh data schema unknown before init, actual startup schema11 verified. ASR OPTIONAL_UNAVAILABLE (not packaged).
Facts apply only to Mac running Codex; not clean Mac/all-Mac/target-device guarantees.

[MAC_LIFECYCLE.json](evidence/M8B/MAC_LIFECYCLE.json): actual installed source package, isolated runtime-only Python,
new outside-Git synthetic app/data roots with Unicode/spaces, foreground127.0.0.1 start/unlock, journal/creative/local
search/conversationOFF actions, actual Chromium journal save, stop/immediate restart and durability/no duplicate mutation.
Provider/privateAIOFF, clinical0/all5specialistsOFF, health permissionsNOT_REQUESTED/health-to-AIOFF, LOCAL ASR unavailable.
Two viewport captures1440x1000/390x844 on Mac; zero nonloopback browser requests/page errors. Narrow screenshot is
Chromium emulation, not Galaxy. Server startup installs existing Python audit egress guard (loopback only).

Backup→new-root restore→safe failed-upgrade simulation→fresh-root rollback/start→successful upgrade→uninstall
KEEP DATA/domain integrity PASS. Failed migration simulation changes only a disposable synthetic schema10 projection,
transaction rolls back/pointer unchanged/verified backup/pending marker retained. It is not OS damage/old binary proof.

**Genuine cross-release path also PASS:** accepted old local package M8A-38d3ed6 with trusted old hash326ef01c…
was installed into another disposable root; new M8B upgrade backup records producer8abf5811… and source326ef01c…;
new minimal-runtime start preserves domain state. New manager restores that backup into old-compatible M8A root,
explicit new producer/backup hash, then old application actually starts in existing historical full-lock environment.
KEEP DATA removal preserves its synthetic journal. This evidence is distinct from synthetic manifest projections.
All disposable roots/runtime copies cleaned; no daemon/autostart/network/trust/system configuration changed.

Local timings ms: existing-runtime copy491.171, preflight565.4, fresh install305.514, readiness789.853,
backup314.418, restore320.868, rollback321.955, upgrade422.983. No guarantees for other devices.

## Phone and separate gates

[Phone readiness](evidence/M8B/PHONE_READINESS.json): no existing accepted private HTTPS/Origin/Host/pairing route
established in repo/runtime contract; tested Tailscale CLI absent, no private account/config/endpoint search.
PHONE_PRIVATE_TRANSPORT_REQUIRED. Minimal separate owner transport goal must choose exact private route and
authorize necessary client/account/config/trust changes + exact Host/Origin/auth/pairing + Galaxy synthetic smoke.
No Tailscale install/config, trust/certificate/remote access/public exposure performed.

PWA candidate code/build/regression confirms encrypted schema2 IndexedDB native PBKDF2/AES-GCM, transactional
outbox, local static shell cache, explicit waiting-update activation/exact backend build header; no automatic
cloud/provider/Health/clinical activation. Real Galaxy/background/persistence/HTTPS remains NOT_RUN.
M7D-N02 **OPEN_HUMAN_LANGUAGE_REVIEW**, FORMAL_VY unchanged; verb-only naturalness/human review not claimed.
M7C-N02 OPEN HARD private-provider gate, M7C-N03 human UA ASR OPEN/NOT_RUN, M6-N01 final Health0.6.1 OPEN/NOT_RUN.
27 findingsOPEN, clinical_active0, cbt_reflection/worry_rumination/sleep_review/nightmare_review/grounding CANDIDATE/OFF.

## Exact-C checks and publication boundary

[EXACT_C_CHECKS.json](evidence/M8B/EXACT_C_CHECKS.json): **667 Python PASS** (43 real Chromium/19 M8B),
**50 web PASS**, TypeScript/Vite build PASS, Ajv M7A7/M7C12/M7D14, canonical admission/five qualification
packages/docs/context/privacy PASS. Actual-Mac driver exit0. One pre-existing Starlette/anyio deprecation warning.
New tests prove runtime/development separation and fail-closed provenance; M8A cross-release fixture now explicitly
supplies independently trusted producer hash per new contract; original frozen M8A evidence is not rewritten.
Active Codex `gpt-6.1-sol/high`, installed0.159.0 catalog high support verified, not application inference entitlement.
[Model evidence](evidence/M8B/MODEL_ENVIRONMENT.json). [Visual review](evidence/M8B/VISUAL_REVIEW.json) synthetic only.

[Exact-C privacy](evidence/M8B/EXACT_C_PRIVACY.json) scans worktree/generated UI/snapshots/all local Git objects;
full final tracked/public tree review before R/push. New public material original code/docs and sanitized synthetic
metadata/screenshots only, no private DB/backup/audio/weights/credentials/release/runtime archives. Heuristics
are not proof of provider suitability/storage encryption/secure erasure. CI NOT_CONFIGURED/NOT_RUN, gh run list[];
no CI added solely for green status. Application live provider calls0, real private data0, system/trust/network changes0.
M8B **AWAITING_REVIEW**. Stop after evidence-only R/normal FF main push/origin equality; actual private pilot **NOT_STARTED**.
