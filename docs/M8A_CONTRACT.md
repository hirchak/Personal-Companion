# M8A — synthetic release/pilot readiness contract

Authority: [owner specification](../prompts/M8A_RELEASE_PILOT_READINESS.md), [release ADR](adr/ADR-011-M8A-LOCAL-RELEASE.md).
Implementation completion = AWAITING_REVIEW. No live provider/private data/hardware/release/pilot.

| ID | Contract | Evidence |
|---|---|---|
| M8A-A01 | External M7D ACCEPT exact C/R/notes | reports/M7D_ARCHITECT_REVIEW.md |
| M8A-A02 | Exact clean-commit package/schema/hash identity | release.prepare/validate_package; real manifest |
| M8A-A03 | Fresh synthetic install/start/restart; no network dependency | verify_m8a.py actual package/process/Chromium |
| M8A-A04 | App/data separated and preserved on app removal | release tests; lifecycle evidence |
| M8A-A05 | Upgrade preflight + verified consistent backup before migration | release.upgrade; negative tests |
| M8A-A06 | Failed/future/corrupt migration safe | pending marker, transactional failure, schema tests |
| M8A-A07 | Compatible backup restored into fresh rollback roots | actual lifecycle; schema matrix |
| M8A-A08 | Domain integrity/history/tombstone/map/memory preserved | release tests + accepted M3/M7D backup regressions |
| M8A-A09 | Uninstall KEEP DATA; separate exact destructive action | release.uninstall/delete_synthetic_data |
| M8A-A10 | Provider default OFF throughout lifecycle | actual status requests; defaults tests |
| M8A-A11 | Specialists OFF / clinical0 | catalog/admission regressions, package defaults |
| M8A-A12 | Health-to-AI OFF; hardware claims unchanged | defaults; readiness gates |
| M8A-A13 | Valid options comparison + at most one actual question | controller fixture/guard tests; N01 |
| M8A-A14 | Stable FORMAL_VY contract and fail-closed pronoun check | payload/hash/instructions/register tests; N02 |
| M8A-A15 | No real/private/provider traffic | synthetic markers; loopback-only audit/browser routing |
| M8A-A16 | Full tracked-tree/privacy scan; generated outputs ignored | public-tree evidence; check_privacy.py |
| M8A-A17 | Relevant M1–M7D Python/browser/web/build/schema/privacy PASS | exact-C checks |
| M8A-A18 | Exact permission checklist; M8B NOT_STARTED | RECOVERY.md personal-pilot checklist |

N01 uses explicitly labeled quoted options/examples as data. Unlabeled unknown quoted questions still count;
repeated punctuation counts as one cluster. Bounded deterministic convention, not perfect semantic detection.
N02 chooses incumbent formal «ви», immutable FORMAL_VY payload/instructions; rejects unquoted informal pronouns
before commit. Does not infer preference/rewrite user quotes. Verb inflection/naturalness remains a human quality
gate; no perfect Ukrainian grammatical classifier claim. Existing stored history retains original skill hashes.
