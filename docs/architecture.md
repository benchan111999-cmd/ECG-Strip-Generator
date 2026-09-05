# Architecture

## Implemented modules

- `models.py` owns immutable, extra-field-rejecting Pydantic request contracts.
- `validation.py` verifies the signal checksum, selects exact channels, converts
  physical units to mV, and rejects clipping/invalid windows.
- `provenance.py` owns canonical JSON and SHA-256 encoding.
- `rendering/geometry.py` owns physical page and panel dimensions.
- `rendering/matplotlib_renderer.py` draws fixed geometry and writes draft PDF,
  PNG and manifest bundles.
- `cli.py` validates the JSON request and reports errors without falling back.
- `datasets/registry.py`, `storage.py` and `transport.py` own pinned source
  metadata, verified immutable acquisitions and constrained HTTPS downloads.
- `datasets/wfdb_adapter.py` owns explicit calibration and consecutive digital
  decoding; `datasets/ptbxl.py` owns source metadata selection and privacy filtering.
- `teaching_packages.py` owns separated draft exports and readback; `cases_cli.py`
  wires the offline workflow. It reuses, rather than replaces, the renderer.
- `examples/make_fixture.py` provides non-clinical verification input only.

See [rendering and calibration](rendering-and-calibration.md) for the input
format and measurable guarantees. The approved plan still governs future
additional source loaders, selection, synthetic teaching recipes and release packages.

## Canonical records

The case manifest owns the independent evidence/review axes. Render-only checks
are scoped separately and cannot upgrade whole-case technical validation,
clinical review or teaching release. A future SQLite catalog is a derived view.
The PTB-XL draft builder alone records passed technical status after verified raw
loading and rendering; its instructor manifest is canonical. The renderer's
provisional not-run manifest is replaced only inside unpublished draft staging.
No source metadata or SQLite record is an alternative approval authority.
Obsidian owns project progress; Git owns code history; Hindsight holds compact
working context.

## Local storage and effects

Rendering consumes a fully specified JSON request and makes no network request.
Validation and encoding complete in memory before a new output directory is
created. Existing output directories are rejected. A filesystem failure may
leave an incomplete new directory; it must not be treated as a complete bundle.

`data/staging` and `data/raw` implement verified acquisition; `data/derived` and
`data/catalog` remain reserved local-only paths. Raw bytes are never modified.
Drafts use separate student/instructor subtrees under a new output run, staged
and checked before atomic visibility. See [real-data drafts](real-data-drafts.md)
for source, privacy and failure boundaries. No service, database or deployment is added.
