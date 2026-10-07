#!/usr/bin/env python3
"""The rider's (and the lorry's) drag over time in the three runs, from their force
histories. Drag is -Fx (the air comes from +x). Means are over time (trapezoidal), not
over solver steps, which the adjustable time step makes unequal.

Prints the lone rider's 2.5-4 s mean, the 0.5 s trailing means every 0.25 s with their
share of it, each run's means over 0.5-1.5, 1.5-2.5 and 2.5-4 s with the share of the
time the rider is pushed forward, and the lorry's 2.5-4 s drag and drag coefficient.

    python3 scripts/forces.py runs > results/forces.txt
"""
import sys
from pathlib import Path

import numpy as np

runs_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "runs")


def history(run, body):
    # force.dat holds the t = 0 evaluation made before the solve, force_0.dat the solve.
    d_ = runs_dir / run / "postProcessing" / f"{body}Forces" / "0"
    a = np.vstack([np.atleast_2d(np.loadtxt(d_ / n, comments="#"))
                   for n in ("force.dat", "force_0.dat")])
    t, keep = np.unique(a[:, 0], return_index=True)
    return t, -a[keep, 1]


def tmean(t, d, a_, b_):
    m = (t >= a_) & (t <= b_)
    return np.trapezoid(d[m], t[m]) / (t[m][-1] - t[m][0]), m


def trailing(t, d, s, span=0.5):
    m = (t > s - span) & (t <= s)
    return np.trapezoid(d[m], t[m]) / (t[m][-1] - t[m][0]) if m.sum() > 2 else np.nan


runs = ["alone", "close", "far"]
H = {r: history(r, "rider") for r in runs}
alone_mean, _ = tmean(*H["alone"], 2.5, 4.0)
print(f"alone rider drag, 2.5-4 s mean: {alone_mean:.2f} N")
print("t    " + "  ".join(f"{r:>14}" for r in runs))
for s in np.arange(0.5, 4.001, 0.25):
    row = []
    for r in runs:
        v = trailing(*H[r], s)
        row.append(f"{v:7.1f} N {100 * v / alone_mean:4.0f}%")
    print(f"{s:4.2f} " + "  ".join(row))
for r in runs:
    t, d = H[r]
    for a_, b_ in [(0.5, 1.5), (1.5, 2.5), (2.5, 4.0)]:
        mean, m = tmean(t, d, a_, b_)
        print(f"{r:5} {a_}-{b_} s: mean {mean:7.2f} N ({100 * mean / alone_mean:5.1f}%), "
              f"min {d[m].min():7.1f}, max {d[m].max():7.1f}, "
              f"share of time pushed forward {100 * np.mean(d[m] < 0):4.1f}%")
for r in ["close", "far"]:
    mean, _ = tmean(*history(r, "lorry"), 2.5, 4.0)
    print(f"lorry {r}: 2.5-4 s mean drag {mean:.0f} N, "
          f"Cd {mean / (0.5 * 1.225 * 25**2 * 9.78):.3f}")
