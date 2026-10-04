# M8C — AWAITING_REVIEW

**Mac-only core engineering gates READY on the tested reference Mac. Actual private pilot NOT_STARTED.**
Production PRIVATE_LOCAL path verified with **ORIGINAL SYNTHETIC CONTENT only**; no real private vault created.
Independent architect ACCEPT and explicit owner/data-owner activation remain required. No additional core engineering
milestone is required after ACCEPT when activation preflight passes; optional modules remain separate.

Base `1533a69c40c1eaa0a8f67a867724a8835101e0af`. Final implementation C `a00a14277974b7f6c25846d0eb7a23879f86183a`. Evidence-only report commit R follows C; its actual SHA/push/origin
equality belongs to final delivery verification after creation, avoiding a recursive self-hash. Branch main;
normal FF development push authorized independently of merge/release/deploy/providers/real-data permissions.
M8B external **ACCEPT** durable: [review](M8B_ARCHITECT_REVIEW.md), exact C434b1cd5/R1533a69c.
M8A-N01/N02 CLOSED_ENGINEERING. Historical M8A/M8B/M7D evidence and M8B report unchanged55 files:
[preservation](evidence/M8C/PRESERVED_HISTORY.json). No published history rewrite.

## Independent readiness

| Result | Status |
|---|---|
| MAC_CORE_PILOT | READY — engineering only, requires independent ACCEPT + owner/data-owner activation |
| PRIVATE_STORAGE_SECURITY | READY — tested target volume protection/permissions verified |
| PRIVATE_BACKUP | READY — tested explicit protected local container + private lifecycle |
| ACTIVATION_PROCEDURE | READY — exact post-review procedure available |
| PHONE_PILOT | NEEDS_TRANSPORT_GATE / PHONE_PRIVATE_TRANSPORT_REQUIRED |
| PRIVATE_AI | BLOCKED_M7C_N02 / OPEN HARD PRIVATE-PROVIDER GATE |
| HUMAN_UA_ASR | NOT_RUN_M7C_N03 / OPEN |
| HEALTH_WATCH | NOT_RUN_M6_N01 / final bridge0.6.1 hardware OPEN |
| CLINICAL_SELF_HELP | OFF_27_FINDINGS_OPEN / clinical_active0 / all5 candidatesOFF |
| M7D-N02 | OPEN_HUMAN_LANGUAGE_REVIEW — not core blocker with conversationOFF |
| ACTUAL_PRIVATE_PILOT / actual private root | NOT_STARTED / NOT_CREATED |

[Machine decision](evidence/M8C/PILOT_READINESS.json). Native facts apply to this tested Mac/volumes, not all Macs,
clean physical installations, Galaxy/Watch/human ASR/private-provider suitability or clinical acceptance.

## Exact release

Release **M8C-a00a14277974b7f6c25846d0eb7a23879f86183a**, manifest format3 / data schema11 / web contract2.
Manifest hash `4fcd18f31bd647f5bbd96ad30eb92cb47d59a1ff7cf4ef0be60c5010259fcc65`.
Runtime lock hash `f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`.
[Full manifest](evidence/M8C/RELEASE_MANIFEST.json); ignored local package retained in generated/releases/ under this
exact release ID. Package is unsigned source/assets with trusted checksums, not signing/notarization/digital signatures.
No public Release/tag/deploy. Exact-C prepare used existing Node/npm; startup needs only existing Python3.13 and12
pinned runtime libraries. Disposable pip-free copied-runtime verification has pytest/Playwright/httpx/pip absent.
No install/download/global dependency changes. [Model support](evidence/M8C/MODEL_ENVIRONMENT.json): installed
Codex0.159.0 catalog/config gpt-6.1-sol/high supported; no model/billing/auth changes or application inference entitlement claim.

## Root, consent, storage and network model

RootKind.SYNTHETIC_TEST retains the valid historical M1 marker; PRIVATE_LOCAL has its own strict typed receipt,
SQLite private_root_identity binding and installation kind/id binding. A loose flag/marker edit cannot convert modes.
Exact raw numeric/bool types and duplicate-key parsing refuse malformed metadata, including bool/int/float aliases.
Runtime rechecks the marker/binding/permissions. Private validation and SQLite connection lifetime share the existing
per-root RLock to avoid WAL/SHM lifetime races during parallel journal/search requests.
No arbitrary existing-root inference, Git/symlink/traversal/cloud folders, discovery/import or real vault migration.
Application/data/backup paths separate. Init requires exact release/private profile/new-empty data/new application,
protected backup container, exact INITIALIZE_PRIVATE_LOCAL root confirmation, literal data-owner acknowledgement
and no-cloud-directory acknowledgement. Receipt local-only/pseudonymous; no real owner receipt/path/identity in Git.
Normal start never initializes. [ADR-013](../docs/adr/ADR-013-M8C-PRIVATE-LOCAL-CORE.md), [contract](../docs/M8C_CONTRACT.md).

[Actual native preflight](evidence/M8C/MAC_PREFLIGHT.json): Darwin/arm64/Python3.13.2; native diskutil target-device
mapping includes APFS Data firmlinks and requires FileVault=True, Encryption=True, EncryptionThisVolumeProper=True.
Global FileVault/hardware encryption alone does not grant READY. Unverified/error/missing protection fails closed.
Verified owner UID, directory0700/file0600/no extended ACL, safe separated paths, writable space, runtime/OFF/loopback.
No usernames/serial/Apple account/volume identifiers/private filenames/recovery information recorded.
[Schema](evidence/M8C/SECURITY_PREFLIGHT_SCHEMA.json), [independent Ajv](evidence/M8C/SECURITY_SCHEMA_CHECKS.json).

**Application-level database encryption NOT_IMPLEMENTED. Application-level backup encryption NOT_IMPLEMENTED.**
At-rest protection is verified FileVault-protected APFS storage + strict owner-only access. Compromised/unlocked OS,
admin/same-user malware, browser/OS copies remain outside this model. This app cannot control third-party sync/OS
backups; owner explicitly chooses non-cloud folders. Tested local backups are on the same protected Mac volume:
logical recovery proof, not protection against physical device loss/failure.

Bind127.0.0.1 only; process-local deny-egress/DNS/external socket guard, local assets/fonts, Host/Origin/CSRF/build
header/session/CSP preserved. Provider credentials/environment cannot activate anything. API allowlist/factory/runtime
reject AI, conversation inference, clinical/specialist, Health, voice/ASR, phone, embeddings/publication/sharing/cloud
operations; optional controls hidden and journal is landing surface. Journal/creative/search/manual maintenance ON;
explicit previewed local exports preserve safeguards. No cloud backup/sync/telemetry/fallback/update download.

Unlock mandatory, one-time5min code only foreground terminal; server session memory-only, private HttpOnly/SameSite
session cookie without Max-Age/Expires. Lock/restart deny old session; idle900s/absolute28800s enforced. Native final
package Chromium controlled-clock test verifies UI+API idle-lock (not a real15min wait). No private API content before
auth, no tokens in DB/evidence. [Stable UI/security negatives](evidence/M8C/VISUAL_REVIEW.json) includes actual final
package Host/Origin/CSRF/build refusal, synthetic-only screenshots1440x1000/390x844 (desktop emulation, not Galaxy).

## Backup, restore, upgrade and removal

Private backup format4 binds exact producing full release/source release/schema/time, snapshot-only release
attestation/checksum, private root identity/kind and protection policy. Existing synthetic formats1/2/3 preserved;
legacy compatibility cannot turn private identity into synthetic. Rehashed wrong-kind/type/provenance/duplicate/cross-
mode corruption rejected before target roots, including relabelled legacy with --allow-legacy-backup.
Backups manual to explicit new child of consented owner-only protected local container; source/target protection
rechecked. **Archive is not independently encrypted**; copying it to unencrypted storage removes protection and is
refused there. No cloud/network upload, auto retention deletion or secure-erasure claim. Independently retain trusted
producer/backup manifest hashes; fully rewritten unsigned artifacts are not authenticated without trusted hashes.

Fresh private restore renews explicit acknowledgement/security/root identity and preserves PRIVATE_PERSONAL /
USER_REPORTED domain provenance/history/tombstones. No private↔synthetic conversion/in-place downgrade; pairing/jobs/
consents/Health/practices remain invalidated/OFF. Old M8A/B synthetic packages cannot open private vaults.

[Final package actual Mac lifecycle](evidence/M8C/MAC_LIFECYCLE.json) PASS: init/start/unlock/journal create-edit-search/
creative/UI/durability/restart/lock, backup/private restore/restart, upgrade/restart, transactional failure with backup/
original pointer/pending marker and actual startup refusal, fresh-root rollback/restart, KEEP DATA uninstall/separate
exact-root disposable private delete/backups preserved, all temporary roots/runtime copies cleaned.
Failure test is explicitly a disposable schema10 projection, not an old-schema binary or OS failure claim.

**Genuine cross-release PASS:** intermediate local M8C3eade011 package → final C package → trusted preupgrade backup
into fresh private root → old application's actual restart. Old manifest3d03cc975960d42f6cd643c2740e85ff20b65a1e1662e9cd9c3c1852d65cf4e8;
new producer is final manifest above and backup source is independently old manifest. Previous package was an
unreviewed intermediate M8C build for engineering proof, not an accepted/public release. Copies staged outside Git
with identical hashes; security path gate unchanged. Post-review operators must use trusted accepted compatible releases.
Canonical activation/start/first real entry: [PILOT_HANDOFF](../docs/PILOT_HANDOFF.md); [INSTALL](../docs/INSTALL.md),
[UPGRADE](../docs/UPGRADE.md), [RECOVERY](../docs/RECOVERY.md), [UNINSTALL](../docs/UNINSTALL.md). Not executed on a real vault.

## Exact-C checks and acceptance matrix

[Check record](evidence/M8C/EXACT_C_CHECKS.json): **751 Python PASS**, including45 actual Chromium/84 M8C;
**50 web PASS**, TypeScript/Vite exact-C build, Ajv M7A7/M7C12/M7D14 + private schema5, canonical admission/all5
qualification packages/docs/snapshot/diff/privacy PASS. Commands/exit codes/environment recorded; one existing
Starlette/anyio deprecation warning. Earlier legacy M4 200ms process fixture timeout rechecked separately PASS;
final full751 PASS, ASR production code unchanged and private ASR OFF. CI NOT_CONFIGURED/NOT_RUN; gh runs[];
no workflow added for green status. Native driver and additional final-package render exit0.

| Criteria | Evidence / result |
|---|---|
| A01 | external M8B review exact C/R durable PASS |
| A02–A03 | typed dual binding, wrong/corrupt kinds, explicit init/consent/security negatives PASS |
| A04–A06 | network/auth/profile/env/factory/optional capability denial PASS |
| A07–A09 | actual native protection/permissions, protected target + release/snapshot/policy provenance PASS |
| A10–A12 | fresh private restore/history/tombstones/cross-mode refusal/upgrade/failure/genuine rollback PASS |
| A13–A14 | KEEP DATA, exact private delete, wrong/unknown roots/backups preserved PASS |
| A15–A17 | truthful private UI + actual production path ORIGINAL SYNTHETIC only; forbidden activity0 PASS |
| A18–A20 | exact post-ACCEPT procedure/core READY/actual pilot NOT_STARTED PASS |

[Exact-C privacy](evidence/M8C/EXACT_C_PRIVACY.json) and final prepublication scan cover worktree/generated UI/context/
all local Git objects/staged public tree. Public material only original code/docs, hashes/status/counts and synthetic
screenshots; no DB/backup/audio/Health/real receipt/unlock/credentials/generated runtime archives. Heuristics are not
proof of private provider suitability/clinical approval/secure erasure; manual diff/material-rights review completed.

Real private data used0; application live provider calls0; system-wide/security/trust/network changes0. Only authorized
local disposable filesystem/runtime operations. M8C **AWAITING_REVIEW**; normal C→evidence-only R→FF main publication,
verify origin/main==R, STOP. No automatic next milestone or actual private pilot.
