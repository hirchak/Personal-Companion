---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-10-06
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
actual_remote_default_branch: main
review_branch: null
historical_review_branch: review/m0-bootstrap
baseline_sha: 519bac8f77965ae7165ff536391dd75f19af284b
implementation_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
report_path: reports/M8E_OWNER_ACTIVATION_REPORT.md
last_reviewed_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
current_milestone: M8E
current_goal: M8E_OWNER_ACTIVATION
current_goal_path: prompts/M8E_OWNER_ACTIVATION.md
current_contract_path: docs/M8E_CONTRACT.md
implementation_status: ACCEPTED
review_status: ACCEPTED
owner_pilot_activation_status: BLOCKED_BY_PREFLIGHT_INVALID_METADATA
next_authorized_milestone: null
research_status: RECEIVED_EXTERNALLY_PARTIAL_PRIMARY_CHECKS
clinical_protocols_enabled: false
real_user_data_allowed_in_development: false
push_review_branch_authorized: false
push_main_authorized: true
merge_main_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# M8E externally ACCEPTED — existing-owner pilot activation in progress

The owner reports independent M8E ACCEPT for C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` / review publication
R2 `519bac8f77965ae7165ff536391dd75f19af284b`. The live GitHub `main` branch and clean local starting checkout
were verified at R2; R2 is a direct child of C4. Durable review record: `reports/M8E_ARCHITECT_REVIEW.md`.

The exact local package was built from a clean detached clone at C4 using existing dependencies:
`M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`, manifest
`4c8cfd0d2e827dc3d50c21614c51f076a878207c8792a5cebab7fc69226136b0`. The package manifest binds C4 and all
payload files; no runtime/vault data is in the package.

Owner-authorized activation is limited to the existing PRIVATE_LOCAL pilot. A path-free metadata lookup found
one matching managed install; local paths and root identity remain owner-local. Its accepted M8D C2 manager
created and verified the protected pre-upgrade backup. Exact-C4 `private-preflight` still fails closed with
`INVALID_METADATA`, although the separate receipt check, schema-version check (11), SQLite integrity check and
foreign-key check pass. Upgrade, post-upgrade preservation verification, app startup and browser opening remain
NOT_RUN. Do not bypass the failed application metadata gate or infer that the upgrade completed. No new vault,
provider/account-setting call, conversation, message, microphone recording, phone transport, deploy, tag, or
GitHub Release is authorized.

External controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`;
phone transport remains OFF / `NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF. See the activation report
for the sanitized operation checkpoint and next safe step.
