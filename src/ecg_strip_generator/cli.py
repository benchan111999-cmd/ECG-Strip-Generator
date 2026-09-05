"""Minimal installed command surface for Milestone 0."""

import platform
from importlib.metadata import version
from typing import Annotated

import typer

app = typer.Typer(
    help="Personal, non-commercial ECG teaching tool. Development skeleton only.",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
)


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
    typer.echo("Milestone 0: development skeleton only.")
    typer.echo("ECG rendering and dataset validation are not implemented.")
    typer.echo("Clinical review and teaching release: not performed.")
