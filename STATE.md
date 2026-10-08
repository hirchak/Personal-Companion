---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-10-08
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
actual_remote_default_branch: main
review_branch: null
historical_review_branch: review/m0-bootstrap
baseline_sha: cfd496119e07689e389691bb0644624f30a939cb
current_goal_base_sha: ed7ec39d904a6319f4f0911c042e04598422a94a
implementation_sha: 4124851adc08858e22e99b3adc6c70d5843c2b6b
accepted_product_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
accepted_review_sha: 519bac8f77965ae7165ff536391dd75f19af284b
report_path: reports/M8E_OWNER_LOCAL_REPAIR_REPORT.md
last_reviewed_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
current_milestone: M8E
current_goal: M8E_OWNER_LOCAL_REPAIR
current_goal_path: prompts/M8E_OWNER_LOCAL_REPAIR.md
current_contract_path: docs/M8E_CONTRACT.md
implementation_status: AWAITING_REVIEW
review_status: AWAITING_REVIEW
accepted_product_status: ACCEPTED
owner_pilot_activation_status: ACTIVE_OWNER_AUTHORIZED_C6
owner_pilot_activation_last_checked: 2026-10-08_FINAL_C6_RUNNING
owner_pilot_hotfix_install_status: C6_INSTALLED_OWNER_AUTHORIZED
next_authorized_milestone: null
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

# M8E owner local repair — AWAITING_REVIEW

Base R4 `ed7ec39d904a6319f4f0911c042e04598422a94a`; source-profile compatibility implementation
`4124851adc08858e22e99b3adc6c70d5843c2b6b`. Original product C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`
and H02 remain externally ACCEPTED. No independent acceptance is asserted for this candidate.

Owner explicitly authorizes the existing-pilot repair/upgrade/restart and diagnosis of the last manual test.
Only its sanitized state/error metadata was read: FAILED / PROVIDER_RPC_FAILED. No message/response/audio content
was inspected. SDK credentials remain SDK-only; no extraction, account setting, agent AI send or microphone action.

The known previous voice profile is accepted as a source only; target/profile/file integrity remain strict.
C5 passed exact Python853/web53/Chromium21 and protected preflight/backup/upgrade; root/schema/counts preserved.
The single authorized live readiness timed out in workspace-routing discovery. Anonymous transport probes
proved IPv6-first DNS and unavailable IPv6 TCP, with IPv4 TCP working. Final C6 pins the same fixed host/port
to IPv4; its anonymous helper CONNECT now passes. Final exact-C6 Python860/web53/build/Chromium21/privacy PASS; protected backup/upgrade and metadata-only
root/schema/count preservation PASS. Exact C6 is running at http://127.0.0.1:8765; static build/mode verified,
local page opened. Post-fix SDK readiness is pending owner approval, actual inference remains owner-manual; see
`reports/M8E_OWNER_LOCAL_REPAIR_REPORT.md`.

Automatic approval initially rejected live readiness. The owner then explicitly authorized one account/read
refresh=false + model/list probe: account/read routing timeout, model/list PASS, no thread/turn/inference.
That permission is consumed; one post-fix control probe has been requested and is pending approval.
An unrelated new untracked prompt is preserved and excluded from this repair. The diagnostic teardown API typo was cleaned
up by terminating only verified owned child processes and deleting only their ephemeral state.

External controls remain NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER; phone OFF / NEEDS_TRANSPORT_GATE; clinical/Health
OFF; HUMAN_UA_ASR PARTIAL_OWNER_PILOT / OPEN. No new milestone, deploy, tag, GitHub Release or auth/PAYG/fallback.
