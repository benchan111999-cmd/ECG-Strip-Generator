"""Exact lead selection and physical-unit validation before plotting."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ecg_strip_generator.models import TWELVE_PANEL_ORDER, RenderRequest
from ecg_strip_generator.provenance import signal_digest

UNIT_TO_MV = {"mV": 1.0, "uV": 0.001, "V": 1000.0}


@dataclass(frozen=True)
class PreparedSignal:
    leads: tuple[str, ...]
    values_mv: NDArray[np.float64]
    times_s: NDArray[np.float64]
    duration_s: float
    conversion_factor: float


def prepare_signal(request: RenderRequest) -> PreparedSignal:
    if signal_digest(request.signal) != request.signal_sha256:
        raise ValueError("Signal checksum mismatch")
    source = request.signal
    requested = request.preset.displayed_leads
    missing = sorted(set(requested) - set(source.leads))
    if missing:
        raise ValueError(f"Missing requested leads: {', '.join(missing)}; no substitution allowed")
    leads = TWELVE_PANEL_ORDER if len(requested) == 12 else requested
    indices = [source.leads.index(lead) for lead in leads]
    factor = UNIT_TO_MV[source.unit]
    values = np.asarray(source.samples, dtype=np.float64)[:, indices] * factor
    if not np.isfinite(values).all():
        raise ValueError("Converted signal must contain only finite values")
    if np.max(np.abs(values)) > request.preset.amplitude_limit_mv:
        raise ValueError("Signal exceeds display amplitude; choose an explicit larger range")
    duration = len(values) / source.sampling_rate_hz
    if not 0.5 <= duration <= 30:
        raise ValueError("Rendered windows must be between 0.5 and 30 seconds")
    if len(requested) == 12 and not np.isclose(duration, 10.0, rtol=0, atol=1e-9):
        raise ValueError(
            "Twelve-lead layout requires exactly 10 seconds, including continuous Lead II"
        )
    times = np.arange(len(values), dtype=np.float64) / source.sampling_rate_hz
    values.setflags(write=False)
    times.setflags(write=False)
    return PreparedSignal(leads, values, times, duration, factor)


@dataclass(frozen=True)
class DisplaySegment:
    row: int
    lead: str
    start_sample: int
    end_sample: int
    start_s: float
    end_s: float
    role: str = "standard"


def display_segments(signal: PreparedSignal) -> tuple[DisplaySegment, ...]:
    """One shared slice plan for drawing and provenance; intervals are half-open."""
    if len(signal.leads) != 12:
        return tuple(
            DisplaySegment(row, lead, 0, len(signal.times_s), 0.0, signal.duration_s)
            for row, lead in enumerate(signal.leads)
        )
    segments = []
    for index, lead in enumerate(signal.leads):
        row, column = divmod(index, 4)
        start, end = column * 2.5, (column + 1) * 2.5
        first, stop = np.searchsorted(signal.times_s, (start, end), side="left")
        segments.append(DisplaySegment(row, lead, int(first), int(stop), start, end))
    segments.append(DisplaySegment(3, "II", 0, len(signal.times_s), 0.0, 10.0, "rhythm"))
    return tuple(segments)
