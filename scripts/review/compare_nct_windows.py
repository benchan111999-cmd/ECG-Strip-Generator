"""Visual screening only: original samples, no filtering or resampling."""

from pathlib import Path

import matplotlib
import numpy as np
import wfdb

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ecg_strip_generator.datasets.registry import load_registry
from ecg_strip_generator.datasets.storage import verify_bundle

p = next(Path("data/raw/mitdb").glob("*/*/files/209.dat"))
verify_bundle(p.parent.parent, load_registry()["mitdb"])
starts = [200160, 203760, 206640, 216000, 219600, 264240, 266040]
fig, axes = plt.subplots(len(starts), 1, figsize=(16, 14), layout="constrained")
for ax, start in zip(axes, starts, strict=True):
    r = wfdb.rdrecord(str(p.with_suffix("")), sampfrom=start, sampto=start + 3600)
    ax.plot(np.arange(3600) / 360, r.p_signal[:, 0], color="black", lw=0.65)
    ax.set(title=f"209 MLII original samples {start}:{start + 3600}", ylim=(-1.2, 2))
    ax.grid(alpha=0.2)
dest = Path("output/candidate-review-2026-09-11/nct-window-comparison.png")
fig.savefig(dest, dpi=130)
print(dest)
