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
    times = np.arange(len(values), dtype=np.float64) / source.sampling_rate_hz
    values.setflags(write=False)
    times.setflags(write=False)
    return PreparedSignal(leads, values, times, duration, factor)
