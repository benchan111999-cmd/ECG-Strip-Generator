"""Preserve reference beat coordinates; screening is not rhythm diagnosis."""

from pathlib import Path

import numpy as np
import wfdb

from ecg_strip_generator.datasets.storage import Receipt, confined

BEATS = frozenset("NLRBaAJ SaV rFejnE/fQ?".replace(" ", ""))
CATEGORIES = ("pac", "pvc", "supraventricular-ectopy", "narrow-complex-tachycardia")


def read_annotations(bundle: Path, receipt: Receipt, record: str, length: int, fs: float) -> list:
    name = record + ".atr"
    if name not in {f.path for f in receipt.files}:
        raise ValueError("Reference annotation file must be in the verified bundle")
    path = confined(bundle, "files/" + name)
    if path.stat().st_size > 4_000_000:
        raise ValueError("Annotation file too large")
    ann = wfdb.rdann(str(path.with_suffix("")), "atr", pn_dir=None)
    if ann.fs is not None and ann.fs != fs:
        raise ValueError("Annotation sampling rate disagrees with signal")
    if (
        len(ann.sample) > 200_000
        or len(ann.sample) != len(ann.symbol)
        or np.any(ann.sample < 0)
        or np.any(ann.sample >= length)
        or np.any(np.diff(ann.sample) < 0)
    ):
        raise ValueError("Invalid annotation positions")
    # Never export arbitrary aux_note text, patient comments or source header comments.
    return [
        {"source_sample": int(t), "symbol": s} for t, s in zip(ann.sample, ann.symbol, strict=True)
    ]


def evidence(events: list, start: int, end: int, fs: float, target: int, category: str) -> dict:
    if category not in CATEGORIES or type(target) is not int:
        raise ValueError("Choose an explicit supported candidate category and target sample")
    selected = [e for e in events if start <= e["source_sample"] < end]
    beats = [e for e in selected if e["symbol"] in BEATS]
    matches = [i for i, e in enumerate(beats) if e["source_sample"] == target]
    if len(matches) != 1:
        raise ValueError("Target must identify exactly one source beat in the window")
    i = matches[0]
    if i == 0 or i == len(beats) - 1 or target - start < fs or end - target < fs:
        raise ValueError("Keep surrounding beats and at least one second on each side")
    symbol = beats[i]["symbol"]
    rules = {"pac": {"A", "a"}, "pvc": {"V", "r"}, "supraventricular-ectopy": {"A", "a", "J", "S"}}
    run = []
    if category in rules:
        if symbol not in rules[category]:
            raise ValueError("Reference beat symbol does not support this candidate category")
    else:
        # Four consecutive N/A/S beats, containing ectopy, each RR < 600 ms.
        # This locates review material only: QRS width and mechanism are NOT inferred.
        for first in range(max(0, i - 3), i + 1):
            part = beats[first : first + 4]
            if (
                len(part) == 4
                and first <= i < first + 4
                and all(e["symbol"] in {"N", "A", "S"} for e in part)
                and any(e["symbol"] in {"A", "S"} for e in part)
                and np.all(
                    (np.diff([e["source_sample"] for e in part]) / fs > 0)
                    & (np.diff([e["source_sample"] for e in part]) / fs < 0.6)
                )
            ):
                run = [e["source_sample"] for e in part]
                break
        if not run:
            raise ValueError("No qualifying rapid beat run around the selected target")
    return {
        "category": category,
        "status": "candidate",
        "target_source_sample": target,
        "target_symbol": symbol,
        "rapid_run_source_samples": run,
        "coordinate_rule": "half-open [start,end); relative_sample = source_sample - start",
        "events": [
            {
                **e,
                "relative_sample": e["source_sample"] - start,
                "seconds_from_window_start": (e["source_sample"] - start) / fs,
            }
            for e in selected
        ],
        "context": {"beats_before_target": i, "beats_after_target": len(beats) - i - 1},
        "clinical_review": "not_reviewed",
        "interpretation": "Source annotations and screening only; no project diagnosis. "
        "S is supraventricular ectopy, not necessarily atrial. A beat timestamp is not a "
        "QRS onset/offset. Rapid-run screening does not establish narrow QRS, sustained "
        "tachycardia, or AVNRT/AVRT. Review morphology, context and suitability manually.",
        "definition_reference": "https://physionet.org/physiotools/wpg/wpg_36.htm",
    }
