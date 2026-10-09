# Build and distribution gates

Run from one clean exact C with the existing project Python, npm/node_modules,
Python.framework 3.13 and installed Command Line Tools. No dependency installation.
Sparkle2.10.0 official tarball must be present at the explicitly owner-authorized
ignored dependency path; expected SHA256 is
`c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c`.
The upstream framework verifies ad-hoc, without a TeamIdentifier; do not call this
an authenticated Developer ID release. Download hash provenance is GitHub release
metadata over HTTPS, not independent publisher authentication. Test runtime trust
is its newly generated Ed25519 public key, independent from feed/hosting checksums.

```bash
.venv/bin/python -m scripts.build_m8f --build 101 --output generated/m8f/development --dmg
```

The native receipt inventories all bundled bytes, links, runtime package versions,
locks, source C, licence notices, exact ASR and Sparkle input. Python distribution
notices ship alongside dependency dist-info licences; React licences remain in
the local build inventory. Outputs/keys/feeds/logs stay ignored, never public Git.
Build requires local pinned Whisper assets by default; `--without-asr` is an
explicit development variant and shows ASR unavailable, never simulated completion.

Local test builds additionally require a fresh test public-key file, loopback feed
and new `/private/tmp/m8f-…` home. Only the LOCAL_TEST compilation accepts this trust.
Private test key is generated from CryptoKit and passed to Sparkle sign_update by
file; no key in arguments/bundle/Git, no Keychain operation. Signed feeds bind
product/channel/arch/build/exact source/native manifest/schema. Sparkle's archive
signature validates before extraction. Production lacks a test-key/feed route.

Ad-hoc runtime signatures and development-only library-validation exception allow
local engineering checks, not external distribution or default Gatekeeper approval.
Check nested `codesign --verify --deep --strict`, entitlements and `spctl --assess`;
assessment failure is recorded, never solved by deleting quarantine/weakening OS trust.
Production must sign all nested Mach-O/framework/helper targets inside-out with an
owner-authorized Developer ID, use hardened runtime and assess needed entitlements,
remove the debug library-validation exception, notarize/staple and recheck on clean
Macs. Credentials/account use, notarization upload and binary publication are separate.

Two future delivery options:

| Option | Source/artifact/user-data separation | Tradeoff |
|---|---|---|
| Approved downloads host | Public source remains public; only reviewed signed/notarized app + signed feed on HTTPS; private vault stays local | Simplest install; public binaries; signing key kept off host |
| Authenticated private distribution | Private download authorization via owner-approved service; signed artifacts/feed still independently verified; no GitHub PAT/client repository credentials | Restricted delivery; authentication/support/expiry require separately reviewed integration |

Recommend the approved HTTPS downloads host with independently signed artifacts and
feed for first delivery, after distribution acceptance. No service/host/domain/release
or visibility change is created here. Production updater enablement requires an explicit
production build profile/key/channel policy plus owner permission; it cannot be enabled
by changing a setting in this development candidate.

Support/recovery: native backup/restore menus and [user guide](M8F_USER_GUIDE.md).
Removing only `.app` keeps the separate data container and backups. Code recovery is
the verified previous bundle, distinct from renewing a vault from an explicit backup.
Historical prerequisite installers remain supported; no automatic old-pilot migration.
