"""Generated non-clinical WFDB bytes exercise the complete offline source path."""

import csv
import hashlib
import io
import json

import numpy as np
import pytest
import wfdb

from ecg_strip_generator.datasets import transport
from ecg_strip_generator.datasets.ptbxl import select
from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import fetch
from ecg_strip_generator.models import STANDARD_LEADS

RECORD = "records500/00000/00001_hr"
HEADER_LEADS = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]


@pytest.fixture(name="raw_source")
def raw_source(tmp_path, monkeypatch):
    digital = (np.arange(5000 * 12).reshape(5000, 12) % 501 - 250).astype("<i2")
    header = "00001_hr 12 500 5000\n" + "".join(
        f"00001_hr.dat 16 1000.0(10)/mV 16 0 {digital[0, i]} 0 0 {name}\n"
        for i, name in enumerate(HEADER_LEADS)
    )
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["ecg_id", "filename_hr", "scp_codes", "patient_id", "report"])
    writer.writerow(
        ["1", RECORD, "{'NORM': 100.0, 'SR': 0.0}", "PRIVATE-PATIENT", "PRIVATE-REPORT"]
    )
    payloads = {
        RECORD + ".hea": header.encode(),
        RECORD + ".dat": digital.tobytes(),
        "ptbxl_database.csv": stream.getvalue().encode(),
        "scp_statements.csv": b",description\nNORM,normal ECG\nSR,sinus rhythm\n",
        "LICENSE.txt": b"Non-clinical test licence fixture.\n",
    }

    def download(url, destination, limit):
        name = url.split("/1.0.3/")[1]
        data = (
            "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in payloads.items()).encode()
            if name == "SHA256SUMS.txt"
            else payloads[name]
        )
        assert len(data) <= limit
        destination.write_bytes(data)
        return len(data)

    monkeypatch.setattr(transport, "download", download)

    def acquire():
        return fetch(load_registry()["ptb-xl"], list(payloads), tmp_path / "data")

    return payloads, digital, acquire


def test_exact_digital_and_independent_wfdb_physical(raw_source):
    _, digital, acquire = raw_source
    bundle = acquire()
    candidate = select(bundle, RECORD, ("II", "V1"), 100, 3100)
    actual = np.array(candidate.request.signal.samples)
    np.testing.assert_array_equal(actual, (digital[100:3100].astype(float) - 10) / 1000)
    independent = wfdb.rdrecord(str(bundle / "files" / RECORD), sampfrom=100, sampto=3100)
    np.testing.assert_array_equal(actual, independent.p_signal)
    assert candidate.request.signal.leads == STANDARD_LEADS
    assert candidate.provenance["channels"][3]["source_name"] == "AVR"
    assert candidate.provenance["channels"][3]["canonical_name"] == "aVR"
    assert candidate.provenance["statement"]["codes"]["SR"] == 0
    exported = json.dumps(candidate.provenance)
    assert "PRIVATE" not in exported and "patient_id" not in exported
    assert str(bundle) not in exported
    assert candidate.request.case.review.clinical_review == "not_reviewed"
    assert candidate.request.case.review.teaching_release == "draft"


@pytest.mark.parametrize("bad", ["0", "0(0)/mV", "200", "1000(0)/unknown", "1000/mV", "nan(0)/mV"])
def test_uncalibrated_or_implicit_units_rejected(raw_source, bad):
    payloads, _, acquire = raw_source
    payloads[RECORD + ".hea"] = payloads[RECORD + ".hea"].replace(b"1000.0(10)/mV", bad.encode())
    with pytest.raises(ValueError, match="Explicit positive"):
        select(acquire(), RECORD, ("II",))


@pytest.mark.parametrize(
    "old,new",
    [
        (b"AVR", b"MLII"),
        (b"AVR", b"II"),
        (b" 16 ", b" 16:1 "),
        (b"00001_hr.dat", b"../outside.dat"),
    ],
)
def test_header_identity_and_timing_fail_closed(raw_source, old, new):
    payloads, _, acquire = raw_source
    payloads[RECORD + ".hea"] = payloads[RECORD + ".hea"].replace(old, new)
    with pytest.raises(ValueError):
        select(acquire(), RECORD, ("II",))


@pytest.mark.parametrize("start,end", [(0, 2999), (0, 5001), (-1, 3000), (1.5, 3000), (5, 5)])
def test_invalid_windows(raw_source, start, end):
    with pytest.raises(ValueError):
        select(raw_source[2](), RECORD, ("II",), start, end)


def test_no_missing_lead_fallback(raw_source):
    with pytest.raises(ValueError, match="Missing requested"):
        select(raw_source[2](), RECORD, ("MLII",))


def test_missing_sample_sentinel_rejected(raw_source):
    payloads, digital, acquire = raw_source
    digital[2, 1] = -32768
    payloads[RECORD + ".dat"] = digital.tobytes()
    with pytest.raises(ValueError, match="Missing"):
        select(acquire(), RECORD, ("II",))


@pytest.mark.parametrize("missing", [RECORD + ".dat", "ptbxl_database.csv", "LICENSE.txt"])
def test_required_receipted_files(raw_source, missing):
    payloads, _, acquire = raw_source
    del payloads[missing]
    with pytest.raises(ValueError):
        select(acquire(), RECORD, ("II",))


def test_checksum_tampering_blocks_extraction(raw_source):
    bundle = raw_source[2]()
    (bundle / "files" / (RECORD + ".dat")).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        select(bundle, RECORD, ("II",))


@pytest.mark.parametrize("mutation", ["short", "extra", "header_length"])
def test_consistent_checksum_does_not_hide_bad_length(raw_source, mutation):
    payloads, _, acquire = raw_source
    if mutation == "header_length":
        payloads[RECORD + ".hea"] = payloads[RECORD + ".hea"].replace(b"5000\n", b"5001\n")
    else:
        data = payloads[RECORD + ".dat"]
        payloads[RECORD + ".dat"] = data[:-24] if mutation == "short" else data + b"extra"
    with pytest.raises(ValueError, match="complete multiplexed"):
        select(acquire(), RECORD, ("II",))


@pytest.mark.parametrize(
    "value",
    ["{}", "{'BAD':100}", "{'NORM':101}", "{'NORM':True}", "__import__('os').system('echo bad')"],
)
def test_invalid_statements_fail_closed(raw_source, value):
    payloads, _, acquire = raw_source
    payloads["ptbxl_database.csv"] = payloads["ptbxl_database.csv"].replace(
        b"{'NORM': 100.0, 'SR': 0.0}", value.encode()
    )
    with pytest.raises((ValueError, SyntaxError)):
        select(acquire(), RECORD, ("II",))
