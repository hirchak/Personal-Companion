# M8E owner UX hotfix — AWAITING_REVIEW

Current base: `8459c5ecceb19447967c9aa10f20ecc5a0cef113` (local main and live origin/main were verified equal before
work). Implementation C: `8d3c528eb3364f01ee60b42c033d1bfe22ef4149`. M8E product C4/R2 remain externally accepted;
this is a bounded forward correction in the same milestone, not a new milestone.

The hotfix implements an actual AI toggle; existing durable consent resumes with one tap, while first-use/revoked
consent has one concise acceptance sheet. External ChatGPT/Codex control reminders are nonblocking and live only in
More → AI & Privacy. Local microphone and pinned local Whisper work without AI consent and remain available when AI
is OFF. Missing ASR assets leave recording saved and show a mapped recovery state. Activation readiness checks only
the existing account type and model/effort catalog; it starts no thread, turn, or inference and exposes only safe
error codes/messages.

Exact-C verification: `.venv/bin/python -m pytest -q` → 810 passed; `npm test` → 53 passed; `npm run build` PASS;
exact package `generated/releases/M8D-8d3c528eb3364f01ee60b42c033d1bfe22ef4149` verified in Chromium using only
synthetic PRIVATE_LOCAL fixtures, synthetic TTS, and local Whisper. Live provider calls 0; non-loopback requests 0.
See `reports/M8E_OWNER_UX_HOTFIX_REPORT.md` for commands, package manifest hash, and evidence.

The existing C4 owner pilot was not opened, inspected, modified, or upgraded during this goal. Candidate install is
`NOT_INSTALLED_AWAITING_REVIEW`. External settings remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; human UA ASR
remains `PARTIAL_OWNER_PILOT / OPEN`; phone is OFF / `NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF.

Delivery sequence is C → exact-C checks → evidence-only R → privacy/public-tree scan → normal fast-forward push
to main → verify origin/main equals R, then stop for independent review. Do not install the hotfix into the existing
owner pilot or start another milestone under this goal.
