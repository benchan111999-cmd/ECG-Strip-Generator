# SVDB 840 dual-channel transition review

## Scope and evidence

Reviewed original ECG1/ECG2, samples [79758,88718), 623.109375–693.109375 s, including the requested [83598,84878) strip and 30 seconds on either side. Official subset receipt was reverified. Seven consecutive 10-second project-decoder windows independently matched WFDB physical samples to absolute tolerance 1e-12 mV. No filtering, resampling, or signal editing. Sample rate 128 Hz; lead identities beyond ECG1/ECG2 are unspecified.

Reviewer artifacts: `output/candidate-review-2026-09-11/svdb840-transition-review/`: `dual-channel-10s.png`, `context-70s.png`, `before-middle-after.png`, and `evidence.json`. Context plots explicitly offset channels vertically; detail plots use original mV. Numbers are beat identifiers, not P-wave labels. In evidence.json, source metadata is from the final verified 10-second chunk; context_beats and the stated scope above cover the complete 70 seconds.

## Findings

- Verified timing change: selected early strip interval 0–3 s has median-RR rate approximately 140/min, middle 3–8 s approximately 120/min, and late 8–10 s approximately 149/min. These are descriptive interval choices, not adjudicated rhythm boundaries. Within-strip middle RR intervals vary approximately 414–539 ms.
- All 22 source beats within the original strip remain S. Across the context there are 41 consecutive S beats from sample 83131 (649.461 s) through 85344 (666.750 s). Preceding N is at 649.008 s; next N is at 667.914 s. These are beat timestamps, not exact onset/termination boundaries.
- Outside the rapid run, median-RR rates are approximately 78/min in 623–648 s and 82/min in 668–693 s. Thus these flanking reference segments are not sinus tachycardia on rate grounds. N labels alone do not establish sinus origin.
- Visual review: rapid-run middle segment does not show a sufficiently clear, reproducible return to the same pre-QRS atrial morphology seen/suspected in the flanking slower reference, with a demonstrable stable PR across both channels. Small atrial deflections remain difficult to separate from ST–T and noise; no reliable manual P-onset/PR measurements are asserted.

## Interpretation boundary

Confirmed: real rate modulation within a narrow-looking rapid run; slower N-labelled rhythm before and after. Not established: non-sinus NCT -> sinus tachycardia -> non-sinus NCT inside the original ten seconds. Source S labels and uncertain P morphology do not prove the proposed conversion; labels can be imperfect and are not used as an absolute exclusion. No specific mechanism or absence of P waves is diagnosed.

Retain as a discussion case about P-wave evidence and rate-versus-mechanism, not a definitive ST-conversion answer key. A longer context showing the rapid run's beginning/end is a stronger comparison candidate, still requiring human clinical review. Owner-approved objective remains distinguishing sinus from non-sinus narrow-QRS tachycardia; the two MITDB209 examples retain their proposed sequence. No clinical-release status changed.

## Verification and limitation

First 70-second project-decoder request correctly failed its existing 30-second limit; verification was repeated in seven 10-second chunks without changing that limit. Source checksum + independent waveform decoding and visual review support data integrity, not rhythm-mechanism certainty. Clinical conversion claim: narrowing only.
