# M8E-H01/H02 — AWAITING_REVIEW

Base R: `16868ac34f50651b4c04465f6de0921c5f631ce3` (local main and live origin/main verified equal before
work). Implementation C2: `e0f56b79f305b5bf937487e73dc3f3222b2ec7c8`, a direct child of R. Prior UX C1 was
`8d3c528eb3364f01ee60b42c033d1bfe22ef4149`. Same M8E only; no new milestone.

H01 separates successful missing/non-ChatGPT account results (`EXISTING_CHATGPT_AUTH_REQUIRED`) from process,
transport, timeout, protocol, and RPC infrastructure failures (`PRIVATE_PROVIDER_ROUTE_UNAVAILABLE`). A missing or
unverifiable required model/profile returns `PRIVATE_PROVIDER_PROFILE_UNVERIFIED`; a verified model without its
required effort returns `PROVIDER_EFFORT_UNSUPPORTED`. Local fake-app-server tests cover account/read and model/list
RPC errors, process exits, malformed protocol, timeouts, missing auth/model, malformed profile, and absent effort.
Raw RPC text is dropped and readiness starts no thread/turn/inference.

H02 now uses an explicit displayable-code allowlist. Unknown uppercase and secret-like synthetic codes collapse to
`LOCAL_SERVICE_UNAVAILABLE` and generic Ukrainian copy; the unknown string is never rendered.

Exact-C2 verification: full Python825, web53/build, exact package and Chromium21, schemas, docs/context, and privacy
checks PASS. Provider calls0; non-loopback requests0. See `reports/M8E_H01_H02_FIX_REPORT.md`.

The accepted C4 owner pilot is recorded active at its prior checkpoint but was not inspected, modified, or upgraded
in this goal. C2 is `NOT_INSTALLED_AWAITING_REVIEW`. External settings remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`;
human UA ASR remains `PARTIAL_OWNER_PILOT / OPEN`; phone OFF / `NEEDS_TRANSPORT_GATE`; clinical and Health OFF.

Delivery: C2 → exact-C2 checks → evidence-only R → privacy/public-tree scan → normal fast-forward push → verify
origin/main equals R → stop for independent review. Do not install into the owner pilot or start another milestone.
