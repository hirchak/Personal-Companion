# M7C local ASR capability — pre-C measurements

Original synthetic audio only; no cloud/human/private recording. Final exact-C evidence pending.
Engine [whisper.cpp](https://github.com/ggml-org/whisper.cpp/tree/927cfce34f31707e17f2bff35c349632fb9e2c3a), MIT,
release sourcev1.9.4 commit927cfce34f31707e17f2bff35c349632fb9e2c3a, actual binary1.9.4-dev.
Tag verification false; no signed-tag claim. Source archive9354923bytes,
SHA57e0d8d9a2f9cf5569a7ce3a653e42fbe0e8b89a1ef4e599aa25121a1fcd481b;
license SHA94f29bbed6a22c35b992c5c6ebf0e7c92f13b836b90f36f461c9cf2f0f1d010d.
Binary SHA54d1e7bf2e36ec29bdf70b87a45e26158396d5004909d16d5ad76e51920b566c.

[Small multilingual model](https://huggingface.co/ggerganov/whisper.cpp/tree/5359861c739e955e79d9a303bcbc70fb988958b1),
MIT metadata, revision5359861c739e955e79d9a303bcbc70fb988958b1,
487601967bytes SHA1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b,
matched upstream LFS checksum. Newly downloaded MODEL total487601967/2500000000bytes.
CMake4.4.3 macOS universal2 wheel54406608bytes SHA6c95b37116bb5c714656e4f76931ebdcb739209a1aee91cf51408ccfe137694e,
installed only in generated/local-asr/tooling; pip timeout handled by pinned download/noindex install.
CPU arm64/Accelerate, MetalOFF/OpenMPOFF/CoreMLOFF/sharedlibsOFF; no sudo/Homebrew/global/trust changes.

Actual commands (paths abbreviated to owned project-generated directories):
`<local-cmake> -S <pinned-source> -B generated/local-asr/build-v1.9.4-cpu -DCMAKE_BUILD_TYPE=Release -DGGML_METAL=OFF -DGGML_ACCELERATE=ON -DGGML_OPENMP=OFF -DWHISPER_COREML=OFF -DWHISPER_BUILD_TESTS=OFF -DBUILD_SHARED_LIBS=OFF`,
`<local-cmake> --build generated/local-asr/build-v1.9.4-cpu --target whisper-cli --parallel 4`.
Execution is fixed sandbox-exec argv with model/input/uk/4threads/noGPU/noFallback/JSONoutput; sanitized env,
shellFalse, bounded stdout/stderr/output, timeout/cancel. Deny network/file-data/outsidewrites/process-exec,
allow exactbinary/model/ownedwork/publicsystemlibs. Profile and binary/model bound to verified local receipt.
Own compiled ORIGINAL_SYNTHETIC sentinels verify outside read/write and EPERM network denial; no real/auth
files inspected. Actual engine executes under the same profile. Default app LOCAL remains DISABLED.

Existing local Apple say Lesya uk_UA generates3 original phrases; existing ffmpeg converts16kmonoPCM;
silence/noise are generated deterministically, not speech references. Benchmark normalizes NFC/casefold,
punctuation→space/whitespace collapse and uses Levenshtein reference-normalized word/character edits.
Pre-C clear/reflectiveWER0, shortWER0.5; latency approximately1.8–2.4s per shortclip, checksum/startup included.
Silence/noise WER/CER undefined, no fake UA quality from tones. Peak RSS not measured; no per-engine peak
from this synchronous subprocess collector. Human UA/real hardware/private voice quality NOT_RUN; no
forecast for future user voice. Model size/startup-inclusive wall/RTF/corpus limits are reported explicitly.

M4 record→localASR→candidate→edit→explicitinsert→explicitsend→genuine synthetic provider PASS interim,
providertextonly. Raw candidates/audio/binary/models/cache/DB remain ignored. Public metadata/checksums
and original synthetic screenshots only. Reproduce via scripts/benchmark_m7c_asr.py,
verify_m7c_asr_isolation.py and verify_m7c_voice_live.py (last consumes1 authorized inference).
