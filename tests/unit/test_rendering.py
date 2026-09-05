"""Independent output geometry, encoded metadata and determinism checks."""

import json
import re

import matplotlib as mpl
import numpy as np
import pytest
from PIL import Image

from ecg_strip_generator.models import RenderRequest
from ecg_strip_generator.provenance import sha256
from ecg_strip_generator.rendering.geometry import calculate_geometry
from ecg_strip_generator.rendering.matplotlib_renderer import STYLE, build_figure, render
from ecg_strip_generator.validation import prepare_signal
from examples.make_fixture import make_fixture


@pytest.mark.parametrize("count,rows,columns", [(n, n, 1) for n in range(1, 7)] + [(12, 4, 1)])
@pytest.mark.parametrize("position", ["left", "right"])
def test_encoded_page_geometry_and_determinism(tmp_path, count, rows, columns, position) -> None:
    request = make_fixture(count)
    request = request.model_copy(
        update={"preset": request.preset.model_copy(update={"calibration_position": position})}
    )
    first = render(request, tmp_path / "first")
    # Host plotting preferences must not change the contract.
    with mpl.rc_context({"font.size": 30, "path.simplify": True, "savefig.bbox": "tight"}):
        second = render(request, tmp_path / "second")
    assert first == second
    for name in ("strip.pdf", "strip.png", "manifest.json"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    pdf = (tmp_path / "first" / "strip.pdf").read_bytes()
    box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
    assert box
    # Expected independently: 10-s four-row print (12 leads) or 6-s rhythm rows.
    width = 286 if count == 12 else 186
    height = 194 if count == 12 else 42 + rows * 48 + (rows - 1) * 8
    assert float(box[1]) == pytest.approx(width * 72 / 25.4, abs=1e-6)
    assert float(box[2]) == pytest.approx(height * 72 / 25.4, abs=1e-6)
    assert b"/CreationDate" not in pdf and b"/ModDate" not in pdf
    # Independent PDF path evidence: a 1-mV pulse is 10 mm high in page points.
    streams = re.findall(rb"stream\r?\n(.*?)endstream", pdf, re.S)
    coords = re.compile(
        rb"([\d.]+) ([\d.]+) m\s+([\d.]+) ([\d.]+) l\s+"
        rb"([\d.]+) ([\d.]+) l\s+([\d.]+) ([\d.]+) l\s+"
        rb"([\d.]+) ([\d.]+) l\s+([\d.]+) ([\d.]+) l"
    )
    pulses = []
    for stream in streams:
        for match in coords.finditer(stream):
            xy = np.array([float(v) for v in match.groups()]).reshape(-1, 2)
            if abs(xy[2, 1] - xy[1, 1] - 10 * 72 / 25.4) < 1e-5:
                pulses.append(xy)
    assert len(pulses) == rows
    for xy in pulses:
        pulse_origin_mm = 0 if position == "left" else (250 if count == 12 else 150)
        assert xy[0, 0] == pytest.approx((10 + pulse_origin_mm + 2) * 72 / 25.4, abs=1e-5)
        assert xy[3, 0] - xy[2, 0] == pytest.approx(5 * 72 / 25.4, abs=1e-5)
    with Image.open(tmp_path / "first" / "strip.png") as png:
        assert png.size == (int(width / 25.4 * 150), int(height / 25.4 * 150))
        scale = json.loads(png.info["ECGScale"])
        assert scale["physical_mm_accuracy"] is False
        assert scale["pixels_per_second"] == pytest.approx(25 * 150 / 25.4)
        assert scale["pixels_per_mv"] == pytest.approx(10 * 150 / 25.4)
        assert png.info["dpi"] == pytest.approx((150, 150), abs=0.02)
        assert "synthetic_didactic" == png.info["SourceEvidence"]
        assert np.asarray(png.convert("RGB")).std() > 5  # not a blank image
    assert first["case"]["review"]["clinical_review"] == "not_reviewed"
    assert first["case"]["review"]["teaching_release"] == "draft"
    assert first["case"]["review"]["technical_validation"] == "not_run"
    assert first["validation"]["render_checks"] == "passed"
    assert first["outputs"]["strip.pdf"]["sha256"] == sha256(pdf)
    assert str(tmp_path) not in (tmp_path / "first" / "manifest.json").read_text()


@pytest.mark.parametrize("speed,gain", [(12.5, 5.0), (25.0, 10.0), (50.0, 20.0)])
@pytest.mark.parametrize("position", ["left", "right"])
def test_plotted_coordinates_preserve_samples_and_scale(speed, gain, position) -> None:
    payload = make_fixture(12).model_dump(mode="json")
    payload["preset"].update(paper_speed_mm_s=speed, gain_mm_mv=gain, calibration_position=position)
    request = RenderRequest.model_validate(payload)
    signal = prepare_signal(request)
    geometry = calculate_geometry(10, request.preset)
    expected_rows = [
        ["I", "aVR", "V1", "V4"],
        ["II", "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
        ["II"],
    ]
    origin = 16 if position == "left" else 0
    with mpl.rc_context(rc=mpl.rcParamsDefault):
        mpl.rcParams.update(STYLE)
        fig = build_figure(request, signal, geometry)
        fig.canvas.draw()
        assert len(fig.axes) == 4
        for row, ax in enumerate(fig.axes):
            pulse, *waves = ax.lines
            assert len(waves) == (4 if row < 3 else 1)
            assert [t.get_text() for t in ax.texts] == expected_rows[row]
            for col, (lead, wave) in enumerate(zip(expected_rows[row], waves, strict=True)):
                first, stop = (col * 250, (col + 1) * 250) if row < 3 else (0, 1000)
                original_channel = request.signal.leads.index(lead)
                np.testing.assert_allclose(
                    wave.get_xdata(), origin + np.arange(first, stop) / 100 * speed
                )
                np.testing.assert_allclose(
                    wave.get_ydata(),
                    geometry.cell_height_mm / 2
                    + np.array(request.signal.samples)[first:stop, original_channel] * gain,
                )
            points = ax.transData.transform([(0, 0), (speed, gain)])
            assert points[1, 0] - points[0, 0] == pytest.approx(speed * 150 / 25.4)
            assert points[1, 1] - points[0, 1] == pytest.approx(gain * 150 / 25.4)
            assert max(pulse.get_ydata()) - min(pulse.get_ydata()) == gain
            if position == "right":
                assert min(pulse.get_xdata()) > 10 * speed
            else:
                assert max(pulse.get_xdata()) < 16
            # Adjacent row grids share a globally aligned 5-mm lattice.
            y = geometry.panel_bounds_mm(row)[1]
            for line in ax.collections[1].get_segments():
                if line[0, 1] == line[1, 1]:
                    grid_y = y + line[0, 1]
                    assert grid_y / 5 == pytest.approx(round(grid_y / 5))
        # No white inter-row gutter in the twelve-lead print layout.
        for above, below in zip(fig.axes, fig.axes[1:], strict=False):
            assert above.get_position().y0 == pytest.approx(below.get_position().y1)
        fig.clear()


def test_existing_output_and_invalid_input_are_not_written(tmp_path) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    sentinel = destination / "original"
    sentinel.write_text("preserve")
    with pytest.raises(FileExistsError):
        render(make_fixture(1), destination)
    assert sentinel.read_text() == "preserve"
    assert list(destination.iterdir()) == [sentinel]
    invalid = make_fixture(1).model_copy(update={"signal_sha256": "0" * 64})
    with pytest.raises(ValueError, match="checksum"):
        render(invalid, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_short_window_labels_remain_on_page() -> None:
    from ecg_strip_generator.models import Signal
    from ecg_strip_generator.provenance import signal_digest

    payload = make_fixture(1).model_dump(mode="json")
    payload["case"].update(case_id="W" * 64, end_sample=600)
    payload["signal"]["samples"] = payload["signal"]["samples"][:600]
    payload["signal_sha256"] = signal_digest(Signal.model_validate(payload["signal"]))
    payload["preset"]["paper_speed_mm_s"] = 12.5
    payload["preset"]["title"] = "W" * 80
    payload["preset"]["teaching_prompt"] = "W" * 120
    request = RenderRequest.model_validate(payload)
    signal = prepare_signal(request)
    geometry = calculate_geometry(signal.duration_s, request.preset)
    with mpl.rc_context(rc=mpl.rcParamsDefault):
        mpl.rcParams.update(STYLE)
        fig = build_figure(request, signal, geometry)
        fig.canvas.draw()
        for text in fig.texts:
            box = text.get_window_extent(fig.canvas.get_renderer())
            assert box.x0 >= 0 and box.y0 >= 0
            assert box.x1 <= fig.bbox.width and box.y1 <= fig.bbox.height
        fig.clear()


def test_corrupt_encoded_geometry_blocks_output(tmp_path, monkeypatch) -> None:
    from matplotlib.figure import Figure

    original = Figure.savefig

    def corrupt_pdf(self, target, **kwargs):
        original(self, target, **kwargs)
        if kwargs["format"] == "pdf":
            damaged = re.sub(rb"/MediaBox\s*\[[^]]+\]", b"/MediaBox [0 0 1 1]", target.getvalue())
            target.seek(0)
            target.truncate()
            target.write(damaged)

    monkeypatch.setattr(Figure, "savefig", corrupt_pdf)
    with pytest.raises(ValueError, match="PDF page geometry verification failed"):
        render(make_fixture(1), tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("count", range(1, 7))
@pytest.mark.parametrize("duration", [6, 10])
def test_rhythm_rows_preserve_full_window_and_requested_order(count, duration) -> None:
    request = make_fixture(count, duration)
    payload = request.model_dump(mode="json")
    payload["preset"]["displayed_leads"].reverse()
    request = RenderRequest.model_validate(payload)
    signal = prepare_signal(request)
    geometry = calculate_geometry(signal.duration_s, request.preset)
    fig = build_figure(request, signal, geometry)
    try:
        assert len(fig.axes) == count
        for row, ax in enumerate(fig.axes):
            assert len(ax.lines) == 2  # exactly one calibration and one continuous trace
            lead = request.preset.displayed_leads[row]
            wave = ax.lines[1]
            assert ax.texts[0].get_text() == lead
            channel = request.signal.leads.index(lead)
            np.testing.assert_array_equal(wave.get_xdata(), np.arange(duration * 100) / 100 * 25)
            np.testing.assert_array_equal(
                wave.get_ydata(),
                geometry.cell_height_mm / 2 + np.array(request.signal.samples)[:, channel] * 10,
            )
            assert geometry.waveform_width_mm == duration * 25
    finally:
        fig.clear()


def test_short_rhythm_request_creates_no_output(tmp_path) -> None:
    from ecg_strip_generator.models import Signal
    from ecg_strip_generator.provenance import signal_digest

    payload = make_fixture(6).model_dump(mode="json")
    payload["signal"]["samples"] = payload["signal"]["samples"][:599]
    payload["case"]["end_sample"] = 599
    payload["signal_sha256"] = signal_digest(Signal.model_validate(payload["signal"]))
    destination = tmp_path / "short"
    with pytest.raises(ValueError, match="at least 6 seconds"):
        render(RenderRequest.model_validate(payload), destination)
    assert not destination.exists()
