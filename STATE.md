---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-09-30
project_slug: personal-companion
repo_url: null
review_branch: null
baseline_sha: null
implementation_sha: null
report_path: null
last_reviewed_sha: null
current_milestone: M0
current_goal: bootstrap_specification
current_goal_path: prompts/M0_BOOTSTRAP.md
current_contract_path: null
implementation_status: NOT_STARTED
review_status: NOT_REVIEWED
next_authorized_milestone: null
research_status: NOT_STARTED
clinical_protocols_enabled: false
real_user_data_allowed_in_development: false
push_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# Поточний стан — джерело навігації, не доказ виконання

## Що є

Підготовлено стартовий пакет технічної специфікації, дослідницьких ТЗ і робочого процесу.
Пакет не є реалізацією застосунку. GitHub URL ще не надано. Стан чужих проєктів не переносився.

## Що не зроблено

Немає сервера, PWA, бази користувачки, AI runtime, health integration, інсталятора або
виконаного пілоту. Жоден клінічний протокол не допущений до використання.

## Наступний дозволений крок

Користувач може передати `prompts/M0_BOOTSTRAP.md` у Codex. Це не дозволяє M1 автоматично.
M0 має перевірити середовище, суперечності специфікації та підготувати точний M1 contract.

## Головні невизначеності

Версія macOS/браузера, модель годинника, фактичні права Codex і MiniMax, ліцензія,
GitHub URL і дозволи на push; приватний HTTPS/sync transport перевіряється на M2.
Деталі, не потрібні для M0, не блокують його.

## Правило оновлення

Тримати цей файл коротким. Історія — у devlog/reports. Посилання на джерело доказів
і коміт важливіші за текстовий відсоток готовності. Секрети й приватні дані сюди не потрапляють.
