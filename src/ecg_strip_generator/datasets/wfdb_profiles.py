"""Pinned source decoding policies, not clinical lead or rhythm inference."""

import math
import re

from ecg_strip_generator.models import STANDARD_LEADS

TWELVE = {n.upper() if n.startswith("aV") else n: n for n in STANDARD_LEADS}
SPEC = (
    "positive header gain; explicit baseline or WFDB ADC-zero baseline; "
    "explicit mV or disclosed WFDB omitted-unit mV convention; no default gain"
)


def profile(dataset: str) -> dict:
    common = {
        "bits": 16,
        "format": "16",
        "missing": -32768,
        "count": 12,
        "leads": TWELVE,
        "calibration_policy": SPEC,
    }
    if dataset == "ptb-xl":
        return {**common, "fs": 500, "calibration_policy": "explicit gain(baseline)/mV only"}
    if dataset == "incartdb":
        return {**common, "fs": 257}
    if dataset in ("mitdb", "svdb"):
        names = ("ECG1", "ECG2") if dataset == "svdb" else (*STANDARD_LEADS, "MLII", "MCL1")
        return {
            **common,
            "bits": 12,
            "format": "212",
            "missing": -2048,
            "count": 2,
            "fs": 128 if dataset == "svdb" else 360,
            "leads": {n: n for n in names},
        }
    raise ValueError("Unsupported source profile")


def calibration(fields: list[str], dataset: str) -> tuple[float, int]:
    explicit = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\((-?[0-9]+)\)/mV", fields[2])
    if dataset == "ptb-xl" and explicit is None:
        raise ValueError("Explicit positive gain, baseline and mV units are required")
    value = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(?:\((-?[0-9]+)\))?(?:/mV)?", fields[2])
    if value is None or not math.isfinite(float(value[1])) or float(value[1]) <= 0:
        raise ValueError("Explicit positive gain, baseline and mV units are required")
    baseline = int(value[2]) if value[2] is not None else int(fields[4])
    return float(value[1]), baseline
