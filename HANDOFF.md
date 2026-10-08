# M8E owner local repair — AWAITING_REVIEW

Base published R4: `ed7ec39d904a6319f4f0911c042e04598422a94a` (live origin/main verified).
Final implementation C6: `4124851adc08858e22e99b3adc6c70d5843c2b6b`; intermediate source fix C5: `1a286f2e840566873ef177f77904b982df620ecb`.
Exact package manifest: `a3cc8564a6e0d327ebb169f9c9708f03b71c8270a68ba5ab87b95bb7c0a8297d`.

Source selection now recognizes the known pre-hotfix voice profile, preserving complete manifest/file validation
and all other profile fields. Targets remain current-only; unknown source profiles fail before backup/activation.
Seven source-upgrade regressions and seven opaque/fixed-host/IPv4 transport regressions use synthetic fixtures.
C5 exact Python853/web53/Chromium21, protected preflight/backup/upgrade and vault preservation passed.
C6 fixes confirmed IPv6-first timeout using IPv4 to the same fixed chatgpt.com:443 endpoint; helper TCP now PASS.
Final exact-C6 Python860/web53/build/Chromium21/privacy PASS. Protected preflight/backup/upgrade PASS;
root/schema/content-free counts preserved. Exact C6 is running at http://127.0.0.1:8765; static build/mode
verified, page opened. Owner manually unlocks/enables/sends; post-fix readiness remains pending approval. The concurrent Chromium run had a5s assistant-count
timeout; the isolated exact same scenario passed21 without assertion/code changes.

Owner now explicitly authorizes repair/upgrade/restart and inspection of the last test; only state/error were
queried, never message/response/audio content. Last manual request: FAILED / PROVIDER_RPC_FAILED. This is not
proof of auth failure or model unavailability. Offline SDK protocol tests are synthetic, network-denied and never
start an inference turn. Live readiness (initialize/account-read refresh=false/model-list, no thread/turn) is
initially rejected by auto-review, then explicitly authorized once by the owner: account/read workspace-routing
timeout, model/list PASS, no inference. That authorization is consumed; one post-fix control probe is pending approval. The helper
connectivity defect was independently isolated through anonymous DNS/TCP-only probes, with no auth/HTTP/RPC.

Original product C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` and H02 remain externally ACCEPTED;
this candidate is AWAITING_REVIEW. Phone/clinical/Health OFF, external controls NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER,
human UA PARTIAL_OWNER_PILOT / OPEN. Keep all unlock, AI enable, messages and microphone actions manual.
See `reports/M8E_OWNER_LOCAL_REPAIR_REPORT.md` and `prompts/M8E_OWNER_LOCAL_REPAIR.md`.

An unrelated untracked `prompts/M8E_Q01_CONVERSATION_QUALITY_AUDIT.md` appeared during work; it was not read,
changed or staged. Preserve it; no quality-audit or next-milestone work was started.
