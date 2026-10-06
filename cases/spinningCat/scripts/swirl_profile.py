"""Swirl and radial velocity against radius on the top plane (z = 0.20 m), averaged around
the axis, at a few times, beside the rotor zone's radius (the AMI surface) and the cat's
own speed at that radius. A step in the swirl at the AMI radius would be the interface
holding back momentum; a smooth fall is the air the cat drags round with it.

    python swirl_profile.py <run_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

run = Path(sys.argv[1])
ami = pv.read(run / "constant/triSurface/AMI.stl")
r_ami = np.hypot(ami.points[:, 0], ami.points[:, 1])
print(f"AMI surface: r {r_ami.min():.3f}-{r_ami.max():.3f} m, "
      f"z {ami.points[:, 2].min():.3f}-{ami.points[:, 2].max():.3f} m")
pp = run / "postProcessing/clipPlanes"
names = {float(d.name): d for d in pp.iterdir()}
edges = np.r_[np.arange(0, 0.6, 0.025), np.arange(0.6, 2.01, 0.1)]
OMEGA = 24.5
for t in (1.0, 5.0, 10.0):
    # average over the 48 writes of the second ending at t, so the turning cat's own
    # passing does not dominate one radius
    ws = [names[k] for k in sorted(names) if t - 1 < k <= t + 1e-6]
    acc_t = np.zeros(len(edges) - 1)
    acc_r = np.zeros(len(edges) - 1)
    for d in ws:
        m = pv.read(d / "top.vtp")
        P, U = m.points, np.asarray(m["U"])
        r = np.hypot(P[:, 0], P[:, 1])
        th = np.arctan2(P[:, 1], P[:, 0])
        ut = -U[:, 0] * np.sin(th) + U[:, 1] * np.cos(th)
        ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)
        air = np.linalg.norm(U, axis=1) > 1e-9
        b = np.digitize(r, edges) - 1
        for i in range(len(edges) - 1):
            s = air & (b == i)
            acc_t[i] += ut[s].mean() if s.any() else np.nan
            acc_r[i] += ur[s].mean() if s.any() else np.nan
    print(f"\nmean over {ws[0].name}-{ws[-1].name} s ({len(ws)} writes)")
    print("  r [m]   u_theta  u_r    (cat's own speed omega*r)")
    for i in range(len(edges) - 1):
        rc = 0.5 * (edges[i] + edges[i + 1])
        print(f"  {rc:5.3f}  {acc_t[i] / len(ws):6.2f} {acc_r[i] / len(ws):6.2f}   "
              f"{OMEGA * rc:5.2f}")
