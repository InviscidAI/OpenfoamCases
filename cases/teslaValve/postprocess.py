"""Print the pressure drop of each direction solved in runs/, and the diodicity.

    python3 postprocess.py [t0]

The pressure drop is rho times the difference of the two ends' area-averaged
pressures, upstream minus downstream, sampled every time step. It is averaged over
time from t0 (default 0.3 s) to the end of the run, weighting each sample by its time
step. The spread is the standard deviation over the same window; the two halves of
the window are printed so a drift shows. Diodicity is the blocking (reverse) drop
over the easy (forward) one, at the same flow rate.
"""
import glob
import os
import sys

import numpy as np

RHO = 1000.0        # kg/m3
AREA = 5e-3 * 1e-3  # m2, the 5 mm channel times the 1 mm span
HERE = os.path.dirname(os.path.abspath(__file__))
ENDS = {"forward": ("right", "left"), "reverse": ("left", "right")}


def series(run, name):
    """Time and value from every postProcessing/<name>/<start>/*.dat, in time order."""
    rows = []
    for f in sorted(glob.glob(os.path.join(run, "postProcessing", name, "*", "*.dat"))):
        rows.append(np.loadtxt(f, comments="#", usecols=(0, 1), ndmin=2))
    if not rows:
        raise FileNotFoundError(f"{run}/postProcessing/{name}")
    d = np.vstack(rows)
    d = d[np.argsort(d[:, 0], kind="stable")]
    _, keep = np.unique(d[:, 0][::-1], return_index=True)   # last value wins on a restart
    d = d[::-1][keep]
    return d[:, 0], d[:, 1]


def window_mean(t, y, a, b):
    m = (t >= a) & (t <= b)
    t, y = t[m], y[m]
    w = np.gradient(t)
    mean = np.sum(w * y) / np.sum(w)
    sd = np.sqrt(np.sum(w * (y - mean) ** 2) / np.sum(w))
    return mean, sd


def yplus(run):
    files = sorted(glob.glob(os.path.join(run, "postProcessing", "yPlus", "*", "yPlus.dat")))
    last = None
    for f in files:
        for line in open(f):
            parts = line.split()
            if line.startswith("#") or len(parts) < 5 or parts[1] != "walls":
                continue
            last = parts
    return None if last is None else (float(last[0]), *map(float, last[2:5]))


def main():
    t0 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
    drops, found = {}, False
    for direction, (up, down) in ENDS.items():
        run = os.path.join(HERE, "runs", direction)
        try:
            t, p_up = series(run, "p" + up.capitalize())
            _, p_down = series(run, "p" + down.capitalize())
            _, q_out = series(run, "flux" + down.capitalize())
        except FileNotFoundError:
            continue
        found = True
        n = min(len(t), len(p_up), len(p_down), len(q_out))
        t, dp, ub = t[:n], RHO * (p_up[:n] - p_down[:n]), q_out[:n] / AREA
        t1 = t[-1]
        if t1 <= t0:
            print(f"{direction}: only reached {t1:.3f} s, before the {t0} s averaging start")
            continue
        mean, sd = window_mean(t, dp, t0, t1)
        tm = 0.5 * (t0 + t1)
        h1, _ = window_mean(t, dp, t0, tm)
        h2, _ = window_mean(t, dp, tm, t1)
        u, _ = window_mean(t, ub, t0, t1)
        drops[direction] = mean
        print(f"{direction:8s} ({up} to {down}): dp = {mean:6.1f} Pa, sd {sd:5.1f} Pa over "
              f"{t0:g}-{t1:g} s; halves {h1:.1f} and {h2:.1f} Pa; "
              f"bulk velocity out {u:.4f} m/s")
        yp = yplus(run)
        if yp:
            print(f"{'':8s} y+ on the walls at {yp[0]:g} s: min {yp[1]:.2f}, max {yp[2]:.2f}, "
                  f"mean {yp[3]:.2f}")
    if "forward" in drops and "reverse" in drops:
        print(f"diodicity Di = dp reverse / dp forward = {drops['reverse'] / drops['forward']:.2f}")
    elif not found:
        print("no runs found under runs/")


if __name__ == "__main__":
    main()
