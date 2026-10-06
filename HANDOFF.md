# M8E owner activation — IN_PROGRESS

M8E is externally ACCEPTED for exact C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` / R2
`519bac8f77965ae7165ff536391dd75f19af284b`. Live GitHub `main` was read-only verified at R2; R2 is a direct
child of C4. The activation task and security boundaries are in `prompts/M8E_OWNER_ACTIVATION.md`.

Exact local package built from a clean detached clone at C4, using only existing Python/Node dependencies:
`M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`, manifest
`4c8cfd0d2e827dc3d50c21614c51f076a878207c8792a5cebab7fc69226136b0`. Its embedded Git commit is C4 and every
payload hash verifies. The temporary clone was removed. The primary working tree was clean after packaging.

No process was listening on loopback port 8765, so no process was stopped. The existing pilot's exact local
app/data/backup/whisper root bindings are not present in the accepted sanitized handoff. No root, receipt, or
private content was inspected to discover them. Therefore private preflight, protected backup, upgrade, vault
preservation, ASR validation, startup, and browser opening remain NOT_RUN / UNVERIFIED. Do not guess a default
root or create a new one.

Next: obtain the owner-approved local root resolver/manager entry point (without receiving private path values),
then run only the accepted PRIVATE_LOCAL preflight → protected backup → exact C4 upgrade → content-free
preservation/schema checks → pinned local ASR validation → foreground loopback start. Do not inspect private
records or settings, create/send a conversation/message, record audio, call providers, or enable phone/clinical/
Health routes. External OpenAI controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`. No next milestone.
