# SVDB 800: possible aberrantly conducted PAC

Review date: 2026-09-11. Owner-approved discussion label:
**Possible aberrantly conducted PAC** (not a confirmed mechanism).

## Identity and source

SVDB 1.0.0, record 800, target sample 61322 at 128 Hz.
Original case: case-143079c509039e1b; six-second window [60938,61706).
Recorded channels: ECG1/ECG2; exact standard lead identities unconfirmed.
The original reference annotation is V and is preserved, not corrected to A.
This review is a separate human interpretation; original draft manifests remain unchanged.

## Observations and measured reference points

- A small pre-QRS positive deflection is visible in ECG2, identified by the owner
  as a possible abnormal P wave.
- The target QRS appears broader than adjacent beats. ECG1 has a dominant negative
  component with oppositely directed ST-T appearance. No definitive QRS duration
  was established; morphology alone does not settle the origin.
- ECG1 positive R-peak samples: 60863, 60955, 61049, 61141, 61235,
  61326 (target), 61429, 61527.
- Four preceding R-R intervals: 718.75, 734.375, 718.75, 734.375 ms;
  mean 726.5625 ms. Target coupling interval 710.9375 ms, next interval
  804.6875 ms, then 765.625 ms. Coupling plus next interval: 1515.625 ms.
- Source beat annotations instead give 695.3125/820.3125 ms around the target.
  These are different fiducial points and must not be mixed with R peaks.
- Tentative ECG2 P-peak samples: 60841, 60933, 61026, 61120, 61213,
  61309 (target-associated deflection), 61407.
- Preceding P-peak intervals: 718.75, 726.5625, 734.375, 726.5625 ms;
  target-associated interval 750 ms, next interval 765.625 ms.
- Tentative P-onset ranges: preceding 61210-61211; target 61305-61307;
  following 61402-61404. Resulting onset intervals approximately
  734-758 ms and 742-773 ms. These are manual selection ranges, not confidence intervals.

## Interpretation boundaries

Raw samples were not filtered, smoothed or baseline-shifted.
Sampling interval is 7.8125 ms. Low-amplitude onset ambiguity limits precision.
Atrial prematurity and causal P-to-QRS conduction are unconfirmed.
True PR and QRS duration could not be reliably established. Short PR/low atrial
origin remains a hypothesis, not a measured or localized finding.
Do not infer a precise full compensatory pause from the interval sums.

## Teaching disposition

Retain for advanced PVC-versus-aberrant-conduction discussion under the possible
PAC label requested by the owner. Exclude from the beginner typical-PVC set.
No teaching release or diagnostic certainty is implied.
Generated figures remain local under ignored output/milestone-4/:
disputed-61322-detail.png, disputed-61322-pp-review.png,
disputed-61322-onsets.png and disputed-61322-context/.

## Related review decisions

MITDB 100 excerpts targeting 66792 and 74986 were accepted by the owner as PAC
demonstration and independent practice respectively. They are not independent
patients. Clarity/no cropping accepted; physical millimetre measurements were
not performed and are not a prerequisite for continuing this review per owner.
Use in-image scale references; do not claim physical print calibration verified.
A clean typical PVC and a real narrow-complex tachycardia example remain to select.
