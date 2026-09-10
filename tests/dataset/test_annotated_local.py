"""Opt-in real M4 bundles; independent ADC decoding, no downloads or diagnoses."""

import os
from pathlib import Path

import numpy as np
import pytest
import wfdb

from ecg_strip_generator.datasets.annotated import select
from ecg_strip_generator.teaching_packages import audit_draft, build_draft

pytestmark = pytest.mark.dataset


@pytest.mark.parametrize(
    "dataset,record,leads,start,end,target,category",
    [
        ("mitdb", "100", ("MLII", "V5"), 964, 3124, 2044, "pac"),
        ("svdb", "800", ("ECG1", "ECG2"), 6090, 6858, 6474, "supraventricular-ectopy"),
        ("incartdb", "I01", ("II",), 7770, 9312, 8541, "pvc"),
    ],
)
def test_real_annotated_window(tmp_path, dataset, record, leads, start, end, target, category):
    value = os.environ.get(f"ECG_{dataset.upper()}_BUNDLE")
    if not value:
        pytest.skip(f"Set ECG_{dataset.upper()}_BUNDLE to the verified {record} bundle")
    bundle = Path(value)
    candidate = select(bundle, dataset, record, leads, start, end, target, category)
    source = str(bundle / "files" / record)
    physical = wfdb.rdrecord(source, sampfrom=start, sampto=end)
    np.testing.assert_array_equal(candidate.request.signal.samples, physical.p_signal)
    header = wfdb.rdheader(source)
    raw_path = bundle / "files" / (record + ".dat")
    if dataset == "incartdb":
        raw = np.fromfile(raw_path, dtype="<i2").reshape(-1, 12)[start:end]
    else:
        packed = np.fromfile(raw_path, dtype=np.uint8).reshape(-1, 3)[start:end].astype(int)
        raw = np.column_stack(
            (packed[:, 0] | ((packed[:, 1] & 15) << 8), packed[:, 2] | ((packed[:, 1] >> 4) << 8))
        )
        raw = np.where(raw >= 2048, raw - 4096, raw)
    calibrated = (raw.astype(float) - np.array(header.baseline)) / np.array(header.adc_gain)
    np.testing.assert_array_equal(candidate.request.signal.samples, calibrated)
    ann = wfdb.rdann(source, "atr")
    expected = [
        (int(t), s) for t, s in zip(ann.sample, ann.symbol, strict=True) if start <= t < end
    ]
    events = candidate.provenance["statement"]["events"]
    assert [(e["source_sample"], e["symbol"]) for e in events] == expected
    assert all(e["relative_sample"] == e["source_sample"] - start for e in events)
    output = build_draft(
        bundle,
        record,
        leads,
        tmp_path / "draft",
        start,
        end,
        dataset_id=dataset,
        target=target,
        category=category,
    )
    assert audit_draft(output)["clinical_review"] == "not_reviewed"
