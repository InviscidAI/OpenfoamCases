"""Write one run of the sofa case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py legs|flat|bare <runDir> [--nprocs N]

The mesh is written directly as a polyMesh, one cell thick (z = 0 to 1 m), from a graded
Cartesian grid of 288 x 241 cells over the room's 5.5 x 2.4 m section, with lines on every edge
of the radiator and the sofa and on both flow cuts (x = 0.70 m under the sofa, y = 0.70 m across
the slot behind it). The writer is radiatorCover's (../radiatorCover/scripts/make_case.py) with
this room's grid, its patches and the sofa:

- the radiator's steel front panel (x = 0.103-0.123, y = 0.15-0.75) is left out of the mesh, its
  faces the patch radiatorPanel; the convector behind it (x = 0.040-0.103, same y) is the
  cellZone convector;
- the radiator's wall at x = 0 is innerWall; the far end at x = 5.5 m is the patio doors, glass
  up to y = 2.10 m and outerWall above;
- in legs and flat the sofa's side profile is left out of the mesh, its faces the patch sofa:
  the seat and base x = 0.273-1.123 m from y = 0.15 m (legs) or the floor (flat) to 0.49 m, the
  backrest frame x = 0.273-0.393 m to 0.70 m and the back cushion x = 0.393-0.573 m to 0.94 m.
  flat is legs less the air under the sofa, on the same grid; bare has no sofa.

The files under template/common/ and template/<sofa|bare>/ are copied in unchanged. This
script writes 0/T (every wall but the panel a radLayerWall), 0/IDefault, the hydrostatic 0/p
and 0/p_rgh at rest and system/decomposeParDict.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"

TAMB = 289.15  # 16 C, the air and every wall layer at t = 0
R = 8314.46261815324 / 28.96


def H(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def graded(keys, size):
    """Lines through every key with cells close to size(t) long between them."""
    out = []
    for a, b in zip(keys[:-1], keys[1:]):
        t = np.linspace(a, b, 2001)
        w = 1 / size(t)
        s = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]
        n = round(s[-1])
        out.extend(np.interp(np.linspace(0, s[-1], n + 1), s, t)[:-1])
    return np.r_[out, keys[-1]]


# ---- the grid ----------------------------------------------------------------------------
# x, from the radiator's wall to the patio doors: 7 mm to 0.3 m, through the convector (0.040),
# the panel (0.103, 0.123), the sofa's back (0.273), the flow cut under it (0.70) and its
# frame, cushion and front (0.393, 0.573, 1.123); widening to 25 mm at 1.3 m, 25 mm to 5.2 m,
# 12 mm at the doors.
x = graded([0, .04, .103, .123, .273, .3, .393, .573, .7, 1.123, 1.3, 5.2, 5.5],
           lambda t: np.interp(t, [0, .3, 1.3, 5.2, 5.5], [.007, .007, .025, .025, .012]))
# y, up from the floor: 8 mm to 1.1 m, through the sofa's underside (0.15), seat (0.49),
# frame (0.70, the flow cut across the slot) and cushion (0.94) and the radiator's top (0.75);
# 15 mm from 1.4 m to the glass's top (2.10) and 2.25 m; 6 mm under the ceiling.
y = graded([0, .15, .49, .70, .75, .94, 1.1, 1.4, 2.1, 2.25, 2.34, 2.4],
           lambda t: np.interp(t, [0, 1.1, 1.4, 2.25, 2.34, 2.4], [.008, .008, .015, .015, .006, .006]))


def solid(run, xc, yc):
    """The radiator's panel, and the sofa in legs and flat: no air in these cells."""
    if .103 < xc < .123 and .15 < yc < .75:
        return True
    return run != "bare" and .273 < xc < 1.123 and (
        (0 if run == "flat" else .15) < yc < .49
        or (xc < .393 and .49 < yc < .70)
        or (.393 < xc < .573 and .49 < yc < .94))


def mesh(run, case):
    nx, ny = len(x) - 1, len(y) - 1
    cc, ids = [], {}
    for j in range(ny):
        for i in range(nx):
            xc, yc = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
            if solid(run, xc, yc):
                continue
            ids[i, j] = len(cc)
            cc.append((xc, yc, .5))
    cc = np.array(cc)

    def p(i, j, k):
        return (k * len(y) + j) * len(x) + i

    pts = np.array([(a, b, k) for k in (0, 1) for b in y for a in x])
    pm = case / "constant/polyMesh"
    pm.mkdir(parents=True)
    internal = []
    bd = {k: [] for k in ["floor", "ceiling", "innerWall", "outerWall", "glass", "radiatorPanel", "frontAndBack"]}
    if run != "bare":
        bd["sofa"] = []
    for (i, j), c in ids.items():
        # left, right, bottom, top, back (z = 0), front (z = 1), each oriented outward
        fs = [([p(i, j, 0), p(i, j, 1), p(i, j + 1, 1), p(i, j + 1, 0)], (i - 1, j)),
              ([p(i + 1, j, 0), p(i + 1, j + 1, 0), p(i + 1, j + 1, 1), p(i + 1, j, 1)], (i + 1, j)),
              ([p(i, j, 0), p(i + 1, j, 0), p(i + 1, j, 1), p(i, j, 1)], (i, j - 1)),
              ([p(i, j + 1, 0), p(i, j + 1, 1), p(i + 1, j + 1, 1), p(i + 1, j + 1, 0)], (i, j + 1)),
              ([p(i, j, 0), p(i, j + 1, 0), p(i + 1, j + 1, 0), p(i + 1, j, 0)], None),
              ([p(i, j, 1), p(i + 1, j, 1), p(i + 1, j + 1, 1), p(i, j + 1, 1)], None)]
        for d, (v, n) in enumerate(fs):
            if d >= 4:
                bd["frontAndBack"].append((v, c))
                continue
            if n in ids:
                if d not in (1, 3):  # each internal face once, from the cell below or left of it
                    continue
                internal.append((v, c, ids[n]))
            else:
                if n[0] < 0:
                    name = "innerWall"
                elif n[0] >= nx:
                    name = "glass" if (y[j] + y[j + 1]) / 2 < 2.1 else "outerWall"
                elif n[1] < 0:
                    name = "floor"
                elif n[1] >= ny:
                    name = "ceiling"
                else:  # a solid cell next door: the panel's or the sofa's
                    name = ("radiatorPanel" if .103 < (x[n[0]] + x[n[0] + 1]) / 2 < .123
                            and .15 < (y[n[1]] + y[n[1] + 1]) / 2 < .75 else "sofa")
                bd[name].append((v, c))
    internal.sort(key=lambda a: (a[1], a[2]))
    faces = [a[0] for a in internal]
    own = [a[1] for a in internal]
    nbr = [a[2] for a in internal]
    bounds = []
    for name, ff in bd.items():
        bounds.append((name, len(ff), len(faces)))
        faces.extend(a[0] for a in ff)
        own.extend(a[1] for a in ff)
    used = sorted(set(v for f in faces for v in f))
    remap = {v: i for i, v in enumerate(used)}

    def lst(name, cls, items):
        with (pm / name).open("w") as f:
            f.write(H(name, cls) + f"{len(items)}\n(\n")
            f.write("\n".join(items))
            f.write("\n)\n")

    lst("points", "vectorField", [f"({a:.10g} {b:.10g} {c:.10g})" for a, b, c in pts[used]])
    lst("faces", "faceList", ["4(" + " ".join(str(remap[v]) for v in f) + ")" for f in faces])
    lst("owner", "labelList", list(map(str, own)))
    lst("neighbour", "labelList", list(map(str, nbr)))
    txt = H("boundary", "polyBoundaryMesh") + f"{len(bounds)}\n(\n"
    for name, n, start in bounds:
        txt += f'{name}\n{{\n type {"empty" if name == "frontAndBack" else "wall"};\n nFaces {n};\n startFace {start};\n}}\n'
    (pm / "boundary").write_text(txt + ")\n")
    conv = np.where((cc[:, 0] > .04) & (cc[:, 0] < .103) & (cc[:, 1] > .15) & (cc[:, 1] < .75))[0]
    (pm / "cellZones").write_text(H("cellZones", "regIOobject") + "1\n(\nconvector\n{\n type cellZone;\n cellLabels List<label>\n"
                                  + str(len(conv)) + "\n(\n" + "\n".join(map(str, conv)) + "\n);\n}\n)\n")
    for name, cls in [("faceZones", "regIOobject"), ("pointZones", "regIOobject")]:
        (pm / name).write_text(H(name, cls) + "0\n(\n)\n")
    return cc, nx, ny, conv, bounds


# Every wall but the panel is a radLayerWall (src/radLayerWall): convection and the radiation
# it absorbs on the room side, and behind it a 1-D layer of 24 slices with its heat capacity
# and an adiabatic back, all starting at 16 C. The glass has no layer: a film of 4.403 W/m2K
# to 0 C outside. Thickness m, conductivity W/m K, rho*cp J/m3 K.
LAYERS = {"floor": (.019, .106, 1237411.2),       # 19 mm wood
          "sofa": (.05, .04, 49000)}              # 50 mm of upholstery foam under fabric
GYPSUM = (.0127, .1587, 723991.)                  # 12.7 mm gypsum board: ceiling, end walls


def fields(case, bounds, cc):
    txt = H("T", "volScalarField") + "dimensions [0 0 0 1 0 0 0];\ninternalField uniform 289.15;\nboundaryField\n{\n"
    for patch, n, start in bounds:
        if patch == "frontAndBack":
            txt += "frontAndBack {type empty;}\n"
            continue
        if patch == "radiatorPanel":
            txt += "radiatorPanel {type fixedValue; value uniform 328.15;}\n"
            continue
        h, ta, eps, nl = 0, 0, .9, 24
        th, k, rc = LAYERS.get(patch, GYPSUM)
        if patch == "glass":
            h, ta, eps, nl = 4.403, 273.15, .84, 0
        txt += (f"{patch}\n{{type radLayerWall; kappaMethod fluidThermo; Q 0; h {h}; Ta {ta}; emissivity {eps}; "
                f"Tinit 289.15; nLayers {nl}; thickness {th}; conductivity {k}; rhoCp {rc}; value uniform 289.15;}}\n")
    (case / "0/T").write_text(txt + "}\n")
    # the radiation at t = 0: black-body intensity at 16 C
    (case / "0/IDefault").write_text(H("IDefault", "volScalarField") + 'dimensions [1 0 -3 0 0 0 0]; internalField uniform 126.15; boundaryField { frontAndBack {type empty;} ".*" {type greyDiffusiveRadiation; value uniform 126.15;} }\n')
    # the air at rest in hydrostatic balance at 16 C, 1e5 Pa at the pressure reference's height
    p = 1e5 * np.exp(-9.81 * (cc[:, 1] - 1.174) / (R * TAMB))
    gh = -9.81 * cc[:, 1]
    rho = p / (R * TAMB)
    for name, vals in [("p", p), ("p_rgh", p - rho * gh)]:
        f = case / "0" / name
        body = f.read_text()
        assert "internalField   uniform 1e5;" in body, name
        f.write_text(body.replace("internalField   uniform 1e5;", "internalField nonuniform List<scalar>\n"
                                  + str(len(vals)) + "\n(\n" + "\n".join(map(str, vals)) + "\n);"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=["legs", "flat", "bare"])
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    kind = "bare" if a.run == "bare" else "sofa"
    shutil.copytree(TEMPLATE / "common/constant", case / "constant")
    shutil.copytree(TEMPLATE / "common/system", case / "system")
    shutil.copytree(TEMPLATE / "common/0.orig", case / "0")
    for d in ("constant", "system", "0.orig"):
        if (TEMPLATE / kind / d).is_dir():
            shutil.copytree(TEMPLATE / kind / d, case / ("0" if d == "0.orig" else d), dirs_exist_ok=True)
    cc, nx, ny, conv, bounds = mesh(a.run, case)
    fields(case, bounds, cc)
    (case / "system/decomposeParDict").write_text(
        "FoamFile {version 2.0; format ascii; class dictionary; object decomposeParDict;}\n"
        f"numberOfSubdomains {a.nprocs};\nmethod scotch;\n")
    dx, dy = np.diff(x), np.diff(y)
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny, "convectorCells": len(conv),
              "min_dx": float(dx.min()), "min_dy": float(dy.min()),
              "max_dx": float(dx.max()), "max_dy": float(dy.max()),
              "cells_under_sofa": int(np.sum(y < .15)), "cells_across_slot": int(np.sum((x >= .123) & (x < .273))),
              "patches": {n: count for n, count, st in bounds}}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    (case / f"{a.run}.foam").touch()
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(conv), "cells, smallest",
          f'{report["min_dx"] * 1e3:.3f} x {report["min_dy"] * 1e3:.3f} mm')


if __name__ == "__main__":
    main()
