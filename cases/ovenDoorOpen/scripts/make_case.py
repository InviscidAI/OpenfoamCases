#!/usr/bin/env python3
"""Write one run of the half kitchen: the oven's door down (open) or kept shut.

    python3 scripts/make_case.py open|shut runs/<run> [--nprocs 8] [--mesh runs/mesh-<run>]

Copies the run's mesh (made by make_mesh.py, blockMesh, snappyHexMesh and kitchen_patches.py) and
template/constant/ (g, thermophysicalProperties, turbulenceProperties, fvOptions) and
template/system/ (fvSchemes, fvSolution, decomposeParDict, planesT0), and writes, from
config/case.json:

  0/        U, T, p, p_rgh, k, omega, nut, alphat. The air at rest at 20 C (293.15 K), in open
            the cavity's air at 325 F (435.93 K), p in hydrostatic balance with 293.15 K air and
            1e5 Pa at y = 1.2 m, p_rgh = p + rho g y with each cell's own density (from the mesh's
            cells.npz). The walls, the ceiling and the floor storedLayerWall73 (src/storedLayerWall73)
            with 24 stored layers, starting at 293.15 K. In open the liner the same condition
            with two layers of steel, 6.5 kg on the liner's meshed area, starting at 435.93 K, and
            the door, the cabinets, the range's front and its cooktop adiabatic. In shut the
            range's front and cooktop one even heat flux, 118.5 W over their meshed area
            (externalWallHeatFluxTemperature, mode flux), and the cabinets adiabatic.
  system/fvSolution   the pressure reference at the cell centre nearest (1.2, 1.7, 2.4), with the
            starting pressure there (the template's are the solved runs', and this checks them).
  system/functions    wallHeatFlux, the coded monitor (scripts/monitor.C, run at every step, one
            row every 0.625 s into postProcessing/metrics/metrics.csv and the twelve cells of
            highest Courant number into courant.csv; it also commits the stored layers' final
            state after every step) and the planes (the section, which is the symmetry plane,
            and a plan at standing head height, 1.60 m, T and U every 0.625 s).
  system/controlDict  0-300 s from rest.

These are the solved runs' files byte for byte, but for the library's path in controlDict,
planesT0 and the monitor's compile options (the solved runs named the built library by its full
path), and an abort function object the solved runs had and never used, which is left out. The
constant/fvOptions' scalarCodedSource is a do-nothing source that keeps the wall heat flux the
energy equation used, before the turbulence model updates alphat, for the monitor.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
ZONES = ("mouth", "mouthUpper", "mouthLower", "symmetry", "summary")


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


PLANES = (CASE / "template" / "system" / "planesT0").read_text()
PLANES = PLANES[PLANES.index("planes\n"):PLANES.rindex("}")]

METRICS = """wallHeatFlux { type wallHeatFlux; libs (fieldFunctionObjects); patches (liner door rangeFront cooktop walls ceiling floor cabinets); executeControl timeStep; executeInterval 1; writeControl none; log false; }
metrics { type coded; libs (utilityFunctionObjects); name metrics73;
 executeControl timeStep; executeInterval 1; writeControl none;
 codeOptions #{ -I@SRC@ -I$(LIB_SRC)/thermoTools/lnInclude -I$(LIB_SRC)/meshTools/lnInclude #};
 codeLibs #{ -L$(FOAM_USER_LIBBIN) -lstoredLayerWall73 -lthermoTools #};
 codeInclude #{
 #include "fvCFD.H"
 #include "storedLayerWall73.H"
 #include <fstream>
 #include <iomanip>
 #include <vector>
 #include <algorithm>
 #};
 codeExecute #{
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("open", "shut"))
    ap.add_argument("dest")
    ap.add_argument("--nprocs", type=int, default=8)
    ap.add_argument("--mesh")
    a = ap.parse_args()
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    run, c = a.run, Path(a.dest)
    mesh = Path(a.mesh) if a.mesh else CASE / "runs" / f"mesh-{run}"
    if not (mesh / "cells.npz").is_file():
        raise SystemExit(f"{mesh} has no finished mesh: Allrun builds it")
    if c.exists():
        raise SystemExit(f"{c} exists; ./Allclean or move it away first")
    C = np.load(mesh / "cells.npz")["C"]
    rep = json.loads((mesh / "patches.json").read_text())
    walls = [n for n in rep if n not in ZONES]

    shutil.copytree(mesh / "constant" / "polyMesh", c / "constant" / "polyMesh")
    t = CASE / "template"
    for f in sorted((t / "constant").iterdir()):
        shutil.copy(f, c / "constant" / f.name)
    shutil.copytree(t / "system", c / "system")
    d = c / "system" / "decomposeParDict"
    d.write_text(d.read_text().replace("numberOfSubdomains 8;", f"numberOfSubdomains {a.nprocs};"))
    (c / "0").mkdir()

    T0 = cfg["T0"]
    gasR = 8314.46261815324 / cfg["molWeight"]
    p0 = cfg["pRef"] * np.exp(-9.81 * (C[:, 1] - cfg["yRef"]) / (gasR * T0))
    Tc = np.full(len(C), T0)
    if run == "open":
        b = cfg["cavity"]
        Tc[(C[:, 0] < b[3]) & (C[:, 1] > b[1]) & (C[:, 1] < b[4]) & (C[:, 2] < b[5])] = cfg["liner"]["Tinit"]
    rho0 = p0 / (gasR * Tc)

    # The requested reference point lies on cell faces: the nearest cell centre is used.
    cell = int(np.argmin(np.sum((C - np.array(cfg["pRefRequested"])) ** 2, axis=1)))
    point, pRef = C[cell], p0[cell]
    f = c / "system" / "fvSolution"
    s = f.read_text()
    s = re.sub(r"pRefPoint\s*\([^;]+;", "pRefPoint (" + " ".join(f"{v:.12g}" for v in point) + ");", s)
    s = re.sub(r"pRefValue\s*[^;]+;", f"pRefValue {pRef:.16g};", s)
    f.write_text(s)

    lin = cfg["liner"]
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    values = {"U": "(0 0 0)", "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    for n in dims:
        s = hdr(n, "volVectorField" if n == "U" else "volScalarField") + f"dimensions [{dims[n]}];\n"
        if n in ("T", "p", "p_rgh"):
            v = {"T": Tc, "p": p0, "p_rgh": p0 + rho0 * 9.81 * C[:, 1]}[n]
            s += "internalField nonuniform List<scalar>\n" + str(len(C)) + "\n(\n" + "\n".join(f"{x:.15g}" for x in v) + "\n);\n"
        else:
            s += f"internalField uniform {values[n]};\n"
        s += "boundaryField\n{\nsymmetry { type symmetry; }\n"
        for w in walls:
            if n == "U":
                bc = "type noSlip;"
            elif n == "T":
                bc = "type zeroGradient;"
                if w in cfg["layers"] or w == "liner":
                    if w == "liner":
                        N, th, k, rc, ti = (lin["nLayers"], lin["mass"] / (lin["rho"] * rep[w]["area"]), lin["k"],
                                            lin["rho"] * lin["cp"], lin["Tinit"])
                    else:
                        L = cfg["layers"][w]
                        N, th, k, rc, ti = L["nLayers"], L["thickness"], L["k"], L["rhoCp"], T0
                    bc = (f"type storedLayerWall73; kappaMethod fluidThermo; Tinit {ti}; Q 0; h 0; Ta 0; nLayers {N}; "
                          f"thickness {th:.16g}; conductivity {k}; rhoCp {rc}; emissivity 0.9; value uniform {ti};")
                if run == "shut" and w in ("rangeFront", "cooktop"):
                    q = cfg["shutQ"] / (rep["rangeFront"]["area"] + rep["cooktop"]["area"])
                    bc = f"type externalWallHeatFluxTemperature; mode flux; q uniform {q:.16g}; kappaMethod fluidThermo; value uniform {T0};"
            elif n == "p":
                bc = "type calculated; value uniform 100000;"
            elif n == "p_rgh":
                bc = "type fixedFluxPressure; value uniform 100000;"
            elif n == "k":
                bc = "type kLowReWallFunction; value uniform 1e-4;"
            elif n == "omega":
                bc = "type omegaWallFunction; value uniform 1;"
            elif n == "nut":
                bc = "type nutkWallFunction; value uniform 0;"
            else:
                bc = "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;"
            s += w + " { " + bc + " }\n"
        (c / "0" / n).write_text(s + "}\n")

    functions = (METRICS.replace("@SRC@", str(CASE / "src" / "storedLayerWall73"))
                 + (CASE / "scripts" / "monitor.C").read_text() + "\n#};\n}\n" + PLANES)
    (c / "system" / "functions").write_text(functions)
    (c / "system" / "controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
 libs ("libstoredLayerWall73.so");
 startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']:g};
 deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
 writeControl adjustableRunTime; writeInterval 30; purgeWrite 0;
 writeFormat binary; writePrecision 10; writeCompression on;
 timeFormat general; timePrecision 10; runTimeModifiable false;
 functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(c, "reference cell", cell, "at", point, "pRefValue", f"{pRef:.16g}")


if __name__ == "__main__":
    main()
