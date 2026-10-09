# ADR-018 — Standalone Mac shell and independently signed updates

2026-10-09. Status: IMPLEMENTED_CANDIDATE_AWAITING_REVIEW.
Authority: [M8F](../../prompts/M8F_MACOS_APP_INSTALLER_UPDATES.md).

Use AppKit/WKWebView with the existing paper/ink/sage React surface. Compile arm64
with the installed Command Line Tools; deployment target macOS 14. Other Macs and
older OS versions need separate verification. Copy the existing Python 3.13
framework interpreter, standard library and exactly requirements.runtime.lock;
relocate Mach-O linkage inside the bundle. No pip, Node, Git, project venv,
developer environment or account state is required or included at runtime.

Keep the accepted M8D format4 release payload and typed root/backup/security
contracts. Add a separate native manifest over runtime, payload, UI, licences and
Whisper. Both identities bind exact source C. Native metadata is additive; old
release provenance is not relabeled as standalone. Data resides outside the app
in a distinct PersonalCompanionStandalone Application Support container; it never
discovers or upgrades the existing pilot. First initialization needs GUI consent.
Only the generated native `.app/Contents/Resources/payload` build location is
additively admitted by release.package_path; symlink/Git-content checks remain.
Data roots inside Git remain forbidden. Installed payloads use the existing
outside-Git path contract.
PRIVATE_LOCAL still requires verified FileVault APFS, 0700/0600 and no ACL grants.
No application-level encryption claim. Test builds have a different bundle ID,
disposable-home boundary and independent test trust; production updates disabled.

An inherited anonymous pipe carries bounded native commands and transient unlock
codes. No credential is put in arguments, URLs, environment, diagnostics or files.
The native shell requires an explicit unlock, uses LocalAuthentication in the
normal build, and redeems the one-time code in an origin-bound WKWebView closure.
Nonpersistent cookies preserve existing Host/Origin/CSRF/build/idle-lock gates.
Sleep and session changes revoke sessions. EOF/Quit stops the child; its held
OS lock scopes single-instance and maintenance to this managed root.

Use Sparkle **2.10.0**, independently pinned Ed25519 archive AND signed-feed
verification, validation before extraction, explicit checks/install and monotonic
build identity. Owner separately authorized only its project-local official
download/integration. No privileged custom installer/downloader. Test keys live
only in disposable ignored files, never Keychain or bundles; normal builds cannot
enable this channel. Sparkle performs download/stage/copy/swap/relaunch. The app
stops writers, verifies a WAL/attachments backup and restores a copy before allowing
installation; keeps a previous code bundle separately. Incompatible migrations
are blocked until a reviewed migration plan can be proved on a copy. Code recovery
and fresh-root data recovery remain distinct explicit operations.

Existing pinned whisper.cpp CPU/small-multilingual assets may be copied only after
exact hashes and MIT notices are checked. A relocated receipt and actual packaged
engine isolation test are needed; historical dev-cache proof alone is insufficient.
Audio storage works with ASR unavailable. AI defaults OFF and unavailable without
an explicitly authorized existing route; no Codex/account installation or calls.
Q03, specialist candidates, clinical/Health/phone/sync gates remain unchanged.

Developer artifacts are ad-hoc signed local candidates. Production requires an
owner-selected identity, nested Developer ID signing/hardened-runtime assessment,
notarization, reviewed production update key/channel/host and independent release
acceptance. No signing identity/account access, notarization, upload or release is
authorized here. Source main publication is separate from binaries and user data.

Sources: [Sparkle setup/security](https://sparkle-project.org/documentation/),
[exact Sparkle release](https://github.com/sparkle-project/Sparkle/releases/tag/2.10.0),
[Apple notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution),
[Whisper model licence](https://github.com/openai/whisper/blob/main/LICENSE).
