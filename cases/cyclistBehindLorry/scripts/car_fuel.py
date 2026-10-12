#!/usr/bin/env python3
"""The car's drag in the three car runs, and the fuel it saves behind the lorry.

Drag is -Fx on the car's body and wheels (postProcessing/carForces, the air coming from
+x). A mean over a window weights each solver step by its length, the step's value holding
over the step that ends at its time stamp; the adjustable time step makes the steps
unequal. The window, 4-8 s, was fixed in config_car.sh (AVG_START, AVG_END) before the
results were read.

    share      = drag behind the lorry / drag alone
    fuel saved = 0.5 x (1 - share)

The one-half is the share of a car's energy that goes to aerodynamic drag at motorway
speed: "for high-speed driving, one-half of the energy goes to overcoming drag" (National
Research Council, Cost, Effectiveness, and Deployment of Fuel Economy Technologies for
Light-Duty Vehicles, 2015, ch. 6, p. 207). It assumes the engine's efficiency does not
change at the lower load.

Prints, per run: the 4-8 s mean, its share and the fuel saved, Cd on 2.265 m2, the 1 s
means over 1-8 s, the range of the 0.5 s trailing means over 4.5-8 s as a share of the
lone car's 4-8 s mean, and, behind the lorry, the time from which the car's 0.25 s mean
drag stays 3% below the lone car's over the same seconds for at least 0.5 s, and the
lorry's own 4-8 s drag. With --readout it also writes the clip's live readout: every
1/30 s of flow, updated every sixth, the fuel saved from the mean drag over the 0.5 s
before the update in both runs (the lone car over the same seconds; every car's drag is
low just after the impulsive start), rounded to the whole percent, blank before 0.5 s.

    python3 scripts/car_fuel.py runs > results/car_fuel.txt
    python3 scripts/car_fuel.py runs --readout results/car_fuel_readout.csv
"""
import argparse
from pathlib import Path

import numpy as np

FUEL_PER_DRAG = 0.5        # NRC 2015, p. 207
SETTLED = (4.0, 8.0)
RHO, V, A_CAR, A_LORRY = 1.225, 25.0, 2.265, 9.78
FRAME_DT, UPDATE, WINDOW, START, FRAMES = 1 / 30, 6, 0.5, 0.5, 241


def history(run, name="carForces"):
    d = Path(run) / "postProcessing" / name / "0"
    a = np.vstack([np.atleast_2d(np.loadtxt(p, comments="#"))
                   for p in sorted(d.glob("force*.dat"))])
    t, keep = np.unique(a[:, 0], return_index=True)
    return t, -a[keep, 1]


def mean(t, f, t0, t1):
    dt = np.diff(np.r_[0.0, t])
    sel = (t > t0 + 1e-9) & (t <= t1 + 1e-9)
    return float((f[sel] * dt[sel]).sum() / dt[sel].sum())


def fuel(share):
    return 100 * FUEL_PER_DRAG * (1 - share)


def summary(runs):
    ta, fa = history(runs / "carAlone")
    ref = mean(ta, fa, *SETTLED)
    print("Car drag (body and wheels, drag = -Fx), N; means over time, 4-8 s")
    for run in ("carAlone", "tailgate", "safe"):
        t, f = history(runs / run)
        m = mean(t, f, *SETTLED)
        blocks = " ".join(f"{mean(t, f, a, a + 1):.0f}" for a in range(1, 8))
        rm = [mean(t, f, x - 0.5, x) / ref for x in np.arange(4.5, 8.001, 0.05)]
        print(f"  {run:9s} 4-8 s {m:6.1f}  share {m / ref:.3f}  fuel saved {fuel(m / ref):5.1f}%  "
              f"Cd {m / (0.5 * RHO * V ** 2 * A_CAR):.3f}  1 s means 1-8 s: {blocks}; "
              f"0.5 s means 4.5-8 s {min(rm):.3f}-{max(rm):.3f}")
        if run != "carAlone":
            xs = np.arange(0.3, 8.0, 0.01)
            below = np.array([mean(t, f, x - 0.25, x) < 0.97 * mean(ta, fa, x - 0.25, x)
                              for x in xs])
            held = next(xs[j] for j in range(len(xs)) if below[j:j + 50].all())
            tl, fl = history(runs / run, "lorryForces")
            ml = mean(tl, fl, *SETTLED)
            print(f"            its drag held 3% below the lone car's from {held:.2f} s; "
                  f"lorry drag 4-8 s {ml:.0f} N (Cd {ml / (0.5 * RHO * V ** 2 * A_LORRY):.3f})")


def readout(runs, out):
    ta, fa = history(runs / "carAlone")
    cols = {}
    for run in ("tailgate", "safe"):
        t, f = history(runs / run)
        vals, shown = [], None
        for k in range(FRAMES):
            tk = k * FRAME_DT
            if k % UPDATE == 0:
                if tk < START - 1e-9:
                    shown = None
                else:
                    share = mean(t, f, tk - WINDOW, tk) / mean(ta, fa, tk - WINDOW, tk)
                    shown = round(fuel(share)) + 0     # + 0 turns a rounded -0 into 0
            vals.append(shown)
        cols[run] = vals
    with open(out, "w") as fh:
        fh.write("frame,t_s,tailgate_fuel_saved_pct,safe_fuel_saved_pct\n")
        for k in range(FRAMES):
            a, b = ("" if c[k] is None else c[k] for c in (cols["tailgate"], cols["safe"]))
            fh.write(f"{k},{k * FRAME_DT:.4f},{a},{b}\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("runs", nargs="?", default="runs")
    p.add_argument("--readout", help="write the clip's live readout to this CSV")
    a = p.parse_args()
    if a.readout:
        readout(Path(a.runs), a.readout)
    else:
        summary(Path(a.runs))


if __name__ == "__main__":
    main()
