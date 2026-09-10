"""Narrow local WFDB reader: explicit calibration, no default gain or network."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import wfdb

from ecg_strip_generator.datasets.storage import Receipt, confined, safe_name
from ecg_strip_generator.datasets.wfdb_profiles import calibration, profile
from ecg_strip_generator.models import Signal

# Orthographic normalization only; original spellings remain in provenance.
PTBXL_LEADS = {
    "I": "I",
    "II": "II",
    "III": "III",
    "AVR": "aVR",
    "AVL": "aVL",
    "AVF": "aVF",
    **{f"V{i}": f"V{i}" for i in range(1, 7)},
}


@dataclass(frozen=True)
class Window:
    signal: Signal
    provenance: dict


def read_window(bundle: Path, receipt: Receipt, record: str, start: int, end: int) -> Window:
    """Caller verifies the entire bundle; every referenced file must be receipted."""
    safe_name(record)
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError("Sample window must be an increasing nonnegative integer interval")
    names = {f.path for f in receipt.files}
    header_name = record + ".hea"
    if header_name not in names:
        raise ValueError("Header is not in the verified receipt")
    header_path = confined(bundle, "files/" + header_name)
    if header_path.stat().st_size > 64_000:
        raise ValueError("Header too large")
    lines = [
        s.strip()
        for s in header_path.read_text(encoding="ascii").splitlines()
        if s.strip() and not s.lstrip().startswith("#")
    ]
    if not lines:
        raise ValueError("Empty WFDB header")
    top = lines[0].split()
    if len(top) < 4 or top[0] != Path(record).name or "/" in top[0]:
        raise ValueError("Only explicit single-segment headers are supported")
    count, fs, length = int(top[1]), float(top[2]), int(top[3])
    rules = profile(receipt.dataset.id)
    lead_map = rules["leads"]
    if (
        count != rules["count"]
        or len(lines) != count + 1
        or not np.isfinite(fs)
        or fs != rules["fs"]
    ):
        raise ValueError("Channel count or explicit sampling rate disagrees with source profile")
    if end > length or (end - start) / fs > 30:
        raise ValueError("Window exceeds source length or 30 seconds")
    channels, gains, baselines, files = [], [], [], set()
    for line in lines[1:]:
        fields = line.split()
        if len(fields) != 9 or fields[1] != rules["format"] or fields[7] != "0":
            raise ValueError("Unsupported WFDB format, timing modifiers or missing channel fields")
        gain, baseline = calibration(fields, receipt.dataset.id)
        file_name = safe_name(fields[0])
        if "/" in file_name:
            raise ValueError("Header signal files must be siblings")
        source_name = (Path(record).parent / file_name).as_posix()
        if source_name not in names:
            raise ValueError("Signal file is not in the verified receipt")
        confined(bundle, "files/" + source_name)
        if fields[8] not in lead_map:
            raise ValueError("Unrecognized recorded lead; no substitution allowed")
        channels.append(fields[8])
        gains.append(gain)
        baselines.append(baseline)
        files.add(source_name)
    if len(set(channels)) != count or (count == 12 and set(channels) != set(lead_map)):
        raise ValueError("Missing or duplicate source lead")
    if (
        len(files) != 1
        or confined(bundle, "files/" + next(iter(files))).stat().st_size
        != (length * count * int(rules["bits"]) + 7) // 8
    ):
        raise ValueError("Expected one complete multiplexed signal file")
    local_record = str(header_path.with_suffix(""))
    digital = wfdb.rdrecord(
        local_record, sampfrom=start, sampto=end, physical=False, return_res=32, pn_dir=None
    )
    if (
        digital.sig_name != channels
        or digital.fs != fs
        or digital.adc_gain != gains
        or digital.baseline != baselines
        or digital.units != ["mV"] * count
    ):
        raise ValueError("WFDB interpretation disagrees with explicit source header")
    values = digital.d_signal
    if values.shape != (end - start, count) or np.any(values == rules["missing"]):
        raise ValueError("Missing or truncated source samples")
    physical = (values.astype(np.float64) - np.array(baselines)) / np.array(gains)
    signal = Signal(
        leads=tuple(lead_map[n] for n in channels),
        sampling_rate_hz=fs,
        unit="mV",
        samples=tuple(map(tuple, physical.tolist())),
    )
    return Window(
        signal,
        {
            "adapter": "profiled-wfdb-2",
            "calibration_policy": rules["calibration_policy"],
            "calibration_reference": "https://physionet.org/physiotools/wag/header-5.htm",
            "record_path": record,
            "header_file": header_name,
            "signal_files": sorted(files),
            "source_sample_count": length,
            "sampling_rate_hz": fs,
            "start_sample": start,
            "end_sample_exclusive": end,
            "source_time_alignment": "simultaneous_recorded_channels",
            "channels": [
                {
                    "source_name": n,
                    "canonical_name": lead_map[n],
                    "adc_gain_per_mv": g,
                    "baseline_adc": b,
                    "unit": "mV",
                }
                for n, g, b in zip(channels, gains, baselines, strict=True)
            ],
            "transformations": [
                "digital_to_mv: (ADC - baseline) / gain",
                "source-profile spelling mapping only; no lead substitution",
                "consecutive source window; no filtering or resampling",
            ],
        },
    )
