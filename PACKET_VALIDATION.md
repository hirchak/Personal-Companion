# Перевірка стартового документаційного пакета v0.1.0

Історичний звіт пакування, не поточний M0 evidence. У розпакованому пакеті три hidden
файли були відсутні; actual M0 результати — у [M0 report](reports/M0_BOOTSTRAP_REPORT.md).

Дата специфікації: 2026-09-30. Об’єкт: документи та допоміжні скрипти, не застосунок.

## Виконано

- `python3 scripts/check_docs.py --json`: PASS. Структура, JSON, локальні Markdown-links,
  fenced blocks, узгодженість STATE/config, source IDs, research briefs і довжина /goal.
- `python3 -m unittest discover -s tests -v`: PASS, 11 тестів tooling.
- `python3 scripts/build_chatgpt_context.py`: PASS. Чотири Markdown snapshots,
  project instructions і manifest із SHA-256 канонічних джерел.
- Перевірено, що PRIVATE-додаток не входить до repo або стандартного ChatGPT-пакета;
  приватні цитати не використані як public fixtures.
- Архіви перевірені на цілісність; source/output hashes звірені при пакуванні.

## Межі перевірки

Heuristic secret-pattern scan — лише допоміжна перевірка, не гарантія відсутності
будь-яких чутливих даних. Git history scan не виконувався: GitHub repo/історії ще немає.
Технічні зовнішні джерела перевірялися для конкретних передумов; повного clinical
research не виконано. Недоступні clinical seed pages чесно позначені в SOURCES.md.

## НЕ виконано

M0 development goal, реалізація застосунку, live provider calls, runtime sandbox test,
Android/Mac install, wearable/ASR benchmark, справжній private-vault security audit,
клінічний content review, GitHub push або Vercel deploy.

Статус застосунку: NOT_STARTED. Протоколи: DISABLED. Repo URL: NOT_SET.
Наведені PASS не можна використовувати як твердження «застосунок готовий».
