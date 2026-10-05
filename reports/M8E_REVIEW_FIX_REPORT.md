# M8E independent review fixes — AWAITING_REVIEW

Base and verified `origin/main` at start: `7a9f2c9839dfa9265780b75f59874fe9ab73178f`.
Independent verdict: M8E `FIX_REQUIRED`, restricted to R01/N01/N02.

Forward implementation history: C2 `5d50a724932b6f51f4cf0be6074c0c2c42150299` fixes pinned Deep goal
semantics, primary unlock copy, and the top Roadmap summary; C3 `6c2a828786757ca28b5427ac986615d4f50d09cf`
completes the unlock-screen description; C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` updates a browser-test
locator only. R2 is the evidence-only successor of C4; its SHA and verified `origin/main` are returned externally
to avoid self-hashing.

## M8E-R01 — resolved in the candidate

`LocalConsent.scope()` reads goal content from the existing Deep conversation's pinned
`goal_binding.id + revision`. It separately checks current goal lifecycle. An ACTIVE revision edit no longer
invalidates/rebinds an older conversation or changes its scope hash, goal text, context, Working Map, closures,
or source bindings. New Deep conversations still bind the current ACTIVE revision. A PAUSED/COMPLETED current
goal fails closed with `GOAL_NOT_ACTIVE` before message persistence or provider execution.

Deterministic ORIGINAL SYNTHETIC regressions cover revision-1 continuation after ACTIVE edit→rev2,
restart/reload with rev1 text/scope/map, a new rev2 conversation with a separate goal/scope/map, and PAUSED
fail-closed. The revision-1 and revision-2 request payloads are checked for cross-use.

## M8E-N01/N02 — resolved

Unlock/loading and descriptive copy use Personal Companion wording; the security/unlock mechanism is unchanged.
The Roadmap top summary now says M8D externally ACCEPTED and M8E AWAITING_REVIEW. Historical milestone sections
and evidence are preserved.

## Validation

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` on C2 backend/tests | exit 0, 802 passed, 1 Starlette deprecation warning |
| `npm --prefix apps/web test` on C2/C3 UI | exit 0, 51 passed |
| `PC_BUILD_COMMIT=6c2a828786757ca28b5427ac986615d4f50d09cf npm --prefix apps/web run build` | exit 0 |
| `.venv/bin/python -m pytest -q tests/test_m1_browser.py` on C4 | exit 0, 1 passed |
| `.venv/bin/python -m pytest -q tests/test_m8d_private.py -k 'pinned_deep_revision or pinned_deep_fails_closed'` | exit 0, 2 passed |
| Impeccable detector for `apps/web/src/main.tsx` | no findings |
| Documentation check / ChatGPT context snapshot | PASS |
| `scripts/check_privacy.py --include-generated` | staged R2, exit 0; scans worktree text and all local Git objects, including staged R2; [JSON result](evidence/M8E_REVIEW_FIXES/PRIVACY.json) |

Environment: Darwin/arm64, Python 3.13.2, Node 26.8.2/npm 11.19.1, existing dependencies only. No release
package, tag, deployment, live provider call, native evaluation, or system integration. The real owner vault,
content and account settings were not inspected. Historical M8D native 4/4 evidence is untouched; no attempt
was added or repeated.

Owner-history correction remains: the first real private AI/manual voice test preceded independent external
account-setting verification. `TRAINING_CONTROL_CONFIRMATION` and `CODEX_ENVIRONMENTS_CONFIRMATION` remain
`NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; no account inspection or retroactive training-off claim is made.
HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`; phone transport remains `NOT_ACTIVATED / NEEDS_TRANSPORT_GATE`.
Clinical=0, all five specialist modules OFF, Health OFF. CI is NOT_RUN/no configured workflow.

M8E remains AWAITING_REVIEW. STOP for independent architect review of exact C/R2.
