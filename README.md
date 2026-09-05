# ECG Strip Generator

ECG Strip Generator is a standalone tool-development subproject of ECG Course.

## Status

Milestone 0 provides a Python project skeleton, runtime-report command, and
development checks. ECG rendering, dataset handling, and reviewed teaching
packages are not implemented yet. See the
[approved execution plan](docs/plans/2026-09-05-ecg-strip-generator-revised-execution-plan.md).

This tool is for personal, non-commercial education only, not patient care,
diagnosis, formal institutional operations, or paid courses.

## Setup

Install uv separately, then run from this repository:

```console
uv sync --locked --python 3.12
uv run --locked ecg-strip --version
uv run --locked ecg-strip doctor
```

uv uses an isolated `.venv` and Python 3.12; do not install these dependencies
into system Python. `uv.lock` pins the resolved environment. Setup downloads
Python if needed and package dependencies, but no ECG datasets.

`doctor` reports runtime identity only. It does not certify dataset availability,
clinical correctness, or rendering calibration.

## Development checks

```console
uv run --locked python -c "import ecg_strip_generator"
uv run --locked python -m pytest tests/unit
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Fast tests require no external datasets. Later dataset tests must never download
data implicitly.

## Documentation

- [Architecture](docs/architecture.md)
- [Clinical safety](docs/clinical-safety.md)
- [Data sources](docs/data-sources.md)
- [Rendering and calibration](docs/rendering-and-calibration.md)

## Language

English is the primary project language. zh-HK wording may be added when it improves local usability.

## Development workflow

- The current workflow uses `main` for single-developer work.
- Keep changes focused and run relevant checks before committing.
- Verified milestones within the approved plan may be committed locally automatically.
- Every remote push still requires separate project-owner approval.

## Privacy and publishing

This is a public repository. Do not add patient-identifiable information, student names, exam answers, secrets, API keys, tokens, credentials, or unreviewed private teaching material.

Original source files must be preserved, and their provenance must remain clear. Do not rename, move, or delete original source files without explicit approval.

Local data (`data/`), generated output (`output/`), environments, and caches are
ignored by Git. Do not commit raw recordings or private answer keys.

## Code licence

No project code licence has been selected or granted. Do not infer a licence
from the public repository or the personal-use scope. Dataset and dependency
licences are separate and retain their own terms.

## Deployment

No deployment platform is configured yet.

## Project dashboard

Project progress is tracked in the owner's Obsidian project dashboard.
