"""Run from repository root after render_candidates.py; unfiltered QRS detail."""

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import wfdb

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path("output/candidate-review-2026-09-11")
fig, axes = plt.subplots(2, 1, figsize=(12, 7), layout="constrained")
results = []
wide_pvc = "--wide-pvc" in sys.argv
records = ["100", "119"] if wide_pvc else ["100", "209"]
targets = [546792, 42126] if wide_pvc else [546792, 203072]
for ax, rec, target in zip(axes, records, targets, strict=True):
    p = next(Path("data/raw/mitdb").glob(f"*/*/files/{rec}.dat"))
    r = wfdb.rdrecord(str(p.with_suffix("")), sampfrom=target - 90, sampto=target + 126)
    t = np.arange(-90, 126) / 360 * 1000
    ax.plot(t, r.p_signal[:, 0], color="black", lw=1)
    ax.set_xticks(np.arange(-240, 361, 20), minor=True)
    ax.set_xticks(np.arange(-200, 301, 100))
    ax.grid(which="both", alpha=0.3)
    ax.axvline(0, color="blue", lw=0.7, label="Source beat annotation (not QRS onset)")
    ax.set(
        xlabel="Milliseconds relative to source beat annotation",
        ylabel="MLII (mV)",
        title=f"MITDB {rec}; sample {target}; original 360 Hz samples",
    )
    ax.legend(loc="upper right")
    a = wfdb.rdann(str(p.with_suffix("")), "atr")
    beats = [(int(t), s) for t, s in zip(a.sample, a.symbol, strict=False) if s in {"N", "A", "V"}]
    i = [t for t, s in beats].index(target)
    results.append({"record": rec, "target": target, "neighbours": beats[i - 3 : i + 4]})
image_name = "wide-pvc-comparison.png" if wide_pvc else "qrs-review.png"
json_name = "wide-pvc-context.json" if wide_pvc else "measurement-context.json"
fig.savefig(root / image_name, dpi=180)
(root / json_name).write_text(json.dumps(results, indent=2))
print(root / image_name)
