"""Write one run of the tall-room fan case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py nofan|fan_ceiling|fan_radiator|bare <runDir> [--nprocs N]

The mesh is written directly as a polyMesh, one cell thick (z = 0 to 1 m), from a graded
Cartesian grid of 240 x 183 cells over the room's 5.0 x 3.3 m section, with lines on every edge
of the radiator, the window and both fans. The writer is radiatorCover's
(../radiatorCover/scripts/make_case.py, its bare room) with this room's grid and window:

- the radiator's steel front panel (x = 0.103-0.123, y = 0.15-0.75) is left out of the mesh, its
  faces the patch radiatorPanel; the convector behind it (x = 0.040-0.103, same y) is the
  cellZone convector;
- the window wall at x = 0 is glass from y = 0.90 to 2.90 m and outerWall below and above it;
  the inner wall at x = 5.0 m is innerWall;
- the fan aimed at the radiator is the cellZone fan_radiator (centres x = 0.95-1.01 m,
  y = 0.055-0.245 m) and the fan aimed at the ceiling the cellZone fan_ceiling (centres
  x = 3.905-4.095 m, y = 0.22-0.28 m); fan is the two together. Both are in every run's mesh,
  as plain air unless constant/fvOptions drives one. The faceZones <fan>Out and <fan>In are the
  zone's outer faces across its blowing direction, on the outlet and the inlet side, for the
  flow monitors.

Every run has the same mesh and fields. The files under template/common/ and
template/<run>/ (bare: template/nofan/ and template/bare/) are copied in unchanged. This
script writes 0/T (every wall but the panel a radLayerWall), 0/IDefault, the hydrostatic 0/p
and 0/p_rgh at rest, the polyMesh and system/decomposeParDict.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"

TAMB = 289.15                      # 16 C, the air and every wall layer at t = 0
R = 8314.46261815324 / 28.96
YREF = 1.65                        # p = 1e5 Pa at the pressure reference's height
RUNS = ["nofan", "fan_ceiling", "fan_radiator", "bare"]


def H(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def graded(keys, size, cap):
    """Lines through every key, cells close to size(t) long, no cell longer than cap(t) and
    neighbours within 1.15 of each other, by alternating projections onto the three."""
    out, groups, caps = [], [], []
    for a, b in zip(keys[:-1], keys[1:]):
        t = np.linspace(a, b, 2001)
        w = 1 / size(t)
        s = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]
        n = int(np.ceil(s[-1] - 1e-9))
        # two intervals in y set by hand: 7 cells over 0.15-0.22 and 4 over 0.245-0.28
        n = 7 if abs(a - .15) < 1e-8 and abs(b - .22) < 1e-8 else 4 if abs(a - .245) < 1e-8 else n
        pts = np.interp(np.linspace(0, s[-1], n + 1), s, t)
        groups.append((len(out), len(out) + n, b - a))
        out.extend(np.diff(pts))
        caps.extend([cap((a + b) / 2) * 1.00000001] * n)
    d, caps = np.array(out), np.array(caps)
    for it in range(50000):
        for i in range(len(d) - 1):
            if d[i] > 1.1499 * d[i + 1]:
                v = (d[i] - 1.1499 * d[i + 1]) / (1 + 1.1499 ** 2)
                d[i] -= v
                d[i + 1] += 1.1499 * v
            if d[i + 1] > 1.1499 * d[i]:
                v = (d[i + 1] - 1.1499 * d[i]) / (1 + 1.1499 ** 2)
                d[i + 1] -= v
                d[i] += 1.1499 * v
        d = np.minimum(d, caps)
        for a, b, L in groups:
            d[a:b] += (L - d[a:b].sum()) / (b - a)
        if it % 50 == 0 and max(np.max(d / caps), np.max(d[1:] / d[:-1]) / 1.15, np.max(d[:-1] / d[1:]) / 1.15) < 1 + 1e-8:
            break
    assert np.max(d / caps) < 1.00001
    assert max(np.max(d[1:] / d[:-1]), np.max(d[:-1] / d[1:])) < 1.15001
    return np.r_[0, np.cumsum(d)]


# ---- the grid ----------------------------------------------------------------------------
# x, from the window wall to the inner wall: 10 mm to 0.3 m, through the convector (0.040), the
# panel (0.103, 0.123), the radiator fan's zone (0.95, 1.01) and the ceiling fan's (3.905,
# 4.095); 15 mm around each fan, up to 29 mm between, at most 30 mm.
x = graded([0, .04, .103, .123, .30, .60, .85, .95, 1.01, 1.10, 1.4, 3.5, 3.8, 3.905, 4.095, 4.2, 4.5, 5],
           lambda t: np.interp(t, [0, .3, .6, .85, 1.1, 1.4, 3.5, 3.8, 4.2, 4.5, 5],
                               [.010, .010, .029, .015, .015, .029, .029, .015, .015, .029, .029]),
           lambda t: .01 if t < .3 else .015 if .85 < t < 1.1 or 3.8 < t < 4.2 else .03)
# y, up from the floor: 12 mm to 0.9 m, through the radiator fan's zone (0.055, 0.245), the
# radiator (0.15, 0.75), the ceiling fan's zone (0.22, 0.28), the glass (0.90, 2.90) and the
# monitored lines (1.1, 1.5, 3.2); 29 mm from 1.1 to 2.9 m; 12 mm under the ceiling at 3.3 m.
y = graded([0, .055, .15, .22, .245, .28, .75, .9, 1.1, 1.5, 1.8, 2.9, 3.1, 3.2, 3.24, 3.3],
           lambda t: np.interp(t, [0, .9, 1.1, 2.9, 3.1, 3.3], [.012, .012, .029, .029, .012, .012]),
           lambda t: .012 if t < .9 or t > 3.24 else .03)


def lst(pm, name, cls, items):
    with (pm / name).open("w") as f:
        f.write(H(name, cls) + f"{len(items)}\n(\n")
        f.write("\n".join(items))
        f.write("\n)\n")


def mesh(case):
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
                    name = "glass" if .9 < (y[j] + y[j + 1]) / 2 < 2.9 else "outerWall"
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
    lst(pm, "points", "vectorField", [f"({a:.10g} {b:.10g} {c:.10g})" for a, b, c in pts[used]])
    lst(pm, "faces", "faceList", ["4(" + " ".join(str(remap[v]) for v in f) + ")" for f in faces])
    lst(pm, "owner", "labelList", list(map(str, own)))
    lst(pm, "neighbour", "labelList", list(map(str, nbr)))
    txt = H("boundary", "polyBoundaryMesh") + f"{len(bounds)}\n(\n"
    for name, n, start in bounds:
        txt += f'{name}\n{{\n type {"empty" if name == "frontAndBack" else "wall"};\n nFaces {n};\n startFace {start};\n}}\n'
    (pm / "boundary").write_text(txt + ")\n")
    (pm / "pointZones").write_text(H("pointZones", "regIOobject") + "0\n(\n)\n")

    # the cell zones: the convector and both fans
    conv = np.where((cc[:, 0] > .04) & (cc[:, 0] < .103) & (cc[:, 1] > .15) & (cc[:, 1] < .75))[0]
    fanR = np.where((cc[:, 0] > .95) & (cc[:, 0] < 1.01) & (cc[:, 1] > .055) & (cc[:, 1] < .245))[0]
    fanC = np.where((cc[:, 0] > 3.905) & (cc[:, 0] < 4.095) & (cc[:, 1] > .22) & (cc[:, 1] < .28))[0]
    zones = {"convector": conv, "fan_radiator": fanR, "fan_ceiling": fanC, "fan": np.r_[fanR, fanC]}
    txt = H("cellZones", "regIOobject") + str(len(zones)) + "\n(\n"
    for n, z in zones.items():
        txt += n + "\n{type cellZone; cellLabels List<label>\n" + str(len(z)) + "\n(\n" + "\n".join(map(str, z)) + "\n);\n}\n"
    (pm / "cellZones").write_text(txt + ")\n")

    # the face zones: each fan zone's outer internal faces across its blowing direction (-x for
    # fan_radiator, +y for fan_ceiling), Out on the downstream side and In on the upstream side,
    # flipped where needed so that a positive flux runs along the blowing direction
    own, nbr = np.array(own[:len(nbr)]), np.array(nbr)
    dc = cc[nbr] - cc[own]
    sets = pm / "sets"
    sets.mkdir()
    fzones = {}
    for name, z, axis, sgn in [("fan_radiator", fanR, 0, -1), ("fan_ceiling", fanC, 1, 1)]:
        (sets / (name + "Cells")).write_text(H(name + "Cells", "cellSet") + str(len(z)) + "\n(\n" + "\n".join(map(str, z)) + "\n)\n")
        inside = np.zeros(len(cc), bool)
        inside[z] = True
        outer = inside[own] ^ inside[nbr]
        axial = outer & (np.abs(dc[:, axis]) > 1e-8)
        side = np.where(inside[own], 1, -1)  # +1: the face's normal points out of the zone
        for suffix, want in [("Out", sgn), ("In", -sgn)]:
            fzones[name + suffix] = (np.where(axial & (side == want))[0], sgn < 0)
    txt = H("faceZones", "regIOobject") + str(len(fzones)) + "\n(\n"
    for n, (f, flip) in fzones.items():
        txt += (n + "\n{type faceZone; faceLabels List<label>\n" + str(len(f)) + "\n(\n" + "\n".join(map(str, f))
                + "\n);\nflipMap List<bool>\n" + str(len(f)) + "\n(\n" + "\n".join(["1" if flip else "0"] * len(f)) + "\n);\n}\n")
    (pm / "faceZones").write_text(txt + ")\n")
    return cc, nx, ny, zones, fzones, bounds


def hydrostatic(cc):
    """The air at rest at 16 C in hydrostatic balance: p, rho and p_rgh in every cell."""
    p = 1e5 * np.exp(-9.81 * (cc[:, 1] - YREF) / (R * TAMB))
    rho = p / (R * TAMB)
    return p, rho, p + rho * 9.81 * cc[:, 1]


def volumes(cc):
    i = np.searchsorted(x, cc[:, 0])
    j = np.searchsorted(y, cc[:, 1])
    return (x[i] - x[i - 1]) * (y[j] - y[j - 1])


def initial_integrals():
    """The air's mass and internal energy (cv/R) integral p dV at t = 0, whole section and the
    convector zone, per metre; scripts/extract_results.py starts the convector's balance here."""
    cc = np.array([((x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2, .5)
                   for j in range(len(y) - 1) for i in range(len(x) - 1)
                   if not (.103 < (x[i] + x[i + 1]) / 2 < .123 and .15 < (y[j] + y[j + 1]) / 2 < .75)])
    p, rho, _ = hydrostatic(cc)
    v = volumes(cc)
    z = (cc[:, 0] > .04) & (cc[:, 0] < .103) & (cc[:, 1] > .15) & (cc[:, 1] < .75)
    cv = 1005 - R
    return dict(mass=float(np.sum(rho * v)), U=float(cv / R * np.sum(p * v)),
                zoneMass=float(np.sum(rho[z] * v[z])), zoneU=float(cv / R * np.sum(p[z] * v[z])))


# Every wall but the panel is a radLayerWall (src/radLayerWall): convection and the radiation
# it absorbs on the room side, and behind it a 1-D layer of 24 slices with its heat capacity
# and an adiabatic back, all starting at 16 C. The glass has no layer: a film of 4.403 W/m2K
# to 0 C outside. Thickness m, conductivity W/m K, rho*cp J/m3 K.
FLOOR = (.019, .106, 1237411.2)     # 19 mm wood
GYPSUM = (.0127, .1587, 723991.)    # 12.7 mm gypsum board: ceiling, inner wall, window wall


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
        th, k, rc = FLOOR if patch == "floor" else GYPSUM
        if patch == "glass":
            h, ta, eps, nl = 4.403, 273.15, .84, 0
        txt += (f"{patch}\n{{type radLayerWall; kappaMethod fluidThermo; Q 0; h {h}; Ta {ta}; emissivity {eps}; "
                f"Tinit 289.15; nLayers {nl}; thickness {th}; conductivity {k}; rhoCp {rc}; value uniform 289.15;}}\n")
    (case / "0/T").write_text(txt + "}\n")
    # the radiation at t = 0: black-body intensity at 16 C
    (case / "0/IDefault").write_text(H("IDefault", "volScalarField") + 'dimensions [1 0 -3 0 0 0 0]; internalField uniform 126.15; boundaryField { frontAndBack {type empty;} ".*" {type greyDiffusiveRadiation; value uniform 126.15;} }\n')
    p, rho, p_rgh = hydrostatic(cc)
    for name, vals in [("p", p), ("p_rgh", p_rgh)]:
        f = case / "0" / name
        body = f.read_text()
        assert "internalField   uniform 1e5;" in body, name
        f.write_text(re.sub(r"internalField.*?;", "internalField nonuniform List<scalar>\n" + str(len(vals))
                            + "\n(\n" + "\n".join(map(str, vals)) + "\n);", body, count=1, flags=re.S))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=RUNS)
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    shutil.copytree(TEMPLATE / "common/constant", case / "constant")
    shutil.copytree(TEMPLATE / "common/system", case / "system")
    shutil.copytree(TEMPLATE / "common/0.orig", case / "0")
    for kind in (["nofan", "bare"] if a.run == "bare" else [a.run]):
        shutil.copytree(TEMPLATE / kind, case, dirs_exist_ok=True)
    cc, nx, ny, zones, fzones, bounds = mesh(case)
    fields(case, bounds, cc)
    (case / "system/decomposeParDict").write_text(
        "FoamFile {version 2.0; format ascii; class dictionary; object decomposeParDict;}\n"
        f"numberOfSubdomains {a.nprocs}; method scotch;\n")
    dx, dy = np.diff(x), np.diff(y)
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny,
              "min_dx": float(dx.min()), "min_dy": float(dy.min()),
              "max_dx": float(dx.max()), "max_dy": float(dy.max()),
              "ratio_x": float(max(np.max(dx[1:] / dx[:-1]), np.max(dx[:-1] / dx[1:]))),
              "ratio_y": float(max(np.max(dy[1:] / dy[:-1]), np.max(dy[:-1] / dy[1:]))),
              "zones": {n: len(z) for n, z in zones.items()},
              "faceZones": {n: len(f) for n, (f, flip) in fzones.items()},
              "patches": {n: count for n, count, st in bounds}}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    (case / "case.foam").touch()
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(zones["convector"]), "cells, fans",
          len(zones["fan_radiator"]), "and", len(zones["fan_ceiling"]), "cells, smallest",
          f'{report["min_dx"] * 1e3:.3f} x {report["min_dy"] * 1e3:.3f} mm')


if __name__ == "__main__":
    main()
