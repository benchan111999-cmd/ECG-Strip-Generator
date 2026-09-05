"""Checksummed acquisition bundles, never overwritten after atomic publication."""

import hashlib
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from ecg_strip_generator.datasets.registry import Dataset
from ecg_strip_generator.models import Contract, Digest


def safe_name(name: str) -> str:
    """Portable relative file names; reject Windows aliases and URL escapes."""
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)
    }
    if any(
        not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part)
        or part.endswith(".")
        or part.split(".")[0].upper() in reserved
        for part in name.split("/")
    ):
        raise ValueError("Unsafe relative source path")
    return name


def confined(root: Path, relative: str) -> Path:
    candidate = root.absolute() / relative
    for node in (candidate, *candidate.parents):
        if node.is_symlink() or node.is_junction():
            raise ValueError("Linked data paths are not supported")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("Data path escapes its root")
    return candidate


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def selection_id(names: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(names)).encode("ascii")).hexdigest()


def checksums(payload: bytes, names: list[str]) -> dict[str, str]:
    """Parse publisher sha256sum format; never interpret unrequested paths."""
    result = {}
    requested = set(names)
    for line in payload.decode("utf-8").splitlines():
        match = re.fullmatch(r"([a-fA-F0-9]{64}) [ *]?(.+)", line)
        if match:
            name = match[2].removeprefix("./")
            if name in requested:
                if name in result:
                    raise ValueError("Duplicate official checksum entry")
                result[name] = match[1].lower()
    if set(result) != requested:
        raise ValueError("Requested file missing from official checksum list")
    return result


class FileReceipt(Contract):
    path: str
    source_url: str
    size: Annotated[int, Field(strict=True, gt=0)]
    sha256: Digest
    checksum_kind: Literal["official", "locally_observed"]


class Receipt(Contract):
    schema_version: Literal["1"] = "1"
    dataset: Dataset
    retrieved_at: datetime
    selection: Digest
    checksum_list_sha256: Digest | None
    files: Annotated[tuple[FileReceipt, ...], Field(min_length=1)]


def verify_bundle(bundle: Path, dataset: Dataset) -> Receipt:
    receipt_path = confined(bundle, "receipt.json")
    if receipt_path.stat().st_size > 2_000_000:
        raise ValueError("Receipt too large")
    receipt = Receipt.model_validate_json(receipt_path.read_bytes())
    if receipt.dataset != dataset or receipt.retrieved_at.utcoffset() is None:
        raise ValueError("Receipt source metadata or timestamp mismatch")
    names = [safe_name(item.path) for item in receipt.files]
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError("Duplicate receipt path")
    if receipt.selection != selection_id(names):
        raise ValueError("Receipt selection mismatch")
    expected_files = {f"files/{name}" for name in names} | {"receipt.json"}
    official = {}
    if dataset.checksum_file:
        sums = confined(bundle, "official-sha256sums.txt")
        if sums.stat().st_size > 16_000_000 or sha256(sums) != receipt.checksum_list_sha256:
            raise ValueError("Official checksum evidence changed")
        official = checksums(sums.read_bytes(), names)
        expected_files.add("official-sha256sums.txt")
    elif receipt.checksum_list_sha256 is not None:
        raise ValueError("Unexpected official checksum evidence")
    actual_files = set()
    for path in bundle.rglob("*"):
        confined(bundle, path.relative_to(bundle).as_posix())
        if path.is_file():
            actual_files.add(path.relative_to(bundle).as_posix())
    if actual_files != expected_files:
        raise ValueError("Bundle contains missing or unrecorded files")
    for item in receipt.files:
        path = confined(bundle, f"files/{item.path}")
        kind = "official" if dataset.checksum_file else "locally_observed"
        if item.source_url != dataset.files_url + item.path or item.checksum_kind != kind:
            raise ValueError("File source or checksum classification mismatch")
        if path.stat().st_size != item.size or sha256(path) != item.sha256:
            raise ValueError("Raw file integrity mismatch")
        if official and official[item.path] != item.sha256:
            raise ValueError("Raw file differs from official checksum")
    return receipt


def fetch(dataset: Dataset, names: list[str], root: Path) -> Path:
    """One atomic bundle per explicit selection; failures remain in staging."""
    from ecg_strip_generator.datasets.transport import download

    if not names or len(names) > 1000:
        raise ValueError("Select between 1 and 1000 files explicitly")
    names = sorted(safe_name(n) for n in names)
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError("Duplicate or case-colliding paths")
    if any(b.casefold().startswith(a.casefold() + "/") for a in names for b in names if a != b):
        raise ValueError("File and directory paths collide")
    identity = selection_id(names)
    version_path = f"{dataset.id}/{dataset.version}"
    stage_root = confined(root, f"staging/{version_path}")
    target = confined(root, f"raw/{version_path}/{identity}")
    stage_root.mkdir(parents=True, exist_ok=True)
    lock = stage_root / "fetch.lock"
    # Cooperating writers serialize; stale locks require manual inspection.
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        if target.exists():
            verify_bundle(target, dataset)
            return target
        stage = Path(tempfile.mkdtemp(prefix="attempt-", dir=stage_root))
        official = {}
        sums_digest = None
        if dataset.checksum_file:
            sums = stage / "official-sha256sums.txt"
            download(dataset.files_url + dataset.checksum_file, sums, 16_000_000)
            sums_digest = sha256(sums)
            official = checksums(sums.read_bytes(), names)
        receipts = []
        for name in names:
            destination = stage / "files" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            size = download(dataset.files_url + name, destination, 256_000_000)
            digest = sha256(destination)
            if official and official[name] != digest:
                raise ValueError("Downloaded file differs from official checksum")
            receipts.append(
                FileReceipt(
                    path=name,
                    source_url=dataset.files_url + name,
                    size=size,
                    sha256=digest,
                    checksum_kind="official" if official else "locally_observed",
                )
            )
        receipt = Receipt(
            dataset=dataset,
            retrieved_at=datetime.now(UTC),
            selection=identity,
            checksum_list_sha256=sums_digest,
            files=tuple(receipts),
        )
        with (stage / "receipt.json").open("x", encoding="utf-8") as handle:
            handle.write(receipt.model_dump_json(indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        verify_bundle(stage, dataset)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError("Raw bundle already exists")
        stage.rename(target)
        return target
    finally:
        lock.unlink()


def audit(dataset: Dataset, root: Path) -> dict:
    """Offline byte verification; a subset is never a complete dataset."""
    base = confined(root, f"raw/{dataset.id}/{dataset.version}")
    count = 0
    if base.exists():
        for bundle in sorted(base.iterdir()):
            confined(base, bundle.name)
            if not bundle.is_dir() or not re.fullmatch(r"[a-f0-9]{64}", bundle.name):
                raise ValueError("Unexpected raw bundle entry")
            receipt = verify_bundle(bundle, dataset)
            if receipt.selection != bundle.name:
                raise ValueError("Raw bundle directory identity mismatch")
            count += len(receipt.files)
    return {
        "dataset": dataset.id,
        "version": dataset.version,
        "licence": dataset.licence,
        "landing_url": dataset.landing_url,
        "verified_file_copies": count,
        "local_status": "verified_subset" if count else "not_downloaded",
    }
