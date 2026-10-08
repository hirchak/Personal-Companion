# M8B: upgrade, backup, restore і rollback

Усі приклади — synthetic roots. Зупиніть foreground server (Ctrl+C). Running data lock відхилить операцію.
Збережіть trusted package + expected manifest hash для попередньої сумісної версії. Немає auto-update.

```bash
.venv/bin/python -m apps.core.release backup --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT" --backup "$NEW_BACKUP_ROOT"
.venv/bin/python -m apps.core.release upgrade --package "$NEW_PACKAGE" --manifest-hash "$NEW_HASH" --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT" --backup "$NEW_PREUPGRADE_BACKUP"
```

Upgrade перевіряє package hashes, platform/dependencies, app identity, synthetic marker, schema2–11 та integrity,
paths/port/storage; stages assets; створює consistent backup і перевіряє snapshot; **лише потім** ставить durable
upgrade-pending marker і запускає transactional migration. App pointer перемикається після успіху.
На error не продовжуйте startup. Migration failure/interrupt залишає backup і marker для explicit recovery.
Помилка preflight не запускає migration/backup. Source roots не мігруються просто через start/preflight.

Schema11 package приймає backup schemas2–11; restore мігрує їх до11. Це підтримка поточної release family,
не доказ запуску всіх historical application binaries. Future schema/incompatible release → відмова.
Backup зберігає typed domain provenance/history/tombstones; видаляє device authorization/consent approvals,
скасовує runtime jobs; finalized synthetic audio з checksum копіюється за accepted контрактом.
Backup **не encrypted at-rest**. Реальні дані/FileVault/encryption/retention потребують окремих M8B рішень.

Restore/rollback завжди у **нові** app/data roots:

```bash
.venv/bin/python -m apps.core.release restore --package "$COMPATIBLE_PACKAGE" --manifest-hash "$TRUSTED_HASH" --backup "$BACKUP_ROOT" --app "$FRESH_APP_ROOT" --data "$FRESH_SYNTHETIC_DATA_ROOT"
.venv/bin/python -m apps.core.release rollback --package "$OLD_COMPATIBLE_PACKAGE" --manifest-hash "$OLD_TRUSTED_HASH" --backup "$PREUPGRADE_BACKUP" --app "$ROLLBACK_APP_ROOT" --data "$ROLLBACK_SYNTHETIC_DATA_ROOT"
```

Rollback = сумісний package + відновлений pre-upgrade стан; немає in-place schema downgrade чи overwrite old root.
Для M8A сумісні local packages schema11; restored old schemas проходять прийняту migration до11.
Restore збільшує restore epoch/reconciliation, анулює pairing/approvals, блокує practice revalidation,
Health reconnect; не відновлює activation чи inference. Перевірте домени перед зміною operator-selected root.
Невдалий restore не стирає backup/існуючий root; partial outputs не використовуйте як installed root.
Оригінальний проблемний root лишається для recovery; не видаляйте його за замовчуванням.


## M8B release-aware provenance

New release backups format3 bind exact producing manifest/release/Git, source release reference, snapshot schema,
creation time і snapshot-only SQLite attestation. При upgrade backup створює NEW verified manager; source release
може бути OLD. Snapshot checksum охоплює attestation; restore перевіряє exact equality/compatibility перед roots.
Receipt повертає `backup_manifest_hash`; збережіть окремо. Для сильнішої unsigned перевірки додайте
`--backup-manifest-hash "$TRUSTED_BACKUP_HASH"` до restore/rollback. Across-release producer default не вгадується:
додайте `--producer-manifest-hash "$TRUSTED_PRODUCER_HASH"`, якщо target package має інший manifest hash.
Це checksums із trusted hashes, не підпис/notarization.

Generic historical Store backups format1/2 не отримують вигаданий producer і зберігають історичний app_version.
Release restore відхиляє їх за замовчуванням; deliberate compatibility choice `--allow-legacy-backup` дає
LEGACY_UNKNOWN_PRODUCER та звичайну typed snapshot validation. Не застосовувати цю опцію для обходу corrupt
format3 provenance. Новий private pilot тут не дозволений; див. PILOT_HANDOFF.md.

## M8C PRIVATE_LOCAL maintenance (after explicit activation)

The historical examples above remain SYNTHETIC_TEST. Use explicit `--mode PRIVATE_LOCAL` for the distinct private
installation. Archive at-rest protection = freshly verified FileVault-protected APFS volume + owner-only container;
NOT application-encrypted archive. Copying to unencrypted storage removes protection. No backup cloud routing/delete.
Private backup format4 binds private identity/policy to release producer/source/snapshot attestation. Trusted independent
producer and backup manifest hashes remain required operator practice; no signature claim. Cross-mode restore fails.

Run from exact trusted **new** package for upgrade; backup target must be a new child of the acknowledged protected
backup container, and server must be stopped. New manager is the producer; old active package is source.

```bash
"$PYTHON" -I -B "$NEW_PACKAGE/launch.py" upgrade --mode PRIVATE_LOCAL --package "$NEW_PACKAGE" --manifest-hash "$NEW_HASH" --app "$APP_ROOT" --data "$DATA_ROOT" --backup "$NEW_PREUPGRADE_BACKUP"
```

Restore/rollback require compatible PRIVATE_LOCAL-aware M8C package, fresh application/data roots, protected source
backup plus target volume/container, and renewed explicit acknowledgement. Old M8A/B cannot open private roots.
No in-place downgrade or silent synthetic conversion. Exact selected target root is confirmed again:

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" restore --mode PRIVATE_LOCAL --package "$COMPATIBLE_PACKAGE" --manifest-hash "$TRUSTED_HASH" --producer-manifest-hash "$TRUSTED_PRODUCER_HASH" --backup-manifest-hash "$TRUSTED_BACKUP_HASH" --backup "$BACKUP_ROOT" --app "$FRESH_APP_ROOT" --data "$FRESH_DATA_ROOT" --backup-directory "$BACKUP_DIRECTORY" --confirm "INITIALIZE_PRIVATE_LOCAL:$FRESH_DATA_ROOT" --data-owner-consent I_AM_THE_DATA_OWNER_AND_CONSENT_TO_LOCAL_STORAGE_AND_PROTECTED_LOCAL_BACKUPS --acknowledge-no-cloud-directory
```

For rollback use the same command with `rollback`, trusted old-compatible M8C package and preupgrade backup.
Root identity renewed; domain privacy/provenance/history/tombstones preserved. Device/AI/Health/practice reapproval
states remain invalidated, every optional profile capability stays OFF. Start uses `--mode PRIVATE_LOCAL` after verifying
restored state. Failed migration leaves verified backup/pending marker/original pointer; restore into fresh roots,
never remove marker to bypass recovery. Detailed initial activation: [PILOT_HANDOFF](PILOT_HANDOFF.md).


## M8D optional owner pilot

M8C→M8D is an explicit application upgrade with protected pre-upgrade backup and fresh private security preflight. Preserve the same root identity/schema11 and journal data; no existing-data migration/discovery during M8D. Optional AI/voice stay OFF after startup and need local acknowledgements. See [pilot handoff](PILOT_HANDOFF.md#m8d-optional-aivoice--post-accept-owner-procedure-not-executed).

M8D lifecycle commands accept an explicit loopback `--port` for initialize/upgrade/restore/rollback as well as preflight/start. Default8765 is unchanged. The actual selected port must be free; this isolates disposable engineering roots from an existing core pilot without weakening the socket preflight.

### M8E historical source profile

Source selection recognizes the exact previous voice declaration `EXPLICIT_OWNER_GATE_DEFAULT_OFF` alongside
the current `LOCAL_SESSION_ONLY_NO_AI_CONSENT`. All other profile fields, manifest identity and the complete
file-hash set must still match. New upgrade targets require the current profile; an unknown or modified source
profile fails before backup/activation. This permits the protected existing-vault upgrade to the independent
local-microphone hotfix without editing the installed source manifest, its files, or the vault.
