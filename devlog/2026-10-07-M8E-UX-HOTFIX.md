# 2026-10-07 — M8E owner UX hotfix

- Implemented C `8d3c528eb3364f01ee60b42c033d1bfe22ef4149` from base `8459c5ecceb19447967c9aa10f20ecc5a0cef113`.
- Added one-click AI toggle, one first-use consent action, independent local microphone/Whisper, bounded non-inference readiness, and sanitized activation errors. Exact payload and all existing M8E safety boundaries remain unchanged.
- Exact-C results: Python810, web53/build, package manifest `37284370428872e7a8e05fc7fa7aa9ffa962a1a1860b540fdbd76c9e0362d316`, Chromium synthetic PRIVATE_LOCAL PASS; provider calls0; real vault inspected NO.
- Candidate not installed into the existing owner pilot. Current status AWAITING_REVIEW; evidence/report: `reports/M8E_OWNER_UX_HOTFIX_REPORT.md`.
