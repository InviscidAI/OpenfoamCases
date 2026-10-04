#!/usr/bin/env python3
"""Fan reversed: the four heights' histories in both rooms, from the committed CSVs.

Reads results/vs_ceilingFanWinter/*.csv (written by compare_07.py) and writes
results/four_height_histories.png. No field data is needed.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

d = Path(__file__).resolve().parent / "results"
v = d / "vs_ceilingFanWinter"
series = [  # (csv, legend, colour, line style)
    (v / "ceilingFanWinter_up_medium.csv", "ceilingFanWinter: 3.05 m ceiling, 1300 W", "#2a78d6", "-"),
    (v / "heater2600W_up_medium_tall.csv", "this case: 6.10 m ceiling, 2600 W", "#eb6834", "--"),
    (v / "heater1300W_up_medium_tall.csv", "this case: 6.10 m ceiling, 1300 W", "#1baf7a", ":"),
]
heights = [("010", "0.10 m (4 in)"), ("109", "1.09 m (43 in)"),
           ("170", "1.70 m (67 in)"), ("275", "2.75 m (108 in)")]

fig, ax = plt.subplots(4, 1, figsize=(7, 12), sharex=True)
for (lbl, title), x in zip(heights, ax):
    for csv, name, colour, ls in series:
        h = pd.read_csv(csv)
        x.plot(h["t"], h[f"T{lbl}_C"], ls, color=colour, lw=2, label=name)
    x.set_title(f"fan reversed, z = {title}", fontsize=10)
    x.set_ylabel("T (°C)")
    x.grid(alpha=0.25)
    for s in ("top", "right"):
        x.spines[s].set_visible(False)
ax[0].legend(fontsize=8, frameon=False)
ax[-1].set_xlabel("t from switch-on (s)")
fig.suptitle("r-weighted mean temperature at four heights, 0 to 180 s", fontsize=11)
fig.tight_layout()
fig.savefig(d / "four_height_histories.png", dpi=100)
