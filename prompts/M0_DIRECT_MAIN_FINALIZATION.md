# M0 — direct-main workflow normalization

Owner decision dated 2026-09-30 establishes normal fast-forward development pushes to the
public repository's `main` for every explicitly issued `/goal`, after its scoped local
checks. Permission is standing until the owner revokes it. Do not ask again before routine
main publication when this gate is met.

This owner decision supersedes the original M0 bootstrap prompt's no-push ceiling only for
this M0 finalization's verified C3/R4 publication to `main`; its other privacy, provider,
deployment, release and no-M1 boundaries remain in force.

Scope: normalize M0 configuration, validation, development instructions and evidence for
direct-main publishing. Preserve all published history. Test `push_main` independently
from `merge_main`, deployment, provider/billing and real-user-data permissions. Retain the
existing review branch as historical; review-branch workflow is optional for a future goal.
Increment the project metadata schema only as needed to represent `push_main` explicitly,
preserving canonical identity, authority and snapshot-policy values.

For this goal, finish C3/R4, verify documentation/configuration and synthetic tooling tests,
test raw-research file exclusion, regenerate/hash-check canonical snapshots, scan staged
files and all local Git objects, then use a normal fast-forward push to `main`. Verify the
exact remote SHA and actual default branch. No force push or history rewrite.

Do not implement M1, open/import private vault data, read/publish raw R01/R02/R03 sources,
call providers, spend, merge, release, tag, deploy or activate clinical content. After
publication, architect review is pending; a new explicit owner `/goal` is required for M1.
