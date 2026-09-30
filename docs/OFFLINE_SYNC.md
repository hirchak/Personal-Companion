# Телефон, офлайн-робота і синхронізація

## Контракт доступності

| Стан | Доступно | Недоступно/обмежено |
|---|---|---|
| Mac online, телефон бачить endpoint | Capture, sync, ASR, дозволений AI | Немає гарантії latency |
| Mac вимкнений, встановлена PWA | Локальний текст/аудіо, cached data, static матеріали | Mac AI/ASR/sync |
| Немає інтернету, Mac у приватній мережі | Локальна синхронізація за робочого HTTPS, ASR | Cloud providers |
| Браузер закритий | Вже збережені локальні записи | Фонові jobs/нагадування не гарантуються |
| PWA ще не встановлена | Потрібне початкове завантаження | Не обіцяти cold-start offline |

Service worker і кеш дозволяють offline shell, але не перетворюють браузер на постійний
сервер [S07]. IndexedDB best-effort storage може бути видалене браузером; запит на
persistent storage може бути відхилений, а користувач завжди може очистити дані [S08].
Показувати попередження «ще немає копії на Mac» та запропонувати encrypted export.

## Transport baseline

M2 має довести один маршрут: HTTPS PWA і API на стабільному приватному origin Mac,
який доступний авторизованому телефону в домашній мережі. Після першого завантаження
PWA працює офлайн; при поверненні до мережі синхронізується. `localhost` на телефоні
означає телефон, не Mac. Самого IP ноутбука в HTTP недостатньо для production mode.

Потрібні валідний для клієнта TLS, pairing і реальна перевірка Samsung/Chrome.
Self-signed certificate з ігноруванням browser warnings не є прийнятним рішенням.
Спосіб TLS/private DNS/приватного тунелю обирається в transport ADR після spike.
До цього доступні synthetic prototype та encrypted export/import як ручний fallback.
Віддалений доступ поза домашньою мережею — опційний окремий gate; не відкривати порти
роутера й не додавати незахищений tunnel «щоб просто запрацювало».

Vercel-shell mode складніший: cross-origin auth, CORS, CSP, cookies/token handling,
Local Network Access permissions і довіра до remote JS. Браузер може вимагати окремий
дозвіл для звернень до локальної мережі [S09]. Перевіряти конкретні версії браузерів.
Не відключати захист браузера як інструкцію для користувачки.

## Outbox і контракт запису

Кожна локальна операція: `operation_id`, `device_id`, `entry_id`, `base_revision`,
`operation_type`, `created_at_utc`, `timezone`, `schema_version`, encrypted payload.
UUID/ULID генерується до синхронізації. Запис у local store і outbox — одна транзакція.
UI підтверджує збереження тільки після завершення транзакції.

Mac приймає пакет після auth/schema/size validation. У тій самій DB transaction:
перевіряє idempotency key, застосовує операцію, фіксує receipt і server revision.
Повтор після timeout повертає той самий результат, а не створює другий запис.
Транспорт at-least-once; вимога — ідемпотентний ефект, не магічний exactly-once delivery.

Стани: LOCAL_SAVED → QUEUED → SYNCING → MAC_CONFIRMED; окремо CONFLICT/FAILED.
AI статус відокремлений: NOT_REQUESTED/QUEUED/RUNNING/DONE/FAILED/CANCELLED.
Результат AI не є підтвердженням синхронізації.

## Конфлікти, час і видалення

Для одного запису з двох пристроїв — optimistic concurrency за base_revision.
Не перезаписувати зміст останнім wall-clock timestamp. Показати обидві версії й
дати об’єднати/вибрати; зберегти походження. Простий append-only capture достатній
для старту; CRDT не додавати до появи конкретного спільного редагування.

Зберігати UTC, zone ID і локальну дату події; день сну може переходити через північ.
Europe/Warsaw — початковий часовий пояс, але зміна зони і DST тестуються.
Device clock може бути неправильним; sync ordering не спирається лише на нього.

Delete — версійована tombstone; stale device не може відновити запис. Після закінчення
retention tombstones неприсутній пристрій потребує re-pair/full resync, а не naive merge.
Після відновлення старого backup підвищувати sync epoch, блокувати автоматичне повернення
видалених записів і явно узгоджувати replay. Revocation не стирає offline copy миттєво.

## Голос і великі вкладення

Аудіо зберігається як окремий encrypted blob із content hash та зв’язком із записом.
Chunk/resume, квота, відміна та checksum перед підтвердженням. Лише після durable Mac
receipt можна запропонувати прибрати телефонну копію; не видаляти її завчасно.

## Критерії M2

На реальному/допустимому тестовому Android: створення offline → перезапуск → sync →
повтор пакета → конфлікт → delete → reconnect старого клієнта → оновлення PWA без втрати outbox.
Усі ці сценарії проходять на synthetic data до реального vault.
