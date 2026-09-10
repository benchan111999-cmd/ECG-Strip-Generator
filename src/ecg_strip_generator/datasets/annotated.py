"""MITDB, SVDB and INCART verified-window candidate selection."""

import re
from pathlib import Path

from ecg_strip_generator.datasets.annotations import evidence, read_annotations
from ecg_strip_generator.datasets.ptbxl import Candidate
from ecg_strip_generator.datasets.registry import attribution, load_registry
from ecg_strip_generator.datasets.storage import sha256, verify_bundle
from ecg_strip_generator.datasets.wfdb_adapter import read_window
from ecg_strip_generator.models import CaseManifest, RenderPreset, RenderRequest, Source
from ecg_strip_generator.provenance import canonical_json, signal_digest
from ecg_strip_generator.provenance import sha256 as digest
from ecg_strip_generator.validation import prepare_signal


def select(
    bundle: Path,
    dataset_id: str,
    record: str,
    leads: tuple[str, ...],
    start: int,
    end: int,
    target: int,
    category: str,
) -> Candidate:
    patterns = {"mitdb": r"[0-9]{3}", "svdb": r"[0-9]{3}", "incartdb": r"I[0-9]{2}"}
    if dataset_id not in patterns or not re.fullmatch(patterns[dataset_id], record):
        raise ValueError("Select an explicit supported annotated source record")
    dataset = load_registry()[dataset_id]
    receipt = verify_bundle(bundle, dataset)
    window = read_window(bundle, receipt, record, start, end)
    events = read_annotations(
        bundle,
        receipt,
        record,
        window.provenance["source_sample_count"],
        window.signal.sampling_rate_hz,
    )
    statement = evidence(events, start, end, window.signal.sampling_rate_hz, target, category)
    if dataset_id == "incartdb":
        statement["source_limitations"] = (
            "Beat labels were manually corrected; automatic beat locations were not "
            "manually corrected and may be misaligned. No automatic relocation is applied."
        )
    identity = digest(
        canonical_json(
            {
                "dataset": dataset_id,
                "version": dataset.version,
                "record": record,
                "start": start,
                "end": end,
                "leads": leads,
                "target": target,
                "category": category,
            }
        )
    )[:16]
    annotation = next(f for f in receipt.files if f.path == record + ".atr")
    case = CaseManifest(
        case_id="case-" + identity,
        start_sample=start,
        end_sample=end,
        source_evidence="real_manual_beat_annotation",
        source=Source(
            dataset=dataset_id,
            version=dataset.version,
            record_id=record,
            annotation_reference=f"{record}.atr:sample={target}",
            licence=dataset.licence,
            attribution=dataset.landing_url,
            checksum_sha256=annotation.sha256,
            checksum_kind=annotation.checksum_kind,
        ),
    )
    request = RenderRequest(
        case=case,
        signal=window.signal,
        signal_sha256=signal_digest(window.signal),
        preset=RenderPreset(
            displayed_leads=leads,
            time_alignment="sequential" if len(leads) == 12 else "simultaneous",
        ),
    )
    prepare_signal(request)
    provenance = {
        **window.provenance,
        "statement": statement,
        "dataset": dataset.model_dump(mode="json"),
        "acquisition_selection": receipt.selection,
        "receipt_sha256": sha256(bundle / "receipt.json"),
        "retrieved_at": receipt.retrieved_at.isoformat(),
        "checksum_list_sha256": receipt.checksum_list_sha256,
        "files": [f.model_dump(mode="json") for f in receipt.files],
    }
    if dataset_id == "svdb":
        provenance["lead_identity"] = {
            "record_specific": "unconfirmed",
            "display_names": ["ECG1", "ECG2"],
            "historical_hypothesis": {"ECG1": "presumed MLII", "ECG2": "presumed V1"},
            "basis": "Olszewski 2001 p69 footnote2; Moody personal communication; "
            "laboratory practice, not record-specific confirmation",
            "reference": "https://www.cs.cmu.edu/~bobski/pubs/tr01108-twosided.pdf#page=83",
        }
    notice = attribution(
        dataset,
        "Consecutive window; source gain and WFDB baseline/unit "
        "semantics applied; original channel names or spelling mapping retained; "
        "no filtering, resampling, annotation relocation or clinical approval.",
    )
    if dataset_id == "svdb":
        notice += (
            "\nGreenwald SD. Improved detection and classification of arrhythmias in "
            "noise-corrupted electrocardiograms using contextual information. "
            "PhD thesis, Harvard-MIT Division of Health Sciences and Technology, 1990."
        )
    return Candidate(request, provenance, notice)
