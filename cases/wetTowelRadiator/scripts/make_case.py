"""Write one run of the wet towel case: its mesh, its starting fields and its dictionaries.

    python3 scripts/make_case.py bare|clothes <runDir> [--nprocs N]

The section is a bedroom 3.0 m from the inner wall (x = 0) to the window wall (x = 3.0 m) and 2.4 m
high, one cell thick (z = 0 to 1 m). The mesh is written directly as a polyMesh from a Cartesian
grid with lines on every edge of the radiator, the towel and the bed; both runs share the grid.
Left out of it, their faces wall patches:

  radiatorPanel  the Stelrad K1's steel front panel, x = 0.103-0.123 m, y = 0.15-0.75 m
  bed            a divan, x = 0.75-2.65 m, y = 0-0.55 m
  cloth          (clothes only) the towel, an upturned U one cell thick: a back leg
                 x = 0.0175-0.021 m and a front leg x = 0.1335-0.137 m from y = 0.30 m up, joined by
                 a top y = 0.7598-0.768 m over x = 0.0175-0.137 m

The convector behind the panel (x = 0.040-0.103 m, y = 0.15-0.75 m) is the cellZone convector.
The window wall is glass from y = 0.9 to 2.1 m and outerWall above and below it.

template/common/ and template/<run>/ are copied in unchanged; 0/ (every field, the pressure at rest
in hydrostatic balance), system/decomposeParDict and constant/polyMesh are written here.

The grid and the mesh are the study's: its builder took radiatorCover's make_case.py and edited it
in place; this script is that code with the edits written out, and it writes the solved runs'
polyMesh and 0/ byte for byte (README, "Running it").
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"


def H(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


# ---- the grid ----------------------------------------------------------------------------
def graded(keys, size):
    """Lines through every key, spaced by the local cell size size(t) between them."""
    out = []
    for a, b in zip(keys[:-1], keys[1:]):
        t = np.linspace(a, b, 2001)
        w = 1 / size(t)
        s = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]
        n = max(1, round(s[-1]))
        out.extend(np.interp(np.linspace(0, s[-1], n + 1), s, t)[:-1])
    return np.r_[out, keys[-1]]


# x: the wall behind the radiator (0), the towel's back leg (0.0175, 0.021), the convector (0.040),
# the panel (0.103, 0.123), the towel's front leg (0.1335, 0.137), the bed (0.75, 2.65) and the
# window wall (3.0); 3.5 mm cells to 0.21 m, 20 mm from 0.75 to 2.75 m, 5 mm at the window.
XKEYS = [0, .0175, .021, .04, .103, .123, .1335, .137, .21, .60, .75, 2.65, 2.75, 3.]
# y: the towel's hem (0.30), the radiator (0.15, 0.75), the towel's top (0.7598, 0.768), the bed
# (0.55), the glass (0.9, 2.1) and the ceiling (2.4); 8.3 mm to 0.85 m, 14.9 mm up the room, 6 mm
# under the ceiling.
YKEYS = [0, .15, .3, .55, .75, .7598, .768, .85, .9, 2.1, 2.25, 2.34, 2.4]
x = graded(XKEYS, lambda t: np.interp(t, [0, .21, .75, 2.75, 3], [.0035, .0035, .020, .020, .005]))
y = graded(YKEYS, lambda t: np.interp(t, [0, .85, 1.1, 2.25, 2.34, 2.4], [.0083, .0083, .0149, .0149, .006, .006]))
# the towel's top (y = 0.7598-0.768) and the 9.8 mm gap under it (0.75-0.7598) one cell each
for a, b in [(.75, .7598), (.7598, .768)]:
    y = y[(y <= a + 1e-10) | (y >= b - 1e-10)]
# smooth the grid by moving lines that are not keys until neighbouring cells differ by at most
# 1.195 times (x is moved in place, y after the cut above)
for arr, keys in [(x, XKEYS), (y, YKEYS)]:
    fixed = {i for i, a in enumerate(arr) if min(abs(a - k) for k in keys) < 1e-9}
    for _ in range(2000):
        for i in range(1, len(arr) - 1):
            if i in fixed:
                continue
            a = arr[i] - arr[i - 1]
            b = arr[i + 1] - arr[i]
            if max(a / b, b / a) > 1.195:
                arr[i] = (arr[i - 1] + arr[i + 1]) / 2


def solid(run, xc, yc):
    """Whether the cell centred at (xc, yc) is left out of the mesh."""
    if .103 < xc < .123 and .15 < yc < .75:  # the steel panel
        return True
    if .75 < xc < 2.65 and yc < .55:  # the bed
        return True
    if run == "clothes" and ((.0175 < xc < .021 or .1335 < xc < .137) and .3 < yc < .768
                             or .0175 < xc < .137 and .7598 < yc < .768):  # the towel
        return True
    return False


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
    bd = {k: [] for k in ["floor", "ceiling", "innerWall", "outerWall", "glass", "radiatorPanel", "frontAndBack", "bed"]}
    if run == "clothes":
        bd["cloth"] = []
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
                if d in (1, 3):  # each internal face once, from the cell below or left of it
                    internal.append((v, c, ids[n]))
                continue
            if n[0] < 0:
                name = "innerWall"
            elif n[0] >= nx:
                name = "glass" if .9 < (y[j] + y[j + 1]) / 2 < 2.1 else "outerWall"
            elif n[1] < 0:
                name = "floor"
            elif n[1] >= ny:
                name = "ceiling"
            else:  # a cell left out of the mesh
                xx, yy = (x[n[0]] + x[n[0] + 1]) / 2, (y[n[1]] + y[n[1] + 1]) / 2
                name = "radiatorPanel" if .103 < xx < .123 and .15 < yy < .75 else ("bed" if .75 < xx < 2.65 and yy < .55 else "cloth")
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
        group = "" if name == "frontAndBack" else "\n inGroups 1(wall);"
        txt += f'{name}\n{{\n type {"empty" if name == "frontAndBack" else "wall"};{group}\n nFaces {n};\n startFace {start};\n}}\n'
    (pm / "boundary").write_text(txt + ")\n")
    conv = np.where((cc[:, 0] > .04) & (cc[:, 0] < .103) & (cc[:, 1] > .15) & (cc[:, 1] < .75))[0]
    (pm / "cellZones").write_text(H("cellZones", "regIOobject") + "1\n(\nconvector\n{\n type cellZone;\n cellLabels List<label>\n"
                                  + str(len(conv)) + "\n(\n" + "\n".join(map(str, conv)) + "\n);\n}\n)\n")
    for name, cls in [("faceZones", "regIOobject"), ("pointZones", "regIOobject")]:
        (pm / name).write_text(H(name, cls) + "0\n(\n)\n")
    return cc, nx, ny, conv, bounds


# ---- the starting fields -------------------------------------------------------------------
T0 = 289.15     # 16 C: the air and every inner surface at rest
Y0 = .00695     # water vapour's mass fraction, 7 g per kg of air
RU = 8314.46261815324
# the mixture's gas constant: H2O, then O2 and N2 in air's 23.15 : 76.85 by mass
R = RU * (Y0 / 18.0153 + .2315 * (1 - Y0) / 31.9988 + (1 - Y0) * .7685 / 28.0134)


def fields(case, run, cc, bounds):
    patches = [p for p, n, s in bounds if p != "frontAndBack"]
    wl = '"(' + "|".join(patches) + ')"'

    def F(n, dim, value, body, cls="volScalarField"):
        (case / "0" / n).write_text(H(n, cls) + f"dimensions {dim};\ninternalField uniform {value};\nboundaryField\n{{\n"
                                    + body + "\nfrontAndBack {type empty;}\n}\n")

    F("U", "[0 1 -1 0 0 0 0]", "(0 0 0)", wl + " {type noSlip;}", "volVectorField")
    for n, dim, v, typ in [("k", "[0 2 -2 0 0 0 0]", "1e-4", "kLowReWallFunction"),
                           ("omega", "[0 0 -1 0 0 0 0]", "1", "omegaWallFunction"),
                           ("nut", "[0 2 -1 0 0 0 0]", "0", "nutkWallFunction"),
                           ("alphat", "[1 -1 -1 0 0 0 0]", "0", "compressible::alphatJayatillekeWallFunction")]:
        F(n, dim, v, wl + f" {{type {typ}; " + ("Prt 0.85;" if n == "alphat" else "") + f" value uniform {v};}}")
    # at rest in hydrostatic balance, 1e5 Pa at y = 1.174 m
    p = 1e5 * np.exp(-9.81 * (cc[:, 1] - 1.174) / (R * T0))
    rho = p / (R * T0)
    for n, vals, typ in [("p", p, "calculated"), ("p_rgh", p + rho * 9.81 * cc[:, 1], "fixedFluxPressure")]:
        F(n, "[1 -1 -2 0 0 0 0]", "1e5", wl + f" {{type {typ}; value uniform 1e5;}}")
        f = case / "0" / n
        f.write_text(f.read_text().replace("internalField uniform 1e5;", f"internalField nonuniform List<scalar>\n{len(vals)}\n(\n"
                                           + "\n".join(map(str, vals)) + "\n);"))
    # T: the panel at 55 C; the towel's and the glass's temperatures are set every step by the
    # wetWalls function object (system/wetWalls), from 16 C and 10.2 C. Every other wall is
    # radLayerWall: 24 nodes of gypsum board (ceiling, inner wall), wood (floor) or foam (bed)
    # with an adiabatic back, or (outerWall) a massless wall, h = 1.863 W/m2K to 0 C.
    txt = ""
    for patch in patches:
        if patch in ["radiatorPanel", "cloth", "glass"]:
            txt += f"{patch} {{type fixedValue; value uniform " + str(dict(radiatorPanel=328.15, cloth=289.15, glass=283.35)[patch]) + ";}\n"
            continue
        N, th, k, rc, h, ta, ti = 24, .0127, .1587, 723991., 0, 0, 289.15
        if patch == "floor":
            th, k, rc = .019, .106, 1237411.2
        if patch == "bed":
            th, k, rc = .05, .04, 49000
        if patch == "outerWall":
            N, h, ta, ti = 0, 1.863, 273.15, 286.03
        txt += (f"{patch} {{type radLayerWall; kappaMethod fluidThermo; Q 0; h {h}; Ta {ta}; emissivity 0.9; Tinit {ti}; "
                f"nLayers {N}; thickness {th}; conductivity {k}; rhoCp {rc}; value uniform {ti};}}\n")
    F("T", "[0 0 0 1 0 0 0]", T0, txt)
    # the species; on the towel and the glass H2O is set every step by wetWalls
    for n, v in [("H2O", Y0), ("O2", .2315 * (1 - Y0)), ("N2", .7685 * (1 - Y0)), ("Ydefault", 0)]:
        txt = ""
        for patch in patches:
            txt += patch + (" {type mixed; refValue uniform 0.00695; refGradient uniform 0; valueFraction uniform 0; value uniform 0.00695;}\n"
                            if n == "H2O" and patch in ["glass", "cloth"] else " {type zeroGradient;}\n")
        F(n, "[0 0 0 0 0 0 0]", v, txt)
    F("IDefault", "[1 0 -3 0 0 0 0]", 126.15, '".*" {type greyDiffusiveRadiation; value uniform 126.15;}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=["bare", "clothes"])
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    shutil.copytree(TEMPLATE / "common", case)
    shutil.copytree(TEMPLATE / a.run, case, dirs_exist_ok=True)
    (case / "0").mkdir()
    cc, nx, ny, conv, bounds = mesh(a.run, case)
    fields(case, a.run, cc, bounds)
    (case / "system/decomposeParDict").write_text(H("decomposeParDict") + f"numberOfSubdomains {a.nprocs}; method scotch;\n")
    (case / "room.foam").touch()
    # the cells, for scripts/extract_results.py
    np.savez(case / "grid.npz", x=x, y=y, cc=cc)
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny, "convectorCells": len(conv),
              "min_dx": float(np.diff(x).min()), "min_dy": float(np.diff(y).min()),
              "max_dx": float(np.diff(x).max()), "max_dy": float(np.diff(y).max()),
              "patches": {n: count for n, count, st in bounds},
              "initialMass_kg": float(sum(np.diff(x)[np.searchsorted(x, cc[:, 0]) - 1] * np.diff(y)[np.searchsorted(y, cc[:, 1]) - 1]
                                          * 1e5 * np.exp(-9.81 * (cc[:, 1] - 1.174) / (R * T0)) / (R * T0)))}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(conv), "cells, smallest",
          f'{report["min_dx"] * 1e3:.2f} x {report["min_dy"] * 1e3:.2f} mm')


if __name__ == "__main__":
    main()
