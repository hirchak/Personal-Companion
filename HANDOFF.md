# M8E-H01 final account-shape correction — AWAITING_REVIEW

Base R3: `df1c151eeca5920d3e2721726fd0ae77f0d09beb` (local main and live origin/main verified equal before work).
C4: `c95e49ff92b5e4d42b877e91e5e9464258dc7588`. Same M8E only; no new milestone.

Account/read semantics now match the owner requirement. A well-formed `account: null` or valid non-ChatGPT string
account type is auth-required. An empty account object or missing/empty/whitespace-only/non-string account type
is protocol/route failure. Synthetic regressions cover each malformed shape. H02 remains ACCEPTED; explicit
error-code allowlisting and all previously accepted M8E behavior are unchanged.

Exact-C4 verification: full Python846, web53/build, exact package, Chromium21, docs/context and privacy PASS.
Live inference calls0; non-loopback requests0. See `reports/M8E_H01_ACCOUNT_SHAPE_REPORT.md`.

The accepted C4 owner pilot was not inspected or changed; candidate installation remains
`NOT_INSTALLED_AWAITING_REVIEW`. External settings are `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; phone OFF /
`NEEDS_TRANSPORT_GATE`; clinical and Health OFF.

Delivery: C4 → exact-C4 checks → evidence-only R4 → privacy scan → normal fast-forward push → verify
origin/main equals R4 → STOP for independent review. Do not install into the owner pilot or start another milestone.
