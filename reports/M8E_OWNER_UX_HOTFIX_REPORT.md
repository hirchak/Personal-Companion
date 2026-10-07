# M8E owner UX hotfix — implementation evidence

**Status:** AWAITING_REVIEW

**Base:** `8459c5ecceb19447967c9aa10f20ecc5a0cef113`

**Implementation C:** `8d3c528eb3364f01ee60b42c033d1bfe22ef4149`

**Prior accepted product:** C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` / R2 `519bac8f77965ae7165ff536391dd75f19af284b`
**Evidence commit:** This report is contained in the evidence-only R commit. Its exact SHA is available as the containing Git commit and is reported in the final delivery; it is not embedded here to avoid a self-hash cycle.

The candidate implements a compact AI toggle that switches OFF and ON with one tap after valid durable consent. New or revoked consent uses one concise sheet and one acceptance button. Consent acceptance no longer enables local voice, and startup does not enable an inactive AI runtime. External ChatGPT/Codex setting reminders are nonblocking and appear only under More → AI & Privacy.

The microphone works independently of AI consent and AI state. An authenticated local session can prepare the pinned whisper.cpp engine; missing or unverified assets do not block recording or persistence. A completed recording is transcribed locally when available, becomes an editable draft, and is never automatically sent. AI disable/revoke preserves local voice; session lock/expiry suspends it. Activation readiness reads only existing account type and supported model/effort catalog, discards account details, and starts no thread, turn, prompt, or inference. UI failures show mapped Ukrainian recovery text and a sanitized stable code.

Exact provider payload, source freshness, Deep scope, journal default OFF, explicit journal expansion, model ceilings, no fallback/PAYG, clinical/Health OFF, and phone transport OFF are preserved. The accepted C4 owner pilot was not opened, inspected, modified, or upgraded during this goal. No real vault, owner conversation, transcript, audio, account setting, or credential was accessed.

## Exact-C checks

Environment: macOS/Darwin arm64, Python 3.13 virtual environment, existing Node/npm dependencies, Chromium; all user-content cases used `ORIGINAL_SYNTHETIC` fixtures and disposable PRIVATE_LOCAL roots.

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | PASS — 810 passed, 1 upstream Starlette deprecation warning, exit 0 |
| `npm test` | PASS — 53 passed, exit 0 |
| `npm run build` | PASS — TypeScript check and Vite production build, exit 0 |
| `.venv/bin/python -m apps.core.release prepare --output generated/releases/M8D-8d3c528eb3364f01ee60b42c033d1bfe22ef4149` | PASS — exact C package, exit 0; manifest hash `37284370428872e7a8e05fc7fa7aa9ffa962a1a1860b540fdbd76c9e0362d316` |
| `PYTHONPATH=. .venv/bin/python scripts/verify_m8e_browser.py --package generated/releases/M8D-8d3c528eb3364f01ee60b42c033d1bfe22ef4149` | PASS — exact packaged C in Chromium; 20 UX/security checks, 0 page errors, 0 non-loopback requests, exit 0 |
| `node scripts/verify_m7a_schemas.mjs` | PASS — 7 checks, exit 0 |
| `node scripts/verify_m7c_schemas.mjs` | PASS — 12 checks, exit 0 |
| `node scripts/verify_m7d_schemas.mjs` | PASS — 14 checks, exit 0 |
| `.venv/bin/python scripts/m7_admission.py` | PASS — structural status; 27 findings remain unresolved, active clinical protocols 0, exit 0 |
| `PYTHONPATH=. .venv/bin/python scripts/qualify_m7d_skills.py --check` | PASS — 5 candidate/off qualification packages, exit 0 |
| `.venv/bin/python scripts/check_docs.py` | PASS — 834 files, 286 JSON files, 369 local links, exit 0 |
| `.venv/bin/python scripts/build_chatgpt_context.py` | PASS — four Markdown snapshots and project instructions; source commit C, exit 0 |
| `.venv/bin/python scripts/check_privacy.py --include-generated` | PASS — no findings across the worktree, generated snapshots, built UI, tracked paths, and all local Git objects, exit 0 |
| `/Users/hirchak/.agents/skills/impeccable/scripts/impeccable detect --json apps/web/src/PrivatePilotControls.tsx apps/web/src/ComposerVoice.tsx apps/web/src/ConversationHome.tsx apps/web/src/private-pilot-errors.ts` | PASS — no findings, exit 0 |
| `python3 -m py_compile apps/core/local_private_ai.py apps/core/codex_conversation_provider.py apps/core/local_private_provider.py apps/core/local_consent.py apps/core/api.py scripts/verify_m8e_browser.py` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |

The exact-package browser report states `live_provider_calls: 0`, `real_vault_inspected: false`, `physical_phone: NOT_RUN_NEEDS_TRANSPORT_GATE`, and `human_ua: PARTIAL_OWNER_PILOT_OPEN`. Browser transcription used synthetic TTS with local Whisper. CI remains NOT_CONFIGURED/NOT_RUN. The privacy scan is heuristic and does not prove absence of personal data or runtime egress. The exact evidence-only R SHA and final normal fast-forward / `origin/main == R` verification are reported by the final delivery; this report does not embed its containing commit hash.

## Preserved owner boundaries

`TRAINING_CONTROL_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER` and
`CODEX_ENVIRONMENTS_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`. Phone transport remains
`OFF / NEEDS_TRANSPORT_GATE`; clinical and Health remain OFF. No installation into the existing pilot, account
change, provider inference, message, conversation creation, owner microphone capture, deploy, tag, release, or
new milestone is part of this candidate.
