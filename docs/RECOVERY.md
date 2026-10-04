# M8A: recovery і окремі gates особистого пілоту

| Збій | Що збережено | Безпечна дія |
|---|---|---|
| App не стартує / prerequisite відсутній | Data root | preflight; перевірте exact Python/dependencies, не встановлюйте system software в M8A |
| Wrong/future schema | Оригінальна DB, backup | Сумісний trusted package; не downgrade DB in-place |
| Corrupt package/hash/missing asset | Vault | Відновіть exact verified package; не змінюйте hashes щоб обійти gate |
| Stale frontend | Vault, mounted draft; encrypted phone store | Скопіюйте draft; explicit verified update/reload. Не очищайте IDB як fix |
| Failed/interrupted migration | Transactional DB, verified backup, pending marker | Restore compatible backup у нові roots; не стирайте pending marker для обходу |
| Interrupted backup | Source DB; final backup якщо atomically published | Не використовуйте .partial; повторіть у новий target після зупинки server |
| Failed restore | Backup + unrelated existing roots | Перевірте checksum/compatibility; новий root; partial root не запускати |
| Locked session | Збережені записи | New foreground restart/new local unlock; autosaved drafts не обіцяються |
| Provider unavailable | User text/history; failed job | У M8A OFF; no fallback/retry/new auth, не відновлюйте inference автоматично |
| ASR unavailable / partial | Saved finalized synthetic audio; partial rules | Package LOCAL unavailable; delete/retry explicitly після окремого existing-ASR gate; cloud NONE |
| Phone sync unavailable | Encrypted local phone state/outbox | Збережіть encrypted recovery; transport/pairing потребує нового дозволу |
| Health Connect unavailable | Journal/creative, explicit missing state | Optional/source reconnect після окремої hardware goal; missing ≠ zero |
| Root busy | Vault, live foreground process | Зупиніть саме свій server Ctrl+C; lock inode не видаляти, довільний PID не kill |

## M8B readiness checklist — NOT_STARTED

M8A не є пілотом. До M8B потрібні explicit owner goal + відповідні дозволи/рішення:

- Встановити/запустити exact package на реальному Mac, перевірити prerequisites/FileVault/access/backup policy.
- Використовувати конкретний real private data root; згода власниці даних на data flow/retention.
- Окремо мігрувати будь-які existing private дані (за потреби), із перевіреним backup/restore.
- Реальний phone pairing і перевірка Android PWA persistence/offline/lock/recovery на Galaxy.
- Будь-яке private networking/Tailscale/account/client/certificate/trust setup — окремий scoped дозвіл.
- Реальний Health Connect/Watch read-only test; M6-N01 final0.6.1 hardware OPEN/NOT_RUN.
- Human Ukrainian ASR samples/real microphone/audio retention — scoped consent; M7C-N03 OPEN/NOT_RUN.
- Provider retention/private-personal suitability review: M7C-N02 OPEN HARD gate; окреме activation рішення.
- Якщо cloud inference колись дозволене: exact route/model/settings/context/consent і billing limits,
  no PAYG/fallback. Luna/max FREE і Sol/ultra DEEP — лише provisional candidates.
- Qualified content/rights/admission review перед будь-якими clinical/specialist capabilities; зараз27OPEN/clinical0.

Це checklist, не запит дозволів зараз. Clean Mac, S24 Ultra/Watch7/Health0.6.1, real Android conditions,
human UA ASR/private HTTPS/Tailscale залишаються NOT_RUN/HARDWARE_UNVERIFIED; synthetic smoke їх не закриває.
