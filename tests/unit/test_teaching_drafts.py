"""Closed student exports, provenance, refusal and deterministic draft publication."""

import json

import pytest
from PIL import Image
from test_real_sources import RECORD
from test_real_sources import raw_source as source_fixture  # noqa: F401
from typer.testing import CliRunner

from ecg_strip_generator.cli import app
from ecg_strip_generator.datasets.ptbxl import select
from ecg_strip_generator.models import STANDARD_LEADS
from ecg_strip_generator.rendering.geometry import calculate_geometry
from ecg_strip_generator.rendering.matplotlib_renderer import build_figure
from ecg_strip_generator.teaching_packages import audit_draft, build_draft, verify_payloads
from ecg_strip_generator.validation import prepare_signal


@pytest.mark.parametrize("leads", [("II",), ("II", "V1"), STANDARD_LEADS])
def test_separated_drafts_no_student_answers(raw_source, tmp_path, leads):
    bundle = raw_source[2]()
    root = build_draft(bundle, RECORD, leads, tmp_path / "draft")
    assert audit_draft(root)["status"] == "draft"
    instructor = next((root / "instructor").iterdir())
    student = next((root / "student").iterdir())
    assert {p.name for p in student.iterdir()} == {
        "strip.pdf",
        "strip.png",
        "README.md",
        "ATTRIBUTION.txt",
        "LICENSE.txt",
    }
    manifest = json.loads((instructor / "manifest.json").read_bytes())
    assert manifest["case"]["review"] == {
        "technical_validation": "passed",
        "clinical_review": "not_reviewed",
        "teaching_release": "draft",
    }
    assert manifest["validation"]["raw_source_checksum"] == "verified"
    assert manifest["validation"]["physical_print_measurement"] == "not_performed"
    assert "normal ECG" in (instructor / "README.md").read_text()
    for path in root.rglob("*"):
        if path.is_file():
            assert b"PRIVATE" not in path.read_bytes()
    for path in student.iterdir():
        assert "norm" not in path.name.lower()
        if path.suffix in (".md", ".txt"):
            assert "normal ECG" not in path.read_text()
            assert "sinus rhythm" not in path.read_text()
        if path.suffix in (".pdf", ".png"):
            assert path.read_bytes() == (instructor / path.name).read_bytes()
    with Image.open(student / "strip.png") as png:
        assert "NORM" not in json.dumps(png.info)
        assert "PRIVATE" not in json.dumps(png.info)
    request = select(bundle, RECORD, leads).request
    prepared = prepare_signal(request)
    figure = build_figure(
        request, prepared, calculate_geometry(prepared.duration_s, request.preset)
    )
    texts = [t.get_text() for t in figure.texts]
    texts += [t.get_text() for ax in figure.axes for t in ax.texts]
    assert not any(word in " ".join(texts) for word in ("normal", "NORM", "sinus", "PRIVATE"))
    figure.clear()
    if len(leads) == 12:
        assert manifest["preset"]["time_alignment"] == "sequential"
        rhythm = manifest["display_segments"][-1]
        assert rhythm["lead"] == "II" and rhythm["source_end_sample_exclusive"] == 5000
    second = build_draft(bundle, RECORD, leads, tmp_path / "repeat")
    assert (root / "package-files.json").read_bytes() == (
        second / "package-files.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        build_draft(bundle, RECORD, leads, root)


def test_readback_rejects_extra_and_changed_files(tmp_path):
    (tmp_path / "a").write_bytes(b"okay")
    verify_payloads(tmp_path, {"a": b"okay"})
    with pytest.raises(ValueError, match="mismatch"):
        verify_payloads(tmp_path, {"a": b"changed"})
    (tmp_path / "answer.txt").write_bytes(b"normal")
    with pytest.raises(ValueError, match="unexpected"):
        verify_payloads(tmp_path, {"a": b"okay"})


def test_cli_explicit_selection_and_no_download(raw_source, tmp_path, monkeypatch):
    bundle = raw_source[2]()
    from ecg_strip_generator.datasets import transport

    monkeypatch.setattr(transport, "download", lambda *a: pytest.fail("Unexpected network"))
    runner = CliRunner()
    base = [
        "cases",
        "draft-ptbxl",
        str(bundle),
        "--record",
        RECORD,
        "--output",
        str(tmp_path / "draft"),
    ]
    assert runner.invoke(app, base).exit_code == 1
    assert runner.invoke(app, base + ["--lead", "II", "--twelve"]).exit_code == 1
    result = runner.invoke(app, base + ["--lead", "II"])
    assert result.exit_code == 0, result.output
    assert runner.invoke(app, ["cases", "audit-draft", str(tmp_path / "draft")]).exit_code == 0
    student = next((tmp_path / "draft/student").iterdir())
    (student / "answer.txt").write_text("normal")
    with pytest.raises(ValueError, match="Unexpected"):
        audit_draft(tmp_path / "draft")
    assert runner.invoke(app, ["cases", "audit-draft", str(tmp_path / "draft")]).exit_code == 1


def test_failed_render_never_publishes_package(raw_source, tmp_path, monkeypatch):
    from ecg_strip_generator import teaching_packages

    def interrupted(request, output):
        output.mkdir(parents=True)
        (output / "strip.png").write_bytes(b"partial")
        raise OSError("interrupted")

    monkeypatch.setattr(teaching_packages, "render", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        build_draft(raw_source[2](), RECORD, ("II",), tmp_path / "result")
    assert not (tmp_path / "result").exists()
    assert list(tmp_path.glob(".draft-*/instructor/*/strip.png"))
