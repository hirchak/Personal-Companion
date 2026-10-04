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
