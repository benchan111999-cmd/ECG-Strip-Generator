"""Fresh-process reproducibility of the installed CLI, without any datasets."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ecg_strip_generator.provenance import canonical_json
from examples.make_fixture import make_fixture


@pytest.mark.parametrize("count", [2, 12])
def test_fresh_process_outputs_match(tmp_path, count) -> None:
    source = tmp_path / "request.json"
    source.write_bytes(canonical_json(make_fixture(count).model_dump(mode="json")))
    command = (
        str(Path(sys.executable).with_name("ecg-strip.exe"))
        if os.name == "nt"
        else str(Path(sys.executable).with_name("ecg-strip"))
    )
    for index, epoch in enumerate(("0", "1780000000")):
        env = {**os.environ, "SOURCE_DATE_EPOCH": epoch, "PYTHONHASHSEED": str(index + 1)}
        result = subprocess.run(
            [command, "render", str(source), "--output", str(tmp_path / str(index))],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
    for name in ("strip.pdf", "strip.png", "manifest.json"):
        assert (tmp_path / "0" / name).read_bytes() == (tmp_path / "1" / name).read_bytes()
    manifest = json.loads((tmp_path / "0" / "manifest.json").read_text())
    assert manifest["preset"]["time_alignment"] == ("sequential" if count == 12 else "simultaneous")
    if count == 12:
        segments = manifest["display_segments"]
        assert len(segments) == 13
        assert [
            (s["source_start_sample"], s["source_end_sample_exclusive"]) for s in segments[:4]
        ] == [(0, 250), (250, 500), (500, 750), (750, 1000)]
        assert segments[-1]["lead"] == "II" and segments[-1]["role"] == "rhythm"
        assert (
            segments[-1]["source_start_sample"],
            segments[-1]["source_end_sample_exclusive"],
        ) == (0, 1000)
