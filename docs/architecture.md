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
- `examples/make_fixture.py` provides non-clinical verification input only.

See [rendering and calibration](rendering-and-calibration.md) for the input
format and measurable guarantees. The approved plan still governs future
source loaders, selection, synthetic teaching recipes and teaching packages.

## Canonical records

The case manifest owns the independent evidence/review axes. Render-only checks
are scoped separately and cannot upgrade whole-case technical validation,
clinical review or teaching release. A future SQLite catalog is a derived view.
Obsidian owns project progress; Git owns code history; Hindsight holds compact
working context.

## Local storage and effects

Rendering consumes a fully specified JSON request and makes no network request.
Validation and encoding complete in memory before a new output directory is
created. Existing output directories are rejected. A filesystem failure may
leave an incomplete new directory; it must not be treated as a complete bundle.

`data/staging`, `data/raw`, `data/derived`, and `data/catalog` remain
local-only and unimplemented. Future downloads must be verified before promotion;
raw data is immutable. Future student/instructor packages will use separate roots.
