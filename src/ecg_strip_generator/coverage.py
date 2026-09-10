"""Offline coverage projection of audited M4 drafts; never an approval authority."""

import json
from pathlib import Path
from typing import Annotated

import typer

from ecg_strip_generator.datasets.annotations import CATEGORIES
from ecg_strip_generator.models import CaseManifest
from ecg_strip_generator.teaching_packages import audit_draft

app = typer.Typer(no_args_is_help=True)


def report(packages: list[Path]) -> dict:
    cases = {category: set() for category in CATEGORIES}
    for package in packages:
        audit = audit_draft(package)
        path = package / "instructor" / audit["case_id"] / "manifest.json"
        manifest = json.loads(path.read_bytes())
        case = CaseManifest.model_validate(manifest["case"])
        if case.source.dataset not in {"mitdb", "svdb", "incartdb"}:
            raise ValueError("Coverage accepts only audited Milestone 4 source drafts")
        statement = manifest["source_provenance"]["statement"]
        if statement["status"] != "candidate" or statement["category"] not in cases:
            raise ValueError("Unsupported coverage evidence")
        cases[statement["category"]].add(case.case_id)
    return {
        "scope": "explicitly supplied, locally audited M4 draft packages only",
        "clinical_approval_inferred": False,
        "release_workflow_implemented": False,
        "categories": [
            {
                "category": name,
                "status": "candidate" if ids else "gap",
                "candidate_count": len(ids),
                "released_count": 0,
                "case_ids": sorted(ids),
            }
            for name, ids in cases.items()
        ],
        "limitations": "Candidates are not released coverage. Narrow-complex candidates are "
        "rapid beat-run screening targets; QRS width, sustained rhythm and mechanism need review. "
        "Release-state edits are rejected, not counted as approval. "
        "Unlisted cases are not audited.",
    }


@app.command("report")
def report_command(
    package: Annotated[list[Path] | None, typer.Option("--package")] = None,
) -> None:
    """Print candidate counts and honest gaps; never download or change case review."""
    try:
        result = report(package or [])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        typer.echo("Coverage rejected: an input package or its evidence is invalid.", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2))
