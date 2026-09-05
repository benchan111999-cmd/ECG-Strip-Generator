"""Deterministic draft PDF/PNG with explicit physical and digital scale metadata."""

import io
import platform
import re
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import matplotlib as mpl
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from PIL import Image

from ecg_strip_generator.models import RenderRequest
from ecg_strip_generator.provenance import canonical_json, sha256
from ecg_strip_generator.rendering.geometry import MM_PER_INCH, Geometry, calculate_geometry
from ecg_strip_generator.validation import PreparedSignal, display_segments, prepare_signal

RENDERER_VERSION = "2"
STYLE = {
    "font.family": ["DejaVu Sans"],
    "font.size": 7,
    "text.usetex": False,
    "text.parse_math": False,
    "path.simplify": False,
    "agg.path.chunksize": 0,
    "pdf.fonttype": 42,
    "pdf.compression": 0,
    "savefig.bbox": None,
    "figure.autolayout": False,
}


def build_figure(request: RenderRequest, signal: PreparedSignal, geometry: Geometry) -> Figure:
    """Called inside the renderer's isolated rc_context; coordinates are millimetres."""
    preset = request.preset
    fig = Figure(
        figsize=(geometry.page_width_mm / MM_PER_INCH, geometry.page_height_mm / MM_PER_INCH),
        dpi=preset.dpi,
    )
    FigureCanvasAgg(fig)
    segments = display_segments(signal)
    wave_origin = geometry.calibration_gutter_mm if preset.calibration_position == "left" else 0.0
    pulse_origin = 0.0 if preset.calibration_position == "left" else geometry.waveform_width_mm
    for row in range(geometry.rows):
        x, y, width, height = geometry.panel_bounds_mm(row)
        ax = fig.add_axes(
            (
                x / geometry.page_width_mm,
                y / geometry.page_height_mm,
                width / geometry.page_width_mm,
                height / geometry.page_height_mm,
            )
        )
        ax.set(xlim=(0, width), ylim=(0, height))
        ax.set_axis_off()
        for step, colour, thickness in ((1, "#f4dada", 0.22), (5, "#dcaaaa", 0.45)):
            lines = [((v, 0), (v, height)) for v in np.arange(0, width + 1e-9, step)]
            # Align horizontal grid globally even when a row height is not a multiple of 5 mm.
            ys = np.arange(np.ceil(y / step) * step, y + height + 1e-9, step) - y
            lines += [((0, v), (width, v)) for v in ys]
            ax.add_collection(LineCollection(lines, colors=colour, linewidths=thickness, zorder=0))
        baseline = height / 2
        pulse_width = 0.2 * preset.paper_speed_mm_s
        ax.plot(
            pulse_origin + np.array([2, 3, 3, 3 + pulse_width, 3 + pulse_width, 4 + pulse_width]),
            [
                baseline,
                baseline,
                baseline + preset.gain_mm_mv,
                baseline + preset.gain_mm_mv,
                baseline,
                baseline,
            ],
            color="#202020",
            linewidth=0.7,
            solid_capstyle="butt",
            gid="calibration",
        )
        for segment in (item for item in segments if item.row == row):
            channel = signal.leads.index(segment.lead)
            window = slice(segment.start_sample, segment.end_sample)
            # Absolute relative-to-window times preserve column timing; no cross-lead join.
            ax.plot(
                wave_origin + signal.times_s[window] * preset.paper_speed_mm_s,
                baseline + signal.values_mv[window, channel] * preset.gain_mm_mv,
                color="#202020",
                linewidth=0.7,
                solid_capstyle="butt",
                gid=segment.role,
            )
            ax.text(
                wave_origin + segment.start_s * preset.paper_speed_mm_s + 1.5,
                height - 1.5,
                segment.lead,
                va="top",
                fontsize=7,
                fontweight="bold",
            )

    # Fixed positions; no tight/constrained layout or content-dependent page resizing.
    left = geometry.margin_mm / geometry.page_width_mm
    case_label = preset.title or request.case.case_id
    if len(case_label) > 22:
        case_label = case_label[:10] + "..." + case_label[-8:]
    fig.text(left, 1 - 5 / geometry.page_height_mm, case_label, fontsize=8, va="top")
    kind = "SYNTHETIC" if request.case.source_evidence == "synthetic_didactic" else "REAL SOURCE"
    fixture = " / NON-CLINICAL FIXTURE" if request.case.source.non_clinical_fixture else ""
    fig.text(
        left, 1 - 10 / geometry.page_height_mm, f"{kind}{fixture} / DRAFT", fontsize=6, va="top"
    )
    start = request.case.start_sample / request.signal.sampling_rate_hz
    fig.text(
        left,
        1 - 15 / geometry.page_height_mm,
        f"{preset.time_alignment.title()} | "
        f"{start:g}-{start + signal.duration_s:g} s (end exclusive)",
        fontsize=6,
        va="top",
    )
    fig.text(
        left,
        14 / geometry.page_height_mm,
        f"{preset.paper_speed_mm_s:g} mm/s | {preset.gain_mm_mv:g} mm/mV | pulse 1 mV / 0.2 s",
        fontsize=6,
    )
    fig.text(
        left,
        9 / geometry.page_height_mm,
        "Not clinically reviewed. Not for teaching release.",
        fontsize=5,
    )
    fig.text(
        left,
        4 / geometry.page_height_mm,
        "PDF: print 100%; no fit-to-page. PNG: display scale only.",
        fontsize=5,
    )
    if preset.teaching_prompt:
        prompt = preset.teaching_prompt
        if len(prompt) > 36:
            prompt = prompt[:33] + "..."
        fig.text(left, 1 - 20 / geometry.page_height_mm, prompt, fontsize=5, va="top")
    return fig


def render(request: RenderRequest, output_dir: Path) -> dict:
    """Validate before creating output. Existing destinations are never overwritten."""
    # Revalidate even model_copy/model_construct callers rather than trusting a frozen wrapper.
    request = RenderRequest.model_validate(request.model_dump(mode="json"))
    prepared = prepare_signal(request)
    geometry = calculate_geometry(prepared.duration_s, request.preset)
    if output_dir.exists():
        raise FileExistsError("Output directory already exists; choose a new directory")
    environment = {name: version(name) for name in ("matplotlib", "numpy", "pillow")}
    environment["python"] = platform.python_version()
    image_scale = {
        "duration_s": prepared.duration_s,
        "sampling_rate_hz": request.signal.sampling_rate_hz,
        "pixels_per_second": request.preset.paper_speed_mm_s * request.preset.dpi / MM_PER_INCH,
        "pixels_per_mv": request.preset.gain_mm_mv * request.preset.dpi / MM_PER_INCH,
        "physical_mm_accuracy": False,
        "time_alignment": request.preset.time_alignment,
    }
    with mpl.rc_context(rc=mpl.rcParamsDefault):
        mpl.rcParams.update(STYLE)
        fig = build_figure(request, prepared, geometry)
        pdf, png = io.BytesIO(), io.BytesIO()
        try:
            fig.savefig(
                pdf,
                format="pdf",
                metadata={
                    "Creator": f"ECG Strip Generator renderer {RENDERER_VERSION}",
                    "Producer": "Matplotlib",
                    "CreationDate": None,
                    "ModDate": None,
                    "Title": f"{request.case.case_id} - DRAFT",
                },
            )
            fig.savefig(
                png,
                format="png",
                dpi=request.preset.dpi,
                metadata={
                    "Software": f"ECG Strip Generator renderer {RENDERER_VERSION}",
                    "ECGScale": canonical_json(image_scale).decode("ascii").strip(),
                    "Review": "draft; not clinically reviewed; not for teaching release",
                    "SourceEvidence": request.case.source_evidence,
                },
            )
        finally:
            fig.clear()
    pdf_bytes, png_bytes = pdf.getvalue(), png.getvalue()
    box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf_bytes)
    expected_points = np.array([geometry.page_width_mm, geometry.page_height_mm]) * 72 / MM_PER_INCH
    if box is None or not np.allclose(
        [float(box[1]), float(box[2])], expected_points, rtol=0, atol=1e-6
    ):
        raise ValueError("Encoded PDF page geometry verification failed")
    with Image.open(io.BytesIO(png_bytes)) as image:
        expected_pixels = tuple(
            int(v / MM_PER_INCH * request.preset.dpi)
            for v in (geometry.page_width_mm, geometry.page_height_mm)
        )
        if image.size != expected_pixels:
            raise ValueError("Encoded PNG dimensions verification failed")
        image.load()
        image_scale["pixel_width"], image_scale["pixel_height"] = image.size
        image_scale["dpi_metadata"] = list(image.info["dpi"])
    manifest = {
        "case": request.case.model_dump(mode="json"),
        "signal_sha256": request.signal_sha256,
        "recorded_leads": list(request.signal.leads),
        "displayed_leads": list(prepared.leads),
        "sampling_rate_hz": request.signal.sampling_rate_hz,
        "input_unit": request.signal.unit,
        "output_unit": "mV",
        "start_time_s": request.case.start_sample / request.signal.sampling_rate_hz,
        "end_time_s_exclusive": request.case.end_sample / request.signal.sampling_rate_hz,
        "transformations": [
            {"operation": "physical_unit_to_mv", "factor": prepared.conversion_factor},
            {"operation": "exact_lead_selection", "leads": list(prepared.leads)},
        ],
        "preset": request.preset.model_dump(mode="json"),
        "display_segments": [
            {
                **asdict(segment),
                "source_start_sample": request.case.start_sample + segment.start_sample,
                "source_end_sample_exclusive": request.case.start_sample + segment.end_sample,
            }
            for segment in display_segments(prepared)
        ],
        "geometry_mm": geometry.as_dict(),
        "png_scale": image_scale,
        "renderer": {"name": "matplotlib", "version": RENDERER_VERSION, "environment": environment},
        "validation": {
            "render_checks": "passed",
            "scope": [
                "input_shape",
                "signal_checksum",
                "lead_identity",
                "units",
                "amplitude",
                "geometry",
                "output_encoding",
            ],
            "raw_source_checksum": "declared_not_verified",
            "physical_print_measurement": "not_performed",
        },
        "outputs": {
            "strip.pdf": {"sha256": sha256(pdf_bytes)},
            "strip.png": {"sha256": sha256(png_bytes)},
        },
    }
    # Overall case technical status stays not_run: raw-source verification is future work.
    payloads = {
        "strip.pdf": pdf_bytes,
        "strip.png": png_bytes,
        "manifest.json": canonical_json(manifest),
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, payload in payloads.items():
        with (output_dir / name).open("xb") as file:
            file.write(payload)
    return manifest
