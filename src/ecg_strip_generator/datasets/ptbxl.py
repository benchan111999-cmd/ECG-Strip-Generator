"""Verified PTB-XL candidate selection; no patient metadata or clinical approval."""

import ast
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from ecg_strip_generator.datasets.registry import attribution, load_registry
from ecg_strip_generator.datasets.storage import confined, sha256, verify_bundle
from ecg_strip_generator.datasets.wfdb_adapter import read_window
from ecg_strip_generator.models import CaseManifest, RenderPreset, RenderRequest, Source
from ecg_strip_generator.provenance import canonical_json, signal_digest
from ecg_strip_generator.provenance import sha256 as digest


@dataclass(frozen=True)
class Candidate:
    request: RenderRequest
    provenance: dict
    attribution: str


def statement(files: Path, record: str) -> dict:
    """Export only ECG id and statement codes, never patient id or report text."""
    with (files / "ptbxl_database.csv").open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["filename_hr"] == record]
    if len(rows) != 1:
        raise ValueError("Record must match exactly one PTB-XL metadata row")
    row = rows[0]
    if not row["ecg_id"].isdigit() or len(row["scp_codes"]) > 10_000:
        raise ValueError("Invalid ECG identifier or statement payload")
    codes = ast.literal_eval(row["scp_codes"])
    if not isinstance(codes, dict) or not codes:
        raise ValueError("Missing dataset diagnostic statements")
    with (files / "scp_statements.csv").open(encoding="utf-8", newline="") as handle:
        descriptions = {r[""]: r["description"] for r in csv.DictReader(handle)}
    for key, value in codes.items():
        if key not in descriptions or type(value) not in (float, int) or not 0 <= value <= 100:
            raise ValueError("Unknown statement or invalid source likelihood")
    return {
        "ecg_id": row["ecg_id"],
        "field": "scp_codes",
        "codes": codes,
        "descriptions": {k: descriptions[k] for k in codes},
        "interpretation": "Dataset statements only; not a project diagnosis. "
        "Zero is a source value, not proof of absence.",
    }


def select(
    bundle: Path, record: str, leads: tuple[str, ...], start: int = 0, end: int = 5000
) -> Candidate:
    if not re.fullmatch(r"records500/[0-9]{5}/[0-9]{5}_hr", record):
        raise ValueError("Select an explicit PTB-XL records500 record")
    dataset = load_registry()["ptb-xl"]
    receipt = verify_bundle(bundle, dataset)
    required = {"ptbxl_database.csv", "scp_statements.csv", "LICENSE.txt"}
    if not required <= {f.path for f in receipt.files}:
        raise ValueError("Verified metadata, statement dictionary and licence are required")
    evidence = statement(confined(bundle, "files"), record)
    window = read_window(bundle, receipt, record, start, end)
    preset = RenderPreset(
        displayed_leads=leads, time_alignment="sequential" if len(leads) == 12 else "simultaneous"
    )
    identity = digest(
        canonical_json(
            {
                "dataset": dataset.id,
                "version": dataset.version,
                "record": record,
                "start": start,
                "end": end,
                "leads": leads,
            }
        )
    )[:16]
    header = next(f for f in receipt.files if f.path == record + ".hea")
    case = CaseManifest(
        case_id="case-" + identity,
        start_sample=start,
        end_sample=end,
        source_evidence="real_dataset_diagnostic_statement",
        source=Source(
            dataset=dataset.id,
            version=dataset.version,
            record_id=Path(record).name,
            annotation_reference="ptbxl_database.csv:ecg_id=" + evidence["ecg_id"] + ":scp_codes",
            licence=dataset.licence,
            attribution="PTB-XL 1.0.3; Wagner et al.; "
            "https://doi.org/10.13026/kfzx-aw45; CC-BY-4.0",
            checksum_sha256=header.sha256,
            checksum_kind=header.checksum_kind,
        ),
    )
    request = RenderRequest(
        case=case, signal=window.signal, signal_sha256=signal_digest(window.signal), preset=preset
    )
    from ecg_strip_generator.validation import prepare_signal

    prepare_signal(request)
    provenance = {
        **window.provenance,
        "statement": evidence,
        "dataset": dataset.model_dump(mode="json"),
        "acquisition_selection": receipt.selection,
        "receipt_sha256": sha256(bundle / "receipt.json"),
        "retrieved_at": receipt.retrieved_at.isoformat(),
        "checksum_list_sha256": receipt.checksum_list_sha256,
        "files": [f.model_dump(mode="json") for f in receipt.files],
    }
    return Candidate(
        request,
        provenance,
        attribution(
            dataset,
            "Consecutive window selected; digital values converted using explicit "
            "header gain and baseline; lead spelling normalized; selected leads plotted. "
            "No filtering, resampling or clinical approval.",
        ),
    )
