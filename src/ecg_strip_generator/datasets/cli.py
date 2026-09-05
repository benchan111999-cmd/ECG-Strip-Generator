"""Dataset CLI wiring; audit never downloads."""

import json
from http.client import HTTPException
from pathlib import Path
from typing import Annotated

import typer

from ecg_strip_generator.datasets.registry import attribution, load_registry
from ecg_strip_generator.datasets.storage import audit, fetch

app = typer.Typer(
    help="Review sources and acquire explicitly selected files.", no_args_is_help=True
)


@app.command("audit")
def audit_command(
    data_root: Annotated[Path, typer.Option("--data-root")] = Path("data"),
) -> None:
    """Validate registry and local bundle bytes offline; no clinical validation."""
    results = []
    failed = False
    for dataset in load_registry().values():
        try:
            results.append(audit(dataset, data_root))
        except (ValueError, OSError) as exc:
            results.append({"dataset": dataset.id, "local_status": "failed", "error": str(exc)})
            failed = True
    typer.echo(json.dumps(results, indent=2))
    if failed:
        raise typer.Exit(1)


@app.command("fetch")
def fetch_command(
    dataset: Annotated[str, typer.Argument()],
    files: Annotated[list[str], typer.Option("--file", help="Exact relative path; repeatable.")],
    data_root: Annotated[Path, typer.Option("--data-root")] = Path("data"),
) -> None:
    """Fetch a subset; no recursion, archives, auto-retry or raw overwrite."""
    try:
        registry = load_registry()
        if dataset not in registry:
            raise ValueError("Unknown dataset identifier")
        bundle = fetch(registry[dataset], files, data_root)
    except (ValueError, OSError, HTTPException) as exc:
        typer.echo(f"Fetch failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Verified subset: {bundle.name}. Clinical review remains pending.")


@app.command("attribution")
def attribution_command(
    dataset: Annotated[str, typer.Argument()],
    changes: Annotated[str, typer.Option("--changes")],
) -> None:
    """Print source notice with an explicit description of changes."""
    registry = load_registry()
    if dataset not in registry:
        raise typer.BadParameter("Unknown dataset identifier")
    if not changes.strip():
        raise typer.BadParameter("Describe actual changes")
    typer.echo(attribution(registry[dataset], changes))
