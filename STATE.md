---
state_schema_version: 1
packet_version: 0.1.0
updated_at: 2026-10-10
project_slug: personal-companion
repo_url: https://github.com/hirchak/Personal-Companion.git
repo_visibility: public
default_branch: main
actual_remote_default_branch: main
review_branch: null
historical_review_branch: review/m0-bootstrap
baseline_sha: cfd496119e07689e389691bb0644624f30a939cb
current_goal_base_sha: f32038f62e276400c41fb21c76ce753316b7aaa7
implementation_sha: null
accepted_product_sha: 55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d
accepted_review_sha: 519bac8f77965ae7165ff536391dd75f19af284b
report_path: reports/M8F_MACOS_APP_REPORT.md
last_reviewed_sha: 8b0a06442e339a553072ca32851b2f5dea6fb73c
current_milestone: M8F
current_goal: M8F_STANDALONE_MACOS_APP_SAFE_UPDATES
current_goal_path: prompts/M8F_MACOS_APP_INSTALLER_UPDATES.md
current_contract_path: docs/M8F_CONTRACT.md
implementation_status: IN_PROGRESS
review_status: IN_PROGRESS
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

# M8F — IN_PROGRESS

Owner issued standalone macOS + safe updates goal; actual base/origin f32038f verified.
Actual executor GPT-6.1 Sol/High; Plan Mode OFF. Push main authorized; merge/deploy/provider/data not authorized.
Native AppKit/WKWebView, real relocated Python13, runtime-only dependencies, UI, Whisper and Sparkle2.10.0
are implemented. Owner separately authorized project-local Sparkle download/integration. Local C8 app/DMG
and packaged core/ASR/isolation/backup/restore passed; final corrected C9 artifacts/checks pending.
Actual hardware Mac14,15 / Apple M2 / 8GB / macOS27, not the requested16GB reference.

C8 microphone test unexpectedly captured possible non-synthetic audio locally and ASR ran; no provider
inference/upload/Git content. Candidate stopped, root excluded and deleted without reading file content
after exact scoped owner authorization. Incident is retained in final report, not relabeled synthetic.
C9 LOCAL_TEST denies physical microphone at both native and page layers; an explicit menu uses only
authored bundled synthetic PCM. Existing owner pilot/vault was never inspected or modified.

Next: final clean exact-C build, original-synthetic native Finder/GUI one-button A→B/signature negatives,
full checks, independent UI review, evidence-only R/privacy scan/normalFF main/remote equality.
Clinical/five specialists/Health/phone/cloud/telemetry OFF; AI unavailable/defaultOFF. No next milestone.
