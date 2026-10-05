# ADR-015 — Durable local consent and ordinary exact send

2026-10-05, M8E owner requirement; implementation awaits independent review.

Keep the M8D canonical provider constructor and all exact freshness checks. Introduce explicitly typed
standard_send under versioned local consent: backend builds/freeze/signs exact preview at Send, then reuses
its approved payload. The absence of a blocking frontend popup is not absence of an approval: the authenticated
owner's explicit Send authorizes current text within the accepted bounded scope. Expanded journal context
still uses explicit selection + preview approval; no journal references accepted by ordinary send contract.

Two additive local SQLite tables, local_profile_consents/local_deep_scopes, are initialized only by optional
private profile. Existing schema11 domains remain unchanged. Consent binds version/privacy/destination/profiles/
vault/restore epoch and explicit local acceptance timestamp; it makes no external account-setting claim.
Backup copies these tables, but restored epoch rejects old consent; new device/profile cannot inherit it.
No real vault migration is performed in engineering. Lock/restart cancel runtime; accepted enabled consent
can resume only after authentication, without a new seven-checkbox ceremony. Persistent disable/revoke differ
from runtime suspend. Legacy M8D acknowledgement preserves session-only compatibility, not durable acceptance.

Deep scopes bind exact goal/session/focus/range and explicit map corrections. Dynamic advisory map updates
are inside that accepted session scope; all exact per-turn map/source hashes still fail closed. Private context
never runs cross-conversation FTS and refuses digest sources outside the current conversation. Goal-bound prior
closures/maps remain explicit in session scope. This preserves M7D map authority and stale source rules.

Reuse M4 PCMRecorder, Mac Voice and encrypted PWA PhoneStore. Composer is a presentation adapter:
Stop→durable WAV→LOCAL ASR→editable draft; Send records reviewed text before source-bound dispatch.
ASR failure/unavailability preserves audio. Phone's new primary recording path only saves encrypted local
bytes; no network check or automatic upload. Existing upload additionally refuses absent pairing/repair before
any request. Actual transport is still OFF and needs a separately authorized physical gate.

Alternatives rejected: silently removing exact binding; storing private consent/drafts in browser plaintext;
cloud speech fallback; second audio database; duplicate recorder/ASR engine; public runtime installation.
Unfinished recording and unsuccessful backend persistence remain visibly non-durable with retry/unload warning.
Browser crash before persistence cannot be guaranteed; no background or OS-level durability claim.

Forward activation correction is in M8E_CONTRACT; historical owner account-confirmation claims are not rewritten.
