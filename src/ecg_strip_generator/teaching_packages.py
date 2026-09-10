"""Source-verified draft packaging with a closed student surface, not a release engine."""

import json
import re
import tempfile
from pathlib import Path

from ecg_strip_generator.datasets.ptbxl import select
from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import confined, verify_bundle
from ecg_strip_generator.provenance import canonical_json, sha256
from ecg_strip_generator.rendering.matplotlib_renderer import render


def verify_payloads(root: Path, payloads: dict[str, bytes]) -> None:
    """Exact file allowlist and readback; no unreviewed text can enter a student export."""
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(payloads):
        raise ValueError("Draft package has missing or unexpected files")
    for name, expected in payloads.items():
        if confined(root, name).read_bytes() != expected:
            raise ValueError("Draft package readback mismatch")


def build_draft(
    bundle: Path,
    record: str,
    leads: tuple[str, ...],
    output: Path,
    start: int = 0,
    end: int = 5000,
    *,
    dataset_id: str = "ptb-xl",
    target: int | None = None,
    category: str | None = None,
) -> Path:
    """Only source-verified requests constructed here may upgrade technical checks."""
    output = confined(output.parent, output.name)
    if output.exists():
        raise FileExistsError("Draft destination exists; never overwrite")
    if output.resolve().is_relative_to(bundle.resolve()) or bundle.resolve().is_relative_to(output):
        raise ValueError("Draft output must be separate from raw source data")
    if dataset_id == "ptb-xl":
        if target is not None or category is not None:
            raise ValueError("PTB-XL uses dataset statements, not a beat target")
        candidate = select(bundle, record, leads, start, end)
    else:
        from ecg_strip_generator.datasets.annotated import select as select_annotated

        candidate = select_annotated(
            bundle, dataset_id, record, leads, start, end, target, category
        )
    request = candidate.request
    # No caller title, prompt, case id, diagnosis, metadata or free-text route into figures.
    if request.preset.title or request.preset.teaching_prompt:
        raise ValueError("Student figures accept only fixed neutral text")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".draft-", dir=output.parent))
    instructor = stage / "instructor" / request.case.case_id
    manifest = render(request, instructor)
    # Recheck immutable evidence after decoding/rendering, before promotion.
    dataset = load_registry()[dataset_id]
    verify_bundle(bundle, dataset)
    manifest["case"]["review"]["technical_validation"] = "passed"
    manifest["validation"]["raw_source_checksum"] = "verified"
    manifest["validation"]["scope"] += [
        "raw_source_files",
        "source_profile_adc_calibration",
        "consecutive_source_samples",
        "source_lead_mapping",
    ]
    manifest["source_provenance"] = candidate.provenance
    manifest["attribution"] = candidate.attribution
    manifest["package_status"] = "draft"
    manifest["validation"]["student_surface"] = "fixed-text and exact-file allowlist"
    # The renderer's provisional manifest is replaced only inside unpublished staging.
    (instructor / "manifest.json").write_bytes(canonical_json(manifest))
    notice = candidate.attribution.encode("utf-8") + b"\n"
    if dataset_id == "ptb-xl":
        licence = confined(bundle, "files/LICENSE.txt").read_bytes()
    else:
        licence = (
            "Source database licence notice (link, not a copy of the licence text).\n"
            f"{dataset.licence}: {dataset.licence_url}\n"
            "Retain this notice and ATTRIBUTION.txt with these derivatives.\n"
            "No project code licence or clinical endorsement is granted.\n"
        ).encode()
    statement = candidate.provenance["statement"]
    instructor_notes = (
        "# Instructor draft\n\nDataset statements (not a project diagnosis):\n\n"
        + json.dumps(statement, ensure_ascii=True, indent=2)
        + "\n\nClinical review: not_reviewed. Teaching release: draft.\n"
        + "Source likelihood values are preserved; zero does not establish absence.\n"
        + "Inspect morphology and suitability manually before approving any label.\n"
    ).encode()
    if dataset_id == "svdb":
        instructor_notes += (
            b"\nRecorded ECG1/ECG2 retained. Presumed MLII/V1 based on historical laboratory "
            b"practice only; individual-record lead identity unconfirmed.\n"
            b"Olszewski 2001, p69 footnote2, citing Moody personal communication.\n"
            b"https://www.cs.cmu.edu/~bobski/pubs/tr01108-twosided.pdf#page=83\n"
        )
    student_notes = (
        b"# ECG interpretation draft\n\nReview the rate, rhythm, intervals and morphology.\n"
        b"Not clinically reviewed. Not for teaching release or patient care.\n"
        b"Print PDF at 100%; disable fit-to-page. PNG is for screen display.\n"
        b"Keep ATTRIBUTION.txt and LICENSE.txt with these derivatives.\n"
    )
    if dataset_id == "svdb":
        student_notes += (
            b"ECG1/ECG2 are recorded channel names; standard lead positions unconfirmed.\n"
        )
    payloads = {}
    for role, notes in (("student", student_notes), ("instructor", instructor_notes)):
        prefix = f"{role}/{request.case.case_id}/"
        payloads.update(
            {
                prefix + "README.md": notes,
                prefix + "ATTRIBUTION.txt": notice,
                prefix + "LICENSE.txt": licence,
            }
        )
        for name in ("strip.pdf", "strip.png"):
            payloads[prefix + name] = (instructor / name).read_bytes()
    payloads[f"instructor/{request.case.case_id}/manifest.json"] = canonical_json(manifest)
    for name, data in payloads.items():
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(data)
    verify_payloads(stage, payloads)
    inventory = {name: sha256(data) for name, data in payloads.items()}
    (stage / "package-files.json").write_bytes(canonical_json(inventory))
    audit_draft(stage)
    if output.exists():
        raise FileExistsError("Draft destination appeared during generation")
    stage.rename(output)
    return output


def audit_draft(output: Path) -> dict:
    """Readback of expected surfaces and recorded hashes; not clinical validation."""
    inventory = json.loads(confined(output, "package-files.json").read_bytes())
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != set(inventory) | {"package-files.json"}:
        raise ValueError("Unexpected or missing package file")
    for name, expected in inventory.items():
        if sha256(confined(output, name).read_bytes()) != expected:
            raise ValueError("Package file checksum mismatch")
    manifests = list(confined(output, "instructor").glob("*/manifest.json"))
    if len(manifests) != 1:
        raise ValueError("Expected exactly one instructor case manifest")
    manifest = json.loads(manifests[0].read_bytes())
    case_id = manifest["case"]["case_id"]
    if not re.fullmatch(r"case-[a-f0-9]{16}", case_id):
        raise ValueError("Non-neutral case identifier")
    student_files = {
        f"student/{case_id}/{name}"
        for name in ("strip.pdf", "strip.png", "README.md", "ATTRIBUTION.txt", "LICENSE.txt")
    }
    if {n for n in inventory if n.startswith("student/")} != student_files:
        raise ValueError("Unexpected student surface")
    if manifest["case"]["review"] != {
        "technical_validation": "passed",
        "clinical_review": "not_reviewed",
        "teaching_release": "draft",
    }:
        raise ValueError("Unexpected draft review state")
    for role in ("student", "instructor"):
        base = confined(output, f"{role}/{case_id}")
        for name, expected in manifest["outputs"].items():
            if sha256(confined(base, name).read_bytes()) != expected["sha256"]:
                raise ValueError("Draft output checksum mismatch")
    return {
        "case_id": case_id,
        "status": "draft",
        "output_checksums": "passed",
        "clinical_review": "not_reviewed",
    }
