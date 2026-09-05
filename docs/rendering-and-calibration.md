# Rendering and calibration

## Implemented boundary

Milestone 1 renders **unreviewed drafts** from validated physical samples in a
JSON request. It supports one, two, or twelve exact recorded leads, a grid,
calibration pulse, optional title/prompt, PDF, PNG, and an output manifest.
It does not verify a dataset's original files, approve clinical labels, or
create student/instructor teaching packs.

## Reproduce the non-clinical example

From the repository after `uv sync --locked --python 3.12`:

```console
uv run --locked python examples/make_fixture.py --leads 12 --output output/fixture-12.json
uv run --locked ecg-strip render output/fixture-12.json --output output/draft-12
```

Use `--leads 1` or `--leads 2` for the other layouts. Choose a new fixture
filename and output directory each time; existing destinations are never
overwritten. The example's triangles/ramps are deliberately **not ECG rhythms**.
Twelve channels are independent test functions, not a physiological lead model.
These samples and all generated files remain under ignored `output/`.

Each render creates `strip.pdf`, `strip.png`, and `manifest.json`.
A failed filesystem write can leave a partial new directory; only a successful
command with all three files is a complete render bundle. It is still a draft.

## Request and manifest

`RenderRequest` in `models.py` is the input contract. The example produces a
complete JSON request:

- `case`: case ID, source dataset/version/record/reference, declared licence and
  attribution, declared source checksum/kind, evidence class, exclusive sample
  window, and three review statuses.
- `signal`: exact recorded lead names, finite physical samples in sample-major
  order, sampling rate, and `mV`, `uV`, or `V`. ADC counts are unsupported.
- `signal_sha256`: checksum of the canonical, validated signal object.
- `preset`: displayed leads, simultaneous timing, speed, gain, vertical range,
  DPI, and optional plain-ASCII `title`/`teaching_prompt`.

For a programmatically prepared signal, use `provenance.signal_digest(signal)`.
It hashes sorted ASCII JSON with compact separators and one final LF, using
the validated model's numeric representation. This checks the supplied signal,
**not** the declared source-file checksum. Never recompute it just to conceal
an unexpected mismatch.

The output manifest omits raw samples and local paths. It records the source,
window, leads, conversion factor, renderer environment, output checksums,
geometry and PNG metadata. It preserves clinical and teaching status.
`validation.render_checks=passed` is scoped to the render checks;
overall `case.review.technical_validation` stays `not_run` because full
raw-source validation is not implemented. This is not a released case manifest.

Titles/prompts must be neutral and non-identifying. This renderer does not
perform student answer-leak checks. Long visible titles/IDs and prompts are
abbreviated to fit fixed header space; the complete text remains in the manifest.

## Lead, timing and unit rules

Only exact names are accepted: the standard twelve leads plus `MLII` and
`MCL1`. `MLII` is never substituted for `II`. Duplicate, unknown or missing
requested leads fail. Twelve-lead output requires all twelve standard leads;
one-/two-lead sources cannot be expanded.

One-/two-lead rows preserve requested order. Twelve-lead panels are:

```text
I    aVR    V1    V4
II   aVL    V2    V5
III  aVF    V3    V6
```

Every panel shows the **same simultaneous time window**. Sequential columns
are not implemented and are rejected. Samples cover
`[start_sample, end_sample)`; duration is `N / sampling_rate` and the final
plotted point is at `(N - 1) / sampling_rate`. No interpolation, filtering,
resampling, lead inference, or synthetic fallback is performed.

Units convert explicitly to mV: mV × 1, uV × 0.001, V × 1000. Samples outside
the declared vertical range fail instead of being clipped or auto-scaled.
Defaults are 25 mm/s, 10 mm/mV, ±2 mV and 150 DPI.

## Physical geometry

Each panel reserves 16 mm for labels/calibration before the waveform.
The pulse is exactly **1 mV high and 0.2 seconds wide**. Let duration be D,
paper speed S, gain G, vertical amplitude limit A, rows R and columns C:

- waveform width = D × S mm;
- panel width = 16 + D × S mm;
- panel height = 2 × A × G + 8 mm;
- page width = max(86, 20 + C × panel width + (C - 1) × 8) mm;
- page height = 42 + R × panel height + (R - 1) × 8 mm.

The 86-mm minimum preserves annotation space without stretching the waveform.
One/two leads use one column; twelve leads use three rows and four columns.
PDF page points are millimetres × 72 / 25.4. No tight bounding box or automatic
layout is used. Encoded PDF page size and PNG dimensions are checked before
writing; tests also inspect actual PDF calibration-pulse paths and figure
transforms. Windows must be 0.5–30 seconds, speed 12.5–50 mm/s, gain 5–20 mm/mV,
vertical amplitude limit 1.5–5 mV, and DPI 72–300. Pages over 1500 mm wide or
40 million pixels are rejected.

PDF geometry is numerically verified. **Manual print calibration remains
unperformed**: print at 100%, disable fit-to-page, and measure both axes before
claiming physically calibrated release. Large custom pages require suitable
paper/printer handling; reducing them to A4 changes the scale.

PNG is for display only. It carries duration, sampling rate, DPI, pixels/second,
pixels/mV and `physical_mm_accuracy=false`. Raster dimensions are integer
pixels, so subpixel positions are quantized; a screen does not promise physical
millimetres.

## Reproducibility and verification

Run `uv run --locked python -m pytest tests`. Tests cover invalid metadata and
sample shapes, exact lead selection, three unit conversions, all three layouts,
actual PDF page/pulse geometry, PNG encoding, amplitude rejection, refusal to
overwrite, and different-process byte equality.

The same validated input and preset produce identical PDF, PNG and manifest
bytes within the same locked Python/library/platform environment. Plot styles
are isolated, the bundled DejaVu Sans font is selected, path simplification is
disabled, and PDF dates are omitted. Cross-platform or upgraded-library byte
identity is not promised; the manifest records the render environment.
Rendering calls are sequential; Matplotlib global style contexts are not a
thread-safe concurrent service.

Clinical review, source audit, student/instructor separation, and physical
print measurement remain separate later checks.
