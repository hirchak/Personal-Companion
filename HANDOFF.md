# Передача контексту — M0 direct-main finalization

Дата: 2026-09-30. M0 AWAITING_REVIEW; M1/app NOT_STARTED and unauthorized.

Owner decision autorizes normal fast-forward pushes to public `main` after checks for each
explicit `/goal`. `push_main=true` is separate from merge/deploy/provider/private-data gates.
C3 `bc5cf13c3a3569edd0e0c9d9d157889471d0a0bd` has been pushed directly to origin/main.
`gh repo edit --default-branch main` succeeded; GitHub metadata now reports default `main`.
The historical `review/m0-bootstrap` ref remains at R3 `ca0e1fc3af42bcc31e4038a591f7356713718005`.

Base B `c891a49f17af190b84e2b4d70e85597bf3e3b1ba`; R3 ancestry is unchanged. R4 evidence
commit is the remaining M0 step: run staged privacy checks, ensure evidence-only paths, create
R4, then normal-push as a fast-forward to main and verify the final ref. No M1/app,
merge/release/deploy/provider/private-data operations are authorized.
