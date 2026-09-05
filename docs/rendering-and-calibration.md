# Rendering and calibration

## Implemented boundary

The renderer creates **unreviewed drafts** from validated physical samples:
one/two-lead rhythm rows or a twelve-lead **3 × 4 + Lead II rhythm strip**.
Outputs are PDF, PNG and a provenance manifest. Source-file verification,
clinical approval and student/instructor teaching packages are still pending.

## Reproduce the non-clinical example

After `uv sync --locked --python 3.12`, run:

```console
uv run --locked python examples/make_fixture.py --leads 12 --output output/fixture-12.json
uv run --locked ecg-strip render output/fixture-12.json --output output/draft-12
```

Use `--leads 1` or `--leads 2` for two-second one-/two-lead examples.
The twelve-channel example supplies ten seconds. Its triangle/ramp functions
are deliberately **not ECG rhythms or a physiological lead model**.

Choose new filenames/directories; existing destinations are never overwritten.
Each successful render creates `strip.pdf`, `strip.png`, and
`manifest.json`. A filesystem error can leave a partial new directory; only
all three files plus a successful command constitute a complete draft bundle.

## Continuous twelve-lead print layout

Owner clarification on 2026-09-05 replaces the initial isolated, simultaneous
panels. All twelve input channels must be present for the **same continuous
10-second window**. Upper rows use sequential quarter-window excerpts:

| Row | 0–2.5 s | 2.5–5 s | 5–7.5 s | 7.5–10 s |
|---|---|---|---|---|
| 1 | I | aVR | V1 | V4 |
| 2 | II | aVL | V2 | V5 |
| 3 | III | aVF | V3 | V6 |
| 4 | **Lead II continuously across all 10 seconds** | | | |

The x-axis advances continuously across each row. There are no internal panel
gutters or per-lead calibration blocks. Rows share a continuous grid. Different
lead excerpts remain separate paths: no artificial line interpolates across a
lead switch. The normal one-sample interval at a switch does not become blank
panel space.

The bottom rhythm strip uses every original Lead II sample over the window;
it is never assembled from repeated short snippets. Missing II, shorter/longer
than ten-second input, and requests for the retired simultaneous twelve-panel
layout fail explicitly. Select a ten-second source window before rendering;
the renderer never silently crops, pads, repeats, or resamples.

Set `preset.time_alignment="sequential"` for twelve-lead output.
One-/two-lead rows retain `"simultaneous"` timing and requested order.
Previously saved twelve-lead requests must be regenerated with ten seconds and
the new timing value; they are not silently reinterpreted.

## Calibration

Every row, including the bottom Lead II row, has **one** calibration pulse.
`preset.calibration_position` accepts `"right"` (default, matching the owner's
reference) or `"left"`. The pulse is 1 mV high and 0.2 seconds wide.

A 16-mm gutter at the chosen row edge reserves calibration space outside the
recorded duration. It does not consume any of the ten seconds. No calibration
markers are inserted at internal lead boundaries.

## Request and manifest

`RenderRequest` in `models.py` owns the input contract:

- `case`: neutral case ID; source dataset/version/record/reference; declared
  licence, attribution and source checksum/kind; evidence class; exclusive
  sample window; independent technical, clinical and teaching statuses.
- `signal`: exact recorded leads, finite sample-major physical values,
  sampling rate, and `mV`, `uV`, or `V`. ADC counts are unsupported.
- `signal_sha256`: checksum of the canonical validated signal.
- `preset`: displayed leads, timing mode, calibration position, speed/gain,
  vertical range, DPI, and optional plain-ASCII `title`/`teaching_prompt`.

Use `provenance.signal_digest(signal)` to hash sorted ASCII JSON with compact
separators and one final LF using the validated numeric representation. This
checks the supplied values, **not** the declared original source-file checksum.
Never recompute a digest to conceal an unexpected mismatch.

The output manifest omits raw samples/local paths and records conversion,
renderer environment, geometry, PNG metadata and output checksums.
`display_segments` records each row/lead, intended relative time interval,
relative sample indices and absolute source indices; the full rhythm strip is
identified by `role="rhythm"`.

All sample intervals are half-open. For sampling rates that do not divide a
2.5-second boundary exactly, the next column begins at the first sample at or
after that boundary. Samples retain their original times; no boundary sample
is duplicated or shifted.

`validation.render_checks=passed` is scoped to drawing checks. Overall
`case.review.technical_validation` stays `not_run` while original-source
verification remains unavailable; clinical review and teaching release remain
unreviewed/draft. Titles/prompts must be neutral and non-identifying; these
bundles have not passed student answer-leak checks. Long visible labels are
abbreviated to fit; the complete text stays in the manifest.

## Lead and unit rules

Supported exact names are the standard twelve leads plus `MLII` and `MCL1`.
MLII is never substituted for II. Missing, duplicate or unknown leads fail.
One-/two-lead sources cannot be expanded into twelve leads.

Unit conversion to mV is explicit: mV × 1, uV × 0.001, V × 1000.
Values outside the declared vertical range fail instead of being clipped or
auto-scaled. No interpolation, filtering, lead inference, or synthetic fallback
is applied. The final plotted sample is at `(N - 1) / sampling_rate`.

## Physical geometry

For duration D, speed S, gain G, amplitude limit A and row count R:

- waveform width = D × S mm;
- row width = 16 + D × S mm, including the single edge calibration gutter;
- row height = 2 × A × G + 8 mm;
- page width = max(86, 20 + row width) mm;
- page height = 42 + R × row height + (R - 1) × row gap mm.

Twelve-lead output uses four rows with zero inter-row gap. One/two leads use
one/two rows and an 8-mm row gap. Grid lines are globally aligned even when row
height is not a multiple of five millimetres.

Defaults: 25 mm/s, 10 mm/mV, ±2 mV, 150 DPI. The twelve-lead test example
explicitly uses ±1.5 mV, making its PDF 286 × 194 mm without changing waveform
scale. The supported amplitude limit is 1.5–5 mV; choose an explicit larger
range if necessary. Larger ranges create taller pages and may require larger
paper. One-/two-lead windows support 0.5–30 s; twelve leads require exactly 10 s.
Speed 12.5–50 mm/s, gain 5–20 mm/mV and DPI 72–300 are supported.
Pages above 1500 mm wide or 40 million pixels fail.

PDF page points equal millimetres × 72 / 25.4. No tight bounding box or automatic
layout rescaling is used. Encoded page/pixel dimensions are checked before writes.
Tests independently inspect encoded PDF pulse dimensions/positions, actual plot
transforms, waveform sample values and timing, and shared grid alignment.

**Manual print calibration remains unperformed.** Print at 100% with
fit-to-page disabled and measure both axes before claiming calibrated release.

PNG carries duration, sampling rate, timing mode, DPI, pixels/second and
pixels/mV with `physical_mm_accuracy=false`. Integer pixels quantize positions;
screens do not promise physical millimetres.

## Reproducibility

Run `uv run --locked python -m pytest tests`.
The same validated request/preset produces identical PDF, PNG and manifest bytes
within the locked runtime/platform, including fresh-process twelve-lead runs.
Styles are isolated, DejaVu Sans is selected, path simplification is disabled,
and PDF dates are omitted. Cross-platform or library-upgrade byte identity is
not promised; the manifest records the environment and renderer version.

Renderer version 2 retires the independent twelve-panel layout. Rendering is
sequential; Matplotlib style contexts are not a concurrent service.
