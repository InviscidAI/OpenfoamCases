"""Write one run of the radiator cover case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py bare|cover <runDir> [--nprocs N]

The mesh is written directly as a polyMesh, one cell thick (z = 0 to 1 m), from a Cartesian
grid with lines on every edge of the radiator, the cover and its slots. Both runs share the
grid and the cells; the radiator's steel front panel (x = 0.103-0.123, y = 0.15-0.75) is left
out of it, its faces the patch radiatorPanel. In the cover run the internal faces along the
cover's top, rails and grille are split into pairs of coincident wall patches (<part>A, the
side the face's owner cell is on, and <part>B) that 0/T makes 1-D conducting thermal baffles.
The convector behind the panel (x = 0.040-0.103, y = 0.15-0.75) is the cellZone convector.

The files under template/ are copied in unchanged; 0/T, 0/IDefault and
system/decomposeParDict are written here.
"""
import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"


def H(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def grid(keys, step):
    """Uniform cells of at most `step` between each pair of key lines."""
    a = []
    for lo, hi in zip(keys[:-1], keys[1:]):
        a.extend(np.linspace(lo, hi, math.ceil(round((hi - lo) / step, 8)) + 1)[:-1])
    return np.array(a + [keys[-1]])


# ---- the grid ----------------------------------------------------------------------------
# x, from the window wall into the room: 3 mm or less to 0.25 m, through the radiator
# (0.040, 0.103, 0.123), the grille and frame (0.162, 0.165, 0.178) and the top's overhang
# (0.190); then widening to 22 mm, 22 mm from 1 to 3 m, narrowing to 5 mm at 3.8 m and 5 mm
# to the inner wall at 4 m.
x0 = grid([0, .04, .103, .123, .162, .165, .178, .19, .20, .25], .003)
x1 = .25 + np.r_[0, np.cumsum(np.geomspace(.0035, .022, 72))] * .75 / sum(np.geomspace(.0035, .022, 72))
x = np.unique(np.round(np.r_[x0, x1, np.linspace(1, 3, 91),
                             3 + np.r_[0, np.cumsum(np.geomspace(.022, .005, 60))] * .8 / sum(np.geomspace(.022, .005, 60)),
                             np.linspace(3.8, 4, 41)], 10))
# y, up from the floor: 3 mm or less to 0.83 m, with lines at the floor gap (0.04), the
# rails (0.12, 0.72, 0.80), the radiator (0.15, 0.75), the top (0.815) and the edges of
# every slot (0.126 + 0.024 k and 0.012 above it, k = 0-24); 5 mm to the glass at 0.90 m;
# 12 mm up the glass to 2.10 m; narrowing to 4.8 mm at the ceiling, 2.4 m.
SLOTS = [(round(.126 + .024 * k, 9), round(.138 + .024 * k, 9)) for k in range(25)]
ykeys = sorted(set([0, .04, .12, .15, .72, .75, .8, .815, .83] + [round(.126 + .024 * i + j, 9) for i in range(25) for j in (0, .012)]))
y0 = grid(ykeys, .003)
y = np.unique(np.round(np.r_[y0, grid([.83, .875, .9], .005), np.linspace(.9, 2.1, 101),
                             2.1 + np.r_[0, np.cumsum(np.geomspace(.012, .0048, 38))] * .3 / sum(np.geomspace(.012, .0048, 38))], 10))

# the cover's parts and their MDF thickness, m (B&Q's 13 mm body and 3 mm grille; the top
# 15 mm, 81.5 less 80 cm)
THICKNESS = {"top": .015, "topRail": .013, "bottomRail": .013, "grille": .003}
KAPPA_MDF = 0.13  # W/m K


def baffle(i, j, axis, run):
    """The cover part on the face on the +x (axis 0) or +y (axis 1) side of cell (i, j)."""
    if run == "cover":
        if axis == 0 and abs(x[i + 1] - .165) < 1e-8:  # the front, at the grille's room face
            yc = (y[j] + y[j + 1]) / 2
            if .04 < yc < .12:
                return "bottomRail"
            if .72 < yc < .8:
                return "topRail"
            if .12 < yc < .72 and not any(.126 + .024 * k < yc < .138 + .024 * k for k in range(25)):
                return "grille"
        if axis == 1 and abs(y[j + 1] - .8) < 1e-8 and (x[i] + x[i + 1]) / 2 < .19:  # the top
            return "top"
    return None


def mesh(run, case):
    nx, ny = len(x) - 1, len(y) - 1
    cc, ids = [], {}
    for j in range(ny):
        for i in range(nx):
            xc, yc = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
            if .103 < xc < .123 and .15 < yc < .75:  # the steel panel: no air
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
    if run == "cover":
        for part in ["top", "topRail", "bottomRail", "grille"]:
            bd[part + "A"] = []
            bd[part + "B"] = []
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
                part = baffle(i, j, 0 if d == 1 else 1, run)
                if part:
                    bd[part + "A"].append((v, c))
                    bd[part + "B"].append((v[::-1], ids[n]))
                else:
                    internal.append((v, c, ids[n]))
            else:
                if n[0] < 0:
                    name = "glass" if .9 < (y[j] + y[j + 1]) / 2 < 2.1 else "outerWall"
                elif n[0] >= nx:
                    name = "innerWall"
                elif n[1] < 0:
                    name = "floor"
                elif n[1] >= ny:
                    name = "ceiling"
                else:
                    name = "radiatorPanel"
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


def fields(case, bounds):
    """0/T (the radiator panel at 55 C, the cover's baffles) and 0/IDefault."""
    txt = H("T", "volScalarField") + '#include "../../../config/caseSettings"\ndimensions [0 0 0 1 0 0 0];\ninternalField uniform $Tamb;\nboundaryField\n{\n'
    txt += "glass { type externalWallHeatFluxTemperature; mode coefficient; h uniform $hGlassExt; Ta uniform $Tout; kappaMethod fluidThermo; qr qr; value uniform $Tamb; }\n"
    txt += '"(floor|outerWall)" { type externalWallHeatFluxTemperature; mode flux; q uniform 0; kappaMethod fluidThermo; qr qr; value uniform $Tamb; }\n'
    txt += '"(ceiling|innerWall)" { type fixedValue; value uniform $Tamb; }\nradiatorPanel { type fixedValue; value uniform 328.15; }\nfrontAndBack { type empty; }\n'
    for name, n, start in bounds:
        if not name.endswith(("A", "B")) or name == "frontAndBack":
            continue
        part = name[:-1]
        other = part + ("B" if name.endswith("A") else "A")
        # 1-D steady conduction through the MDF; rho and Cp are required by the
        # thermophysical type but a thermalBaffle1D stores no heat
        txt += f'''{name}
{{
 type compressible::thermalBaffle1D<hConstSolidThermoPhysics>;
 sampleMode nearestPatchFace; samplePatch {other}; sampleRegion region0;
 offset (0 0 0);
 qr qr; qrRelaxation 1; qrNbr qr;
 thickness uniform {THICKNESS[part]};
 specie {{ molWeight 100; }}
 transport {{ kappa {KAPPA_MDF}; }}
 thermodynamics {{ Hf 0; Cp 1000; }}
 equationOfState {{ rho 700; }}
 value uniform 293.15;
}}
'''
    (case / "0/T").write_text(txt + "}\n")
    (case / "0/IDefault").write_text(H("IDefault", "volScalarField") + 'dimensions [1 0 -3 0 0 0 0];\ninternalField uniform 133.4;\nboundaryField\n{\nfrontAndBack {type empty;}\n".*" { type greyDiffusiveRadiation; value uniform 133.4;}\n}\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=["bare", "cover"])
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=16)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    shutil.copytree(TEMPLATE / "constant", case / "constant")
    shutil.copytree(TEMPLATE / "system", case / "system")
    shutil.copytree(TEMPLATE / "0.orig", case / "0")
    cc, nx, ny, conv, bounds = mesh(a.run, case)
    fields(case, bounds)
    (case / "system/decomposeParDict").write_text(
        "FoamFile {version 2.0; format ascii; class dictionary; object decomposeParDict;}\n"
        f"numberOfSubdomains {a.nprocs};\nmethod scotch;\n")
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny, "convectorCells": len(conv),
              "min_dx": float(min(np.diff(x))), "min_dy": float(min(np.diff(y))),
              "patches": {n: count for n, count, st in bounds},
              "slots": [{"bottom": lo, "top": hi,
                         "cells": int(sum((y[:-1] >= lo - 1e-8) & (y[1:] <= hi + 1e-8)))} for lo, hi in SLOTS]}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(conv), "cells, smallest",
          f'{report["min_dx"] * 1e3:.2f} x {report["min_dy"] * 1e3:.2f} mm')


if __name__ == "__main__":
    main()
