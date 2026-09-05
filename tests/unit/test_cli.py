"""Installed command boundaries; no external data or network."""

from importlib.metadata import version

from typer.testing import CliRunner

from ecg_strip_generator.cli import app

runner = CliRunner()


def test_installed_version_is_available() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == version("ecg-strip-generator")


def test_doctor_discloses_incomplete_validation() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Python 3.12." in result.stdout
    assert "waveform validation is not implemented" in result.stdout
    assert "Clinical review and teaching release: not performed" in result.stdout


def test_missing_input_does_not_create_output(tmp_path) -> None:
    result = runner.invoke(
        app, ["render", str(tmp_path / "missing.json"), "--output", str(tmp_path / "result")]
    )
    assert result.exit_code != 0
    assert not (tmp_path / "result").exists()
