# M8E owner local repair — AWAITING_REVIEW

Base R4: `ed7ec39d904a6319f4f0911c042e04598422a94a`; live origin/main verified before work.
Final implementation C6: `4124851adc08858e22e99b3adc6c70d5843c2b6b`.
Intermediate source fix C5: `1a286f2e840566873ef177f77904b982df620ecb`.
Original accepted product `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` and H02 remain externally ACCEPTED.
This new repair has no independent ACCEPT. Existing local restart evidence changes were preserved.

## Change

The new manager rejected the pre-hotfix source because its voice declaration differed from the current profile.
Source selection now recognizes exactly the old `EXPLICIT_OWNER_GATE_DEFAULT_OFF` variant, with all other
fields unchanged. Manifest identity and the complete file-hash set are checked first. Target validation remains
current-only. Unknown profiles, safety-field changes, tampered files and historical targets fail closed.
No installed source files/manifests or vault receipts are edited to make them pass.

Seven deterministic PRIVATE_LOCAL fixture regressions cover protected upgrade, preserved entry/root, backup
source/producer provenance, unknown voice/clinical/Health/fallback variants, integrity tampering and strict targets.
These use ORIGINAL SYNTHETIC data; no real owner records are engineering fixtures.

## Verification checkpoint

Mac arm64, existing Python3.13/Node/Vite/Chromium/local Whisper only; no installs.

| Command / check | Result |
|---|---|
| `pytest tests/test_m8e_source_upgrade.py -q` | exit0, 7 PASS |
| `pytest -q` before final added target-negative test | exit0, 852 PASS |
| `npm --prefix apps/web test` | exit0, 53 PASS |
| Clean exact-C5 `release prepare` / TypeScript + Vite | exit0, PASS |
| Exact-C5 package `verify_m8e_browser --package ...` | exit0, 21 checks PASS |
| Chromium page errors / non-loopback requests / live provider calls | 0 / 0 / 0 |
| Privacy scan, public tree + snapshots + local Git objects | exit0, PASS at pre-final checkpoint |
| Final exact-C5 full Python | exit0, 853 PASS |
| C5 owner preflight / protected backup / upgrade | exit0, PASS / PASS / PASS |
| C5 root identity / schema-integrity / content-free table-count preservation | YES / PASS / YES |
| C6 transport + source + private focused tests | exit0, 65 PASS |
| C6 anonymous fixed-destination helper TCP CONNECT | exit0, PASS |
| Final exact-C6 full Python / web / build / Chromium | exit0, 860 / 53 / PASS / 21 PASS |
| Final docs / privacy-public tree | exit0 / exit0, PASS |
| Final C6 preflight / protected backup / existing-root upgrade | exit0, PASS / PASS / PASS |
| Final C6 root/schema/integrity/count preservation | YES / PASS / PASS / YES |
| Final C6 restart / static build+PRIVATE_LOCAL mode verification | PASS / PASS (exit0) |
| Local page | OPEN, http://127.0.0.1:8765 |
| Post-fix SDK readiness | NOT_RUN, owner control-probe permission pending |
| Live provider inference / real microphone recordings | 0 / 0 |

Initial bounded pytest invocation hit sandbox loopback denial; elevated synthetic regression execution succeeded.
Initial exact-clone tests started before web dist/browser prerequisites were ready: 49 failed / 804 passed (exit1).
The missing existing Chromium/ASR paths and generated web dist were prepared; final exact-C5 passed853.
The first C6 packaged-browser run during concurrent full regression also timed out5s waiting for a second
synthetic assistant after the Deep quality profile switch. The identical isolated scenario passed21 after full
regression ended, with no code/assertion changes. Those preliminary failures are not represented as PASS.

Intermediate C5 package: `M8D-1a286f2e840566873ef177f77904b982df620ecb`, manifest
`437237746443dd4bedb39ac60a4ed4ea94a66698e1e8d417afdf35186a4f80e5`, format4/schema11.
It was built from a clean detached clone at C5, using only existing dependency caches; complete package verified.
Final C6 package `M8D-4124851adc08858e22e99b3adc6c70d5843c2b6b`, manifest
`a3cc8564a6e0d327ebb169f9c9708f03b71c8270a68ba5ab87b95bb7c0a8297d`, format4/schema11, was likewise built from
the exact clean detached C6 and verified completely. No moving-main build, downloaded dependencies or external release.
Runtime lock remains `f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`.

## Owner diagnosis and authorization

Owner explicitly requested repair/local activation and allowed inspection of the last manual test. Only its
allowlisted state/error metadata was queried: FAILED / PROVIDER_RPC_FAILED. No conversation/message/response/audio
content or IDs were read into tools/evidence. Credentials remained inside the SDK, never extracted or copied.

Local network-denied native SDK probes used ephemeral synthetic thread configuration, never `turn/start` or
prompt submission. Empty-auth account/read, model/list and thread configuration passed. Existing-auth offline
account/read failed in workspace-routing discovery; the denied network makes that inconclusive for the owner's
live failure. All synthetic ephemeral client state was removed. No real app conversation was created.

Automatic approval review initially rejected live readiness before execution because explicit permission was
absent under earlier restrictions. Owner subsequently explicitly authorized one `account/read` refresh=false +
`model/list` check through the accepted transport, without thread/turn/inference. The authorized probe returned
account/read workspace-routing timeout (RPC -32603); model/list PASS. It did not establish auth/model entitlement.
The probe exited1 because its teardown called `close_transport` instead of `stop_transport`; the typo was fixed
without rerunning readiness. Only verified owned diagnostic children were terminated and their ephemeral state removed.

Anonymous fixed-host transport diagnostics (no SDK/auth/RPC/HTTP upstream) returned UNAVAILABLE. Under the exact
helper OS network/file profile, DNS passed, first address family was IPv6, IPv4 TCP passed and IPv6 TCP timed out.
This establishes a transport connectivity defect independently of account data. C6 uses an explicit IPv4 socket
to the same `chatgpt.com:443`; anonymous helper CONNECT now PASS. Its TLS blind byte relay/allowlist/isolation,
SDK-only auth, model/effort/context/privacy contracts and no-provider-fallback/PAYG remain unchanged.

Seven deterministic fake-socket tests cover IPv6-first delay, the IPv4 fixed host, bidirectional opaque byte relay,
rejection of unknown hosts/ports/protocols before opening a socket, and clean close without a success response or
raw errors on timeout/connection failure. No arbitrary external destination, credential copy or TLS interception.

The single live readiness authorization is consumed. One post-fix control probe has been requested and is pending
approval; none has run yet. No agent inference ran. Manual owner enable/send remains the inference validation. Startup stays AI OFF and performs no provider call.
Fresh unlock code was generated only in the local foreground session and is absent from files/evidence.

Official [app-server auth documentation](https://learn.chatgpt.com/docs/app-server) and
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) were checked for supported
RPC/config behavior; no new login/key, proxy/gateway provider, account setting or auth-storage change was used.

Phone OFF / NEEDS_TRANSPORT_GATE; clinical/Health OFF; external settings NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER;
human UA PARTIAL_OWNER_PILOT / OPEN. Raw audio external NEVER. No new milestone/deploy/tag/GitHub Release.

Evidence publication: normal forward C5/C6 plus evidence-only R; exact R/push verification reported after commit.
No recursive report self-hash; no deploy, tag or external release. CI is NOT_CHECKED, local verification above.
An unrelated new untracked quality-audit prompt appeared during execution, was preserved and not read/staged;
no quality-audit or later-milestone work occurred.
