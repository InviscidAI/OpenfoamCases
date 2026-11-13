"""Write one run of the radiator fan bar case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py bare|fan <runDir> [--nprocs N]

The mesh is written directly as a polyMesh, one cell thick (z = 0 to 1 m), from a graded
Cartesian grid of 184 x 180 cells over the room's 3.4 x 2.7 m section, with lines on every edge
of the radiator, the fan bar and the window. The writer is radiatorCover's
(../radiatorCover/scripts/make_case.py, its bare room) with this room's grid, a double panel
and the bar:

- the radiator's two steel panels (x = 0.024-0.042 and 0.106-0.124 m, y = 0.10-0.70 m) are left
  out of the mesh, their faces the patch radiatorPanel; the fins between them (x = 0.042-0.106,
  same y) are the cellZone convector, 660 cells; the 24 mm behind the back panel stays open air;
- the fan bar's housing, only in the fan run: a top plate (x = 0.024-0.124, y = 0.72-0.73 m) and
  a back plate (x = 0.024-0.042, y = 0.70-0.72 m) left out of the mesh, their faces the patch
  fanBar. Under the top plate is a 20 mm channel whose floor is the fins' open top and the front
  panel's top face, and whose outlet faces the room at x = 0.124 m. In the bare run the plates'
  46 cells are plain air and every other cell centre is the fan run's;
- the cellZone fan, 12 cells over the front panel inside the channel (x = 0.106-0.124,
  y = 0.70-0.72 m), is driven only in the fan run (constant/fanSettings);
- the faceZones fanIn and fanOut (4 faces each, x = 0.106 and 0.124 m) and convIn and convOut
  (11 faces each, y = 0.10 and 0.70 m) are the zones' outer faces across their flow direction;
- the window wall at x = 0 is glass from y = 0.85 to 2.45 m and outerWall below and above it;
  the inner wall at x = 3.4 m is innerWall.

The files under template/common/ and template/<run>/ are copied in unchanged (0.orig/ into
0/). This script writes the polyMesh, the hydrostatic 0/p and 0/p_rgh at rest and
system/decomposeParDict. Its mesh and 0/p, 0/p_rgh are the solved runs' byte for byte.
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

TAMB = 289.15                      # 16 C, the air and every wall layer at t = 0
R = 8314.46261815324 / 28.96
YREF = 1.35                        # p = 1e5 Pa at the pressure reference's height
RUNS = ["bare", "fan"]


def H(n, c="dictionary"):
    return f"FoamFile {{version 2.0; format ascii; class {c}; object {n};}}\n"


def graded(keys, fn):
    """Lines through every key, cells close to fn(t) long; the cell counts of two intervals are
    set by hand (one more over 0.90-1.10 m, rounded up over 0.85-0.90 m)."""
    out = []
    for a, b in zip(keys[:-1], keys[1:]):
        t = np.linspace(a, b, 4001)
        w = 1 / fn(t)
        s = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]
        n = math.ceil(s[-1]) + 1 if abs(a - .9) < 1e-9 else math.ceil(s[-1]) if abs(a - .85) < 1e-9 else round(s[-1])
        out.extend(np.interp(np.linspace(0, s[-1], n + 1), s, t)[:-1])
    return np.r_[out, keys[-1]]


# ---- the grid ----------------------------------------------------------------------------
# x, from the window wall: 6 mm to 0.2 m, through the back panel (0.024, 0.042) and the front
# panel (0.106, 0.124); 9.5 mm to 0.6 m; 28 mm from 0.8 m to the inner wall at 3.4 m.
x = graded([0, .024, .042, .106, .124, .2, .5, .6, 3.3, 3.4],
           lambda t: np.interp(t, [0, .2, .3, .6, .8, 3.4], [.006, .006, .0095, .0095, .028, .028]))
# y, up from the floor: 11.5 mm to the radiator's top, 5 mm through the bar (0.70, 0.72, 0.73)
# and its outlet, the glass (0.85, 2.45), 28 mm in the middle of the room, 11.5 mm under the
# ceiling at 2.7 m.
y = graded([0, .1, .6, .66, .7, .72, .73, .78, .85, .9, 1.1, 2.45, 2.6, 2.7],
           lambda t: np.interp(t, [0, .58, .66, .78, .86, .9, 1.1, 2.35, 2.55, 2.64, 2.7],
                               [.0115, .0115, .005, .005, .0115, .011, .028, .028, .0115, .0115, .0115]))


def ratio(d):
    return float(max(max(d[1:] / d[:-1]), max(d[:-1] / d[1:])))


assert ratio(np.diff(x)) <= 1.15 and ratio(np.diff(y)) <= 1.15
# the cell-size limits by region, counting cells that cross a region's edge
for coords, ranges in [(x, [(0, .2, .006), (.2, .6, .01), (.6, 3.4, .03)]),
                       (y, [(0, .66, .012), (.66, .78, .005), (.78, .9, .012), (.9, 2.64, .03), (2.64, 2.7, .012)])]:
    for lo, hi, lim in ranges:
        assert np.diff(coords)[(coords[:-1] < hi - 1e-10) & (coords[1:] > lo + 1e-10)].max() <= lim + 1e-10


def panel(a, b):
    return (.024 < a < .042 or .106 < a < .124) and .1 < b < .7


def plate(a, b):
    return (.024 < a < .124 and .72 < b < .73) or (.024 < a < .042 and .7 < b < .72)


def lst(pm, name, cls, items):
    with (pm / name).open("w") as f:
        f.write(H(name, cls) + f"{len(items)}\n(\n")
        f.write("\n".join(items))
        f.write("\n)\n")


def mesh(run, case):
    nx, ny = len(x) - 1, len(y) - 1
    cc, ids = [], {}
    for j in range(ny):
        for i in range(nx):
            xc, yc = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
            if panel(xc, yc) or (run == "fan" and plate(xc, yc)):  # steel: no air
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
    if run == "fan":
        bd["fanBar"] = []
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
                    name = "glass" if .85 < (y[j] + y[j + 1]) / 2 < 2.45 else "outerWall"
                elif n[0] >= nx:
                    name = "innerWall"
                elif n[1] < 0:
                    name = "floor"
                elif n[1] >= ny:
                    name = "ceiling"
                else:
                    name = "radiatorPanel" if panel((x[n[0]] + x[n[0] + 1]) / 2, (y[n[1]] + y[n[1] + 1]) / 2) else "fanBar"
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
    points = [f"({a:.10g} {b:.10g} {c:.10g})" for a, b, c in pts[used]]
    faces = [[remap[v] for v in f] for f in faces]
    lst(pm, "points", "vectorField", points)
    lst(pm, "faces", "faceList", ["4(" + " ".join(map(str, f)) + ")" for f in faces])
    lst(pm, "owner", "labelList", list(map(str, own)))
    lst(pm, "neighbour", "labelList", list(map(str, nbr)))
    txt = H("boundary", "polyBoundaryMesh") + f"{len(bounds)}\n(\n"
    for name, n, start in bounds:
        txt += f'{name}\n{{\n type {"empty" if name == "frontAndBack" else "wall"};\n nFaces {n};\n startFace {start};\n}}\n'
    (pm / "boundary").write_text(txt + ")\n")
    (pm / "pointZones").write_text(H("pointZones", "regIOobject") + "0\n(\n)\n")

    # the cell zones: the fins and the fan
    conv = np.where((cc[:, 0] > .042) & (cc[:, 0] < .106) & (cc[:, 1] > .1) & (cc[:, 1] < .7))[0]
    fan = np.where((cc[:, 0] > .106) & (cc[:, 0] < .124) & (cc[:, 1] > .7) & (cc[:, 1] < .72))[0]
    zones = {"convector": conv, "fan": fan}
    (pm / "cellZones").write_text(H("cellZones", "regIOobject") + "2\n(\n" + "".join(
        n + "\n{ type cellZone; cellLabels List<label>\n" + str(len(z)) + "\n(\n" + "\n".join(map(str, z)) + "\n);\n}\n"
        for n, z in zones.items()) + ")\n")

    # the face zones: a zone's outer faces (its boundary faces too) lying in the plane across its
    # flow direction, the flip set where the face's normal points against +x (fan) or +y (fins)
    P = np.array([list(map(float, s.strip("()").split())) for s in points])
    fzones = {}
    for n, z, axis, loc in [("fanIn", "fan", 0, .106), ("fanOut", "fan", 0, .124),
                            ("convIn", "convector", 1, .1), ("convOut", "convector", 1, .7)]:
        cells = set(zones[z].tolist())
        ff, fl = [], []
        for k, v in enumerate(faces):
            if (own[k] in cells) == (k < len(nbr) and nbr[k] in cells):
                continue
            vs = P[v]
            cf = vs.mean(axis=0)
            sf = np.cross(vs[1] - vs[0], vs[2] - vs[0])
            if abs(cf[axis] - loc) < 1e-9 and abs(sf[axis]) > 1e-12:
                ff.append(k)
                fl.append(sf[axis] < 0)
        assert ff, n
        fzones[n] = (ff, fl)
    (pm / "faceZones").write_text(H("faceZones", "regIOobject") + "4\n(\n" + "".join(
        n + "\n{ type faceZone; faceLabels List<label>\n" + str(len(ff)) + "\n(\n" + "\n".join(map(str, ff))
        + "\n); flipMap List<bool>\n" + str(len(fl)) + "\n(\n" + "\n".join("true" if f else "false" for f in fl) + "\n); }\n"
        for n, (ff, fl) in fzones.items()) + ")\n")
    return cc, nx, ny, zones, fzones, bounds


def hydrostatic(cc):
    """The air at rest at 16 C in hydrostatic balance: p, rho and p_rgh in every cell."""
    p = 1e5 * np.exp(-9.81 * (cc[:, 1] - YREF) / (R * TAMB))
    rho = p / (R * TAMB)
    return p, rho, p + rho * 9.81 * cc[:, 1]


def volumes(cc):
    i = np.searchsorted(x, cc[:, 0]) - 1
    j = np.searchsorted(y, cc[:, 1]) - 1
    return np.diff(x)[i] * np.diff(y)[j]


def centres(run):
    """The air's cell centres of a run, in the mesh's order, without writing it."""
    return np.array([((x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2, .5)
                     for j in range(len(y) - 1) for i in range(len(x) - 1)
                     if not (panel((x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2)
                             or (run == "fan" and plate((x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2)))])


def initial_integrals(run):
    """The air's mass and internal energy (cv/R) integral p dV at t = 0, whole section and the
    convector zone, per metre; scripts/extract_results.py starts the fins' balance here."""
    cc = centres(run)
    p, rho, _ = hydrostatic(cc)
    v = volumes(cc)
    z = (cc[:, 0] > .042) & (cc[:, 0] < .106) & (cc[:, 1] > .1) & (cc[:, 1] < .7)
    cv = 1005 - R
    return dict(mass=float(np.sum(rho * v)), energy=float(cv / R * np.sum(p * v)),
                zoneMass=float(np.sum(rho[z] * v[z])), zoneEnergy=float(cv / R * np.sum(p[z] * v[z])),
                zoneVolume=float(np.sum(v[z])))


def fields(case, cc):
    p, rho, p_rgh = hydrostatic(cc)
    for n, vals in [("p", p), ("p_rgh", p_rgh)]:
        bc = "calculated" if n == "p" else "fixedFluxPressure"
        (case / "0" / n).write_text(
            H(n, "volScalarField") + "dimensions [1 -1 -2 0 0 0 0];\ninternalField nonuniform List<scalar>\n"
            + str(len(vals)) + "\n(\n" + "\n".join(map(str, vals)) + "\n);\nboundaryField\n{\n"
            + '"(floor|ceiling|innerWall|outerWall|glass|radiatorPanel|fanBar)" {type ' + bc
            + "; value uniform 1e5;}\nfrontAndBack {type empty;}\n}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=RUNS)
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=7)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    shutil.copytree(TEMPLATE / "common/constant", case / "constant")
    shutil.copytree(TEMPLATE / "common/system", case / "system")
    shutil.copytree(TEMPLATE / "common/0.orig", case / "0")
    shutil.copytree(TEMPLATE / a.run / "constant", case / "constant", dirs_exist_ok=True)
    shutil.copytree(TEMPLATE / a.run / "0.orig", case / "0", dirs_exist_ok=True)
    cc, nx, ny, zones, fzones, bounds = mesh(a.run, case)
    fields(case, cc)
    (case / "system/decomposeParDict").write_text(H("decomposeParDict") + f"numberOfSubdomains {a.nprocs};\nmethod scotch;\n")
    dx, dy = np.diff(x), np.diff(y)
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny,
              "min_dx": float(dx.min()), "min_dy": float(dy.min()),
              "max_dx": float(dx.max()), "max_dy": float(dy.max()),
              "ratio_x": ratio(dx), "ratio_y": ratio(dy),
              "zones": {n: len(z) for n, z in zones.items()},
              "faceZones": {n: len(f) for n, (f, fl) in fzones.items()},
              "patches": {n: count for n, count, st in bounds}}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    (case / "case.foam").touch()
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(zones["convector"]), "cells, fan",
          len(zones["fan"]), "cells, smallest", f'{report["min_dx"] * 1e3:.3f} x {report["min_dy"] * 1e3:.3f} mm')


if __name__ == "__main__":
    main()
