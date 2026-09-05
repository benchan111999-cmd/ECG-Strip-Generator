"""Generate only non-clinical triangle/ramp fixtures for renderer verification."""

import argparse
from pathlib import Path

from ecg_strip_generator.models import STANDARD_LEADS, RenderRequest, Signal
from ecg_strip_generator.provenance import canonical_json, signal_digest


def make_fixture(count: int = 12) -> RenderRequest:
    """No ECG physiology or diagnostic rhythm is modelled by these fixtures."""
    if count not in (1, 2, 12):
        raise ValueError("Fixture lead count must be 1, 2 or 12")
    sample_count = 1000 if count == 12 else 200
    leads = STANDARD_LEADS if count == 12 else ("II",) if count == 1 else ("I", "II")
    # Integer arithmetic gives stable, visibly distinct channel values without random state.
    samples = [
        [
            (((i + channel * 7) % 40) - 20) / 40.0 * (1 + channel / 24)
            for channel in range(len(leads))
        ]
        for i in range(sample_count)
    ]
    signal = Signal(leads=leads, sampling_rate_hz=100.0, unit="mV", samples=samples)
    digest = signal_digest(signal)
    return RenderRequest.model_validate(
        {
            "case": {
                "case_id": f"fixture-{count}",
                "source": {
                    "dataset": "non-clinical-fixture",
                    "version": "1",
                    "record_id": f"fixture-{count}",
                    "annotation_reference": "Triangle/ramp test function; no rhythm annotation",
                    "licence": "Local test fixture; no redistribution licence granted",
                    "attribution": "ECG Strip Generator non-clinical renderer test",
                    "checksum_sha256": digest,
                    "checksum_kind": "locally_observed",
                    "non_clinical_fixture": True,
                },
                "source_evidence": "synthetic_didactic",
                "start_sample": 0,
                "end_sample": sample_count,
            },
            "signal": signal.model_dump(mode="json"),
            "signal_sha256": digest,
            "preset": {
                "displayed_leads": leads,
                "time_alignment": "sequential" if count == 12 else "simultaneous",
                "calibration_position": "right",
                "amplitude_limit_mv": 1.5 if count == 12 else 2.0,
            },
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leads", type=int, choices=(1, 2, 12), default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as target:
        target.write(canonical_json(make_fixture(args.leads).model_dump(mode="json")))
