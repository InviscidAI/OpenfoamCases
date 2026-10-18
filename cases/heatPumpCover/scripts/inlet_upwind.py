#!/usr/bin/env python3
"""The air entering the coil, from the cells just upstream of its inlet face, against coilInT.

coilInT weights T on the coil's inflow faces by phi; T on those faces is interpolated between
the outside cell and the first coil cell, which the coil has already cooled. Here the cell
values one and three cells upstream (x = 0.2445 and 0.22 m, system/inletUpwindDict, a
cuttingPlane with interpolate false), weighted by the positive Ux times the face area, give
the temperature of the air before the coil touches it. The last column is the fraction F of
the upstream air's distance from the coil's surface (-6 C) by which coilInT reads colder,
which coil_number.py takes out.

    python3 scripts/inlet_upwind.py runs > results/inlet_upwind.txt

after, in each run, postProcess -dict system/inletUpwindDict -fields '(T U)' -time 50,55,60
(Allrun does this after the solve).
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

OUT_K, TS_K = 275.15, 267.15
runs = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs")
for run in ("open", "covered"):
    pp = runs / run / "postProcessing"
    dat = max((pp / "coilInT").glob("*/*.dat"), key=lambda q: q.stat().st_size)
    tin = {round(float(l.split()[0]), 2): float(l.split()[1]) for l in open(dat) if l[0] != "#"}
    for t in ("50", "55", "60"):
        row = [f"{run:8s} t={t}  coilInT: {OUT_K - tin[float(t)]:.3f} K below 2 C"]
        up1 = None
        for s in ("up1", "up3"):
            m = pv.read(pp / "inletUpwind" / t / f"{s}.vtp").compute_cell_sizes()
            ux = m.cell_data["U"][:, 0]; A = m.cell_data["Area"]; T = m.cell_data["T"]
            w = np.clip(ux, 0, None) * A
            Tw = (w * T).sum() / w.sum()
            up1 = Tw if up1 is None else up1
            row.append(f"{s}: {OUT_K - Tw:.3f} K (flow {w.sum():.4f} m3/s, area {A.sum():.4f})")
        row.append(f"F: {(up1 - tin[float(t)]) / (up1 - TS_K):.4f}")
        print("  ".join(row))
