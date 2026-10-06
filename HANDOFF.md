# M8E owner activation — PREFLIGHT_BLOCKED

M8E is externally ACCEPTED for exact C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` / R2
`519bac8f77965ae7165ff536391dd75f19af284b`. Live GitHub `main` was read-only verified at R2; R2 is a direct
child of C4. The activation task and security boundaries are in `prompts/M8E_OWNER_ACTIVATION.md`.

Exact local package built from a clean detached clone at C4, using only existing Python/Node dependencies:
`M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`, manifest
`4c8cfd0d2e827dc3d50c21614c51f076a878207c8792a5cebab7fc69226136b0`. Its embedded Git commit is C4 and every
payload hash verifies. The temporary clone was removed. The primary working tree was clean after packaging.

No process was listening on loopback port 8765, so no process was stopped. A narrow local install-marker lookup
found one PRIVATE_LOCAL installation; its paths, root identity and backup destination remain local and are not
recorded here. The installed accepted M8D C2 manager created and verified a protected pre-upgrade backup.
Exact-C4 `private-preflight` failed closed with `INVALID_METADATA`, including on the elevated retry. Read-only
metadata checks independently show the root receipt valid, schema 11, SQLite integrity PASS and foreign-key
check PASS. The mismatch remains unresolved; no upgrade, post-upgrade verification, app start or browser open
was attempted. The C4 manager's failed gate must not be bypassed.

Next: resolve the C4 `INVALID_METADATA` failure through an approved path before attempting upgrade. Do not alter
or inspect private records to diagnose it, and do not bypass the accepted preflight. The exact C4 profile and
local whisper assets validate; phone remains OFF, clinical/Health remain OFF, and external OpenAI controls remain
`NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`. No provider call, message, conversation, microphone capture, account
change, deploy, tag, release or next milestone.
