# Architecture

## Current implementation

Milestone 0 supplies an installable Python 3.12 package and the `ecg-strip`
command. `doctor` reports runtime identity and explicitly discloses missing
capabilities. It does not inspect datasets, render signals, or approve cases.

## Planned boundaries

Follow the [approved execution plan](plans/2026-09-05-ecg-strip-generator-revised-execution-plan.md).
Future modules will separate source loading, manifest validation, deterministic
rendering, and teaching packages. Create each module only in its milestone.

## Canonical records

Per-case manifests will own the four independent evidence/review axes. A future
SQLite catalog is a derived view. Obsidian owns project progress; Git owns code
history; Hindsight holds compact working context.

## Local storage

`data/staging`, `data/raw`, `data/derived`, and `data/catalog` are local-only.
Future downloads must be verified before promotion; raw data is immutable.
`output/student` and `output/instructor` will remain separate, ignored roots.
