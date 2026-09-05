"""Opt-in real-file tests. No downloads; set ECG_PTBXL_BUNDLE explicitly."""

import json
import os
from pathlib import Path

import numpy as np
import pytest
import wfdb

from ecg_strip_generator.datasets.ptbxl import select
from ecg_strip_generator.models import STANDARD_LEADS
from ecg_strip_generator.teaching_packages import audit_draft, build_draft

pytestmark = pytest.mark.dataset


@pytest.fixture
def bundle():
    value = os.environ.get("ECG_PTBXL_BUNDLE")
    if not value:
        pytest.skip("Set ECG_PTBXL_BUNDLE to the verified record 00001_hr bundle")
    return Path(value)


@pytest.mark.parametrize(
    "leads,end", [(("II",), 3000), (("II", "V1"), 5000), (STANDARD_LEADS, 5000)]
)
def test_real_raw_values_and_draft_contract(bundle, tmp_path, leads, end):
    record = "records500/00000/00001_hr"
    candidate = select(bundle, record, leads, 0, end)
    physical = wfdb.rdrecord(str(bundle / "files" / record), sampfrom=0, sampto=end)
    np.testing.assert_array_equal(candidate.request.signal.samples, physical.p_signal)
    raw = np.fromfile(bundle / "files" / (record + ".dat"), dtype="<i2").reshape(-1, 12)
    np.testing.assert_array_equal(candidate.request.signal.samples, raw[:end].astype(float) / 1000)
    assert candidate.provenance["statement"]["codes"]["NORM"] == 100
    output = build_draft(bundle, record, leads, tmp_path / "draft", 0, end)
    assert audit_draft(output)["clinical_review"] == "not_reviewed"
    manifest = json.loads(next((output / "instructor").glob("*/manifest.json")).read_bytes())
    assert manifest["signal_sha256"] == candidate.request.signal_sha256
    assert len(manifest["recorded_leads"]) == 12
    assert len(manifest["displayed_leads"]) == len(leads)
