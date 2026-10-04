# ADR-013 — Private local core root, volume protection and protected local backups

2026-10-04. ACCEPTED_EXTERNAL_REVIEW. M8C uses ORIGINAL SYNTHETIC content only.

Keep existing SYNTHETIC_TEST marker/fixtures intact. PRIVATE_LOCAL has its own typed receipt and SQLite
private_root_identity attestation, bound identically; installation additionally binds root kind/id. No startup
initialization, guessing an existing vault, loose-flag conversion, cross-mode restore or existing-data discovery.
Same owner can deliberately rewrite the database/code/receipt; this is corruption/mix-up protection, not tamper
resistance against a compromised/unlocked OS. No custom crypto or signature claim.

Bounded security policy: actual APFS target volume must report FileVault=True, Encryption=True AND
EncryptionThisVolumeProper=True via read-only diskutil plist; map the supplied path by filesystem device, including
Mac Data firmlinks. No global FileVault status alone, hardware encryption alone, or system sealed-volume encryption
claim. Unknown/error/permission denied fails closed. Native metadata/IDs remain transient, only status is emitted.
[Apple Platform Security](https://support.apple.com/en-au/guide/security/sec4c6dc1b6e/1/web/1) describes the
credential-bound FileVault model and distinguishes unprotected hardware UID encryption.

Data/application/backup container require owner UID, directory0700/file0600 and no extended ACL grants;
unsafe/Git/symlink/traversal/cloud-folder paths rejected. Owners acknowledge that chosen folders are not externally
synchronized; the application cannot disable OS backups or third-party sync agents. Application-level DB and archive
encryption NOT_IMPLEMENTED. Unlocked OS, malware/admin/same-user browser/system copies remain outside protection.
Local auth/15-minute idle and8-hour absolute lock, one-time terminal code, in-memory server session only, session-only HttpOnly/SameSite cookie (no Max-Age/Expires), restart new unlock.
The app/foreground process is local127.0.0.1; Host/Origin/CSRF/build-header/CSP/deny-egress preserved.

Private backup is manual to an explicitly chosen owner-only directory on a freshly verified protected local APFS
volume. Format4 preserves root kind/private receipt/security policy, exact producer/source/schema/time, snapshot-
only release attestation/checksum and database root identity. Independently retain backup/producer hashes; checksums
are not signatures. Archive is protected by the volume, NOT independently encrypted. Moving/copying to an
unencrypted location removes protection; restore rechecks source protection. No cloud routing/upload/retention delete.
Fresh-root restore/rollback repeats explicit data-owner acknowledgement and target-security gates, generates a new
root identity and keeps domain provenance/history/tombstones. No private↔synthetic conversion or in-place downgrade.
M8A/B packages cannot open private roots; rollback needs a compatible M8C private-aware package.

Private release manifest format3/M8C exact C binds MAC_PRIVATE_CORE_PROFILE. Existing format1/2 + backup1/2/3
synthetic compatibility remains. Journal/creative/search/explicit local export + manual maintenance allowed;
API allowlist denies every optional/future route. Provider env ignored, factory rejects optional injection;
Runtime refuses non-OFF mode. AI/clinical/all5/Health/ASR/phone/embeddings/sharing/cloud/telemetry remain OFF/NONE.
UI journal landing/local-private label; optional surfaces hidden. Minimal public runtime-mode has no content/identity.

Initializer requires exact trusted release + exact INITIALIZE_PRIVATE_LOCAL:<root> + literal data-owner
acknowledgement + no-cloud-directory acknowledgement + protected backup container. Receipt stays local, contains
no personal identity. Actual private pilot/root not initialized during M8C. Post-review owner/data-owner activation
needs no additional core engineering milestone if final acceptance criteria pass. Optional module gates unchanged.
Uninstall keeps private data; separate DELETE_PRIVATE_LOCAL_DATA:<root> never deletes backups or claims secure erasure.

External architect ACCEPT exact Ca00a1427/R4eb8188 durably recorded in reports/M8C_ARCHITECT_REVIEW.md.
The engineering synthetic-only scope above is historical M8C; owner now separately authorizes new-empty
private core activation through the unchanged accepted handoff. No developer access to future contents.
