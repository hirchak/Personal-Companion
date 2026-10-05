M8E — CONVERSATION-FIRST MOBILE UX + SEAMLESS LOCAL VOICE
PERSONAL COMPANION PILOT EXPERIENCE

Repository:
https://github.com/hirchak/Personal-Companion.git

Expected current main:
49d03d97d444083a63d18f3f3ec9ec8d295c19fd

M8D private AI/local voice engineering is externally ACCEPTED.
Owner's existing PRIVATE_LOCAL vault is active.

This goal is primarily product UX + bounded integration refinement.

Do NOT inspect, dump, screenshot, search or otherwise read the owner's actual private entries, conversations, audio, paths or receipts.

All engineering/testing uses disposable PRIVATE_LOCAL roots and ORIGINAL SYNTHETIC content.

No new live provider benchmark is required.

==================================================
0. MODEL / EXECUTION
==================================================

Preferred implementation model:
GPT-6.1 Sol / High.

Verify actual installed capability.
Do not invent settings or CLI flags.

Plan Mode OFF.

Follow the standing direct-main workflow:

actual main
→ autonomous implementation/fixes
→ final implementation C
→ exact-C tests
→ evidence-only R
→ privacy/public-tree review
→ normal fast-forward push to main
→ verify origin/main == R
→ STOP.

No force push.
No release/tag/deploy.

==================================================
1. CORRECT THE REAL ACTIVATION HISTORY
==================================================

Owner clarification:

During the first real private AI/manual voice test, the owner checked the disclosure boxes inside Personal Companion but had NOT independently verified or changed the external OpenAI account settings:

- ChatGPT "Improve the model for everyone"
- Codex "Include environments"

Therefore any current durable statement claiming that these external settings had already been confirmed OFF before that first test is inaccurate.

Correct this forward.

Do NOT rewrite historical commits/evidence.

Record truthfully:

FIRST_REAL_PRIVATE_AI_TEST:
occurred before independent external-account setting verification.

TRAINING_CONTROL_CONFIRMATION:
NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER

CODEX_ENVIRONMENTS_CONFIRMATION:
NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER

Future private AI use should present the one-time setup requirement described below.

Do NOT inspect the owner's OpenAI account automatically.

Do NOT claim retroactive training-off.

==================================================
2. PRODUCT DIRECTION
==================================================

Personal Companion should stop feeling like an engineering harness.

It should feel like a polished personal AI application.

Primary experience:

CONVERSATION FIRST.

Secondary:
Journal
Creative
More / Settings

The supplied ChatGPT screenshots are interaction references only:

- minimal centered conversation experience;
- bottom-anchored composer;
- compact microphone interaction;
- clean recording visualization;
- easily accessible previous conversations;
- mobile-app feel.

Do NOT clone ChatGPT branding, proprietary visual assets, logos or exact trade dress.

Create an original Personal Companion interpretation using the existing paper / ink / sage identity.

==================================================
3. DEFAULT LANDING = CONVERSATION
==================================================

After unlock, the normal default landing surface must be:

РОЗМОВА

not Journal.

Journal remains one tap away.

Target primary navigation:

Розмова
Щоденник
Творчість
Більше

For narrow/mobile layouts:
prefer native-feeling bottom navigation.

For desktop:
use an appropriate responsive layout, potentially with a collapsible conversation/history rail.

Navigation state should be obvious without looking like a SaaS admin dashboard.

==================================================
4. FREE AND DEEP MUST BE FIRST-CLASS MODES
==================================================

The user must immediately understand that there are two conversation modes:

Звичайна
Глибока

Use a compact segmented switch / equivalent near the Conversation header.

Do not hide Deep behind an unrelated "Цілі" button.

ZVYCHAINA / FREE:

- normal natural conversation;
- Luna / High;
- bounded history of this conversation;
- no journal context by default;
- no goal required.

GLYBOKA / DEEP:

- long-running structured conversation;
- agreed goal;
- editable focus;
- working map;
- closure/session continuity;
- previous Deep state preserved locally;
- journal context still OFF unless explicitly selected.

When the user selects Deep:

if there is an appropriate active goal:
offer to continue it;

otherwise:
guide the user through selecting/creating a goal in a simple sheet.

Do not weaken existing exact goal/revision/source binding.

==================================================
5. MODEL SELECTION IS NOT A CONVERSATION MODE
==================================================

Do not confuse model choice with Free/Deep.

Free:
fixed Luna / High for now.

Deep:
compact selector:

Економний
Luna / Max

Якісний
Sol 6.1 / High

Owner ceilings remain binding:

Luna <= Max
Sol 6.1 <= High

No Sol xhigh/max/ultra.
No fallback.

The normal conversation screen should not expose large technical model/provider configuration panels.

Detailed model information may be available through Settings/info.

==================================================
6. CONVERSATION HISTORY / CONTEXT WINDOWS
==================================================

Conversation history is a first-class product feature.

The user must be able to:

- start a new conversation;
- see recent conversations;
- reopen one;
- continue the exact same local conversation context;
- distinguish normal vs Deep conversations;
- archive/delete conversations;
- continue Deep sessions attached to their existing goal/session state.

Desktop:
a collapsible left conversation rail/sidebar is acceptable.

Mobile:
use a drawer/sheet accessible from a clear Chats/History button.

Do not permanently consume narrow mobile width with a desktop sidebar.

Each conversation should display a useful local title.

Do NOT spend provider calls merely to generate titles.

Use a deterministic/local title approach unless existing accepted logic already provides one.

Examples:
first meaningful user text truncated safely,
explicit user rename,
or existing local title logic.

Do not automatically pull unrelated old conversations into a new conversation.

Existing accepted bounded conversation continuity remains the authority.

==================================================
7. MEMORY / CONTEXT BEHAVIOR
==================================================

Do NOT create a hidden "AI knows everything" mode.

Context rules remain:

New Free conversation:
current bounded conversation only.

Reopened Free conversation:
its own local conversation history resumes.

Deep:
its agreed goal/focus/map/session state resumes.

Journal:
OFF by default.

Other conversations:
NOT automatically injected.

Existing user-confirmed memory mechanisms, where applicable, must preserve their current explicit/provenance rules.
Do not add automatic memory promotion.

The history UI exists so the user can deliberately return to a topic.

==================================================
8. REMOVE REPEATED ENGINEERING-STYLE CONSENT
==================================================

Current seven-checkbox session acknowledgement is not acceptable normal UX.

Implement versioned durable LOCAL consent for this device/private profile.

On the first AI activation for the current privacy/provider profile:

show ONE concise onboarding sheet explaining:

- confirmed text and bounded approved context may be processed by OpenAI;
- raw microphone audio stays local;
- journal is not automatically included;
- provider retention is not claimed to be zero;
- there is no automatic model/provider fallback;
- external OpenAI account Data Controls are controlled by the owner, not by this application.

Require one explicit acceptance.

Also clearly tell the owner that before subsequent private AI use they should verify:

ChatGPT:
Improve the model for everyone = OFF

Codex:
Include environments = OFF

Do not claim the application verified those external settings.

Persist accepted consent locally.

Do not store it in Git/evidence.

Do NOT require the same seven checkboxes after every restart/unlock.

Consent must be version-bound.

If provider destination, privacy contract or materially relevant scope changes:
invalidate the durable consent and ask again.

User must be able to go to:

Більше / Settings
→ AI & Privacy
→ inspect consent
→ disable AI
→ revoke/reset consent.

==================================================
9. NORMAL SEND SHOULD BE NORMAL
==================================================

For an ordinary message containing only:

- current user text;
- current conversation's already-approved bounded history;
- existing session/Deep scope where applicable;

the UX must be:

type
→ Send
→ response.

Do NOT show the giant exact-context confirmation popup for every ordinary message.

Pressing Send is the explicit per-message approval for the current message inside the already accepted bounded conversation scope.

Backend security remains strict:

- canonical exact provider payload;
- exact hashes;
- source revisions;
- provider profile;
- no silent expansion.

The user may have an optional:

"Що буде надіслано"

inspection control.

But it must not block every normal message.

==================================================
10. EXTRA JOURNAL CONTEXT STILL NEEDS EXPLICIT APPROVAL
==================================================

If the user adds information outside the existing conversation/session scope, such as journal entries:

require a concise contextual approval.

Example:

"До контексту буде додано 3 записи щоденника."

The user can:

- inspect them;
- deselect individual items;
- confirm.

After confirmation, use the accepted canonical exact payload/hash mechanism.

No whole-vault context.

If any selected record revision changes:
fail closed and ask for fresh approval.

==================================================
11. DEEP SESSION SCOPE APPROVAL
==================================================

Starting a Deep Session creates an explicit bounded scope:

- agreed goal;
- current goal revision;
- focus;
- current Deep conversation;
- working map;
- prior closures;
- selected retrieval range where applicable.

Show this clearly when starting/changing the Deep scope.

Once the scope is accepted, normal subsequent messages inside the unchanged Deep session should not require another giant provider-context modal each time.

If the Deep scope materially changes:
renew the scope confirmation.

Additional journal records still require explicit additional-context approval.

==================================================
12. VOICE UX — REMOVE THE ENGINEERING POPUP FLOW
==================================================

The current large "Голосовий ввід" modal with:

- microphone;
- local recognition section;
- save transcript;
- insert text;
- audio controls;
- multiple separate buttons;

is too technical for the primary UX.

Replace the primary flow.

Target composer:

[ + ] [ message input ] [ model/mode if needed ] [ microphone ] [ send ]

The microphone must be directly integrated into the composer.

==================================================
13. VOICE RECORDING INTERACTION
==================================================

Target interaction:

User taps microphone.

Composer transforms into a clear recording state.

Show an original Personal Companion recording visualization:
waveform / pulse / animated voice indicator.

Do not copy ChatGPT's exact orb/waveform visuals.

Show:

- recording duration;
- clear "recording" state;
- Cancel;
- Stop / Finish.

The interaction should feel app-like and immediate.

No separate setup modal for every recording.

If browser microphone permission has not yet been granted:
request it through the normal browser permission flow.

==================================================
14. AFTER STOP → AUTO TRANSCRIBE
==================================================

When user presses Stop/Finish:

1. finalize local recording;
2. persist raw audio locally;
3. if approved local whisper.cpp is currently available:
   automatically begin local transcription;
4. show a compact state in the composer such as:
   "Розпізнаю…";
5. when completed:
   place the transcript directly into the normal text composer;
6. user can freely edit it;
7. normal Send sends the edited text.

Do NOT auto-send to AI after transcription.

Do NOT require:

"Зберегти транскрипт"
"Вставити текст у розмову"

for the normal path.

Those are implementation details, not user workflow.

==================================================
15. ASR FAILURE / UNAVAILABLE STATE
==================================================

Audio must never disappear merely because transcription is unavailable.

If local ASR is unavailable, crashes, Mac backend is unavailable, or the audio cannot currently be transcribed:

persist the audio locally in an explicit state such as:

WAITING_FOR_LOCAL_ASR
TRANSCRIPTION_FAILED
REVIEW_REQUIRED

Surface a simple user message:

"Запис збережено. Розпізнаємо, коли локальний сервіс буде доступний."

Allow manual Retry.

No cloud ASR fallback.

==================================================
16. VOICE HISTORY
==================================================

Provide an unobtrusive Voice History / Голосові записи area.

Do not place it as a permanent large element on the main composer.

Accessible via:
More,
or a small history/action affordance.

Each voice item should expose useful states:

Записано
Очікує розпізнавання
Розпізнається
Готово
Потрібна перевірка
Помилка

Where appropriate show:

- timestamp;
- duration;
- transcript preview if available;
- retry;
- insert/use transcript;
- delete audio.

Raw audio remains local.

No secure-erasure claim.

==================================================
17. PHONE / OFFLINE VOICE PREPARATION
==================================================

M8E does NOT authorize the real phone transport gate.

However, prepare the UX/state model so the phone PWA can behave correctly offline.

If PWA is running on a phone and Mac/private transport is unavailable:

- recording must still be possible where browser capabilities permit;
- raw audio must be stored in the existing encrypted local PWA storage/outbox architecture;
- state becomes QUEUED_FOR_MAC / WAITING_FOR_TRANSCRIPTION or equivalent;
- user can see it in Voice History;
- user may delete it locally.

When a FUTURE approved private phone transport becomes available:
the queued audio may sync to Mac and be transcribed locally.

Do NOT implement public cloud audio storage.

Do NOT use Vercel as a private audio vault.

Do NOT enable Tailscale/certificates/phone pairing in M8E.

Actual physical Galaxy transport remains:
NEEDS_TRANSPORT_GATE.

Chromium/offline simulation is allowed.

==================================================
18. IMPORTANT PHONE SEMANTICS
==================================================

"Internet available" is not itself sufficient.

Automatic phone→Mac processing must require the approved private transport to the Mac.

Until that transport exists:

queued phone audio remains encrypted locally on the phone/PWA.

No public internet upload.

No provider receives raw audio.

==================================================
19. MOBILE-FIRST APP SHELL
==================================================

At 390px width the product must look and behave like a real mobile app.

Target interaction characteristics:

- full-height app shell;
- persistent bottom navigation;
- conversation content scrolls independently;
- composer stays reachable near bottom;
- safe-area handling;
- touch-friendly tap targets;
- drawers/sheets instead of desktop modal clutter;
- no horizontal overflow;
- keyboard/viewport behavior handled;
- recording state works with mobile viewport resizing.

Do not simply shrink the desktop UI.

==================================================
20. DESKTOP EXPERIENCE
==================================================

Desktop can take advantage of more space.

Suggested structure:

left:
collapsible conversation history;

center:
active conversation;

optional compact header/actions.

Do not fill the entire desktop with whitespace and floating technical controls.

Keep focus on conversation.

==================================================
21. CONVERSATION EMPTY STATE
==================================================

A fresh Conversation page should feel inviting and minimal.

Conceptually:

"Що у вас сьогодні на думці?"

composer immediately accessible.

Secondary quick starts may include:

Просто поговорити
Розібрати думку
Подумати над рішенням

Do not overfill empty state with cards/settings.

==================================================
22. DEEP MODE EXPERIENCE
==================================================

When user switches to "Глибока":

make the difference understandable.

Deep may show a compact scope/header:

Мета
Фокус
Поточний етап

Working Map may exist behind a drawer/details area instead of permanently occupying the conversation.

The user should be able to:

- continue an existing Deep topic;
- choose another active goal;
- begin a new Deep conversation;
- close/pause it;
- return later.

Keep the actual M7D contracts underneath.

==================================================
23. CONVERSATION LIST ORGANIZATION
==================================================

Conversation history should make both kinds understandable.

Possible visual distinctions:

Звичайна
Глибока

For Deep optionally show goal/title.

No need for excessive folders initially.

Search/history filtering may be added only if easy and already supported locally.

Do not build a complex project-management system.

==================================================
24. AI STATUS SHOULD BE QUIET
==================================================

Remove the giant engineering-style AI status panel from the normal conversation experience.

Replace it with compact indicators.

Examples:

Luna · High
Deep · Luna Max
AI вимкнено
🎙 локально

Detailed disclosure/status belongs in Settings.

Historical assistant messages remain visible when AI is currently OFF.

This is expected and must not look contradictory.

==================================================
25. SETTINGS / MORE
==================================================

Create a coherent More/Settings area.

At minimum:

AI & Privacy
Models
Local Voice
Voice History
Backups
Data
About / Technical status

AI & Privacy:

- provider destination;
- local durable consent;
- journal context default OFF;
- raw audio local;
- provider fallback NONE;
- external account-setting reminder;
- revoke/disable AI.

Models:

- Free Luna/High;
- Deep Luna/Max;
- Deep Sol6.1/High;
- owner ceilings.

Local Voice:

- whisper status;
- local-only disclosure;
- retained audio management;
- no cloud fallback.

Technical details should not dominate normal user interaction.

==================================================
26. VISUAL LANGUAGE
==================================================

Use the supplied screenshots only as UX inspiration:

- strong focus on composer;
- minimal chrome;
- recording state visually obvious;
- compact switches;
- polished app feel.

Do NOT clone them.

Keep Personal Companion's own identity:
warm paper/sage/ink can remain the default light theme.

Refine it toward:
modern,
calm,
premium,
personal,
less "form page",
more "application".

Avoid excessive:
borders,
fieldsets,
boxed engineering sections,
raw JSON,
technical labels in primary UX.

Use original icons/standard iconography.

No external copyrighted visual assets.

==================================================
27. OPTIONAL DARK MODE
==================================================

Dark mode is NOT required to complete M8E.

If the current design system already supports it cheaply, it may be prepared.

Do not scope-expand merely to imitate the dark screenshots.

Interaction quality matters more.

==================================================
28. REAL PRIVATE VAULT
==================================================

Do NOT inspect the owner's actual content during implementation.

Do not use the real conversation transcript shown by the owner as a public fixture.

Do not commit screenshots of the real vault.

Use ORIGINAL SYNTHETIC fixtures only.

Owner will manually run the accepted build later.

==================================================
29. HUMAN VOICE STATUS
==================================================

The owner has manually exercised a real Ukrainian microphone→local-whisper path at least once.

Do NOT copy that private transcript/audio into Git.

This does NOT automatically close the formal human-UA ASR gate.

Represent it truthfully as something like:

HUMAN_UA_ASR:
PARTIAL_OWNER_PILOT / STILL_OPEN

until a deliberate bounded human evaluation is completed.

No clinical or quality certification.

==================================================
30. SECURITY / PRIVACY MUST NOT REGRESS
==================================================

Preserve:

PRIVATE_LOCAL typed root
FileVault/security preflight
owner-only permissions
localhost application
auth/auto-lock
CSRF/Origin/Host controls
main-process deny-egress
isolated provider process
no vault filesystem access by provider
canonical exact provider payload
journal default OFF
no whole-vault mode
raw audio NEVER to provider
local whisper only
no provider fallback
no PAYG
no hidden second provider
Health OFF
phone transport OFF
clinical_active = 0
all specialist modules OFF

==================================================
31. NORMAL SEND CONSENT CONTRACT
==================================================

Important architectural requirement:

Removing the visible per-message preview modal must NOT remove exact backend binding.

For standard messages inside an already accepted scope:

- user pressing Send is the explicit per-message action;
- backend constructs the exact canonical payload;
- payload may contain only the already-consented conversation/session scope;
- no additional journal/private source may appear silently;
- exact payload/hash is recorded locally;
- source/profile changes fail closed.

For expanded scope:
explicit extra-context approval is required.

Tests must demonstrate this distinction.

==================================================
32. VOICE STATE MACHINE
==================================================

Codex may choose exact internal architecture, but externally the state machine must support:

IDLE
RECORDING
LOCAL_AUDIO_SAVED
TRANSCRIBING
DRAFT_READY

and recoverable branches such as:

WAITING_FOR_LOCAL_ASR
REVIEW_REQUIRED
FAILED
CANCELLED
DELETED

No hidden data loss.

Restart/reload must not fabricate successful transcription.

==================================================
33. MOBILE OFFLINE QUEUE
==================================================

Use existing accepted PWA encrypted local storage/outbox capabilities where appropriate.

Do not create a second unrelated storage system if existing architecture can support queued voice.

At minimum simulate:

phone/PWA offline
→ capture audio
→ encrypted local persistence
→ queued status visible after reload
→ Mac unavailable
→ no upload
→ future-transport-ready state preserved.

Do not claim actual Galaxy hardware PASS from Chromium.

==================================================
34. TESTING
==================================================

Preserve relevant M1–M8D regressions.

Add/adjust deterministic tests for at least:

A. Landing/navigation
- unlock → Conversation default;
- Journal still reachable;
- Creative reachable;
- More/Settings reachable;
- 390px bottom nav;
- desktop navigation/history layout.

B. Conversation modes
- visible Free / Deep selector;
- Free starts without goal;
- Deep guides goal selection;
- reopen prior Free conversation;
- reopen prior Deep conversation with exact goal/session state;
- New Conversation creates clean bounded history.

C. Model UX
- Free Luna/High;
- explicit Deep Luna/Max;
- explicit Deep Sol6.1/High;
- no Sol above High;
- no automatic fallback.

D. Consent
- first-time one-sheet consent required;
- durable versioned consent persists locally across normal restart;
- repeated seven-checkbox flow removed;
- revoke removes consent;
- privacy/profile version change requires renewed consent;
- app does not claim external settings were verified automatically.

E. Send
- standard bounded conversation sends without repeated popup;
- Send itself authorizes current message inside existing scope;
- canonical provider payload remains exact;
- no journal context appears by default;
- extra journal selection triggers explicit approval;
- stale selected entry fails closed.

F. Voice
- mic accessible from composer;
- start recording;
- visible compact recording state;
- cancel;
- stop;
- auto local transcription;
- transcript automatically populates composer;
- transcript editable;
- no automatic AI send;
- raw audio absent from provider payload;
- local-ASR failure preserves audio;
- retry works;
- Voice History survives reload.

G. Offline/mobile queue
- simulated PWA offline audio capture;
- encrypted local queued state;
- reload preserves it;
- unavailable Mac does not upload anywhere;
- future private-transport eligibility remains explicit;
- no cloud fallback.

H. Responsive visual
- 390px no horizontal overflow;
- keyboard/visual viewport;
- desktop coherent;
- no giant engineering control panel on normal conversation page.

Use real Chromium where relevant.

No live provider calls.

==================================================
35. VISUAL REVIEW
==================================================

Perform a bounded visual review of the final synthetic build at:

- desktop;
- 390px mobile;
- empty conversation;
- active conversation;
- Deep mode;
- recording state;
- transcribing state;
- conversation-history drawer/sidebar;
- Settings/AI & Privacy.

Use only ORIGINAL SYNTHETIC content.

Fix obvious UX issues autonomously.

Do not use an LLM provider call for this review.

==================================================
36. DEFINITION OF DONE
==================================================

M8E is ready for independent review when:

- Conversation is the default landing;
- Free/Deep are obvious top-level conversation modes;
- previous conversations are easy to reopen;
- New Conversation is clear;
- Deep continuity remains exact;
- primary mobile UX feels app-like;
- mic is integrated directly in composer;
- recording is visually clear;
- stop automatically starts local ASR;
- transcript lands directly in composer;
- no normal save/insert-transcript ceremony;
- failed/unavailable ASR preserves audio safely;
- Voice History exists;
- mobile offline queued voice state is supported/simulated without enabling real phone transport;
- durable one-time AI consent replaces repeated seven-checkbox flow;
- ordinary messages do not require repeated giant preview;
- expanded journal context still requires explicit approval;
- exact backend payload binding remains intact;
- no security/privacy regression;
- no live provider calls;
- real vault contents are untouched;
- exact C/R published normally to main.

==================================================
37. FINAL RESPONSE
==================================================

Return concise handoff:

Base
C
R
origin/main

default landing
navigation

conversation modes:
Free
Deep

conversation history:
new
resume
Deep resume

models:
Free
Deep economical
Deep quality

consent:
first-time behavior
durable behavior
revoke behavior
external account settings status

normal send:
popup required YES/NO
backend exact binding status

journal context:
default
expanded approval

voice:
composer mic
recording UX
automatic local transcription
draft behavior
failure queue
Voice History
raw audio external

mobile:
390px
offline audio queue
physical phone status

tests:
Python
web
Chromium
build
privacy
visual review

real vault inspected = NO
live provider calls = 0

HUMAN_UA_ASR:
PARTIAL_OWNER_PILOT / OPEN

PHONE_TRANSPORT:
NOT_ACTIVATED / NEEDS_TRANSPORT_GATE

clinical = OFF
Health = OFF

M8E = AWAITING_REVIEW

STOP.