# M8A: видалити runtime, зберегти дані

Зупиніть server. Команда видаляє лише керований app root; **KEEP DATA** — єдина uninstall поведінка.
Немає generic `--delete-data` flag.

```bash
.venv/bin/python -m apps.core.release uninstall --app "$APP_ROOT" --data "$SYNTHETIC_DATA_ROOT"
```

Journal/creative/conversations/vault/backups лишаються. Невідомий install marker/content/root → відмова.
Для навмисного видалення **лише синтетичного** data root існує інша команда з exact absolute-path confirmation:

```bash
.venv/bin/python -m apps.core.release delete-synthetic-data --data "$SYNTHETIC_DATA_ROOT" --confirm "DELETE_SYNTHETIC_DATA:$SYNTHETIC_DATA_ROOT"
```

Ця команда не авторизує реальні приватні дані й не видаляє інші backups/exports/browser copies.
Перевірте absolute path. Secure erasure не доведене: filesystem/OS backups, snapshots і копії можуть залишитися.
Lock inode може залишитися біля root; це не background process і не приватний вміст.

## M8C PRIVATE_LOCAL uninstall and separate deletion

Uninstall retains exactly KEEP DATA behavior for private mode; no generic delete-data flag:

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" uninstall --mode PRIVATE_LOCAL --app "$APP_ROOT" --data "$DATA_ROOT"
```

Separate irreversible owner action after checking the exact local path/root kind (tested only on disposable roots
with synthetic content in M8C):

```bash
"$PYTHON" -I -B "$PACKAGE/launch.py" delete-private-data --data "$DATA_ROOT" --confirm "DELETE_PRIVATE_LOCAL_DATA:$DATA_ROOT"
```

Deletes that validated PRIVATE_LOCAL vault only, refuses unknown/synthetic/corrupt/wrong-kind roots and missing
confirmation. Backups/exports/browser/OS snapshots are **not** silently deleted. No secure-erasure claim. Data may
remain in APFS/OS backups/copies; delete is not evidence of physical media erasure. Real deletion not authorized in M8C.


## M8D optional owner pilot

M8D keeps REMOVE APPLICATION / KEEP PRIVATE DATA. AI/voice disable/lock stops pending work and revokes session activation; local records/audio/backups are not silently erased. User-visible manual audio deletion claims no secure erase. Separate exact-confirmation PRIVATE_LOCAL deletion remains ADR-013; engineering uses disposable synthetic roots only.
