"""Draft rendering and installed runtime reporting."""

import platform
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from ecg_strip_generator.cases_cli import app as cases_app
from ecg_strip_generator.datasets.cli import app as datasets_app
from ecg_strip_generator.models import RenderRequest

app = typer.Typer(
    help="Personal, non-commercial ECG teaching tool. Unreviewed draft output only.",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
)


app.add_typer(datasets_app, name="datasets")
app.add_typer(cases_app, name="cases")


@app.callback()
def main(
    show_version: Annotated[
        bool, typer.Option("--version", help="Show the installed package version.", is_eager=True)
    ] = False,
) -> None:
    if show_version:
        typer.echo(version("ecg-strip-generator"))
        raise typer.Exit()


@app.command()
def doctor() -> None:
    """Report runtime identity only; this does not validate ECGs or datasets."""
    typer.echo(f"ECG Strip Generator {version('ecg-strip-generator')}")
    typer.echo(f"Python {platform.python_version()}")
    typer.echo("Milestone 3: verified PTB-XL source windows and separated draft packages.")
    typer.echo("Use datasets audit for raw bytes; cases draft-ptbxl checks explicit calibration.")
    typer.echo("Clinical review and teaching release: not performed.")


@app.command("render")
def render_command(
    request_file: Annotated[
        Path, typer.Argument(help="JSON render request with physical samples.")
    ],
    output: Annotated[
        Path, typer.Option("--output", help="New output directory; never overwrite.")
    ],
) -> None:
    """Create draft strip.pdf, strip.png and manifest.json; no downloads or release."""
    from ecg_strip_generator.rendering.matplotlib_renderer import render

    try:
        if request_file.stat().st_size > 20_000_000:
            raise ValueError("Render request exceeds 20 MB limit")
        request = RenderRequest.model_validate_json(request_file.read_bytes())
        render(request, output)
    except ValidationError as exc:
        messages = [
            f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
            for e in exc.errors(include_input=False, include_url=False)[:3]
        ]
        typer.echo("Invalid request: " + "; ".join(messages), err=True)
        raise typer.Exit(code=1) from exc
    except (ValueError, OSError) as exc:
        typer.echo(f"Render failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo("Draft PDF, PNG and manifest written. Clinical review and release remain pending.")
