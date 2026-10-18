#!/usr/bin/env python3
"""Each run's number: how much colder than the outside air (2 C) the air entering the coil is.

The run's own monitor, coilInT (results/<run>/monitors/coilInT.dat), weights T on the coil's
inflow faces by the face flux. T on those faces is interpolated between the outside cell and
the first coil cell, which the coil has already cooled, so it reads the air as colder than it
is by a fixed fraction F of its distance from the coil's surface temperature, Ts = -6 C.
Against the cell values one cell upstream at 50, 55 and 60 s (results/inlet_upwind.txt,
written by inlet_upwind.py), F = 0.0301 in `open` and 0.0304-0.0305 in `covered`. The air
entering is taken as T_in = (T_face - F Ts) / (1 - F) with F = 0.0302 in both runs, which
puts it within 0.002 K of the upstream cells at those three times in both. That correction
is 0.24 K in `open` and 0.22 K in `covered`.

The clip shows, at each write, the mean over the last 2 s of flow (8 writes, fewer at the
start), so that the tenths do not flicker, rounded to 0.1 K and never shown below zero.

Writes results/coil_number.csv (per write: the monitor's reading, the corrected value and the
value shown) and prints the 50-60 s means.

    python3 scripts/coil_number.py [results dir]      # default: results/ beside scripts/
"""
import csv
import sys
from pathlib import Path

import numpy as np

F, TS, OUT_C = 0.0302, -6.0, 2.0
WINDOW = 8                      # writes, 0.25 s apart: 2 s

res = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "results"
cols, times = {}, None
for run in ("open", "covered"):
    rows = [l.split() for l in (res / run / "monitors/coilInT.dat").read_text().splitlines()
            if l and l[0] != "#"]
    t = np.array([float(r[0]) for r in rows])
    tf = np.array([float(r[1]) for r in rows]) - 273.15
    tin = (tf - F * TS) / (1 - F)
    below = OUT_C - tin
    shown = np.array([below[max(0, i - WINDOW + 1):i + 1].mean() for i in range(len(below))])
    shown = np.array([max(round(float(v), 1), 0.0) + 0.0 for v in shown])
    if times is None:
        times = t
    elif not np.array_equal(times, t):
        raise SystemExit("the two runs' monitors were written at different times")
    cols[run] = (OUT_C - tf, below, shown)
    sel = (t >= 50) & (t <= 60)
    print(f"{run}: {len(t)} writes; 50-60 s mean {below[sel].mean():.3f} K below outside "
          f"(monitor {(OUT_C - tf[sel]).mean():.3f} K); shown at 5/10/30/60 s: "
          f"{[float(shown[np.argmin(abs(t - s))]) for s in (5, 10, 30, 60)]}")

with open(res / "coil_number.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["time_s"] + [f"{run}_{c}" for run in cols
                             for c in ("monitor_K_below", "corrected_K_below", "shown_C_below")])
    for i, t in enumerate(times):
        w.writerow([f"{t:g}"] + [f"{v:.4f}" if j < 2 else f"{v:.1f}"
                                 for run in cols for j, v in enumerate(a[i] for a in cols[run])])
