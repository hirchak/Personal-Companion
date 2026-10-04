# Mac-only core pilot: post-M8C ACCEPT activation handoff

**Do not execute during M8C.** M8C tests the production PRIVATE_LOCAL path using disposable ORIGINAL SYNTHETIC
content only. ACTUAL_PRIVATE_PILOT NOT_STARTED; actual private root NOT_CREATED. After independent M8C ACCEPT,
explicit owner/data-owner activation may start a new empty Mac-only vault without another core engineering milestone
if all core readiness criteria pass. Existing private data import/migration requires a separate exact-source action.

## Independent gates

MAC_CORE_PILOT, PRIVATE_STORAGE_SECURITY, PRIVATE_BACKUP, ACTIVATION_PROCEDURE are READY only when final exact-C
checks/unmocked security + private lifecycle pass; see reports/evidence/M8C/PILOT_READINESS.json after completion.
These are engineering readiness, not consent, release publication, clinical approval or actual activation.
PHONE NEEDS_TRANSPORT_GATE / PHONE_PRIVATE_TRANSPORT_REQUIRED. Private AI BLOCKED_M7C_N02; human UA ASR
NOT_RUN_M7C_N03; Health/Watch NOT_RUN_M6_N01; clinical/self-help OFF_27_FINDINGS_OPEN; five specialists OFF.
M7D-N02 OPEN_HUMAN_LANGUAGE_REVIEW is not a core blocker with conversationOFF. No phone/Tailscale/cert changes.

## Exact operator procedure after independent ACCEPT and explicit activation

1. Select the **exact accepted** M8C source package/release ID/manifest hash from the final report and retain a
   trusted copy. Verify installed Python3.13/Darwin arm64 + exact requirements.runtime.lock. No automatic download
   or system dependency installation; unsigned checksums are not notarization/signatures.
2. Choose local application/data roots outside Git/cloud-sync folders; neither may contain the other. First vault
   must be NEW or genuinely EMPTY. Do not select an existing journal/Obsidian/other-app vault. Choose an explicit
   separate local backup container on verified FileVault-protected APFS storage. Verify externally configured
   sync/OS backups; this app cannot switch them off. Operator creates only chosen app/data parents and backup
   container as owner0700, with no extended ACL. No encryption/system changes are performed by the app.
3. Set local variables (never put actual paths/consent/unlock into public evidence): `PYTHON`, `PACKAGE`,
   `EXPECTED_HASH`, `APP_ROOT`, `DATA_ROOT`, `BACKUP_DIRECTORY`. Parents must already exist; application root new.
   Data/backup files require0600/directories0700. Preflight verifies actual filesystem device/volume/FileVault,
   permissions/ACL/symlink/Git/cloud path/runtime/space/loopback and exact release/profile.

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" private-preflight --package "$PACKAGE" --manifest-hash "$EXPECTED_HASH" --app "$APP_ROOT" --data "$DATA_ROOT" --backup-directory "$BACKUP_DIRECTORY"
```

4. The data-owner reads the local-only/backup policy and deliberately acknowledges it. This consent is separate
   from developer/architect acceptance. The literal below acknowledges local storage and protected local backups;
   no identity is requested. Exact root confirmation prevents accidental activation. No normal startup does this.

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" initialize-private --package "$PACKAGE" --manifest-hash "$EXPECTED_HASH" --app "$APP_ROOT" --data "$DATA_ROOT" --backup-directory "$BACKUP_DIRECTORY" --confirm "INITIALIZE_PRIVATE_LOCAL:$DATA_ROOT" --data-owner-consent I_AM_THE_DATA_OWNER_AND_CONSENT_TO_LOCAL_STORAGE_AND_PROTECTED_LOCAL_BACKUPS --acknowledge-no-cloud-directory
"$PYTHON" -I -B "$PACKAGE/launch.py" start --mode PRIVATE_LOCAL --app "$APP_ROOT" --data "$DATA_ROOT" --port 8765
```

5. Open `http://127.0.0.1:8765`, enter the one-time code shown only in the foreground operator terminal. Do not log,
   screenshot, share or save it. UI says «Локальний приватний пілот», opens the journal, then «Додати запис» → text →
   «Зберегти на Mac». First real entry happens **only after this explicit post-review activation**, never in M8C.
6. Journal/creative/local search available; explicit previewed local exports retained. AI conversation/Health/
   voice/phone/clinical/sharing/cloud/telemetry are unavailable and hidden. No provider keys/env enable them.

## Stop, restart, lock and backup

Ctrl+C stops the single foreground runtime; no autostart/daemon. Restart with the same explicit PRIVATE_LOCAL roots
creates new unlock state. Lock erases UI/session access; after lock use foreground restart for a new code. Idle15min,
absolute8hours. Private cookie is session-only; reusable server credentials are never persisted. Unsaved drafts are not promised durable. All app requests/assets localhost; no network egress.

Stop before backup/maintenance. Choose a **new** snapshot child directly inside the consented backup container:

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" backup --mode PRIVATE_LOCAL --app "$APP_ROOT" --data "$DATA_ROOT" --backup "$NEW_BACKUP_ROOT"
```

Retain producing manifest hash and backup manifest hash separately in a protected owner-local receipt; never Git.
Test a fresh-root restore before depending on backup. Backup protection is verified FileVault/volume + owner-only
access, **NOT independently encrypted archive**; copying to unencrypted storage removes protection. No automatic
retention deletion, cloud upload or synchronization. SQLite application encryption NOT_IMPLEMENTED.

[UPGRADE](UPGRADE.md) defines protected backup/restore/upgrade/rollback commands and explicit renewed consent.
[RECOVERY](RECOVERY.md) defines fail-closed recovery; do not delete markers or downgrade in place.
[UNINSTALL](UNINSTALL.md) removes application/keeps vault/backups and defines separate exact-root private deletion.
Safely stop pilot: stop process, choose verified protected backup/export if needed, preserve data; no generic wipe.

## Security limitations

Protection is for data at rest on verified FileVault-protected volumes and normal local access boundaries.
Compromised/unlocked OS, same-user malware/admin/browser extensions/system screenshots/OS backups remain outside
this model. One-time local terminal unlock is not a separate at-rest encryption password. No secure-erasure claim.
Actual native facts apply only to tested Mac; re-run security checks on the actual activation Mac/target volumes.
No extra engineering milestone is required for core activation after ACCEPT when these checks pass; any newly
missing prerequisite remains an explicit blocker, not permission to alter system security or install dependencies.
Phone/private provider/human ASR/Health/clinical modules each require separate gates and authorizations.
