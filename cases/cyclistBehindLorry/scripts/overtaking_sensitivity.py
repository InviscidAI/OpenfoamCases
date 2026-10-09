#!/usr/bin/env python3
"""How the overtaking force on the rider depends on the model's assumptions.

Runs scripts/overtaking_force.py's model once per variant, changing one assumption at a
time, and prints for each: the sideways peak away from the lorry (the cab's push) and
towards it (the pull behind the doors), with his shoulders' x in the lorry's frame (the
doors at 0, the cab's front at 16.5 m), the in-plane peak with its components, and the
vertical range, per write and as shown (the six-write mean).

    python3 scripts/overtaking_sensitivity.py runs/overtaking > results/overtaking_sensitivity.txt
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import overtaking_force as M  # noqa: E402


def smooth(F, n):
    """Running mean over the n writes up to each one (a body that takes n writes to feel
    a change)."""
    c = np.cumsum(np.vstack([np.zeros((1, 3)), F]), axis=0)
    out = np.empty_like(F)
    for k in range(len(F)):
        k0 = max(0, k - n + 1)
        out[k] = (c[k + 1] - c[k0]) / (k + 1 - k0)
    return out


def summary(F, times, xr):
    sh = M.shown(F)
    ia, it = int(np.argmin(F[:, 1])), int(np.argmax(F[:, 1]))
    hp = np.hypot(F[:, 0], F[:, 1])
    ih = int(np.argmax(hp))
    return (f"away {-F[ia, 1]:5.1f} (x {xr[ia]:6.2f}) | towards {F[it, 1]:4.1f} (x {xr[it]:6.2f}) | "
            f"in-plane {hp[ih]:5.1f} [{F[ih, 0]:+5.1f}, {F[ih, 1]:+5.1f}] | vertical "
            f"{F[:, 2].min():+4.1f}..{F[:, 2].max():+4.1f} || shown: away {-sh[:, 1].min():5.1f}, "
            f"towards {sh[:, 1].max():4.1f}, in-plane {np.hypot(sh[:, 0], sh[:, 1]).max():5.1f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run", nargs="?", default=str(M.CASE / "runs" / "overtaking"))
    p.add_argument("--cache", default=None)
    a = p.parse_args()
    r = M.RIDER
    times, x, U = M.load_lines(a.run, a.cache)
    xr = M.path_x(times)
    w, f, xs, ar = M.body_weights(M.shoulder_x_own())
    wts = (w, f, xs)
    A = dict(M.FORCE_AREAS)
    V = r["closing_speed"]
    lorry = (V * 3.6 + 20.0) / 3.6                # 80 km/h

    print("Force on the rider, N: + x forwards, + y towards the lorry, + z up.")
    print(f"The model: CA = {A} m^2, rho {M.RHO}, rider at 20 km/h (closing "
          f"{V * 3.6:.0f} km/h), body-weighted over three heights on y = -3.0 m.")
    print(f"Silhouettes of the rider and bike: side {ar['side']:.3f} m^2, front {ar['front']:.3f}, "
          f"top {ar['top']:.3f}; side share by band (knee, hip, shoulder lines) "
          f"{np.round(w.sum(1), 3).tolist()}, frontal share {np.round(f, 3).tolist()}")
    F0 = M.forces(times, x, U, weights=wts)
    print(f"Riding in still air (first write): {F0[0].round(2).tolist()} N\n")

    # A point model: all weight on the shoulder line at his shoulders.
    j0 = int(np.argmin(np.abs(xs)))
    w_pt = np.zeros_like(w)
    w_pt[2, j0] = 1.0
    w_eq = np.zeros_like(w)
    for b in range(3):
        w_eq[b] = w[b] / w[b].sum() / 3
    variants = [
        ("the model", {}),
        ("frontal CA_x 0.31 m^2 (16 deg torso)", {"areas": {**A, "x": 0.31}}),
        ("frontal CA_x 0.40 m^2 (more upright)", {"areas": {**A, "x": 0.40}}),
        ("side CA_y 0.68 m^2 (RANS 90 deg, pedals level)", {"areas": {**A, "y": 0.68}}),
        ("side CA_y 0.93 m^2 (CA_y + RANS's 18% under-prediction)", {"areas": {**A, "y": 0.93}}),
        ("both areas x 0.82 (his 0.45 m^2 frontal vs the mannequin's 0.55)",
         {"areas": {**A, "x": A["x"] * 0.815, "y": A["y"] * 0.815}}),
        ("vertical CA_z x 0.5", {"areas": {**A, "z": A["z"] * 0.5}}),
        ("vertical CA_z x 1.2", {"areas": {**A, "z": A["z"] * 1.2}}),
        ("rider at 15 km/h (closing 65 km/h)", {"closing": lorry - 15 / 3.6}),
        ("rider at 25 km/h (closing 55 km/h)", {"closing": lorry - 25 / 3.6}),
        ("one point: his shoulders on the shoulder line", {"weights": (w_pt, np.array([0, 0, 1.0]), xs)}),
        ("three heights weighted equally", {"weights": (w_eq, np.ones(3) / 3, xs)}),
        ("averaged across his width, y -3.0 +- 0.2 m (quadratic in y)", {"y_spread": (0.2, 5)}),
        ("gap 0.75 m (line y = -2.25 m)", {"iy": 0}),
        ("gap 2.5 m (line y = -4.0 m)", {"iy": 2}),
    ]
    for name, kw in variants:
        kw.setdefault("weights", wts)
        F = M.forces(times, x, U, **kw)
        print(f"{name}\n    {summary(F, times, xr)}")
    print("\nIf his body takes time to feel a change (running mean of the force):")
    for n, what in [(6, "0.05 s, the readout's own mean"), (18, "0.15 s"),
                    (36, "0.30 s, about the time the air takes to cross his 1.75 m")]:
        print(f"  {what}\n    {summary(smooth(F0, n), times, xr)}")
    # The lorry's part: the force minus his own riding drag in still air.
    d = F0 - F0[0]
    print(f"\nThe lorry's part (force minus the first write's riding drag): sideways "
          f"{d[:, 1].min():+.1f} to {d[:, 1].max():+.1f} N, fore-aft {d[:, 0].min():+.1f} to "
          f"{d[:, 0].max():+.1f} N")
    hp = np.hypot(F0[:, 0], F0[:, 1])
    ih = int(np.argmax(hp))
    print(f"In-plane peak at t = {times[ih]:.3f} s, his shoulders at x = {xr[ih]:.2f} m "
          f"(the cab's front is at 16.5 m), force {F0[ih].round(1).tolist()} N")
    sh = M.shown(F0)
    above = np.where(-sh[:, 1] >= 17.0)[0]
    print(f"Shown sideways at or above 17 N: {len(above)} of {len(sh)} writes")
    for thr in (10, 14):
        idx = np.where(-F0[:, 1] >= thr)[0]
        if len(idx):
            print(f"Sideways push above {thr} N: t {times[idx[0]]:.3f}-{times[idx[-1]]:.3f} s "
                  f"({(idx[-1] - idx[0] + 1) / 120:.3f} s of flow, his shoulders x "
                  f"{xr[idx[0]]:.2f} to {xr[idx[-1]]:.2f} m)")


if __name__ == "__main__":
    main()
