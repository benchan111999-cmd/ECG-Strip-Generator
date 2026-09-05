# Real-data draft workflow

## Scope and source decision

Milestone 3 supports explicitly selected PTB-XL 1.0.3 `records500` records only.
The owner approved using actual PTB-XL leads for the single/two-lead and
twelve-lead candidates on 2026-09-06. This demonstrates the lead-range boundary,
not independent patients or separate rhythm episodes. Multiple views of the
same source record must not be counted as independent examples.

NSRDB is deferred: all 18 officially checksummed headers inspected on
2026-09-06 declare gain zero. The [WFDB header specification](https://physionet.org/physiotools/wag/header-5.htm)
defines zero or absent gain as uncalibrated. Its optional default of 200 is
not independent calibration evidence and is not used here. No NSRDB waveforms
were downloaded. Reconsider this source only after source-grounded calibration
evidence and an explicit owner decision; do not modify its original headers.

## Acquire one complete source group

From the repository root, using the existing locked Python environment:

```console
uv run --locked ecg-strip datasets fetch ptb-xl --file records500/00000/00001_hr.hea --file records500/00000/00001_hr.dat --file ptbxl_database.csv --file scp_statements.csv --file LICENSE.txt
```

Use the returned selection digest in the bundle path below. The example's
selection digest depends on filenames, not file contents; every use still
checks the actual files against the captured publisher checksums.

```text
data/raw/ptb-xl/1.0.3/a821971dd24eedf94945d1ee4a982bd82d8d1611052e88ac8c6d853eea760d74
```

The whole-record `.dat` is acquired, even for a short excerpt. No range download,
partial-file checksum, archive, synthetic fallback or implicit download is used.
Keep all original bytes and acquisition receipts under ignored `data/`.

## Generate drafts

Replace `BUNDLE` with the directory above; choose a new destination each time.

```console
uv run --locked ecg-strip cases draft-ptbxl BUNDLE --record records500/00000/00001_hr --lead II --end-sample 3000 --output output/example-1
uv run --locked ecg-strip cases draft-ptbxl BUNDLE --record records500/00000/00001_hr --lead II --lead V1 --output output/example-2
uv run --locked ecg-strip cases draft-ptbxl BUNDLE --record records500/00000/00001_hr --twelve --output output/example-12
uv run --locked ecg-strip cases audit-draft output/example-12
```

Sample intervals are half-open. Defaults are `[0,5000)` at 500 Hz (10 seconds).
`--start-sample` and `--end-sample` must select consecutive samples within the
record; rhythm strips require at least six seconds, twelve leads exactly ten.
Select 1–6 recorded leads with repeated `--lead`, or the standard twelve with
`--twelve`. Unknown/missing leads fail. No first-channel fallback exists.

The adapter requires a complete, single-file, multiplexed format-16 record,
twelve distinct expected channels, explicit positive ADC gain, baseline and mV
units, and 500 Hz. Timing modifiers, unsupported encodings, incomplete file
lengths, missing sample sentinels and invalid amplitudes fail. Physical samples
are `(ADC - baseline) / gain`; there is no filtering, resampling, padding or
waveform synthesis. The spelling-only mapping `AVR/AVL/AVF` to `aVR/aVL/aVF`
is recorded alongside original header names; no lead identity is inferred.

Source channels are simultaneously acquired. The twelve-lead *presentation*
uses the existing sequential 2.5-second columns plus full 10-second Lead II.
The manifest records both source alignment and displayed sample boundaries.

## Output and authority

```text
output/example-12/
  student/case-<opaque-id>/
    strip.pdf, strip.png, README.md, ATTRIBUTION.txt, LICENSE.txt
  instructor/case-<opaque-id>/
    strip.pdf, strip.png, README.md, ATTRIBUTION.txt, LICENSE.txt, manifest.json
  package-files.json
```

Only the `student/` subtree is a student-facing draft. Never distribute the
whole run directory as a student package. Neutral case IDs derive from source
and view selection, not diagnostic labels. There is no user-supplied title,
prompt or free text on this path. Figures are shared byte-for-byte between
roles; statements and provenance exist only in the instructor subtree.
The source licence and attribution accompany both derivatives. All remain local,
unreviewed drafts, not approved lecture materials or patient-care output.

The instructor manifest is the canonical case record. It includes file URLs,
checksums and classifications, acquisition receipt digest/time, dataset version,
ECG record ID, statement field/codes, original and normalized leads, per-channel
calibration, extraction interval, transformations, display segments, renderer
environment, output digests and attribution. Patient IDs, dates, demographics,
free-text reports and local absolute paths are not exported.

PTB-XL statement codes/likelihoods are copied as source evidence, including zero
values; zero must not be reinterpreted as proof of absence. Record 00001_hr has
`NORM: 100` and is a normal-*candidate*, not a project-approved diagnosis.
Clinical review remains `not_reviewed`; teaching release remains `draft`.
Technical status is `passed` only after this verified-source path and rendering
checks. Physical print measurement remains separately `not_performed`.
The generic JSON renderer still cannot grant source-verified technical status.

Files are generated under a fresh `.draft-*` staging directory, read back against
the exact file allowlist and bytes, then renamed as a complete run. Failed attempts
remain unpublished in staging; existing destinations are never overwritten.
The offline audit checks file inventory, digests, student file surface and draft
review states. This is not an arbitrary-PDF/OCR diagnosis detector or protection
against coordinated rewriting of all local evidence. Keep the dedicated output
parent away from raw data and unrelated concurrent writers.

## Verification

Fast tests generate non-clinical WFDB fixtures and never download datasets.
For real-file checks, set `ECG_PTBXL_BUNDLE` to the verified bundle above, then run:

```console
uv run --locked python -m pytest tests/dataset/test_ptbxl_local.py -q
```

Without that environment variable, these tests explicitly skip. They independently
compare decoded values with WFDB physical output and original little-endian ADC
bytes, and exercise the one-, two- and twelve-lead draft paths. Byte reproducibility
is scoped to the locked runtime/platform. Clinical review and actual 100% print
measurement are still human tasks; neither a source label nor a green test approves them.
