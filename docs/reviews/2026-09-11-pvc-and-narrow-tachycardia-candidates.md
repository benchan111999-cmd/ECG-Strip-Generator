# PVC and narrow-complex tachycardia candidates

Date: 2026-09-11. Reviewer drafts only; clinical approval and teaching release pending.

## Scope

The owner requested entry into M5 and clearer typical PVC / genuine narrow-complex
tachycardia examples. This checkpoint addresses those two remaining M4 candidate
gaps first. The plan's full M5 AFDB/VFDB adapters and transition support are not
implemented by this candidate search.

## Preferred PVC: MITDB 100

- Source version 1.0.0; reference beat V at sample 546792, 360 Hz.
- Ten-second window [545352, 548952), MLII and V5.
- Both channels show a conspicuous premature ventricular-annotated complex with
  morphology distinct from surrounding beats. Cleaner than the inspected INCART
  I01 sample 5263 window; SVDB 800 sample 61322 remains excluded as a typical PVC.
- Previous N at 546599 and next N at 547199: annotation intervals 536.1 ms and
  1130.6 ms. Their sum is 1666.7 ms. These are annotation-coordinate intervals,
  not manually located R-peak or atrial timing measurements; no automatic claim
  of an exactly compensatory pause.
- Display range explicitly +/-4 mV because the source dips below -2 mV; gain
  stays 10 mm/mV. No clipping, filtering, baseline shift or resampling.
- Local artifact: output/candidate-review-2026-09-11/mitdb-100-546792/strip.png
  (with PDF, render manifest and source-evidence.json).

## Preferred narrow-complex candidate: MITDB 209

- Source version 1.0.0; newly acquired only 209.hea, 209.dat and 209.atr through
  the existing staged fetch and official SHA-256 verification workflow.
- Source rhythm labels delimit SVTA [200042, 210347), about 28.625 seconds.
- Selected ten-second window [201600, 205200), 560-570 seconds at 360 Hz,
  entirely within that labelled episode. All 26 beat annotations are A.
- Median annotation RR is 136 samples (377.8 ms), giving approximately 158.8 bpm.
- MLII is clearer than V1. The source waveform shows repeated narrow complexes;
  a visual estimate on the unfiltered MLII detail at sample 203072 is roughly
  60-70 ms (approximately -25 to +35/40 ms relative to the beat marker).
  This is an agent visual estimate, not a validated delineator or human-approved
  interval; inspect the complete waveform and confirm before teaching release.
- Mechanism-neutral proposed label: narrow-complex tachycardia, source SVTA.
  No AVNRT/AVRT diagnosis, atrial mechanism, onset or termination demonstration
  is inferred from this established-rhythm strip.
- A standard single-MLII student/instructor draft is available under
  output/candidate-review-2026-09-11/mitdb209-package/.
- Two-channel reviewer reference: output/candidate-review-2026-09-11/mitdb-209-203072/.

## Compared but not preferred

- SVDB 801: N/S rapid run [4655, 6186] spans 11.96 seconds; inspected [4608,5888).
  Marked morphology variation/artifact and baseline movement make this less
  straightforward than MITDB 209. Preserve ECG1/ECG2 names and source S labels.
- INCART I01: V at 5263, inspected [4480,7050), II/V1/V5; baseline drift and
  noise reduce clarity. INCART annotation locations are not manually corrected.

## Verification and reproduction

All selected bundles passed verify_bundle against registered sources before and
after rendering. Every reviewer window was independently read with wfdb.rdrecord
and compared to the project decoder at absolute tolerance 1e-12 mV, zero relative
tolerance. Source and rendered samples are consecutive and unfiltered. Renderer
checks enforce geometry and amplitude; packages remain drafts.

From the repository root, use the locked project environment:

    uv run --no-sync python scripts/review/scan_candidates.py
    uv run --no-sync python scripts/review/render_candidates.py
    uv run --no-sync python scripts/review/measure_candidates.py

The renderer script skips already existing candidate destinations; the scanner
and measurement script are local review helpers, not general selection algorithms.
QRS detail: output/candidate-review-2026-09-11/qrs-review.png.
Original datasets and generated artifacts remain ignored by Git.

## Source references

- https://physionet.org/content/mitdb/1.0.0/
- https://physionet.org/physiobank/database/html/mitdbdir/records.htm#100
- https://physionet.org/physiobank/database/html/mitdbdir/records.htm#209
- https://physionet.org/content/svdb/1.0.0/

Keep dataset attribution with derivatives. No public push or teaching release
was performed. Full M5 remains separate work.
