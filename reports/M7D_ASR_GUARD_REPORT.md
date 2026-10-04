# M7D local ASR speech-presence guard

Existing checksum-pinned project-local whisper.cpp1.9.4-dev/CPU small multilingual487601967bytes; no new
ASR/VAD model downloads, system installs or cloud fallback. PCM_SIGNAL_V1 measures local energy,
zero crossings and modulation. Near-silence/flat seeded broadband noise stop before Whisper; ambiguous
signal returns UNCERTAIN and M4 REVIEW_REQUIRED. Explicit user review/edit is required before insertion;
no normal sendable hallucinated candidate for NO_SPEECH, no auto-send. Retry/delete remain available.

Actual original Lesya TTS and deterministic generated PCM only. No private or human/owner/girlfriend voice.
Six cases: silence, noise, quiet(scale0.025), normal, short, leading/trailing silence. False normal acceptances0,
false speech rejections0 on this bounded corpus. Quiet/normal WER0, shortWER0.5, paddedWER0.2857 remain
synthetic engine limits, not a forecast for Ukrainian human speech. Full metrics/checksums/source scope in
reports/evidence/M7D/ASR_GUARD.json; raw audio/models stay ignored local-only. Human UA NOT_RUN, cloud NONE.
Signal heuristic is not perfect VAD; music/complex noise/tones/microphones/RSS/real hardware unverified.
Engineering part of M7C-N03 guarded; separate human quality gate remains OPEN.
