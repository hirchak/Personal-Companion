M8E OWNER UX HOTFIX
ONE-CLICK AI + ALWAYS-LOCAL VOICE + USEFUL ACTIVATION ERRORS

Repository:
https://github.com/hirchak/Personal-Companion.git

Expected current main:
8459c5ecceb19447967c9aa10f20ecc5a0cef113

M8E product and current owner pilot are ACCEPTED/ACTIVE.

The owner has now manually tested the interface and explicitly wants the normal experience simplified.

This is NOT a new milestone.
This is a bounded M8E usability/runtime correction.

==================================================
1. OWNER INTENT
==================================================

Normal application behavior must be extremely simple.

AI:

OFF
→ tap
→ ON

ON
→ tap
→ OFF

Microphone:

tap microphone
→ record
→ finish
→ local Whisper transcription
→ text appears in composer
→ user edits if desired
→ normal Send

No repeated disclosure ceremony.
No seven-checkbox UI.
No separate voice acknowledgement UI.

==================================================
2. EXISTING DURABLE CONSENT
==================================================

For an existing PRIVATE_LOCAL vault that already has valid current-version durable AI consent:

the compact AI button must perform a direct one-click resume/enable.

Do NOT ask for the consent sheet again.

Do NOT ask for external account-setting confirmation.

Do NOT show multiple checkboxes.

The current owner pilot already has durable consent history; preserve it.

==================================================
3. NEW INSTALL / REVOKED CONSENT
==================================================

For a genuinely new install, revoked consent, restored consent epoch, or materially changed privacy/provider contract:

allow ONE simple first-use sheet.

Keep it concise.

Concept:

"AI може надсилати підтверджений текст і вибраний контекст до OpenAI.
Аудіо з мікрофона залишається локально.
Щоденник не додається автоматично."

One primary button:

Увімкнути AI

No checkbox list.

Acceptance creates the existing version-bound durable local consent.

After that:
normal AI ON/OFF is one click.

==================================================
4. EXTERNAL OPENAI SETTINGS
==================================================

Do NOT make these runtime blockers:

- ChatGPT "Improve the model for everyone"
- Codex "Include environments"

Current durable status remains:

TRAINING_CONTROL_CONFIRMATION =
NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER

CODEX_ENVIRONMENTS_CONFIRMATION =
NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER

The application cannot verify these settings automatically.

Show them only as a nonblocking reminder under:

Більше
→ AI & Privacy

Do not show them in the normal conversation flow.

Do not claim they are OFF.

==================================================
5. LOCAL MICROPHONE MUST BE INDEPENDENT OF AI
==================================================

Current composer logic unnecessarily gates microphone availability using AI consent / local_voice state.

Remove that product-level coupling.

Local microphone and local ASR are a local capability.

The microphone must be usable when:

AI = OFF

provided the accepted local voice backend/assets are available.

The browser microphone permission remains the actual user permission interaction.

Do NOT require AI consent merely to record or transcribe local audio.

==================================================
6. LOCAL VOICE ACTIVATION
==================================================

For PRIVATE_LOCAL Mac:

when the user first taps the microphone:

- request normal browser microphone permission if required;
- initialize/reuse the accepted local whisper.cpp backend;
- do not show an application-level voice consent checklist.

If approved local whisper assets are unavailable:

recording may still be preserved locally according to the existing queue/history rules;
show a truthful compact state.

No cloud ASR fallback.

Raw audio external = NEVER.

==================================================
7. VOICE UX
==================================================

Primary interaction stays entirely in composer.

Tap mic:
→ recording visualization.

Controls only:

Cancel
Finish

Finish:
→ persist local audio
→ automatically start local Whisper if available
→ show "Розпізнаю…"
→ transcript appears directly in composer
→ user edits
→ Send manually

No:

"Enable local voice"
"Save transcript"
"Insert transcript"
"Confirm voice"
or other engineering workflow in the primary path.

Voice History remains available under More as recovery/history.

==================================================
8. AI BUTTON
==================================================

Compact conversation AI control should behave like a proper toggle.

Examples:

AI вимкнено

or

Luna · High

or in Deep:

Deep · Luna Max
Deep · Sol 6.1 High

When OFF and valid durable consent exists:

single click attempts activation.

When ON:

single click disables AI.

Do not force the user into Settings to switch it.

==================================================
9. IMPORTANT — FIX CURRENT GENERIC ERROR UX
==================================================

Current PrivatePilotControls receives a backend error code but discards it and always shows a generic message.

Fix this.

Never expose secrets, paths, account identifiers or raw exception messages.

But preserve and display a sanitized stable activation reason.

Map known safe codes to useful user-facing messages.

At minimum distinguish cases such as:

DURABLE_CONSENT_REQUIRED
PRIVATE_PROVIDER_ROUTE_UNAVAILABLE
EXISTING_CHATGPT_AUTH_REQUIRED
PRIVATE_PROVIDER_PROFILE_UNVERIFIED
PROVIDER_EFFORT_UNSUPPORTED
OWNER_SESSION_REQUIRED
OWNER_SESSION_CHANGED
LOCAL_ASR_ASSET_UNAVAILABLE
LOCAL_ASR_PROFILE_UNVERIFIED
CONSENT_VERSION_CHANGED

If another SafeError occurs:
show a generic message plus its allowlisted sanitized code.

Do not display raw exception text.

==================================================
10. PROVIDER READINESS
==================================================

The current owner screenshot shows:

AI OFF
+
activation failure.

The generic UI currently prevents us from knowing the actual cause.

Add a bounded readiness path if necessary so activation can fail with an exact sanitized reason.

Do not make an inference request merely to test readiness.

No test conversation.
No provider turn/start for UX diagnostics unless it is already strictly required by the accepted activation mechanism.

No PAYG.
No new auth.
No fallback.

==================================================
11. DO NOT WEAKEN AI PRIVACY BOUNDARIES
==================================================

Preserve:

exact canonical provider payload
bounded current conversation
Deep scope binding
journal default OFF
explicit journal expansion approval
no whole-vault context
provider child has no vault filesystem authority
raw audio never provider
no provider fallback
no PAYG
Health OFF
clinical OFF
phone transport OFF

Simplify USER INTERACTION, not backend privacy boundaries.

==================================================
12. AI OFF BEHAVIOR
==================================================

AI OFF must NOT disable local conversation storage or microphone.

With AI OFF:

- user may type;
- user may record;
- local Whisper may transcribe;
- transcript may appear in composer;
- conversation may remain local.

Sending to external AI requires AI ON.

Historical AI messages remain visible.

==================================================
13. TESTS
==================================================

Add deterministic coverage for:

1. existing durable consent:
   AI OFF → one click → AI ON.
   No consent modal.

2. AI ON → one click → AI OFF.

3. revoked/no consent:
   one simple first-use sheet;
   one acceptance;
   subsequent toggles require no sheet.

4. no seven-checkbox UI in primary M8E flow.

5. external account-control reminder does not block activation.

6. microphone works when AI OFF.

7. microphone does not require durable AI consent.

8. local Whisper works with AI OFF.

9. voice transcription fills composer and does not auto-send.

10. raw audio absent from provider payload.

11. provider activation failure surfaces exact sanitized error code/message.

12. raw backend exception/path/account data never appears.

13. local voice/backend unavailable gives useful non-destructive status.

14. journal/Deep/private bindings unchanged.

Use Chromium where relevant.

No live provider inference calls.

==================================================
14. REAL OWNER VAULT
==================================================

Do NOT use the real vault during implementation/evidence.

Do not inspect owner conversations, journal entries, transcripts or audio.

Use synthetic PRIVATE_LOCAL roots.

After implementation:
STOP for independent review.

Do NOT install the candidate into the real owner pilot before independent ACCEPT.

==================================================
15. DELIVERY
==================================================

Standing workflow:

verify current main
→ implement/fix
→ final C
→ exact-C tests
→ evidence-only R
→ privacy/public-tree review
→ normal fast-forward main push
→ verify origin/main == R
→ STOP.

No force push.
No deploy.
No tag/release.
No next milestone.

==================================================
16. FINAL RESPONSE
==================================================

Return:

Base
C
R
origin/main

AI toggle:
existing consent one-click = YES/NO
OFF→ON
ON→OFF

first-use consent:
number of confirmations

microphone:
works with AI OFF YES/NO
separate application consent required YES/NO
local whisper
raw audio external

activation diagnostics:
sanitized error code preserved YES/NO

tests
live inference calls = 0
real vault inspected = NO

phone OFF
clinical OFF
Health OFF

M8E HOTFIX = AWAITING_REVIEW

STOP.