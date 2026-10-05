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

## M8D optional AI/voice — post-ACCEPT owner procedure (NOT EXECUTED)

M8D implementation is AWAITING_REVIEW. Existing real core vault is never used in engineering.
After independent M8D ACCEPT, the owner may activate this optional profile on the existing PRIVATE_LOCAL
vault; no new vault, import/discovery or migration. Keep the accepted M8C application and compatible
pre-upgrade backup for fresh-root rollback. Human Ukrainian ASR remains OPEN_HUMAN_TEST.

1. Verify the exact accepted M8D implementation package/manifest from the final report, runtime lock and
   file hashes; use its local `launch.py`, existing Python/Codex/whisper assets only. Stop the foreground
   M8C app. Retain a backup created by the accepted M8C manager before optional activation, or recover a compatible pre-upgrade backup using the accepted M8D manager with the M8C target package. The old M8C manager cannot validate a new M8D producing manifest. The owner supplies existing app/vault/backup paths locally; never paste them into Git/reports.
2. Run accepted M8D `private-preflight --package "$PACKAGE" --manifest-hash "$HASH" --app "$APP"
   --data "$VAULT" --backup-directory "$BACKUPS" --port 8765`. Every required check must PASS.
   FileVault/volume/0700-0600/ACL/app-data/backup policies remain ADR-013. Missing prerequisite: stop;
   no system security, auth, dependency, network or billing changes to fix it silently.
3. Run `upgrade --mode PRIVATE_LOCAL --package "$PACKAGE" --manifest-hash "$HASH" --app "$APP"
   --data "$VAULT" --backup "$BACKUPS/owner-chosen-pre-M8D-backup"`. This preserves the same vault
   and creates a protected exact-provenance backup before selecting the new application. No in-place
   downgrade. Check output PASS; retain backup/producer/manifest hashes locally.
4. Select the already installed verified local ASR assets explicitly. Start `start --mode PRIVATE_LOCAL
   --app "$APP" --data "$VAULT" --port 8765 --local-asr-assets "$LOCAL_ASR_ASSETS"` using accepted
   M8D launcher. This does not install/download a model. One-time unlock code stays in the local terminal.
5. Open `http://127.0.0.1:8765`, unlock, then «Розмова». AI and local voice initially OFF. Expand controls:
   owner acknowledges text leaves Mac for existing OpenAI/ChatGPT subscription, audio stays local,
   only exact approved context, no zero-retention certification, no fallback/PAYG; confirms ChatGPT
   Improve the model for everyone OFF and Codex Include environments OFF. This procedure does not
   inspect/change those settings. Click explicit session AI enable; failure stays visible, no substitute.
6. FREE defaults Luna/High. Choose DEEP economical Luna/Max or quality Sol6.1/High explicitly. Sol above
   High is forbidden. Changing profile invalidates previous context previews and stops pending inference.
   Approve the separate local-only audio/review/manual-deletion acknowledgement to enable voice.
7. Every send shows exact current text/history/goal/focus/map and any explicitly selected journal entries,
   destination/model/effort. Journal is OFF by default; no whole-vault discovery. Confirm only after
   reviewing the exact preview. Silence blocks ASR, uncertain candidates need review/edit. Transcription
   inserts a draft; it never sends automatically. Audio is retained locally until explicit deletion.
8. Owner-side human UA test after ACCEPT: five short natural utterances (normal quiet speech; optionally
   names/numbers; one very short phrase; one after brief silence). Review/edit local transcripts, decide
   usefulness. Keep recordings/transcripts/private details local; only a sanitized verdict may be supplied
   later under explicit authorization. Engineering synthetic TTS does not close human quality.

Lock/disable/restart/restore leave AI/voice OFF and require local acknowledgements again. Backup/restore
uses the same protected-volume policy and exact provenance; restoration repeats private security/data-owner
consent. Never recreate the actual vault to activate AI. Clinical/all specialists/Health/phone/embeddings/
cloud ASR/sync/telemetry/publication remain OFF/NONE. Actual private AI activation during M8D = NOT_STARTED.

M8D delivered C `d0b24846ced133864c45dc0b0eb71a1b01f0e947`, release `M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947`, manifest `4dcef73b066f3adf7c969baedb9d76b39d7885e58967c44c90e8cd986a57a866`, runtime lock `f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`. Use only after independent ACCEPT of that exact implementation; current actual AI activation NOT_STARTED.


### Independent M8D review gate — 2026-10-05

C1 d0b24846 / R1 aa5d027 = FIX_REQUIRED (R01/R02); the C1 activation procedure is not authorized for execution
until a corrected exact implementation receives independent ACCEPT.
TRAINING_CONTROL_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
CODEX_ENVIRONMENTS_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
No owner-settings confirmation to the architect is asserted. Owner must explicitly provide the required
literal-true local runtime acknowledgements at real activation; no account/settings inspection or real activation
occurs in engineering. Canonical preview must show the exact ordered provider context and reflection state;
stale/reordered approval fails. Native engineering ledger exhausted4/4; only fixture providers for this correction.

Corrected M8D candidate C2 `96a61da305b98c7c33112f47fc134be8e36e79ec`, release `M8D-96a61da305b98c7c33112f47fc134be8e36e79ec`, manifest `846266388233eeded13fe332064df4d41d415a654c1d30fb47556cbf05d3d4dd`. Earlier C1 activation reference is superseded; use corrected exact release only after independent ACCEPT and explicit local real-activation settings confirmations. This procedure remains NOT EXECUTED.


### Owner-authorized M8D activation — external ACCEPT, 2026-10-05

Exact C2 96a61da305b98c7c33112f47fc134be8e36e79ec / R2 20e86a7e7204d0332638e30348b1329364de7ac0
is now independently ACCEPTED. Owner explicitly confirms training/environment controls OFF for this activation
only (no account/settings inspection, zero-retention/commercial/third-party certification). The historical
NOT_YET_CONFIRMED_TO_ARCHITECT status above is superseded for this new activation by explicit owner statements,
not retroactively changed in engineering evidence. Upgrade EXISTING vault only; no initialize/new vault/import.
Owner manually unlocks, acknowledges disclosures, enables voice, chooses Deep model, records/reviews/previews/sends.
Agent performs only preflight/protected backup/preservation/app upgrade/pinned assets/startup; no AI send or recording.
