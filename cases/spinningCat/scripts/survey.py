"""How the stirred air spreads over 0-10 s, read from the run's own planes and integrals.

For each plane at a sample of times: the point count, speed percentiles over the air
(points off the cat), and how far out and how high air moving faster than 0.2 and 0.5 m/s
reaches. Then the box's kinetic energy and the torque about the spin axis over time, as
the measure of when the start-up has settled.

    python survey.py <run_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

run = Path(sys.argv[1])
pp = run / "postProcessing"
times = sorted((d.name for d in (pp / "clipPlanes").iterdir()), key=float)
pick = [t for i, t in enumerate(times) if (i + 1) % 24 == 0 or i < 3]
print("t [s]   plane  points  p50   p95   p99.5  max   r(>0.2) r(>0.5) z(>0.2) z(>0.5)")
pooled = {"side": [], "top": []}
for t in pick:
    for name in ("side", "top"):
        m = pv.read(pp / "clipPlanes" / t / f"{name}.vtp")
        P, U = m.points, np.asarray(m["U"])
        sp = np.linalg.norm(U, axis=1)
        air = sp > 1e-9   # wall points carry exactly zero on the floor; cat points move
        r = np.hypot(P[:, 0], P[:, 1])
        z = P[:, 2]
        a = sp[air]
        pooled[name].append(np.percentile(a, 99.5))

        def reach(v, th):
            s = v[sp > th]
            return s.max() if len(s) else 0.0
        print(f"{float(t):6.3f}  {name:5s} {len(P):7d} {np.percentile(a, 50):5.2f} "
              f"{np.percentile(a, 95):5.2f} {np.percentile(a, 99.5):6.2f} {a.max():5.2f} "
              f"{reach(r, 0.2):7.2f} {reach(r, 0.5):7.2f} "
              f"{reach(z, 0.2) if name == 'side' else float('nan'):7.2f} "
              f"{reach(z, 0.5) if name == 'side' else float('nan'):7.2f}")

ke = np.loadtxt(pp / "kineticEnergy/0/volFieldValue.dat", comments="#")
print("\nkinetic energy in the box [J] (the monitor integrates 0.5 rho |U|^2, rho 1.204), every 1 s:")
for T in range(1, 11):
    i = np.argmin(abs(ke[:, 0] - T))
    print(f"  t = {ke[i, 0]:5.2f} s  {ke[i, 1]:.4f}")

mo = pp / "catForces/0/moment.dat"
rows = [l.replace("(", " ").replace(")", " ").split() for l in mo.read_text().splitlines()
        if not l.startswith("#")]
M = np.array([[float(x) for x in r[:4]] for r in rows])
print("\nmoment about z on the cat, mean over each second (first three columns: total):")
for T in range(10):
    s = (M[:, 0] > T) & (M[:, 0] <= T + 1)
    print(f"  {T}-{T + 1} s  Mz = {M[s, 3].mean():8.4f} N m")
