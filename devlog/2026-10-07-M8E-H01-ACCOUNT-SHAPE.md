# 2026-10-07 — M8E-H01 final account-shape correction

- Base R3 `df1c151eeca5920d3e2721726fd0ae77f0d09beb`; forward C4 `c95e49ff92b5e4d42b877e91e5e9464258dc7588`.
- `account: null` and valid non-ChatGPT string type remain auth-required. Empty account objects and missing/invalid account types now fail as protocol/route.
- Added deterministic local JSON-RPC cases for empty object, missing type, null/non-string/empty/whitespace type. H02 remains accepted; no raw data reaches UI.
- Exact-C4 Python846, web53/build, Chromium21, docs/privacy PASS. Live provider calls0; real vault inspected NO; owner pilot untouched/uninstalled.
- Status AWAITING_REVIEW. Report: `reports/M8E_H01_ACCOUNT_SHAPE_REPORT.md`.
