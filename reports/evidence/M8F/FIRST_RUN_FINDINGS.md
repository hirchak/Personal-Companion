# First-run findings retained

C1–C10 are forward commits; no failed history was rewritten. Initial implementation used
universal otool output incorrectly, an invalid Frameworks/runtime layout and Python's launcher
instead of the actual interpreter. C2/C3/C4 correct these; C5 was documentation only and did
not fix package_path, so C6 carries the actual bounded payload-path fix. C7 supplies the supported
one-action Sparkle driver/dirty guard; C8 confines preflight to the new managed root, avoiding
unrelated Application Support siblings. C9 adds physical test-capture denial; C10 supplies worker
serialization/busy state and persistent recovery errors after independent UI review.

An early default pytest collected dependency tests inside ignored generated bundles; testpaths
now selects the complete project tests directory (1041 tests). No project test was skipped.
M3/M4 positive fake-process protocol cases allow one second of interpreter scheduling; their
intentional timeout cases retain 150/200ms, and production runtime deadlines are unchanged.

C7 full: 1035 PASS / 3 FAIL. C8: 1039 PASS / 1 FAIL. C9: 1038 PASS / 2 FAIL.
Exact-C10 diagnostic full: 1041 PASS,857.38s,exit0. Its plugin calls original assertions unchanged,
adds no skips and captures synthetic states only if an assertion fails. Initial diagnostic import
failed during setup; retained original log and corrected only ignored instrumentation. Another
instrumented run stopped on fake-media failure. Default C10 runs remain flaky: one full returned
1038 PASS / 3 recording-start failures; final isolated standard full returned1039 PASS /2 FAIL:

- M3 oversized fixture: expected OUTPUT_LIMIT, observed PROVIDER_ERROR.
- M4 track interruption fixture: recording state missing at original five-second assertion.

Both exact failing nodeids passed unchanged same-C10 focused recheck (2 PASS,11.57s). Nine media
fixtures passed observational diagnostics. Standard full flakiness remains OPEN; recheck is not
an erased failure or a proof of its cause. M2/8GB had11.3GB encrypted swap in use, but causality
was not proved. Default parallel web run timed out on PBKDF2/audio-store test; all53 passed with
one worker and unchanged five-second test deadline. Full log hashes/safe summaries are retained.

Native C10 transcript save followed immediately by Quit did not persist before confirmation;
that attempt is not claimed PASS. Repeating the explicit save and waiting for the settled GUI
confirmation produced a durable second message; Quit then closed the local port.

C8 scope incident: attempted denied microphone test unexpectedly captured potentially
non-synthetic physical audio and local ASR ran. A potential transcript entered accessibility tool
output. It was not reused as evidence, uploaded to a provider or committed. Exact candidate stopped;
only the affected test root was removed, without file-content reads, after explicit scoped owner
permission. Removal does not erase tool history. Existing real pilot/vault was never inspected or
modified. This is a material scope deviation; the entire run is not called synthetic-only.
C9+ LOCAL_TEST denies physical input at native/page layers; its explicit fixture uses only
bundled authored PCM. All final public evidence is C10 original synthetic metadata.

C11 source review found that the guard only saw a visible recording strip. It now sees a
Boolean covering STARTING/RECORDING/SAVING/in-memory audio draft, independent of visibility.
The legacy panel is hidden in PRIVATE_LOCAL and is characterized by a real fake-device browser
case; native C11 STARTING was refused before backup/pending/feed check. This is not a claim
that hidden legacy capture was reachable in standalone. Current C11 GUI synthetic start stuck
at STARTING twice and was canceled; no physical input, no PASS claim. Actual bundled C11
ASR/lifecycle passed separately. Cycle uses controlled domain-authored notes/message and an
authored WAV through unchanged upload/chunk/finalize methods, not fake ASR. Actual C11
A101→B102 one-click/autorelaunch preserved2 notes/1message/1audio/identity;UI pulses91.
Exact-C11 full1042 PASS with unchanged-assertion failure observer,939.38s;web53 and targeted21
PASS. Prior standard flakes remain reported. Q03 initial C11 script omitted PYTHONPATH and
failed before running; corrected invocation passed, initial log retained. No original failure
or C10 source receipt is relabeled as C11 proof.
