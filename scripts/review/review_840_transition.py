"""Source-preserving dual-channel review; no automated P-wave diagnosis."""

import json
from pathlib import Path

import matplotlib
import numpy as np
import wfdb

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ecg_strip_generator.datasets.annotations import BEATS
from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import verify_bundle
from ecg_strip_generator.datasets.wfdb_adapter import read_window

dest = Path("output/candidate-review-2026-09-11/svdb840-transition-review")
dest.mkdir(exist_ok=True)
p = next(Path("data/raw/svdb").glob("*/*/files/840.dat"))
receipt = verify_bundle(p.parent.parent, load_registry()["svdb"])
start, end, fs = 79758, 88718, 128
r = wfdb.rdrecord(str(p.with_suffix("")), sampfrom=start, sampto=end)
for lo in range(start, end, 1280):
    w = read_window(p.parent.parent, receipt, "840", lo, min(lo + 1280, end))
    np.testing.assert_allclose(
        np.asarray(w.signal.samples),
        r.p_signal[lo - start : min(lo + 1280, end) - start],
        rtol=0,
        atol=1e-12,
    )
a = wfdb.rdann(str(p.with_suffix("")), "atr")
beats = [
    (int(t), s) for t, s in zip(a.sample, a.symbol, strict=True) if start <= t < end and s in BEATS
]
fig, axes = plt.subplots(7, 1, figsize=(18, 16), layout="constrained")
for k, ax in enumerate(axes):
    lo = start + k * 1280
    t = np.arange(lo, lo + 1280) / fs
    for ch, offset in [(0, 1.3), (1, -1.3)]:
        ax.plot(t, r.p_signal[k * 1280 : (k + 1) * 1280, ch] + offset, lw=0.65, color="black")
        ax.text(t[0], offset + 1, r.sig_name[ch], fontsize=9)
    for bt, s in beats:
        if lo <= bt < lo + 1280:
            ax.text(bt / fs, 2.7, s, fontsize=7, ha="center")
    ax.set(
        title=f"840 original dual-channel: {lo / fs:.3f}-{(lo + 1280) / fs:.3f} s",
        ylim=(-2.8, 3),
        ylabel="mV + display offset",
    )
    ax.grid(alpha=0.2)
fig.savefig(dest / "context-70s.png", dpi=150)
plt.close(fig)
fig, axes = plt.subplots(2, 1, figsize=(18, 7), layout="constrained")
for ch, ax in enumerate(axes):
    lo, hi = 83598, 84878
    ax.plot(
        (np.arange(lo, hi) - lo) / fs,
        r.p_signal[lo - start : hi - start, ch],
        color="black",
        lw=0.9,
    )
    for n, (bt, _s) in enumerate([(bt, s) for bt, s in beats if lo <= bt < hi], 1):
        ax.text((bt - lo) / fs, 1.4, str(n), fontsize=9, ha="center")
    ax.set(
        title=f"840 {r.sig_name[ch]} original samples; numbers identify beats, NOT P waves",
        ylim=(-1.2, 1.6),
        xlabel="Seconds from original strip start",
        ylabel="mV",
    )
    ax.set_xticks(np.arange(0, 10, 0.2), minor=True)
    ax.grid(which="both", alpha=0.25)
fig.savefig(dest / "dual-channel-10s.png", dpi=160)
plt.close(fig)
fig, axes = plt.subplots(2, 3, figsize=(18, 7), layout="constrained")
for col, (label, lo, hi) in enumerate(
    [("Before", 82000, 82384), ("Middle", 84080, 84464), ("After", 86200, 86584)]
):
    for ch in range(2):
        ax = axes[ch, col]
        ax.plot(
            np.arange(lo, hi) / fs, r.p_signal[lo - start : hi - start, ch], color="black", lw=1
        )
        ax.set(
            title=f"{label}: {r.sig_name[ch]}",
            ylim=(-1.2, 1.6),
            xlabel="Source seconds",
            ylabel="mV",
        )
        ax.set_xticks(np.arange(lo / fs, hi / fs, 0.04), minor=True)
        ax.grid(which="both", alpha=0.2)
fig.savefig(dest / "before-middle-after.png", dpi=160)
details = {
    "source": w.provenance,
    "receipt": receipt.model_dump(mode="json"),
    "independent_decoder_comparison": "passed atol=1e-12 mV",
    "fs": fs,
    "channels": r.sig_name,
    "context_beats": beats,
    "strip_beats": [
        {
            "sample": bt,
            "symbol": s,
            "seconds": (bt - 83598) / fs,
            "previous_rr_ms": (bt - beats[i - 1][0]) * 1000 / fs if i else None,
        }
        for i, (bt, s) in enumerate(beats)
        if 83598 <= bt < 84878
    ],
    "processing": (
        "Original physical samples, no filtering/resampling; context has explicit display offsets; "
        "annotations are source beat labels, not rhythm diagnoses."
    ),
}
(dest / "evidence.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "strip_beats": details["strip_beats"],
            "context_counts": {
                s: sum(bs == s for _, bs in beats) for s in sorted({s for _, s in beats})
            },
        },
        indent=2,
    )
)
