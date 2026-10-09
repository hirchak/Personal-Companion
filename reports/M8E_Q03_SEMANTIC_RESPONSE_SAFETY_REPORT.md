# M8E-Q03 — semantic response-release safety

Final implementation C2: `a66008cf1b16b131f8c164d7cb9082e861966806` (runtime identical to C1 `e220c3016b3753b4326e76358165740d739f8aeb`). Base: `5130e92e1454b95b5066ddb4fcd0b2212e142338`.
Actual executor GPT-6.1 Sol/High confirmed from own-turn metadata. Delivery status AWAITING_REVIEW; exact-C2 verification complete;
independent status remains AWAITING_REVIEW, never self-ACCEPT. [Contract](../docs/M8E_Q03_CONTRACT.md),
[ADR-017](../docs/adr/ADR-017-M8E-Q03-RESPONSE-RELEASE.md).

## Answer to the central question

New controller-generated responses are withheld from public API/UI until the complete final object passes
structural/source checks and a bounded release decision, then final freshness/cancellation checks and one
atomic commit. Known bad fixtures are blocked. Ordinary authored Free/Deep examples remain usable.
**General semantic safety is OPEN**: finite contextual rules are not a universal classifier, and no
qualified clinical content review or real-model quality evaluation occurred. Explicit detected current-danger
generated responses remain closed pending a separately authorized qualified route; no approved crisis service
or emergency monitoring capability is claimed.

## Verified baseline and channels

[Baseline](evidence/M8E_Q03/BASELINE.json) binds actual remote/base and reviewed diff. An exact old-SHA
synthetic execution [reproduced](evidence/M8E_Q03/BASELINE_LEAK.json) partial visibility in both get/poll and
page while state was RUNNING and before any assistant DB row existed; the role-claim fixture was subsequently
committed by the old structural controller. Evidence contains booleans/hashes only. The old UI directly
rendered partial_candidate. Historical Q01/Q02 artifacts are retained, not retroactively rewritten.

Current flow passes no provider delta consumer. get/page/action projections always return partial_candidate:null
and hide non-final candidate objects. UI independently suppresses pending assistant/goal/closure content even
when a synthetic network test injects fake wire fields. Delayed previous-conversation loads and stale polling
are guarded. The existing public job states remain; additive release_status reports forming/checking/released.
No SSE or alternate conversation endpoint bypass was found: paginated history reads committed message rows,
Deep maps and closures derive from transactional committed candidates. Local ASR drafts remain editable user
input and are outside assistant-response release; their independent behavior is preserved.

## Decision and persistence

Serialize the validated candidate once, including all assistant, goal, closure and map text. Review input is
immutable. Typed backend-owned decisions bind request hash, complete candidate hash, request metadata hash
(context/goal/source/skills/model/profile), attempt, config/assessor/controller implementation hashes, issuance
and expiry. No model safe=true field, request body or user JSON can supply a decision.

Missing/invalid/failed/timed-out/stale decisions deny release. Detected current personal danger remains closed
even for an injected ALLOW adapter. Source/profile/consent/policy reassembly and cancellation checks repeat at
publication. Controller/private-gate locks order commit against cancel/revocation. Message, map and receipt
are one transaction; a late map validation error rolls all of them back. A late worker/decision cannot win a
new attempt. Explicit retry retains request/context/profile/policy and obtains a new attempt-bound decision.
No text repair, automatic retry, fallback, second model call or model authority promotion.

Restart fails pending work; restore validates new receipt hashes. Previously completed legacy messages remain
readable without being retrospectively represented as Q03-assessed. Plain hashes are integrity bindings under
the accepted trusted-backend/storage model, not signed protection from an attacker controlling the database.
No schema migration or owner-vault action is introduced.

Unreleased text is not stored in jobs/messages/maps/closures or emitted through public failure metadata.
Unknown SafeError codes and provider exception details collapse to explicit safe classifications. Numeric
usage and bounded known metadata are retained; raw RPC/error strings are discarded. If final persistence and
its error-write both fail, a text-free transient failure notice prevents a chained worker traceback from
printing the candidate. Storage recovery/restart remains necessary; no successful release is fabricated.
Private generation/review memory is unavoidable and is not claimed to be encrypted/zero-retention.

## Bounded policy and limitations

[Versioned policy](../apps/core/policies/conversation_release.json) ships under the existing apps/core resource
prefix; no new package workflow or actual Mac package was created. [Coverage](../research/evals/m8e_q03/coverage.json)
distinguishes KNOWN_COVERED mechanism/bounded samples, OPEN generalization and QUALIFIED_REVIEW_REQUIRED.

| Area | Current protection | Remaining limit |
|---|---|---|
| Role/diagnosis/prescription | Selected direct claims/commands; contextual denial and source quotations | All diagnoses, indirect implication, languages and doses are not classified |
| Stop/refusal/no questions | Explicit tested boundaries, forced exercise/continuation and unreviewed body commands | Indirect preferences, sarcasm and all coercion remain OPEN |
| Guarantee/false belief | Tested guarantees and mind-reading-neighbor endorsement; fiction pair remains allowed | General reassurance loops and belief/motive truth are not resolved |
| Sleep/dream/fiction | Selected invented sleep values and symbolic/fiction pathology assertions | No medical measurement, triage or complete dream interpretation detector |
| Current danger | Tested direct current-personal danger closes generated release | Qualified routing, contacts, indirect danger and miss rates remain OPEN |
| Ambiguous language | Selected minimal neutral clarifications; unresolved risky response requires review | No general intent or risk inference guarantee |
| Ordinary Free/Deep | Listening, correction, useful wording, no question, ordinary sleep and source-bound map tests | Authored fixtures do not prove live-model or human benefit |

This is a compositional finite lexical/attribution/intent policy, not a blacklist presented as universal semantic
judgment. It can overblock unquoted educational/scheduling phrasing and miss untested paraphrases, obfuscation,
languages or implicit risk. Literal verified USER_STATED text is kept as source, not promoted to an assistant
assertion. Exact supplied quotes and formal address are preserved; text is never rewritten after review.

## Test evidence

[Characterization](evidence/M8E_Q03/CHARACTERIZATION.json) runs actual controller fixtures:24 prior bad cases
(14 Q01+10 Q02) excluded and32 authored normal samples released. Reports contain identifiers/hashes/statuses,
not candidate prose. ACCEPT/REJECT/REQUIRE_REVIEW observations are algorithm outputs against authored expected
boundaries, not qualified clinical gold. Technical exclusion and semantic label agreement remain separate.

Tests additionally cover all prose sinks, malformed output, absent/wrong/stale/timed-out decisions, changed
request/response/metadata/attempt/policy, source/model/consent/revocation, cancel/retry/restart, quote/negation/
fiction-to-real variants, map rollback, storage-error logging, and DOM/API visibility while review is held.
Built desktop/mobile tests inject fake partial/auxiliary fields, reload failed/cancelled jobs, retry explicitly,
and release delayed history after selecting a different conversation. Original user messages remain stored.

Focused tests passed during implementation. Two harness failures were corrected: an imported unlock helper
used the old browser port; a cancel test released its review barrier before the HTTP cancellation acknowledgement.
No unsafe text was treated as an acceptable outcome. [Full exact-C2 evidence](evidence/M8E_Q03/CHECKS.json):1021 Python tests PASS in467.89s,53 web tests,
TypeScript/Vite build, admission/qualification/docs/snapshot/privacy PASS. One existing Starlette deprecation
warning remains. Built browser tests are included in the full Python result; desktop/mobile screenshots
were inspected and mechanical UI detector returned no findings. First-run infrastructure errors, if any, are recorded separately from exact reruns, not hidden.

## Scope and next gates

All five qualification records remain OFF/runtime_instructions:null; active skill instructions, source/Deep
bindings, consent, journal/memory/Health/practice authority, provider profiles and account controls remain.
No live SDK/inference/account calls, private vault/audio/owner pilot, Health/phone activation, installations,
Mac packaging, deploy/tag/release or next milestone. Existing human UA ASR and external-account verification
states are unchanged and not newly rechecked. No therapeutic efficacy or independent content ACCEPT claim.

Required later decisions: qualified Ukrainian content/label review; reviewed crisis resources and applicability;
source/right clearance where needed; independently evaluated false positives/negatives; a separately authorized
assessor route/budget if needed; explicit exact-version pilot upgrade or activation. Q01 unused calls do not
transfer. Impeccable's existing product-record schema drift was observed and left outside this scope.

## Publication

Exact base → implementation C → exact-C checks → evidence-only R → staged privacy/public-source review →
normalFF main → actual remote equality → STOP AWAITING_REVIEW. R contains state/handoff/report/devlog and
sanitized evidence only. Final R/origin SHA is reported after creation, avoiding a recursive self-hash.
CI NOT_CHECKED unless separately verified.


## First full-run findings and forward correction

[First-run evidence](evidence/M8E_Q03/FIRST_RUN_FINDINGS.json): C1 full suite returned exit1 with1019 passed/2 failed.
One synthetic ASR process termination produced PermissionError and passed on immediate same-C1 recheck;
ASR code was not changed. The other test incorrectly required Q01 baseline/controller equivalence after Q03.
C2 changes only that assertion to require Q01_BASELINE_GENERATION_CHANGED. The historical evaluator, frozen
inputs, permissions and ledgers remain unchanged. Final full exact-C2 verification returned exit0:1021 passed,467.89s,one existing upstream warning.

Final technical outcome is AWAITING_REVIEW. Evidence-only R and remote equality are verified after commit;
its own hash is not embedded recursively in this report. Full scope completion does not close qualified
content or general semantic-safety gates; those remain explicitly OPEN/review-required as specified.
