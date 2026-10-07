---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-10-07
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
actual_remote_default_branch: main
review_branch: null
historical_review_branch: review/m0-bootstrap
baseline_sha: cfd496119e07689e389691bb0644624f30a939cb
current_goal_base_sha: 8459c5ecceb19447967c9aa10f20ecc5a0cef113
implementation_sha: 8d3c528eb3364f01ee60b42c033d1bfe22ef4149
diagnostic_candidate_sha: 1edacfb4749205cf1ccdc22f0601b5dac43a0d27
accepted_product_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
accepted_review_sha: 519bac8f77965ae7165ff536391dd75f19af284b
diagnostic_candidate_status: ACCEPTED
report_path: reports/M8E_OWNER_UX_HOTFIX_REPORT.md
last_reviewed_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
current_milestone: M8E
current_goal: M8E_OWNER_UX_HOTFIX
current_goal_path: prompts/M8E_OWNER_UX_HOTFIX.md
current_contract_path: docs/M8E_CONTRACT.md
implementation_status: AWAITING_REVIEW
review_status: AWAITING_REVIEW
accepted_product_status: ACCEPTED
owner_pilot_activation_status: ACTIVE
owner_pilot_activation_last_checked: 2026-10-06_C4_CHECKPOINT_NOT_RECHECKED_THIS_GOAL
owner_pilot_hotfix_install_status: NOT_INSTALLED_AWAITING_REVIEW
next_authorized_milestone: null
research_status: RECEIVED_EXTERNALLY_PARTIAL_PRIMARY_CHECKS
external_account_controls: NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER
human_ua_asr: PARTIAL_OWNER_PILOT_OPEN
phone_transport: OFF_NEEDS_TRANSPORT_GATE
clinical_protocols_enabled: false
health_enabled: false
real_user_data_allowed_in_development: false
push_review_branch_authorized: false
push_main_authorized: true
merge_main_authorized: false
deployment_authorized: false
paid_or_subscription_calls_authorized: false
---

# M8E owner UX hotfix — AWAITING_REVIEW

M8E C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` / R2
`519bac8f77965ae7165ff536391dd75f19af284b` remains externally ACCEPTED. The current same-milestone UX hotfix
implementation is C `8d3c528eb3364f01ee60b42c033d1bfe22ef4149`, based on `8459c5ecceb19447967c9aa10f20ecc5a0cef113`.
It is AWAITING_REVIEW. The accepted C4 owner pilot was not inspected, modified, upgraded, or rechecked during this
goal; the hotfix has not been installed.

The candidate adds a one-click AI ON/OFF toggle after durable consent, one concise first-use consent action,
nonblocking external-settings reminder under More → AI & Privacy, local microphone/Whisper independent of AI
consent/state, and sanitized activation errors backed by non-inference readiness. Exact payload/source/Deep scope,
journal default OFF, model ceilings, no fallback/PAYG, and all clinical/Health/phone boundaries remain unchanged.

Exact-C checks: full Python `810 passed`; web `53 passed` and build PASS; exact M8D-format package prepared from C
with manifest `37284370428872e7a8e05fc7fa7aa9ffa962a1a1860b540fdbd76c9e0362d316`; exact-package Chromium uses
synthetic PRIVATE_LOCAL fixtures, synthetic TTS/local Whisper, 0 live provider calls, 0 non-loopback requests.
Final evidence-only report and current durable context are in `reports/M8E_OWNER_UX_HOTFIX_REPORT.md`.

External account controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; HUMAN_UA_ASR remains
`PARTIAL_OWNER_PILOT / OPEN`; phone transport remains `OFF / NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF.
No real vault content, account settings, provider messages, microphone audio, release, tag, or deploy was accessed.
Next action is independent review of the pushed C/R; installing the candidate requires a later explicit owner goal.
