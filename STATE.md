---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-09-30
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
review_branch: null
historical_review_branch: review/m0-bootstrap
baseline_sha: c891a49f17af190b84e2b4d70e85597bf3e3b1ba
implementation_sha: d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60
report_path: reports/M0_BOOTSTRAP_REPORT.md
last_reviewed_sha: 18fefa8dd037fae1982dcc34a64f34325c10830c
current_milestone: M0
current_goal: m0_direct_main_workflow
current_goal_path: prompts/M0_DIRECT_MAIN_FINALIZATION.md
current_contract_path: docs/M1_CONTRACT.md
implementation_status: IN_PROGRESS
review_status: NOT_REVIEWED
next_authorized_milestone: null
research_status: NOT_STARTED
clinical_protocols_enabled: false
real_user_data_allowed_in_development: false
push_review_branch_authorized: false
push_main_authorized: true
merge_main_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# Поточний стан — M0 direct-main normalization

Owner decision: normal fast-forward pushes у public `main` дозволені після checks для
кожної явно виданої `/goal`. `push_main=true` окреме від `merge_main=false`.
Review branch optional; існуючий `review/m0-bootstrap` з C2/R2/R3 — історичний і збережений.

Теперішня ціль створює лише M0 direct-main workflow, checks і report. M1/app NOT_STARTED
і не дозволені новою окремою goal; протоколи DISABLED. Deploy/provider/billing/private data
також OFF. Force-push/history rewrite заборонені.

Після C3/R4 та privacy scan зробити normal fast-forward push у `origin/main`. GitHub
default branch налаштовано як `main`; після push звірити фактичний ref/default. CI NOT_RUN.
