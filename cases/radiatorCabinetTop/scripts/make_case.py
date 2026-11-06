"""Write one run of the radiator cabinet case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py bare|solid|perforated <runDir> [--nprocs N]

The mesh is written directly as a polyMesh, one cell thick (z = 0 to 1 m), from a Cartesian
grid of 6 mm cells over the radiator and the cabinet, widening into the room, over the section's
5.5 x 2.9 m. The writer is radiatorCover's (../radiatorCover/scripts/make_case.py) with this
room's grid, its radiator and its cabinet; the study that solved the runs edited radiatorCover's
writer in place at run time, and those edits are written out here.

- The window wall is x = 0: the glass from y = 0.852 m (the 6 mm line nearest 0.85) to 2.500 m,
  outerWall below and above it. The room's far end at x = 5.5 m is innerWall.
- The radiator's front and rear iron columns (x = 0.060-0.120 and 0.228-0.288 m,
  y = 0.078-0.660 m) are left out of the mesh, their faces the patch radiatorPanel; the middle
  between them (x = 0.120-0.228 m, same y) is the cellZone convector.
- In solid and perforated the cabinet's front (x = 0.330 m, y < 0.756 m) and top (y = 0.756 m,
  x < 0.330 m) are internal faces split into pairs of coincident wall patches (<part>A, the side
  the face's owner cell is on, and <part>B) that 0/T makes 1-D conducting thermal baffles:
  bottomRail (y < 0.084), grille (between the front's 11 open strips, 24 mm at a 60 mm pitch from
  y = 0.084 m), topRail (y = 0.708-0.756) and top. In perforated the top has 5 open strips,
  24 mm at a 60 mm pitch from x = 0.036 m. bare has no cabinet. All three share the grid and the
  cells, 83,068.

The files under template/common/ and template/<cabinet|bare>/ are copied in unchanged. This
script writes 0/T (every wall but the iron a radLayerWall, the cabinet's parts thermal baffles),
0/IDefault, 0/G and 0/qr at the black-body values of 16 C, the hydrostatic 0/p and 0/p_rgh at
rest, system/decomposeParDict, and initial.json, the air's and the convector zone's mass and
energy at t = 0, which scripts/extract_results.py reads.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"

TAMB = 289.15     # 16 C, the air and every wall layer at t = 0
TIRON = 374.82    # 215 F, the iron and the convector zone from t = 0
R = 8314.46261815324 / 28.96
CV = 1005 - R
SIGMA = 5.670374419e-8


def H(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def graded(keys, size):
    """Lines through every key, with cells close to size(t) long between them (rounded up)."""
    out = []
    for a, b in zip(keys[:-1], keys[1:]):
        t = np.linspace(a, b, 2001)
        w = 1 / size(t)
        s = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(t))]
        n = int(np.ceil(s[-1] - 1e-9))
        out.extend(np.interp(np.linspace(0, s[-1], n + 1), s, t)[:-1])
    return np.r_[out, keys[-1]]


# ---- the grid ----------------------------------------------------------------------------
# x, from the window wall into the room: 6 mm to 0.45 m (the iron, the cabinet's front at 0.330
# and its strips, and the lateral flow cut at 0.450), widening to 30 mm at 1.2 m, 30 mm to 5.2 m,
# 12 mm at the far end.
x = np.round(np.r_[np.linspace(0, .420, 71)[:-1],
                   graded([.420, .450, 1.2, 5.2, 5.5],
                          lambda t: np.interp(t, [.420, .450, 1.2, 5.2, 5.5], [.006, .006, .030, .030, .012]))], 10)
# y, up from the floor: 6 mm to 0.90 m (the iron, the cabinet's top at 0.756, the line above it
# at 0.900), widening to 15 mm at 1.3 m, 15 mm past the glass's top (2.500) to 2.75 m, 6 mm under
# the ceiling at 2.9 m.
y = np.round(np.r_[np.linspace(0, .900, 151)[:-1],
                   graded([.900, 1.3, 2.5, 2.75, 2.84, 2.9],
                          lambda t: np.interp(t, [.900, 1.3, 2.75, 2.84, 2.9], [.006, .015, .015, .006, .006]))], 10)

FRONT_STRIPS = [(.084 + .060 * k, .108 + .060 * k) for k in range(11)]
TOP_STRIPS = [(.036 + .060 * k, .060 + .060 * k) for k in range(5)]
PARTS = ["top", "topRail", "bottomRail", "grille"]


def iron(xc, yc):
    """The front and rear iron columns: no air in these cells."""
    return ((.060 < xc < .120) or (.228 < xc < .288)) and .078 < yc < .660


def baffle(i, j, axis, run):
    """The cabinet part on the face on the +x (axis 0) or +y (axis 1) side of cell (i, j)."""
    if run == "bare":
        return None
    xc, yc = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
    if axis == 0 and abs(x[i + 1] - .330) < 1e-8:  # the front
        if 0 < yc < .084:
            return "bottomRail"
        if .708 < yc < .756:
            return "topRail"
        if .084 < yc < .708 and not any(a < yc < b for a, b in FRONT_STRIPS):
            return "grille"
    if axis == 1 and abs(y[j + 1] - .756) < 1e-8 and xc < .330:  # the top
        if run == "solid" or not any(a < xc < b for a, b in TOP_STRIPS):
            return "top"
    return None


def mesh(run, case):
    nx, ny = len(x) - 1, len(y) - 1
    cc, ids = [], {}
    for j in range(ny):
        for i in range(nx):
            xc, yc = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
            if iron(xc, yc):
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
        for part in PARTS:
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
                    name = "glass" if .850 < (y[j] + y[j + 1]) / 2 < 2.500 else "outerWall"
                elif n[0] >= nx:
                    name = "innerWall"
                elif n[1] < 0:
                    name = "floor"
                elif n[1] >= ny:
                    name = "ceiling"
                else:  # an iron cell next door
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
    conv = np.where((cc[:, 0] > .120) & (cc[:, 0] < .228) & (cc[:, 1] > .078) & (cc[:, 1] < .660))[0]
    (pm / "cellZones").write_text(H("cellZones", "regIOobject") + "1\n(\nconvector\n{\n type cellZone;\n cellLabels List<label>\n"
                                  + str(len(conv)) + "\n(\n" + "\n".join(map(str, conv)) + "\n);\n}\n)\n")
    for name, cls in [("faceZones", "regIOobject"), ("pointZones", "regIOobject")]:
        (pm / name).write_text(H(name, cls) + "0\n(\n)\n")
    return cc, nx, ny, conv, bounds


# Every wall but the iron is a radLayerWall (src/radLayerWall): convection and the radiation it
# absorbs on the room side, and behind it a 1-D layer of 24 slices with its heat capacity and an
# adiabatic back, all at 16 C at t = 0. The glass has no layer: a film of 23.577 W/m2K to 0 C
# outside (single glazing, U = 5.8 less the inside film's 0.13 m2K/W). Thickness m,
# conductivity W/m K, rho*cp J/m3 K.
FLOOR = (.019, .106, 1237411.2)     # 19 mm wood
GYPSUM = (.0127, .1587, 723991.)    # 12.7 mm gypsum board: ceiling and walls


def fields(case, bounds, cc, conv):
    txt = H("T", "volScalarField") + "dimensions [0 0 0 1 0 0 0];\ninternalField uniform 289.15;\nboundaryField\n{\n"
    for patch, n, start in bounds:
        if patch == "frontAndBack":
            txt += "frontAndBack {type empty;}\n"
            continue
        if patch == "radiatorPanel":
            txt += f"radiatorPanel {{type fixedValue; value uniform {TIRON};}}\n"
            continue
        if patch.endswith(("A", "B")):
            # the sheet: 1.2 mm, conductivity 0.5 W/m K (not steel's 50, so as not to tie the two
            # explicitly coupled faces stiffly; 417 W/m2K across it is still far above the films);
            # rho and Cp are required by the thermophysical type but a thermalBaffle1D stores no heat
            other = patch[:-1] + ("B" if patch.endswith("A") else "A")
            txt += f'''{patch}
{{
 type compressible::thermalBaffle1D<hConstSolidThermoPhysics>;
 sampleMode nearestPatchFace; samplePatch {other}; sampleRegion region0;
 offset (0 0 0); qr qr; qrRelaxation 1; qrNbr qr;
 thickness uniform 0.0012;
 specie {{ molWeight 100; }}
 transport {{ kappa 0.5; }}
 thermodynamics {{ Hf 0; Cp 1000; }}
 equationOfState {{ rho 700; }}
 value uniform 289.15;
}}
'''
            continue
        h, ta, eps, nl = 0, 0, .9, 24
        th, k, rc = FLOOR if patch == "floor" else GYPSUM
        if patch == "glass":
            h, ta, eps, nl = 23.577, 273.15, .84, 0
        txt += (f"{patch}\n{{type radLayerWall; kappaMethod fluidThermo; Q 0; h {h}; Ta {ta}; emissivity {eps}; "
                f"Tinit 289.15; nLayers {nl}; thickness {th}; conductivity {k}; rhoCp {rc}; value uniform 289.15;}}\n")
    (case / "0/T").write_text(txt + "}\n")
    # the radiation at t = 0: black-body intensity, incident radiation and no net flux at 16 C
    I = SIGMA * TAMB ** 4 / np.pi
    (case / "0/IDefault").write_text(H("IDefault", "volScalarField") + f'dimensions [1 0 -3 0 0 0 0]; internalField uniform {I}; boundaryField {{ frontAndBack {{type empty;}} ".*" {{type greyDiffusiveRadiation; value uniform {I};}} }}\n')
    for name, value in [("G", 4 * SIGMA * TAMB ** 4), ("qr", 0)]:
        (case / "0" / name).write_text("FoamFile {version 2.0;format ascii;class volScalarField;object " + name + ";}\n"
                                       "dimensions [1 0 -3 0 0 0 0];\ninternalField uniform " + str(value) + ";\n"
                                       'boundaryField { frontAndBack {type empty;} ".*" {type calculated;value uniform ' + str(value) + ";} }\n")
    # the air at rest in hydrostatic balance at 16 C, 1e5 Pa at the pressure reference (2.75, 1.45)
    p = 1e5 * np.exp(-9.81 * (cc[:, 1] - 1.45) / (R * TAMB))
    gh = -9.81 * cc[:, 1]
    rho = p / (R * np.full(len(cc), TAMB))
    for name, vals in [("p", p), ("p_rgh", p - rho * gh)]:
        f = case / "0" / name
        body = f.read_text()
        assert "internalField   uniform 1e5;" in body, name
        f.write_text(body.replace("internalField   uniform 1e5;", "internalField nonuniform List<scalar>\n"
                                  + str(len(vals)) + "\n(\n" + "\n".join(map(str, vals)) + "\n);"))
    # the start's mass and energy, for the radiator's heat in extract_results.py
    vol = np.diff(x)[np.searchsorted(x, cc[:, 0]) - 1] * np.diff(y)[np.searchsorted(y, cc[:, 1]) - 1]
    init = dict(initialMass_kg=float((rho * vol).sum()), initialZoneMass_kg=float((rho[conv] * vol[conv]).sum()),
                initialZoneU_J=float((CV / R * p[conv] * vol[conv]).sum()), initialAirU_J=float((CV / R * p * vol).sum()),
                initial_zone_heat_J=0.0)
    (case / "initial.json").write_text(json.dumps(init, indent=2))
    return vol


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=["bare", "solid", "perforated"])
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=5)
    a = ap.parse_args()
    case = Path(a.dir)
    if case.exists():
        shutil.rmtree(case)
    kind = "bare" if a.run == "bare" else "cabinet"
    shutil.copytree(TEMPLATE / "common/constant", case / "constant")
    shutil.copytree(TEMPLATE / "common/system", case / "system")
    shutil.copytree(TEMPLATE / "common/0.orig", case / "0")
    shutil.copytree(TEMPLATE / kind / "system", case / "system", dirs_exist_ok=True)
    cc, nx, ny, conv, bounds = mesh(a.run, case)
    vol = fields(case, bounds, cc, conv)
    (case / "system/decomposeParDict").write_text(H("decomposeParDict") + f"numberOfSubdomains {a.nprocs}; method scotch;\n")
    dx, dy = np.diff(x), np.diff(y)
    report = {"run": a.run, "cells": len(cc), "nx": nx, "ny": ny, "convectorCells": len(conv),
              "convectorVolume_m3": float(vol[conv].sum()),
              "min_dx": float(dx.min()), "min_dy": float(dy.min()), "max_dx": float(dx.max()), "max_dy": float(dy.max()),
              "patches": {n: count for n, count, st in bounds}}
    (case / "mesh_geometry.json").write_text(json.dumps(report, indent=2))
    (case / "case.foam").touch()
    print(a.run, report["cells"], "cells,", nx, "x", ny, "grid, convector", len(conv), "cells, smallest",
          f'{report["min_dx"] * 1e3:.3f} x {report["min_dy"] * 1e3:.4f} mm')


if __name__ == "__main__":
    main()
