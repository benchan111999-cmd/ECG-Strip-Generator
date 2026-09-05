"""Exercise the installed command boundary without datasets or network access."""

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
    assert "dataset validation are not implemented" in result.stdout
    assert "Clinical review and teaching release: not performed" in result.stdout


def test_unimplemented_render_command_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["render", "case.json"])
    assert result.exit_code != 0
    assert list(tmp_path.iterdir()) == []
