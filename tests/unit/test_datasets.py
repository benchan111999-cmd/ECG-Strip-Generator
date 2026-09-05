"""Offline source lifecycle tests with non-clinical bytes only."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from ecg_strip_generator.cli import app
from ecg_strip_generator.datasets import transport
from ecg_strip_generator.datasets.registry import Dataset, attribution, load_registry
from ecg_strip_generator.datasets.storage import audit, checksums, fetch, safe_name, verify_bundle


@pytest.fixture
def dataset():
    return load_registry()["nsrdb"]


@pytest.fixture
def server(monkeypatch):
    payloads = {"a.hea": b"non-clinical header\n", "nested/a.dat": b"fixture bytes"}
    payloads["SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(value).hexdigest()}  {key}\n" for key, value in payloads.items()
    ).encode()
    calls = []

    def download(url, destination, limit):
        name = url.split("/1.0.0/")[1]
        calls.append(name)
        payload = payloads[name]
        if isinstance(payload, BaseException):
            destination.write_bytes(b"interrupted")
            raise payload
        assert len(payload) <= limit
        destination.write_bytes(payload)
        return len(payload)

    monkeypatch.setattr(transport, "download", download)
    return payloads, calls


def test_registry_complete_and_not_runtime_state():
    registry = load_registry()
    assert set(registry) == {
        "ptb-xl",
        "incartdb",
        "mitdb",
        "svdb",
        "afdb",
        "vfdb",
        "nsrdb",
        "cudb",
        "sddb",
    }
    assert sum(d.role == "core" for d in registry.values()) == 7
    for d in registry.values():
        assert d.citation and d.limitations and d.checksum_file == "SHA256SUMS.txt"
        notice = attribution(d, "None; original bytes.")
        assert d.licence_url in notice and d.citation in notice
        assert "Changes: None" in notice and "Pollard" in notice
        assert "download_status" not in Dataset.model_fields


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", "latest"),
        ("id", "../a"),
        ("licence", "unknown"),
        ("citation", ""),
        ("limitations", []),
        ("checksum_file", None),
    ],
)
def test_registry_fails_closed(dataset, field, value):
    raw = dataset.model_dump()
    raw[field] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate(raw)


@pytest.mark.parametrize(
    "name",
    [
        "../a",
        "/a",
        "C:/a",
        "a\\b",
        "a//b",
        "a/..",
        "%2e%2e/a",
        "a?x",
        "a#b",
        "a:stream",
        "NUL.dat",
        "com1",
        "a.",
        "",
        "a/CON.txt",
    ],
)
def test_portable_path_rejection(name):
    with pytest.raises(ValueError):
        safe_name(name)


def test_official_batch_and_idempotent_fetch(dataset, server, tmp_path):
    payloads, calls = server
    root = tmp_path / "data"
    bundle = fetch(dataset, ["nested/a.dat", "a.hea"], root)
    receipt = verify_bundle(bundle, dataset)
    assert all(f.checksum_kind == "official" for f in receipt.files)
    assert receipt.retrieved_at.utcoffset().total_seconds() == 0
    assert (bundle / "files/nested/a.dat").read_bytes() == payloads["nested/a.dat"]
    before = {p: p.read_bytes() for p in bundle.rglob("*") if p.is_file()}
    assert fetch(dataset, ["a.hea", "nested/a.dat"], root) == bundle
    assert len(calls) == 3
    assert all(p.read_bytes() == data for p, data in before.items())
    assert audit(dataset, root)["local_status"] == "verified_subset"


@pytest.mark.parametrize("failure", [OSError("connection lost"), KeyboardInterrupt()])
def test_interruption_never_promotes_partial_batch(dataset, server, tmp_path, failure):
    payloads, _ = server
    payloads["nested/a.dat"] = failure
    with pytest.raises(type(failure)):
        fetch(dataset, ["a.hea", "nested/a.dat"], tmp_path)
    assert not (tmp_path / "raw").exists()
    assert list((tmp_path / "staging").rglob("a.hea"))
    assert not list(tmp_path.rglob("fetch.lock"))
    assert audit(dataset, tmp_path)["local_status"] == "not_downloaded"


def test_corrupt_download_and_missing_checksum_rejected(dataset, server, tmp_path):
    payloads, _ = server
    payloads["a.hea"] = b"different bytes"
    with pytest.raises(ValueError, match="official checksum"):
        fetch(dataset, ["a.hea"], tmp_path)
    with pytest.raises(ValueError, match="missing"):
        fetch(dataset, ["absent.hea"], tmp_path)
    assert not (tmp_path / "raw").exists()


def test_failed_official_evidence_never_falls_back(dataset, server, tmp_path):
    server[0]["SHA256SUMS.txt"] = OSError("unavailable")
    with pytest.raises(OSError):
        fetch(dataset, ["a.hea"], tmp_path)
    assert server[1] == ["SHA256SUMS.txt"]
    assert not (tmp_path / "raw").exists()


def test_locally_observed_requires_reviewed_absence(dataset, server, tmp_path):
    data = dataset.model_dump()
    data.update(checksum_file=None, checksum_absence_reason="Test-only source lacks checksums")
    local = Dataset.model_validate(data)
    bundle = fetch(local, ["a.hea"], tmp_path)
    receipt = verify_bundle(bundle, local)
    assert receipt.files[0].checksum_kind == "locally_observed"
    assert receipt.checksum_list_sha256 is None
    assert server[1] == ["a.hea"]


@pytest.mark.parametrize("change", ["signal", "receipt", "evidence", "extra", "missing"])
def test_audit_detects_raw_tampering(dataset, server, tmp_path, change):
    bundle = fetch(dataset, ["a.hea"], tmp_path)
    if change == "signal":
        (bundle / "files/a.hea").write_bytes(b"changed")
    elif change == "receipt":
        p = bundle / "receipt.json"
        raw = json.loads(p.read_text())
        raw["files"][0]["checksum_kind"] = "locally_observed"
        p.write_text(json.dumps(raw))
    elif change == "evidence":
        (bundle / "official-sha256sums.txt").write_bytes(b"changed")
    elif change == "extra":
        (bundle / "extra").write_bytes(b"untracked")
    else:
        (bundle / "files/a.hea").unlink()
    with pytest.raises((ValueError, OSError)):
        audit(dataset, tmp_path)
    before_calls = len(server[1])
    with pytest.raises((ValueError, OSError)):
        fetch(dataset, ["a.hea"], tmp_path)
    assert len(server[1]) == before_calls


def test_lock_is_not_broken(dataset, server, tmp_path):
    lock = tmp_path / "staging/nsrdb/1.0.0/fetch.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("other writer")
    with pytest.raises(FileExistsError):
        fetch(dataset, ["a.hea"], tmp_path)
    assert lock.read_text() == "other writer" and server[1] == []


@pytest.mark.parametrize("names", [[], ["a", "A"], ["a", "a/b"], ["a", "A/b"]])
def test_bad_selection_never_starts(dataset, server, tmp_path, names):
    with pytest.raises(ValueError):
        fetch(dataset, names, tmp_path)
    assert server[1] == []


def test_duplicate_checksum_rejected():
    line = f"{'a' * 64}  a.hea\n".encode()
    with pytest.raises(ValueError, match="Duplicate"):
        checksums(line * 2, ["a.hea"])


@pytest.mark.parametrize("separator", [" ", "  ", " *"])
def test_publisher_and_gnu_checksum_formats(separator):
    line = f"{'a' * 64}{separator}./a.hea\n".encode()
    assert checksums(line, ["a.hea"]) == {"a.hea": "a" * 64}


def test_cli_offline_audit_and_attribution(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline audit attempted network")

    monkeypatch.setattr(transport, "download", forbidden)
    runner = CliRunner()
    result = runner.invoke(app, ["datasets", "audit", "--data-root", str(tmp_path / "data")])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.stdout)
    assert len(rows) == 9 and all(r["local_status"] == "not_downloaded" for r in rows)
    assert not (tmp_path / "data").exists()
    notice = runner.invoke(app, ["datasets", "attribution", "ptb-xl", "--changes", "None"])
    assert notice.exit_code == 0 and "CC-BY-4.0" in notice.stdout
    assert runner.invoke(app, ["datasets", "fetch", "nsrdb"]).exit_code != 0
    assert runner.invoke(app, ["datasets", "fetch", "unknown", "--file", "a"]).exit_code != 0


def test_cli_fetch_and_corrupt_audit(dataset, server, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app, ["datasets", "fetch", dataset.id, "--file", "a.hea", "--data-root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    next((tmp_path / "raw").rglob("a.hea")).write_bytes(b"bad")
    result = runner.invoke(app, ["datasets", "audit", "--data-root", str(tmp_path)])
    assert result.exit_code == 1
    assert any(r["local_status"] == "failed" for r in json.loads(result.stdout))


def test_rename_failure_retains_only_staging(dataset, server, tmp_path, monkeypatch):
    def denied(*args):
        raise OSError("rename failed")

    monkeypatch.setattr(Path, "rename", denied)
    with pytest.raises(OSError, match="rename failed"):
        fetch(dataset, ["a.hea"], tmp_path)
    assert not list((tmp_path / "raw").rglob("receipt.json"))
    assert list((tmp_path / "staging").rglob("receipt.json"))
