# Semantic safety review proposal — not implemented

Q01 demonstrated fourteen authored counterexamples accepted by the structural
controller. Q02 retains those exact cases and adds five specialist failure types
in both Free and Deep. Clinical OFF prevents dispatch; it does not make ordinary
assistant prose safe. This proposal neither closes that gap nor changes runtime.

## Proposed separate implementation goal

Before activation, specify a reviewable response-release boundary covering both
streaming display and final persistence. Unreviewed deltas must not bypass whatever
semantic release decision a future design chooses. A failed, missing, timed-out or
stale decision must not release the rejected prose or silently resend it to another
provider. Exact request/context/skill/model hashes must bind the decision. Reuse the
accepted source and consent checks; semantic assessment cannot grant data access.

Represent separate outcomes for normal reflection, an explicit refusal/stop,
uncertain intent needing a minimal clarification, and immediate-danger support.
Do not convert a keyword, symptom score or fictional passage into diagnosis.
Quoted fiction and present personal intent require separate minimal-pair fixtures.
If risk is ambiguous, assess a proportionate clarification and its false-positive
burden, rather than defaulting every creative text to an emergency flow.

An independent qualified reviewer must define content boundaries and review positive
and negative examples, including failure consequences. Model-based assessment, if
later authorized, is fallible and needs its own quota/privacy/failure policy; no
additional reviewer call is authorized in Q02. Lexical deny lists can cover known
regressions but are not a general semantic safety classifier.

## Required negative evidence

Retain all Q01 diagnosis/fiction/crisis/false-belief/refusal/guarantee/stop fixtures.
Add forced disputation, repeated reassurance, invented sleep metrics/diagnosis,
symbolic dream diagnosis and nonconsensual exercise. Vary paraphrase, negation,
quotation, Ukrainian spelling, explicit correction and delayed return. Pair each
negative with an acceptable response to avoid rewarding blanket refusal.

Test missing/replayed decisions, model/skill/source drift, cancellation during
streaming, no-provider/offline mode and persistence ordering. Require proof that
failed content cannot appear through a delta, retry, history view, map or closure.
Retain the user's original message and a safe error without publishing the rejected
candidate. Avoid logging private text in production diagnostics.

## Limits and release gates

Measure critical failures separately from usability, intent, autonomy and source
fidelity. Report false positives and missed hazards by scenario, not one aggregate
score. A safe single response, authored fixture PASS or independent engineering
ACCEPT does not establish clinical effectiveness or production reliability.

Required next decisions: exact release-boundary design; qualified content owner and
reviewed labels; rights/applicability; Ukrainian crisis/contact review; offline
behavior; explicit implementation authorization; then scoped synthetic evaluation
if separately permitted. The five specialist drafts remain CANDIDATE/OFF throughout.
