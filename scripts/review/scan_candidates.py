"""Run from repository root to inspect checksum-verified local beat records."""

from collections import Counter
from pathlib import Path

import wfdb

from ecg_strip_generator.datasets.annotations import BEATS
from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import verify_bundle

for p in Path("data/raw").glob("*/*/*/files/*.atr"):
    ds = p.parts[2]
    verify_bundle(p.parent.parent, load_registry()[ds])
    a = wfdb.rdann(str(p.with_suffix("")), "atr")
    h = wfdb.rdheader(str(p.with_suffix("")))
    beats = [(int(t), s) for t, s in zip(a.sample, a.symbol, strict=False) if s in BEATS]
    print(ds, p.stem, h.fs, Counter(a.symbol))
    print("PVC samples:", [t for t, s in beats if s == "V"][:20])
    print(
        "Rhythm labels:",
        [(int(t), n) for t, n in zip(a.sample, a.aux_note, strict=False) if n.startswith("(")][:30],
    )
    runs = []
    run = []
    for t, s in beats:
        if s in {"N", "A", "S"}:
            if run and (t - run[-1][0]) / h.fs >= 0.6:
                if len(run) > 4:
                    runs.append(run)
                run = []
            run.append((t, s))
        else:
            if len(run) > 4:
                runs.append(run)
            run = []
    if len(run) > 4:
        runs.append(run)
    runs.sort(key=lambda r: r[-1][0] - r[0][0], reverse=True)
    print(
        "Longest rapid runs:",
        [
            (
                r[0][0],
                r[-1][0],
                len(r),
                round((r[-1][0] - r[0][0]) / h.fs, 2),
                Counter(s for _, s in r),
            )
            for r in runs[:5]
        ],
    )
