# M8C — PRIVATE LOCAL CORE PILOT RUNTIME

Owner execution specification, 2026-10-04. Plan Mode OFF. Final core engineering gate before Mac-only personal pilot.
Expected base/R1533a69c40c1eaa0a8f67a867724a8835101e0af; M8B C434b1cd5ad857776bbfd9b3799a0abddec2858f6.
Preferred installed gpt-6.1-sol/high; verify support, never invent settings. Actual main/clean worktree verified first.
Read STATE/HANDOFF/project.json/WORKFLOW, M8B goal/contract/report, ADR-012, PILOT_HANDOFF, PRIVACY_SECURITY,
DATA_MEMORY, INSTALL/UPGRADE/RECOVERY/UNINSTALL and relevant storage/security/release ADRs.

## Authority, acceptance and limits

Durably record owner-delivered external M8B ACCEPT with exact C/R and verified synthetic Mac lifecycle,
M8A-N01/N02 CLOSED_ENGINEERING, runtime-only dependency surface, exact release-aware backup provenance,
M8A→M8B→old M8A rollback/start, MAC_SYNTHETIC_DRY_RUN READY. Historical evidence immutable.
M8B MAC_CORE_PILOT was NOT_READY solely PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED; phone needs transport.
Carried: M7D-N02 OPEN_HUMAN_LANGUAGE_REVIEW; M7C-N02 OPEN HARD PRIVATE-PROVIDER GATE;
M7C-N03 OPEN/HUMAN UA ASR NOT_RUN; M6-N01 OPEN/final Health0.6.1 hardware NOT_RUN;
27 findings OPEN, clinical0, all five candidates OFF. No actual private/provider/system/network activation in M8B.

Authorized: repo code/docs, existing dependencies/Chromium, exact package builds, read-only actual Mac security
checks/native encryption status, disposable private-mode roots with ORIGINAL SYNTHETIC CONTENT only,
127.0.0.1 runtime, permissions, local backup/restore/upgrade/rollback tests and sanitized evidence.
Forbidden: real journals/creative/audio/Health or existing vault migration/discovery; actual pilot/root activation;
live providers/PAYG/billing/account/auth changes; system/global pip/npm/Homebrew installs; encryption changes;
Tailscale/network/remote/trust/cert/phone pairing; deploy/public Release/tag/signing/notarization/launchd.
Missing prerequisite requiring forbidden changes => BLOCKED_BY_PERMISSION, never perform change.

## Required production private path

Exact release → private security preflight → unmistakably explicit private-root initialization with data-owner
acknowledgement → private local runtime → journal/creative/local search → backup/restore/upgrade/rollback →
uninstall KEEP DATA → post-review activation handoff. M8C executes exact path only on disposable synthetic content.
Real pilot remains NOT_STARTED, actual private vault NOT_CREATED. After independent ACCEPT plus owner/data-owner
activation, no further core engineering milestone if all core criteria pass; any genuine blocker must be explicit.

Distinct typed durable SYNTHETIC_TEST/PRIVATE_LOCAL root kinds; no synthetic marker reuse/renaming/relabeling.
Wrong mode and corrupt metadata fail closed; arbitrary existing files never inferred private; a loose flag cannot
change root kind. Root kind survives restart/backup/restore. Reject Git paths/symlinks/traversal; separate app/data.
Init validates exact release/private profile/new or empty target/path safety/ownership/permissions/encryption/
explicit protected backup target/data-owner consent. Receipt local-only, no identity/private path in Git evidence.
No normal startup creates real private root; no filesystem discovery/import of existing private data.

Separate private preflight: exact release, Darwin/arm64/Python/runtime, ownership/permissions/ACL/path safety,
app/data separation, writable space, loopback, actual target volume encryption, backup protection, OFF defaults.
Status PASS/OPTIONAL_UNAVAILABLE/NOT_RUN/BLOCKED_BY_PERMISSION/INCOMPATIBLE/SECURITY_REQUIREMENT_NOT_MET.
No READY if protection unverified; no FileVault/security changes. Facts apply only to tested Mac; no username,
serial/Apple account/absolute home/private filename/content/secret/recovery information in evidence.
Accepted bounded model may use verified Mac volume/FileVault + owner-only FS + localhost + auto-lock;
no custom crypto/dependency download; no claim DB/archive encryption unless implemented and tested.
Compromised/unlocked OS out of scope. Backup must target explicit verified protected local storage, owner-only;
no automatic cloud/iCloud/Dropbox/Drive/network/upload/telemetry or retention deletion. Volume-protected archives
are not independently encrypted; copying to unencrypted storage removes that protection.

Private profile enforce journal/creative/search/backup restore ON; exact explicit local exports only with existing
safeguards. OFF: private/cloud AI, conversation inference, specialist/clinical0, health-to-AI/Health bridge,
human ASR/cloudASRNONE, external embeddings, phone, cloud sync/telemetry/publication/sharing/fallback.
Accidental provider credentials/environment must never activate capability. Preserve domain PRIVATE_PERSONAL /
USER_REPORTED etc.; private records never synthetic. Test content labeled in fixtures/evidence only.

UI truthful local private pilot/local-only label, never Synthetic demo; journal/creative usable first; unavailable
conversation not landing page; unsupported controls hidden/disabled; preserve visual design. No false provider/
clinical/Health/phone/voice/cloud backup claims. 127.0.0.1 only, Host/Origin/CSRF/session/deny-egress, no external DNS/
sockets/fonts/scripts/assets/provider fallback/update download/sync/telemetry. Verify auth/unlock/lock, memory-only
sessions/new restart unlock, inactivity auto-lock and no unauthenticated private API content.

Private backup preserves exact producer/source provenance, protection/root kind, history/tombstones/domains.
Private→private restore only into fresh root, consent/security revalidated; cross-mode/provenance/security failure
before target creation. Forbidden capabilities stay OFF after restore/upgrade. Upgrade+restart, failure, compatible
trusted backup fresh-root rollback+restart; no in-place downgrade. Uninstall REMOVE APP/KEEP DATA only. Separate
private-data delete requires exact root/destructive intent, rejects unknown/wrong kind, leaves backups, no secure
erasure claim; test only disposable roots.

## Actual Mac verification and acceptance

Final-C package exact PRIVATE_LOCAL_RUNTIME_WITH_SYNTHETIC_CONTENT: unmocked security preflight, explicit init,
startup/unlock/journal create/edit/search/creative/restart durability/UI, providerOFF/clinical0/all5OFF/HealthOFF/
voiceOFF/phoneOFF, external requests0, backup/restore/upgrade/rollback/uninstall KEEP DATA/separate delete/cleanup.
Existing Chromium relevant regressions; preserve M1–M8B. Deterministic tests cover distinct/wrong/corrupt modes,
confirmation/paths/symlink/Git/permissions/security schema/FileVault/backup gate/profile/environment/egress/UI/
CRUD/auth/lock/restart/provenance/restore/cross-mode/upgrade/failure/rollback/uninstall/delete/real data0.
Negative tests: unverified data or backup protection, group/world-writable root, symlink/Git root, private via
synthetic and reverse, provider/Health/clinical/phone/ASR activation, wrong backup kind/tampered provenance/delete
without exact confirmation. Fail closed.

M8C-A01 external M8B ACCEPT; A02 distinct root; A03 explicit secure init; A04 localhost/auth/egress;
A05 exact core profile; A06 optional activation blocked; A07 verified or blocked storage; A08 protected backup;
A09 release provenance; A10 private restore; A11 cross-mode refusal; A12 upgrade/failure/rollback;
A13 KEEP DATA; A14 separate delete; A15 truthful UI; A16 actual Mac synthetic-content private path;
A17 no private/provider/system/phone/Health activity; A18 exact post-ACCEPT operator procedure;
A19 core READY iff all pass; A20 actual pilot NOT_STARTED. Details in docs/M8C_CONTRACT.md.

Independent results: MAC_CORE_PILOT/PRIVATE_STORAGE_SECURITY/PRIVATE_BACKUP/ACTIVATION_PROCEDURE READY or NOT_READY;
PHONE_PILOT NEEDS_TRANSPORT_GATE/PHONE_PRIVATE_TRANSPORT_REQUIRED; PRIVATE_AI BLOCKED_M7C_N02;
HUMAN_UA_ASR NOT_RUN_M7C_N03; HEALTH_WATCH NOT_RUN_M6_N01; CLINICAL_SELF_HELP OFF_27_FINDINGS_OPEN;
M7D-N02 language review not a core blocker while conversationOFF; ACTUAL_PRIVATE_PILOT NOT_STARTED.

## Delivery

Create M8B_ARCHITECT_REVIEW, this goal/M8C_CONTRACT/security ADR, update PILOT_HANDOFF/INSTALL/UPGRADE/RECOVERY/
UNINSTALL/PRIVACY_SECURITY/TESTING/ROADMAP, report/evidence M8C, STATE/HANDOFF/append-only devlog and existing
context snapshot. Avoid duplicate canonical docs or historical evidence rewrite. Public material only exact hashes,
sanitized status/test counts/synthetic results/timings/synthetic screenshots. Never vault/path/username/IDs/real
receipt/backups/audio/health/unlock/secrets/FileVault recovery/generated runtime/release roots. Full tracked tree
and ALL local Git objects privacy scan before R and final push. Report test commands/exit/environment/CI truthful.
Standing workflow: final implementation C → exact-C tests + actual Mac private-mode synthetic dry run → evidence-
only R → full privacy/public review → normal FF main push → origin/main==R → STOP. No rewrite/review branch/
release/tag/deploy/actual pilot/next milestone. Completion executor AWAITING_REVIEW, never self-ACCEPT.
Final concise handoff: Base/C/R/origin, M8B review, M8C status, Python/Chromium/web/build/privacy/Mac, release ID/
manifest/runtime lock, kind/preflight/volume/perms/network/auth, backup policy/provenance/restore/rollback,
profile/readiness all modules, real data0/livecalls0/systemchanges0/CI, ACTUAL_PRIVATE_PILOT NOT_STARTED.
