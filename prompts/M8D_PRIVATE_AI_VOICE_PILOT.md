M8D — PRIVATE AI CONVERSATION + LOCAL VOICE PILOT
OPTIONAL MODULE INTEGRATION AFTER ACCEPTED PRIVATE CORE PILOT

Repository:
https://github.com/hirchak/Personal-Companion.git

Expected current main:
cee41e3a7638cf7efba511e93157ff5c3eb47ce7

Accepted private-core implementation:
M8C C = a00a14277974b7f6c25846d0eb7a23879f86183a
M8C R = 4eb8188f771adc9ea472d5c3e3379421b5e16e19

Accepted release:
M8C-a00a14277974b7f6c25846d0eb7a23879f86183a

Current state:
Owner Mac PRIVATE_LOCAL core pilot STARTED.
Existing real private vault must NOT be inspected/read/scanned by the development agent.

==================================================
0. MODEL / EXECUTION
==================================================

Preferred implementation model:
GPT-6.1 Sol / High.

Verify installed support.
Do not invent CLI flags/settings.

Plan Mode OFF.

This is an implementation goal.

Development/testing must use ORIGINAL SYNTHETIC fixtures and disposable private-mode roots.

Do NOT read, inspect, query, copy or test against the owner's existing live private vault.

==================================================
1. OWNER INTENT
==================================================

Owner explicitly wants to test:

- real AI conversation quality;
- Free Conversation;
- Deep Session;
- continuity across turns;
- voice recording from the Mac browser;
- local Ukrainian speech-to-text;
- review/edit of transcript;
- explicit sending of confirmed transcript to AI;
- optional explicitly selected journal context later.

The owner does NOT authorize blanket automatic access to their whole vault.

The intended privacy model is:

CURRENT USER MESSAGE / CONFIRMED TRANSCRIPT
+
BOUNDED CONVERSATION HISTORY
+
ONLY EXPLICITLY SELECTED/PREVIEWED EXTRA CONTEXT

→ external AI provider.

No automatic vault crawl.

==================================================
2. PROVIDER / DATA DESTINATION GATE
==================================================

M7C-N02 currently remains OPEN HARD for general private-provider use.

For this goal, implement a BOUNDED OWNER-ACCEPTED PRIVATE PILOT provider gate.

Target route:

existing authenticated ChatGPT/Codex subscription route only.

No:
- API key billing;
- PAYG;
- credits purchase;
- new account;
- new auth;
- hidden backend endpoint;
- OAuth extraction;
- provider fallback;
- MiniMax fallback;
- second cloud provider.

Before PRIVATE AI activation, require an explicit local owner acknowledgement that:

1. the approved text/context will leave the Mac and be processed by OpenAI;
2. raw audio is NOT sent;
3. only the exact approved context is transmitted;
4. provider service retention is not claimed to be zero;
5. no automatic provider fallback exists.

Also require owner confirmation that, before using private AI:

- ChatGPT "Improve the model for everyone" is OFF;
- Codex "Include environments" is OFF.

Do not attempt to inspect account credentials or private account configuration.

If those confirmations are not available:
private AI activation remains BLOCKED.
Do not weaken the gate.

If current official/provider behavior materially differs from the documented project assumptions, record the conflict and stop the provider activation sub-gate.

==================================================
3. PRIVATE PROVIDER STATUS
==================================================

Do NOT globally claim that consumer-provider privacy is universally approved.

If all M8D private-pilot gates pass, represent M7C-N02 as something equivalent to:

CLOSED_FOR_THIS_OWNER_BOUNDED_PILOT_ONLY

or:

OWNER_ACCEPTED_BOUNDED_PRIVATE_PROVIDER_ROUTE

while preserving that this is NOT:

- zero-retention certification;
- general commercial approval;
- approval for another person's data;
- automatic full-vault access.

Exact naming may follow the project's status conventions.

==================================================
4. AI MODEL PROFILES
==================================================

Reuse the already reviewed provider/controller architecture from M7C/M7D.

Preferred reviewed candidates, only if still genuinely available in installed Codex:

FREE:
gpt-6-luna / high

DEEP economical:
gpt-6-luna / max

DEEP quality:
gpt-6.1-sol / high

Verify actual installed model/effort support.
Do not silently substitute another model.

If a candidate is unavailable:
fail visibly or require explicit owner selection.
No fallback.

Preserve one ConversationController / one model voice.

==================================================
5. PRIVATE AI CONTEXT POLICY
==================================================

PRIVATE_LOCAL AI must NOT receive the entire vault automatically.

Default Free Conversation context:

- current user message;
- bounded history of that conversation;
- accepted conversation state needed by the existing controller.

Default Deep Session:

- current message;
- bounded conversation history;
- exact agreed goal/focus/session state;
- existing source-bound Working Map / closure state as accepted in M7D.

Journal/private-note context:

OFF by default.

If user wants journal context:
use the existing explicit selection/context-preview mechanism.

The UI must show enough information for the user to understand what will be sent.

Binding must preserve:

- exact source revisions;
- exact context hash;
- exact receipt;
- selected range/preset;
- current draft/message;
- provider model/effort/profile.

Edits/deletions/stale context must fail closed.

No hidden memory promotion.
No automatic journal writes from AI.
No Health context.
No creative-to-wellbeing inference.

==================================================
6. LIVE PRIVATE CONVERSATION ACTIVATION CONTRACT
==================================================

Implement a distinct PRIVATE_LOCAL AI capability gate.

Core private mode currently denies conversations/providers.
Do NOT simply remove the deny-all boundary.

Extend the private profile explicitly and narrowly.

Possible runtime states:

PRIVATE_AI_OFF
PRIVATE_AI_OWNER_CONSENTED

Default remains OFF.

On restart:
provider activation should not silently become enabled without the accepted durable/local activation contract.

Owner must have a visible way to disable AI again.

Provider env variables alone must never activate AI.

==================================================
7. PROCESS ISOLATION
==================================================

Preserve the accepted isolated provider-process boundary from M7C/M7D.

The main PRIVATE_LOCAL application process should remain deny-egress.

Only the reviewed provider adapter process may reach the exact provider route.

Preserve:

- sanitized environment;
- no shell/tools;
- no MCP;
- no arbitrary file access;
- no workspace/vault access;
- no plugins/apps/browser/computer use;
- no tool calls;
- no provider fallback;
- timeout;
- cancellation;
- strict structured output;
- request/profile/model binding.

The provider child receives serialized allowed context, not filesystem access to the vault.

==================================================
8. LOCAL VOICE / ASR
==================================================

Enable Mac microphone recording for PRIVATE_LOCAL conversation.

Raw audio must remain local.

Target:
existing reviewed project-local whisper.cpp capability from M7C/M7D.

Known reviewed candidate:
whisper.cpp 1.9.4-dev
small multilingual model
CPU/local Mac route

Use existing verified assets if present.

No cloud ASR.

No provider receives raw audio.

If existing ASR assets are missing:
do NOT silently substitute cloud ASR.
Report the exact missing local asset.

Do not install system components.

==================================================
9. OWNER HUMAN VOICE PILOT
==================================================

Owner explicitly authorizes use of THEIR OWN microphone/voice for the post-review human Ukrainian ASR pilot.

Important:

Development/evidence generation must not inspect/listen to/store the owner's raw voice in Git.

Engineering before review:
synthetic/TTS audio only.

After independent M8D ACCEPT:
the owner may record their own real voice through the application.

Raw audio:
local PRIVATE_PERSONAL only.

No Git.
No screenshots/evidence containing transcript unless owner explicitly supplies sanitized text.

M7C-N03 can only become CLOSED_FOR_OWNER_PILOT after actual human voice testing, not from synthetic tests.

==================================================
10. VOICE UX
==================================================

Restore/implement a microphone control in PRIVATE_LOCAL Conversation.

Desired flow:

press/hold or start recording
→ stop
→ local speech detection
→ local Whisper ASR
→ transcript shown to user
→ user may edit
→ explicit "Send" confirmation
→ confirmed text becomes user conversation message
→ only then AI inference begins.

Never:
record → automatically send to provider.

Silence/noise:
use existing deterministic PCM guard.

NO_SPEECH:
do not run/send.

UNCERTAIN:
require review.

Transcript may be edited before sending.

==================================================
11. RAW AUDIO RETENTION
==================================================

Raw audio must have clear local-only retention behavior.

For the pilot:

- never send audio externally;
- show its state;
- allow explicit deletion;
- do not retain indefinitely without the user knowing;
- do not include raw audio in public evidence.

Choose the smallest safe policy consistent with existing M4 contracts.

Document exact retention behavior.

Do not claim secure erasure.

==================================================
12. PRIVATE UI
==================================================

When PRIVATE AI is activated:

restore:
- "Розмова"
- Free Conversation
- Deep Session

with truthful status.

Journal remains available separately.

Conversation should be usable without selecting journal context.

Add microphone control when local ASR is available.

Display clearly, without excessive warnings:

- AI is external;
- raw audio stays on this Mac;
- only confirmed text/selected context is sent.

If AI is OFF:
conversation should show OFF state rather than pretending to respond.

Do not expose clinical/self-help modules.

==================================================
13. NO AUTOMATIC VAULT ACCESS
==================================================

This is important.

Provider child has NO filesystem access to PRIVATE_LOCAL vault.

The application may read exact selected records locally and serialize only the approved bounded context.

Provider never receives:

- SQLite file;
- filesystem path;
- entire journal database;
- unrelated entries;
- Health data;
- audio;
- secrets;
- backup metadata;
- other local files.

Test this boundary.

==================================================
14. PRIVATE CONVERSATION PERSISTENCE
==================================================

Conversation history, goals, working maps and closures may persist locally in the private vault under existing accepted schemas.

They remain PRIVATE_PERSONAL / derived provenance according to existing contracts.

Restart:
conversation remains locally available.

Interrupted provider request:
FAILED, never auto-resumed.

Retry:
explicit.

Delete/edit source:
existing invalidation rules apply.

==================================================
15. OWNER-CONTROLLED JOURNAL CONTEXT
==================================================

Allow the user to optionally say in effect:

"Use these journal items / this period for this conversation."

Use existing Goal Start / Last7 / Last30 / Custom mechanics where applicable.

Before provider transmission:
create exact local preview/receipt.

No "AI knows my whole journal" hidden mode.

If later product UX wants an easier selector, preserve the same exact binding underneath.

==================================================
16. NO CLINICAL ACTIVATION
==================================================

Keep OFF:

cbt_reflection
worry_rumination
sleep_review
nightmare_review
grounding

clinical_active = 0.

AI may have normal supportive conversation, reflection and brainstorming through existing neutral skills.

No diagnosis.
No therapist claim.
No treatment protocol.

27 findings remain OPEN.

==================================================
17. NO HEALTH
==================================================

Health bridge:
OFF.

health-to-AI:
OFF.

No Health Connect data enters context.

M6-N01 unchanged.

==================================================
18. NO PHONE
==================================================

Phone remains OFF.

PHONE_PILOT:
NEEDS_TRANSPORT_GATE.

No Tailscale.
No certificate changes.
No LAN/public exposure.

==================================================
19. PROVIDER LIVE ENGINEERING EVIDENCE
==================================================

Owner authorizes a bounded LIVE provider smoke for this engineering goal using ORIGINAL SYNTHETIC content only.

Maximum new live provider attempts:
4 total.

No retry that creates another provider attempt unless counted.

No PAYG/new billing/fallback.

Suggested minimum coverage:

FREE:
- simple conversation;
- one continuity turn.

DEEP:
- goal/focus turn;
- continuity/working-map turn.

VOICE:
- synthetic local ASR transcript explicitly confirmed and sent through the same private integration path.

CONTEXT:
- explicit synthetic journal context preview → provider response.

Every attempt must be preserved as PASS/FAIL.
Do not rewrite failures.

Do not use the actual owner private vault for engineering evidence.

==================================================
20. MODEL QUALITY
==================================================

Do not create an LLM judge.

Preserve response samples for human architect review using synthetic inputs only.

Evaluate mechanically:

- valid schema;
- requested context respected;
- rejected facts not resurrected;
- no extra permissions;
- one main follow-up rule;
- Ukrainian address policy;
- no diagnosis;
- no automatic downstream effects.

Human qualitative verdict remains separate.

==================================================
21. PRIVATE PROFILE CHANGES
==================================================

Current M8C private profile is core-only.

M8D may introduce a new exact profile version, for example:

MAC_PRIVATE_AI_VOICE_PILOT_V1

or version 2 of private profile.

It must explicitly enumerate:

ON:
journal
creative
local search
backup/restore
conversation
optional local voice/ASR
owner-approved external AI route

OFF:
clinical
specialist skills
health
phone
external embeddings
cloud sync
telemetry
publication
automatic sharing
provider fallback
cloud ASR

No implicit capability inheritance.

==================================================
22. SECURITY / PRIVACY
==================================================

Preserve M8C:

- PRIVATE_LOCAL typed root;
- FileVault/volume gate;
- 0700/0600;
- no cloud-folder roots;
- backup protection;
- localhost app;
- auth/auto-lock;
- exact release provenance.

Adding provider AI must not weaken local vault security.

Development agent must never inspect current real vault.

Provider child must never receive filesystem authority.

==================================================
23. ACTUAL PRIVATE VAULT
==================================================

During implementation and evidence:
DO NOT TOUCH the owner's current actual private vault.

Use disposable private-mode roots with ORIGINAL SYNTHETIC data only.

After implementation:
M8D = AWAITING_REVIEW.

Do NOT activate AI/voice on the real pilot vault until independent ChatGPT architect review returns ACCEPT.

Prepare an exact post-ACCEPT activation procedure.

==================================================
24. TESTS
==================================================

Preserve M1–M8C regression suite.

Add coverage for at least:

- private AI default OFF;
- explicit owner provider acknowledgement;
- missing acknowledgement blocks transmission;
- provider env cannot bypass gate;
- exact provider profile/model/effort binding;
- no fallback;
- provider process no vault filesystem access;
- exact context serialization;
- current-message-only conversation works with empty vault;
- journal context default OFF;
- explicit journal context preview works;
- stale journal selection fails;
- raw audio never provider payload;
- microphone private UI;
- local ASR only;
- silence/noise gate;
- transcript review/edit before send;
- no auto-send after transcription;
- interrupted inference recovery;
- restart persistence;
- disable AI again;
- clinical stays OFF;
- health stays OFF;
- phone stays OFF;
- no non-provider external egress;
- backup/restore preserves safe AI activation semantics;
- private vault not used in engineering evidence.

Use real Chromium.

==================================================
25. HUMAN UA VOICE GATE
==================================================

Implementation M8D does NOT self-close human Ukrainian ASR quality.

Prepare a small owner-side post-ACCEPT test:

- 5 short natural Ukrainian utterances;
- quiet/normal speaking;
- one sentence with names/numbers if desired;
- one intentionally short phrase;
- one sentence after a brief silence.

Show transcript.
Owner judges usefulness.

Do not upload recordings/evidence.

Only sanitized owner verdict may be recorded later.

==================================================
26. POST-ACCEPT ACTIVATION
==================================================

After independent M8D ACCEPT, owner should be able to enable AI + local voice on the existing PRIVATE_LOCAL pilot without recreating or migrating the vault.

Activation must:

- re-run security preflight;
- verify exact accepted release;
- obtain explicit provider acknowledgement;
- verify owner confirmation of training/environment data-control settings;
- enable exact private AI/voice profile;
- restart;
- preserve existing journal data;
- leave all unrelated optional modules OFF.

No new core vault.

==================================================
27. GIT / DELIVERY
==================================================

Standing workflow:

verify main
→ implement/fix
→ final C
→ exact-C tests
→ bounded synthetic live-provider evidence
→ evidence-only R
→ privacy/public-tree review
→ normal fast-forward push main
→ origin/main == R
→ STOP for independent review.

No force push.
No history rewrite.
No release/tag/deploy.
No real-vault activation during implementation.

==================================================
28. FINAL READINESS
==================================================

Report:

PRIVATE_AI_ENGINEERING:
READY / NOT_READY

LOCAL_VOICE_ENGINEERING:
READY / NOT_READY

PRIVATE_AI_PROVIDER_ROUTE:
READY_FOR_OWNER_BOUNDED_PILOT / BLOCKED

PRIVATE_VAULT_CONTEXT:
EXPLICIT_SELECTION_ONLY

RAW_AUDIO_TO_PROVIDER:
NEVER

FREE_PROFILE:
exact model/effort or NOT_AVAILABLE

DEEP_PROFILE:
exact model/effort or NOT_AVAILABLE

M7C_N02:
exact bounded status

M7C_N03:
still OPEN_HUMAN_TEST until owner test

CLINICAL:
OFF

HEALTH:
OFF

PHONE:
NEEDS_TRANSPORT_GATE

ACTUAL_PRIVATE_AI_ACTIVATION:
NOT_STARTED

==================================================
29. FINAL RESPONSE
==================================================

Return concise handoff:

Base
C
R
origin/main

tests:
Python
Chromium
web/build
privacy

provider:
attempts used / max4
FREE model/profile
DEEP model/profile
failures
fallback NONE
PAYG NONE

voice:
local backend
raw audio external = NO
synthetic ASR integration
human UA = NOT_RUN

context:
default conversation context
journal context behavior
full-vault automatic access = NO

gates:
M7C-N02
M7C-N03
clinical
Health
phone

private real vault:
NOT TOUCHED

post-ACCEPT activation procedure:
READY / NOT_READY

M8D:
AWAITING_REVIEW

STOP.

==================================================
HISTORICAL OWNER CORRECTION — SUPERSEDED BY FINAL BINDING BELOW
==================================================
Received during execution, 2026-10-04. Overrides original model/effort/live-attempt requirements.
FREE gpt-6-luna/high. DEEP gpt-6.1-sol/high only if catalog-supported; if unavailable STOP route.
No silent substitution, no max/ultra or any effort above HIGH. Owner may later explicitly select MEDIUM.
Max NEW M8D live attempts4 TOTAL. Suggested: Free/continuity, Deep goal/focus/continuity,
confirmed local ASR transcript→AI, explicit synthetic journal preview→AI. Do not repeat success for benchmarking;
failed retry only essential and counted within4. No fallback/PAYG/credits/new billing/auth/account.
At correction receipt, actual M8D inference attempts0; max/ultra started0. Capability model/list/initialize
checks are read-only and made no inference. Preserve all subsequent failures; do not reset ledger.


FINAL OWNER BINDING — supersedes ALL previous M8D model/effort instructions.
FREE default: gpt-6-luna / high. DEEP economical: gpt-6-luna / max.
DEEP quality: gpt-6.1-sol / high. Explicit Deep profile choice; no automatic fallback.
Luna allows low/medium/high/xhigh (if supported)/max; MAX is its ceiling.
Sol6.1 allows low/medium/high only; above HIGH is forbidden under all circumstances.
Main comparison: comparable bounded Deep Luna/Max versus Sol6.1/High.
Maximum NEW live attempts stays4 TOTAL; failed/cancelled attempts/retries count.
Priorities: Luna/High Free; Luna/Max Deep; Sol6.1/High Deep; local-ASR confirmed
transcript OR explicit journal integration, choosing the missing required integration.
No wasted benchmarking, no fallback/PAYG/new auth/billing/account route.
At final correction: attempts consumed0, max/ultra attempts started0.
