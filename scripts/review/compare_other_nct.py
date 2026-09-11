"""Unfiltered visual screening of additional real-source rapid runs."""

from pathlib import Path

import matplotlib
import numpy as np
import wfdb

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import verify_bundle

items = []
for ds, rec in [("svdb", "840"), ("svdb", "841"), ("svdb", "842")]:
    files = list(Path("data/raw", ds).glob(f"*/*/files/{rec}.dat"))
    if not files:
        continue
    p = files[0]
    verify_bundle(p.parent.parent, load_registry()[ds])
    a = wfdb.rdann(str(p.with_suffix("")), "atr")
    fs = wfdb.rdheader(str(p.with_suffix(""))).fs
    runs, run = [], []
    for t, s in zip(a.sample, a.symbol, strict=True):
        if s not in {"N", "A", "S", "J", "V", "F", "Q", "L", "R"}:
            continue
        if s not in {"N", "A", "S", "J"} or (run and t - run[-1][0] >= 0.6 * fs):
            if len(run) >= 4 and any(s in {"S", "A", "J"} for _, s in run):
                runs.append(run)
            run = []
        if s in {"N", "A", "S", "J"}:
            run.append((int(t), s))
    if len(run) >= 4 and any(s in {"S", "A", "J"} for _, s in run):
        runs.append(run)
    runs.sort(key=lambda r: len(r), reverse=True)
    for run in runs[:2]:
        start = max(0, run[0][0] - int(fs))
        if len(run) > 25:
            start = run[len(run) // 2][0] - int(5 * fs)
        print(
            ds,
            rec,
            len(run),
            run[0],
            run[-1],
            "window",
            start,
            "bpm",
            60 * fs / np.median(np.diff([t for t, s in run])),
        )
        r = wfdb.rdrecord(str(p.with_suffix("")), sampfrom=start, sampto=start + int(10 * fs))
        items.append((f"{ds} {rec} start={start} fs={fs}", r))
fig, axes = plt.subplots(
    len(items), 1, figsize=(16, 2 * len(items)), layout="constrained", squeeze=False
)
for ax, (title, r) in zip(axes[:, 0], items, strict=True):
    ax.plot(np.arange(len(r.p_signal)) / r.fs, r.p_signal[:, 0], color="black", lw=0.7)
    ax.set_title(title)
    ax.grid(alpha=0.2)
fig.savefig("output/candidate-review-2026-09-11/other-nct-comparison.png", dpi=130)
