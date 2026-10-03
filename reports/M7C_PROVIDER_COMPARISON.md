# M7C provider comparison — AWAITING_REVIEW

Final C `36b99e45a5d6ce93a828cf1be7d82a76685a89e9`, base `73ec6064107d3d25475bb7454d96a2bd964ee77c`. Engineering/synthetic tests, no provider winner or clinical quality ACCEPT.

| Model/route | Scope | Requests | Controller valid | Median / max wall | Reported usage |
|---|---|---:|---:|---|---|
| gpt-6-luna / CODEX_SUBSCRIPTION | FINAL_EXACT_C (21cases) | 25 | 24/25 | 4.191s / 6.330s | {"cachedInputTokens": 166400, "inputTokens": 217147, "outputTokens": 2487, "totalTokens": 219634} |
| gpt-6.1-sol / CODEX_SUBSCRIPTION | FINAL_EXACT_C (6cases) | 9 | 9/9 | 6.535s / 9.066s | {"cachedInputTokens": 43776, "inputTokens": 82321, "outputTokens": 1075, "totalTokens": 83396} |
| gpt-6-luna / CODEX_SUBSCRIPTION | INTERIM_C1 (21cases) | 26 | 26/26 | 4.276s / 7.185s | {"cachedInputTokens": 127744, "inputTokens": 235551, "outputTokens": 2777, "totalTokens": 238328} |
| gpt-6.1-sol / CODEX_SUBSCRIPTION | INTERIM_C1 (21cases) | 26 | 25/26 | 6.102s / 8.456s | {"cachedInputTokens": 58368, "inputTokens": 226402, "outputTokens": 2572, "totalTokens": 228974} |

Both models completed genuine synthetic multi-turn Deep conversation through installed Codex0.159.0
existing ChatGPT auth. Actual streaming observed, validated finals only. Final Luna covers all21cases,
25attempts because failed goal proposal did not run its dependent agreement/followup. Sol final9attempts
cover6targeted cases, including goal proposal→separate synthetic agreement→Deep followup, prior Free
reference,3turn theme, explicit closure and next steps. Full21case/26turn Sol evaluation is INTERIM C1;
it is not relabeled final-C. Frame/skill hashes/request schema/UI/ASR were unchanged by metadata fix;
full regression and affected live paths repeated. No LLM quality judge or automatic provider winner.

Observed failures: C1 Sol DEEP_NEXT returned unsolicited closure, rejected CLOSURE_SCHEMA_REQUIRED.
Final Luna DEEP_GOAL produced unexpected SDK item/server tool request, rejected PROVIDER_TOOL_REQUEST_DENIED.
No invalid final assistant/goal/journal/memory/practice/health write, no tool approval response or fallback.
Exact unsupported SDK item subtype was intentionally not logged; filesystem/shell/MCP/root restrictions
remain. Host CLI working agreements are injected despite project docs0, an explicit route limitation.
Technical structured-output adherence is mixed, not a universal PASS or private-runtime suitability claim.

Canonical goal ledger94/100 total:7interim capability/voice +52interimC1eval +34finalCeval +1finalvoice.
Luna59 attempts (58transport completed,1failed); Sol35transport completed. Controller validation failure
and transport completion are separate. C1 raw per-case goal-counter sum overlapped one concurrent voice
attempt; corrected attributable eval count26 is disclosed. Final per-case local attempt IDs bind exact
ledger records, including failure; raw prompts/reasoning/credentials are not usage logs.6requests remain,
no ledger reset. Metrics are provider-reported tokens, not billing estimates.

MiniMax M3 Token Plan: UNAVAILABLE / AUTH_EXISTING_ROUTE_NOT_EXPOSED,0calls. Authorized env/project/callable
interfaces inspected; no credential extraction/private config search/new login or key. Included quota/
Credits fallback unverified. Existing local LLM: UNAVAILABLE / NO_EXISTING_ROUTE_IDENTIFIED,0calls.
No new billing/auth/account/APIkey/PAYG path/credits purchase or provider fallback; provider internal
allocation/retention/private-personal suitability NOT_VERIFIED. Real private data OFF, clinical0.

Qualitative observations from original synthetic rows: accepted responses used Ukrainian, generally
short reflective questions, separated facts from hypotheses, adjusted rejected/changed interpretations,
referred to the supplied ten-minute prior Free draft, abstained from diagnosis/licensed identity/dosing.
Some next-step text is formulaic; one closure-only case correctly admits no session details rather than
inventing them. These observations are not a score/clinical oracle. Candidate A/B technically usable
in completed cases; provider selection and quality review pending owner/architect.

[Final original synthetic pack](evidence/M7C/FINAL_SYNTHETIC_PROVIDER_REVIEW.json),
[interim full corpus](evidence/M7C/INTERIM_C1_SYNTHETIC_REVIEW.json),
[metrics/ledger](evidence/M7C/PROVIDER_METRICS.json). Public material reviewed: original authored fiction,
no RAW/article/form/private audio/account data. Hidden reasoning never captured. Default runtime OFF.
