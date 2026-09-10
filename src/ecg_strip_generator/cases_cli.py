"""Explicit offline PTB-XL draft selection; acquisition remains a separate command."""

from pathlib import Path
from typing import Annotated

import typer

from ecg_strip_generator.models import STANDARD_LEADS

app = typer.Typer(
    no_args_is_help=True, help="Verified-source draft candidates; no clinical release."
)


@app.command("audit-draft")
def audit_command(output: Annotated[Path, typer.Argument()]) -> None:
    """Check saved draft bytes against their local inventory, not clinical accuracy."""
    import json

    from ecg_strip_generator.teaching_packages import audit_draft

    try:
        result = audit_draft(output)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        typer.echo("Draft audit failed; package is incomplete, changed or invalid.", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2))


@app.command("draft-ptbxl")
def draft_ptbxl(
    bundle: Annotated[
        Path, typer.Argument(help="Verified raw bundle, including metadata/licence.")
    ],
    record: Annotated[str, typer.Option("--record")],
    output: Annotated[Path, typer.Option("--output")],
    lead: Annotated[list[str] | None, typer.Option("--lead")] = None,
    twelve: Annotated[bool, typer.Option("--twelve")] = False,
    start_sample: Annotated[int, typer.Option("--start-sample")] = 0,
    end_sample: Annotated[int, typer.Option("--end-sample")] = 5000,
) -> None:
    """Write separated student/instructor drafts without downloading or releasing."""
    from ecg_strip_generator.teaching_packages import build_draft

    try:
        if bool(lead) == twelve:
            raise ValueError("Choose explicit --lead selections OR --twelve")
        selected = STANDARD_LEADS if twelve else tuple(lead)
        build_draft(bundle, record, selected, output, start_sample, end_sample)
    except (ValueError, OSError, KeyError, IndexError, SyntaxError) as exc:
        # Do not echo source rows, patient fields or Pydantic input values.
        typer.echo(
            f"Draft rejected ({type(exc).__name__}); check source, selection and destination.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Verified-source student/instructor drafts written. Clinical review remains pending."
    )


@app.command("draft-annotated")
def draft_annotated(
    bundle: Annotated[Path, typer.Argument(help="Verified local header/signal/atr bundle.")],
    dataset: Annotated[str, typer.Option("--dataset")],
    record: Annotated[str, typer.Option("--record")],
    output: Annotated[Path, typer.Option("--output")],
    category: Annotated[str, typer.Option("--category")],
    target_sample: Annotated[int, typer.Option("--target-sample")],
    start_sample: Annotated[int, typer.Option("--start-sample")],
    end_sample: Annotated[int, typer.Option("--end-sample")],
    lead: Annotated[list[str] | None, typer.Option("--lead")] = None,
    twelve: Annotated[bool, typer.Option("--twelve")] = False,
) -> None:
    """Select a contextual PAC/PVC/ectopy or rapid-run review candidate, not a diagnosis."""
    from ecg_strip_generator.teaching_packages import build_draft

    try:
        if bool(lead) == twelve:
            raise ValueError("Choose explicit --lead selections OR --twelve")
        build_draft(
            bundle,
            record,
            STANDARD_LEADS if twelve else tuple(lead),
            output,
            start_sample,
            end_sample,
            dataset_id=dataset,
            target=target_sample,
            category=category,
        )
    except (ValueError, OSError, KeyError, IndexError, TypeError) as exc:
        typer.echo(
            f"Draft rejected ({type(exc).__name__}); check source, target, context and leads.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    typer.echo("Source-verified candidate draft written; clinical review and release pending.")
