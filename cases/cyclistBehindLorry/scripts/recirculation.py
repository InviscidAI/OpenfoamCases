#!/usr/bin/env python3
"""Length of the lorry's mean near wake in the far run: the side plane (y = 0) averaged over
2.5-4 s, its streamwise velocity read along z = 2.6 m (the box's mid-height) from the doors
(x = 10 m in the rider's coordinates) back towards the rider, and the first change from
flow towards the doors (Ux > 0) to flow away from them taken as the closure.

    python3 scripts/recirculation.py runs/far results/centreline_mean_Ux.csv
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

run, out = Path(sys.argv[1]), Path(sys.argv[2])
DOORS, BOX_H = 10.0, 2.8
files = []
for f in (run / 'postProcessing' / 'side').glob('*/*.vtp'):
    try:
        t = float(f.parent.name)
    except ValueError:
        continue
    if 2.5 - 1e-8 <= t <= 4.0 + 1e-8:
        files.append((t, f))
files.sort()
avg = base = None
for _, f in files:
    m = pv.read(f)
    u = np.asarray(m.point_data['U'])
    if avg is None:
        avg = np.zeros_like(u, dtype=float)
        base = m.copy()
    avg += u
avg /= len(files)
base.point_data['Umean'] = avg
s = pv.Line((DOORS - 0.02, 0, 2.6), (4.0, 0, 2.6), resolution=1196).sample(base)
valid = np.asarray(s['vtkValidPointMask']).astype(bool)
X = DOORS - s.points[valid, 0]
ux = s['Umean'][valid, 0]
o = np.argsort(X)
X, ux = X[o], ux[o]
i = np.where((ux[:-1] >= 0) & (ux[1:] < 0))[0][0]
L = X[i] + (0 - ux[i]) * (X[i + 1] - X[i]) / (ux[i + 1] - ux[i])
out.parent.mkdir(parents=True, exist_ok=True)
np.savetxt(out, np.c_[X, ux], delimiter=',', header='X_behind_doors_m,Ux_mean_m_per_s', comments='')
print(f"planes averaged: {len(files)} ({files[0][0]:g}-{files[-1][0]:g} s)")
print(f"mean near wake closes {L:.2f} m behind the doors at z = 2.6 m: "
      f"X/H = {L / BOX_H:.3f} on the 2.8 m box")
