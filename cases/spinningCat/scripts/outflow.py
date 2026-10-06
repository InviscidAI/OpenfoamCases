"""Gross one-way radial outflow through the cylinder r = 0.5 m round the spin axis, from the
side plane (x = 0), as Q_out = integral of max(u_r, 0) 2 pi r dz, and the net flow through
the same cylinder for comparison. The plane gives u_r on two lines, y = +0.5 and y = -0.5,
and the two are averaged, so this treats the flow as axisymmetric. U is interpolated
linearly in (y, z) from the plane's points onto z = 0 to 1.6 m every 2 mm.

    python outflow.py <run_dir> [r]
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.interpolate import LinearNDInterpolator

run = Path(sys.argv[1])
r0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
pp = run / "postProcessing/clipPlanes"
writes = {float(d.name): d for d in pp.iterdir()}
times = sorted(writes)
z = np.arange(0.0, 1.6 + 1e-9, 0.002)


def profile(t):
    m = pv.read(writes[t] / "side.vtp")
    P, U = m.points, np.asarray(m["U"])
    near = np.abs(np.abs(P[:, 1]) - r0) < 0.15
    f = LinearNDInterpolator(P[near][:, 1:], U[near][:, 1])
    ur = 0.5 * (f(np.c_[np.full_like(z, r0), z]) - f(np.c_[np.full_like(z, -r0), z]))
    return np.nan_to_num(ur)


print(f"cylinder r = {r0} m, z 0-1.6 m; Q in L/s")
print(" t [s]   Q_out   Q_net   outflow layer (u_r > 0) top [cm]   peak u_r [m/s] at z [cm]")
picks = [t for t in times if abs(t * 2 - round(t * 2)) < 1e-6]
last = [t for t in times if t > times[-1] - 1 + 1e-6]
for t in picks:
    ur = profile(t)
    out = np.trapezoid(np.maximum(ur, 0), z) * 2 * np.pi * r0
    net = np.trapezoid(ur, z) * 2 * np.pi * r0
    pos = np.nonzero(ur > 0)[0]
    top = z[pos[pos < 250].max()] if (pos < 250).any() else np.nan
    k = np.argmax(ur)
    print(f"{t:6.3f} {out * 1e3:7.1f} {net * 1e3:7.1f}   {top * 100:6.1f}"
          f"                             {ur[k]:5.2f} at {z[k] * 100:4.1f}")
mean = np.mean([profile(t) for t in last], axis=0)
out = np.trapezoid(np.maximum(mean, 0), z) * 2 * np.pi * r0
net = np.trapezoid(mean, z) * 2 * np.pi * r0
inst = np.mean([np.trapezoid(np.maximum(profile(t), 0), z) * 2 * np.pi * r0 for t in last])
print(f"\nmean over the last second ({len(last)} writes): Q_out of the mean profile "
      f"{out * 1e3:.1f} L/s, mean of each write's Q_out {inst * 1e3:.1f} L/s, "
      f"net {net * 1e3:.1f} L/s")
