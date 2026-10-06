"""Swirl (out of the side plane) against radius and height, averaged over the last second,
to see whether the swirl stops at the rotor zone's edge (r = 0.38 m, z up to 0.45 m) at
every height, or only where air is drawn in.

    python swirl_side.py <run_dir> [t_end]
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

run = Path(sys.argv[1])
t_end = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
pp = run / "postProcessing/clipPlanes"
names = {float(d.name): d for d in pp.iterdir()}
ws = [names[k] for k in sorted(names) if t_end - 1 < k <= t_end + 1e-6]
re = np.array([0, .1, .2, .3, .34, .37, .40, .43, .5, .6, .8, 1.0, 1.3, 1.6, 2.0])
ze = np.array([0, .05, .1, .2, .3, .4, .45, .5, .6, .8, 1.0, 1.6])
S = {k: np.zeros((len(ze) - 1, len(re) - 1)) for k in ("t", "r", "z", "n")}
for d in ws:
    m = pv.read(d / "side.vtp")
    P, U = m.points, np.asarray(m["U"])
    air = np.linalg.norm(U, axis=1) > 1e-9
    y, z = P[:, 1], P[:, 2]
    ut = -U[:, 0] * np.sign(y)          # at x = 0, theta = +-90 deg
    ur = U[:, 1] * np.sign(y)
    i = np.digitize(z, ze) - 1
    j = np.digitize(abs(y), re) - 1
    ok = air & (i >= 0) & (i < len(ze) - 1) & (j >= 0) & (j < len(re) - 1)
    for a, v in (("t", ut), ("r", ur), ("z", U[:, 2])):
        np.add.at(S[a], (i[ok], j[ok]), v[ok])
    np.add.at(S["n"], (i[ok], j[ok]), 1)
n = np.where(S["n"] > 0, S["n"], np.nan)
print(f"side plane, mean over {ws[0].name}-{ws[-1].name} s; rotor zone r < 0.38, z < 0.45")
for key, title in (("t", "swirl u_theta"), ("r", "radial u_r"), ("z", "vertical u_z")):
    print(f"\n{title} [m/s]; rows z bins, columns r bins")
    print("z\\r      " + " ".join(f"{(a + b) / 2:5.2f}" for a, b in zip(re, re[1:])))
    for r_ in range(len(ze) - 1)[::-1]:
        print(f"{ze[r_]:.2f}-{ze[r_ + 1]:.2f} " +
              " ".join(f"{v:5.2f}" for v in S[key][r_] / n[r_]))
