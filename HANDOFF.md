# M8E-H01 final protocol correction — AWAITING_REVIEW

Base R: `9e6119707c6a9d4d13bd8bca92df4bd65eb80edd` (local main and live origin/main verified before work). C3:
`611d2726e9a69d6e195c677a0a6adb3f46d4daf7`. H02 remains ACCEPTED; C3 fixes the last H01 malformed-result issue.
Same M8E only; no new milestone.

Readiness requires response ID correlation, exactly one result/error branch, and expected dictionary result types for
initialize/account/read/model/list. Malformed or absent results become protocol/route failures. A well-formed
account-null or non-ChatGPT result remains `EXISTING_CHATGPT_AUTH_REQUIRED`; missing/unverifiable required model
remains `PRIVATE_PROVIDER_PROFILE_UNVERIFIED`; unsupported required effort remains `PROVIDER_EFFORT_UNSUPPORTED`.
Tests cover null/list/false/missing results across all three RPCs, account/catalog fields, raw-data suppression, and
no thread/turn/inference.

Exact-C3 verification: full Python841; web53/build; exact package and Chromium21 PASS on final official run; schemas,
docs/context, and privacy PASS. Two earlier exact-package browser runs hit assistant-count timeouts at different
explicit sends; a final rerun of the same package passed. No live provider calls or non-loopback requests.
See `reports/M8E_H01_FINAL_PROTOCOL_REPORT.md`.

The accepted C4 owner pilot was not inspected, modified, upgraded, or rechecked; C3 was not installed. External
settings remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone OFF / `NEEDS_TRANSPORT_GATE`; clinical and Health OFF.

Delivery: C3 → exact-C3 checks → evidence-only R3 → privacy/public-tree scan → normal fast-forward push → verify
origin/main equals R3 → STOP for independent review. No owner-pilot installation or new milestone under this goal.
