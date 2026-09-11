"""Run from repository root; reviewer-only plots, not clinical approval."""

import json
from pathlib import Path

import numpy as np
import wfdb

from ecg_strip_generator.datasets.annotations import evidence, read_annotations
from ecg_strip_generator.datasets.registry import attribution, load_registry
from ecg_strip_generator.datasets.storage import verify_bundle
from ecg_strip_generator.datasets.wfdb_adapter import read_window
from ecg_strip_generator.models import CaseManifest, RenderPreset, RenderRequest, Source
from ecg_strip_generator.provenance import signal_digest
from ecg_strip_generator.rendering.matplotlib_renderer import render

root = Path("output/candidate-review-2026-09-11")
for ds, rec, start, end, target, category, leads in [
    ("mitdb", "106", 94465, 98065, 95905, "pvc", ("MLII",)),
    ("mitdb", "119", 40686, 44286, 42126, "pvc", ("MLII",)),
    ("mitdb", "209", 201600, 205200, 203072, "narrow-complex-tachycardia", ("MLII", "V1")),
    ("mitdb", "100", 545352, 548952, 546792, "pvc", ("MLII", "V5")),
    ("svdb", "801", 4608, 5888, 5191, "narrow-complex-tachycardia", ("ECG1", "ECG2")),
    ("incartdb", "I01", 4480, 7050, 5263, "pvc", ("II", "V1", "V5")),
]:
    if (root / f"{ds}-{rec}-{target}").exists():
        continue
    p = next(Path("data/raw", ds).glob(f"*/*/files/{rec}.dat"))
    bundle = p.parent.parent
    dataset = load_registry()[ds]
    receipt = verify_bundle(bundle, dataset)
    window = read_window(bundle, receipt, rec, start, end)
    ref = wfdb.rdrecord(str(p.with_suffix("")), sampfrom=start, sampto=end)
    np.testing.assert_allclose(np.asarray(window.signal.samples), ref.p_signal, rtol=0, atol=1e-12)
    events = read_annotations(
        bundle,
        receipt,
        rec,
        window.provenance["source_sample_count"],
        window.signal.sampling_rate_hz,
    )
    statement = evidence(events, start, end, window.signal.sampling_rate_hz, target, category)
    ann = next(f for f in receipt.files if f.path == rec + ".atr")
    case = CaseManifest(
        case_id=f"review-{ds}-{rec}-{target}",
        start_sample=start,
        end_sample=end,
        source_evidence="real_manual_beat_annotation",
        source=Source(
            dataset=ds,
            version=dataset.version,
            record_id=rec,
            annotation_reference=f"{rec}.atr:sample={target}",
            licence=dataset.licence,
            attribution=dataset.landing_url,
            checksum_sha256=ann.sha256,
            checksum_kind=ann.checksum_kind,
        ),
    )
    request = RenderRequest(
        case=case,
        signal=window.signal,
        signal_sha256=signal_digest(window.signal),
        preset=RenderPreset(displayed_leads=leads, amplitude_limit_mv=4.0),
    )
    dest = root / f"{ds}-{rec}-{target}"
    render(request, dest)
    details = {
        "source": window.provenance,
        "statement": statement,
        "receipt": receipt.model_dump(mode="json"),
        "independent_wfdb_comparison": "passed",
        "amplitude_limit_mv": 4.0,
        "purpose": "Reviewer-only draft; not a student package or clinical approval",
        "attribution": attribution(
            dataset,
            "Consecutive original samples; calibrated source units; no filtering or resampling.",
        ),
    }
    (dest / "source-evidence.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    verify_bundle(bundle, dataset)
    print(dest.as_posix())
