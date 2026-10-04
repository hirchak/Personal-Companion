# Особистий пілот: handoff після M8B, без активації

M8B перевіряє конкретний Mac із disposable ORIGINAL SYNTHETIC даними. Це не реальний приватний пілот.
Планований профіль — MAC_CORE_PILOT_V1: щоденник, творчість, локальний пошук і backup/restore ON.
Profile файл не активує runtime. Чинний пакет приймає лише synthetic roots; реальний private-root mode потребує
окремої owner goal, реалізації/перевірки точного data labeling і згоди власниці даних. Його не створено в M8B.

## Незалежні readiness gates

| Частина | Стан / наступна дія |
|---|---|
| Mac synthetic engineering dry run | READY тільки після exact-C preflight/lifecycle PASS на цьому Mac |
| MAC_CORE_PILOT із реальним vault | NOT_READY: PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED; окрема bounded owner goal для private local mode/consent/storage |
| PHONE_PILOT | NEEDS_TRANSPORT_GATE: PHONE_PRIVATE_TRANSPORT_REQUIRED |
| Private AI | BLOCKED_M7C_N02; retention/private suitability NOT_VERIFIED |
| Human UA ASR | NOT_RUN_M7C_N03; голосові samples/retention потребують окремої згоди |
| Health/Watch | NOT_RUN_M6_N01; final bridge0.6.1 hardware не перевірено |
| Clinical/self-help | OFF_27_FINDINGS_OPEN; content/rights/admission review не закрито |

Optional AI/ASR/Health/clinical/phone не є причиною core NO-GO. Причина — відсутність дозволеного private-root
runtime profile. Перший real core pilot може бути Mac-only після закриття цього окремого gate.

## Операторський цикл

Application/runtime directory і private data directory — різні каталоги без вкладення. Майбутній private root
обирає власниця, поза Git/public/cloud-sync folders; концептуально — її локальний Application Support/vault.
Не підміняйте приватний root synthetic marker і не створюйте його командами M8B. Права доступу, FileVault,
backup storage/encryption/retention і згода власниці — окремі передумови активації. Backup зараз не encrypted at-rest.

Для вже дозволеного **синтетичного** root застосовуються точні [INSTALL](INSTALL.md), [UPGRADE](UPGRADE.md),
[RECOVERY](RECOVERY.md), [UNINSTALL](UNINSTALL.md). Після майбутнього scoped private-mode goal команди й mode
мають бути явно оновлені/перевірені; нижче не є інструкцією запустити real private vault зараз.

- Start — foreground local127.0.0.1; one-time unlock лише в операторському terminal. Не зберігати код у logs/evidence.
- Stop — Ctrl+C. Restart — той самий verified app/data root; новий код; interrupted work не auto-resume.
- Backup — зупинити сервер; release backup команда повертає producing release hash + backup manifest hash.
  Зберегти receipt/hashes окремо від backup і перевірити restore у новий root. Backup сам по собі не шифрує дані.
- Restore/rollback — нові roots, trusted expected package/producer/backup hashes; no in-place downgrade/overwrite.
  Pairing/consent/jobs/Health revalidation не воскресають автоматично.
- Uninstall — KEEP DATA: видаляється лише керований application/runtime; vault/backups зберігаються.
- Stop pilot safely — Ctrl+C, verified backup/export за explicit choice, залишити data root; не видаляти все як recovery.
- Data removal — лише окремий unmistakable explicit choice. Поточна delete-synthetic-data команда призначена лише
  для synthetic roots; майбутній real mode потребує свого перевіреного consent flow. Secure erasure не доведене;
  backups/exports/browser/OS copies можуть залишитися.

Зараз OFF: private provider/AI, усі5 self-help candidates, clinical0, health-to-AI/Health bridge/human voice ASR,
external embeddings; cloudASRNONE, telemetry/cloud sync/publicationNONE. Відсутні downloads/fallback/autostart.
Не вважайте flags OFF доказом шифрування чи придатності стороннього provider для приватного щоденника.

## Мінімальний окремий phone transport gate

Репозиторій має candidate ADR-002, а не accepted діючий private HTTPS endpoint; package phone transport OFF.
На перевіреному Mac Tailscale CLI відсутній. Нові private network/account endpoints не шукалися й не зчитувалися.
Наступна окрема owner transport goal повинна вибрати точний приватний route та дозволити лише потрібні
client/account/config/trust зміни; адаптувати exact HTTPS Origin/Host/auth/pairing і виконати Galaxy synthetic smoke.
Якщо обрано Tailscale Serve candidate, дозвіл на client/account/Serve потрібен окремо; не Funnel/public exposure.
Без такого gate телефонне hardware тестування не починається. Не обходити TLS warnings.

PWA candidate має schema2 encrypted IndexedDB (native PBKDF2/AES-GCM), transactional outbox,
локальний shell cache та explicit waiting-update activation; це підтверджують code/build/desktop Chromium тести.
Відсутній cloud backend/automatic provider/clinical/Health activation. Real Galaxy/background/storage eviction/
persistence/private HTTPS, Watch/Health0.6.1 та human UA ASR лишаються NOT_RUN, не підмінені desktop evidence.
