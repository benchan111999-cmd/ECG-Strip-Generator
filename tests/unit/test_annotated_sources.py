"""Non-clinical byte fixtures for source profiles, annotation context and draft boundaries."""

import hashlib
import json

import numpy as np
import pytest
import wfdb
from typer.testing import CliRunner

from ecg_strip_generator.cli import app
from ecg_strip_generator.coverage import report
from ecg_strip_generator.datasets import transport
from ecg_strip_generator.datasets.annotated import select
from ecg_strip_generator.datasets.annotations import evidence
from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import fetch
from ecg_strip_generator.models import STANDARD_LEADS
from ecg_strip_generator.teaching_packages import audit_draft, build_draft


@pytest.fixture
def source_factory(tmp_path, monkeypatch):
    def make(dataset, mutate=None):
        fs = {"mitdb": 360, "svdb": 128, "incartdb": 257}[dataset]
        record = "I01" if dataset == "incartdb" else "800" if dataset == "svdb" else "100"
        leads = (
            ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]
            if dataset == "incartdb"
            else ["ECG1", "ECG2"]
            if dataset == "svdb"
            else ["MLII", "V1"]
        )
        fmt = "16" if dataset == "incartdb" else "212"
        baseline = 1024 if dataset == "mitdb" else 0
        values = np.arange(fs * 12 * len(leads)).reshape(-1, len(leads)) % 201 - 100 + baseline
        if fmt == "16":
            data = values.astype("<i2").tobytes()
        else:
            v = values & 4095
            data = (
                np.column_stack(
                    (v[:, 0] & 255, (v[:, 0] >> 8) | ((v[:, 1] >> 8) << 4), v[:, 1] & 255)
                )
                .astype(np.uint8)
                .tobytes()
            )
        header = (
            f"{record} {len(leads)} {fs} {fs * 12}\n"
            + "".join(
                f"{record}.dat {fmt} 200 12 {baseline} {values[0, i]} 0 0 {lead}\n"
                for i, lead in enumerate(leads)
            )
            + "# PRIVATE-PATIENT-NOTE\n"
        )
        annotation_dir = tmp_path / ("annotations-" + dataset)
        annotation_dir.mkdir()
        times = np.array([int(s * fs) for s in [1, 2, 3, 4, 4.4, 4.8, 5.2, 6, 7, 8, 9, 10]])
        wfdb.wrann(
            record,
            "atr",
            sample=times,
            symbol=["N", "N", "N", "N", "S", "S", "S", "N", "A", "V", "N", "N"],
            aux_note=["PRIVATE-AUX"] * len(times),
            write_dir=str(annotation_dir),
        )
        payloads = {
            record + ".hea": header.encode(),
            record + ".dat": data,
            record + ".atr": (annotation_dir / (record + ".atr")).read_bytes(),
        }
        if mutate:
            mutate(payloads, record)

        def download(url, destination, limit):
            name = url.split("/1.0.0/")[1]
            data = (
                "".join(
                    f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in payloads.items()
                ).encode()
                if name == "SHA256SUMS.txt"
                else payloads[name]
            )
            assert len(data) <= limit
            destination.write_bytes(data)
            return len(data)

        monkeypatch.setattr(transport, "download", download)
        bundle = fetch(load_registry()[dataset], list(payloads), tmp_path / "data")
        return bundle, record, fs, values, tuple(leads)

    return make


@pytest.mark.parametrize("dataset", ["mitdb", "svdb", "incartdb"])
def test_original_samples_coordinates_and_privacy(source_factory, dataset):
    bundle, record, fs, values, leads = source_factory(dataset)
    candidate = select(bundle, dataset, record, (leads[0],), 0, 10 * fs, 7 * fs, "pac")
    baseline = 1024 if dataset == "mitdb" else 0
    np.testing.assert_array_equal(
        candidate.request.signal.samples, (values[: 10 * fs].astype(float) - baseline) / 200
    )
    independent = wfdb.rdrecord(str(bundle / "files" / record), sampto=10 * fs)
    np.testing.assert_array_equal(candidate.request.signal.samples, independent.p_signal)
    ev = candidate.provenance["statement"]
    assert ev["target_symbol"] == "A"
    assert all(e["source_sample"] == e["relative_sample"] for e in ev["events"])
    assert all(e["source_sample"] < 10 * fs for e in ev["events"])
    assert "PRIVATE" not in json.dumps(candidate.provenance)
    assert str(bundle) not in json.dumps(candidate.provenance)
    assert candidate.request.case.review.clinical_review == "not_reviewed"
    if dataset == "svdb":
        assert candidate.request.signal.leads == ("ECG1", "ECG2")
        assert candidate.provenance["lead_identity"]["record_specific"] == "unconfirmed"
    if dataset == "incartdb":
        assert "not manually corrected" in ev["source_limitations"]


@pytest.mark.parametrize(
    "category,seconds",
    [("pac", 7), ("pvc", 8), ("supraventricular-ectopy", 4.4), ("narrow-complex-tachycardia", 4.4)],
)
def test_category_evidence_and_draft_output(source_factory, tmp_path, category, seconds):
    bundle, record, fs, _, leads = source_factory("svdb")
    root = build_draft(
        bundle,
        record,
        leads,
        tmp_path / "draft",
        0,
        10 * fs,
        dataset_id="svdb",
        target=int(seconds * fs),
        category=category,
    )
    assert audit_draft(root)["status"] == "draft"
    result = report([root, root])
    row = next(r for r in result["categories"] if r["category"] == category)
    assert row["status"] == "candidate" and row["candidate_count"] == 1
    assert row["released_count"] == 0
    student = next((root / "student").iterdir())
    assert "presumed MLII" not in (student / "README.md").read_text()
    assert "unconfirmed" in (student / "README.md").read_text()
    for p in root.rglob("*"):
        if p.is_file():
            assert b"PRIVATE" not in p.read_bytes()
    with pytest.raises(FileExistsError):
        build_draft(
            bundle,
            record,
            leads,
            root,
            0,
            10 * fs,
            dataset_id="svdb",
            target=int(seconds * fs),
            category=category,
        )
    manifest_path = next((root / "instructor").glob("*/manifest.json"))
    m = json.loads(manifest_path.read_bytes())
    m["case"]["review"]["clinical_review"] = "approved"
    m["case"]["review"]["teaching_release"] = "approved"
    manifest_path.write_text(json.dumps(m))
    inventory = json.loads((root / "package-files.json").read_bytes())
    inventory[manifest_path.relative_to(root).as_posix()] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    (root / "package-files.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError, match="review state"):
        report([root])


@pytest.mark.parametrize("leads", [("II",), ("MLII",), ("V1",), STANDARD_LEADS])
def test_svdb_no_standard_lead_substitution(source_factory, leads):
    bundle, record, fs, _, _ = source_factory("svdb")
    with pytest.raises(ValueError, match="Missing requested"):
        select(bundle, "svdb", record, leads, 0, 10 * fs, 7 * fs, "pac")


@pytest.mark.parametrize(
    "category,seconds",
    [("pac", 4.4), ("pvc", 7), ("narrow-complex-tachycardia", 8), ("AVNRT", 4.4), ("AVRT", 4.4)],
)
def test_no_unsupported_labels(source_factory, category, seconds):
    bundle, record, fs, _, leads = source_factory("svdb")
    with pytest.raises(ValueError):
        select(bundle, "svdb", record, leads, 0, 10 * fs, int(seconds * fs), category)


@pytest.mark.parametrize("gain", ["0", "nan", "200/uV", "200/unknown", "-200"])
def test_calibration_refusal(source_factory, gain):
    def mutate(p, r):
        p[r + ".hea"] = p[r + ".hea"].replace(b" 200 ", f" {gain} ".encode())

    bundle, record, fs, _, leads = source_factory("svdb", mutate)
    with pytest.raises(ValueError, match="Explicit positive"):
        select(bundle, "svdb", record, leads, 0, 10 * fs, 7 * fs, "pac")


@pytest.mark.parametrize("change", ["missing-atr", "short-data", "skew", "missing-sample"])
def test_bad_source_refusal(source_factory, change):
    def mutate(p, r):
        if change == "missing-atr":
            del p[r + ".atr"]
        elif change == "short-data":
            p[r + ".dat"] = p[r + ".dat"][:-3]
        elif change == "skew":
            p[r + ".hea"] = p[r + ".hea"].replace(b" 212 ", b" 212:1 ")
        else:
            data = bytearray(p[r + ".dat"])
            data[:2] = bytes([0, (data[1] & 240) | 8])
            p[r + ".dat"] = bytes(data)

    bundle, record, fs, _, leads = source_factory("svdb", mutate)
    with pytest.raises(ValueError):
        select(bundle, "svdb", record, leads, 0, 10 * fs, 7 * fs, "pac")


def test_half_open_coordinates_and_context():
    events = [
        {"source_sample": n, "symbol": "A" if n == 500 else "N"} for n in [100, 300, 500, 700, 900]
    ]
    result = evidence(events, 100, 900, 100, 500, "pac")
    assert [e["relative_sample"] for e in result["events"]] == [0, 200, 400, 600]
    for start, end in [(500, 900), (100, 501), (490, 900), (100, 550)]:
        with pytest.raises(ValueError):
            evidence(events, start, end, 100, 500, "pac")
    with pytest.raises(ValueError):
        evidence(events, 100, 900, 100, 501, "pac")


def test_cli_offline_and_coverage_gaps(source_factory, tmp_path, monkeypatch):
    bundle, record, fs, _, _ = source_factory("svdb")
    monkeypatch.setattr(transport, "download", lambda *a: pytest.fail("Unexpected network"))
    runner = CliRunner()
    dest = tmp_path / "cli"
    args = [
        "cases",
        "draft-annotated",
        str(bundle),
        "--dataset",
        "svdb",
        "--record",
        record,
        "--start-sample",
        "0",
        "--end-sample",
        str(10 * fs),
        "--target-sample",
        str(7 * fs),
        "--category",
        "pac",
        "--output",
        str(dest),
    ]
    assert runner.invoke(app, args).exit_code == 1
    result = runner.invoke(app, args + ["--lead", "ECG1", "--lead", "ECG2"])
    assert result.exit_code == 0, result.output
    assert runner.invoke(app, ["coverage", "report", "--package", str(dest)]).exit_code == 0
    assert all(r["status"] == "gap" for r in report([])["categories"])
