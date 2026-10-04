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
