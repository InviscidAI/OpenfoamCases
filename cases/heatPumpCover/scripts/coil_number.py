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

The three covers' runs are read the same way, with the same F, and written to another file:

    python3 scripts/coil_number.py results -o coil_number_covers.csv slatsDown slatsUp movedOut

Their runs end at different times (movedOut at 60 s), so a run's columns are empty after its last
write. Beside each it prints the means over 50-60 s and, where the run has them, 80-90 s, and the
upstream plane's reading over the same writes (summary.csv, upstream_K_below_outside_air), the
check that F holds for each cover.
"""
import argparse
import csv
from pathlib import Path

import numpy as np

F, TS, OUT_C = 0.0302, -6.0, 2.0
WINDOW = 8                      # writes, 0.25 s apart: 2 s

ap = argparse.ArgumentParser()
ap.add_argument("results", nargs="?", default=Path(__file__).resolve().parent.parent / "results", type=Path)
ap.add_argument("runs", nargs="*", default=["open", "covered"])
ap.add_argument("-o", dest="csv", default="coil_number.csv")
args = ap.parse_args()
res, default = args.results, args.runs == ["open", "covered"]
cols, times = {}, None
for run in args.runs:
    rows = [l.split() for l in (res / run / "monitors/coilInT.dat").read_text().splitlines()
            if l and l[0] != "#"]
    t = np.array([float(r[0]) for r in rows])
    tf = np.array([float(r[1]) for r in rows]) - 273.15
    tin = (tf - F * TS) / (1 - F)
    below = OUT_C - tin
    shown = np.array([below[max(0, i - WINDOW + 1):i + 1].mean() for i in range(len(below))])
    shown = np.array([max(round(float(v), 1), 0.0) + 0.0 for v in shown])
    if default:
        if times is None:
            times = t
        elif not np.array_equal(times, t):
            raise SystemExit("the two runs' monitors were written at different times")
        cols[run] = (OUT_C - tf, below, shown)
        sel = (t >= 50) & (t <= 60)
        print(f"{run}: {len(t)} writes; 50-60 s mean {below[sel].mean():.3f} K below outside "
              f"(monitor {(OUT_C - tf[sel]).mean():.3f} K); shown at 5/10/30/60 s: "
              f"{[float(shown[np.argmin(abs(t - s))]) for s in (5, 10, 30, 60)]}")
        continue
    with open(res / run / "summary.csv") as fh:
        ups = {round(float(r["time_s"]), 6): float(r["upstream_K_below_outside_air"]) for r in csv.DictReader(fh)}
    upl = np.array([ups.get(round(float(x), 6), np.nan) for x in t])
    cols[run] = dict(zip(np.round(t, 6), zip(OUT_C - tf, below, shown)))
    print(f"{run}: {len(t)} writes, {t[0]:g}-{t[-1]:g} s; shown at 5/8/30/60/90 s: "
          f"{[float(shown[np.argmin(abs(t - s))]) if s <= t[-1] + 1e-9 else None for s in (5, 8, 30, 60, 90)]}")
    for a, b in ((50, 60), (80, 90)):
        sel = (t >= a - 1e-9) & (t <= b + 1e-9)
        if t[-1] < b - 1e-9:
            continue
        print(f"  {a}-{b} s ({sel.sum()} writes): {below[sel].mean():.3f} K below outside "
              f"(monitor {(OUT_C - tf[sel]).mean():.3f} K); upstream plane {np.nanmean(upl[sel]):.3f} K, "
              f"corrected minus upstream {np.nanmean(below[sel] - upl[sel]):+.3f} K")

if default:
    rows = [[f"{t:g}"] + [f"{v:.4f}" if j < 2 else f"{v:.1f}"
                          for run in cols for j, v in enumerate(a[i] for a in cols[run])]
            for i, t in enumerate(times)]
else:
    alltimes = sorted(set().union(*cols.values()))
    rows = [[f"{t:g}"] + [(f"{v:.4f}" if j < 2 else f"{v:.1f}") if t in cols[run] else ""
                          for run in cols for j, v in enumerate(cols[run].get(t, (0, 0, 0)))]
            for t in alltimes]
with open(res / args.csv, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["time_s"] + [f"{run}_{c}" for run in cols
                             for c in ("monitor_K_below", "corrected_K_below", "shown_C_below")])
    w.writerows(rows)
