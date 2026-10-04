# M7D — Deep Session Intelligence

Owner specification: `prompts/M7D_DEEP_SESSION_INTELLIGENCE.md`.
Base `b75e3a4d7176372fef68399c80ddd09b7330d840`; M7C external scoped ACCEPT recorded.
Implementation completion means AWAITING_REVIEW, never self-ACCEPT.

One controller/voice, synthetic only. No private data, clinical activation, health-to-AI,
external embeddings, cloud ASR, auth/billing/PAYG changes, downloads, deploy/release or M8.
M7D ledger has a goal-wide ceiling48 including failures/cancel/schema rejection. M7C ledger stays intact.

| ID | Required contract | Verification |
|---|---|---|
| A01 | Durable scoped M7C ACCEPT | reports/M7C_ARCHITECT_REVIEW.md / exact C/R base |
| A02 | Versioned source-bound provenance map | tests/test_m7d_deep.py; schema11 backup |
| A03 | Rejected hypothesis preserved | rejection merge test; no automatic promotion |
| A04 | Goal vs editable session focus | focus/phase/goal pin tests; UI |
| A05 | Bounded later-session map/closure context | snapshot; multi-session synthetic live bundle |
| A06 | Exact selected range/preview on InferenceStart | four range tests; browser preview; metadata |
| A07 | Stale context/map source safe | pre-send and pre/post-provider checks; edit/delete |
| A08 | One controller, no additional agents | controller assembly; tools empty |
| A09 | Actual effort discovery/config binding | installed model/list; pre-turn effort validation |
| A10 | Bounded Luna/Sol hard corpus + review pack |20 original cases;17 planned attempts/model; no LLM judge |
| A11 | Candidates never confer user authority | exact quoted USER_STATED only; explicit confirmation; no downstream writes |
| A12 | Exact map/context closure, goal remains ACTIVE | closure/session test; explicit session close |
| A13 | Non-speech guard before normal transcript | six existing original synthetic PCM cases; uncertain explicit review |
| A14 | Human UA NOT_RUN; cloud NONE | ASR benchmark metadata |
| A15 | Five admission packages CANDIDATE/OFF | qualify_m7d_skills.py --check; runtime denial |
| A16 | Clinical0 / findings27OPEN | canonical admission validator |
| A17 | Relevant regression/build/browser/privacy | exact-C command outcomes in final report |
| A18 | Real private data OFF | permissions; controller synthetic validation; privacy scan |

A01–A18 refer to M7D-A01–M7D-A18. Live quality is reviewed by owner/architect;
structured/schema PASS is engineering evidence only. Model retention/private suitability remains
NOT_VERIFIED (M7C-N02); human voice/hardware are separate gates. No clinical effectiveness scores.

The deterministic controller resolves explicit preset/custom UTC windows with IANA timezone metadata.
Time ranges govern historical sources, maps and prior closures. The current explicit draft is separately
bound and appended to the final receipt even when custom history excludes now. Preview text/goal/source/
session/map hash drift fails; no silent substitution. Legacy no-binding callers create an internal
GOAL_START preview; the M7D UI always sends the selected binding. Source drill-down uses exact revisions.

Map versions are immutable historical records. Read views compute STALE for changed/deleted sources;
CURRENT entries alone may be confirmed. Rejected/irrelevant items remain in merge history; identical
normalized text cannot be regenerated as current. Semantic paraphrase quality remains a human-review
criterion, not a claimed perfect semantic detector. Source-less entries are denied.

Map capacity40, candidate8, snapshot20 items/2 closures/16KB; source receipt max50; provider input48KB;
output24KB; M7D CLI/eval deadline120s (legacy M7C default60 unchanged); one foreground request/conversation. At capacity, explicit IRRELEVANT and source-invalid model items may move to immutable history;
exact-text rejection/irrelevance tombstones stay binding across versions. Remaining capacity exhaustion
pauses for review instead of discarding confirmed/rejected provenance. Snapshot prioritizes rejected
hypotheses and user-confirmed takeaways within its bounded window. Older goal revisions stay pinned; new
sessions require the current ACTIVE revision. Closing a session does not mark the goal completed.
