# M4 — follow-up local ASR and Ukrainian quality gate

Current: **M4-A14 LOCAL_ASR_BACKEND_NOT_RUN**; REAL_LOCAL_ASR_MODEL = NOT_RUN /
PERMISSION_REQUIRED; HUMAN_UA_QUALITY = NOT_RUN. Deterministic fake and trusted Python fixture
exercise pipeline mechanics only. No actual speech model was executed; engine/model/hash unknown.
No Whisper API/OpenAI/MiniMax/provider call or cloud fallback.

Bounded host inspection found no whisper-cli/whisper-cpp/whisper executable on PATH or model
candidate in this repository. This is not a search of all home/private folders. Existing ffmpeg 9.0
was inspected but is not a runtime dependency and no codec command was run on private material.

## Exact additional permission and prerequisites

Authorize a named, version/commit-pinned whisper.cpp source/binary download, a named **multilingual**
model download (not an English-only `.en` model), project-local build/install if needed, and offline CPU
benchmark execution on generated or individually rights-cleared synthetic material. No sudo/Homebrew/
global installs, system trust, provider spending or real personal recording permission is implied.
Use a fresh owner-approved ignored/generated project-local directory such as `generated/local-asr/`
for source/build/bin/models and temporary input/output. Keep weights and audio outside public Git.

Upstream sources checked 2026-10-01:
[whisper.cpp repository and license](https://github.com/ggml-org/whisper.cpp),
[upstream model/source documentation](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md).
The upstream describes a local C/C++ engine and separate model files. The exact engine release/model
artifact, download bytes and disk/RSS requirements are **NOT_VERIFIED for this follow-up**. Resolve
those against the chosen immutable artifact before permission and download; do not infer current
capacity or Ukrainian accuracy from example tables. Record license/rights, source URL/revision,
checksum from authoritative release/model metadata and independently computed SHA-256 after receipt.

Inspect the actually obtained executable with version/help, capture exact available arguments and
output behavior, then implement its fixed argv contract through the bounded runner. M4 intentionally
contains no guessed whisper flags. Verify CPU/offline configuration, input PCM constraints, exact model
path/hash and no network dependency/fallback. Validate OS filesystem/egress restrictions and exclude
Git/provider auth/credentials before allowing an untrusted or genuine engine. A sanitized environment
and trusted fixture are not isolation proof. Keep the actual engine disabled until these gates pass.

## Actual-model benchmark procedure

Use explicit consent/rights-cleared corpus only. Do not scan existing user audio folders. Generate
silence, low/high-energy noise and tone locally; these test safety, not speech accuracy. For Ukrainian
clear speech and a short phrase, retain exact reference text, language setting, corpus provenance,
license and generation method. Generated/TTS speech is SYNTHETIC/TTS; label it visibly and do not
present it as human speech quality. If no rights-cleared human UA audio exists, HUMAN_UA_QUALITY
stays NOT_RUN. No TTS provider calls are authorized by this runbook.

For each actual-model run record code/engine/model hashes, tool versions, OS/architecture, CPU config,
audio rate/channels/duration, wall time, wall/audio real-time factor and peak RSS if measured. Compute
WER/CER only against a valid reference with documented normalization; punctuation errors need not
imply semantic failure. Include clear phrase, short phrase, silence and noise; inspect hallucinations
and cancellation/timeout/malformed inputs. Preserve untrusted candidate until explicit edit/confirm.
Keep corpus/model/audio files in temporary/ignored storage; publish sanitized counts/metrics only.

PASS applies only to the exact actual local model execution and separately identified corpus.
Otherwise A14 stays LOCAL_ASR_BACKEND_NOT_RUN, even if all engineering tests pass.
