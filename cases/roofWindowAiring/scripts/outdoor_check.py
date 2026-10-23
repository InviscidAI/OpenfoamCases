#!/usr/bin/env python3
"""Is the roof run's outdoor air still 0 C where the window draws it in? From the mid-plane.

    python3 outdoor_check.py runs/roof > results/roof/outdoor_check.txt

In build_roof.py's slope coordinates (u along the roof from the knee wall's top, v off its inner
face; the outdoor box is u -0.7 to 3.139 and v 0.24 to 1.74, the opening u 0.30 to 1.639), at
each time it prints the mean and largest temperature of the outdoor cells on the mid-plane
- in front of the eaves side, where the window draws its air in: within 0.3 m of the roof's
  outer face (v 0.24 to 0.54), below the sash (y < 1.787 m) and u 0.0 to 0.44 m, clear of the
  pocket of room air under the sash's outer half (u 0.44 to 0.86 m), which is the eaves
  side's own small outflow;
- in that pocket;
and the largest temperature and speed within 0.1 m of each of the box's three open faces (the
lower one below the eaves, u < -0.6; the outer one, v > 1.64; the upper one above the ridge,
u > 3.039). If the boundary fed the plume back, the air drawn in would warm above 0 C. Needs
PyVista; reads the gzipped or plain planes.
"""
import gzip
import os
import sys
import tempfile

import numpy as np
import pyvista as pv

run = sys.argv[1]
sq = np.sqrt(0.5)
print("t s: drawn-in air T mean / max (cells) | pocket T mean / max (cells) | open faces: T max, |U| max")
for t in ("1.25", "30", "60", "120", "180", "240", "300"):
    path = f"{run}/postProcessing/planes/{t}/mid.vtp"
    with tempfile.NamedTemporaryFile(suffix=".vtp") as f:
        f.write(gzip.open(path + ".gz").read() if os.path.exists(path + ".gz") else open(path, "rb").read())
        f.flush()
        m = pv.read(f.name)
    c = m.cell_centers().points
    x, y = c[:, 0], c[:, 1]
    u, v = (x + y - 1) * sq, (y - x - 1) * sq
    T = np.asarray(m.cell_data["T"]) - 273.15
    U = np.linalg.norm(np.asarray(m.cell_data["U"]), axis=1)
    out = v > 0.24
    front = out & (v < 0.54) & (y < 1.787)
    drawn, pocket = front & (u > 0.0) & (u < 0.44), front & (u >= 0.44) & (u < 0.86)
    faces = "; ".join(f"{name} {T[sel].max():5.2f} C, {U[sel].max():.3f} m/s" for name, sel in (
        ("lower", out & (u < -0.6)), ("outer", out & (v > 1.64)), ("upper", out & (u > 3.039))))
    print(f"{t:>5}: {T[drawn].mean():6.3f} / {T[drawn].max():6.3f} C ({drawn.sum()}) | "
          f"{T[pocket].mean():5.2f} / {T[pocket].max():5.2f} C ({pocket.sum()}) | {faces}")
