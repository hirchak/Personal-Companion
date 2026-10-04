# ADR-011 — Exact local release, foreground lifecycle and fresh-root rollback

2026-10-04. Status: IMPLEMENTED_AWAITING_REVIEW. Synthetic engineering only.

Package is an unsigned directory built from one clean Git commit and existing dependencies. Includes Python
source, exact requirements input, web lock, built local UI, neutral contracts and metadata-only admission registry.
No venv/node_modules/Git/auth/private data/ASR weights bundled. Python3.13 with all requirements.lock versions,
Darwin arm64 are current supported assumptions, not a clean-Mac compatibility certification. No install/download.
Manifest binds every payload file/hash, schema11, web contract2, contract versions via source/JSON hashes,
default states and exact commit. Expected manifest hash is provided separately by operator. Hash verification is
integrity evidence, not signature/notarization or protection from a malicious trusted build/OS.

Application root contains immutable release directories, installation marker and atomic active pointer;
synthetic data root is a separate sibling/outside subtree. Data marker remains the accepted M1 contract.
Single OS advisory lock next to data is held throughout foreground server/backup/upgrade/removal. Lock file remains
on disk; OS releases lock on process exit. No PID-based kill/daemon/autostart. Launcher exec replaces itself;
operator Ctrl+C/SIGTERM stops that server. All startup socket egress is denied except loopback.

Upgrade stages/verifies app assets before data mutation, makes accepted consistent sanitized backup using a
non-migrating Store handle, verifies it, writes durable pending marker, then invokes transactional Store migration.
Only afterward switches active pointer. Failed migration preserves DB + backup + pending marker; start refuses.
Pre-upgrade SQLite snapshot is an additional internal safety artifact, never the only rollback backup.
No silent schema initialization/migration during packaged start. Metadata/capability states cannot opt into providers.

Rollback means compatible package + backup restored into new app/data roots. Restore deliberately increments epoch,
revokes approvals/devices, marks work failed/reapproval-required, clears runtime activation and reconnects health.
No in-place downgrade: schema2–11 backups migrate to schema11 using this release; incompatible app/schema is refused.
Current rollback packages are schema11 releases. Historical schema projection tests are labeled; a minimal genuine
schema2 fixture also proves upgrade/restore without newer tables. Do not claim old schema binaries were tested.

Web emits exact commit header on every API request. Packaged API refuses stale/missing commit before auth/domain
operations; public same-origin release.json provides compatibility metadata. Wrapper shows update state and retains
mounted draft UI for copying; encrypted phone store stays schema2. Waiting SW activation remains explicit. M2
phone route is disabled in packaged synthetic launcher; phone transport/device tests remain distinct.

Uninstall validates managed synthetic installation and removes app only. A separately named data-delete command
requires exact DELETE_SYNTHETIC_DATA:<absolute-root>; backups/exports may survive. No secure-erasure claim.
ASR is explicitly OPTIONAL_UNAVAILABLE in package; existing checkout ASR remains a separate verified synthetic gate.
No real private data/clinical/pilot/provider release permission is created by this architecture.

Synthetic data labeling and legacy mock responses are separate switches. Packaged /messages cannot synthesize
an assistant response while controller is OFF; release factory rejects provider/ASR/phone/practice activation inputs.
Two distinct labeled synthetic manifest fixtures verify app staging/replacement and failed-migration rollback;
they are installation simulations, not newly published historical release builds.
