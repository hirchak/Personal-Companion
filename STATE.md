---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-09-30
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
review_branch: review/m0-bootstrap
baseline_sha: c891a49f17af190b84e2b4d70e85597bf3e3b1ba
implementation_sha: 18fefa8dd037fae1982dcc34a64f34325c10830c
report_path: reports/M0_BOOTSTRAP_REPORT.md
last_reviewed_sha: 18fefa8dd037fae1982dcc34a64f34325c10830c
current_milestone: M0
current_goal: bootstrap_specification
current_goal_path: prompts/M0_BOOTSTRAP.md
current_contract_path: docs/M1_CONTRACT.md
implementation_status: IN_PROGRESS
review_status: FIX_REQUIRED
next_authorized_milestone: null
research_status: NOT_STARTED
clinical_protocols_enabled: false
real_user_data_allowed_in_development: false
push_authorized: true
merge_main_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# Поточний стан — M0 corrective

Canonical `.gitignore` і `.project/context_map.json` відновлено з owner-provided ZIP;
задані SHA перевірені. `.project/project.json` збережено за оригінальною schema,
authority/snapshot_policy та незмінними metadata; застосовано лише надані актуальні
repo/default/review/permission values.

GitHub connector підтвердив public repository і default `main`. Push дозволено лише
в `review/m0-bootstrap`; merge/deploy/provider/real-data — OFF. Застосунок/M1
NOT_STARTED; M1 unauthorized, клінічні протоколи DISABLED.

Наступне: C2, повторні checks, evidence-only R2 та normal push у review branch.
Нові SHA записати після commits; старі commits лишаються без переписування.
