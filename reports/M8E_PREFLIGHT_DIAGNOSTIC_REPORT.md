# M8E preflight diagnostic — ACCEPTED

## Scope and result

M8E product implementation C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` remains externally accepted. This follow-up diagnoses the previously reported `INVALID_METADATA` from exact-C4 private preflight; it does not start another milestone or authorize activation.

The exact C4 preflight now returns PASS on the existing owner PRIVATE_LOCAL root and on its verified protected pre-upgrade backup snapshot. Both validators reached `COMPLETE`, including `Store.check`. The earlier `INVALID_METADATA` failure did not reproduce, so its original cause is unconfirmed. No application defect or invalid private-data invariant was established, and no upgrade was run.

## Evidence

| Check | Result |
|---|---|
| Base checkout and `origin/main` before this work | `dadfec1a13d1e46fb03ab1c7c3b853b11be666ee` |
| Diagnostic implementation candidate C | `1edacfb4749205cf1ccdc22f0601b5dac43a0d27` |
| Synthetic M8C → accepted M8D C2 lifecycle with fixture conversation/local transcript | PASS; no provider or microphone |
| Exact C4 preflight on synthetic DELETE-journal root | PASS |
| Exact C4 preflight on synthetic WAL root with writer open | PASS |
| Exact C4 preflight on quiescent WAL/SHM copy with no writer/server | PASS |
| Exact C4 preflight on existing owner root | PASS / `COMPLETE`; WAL and SHM present |
| Verified protected backup snapshot | PASS / `COMPLETE`; exact producing M8D C2 provenance checked |
| Existing root main database and WAL file metadata across preflight | Unchanged |
| Existing vault upgrade / application restart / browser launch | NOT_RUN |

The active root was located through installation/release metadata. No private root path, root ID, backup path, receipt, backup hash, row value, or exception message is included here. The exact C4 package implementation was also exercised directly against the root; it returned PASS.

## Diagnostic change

The candidate adds optional fixed-name stage callbacks to the existing private preflight and read-only SQLite inspection path. In diagnostic mode, SQLite open failures map to stable error classes such as `SQLITE_READONLY_WAL_OPEN`; other SQLite failures identify the current allowlisted stage. The normal preflight still performs root identity, schema, integrity, foreign-key, and typed-domain checks and remains fail-closed. Diagnostic output does not include exception text or row content.

The synthetic regressions cover valid schema-11 PRIVATE_LOCAL data, the M8C-to-M8D-style conversation/transcript lifecycle, DELETE and WAL/SHM states, read-only checks, malformed metadata, SQLite integrity failure, foreign-key failure, typed-domain failure, sanitized read-only-open errors, and the rule that failed preflight prevents upgrade.

## Verification

Environment: Python 3.13 virtual environment on the local Mac; all tests used disposable synthetic PRIVATE_LOCAL roots and ephemeral loopback ports.

| Exact-C command | Result |
|---|---|
| `.venv/bin/python -B -m pytest -q tests/test_m1_domain.py` | PASS, exit 0, 50 passed |
| `.venv/bin/python -B -m pytest -q tests/test_m8c_private.py` | PASS, exit 0, 82 passed |
| `.venv/bin/python -B -m pytest -q tests/test_m8d_private.py` | PASS, exit 0, 51 passed |

No live provider calls occurred. No real private content was printed, logged, exported, or retained in evidence. No application data or protected backup was changed. The main database and WAL metadata were unchanged; SQLite may refresh transient WAL shared-memory lock metadata during a read-only open.

## Independent review follow-up — 2026-10-07

The owner reports independent verdict `M8E_PREFLIGHT_DIAGNOSTIC = ACCEPT`, limited to sanitized preflight
observability. The verdict is recorded here as acceptance of diagnostic C `1edacfb4749205cf1ccdc22f0601b5dac43a0d27`
and publication R `d7de88f33db77c6dbb86971fce1d2b4c514e0eb1`. The original `INVALID_METADATA` cause remains
UNCONFIRMED. No claim is made that an application defect or private-data invariant was repaired.

## Current status

The diagnostic candidate is ACCEPTED for its stated observability scope. The original `INVALID_METADATA` cause remains UNCONFIRMED. The accepted product remains M8E/C4; owner-pilot activation is IN_PROGRESS under a separate exact-C4 activation goal. Phone transport stays OFF, clinical and Health stay OFF, external account controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`, and HUMAN_UA_ASR remains `PARTIAL_OWNER_PILOT / OPEN`.

Base SHA is recorded above; implementation C is the diagnostic candidate above. This report is the evidence-only R commit; its own SHA is intentionally not embedded. Push status at report creation: PENDING; the authorized normal fast-forward push and post-push `origin/main` check will be reported in the final handoff. CI: NOT_RUN.
