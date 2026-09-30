# Передача контексту — M0 corrective

Дата: 2026-09-30. M0 remediation AWAITING_REVIEW; M1/app NOT_STARTED.
Repository https://github.com/hirchak/Personal-Companion.git — public, configured
default `main`. Owner authorized normal push тільки у `review/m0-bootstrap`;
merge/main/deploy/provider/private-data permission OFF.

Base B: `c891a49f17af190b84e2b4d70e85597bf3e3b1ba`.
Previous reviewed C/R: `18fefa8dd037fae1982dcc34a64f34325c10830c` /
`2d267d17b45d8d873131181f5a52ff2601a6b2a0`.
Corrective C2: `d4e651a43d93c6a5ed6cbd6c780b9f4d0b7c5c60`.
Corrective evidence R2: determine after evidence commit; current Git history is intact.

## Canonical recovery

Owner ZIP restored exact `.gitignore` and `.project/context_map.json`; original project
JSON schema/authority/snapshot-policy preserved with only authorized values changed.
All four canonical ChatGPT snapshot names restored. Source/archive and hash proof:
`reports/evidence/M0/CANONICAL_STARTER_VERIFY.json`. No raw source research was opened or
added; the ZIP had zero DOCX entries.

## Checks and boundaries

Exact C2 docs checks, 24 synthetic tests, snapshot/source hashes and privacy scan pass.
No M1/app changes, live provider calls, real-user data, deploy or main operations.

Next: complete staged scan, create evidence-only R2, normal push to `origin/review/m0-bootstrap`,
then check the ref. CI NOT_RUN. Main/merge/release remain off. A separate owner goal is
required to start M1 after architecture review.
