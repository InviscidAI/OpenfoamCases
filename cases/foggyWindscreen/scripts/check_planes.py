#!/usr/bin/env python3
"""Air above saturation and where the mist is, from a run's section planes.

    $PYTHON scripts/check_planes.py runs/<run> [t ...]        (default 120 300 600)

Reads postProcessing/clip/<t>/section.vtp(.gz), cell data T (K), w and L (kg/kg). Each face of the
plane is a cell of the one-cell-deep, 1 m thick mesh, so its area in m2 is its volume per metre of
section. Saturation is the solver's (Buck 1981, at 1e5 Pa). For each time it prints the share of the
section above 100.5 % and 102 % relative humidity, the highest relative humidity, and the mist: its
mass per metre, how much of it is in cells thinner than 1 mm (area under 1 mm2, the first cells of
the wall layers on the screens and the headliner, where it is in effect water condensed on that
wall), the share of the section whose air carries more than 1 g/kg, and the mist-weighted mean
height and temperature of the rest.

Needs NumPy and VTK for Python.
"""
import gzip
import os
import sys
import tempfile

import numpy as np
from vtk import vtkXMLPolyDataReader
from vtk.util.numpy_support import vtk_to_numpy


def wsat(T):
    t = T - 273.15
    e = 611.21 * np.exp((18.678 - t / 234.5) * (t / (257.14 + t)))
    return 0.622 * e / (1e5 - 0.378 * e)


def read(path):
    tmp = None
    if path.endswith(".gz"):
        fd, tmp = tempfile.mkstemp(suffix=".vtp")
        with gzip.open(path) as f, os.fdopen(fd, "wb") as g:
            g.write(f.read())
        path = tmp
    r = vtkXMLPolyDataReader()
    r.SetFileName(path)
    r.Update()
    pd = r.GetOutput()
    if tmp:
        os.remove(tmp)
    cd = pd.GetCellData()
    pts = vtk_to_numpy(pd.GetPoints().GetData())[:, :2]
    area, cy = [], []
    for i in range(pd.GetNumberOfCells()):
        ids = pd.GetCell(i).GetPointIds()
        q = pts[[ids.GetId(k) for k in range(ids.GetNumberOfIds())]]
        x, y = q[:, 0], q[:, 1]
        area.append(0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))
        cy.append(y.mean())
    out = {k: vtk_to_numpy(cd.GetArray(k)) for k in ("T", "w", "L")}
    out["A"], out["y"] = np.array(area), np.array(cy)
    return out


def main():
    run = sys.argv[1]
    times = sys.argv[2:] or ["120", "300", "600"]
    print(f"{os.path.basename(os.path.normpath(run))}")
    print("   t s  >100.5%  >102%  RH max   mist g/m  in thin wall cells  air >1 g/kg  rest's mist y m, C")
    for t in times:
        d = os.path.join(run, "postProcessing", "clip", t)
        f = [os.path.join(d, n) for n in ("section.vtp", "section.vtp.gz") if os.path.exists(os.path.join(d, n))]
        if not f:
            print(f"{t:>6}  no plane")
            continue
        p = read(f[0])
        T, w, L, A = p["T"], p["w"], p["L"], p["A"]
        rh = w / wsat(T)
        m = 1e5 / (287.1 * T) * A * L
        thin = A < 1e-6
        air = ~thin
        tot = m.sum()
        y = (m[air] * p["y"][air]).sum() / max(m[air].sum(), 1e-30)
        tc = (m[air] * T[air]).sum() / max(m[air].sum(), 1e-30) - 273.15
        print(f"{float(t):6.1f}  {A[rh > 1.005].sum() / A.sum():6.2%}  {A[rh > 1.02].sum() / A.sum():6.2%}  "
              f"{rh.max():6.1%}   {tot * 1e3:7.3f}   {m[thin].sum() * 1e3:7.3f} ({m[thin].sum() / max(tot, 1e-30):5.1%})"
              f"     {A[air & (L > 1e-3)].sum() / A.sum():6.1%}      {y:5.2f}  {tc:6.2f}")


if __name__ == "__main__":
    main()
