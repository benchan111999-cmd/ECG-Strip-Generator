# Cleaner NCT candidate follow-up

## Owner selection

The owner agreed to use MITDB 119, target sample 42126, as the beginner PVC example. This records asset selection, not an automatic clinical-release approval; existing draft manifests remain unchanged.

## NCT refinement

- The owner identified baseline artifact in the original MITDB 209 window (560–570 s) as distracting for beginners.
- Compared seven unfiltered MLII windows from source-annotated SVTA episodes using `scripts/review/compare_nct_windows.py`.
- Proposed replacement: MITDB 209, samples [266000, 269600), 738.889–748.889 s, MLII, 360 Hz. Reference beat: A at sample 267423. The complete window lies within source SVTA annotations [264111, 269683).
- Original consecutive physical samples; no smoothing, filtering, resampling, or waveform editing. Standard 25 mm/s and 10 mm/mV.
- Visual review: less rapid baseline fluctuation than the previous window, with clear narrow complexes. Some baseline ripple and amplitude variation remain. This is a qualitative comparison, not a validated signal-quality score.
- 27 source A beats in the window; median RR 136 samples, approximately 159/min. Source beat and rhythm labels do not independently prove QRS width or a specific tachycardia mechanism.
- Draft: `output/candidate-review-2026-09-11/mitdb209-cleaner-package/student/case-4b9e906f0b6e6ea7/strip.png` (PDF alongside). Original package preserved.
- Draft audit: output checksums passed; clinical review remains not_reviewed. Owner selection of this NCT replacement remains pending.
- AHA 2025 adult tachyarrhythmia algorithm uses QRS >=0.12 s for the wide-complex branch and explicitly refers to regular narrow-complex rhythms. This supports terminology, not adjudication of this individual strip: https://cpr.heart.org/-/media/CPR-Files/CPR-Guidelines-Files/2025-Algorithms/Algorithm-ACLS-Tachycardia-250514.pdf

Internal candidate review only. Source attribution and licensing remain in the generated package. No publication, milestone completion, commit, or remote push implied.
