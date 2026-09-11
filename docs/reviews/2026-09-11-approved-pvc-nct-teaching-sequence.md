# Owner-selected PVC and NCT teaching sequence

## Final session decision

The owner selected MITDB 119 target 42126 as the beginner PVC example and approved the following three-strip teaching sequence. This decision supersedes earlier candidate notes that treated SVDB 840 only as an unsuitable replacement for a clean regular-NCT introductory strip. It is useful for a different, explicitly uncertainty-aware learning objective.

Objective: distinguish sinus from non-sinus narrow-QRS tachycardia. Sinus tachycardia is itself within the NCT umbrella; do not present NCT and ST as mutually exclusive categories.

| Sequence | Exact existing artifact | Intended learning message |
| --- | --- | --- |
| 1 | `output/candidate-review-2026-09-11/mitdb209-cleaner-package/student/case-4b9e906f0b6e6ea7/strip.png` | Cleaner beginner example: recognize rapid narrow complexes and inspect atrial activity. |
| 2 | `output/candidate-review-2026-09-11/mitdb209-package/student/case-25717c7e542ef962/strip.png` | NCT with superimposed artifact: distinguish noise from cardiac activity; not seeing a P wave does not prove its absence. |
| 3 | `output/candidate-review-2026-09-11/svdb840-alternative-package/student/case-cd7f2bf3bac107f3/strip.png` | Track suspected P waves separating from T waves as rate changes; consider altered underlying rhythm without forcing a definitive diagnosis. |

The order is pedagogical, not chronological or a continuous recording. The first two are different time windows of MITDB 209; the third is a different source record. Do not imply one patient or one continuous event across all three.

## Third-strip discussion boundary

The owner marked repeated pre-QRS deflections as suspected P waves and considers the brief middle segment useful for discussing possible rhythm change. The learning value does not depend on proving non-sinus NCT -> ST -> non-sinus NCT.

- P waves may be hidden within ST-T or other waveform components; visible P waves are not incompatible with NCT.
- Apparent P-T separation can prompt reassessment. It may reflect changed rhythm or improved visibility with slower rate; this strip does not settle the distinction.
- AT, MAT and ST may be discussed as differential possibilities, not established diagnoses or equally supported findings. Do not diagnose MAT without its required atrial morphology and rhythm evidence.
- The original ten seconds contain 22 S-labelled source beats. Dual-channel and 70-second context review confirms rate modulation but does not establish an intervening sinus mechanism. Keep original labels and uncertainty intact.

## Adenosine teaching extension

For an appropriate regular narrow-complex tachycardia, after assessing stability, clinical context and contraindications, adenosine may transiently block AV conduction and expose atrial activity, assisting diagnosis; it may also terminate AV-node-dependent tachycardia. It is not a universal diagnostic test for every unclear NCT and does not guarantee a definitive diagnosis. Do not automatically apply the regular-NCT pathway to suspected MAT or another irregular rhythm. Obtain and review a 12-lead ECG and longer rhythm recording when feasible; instability requires the appropriate urgent pathway rather than delaying care to obtain a teaching diagnosis.

Guideline reference: [AHA 2025 Adult Advanced Life Support](https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-advanced-life-support), regular narrow-complex tachycardia section. This discussion does not claim adenosine was administered in this source recording.

## Status and next step

Owner-approved asset selection and teaching intent are recorded here. Existing clinical-review and release fields remain unchanged; no final mechanism approval, student release, deck production or physical-print approval is inferred. Raw files, rendered strips and the owner's arrow-marked screenshot are not included in Git. Source coordinates and local artifact references remain in the review records.

This session is candidate selection and teaching-review work, not completion of the full M5 AFDB/VFDB implementation. Next: carry the accepted examples and uncertainty-aware sequence into subsequent case packaging/review, and resume the approved M5 scope separately. Remote push requires separate approval.
