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
implementation_sha: d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60
report_path: reports/M0_BOOTSTRAP_REPORT.md
last_reviewed_sha: 18fefa8dd037fae1982dcc34a64f34325c10830c
current_milestone: M0
current_goal: bootstrap_specification
current_goal_path: prompts/M0_BOOTSTRAP.md
current_contract_path: docs/M1_CONTRACT.md
implementation_status: AWAITING_REVIEW
review_status: AWAITING_REVIEW
next_authorized_milestone: null
research_status: NOT_STARTED
clinical_protocols_enabled: false
real_user_data_allowed_in_development: false
push_authorized: true
merge_main_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# Поточний стан — M0 corrective AWAITING_REVIEW

Canonical `.gitignore` і `.project/context_map.json` відновлено з owner-provided ZIP;
SHA зафіксовані в report та evidence. `.project/project.json` має оригінальну schema,
authority/snapshot_policy та canonical values; застосовані тільки owner-authorized
repo/default/review/permissions.

GitHub connector підтвердив public repo і configured default `main`. Explicit normal
push дозволений тільки в `review/m0-bootstrap`; merge/deploy/provider/real-data OFF.
C2 `d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60`; R2 — evidence-only commit після C2.
M1/app NOT_STARTED та не дозволені окремою goal; протоколи DISABLED.

Check/evidence звіт: `reports/M0_BOOTSTRAP_REPORT.md` і `reports/evidence/M0/`.
Після R2 виконати лише нормальний push дозволеної гілки та перевірити remote ref;
CI не запускали. Потім архітектор повторно розглядає виправлення.
