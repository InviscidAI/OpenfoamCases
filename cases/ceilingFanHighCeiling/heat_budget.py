#!/usr/bin/env python3
"""Heat budget of a 10 run from its solver log's `heatBudget` lines.

Each line is: time, step, wedge integral of T (K m3), and the conductive loss through
floor, ceiling and outer wall (K m3/s). Over 7.5 s intervals, the change in the integral
is set against the heater's source minus the wall loss, each step weighted by its length
(the loss is evaluated at the end of the step, as the implicit solve applies it). Watts
are for the whole room: x rho cp x 360/wedge.

usage: heat_budget.py LOG [--heater-w 2600] [--interval 7.5]
"""
import argparse
import numpy as np

RHO, CP, WEDGE = 1.20, 1005.0, 5.0

ap = argparse.ArgumentParser()
ap.add_argument("log")
ap.add_argument("--heater-w", type=float, default=2600.0)
ap.add_argument("--interval", type=float, default=7.5)
a = ap.parse_args()

rows = [l.split()[1:7] for l in open(a.log) if l.startswith("heatBudget ")]
d = np.array(rows, float)
t, dt, VT, q = d[:, 0], d[:, 1], d[:, 2], d[:, 3:6]
full = RHO * CP * 360.0 / WEDGE  # K m3/s on the wedge -> W in the room
S = a.heater_w * WEDGE / 360.0 / (RHO * CP)

print(f"{len(t)} steps to t = {t[-1]:.3f} s; heater {a.heater_w:.0f} W")
print(f"{'interval s':>14} {'stored W':>9} {'heater W':>9} {'walls W':>8} "
      f"{'(floor ceil wall)':>22} {'imbalance W':>12} {'% of heater':>11}")
edges = np.arange(0.0, t[-1] + 1e-9, a.interval)
worst = 0.0
for t0, t1 in zip(edges[:-1], edges[1:]):
    # steps whose end lies in (t0, t1]; the stored change runs from the step before
    i = np.nonzero((t > t0 + 1e-12) & (t <= t1 + 1e-12))[0]
    i = i[i > 0]  # the first logged step has no stored value before it
    if len(i) == 0:
        continue
    span = dt[i].sum()
    stored = (VT[i[-1]] - VT[i[0] - 1]) / span * full
    loss = (q[i] * dt[i, None]).sum(0) / span * full
    imb = stored - (S * full - loss.sum())
    worst = max(worst, abs(imb))
    print(f"{t0:6.1f}-{t1:6.1f} {stored:9.2f} {S*full:9.1f} {loss.sum():8.2f} "
          f"({loss[0]:6.2f} {loss[1]:6.2f} {loss[2]:6.2f}) {imb:12.4f} {100*imb/(S*full):11.4f}")
print(f"largest imbalance over any interval: {worst:.4f} W ({100*worst/(S*full):.4f}% of the heater)")
