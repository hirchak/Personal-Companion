# M8E independent review fixes — same milestone only

Base/origin main before these fixes: `7a9f2c9839dfa9265780b75f59874fe9ab73178f`.
Prior M8E C/R: `c571c41e59d9f53d96480d1fc20e2cce60a54936` /
`7a9f2c9839dfa9265780b75f59874fe9ab73178f`. Verdict: `FIX_REQUIRED`.

Fix only M8E-R01, N01 and N02. Keep the existing Conversation-first UX, local consent, ordinary exact-bound Send,
explicit journal/Deep scope, local voice/offline queue, provider/model ceilings, and all privacy/security gates.
Do not inspect the real owner vault or account settings; do not make live provider calls, install/upgrade the real
vault, configure phone transport, deploy, tag, release, force-push, or start another milestone.

M8E-R01: An existing Deep conversation/session is pinned to its original `goal_binding.id + revision`. After an
ACTIVE goal edit revision 1→2, it must continue using revision 1 goal text, scope hash, map, closures and source
bindings. A new Deep conversation uses revision 2. Check current goal lifecycle separately: only non-ACTIVE state
blocks continuation (`GOAL_NOT_ACTIVE`); never require current revision equals the pinned revision. Test edits,
old-session resume/reload, distinct old/new maps/scopes/content, and the non-ACTIVE fail-closed boundary.

M8E-N01: Replace stale unlock/loading copy that calls the app a journal with neutral Personal Companion copy.
Do not change authentication or unlock behavior.

M8E-N02: Correct the top-level Roadmap summary to `M8D = externally ACCEPTED`, `M8E = AWAITING_REVIEW`;
preserve detailed historical milestone sections/evidence.

Delivery: forward implementation C2, exact-C2 full/relevant checks, evidence-only R2, docs/context snapshot,
public-tree/material-rights scan, ordinary fast-forward to main and verify `origin/main == R2`. Stop after publish
for independent architect review; implementation remains `AWAITING_REVIEW`.
