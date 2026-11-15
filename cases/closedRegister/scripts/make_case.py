#!/usr/bin/env python3
"""Write one run of the house: every register open, or the spare room's closed.

    python3 scripts/make_case.py open|closed runs/<run> [--nprocs 8] [--mesh runs/mesh]

Copies the shared mesh (made by make_mesh.py, blockMesh, snappyHexMesh and house_patches.py) and
template/constant/ (g, thermophysicalProperties, turbulenceProperties, fvOptions) and
template/system/ (fvSchemes, fvSolution, decomposeParDict, planesT0), and writes, from
config/case.json:

  0/        U, T, p, p_rgh, k, omega, nut, alphat. The air at rest at 62 F (289.82 K), p in
            hydrostatic balance with 1e5 Pa at y = 0.5 m, p_rgh = p + rho g y (from the mesh's
            cells.npz). Each open register a flowRateInletVelocity of its mass flow at the supply
            temperature; the return grille a fixed pressure (prghPressure, 1e5 Pa) with
            inletOutlet T, k and omega. The floor, ceiling and walls storedLayerWall
            (src/storedLayerWall) with 24 stored layers, starting at 289.82 K; the windows the
            same condition with no layers and a film of 4.4 W/m2K to 266.48 K outside. In closed
            the spare room's register is a no-slip, adiabatic wall with wall functions, and its
            patch's type in constant/polyMesh/boundary is wall.
  system/functions   wallHeatFlux, the coded monitor (scripts/monitor.C, every step, one row
            every 0.625 s into postProcessing/metrics/metrics.csv, and the twelve cells of
            highest Courant number into courant.csv) and the planes (head, seated and ankle
            plans and three sections, T and U every 0.625 s).
  system/controlDict  0-300 s from rest.

These are the solved runs' files byte for byte, but for the library's path in controlDict and
planesT0 (the solved runs named the built library by its full path), the names of the wall
condition and of the two coded objects (the solved runs' carried a number of ours), and an abort
function object the solved runs had and never used, which is left out.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
GAS_R = 8314.46261815324 / 28.96
HEATS = ["floor", "ceiling", "walls", "windows"]


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


PLANES = (CASE / "template" / "system" / "planesT0").read_text()
PLANES = PLANES[PLANES.index("planes\n"):PLANES.rindex("}")]

METRICS = """wallHeatFlux { type wallHeatFlux; libs (fieldFunctionObjects); patches (floor ceiling walls windows); executeControl timeStep; executeInterval 1; writeControl none; log false; }
metrics { type coded; libs (utilityFunctionObjects); name houseMetrics;
 executeControl timeStep; executeInterval 1; writeControl none;
 codeInclude #{
 #include "fvCFD.H"
 #include <fstream>
 #include <iomanip>
 #include <vector>
 #include <algorithm>
 #};
 codeExecute #{
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("open", "closed"))
    ap.add_argument("dest")
    ap.add_argument("--nprocs", type=int, default=8)
    ap.add_argument("--mesh", default=str(CASE / "runs" / "mesh"))
    a = ap.parse_args()
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    run, mesh, c = a.run, Path(a.mesh), Path(a.dest)
    if not (mesh / "cells.npz").is_file():
        raise SystemExit(f"{mesh} has no finished mesh: Allrun builds it")
    if c.exists():
        raise SystemExit(f"{c} exists; ./Allclean or move it away first")
    C = np.load(mesh / "cells.npz")["C"]

    shutil.copytree(mesh / "constant" / "polyMesh", c / "constant" / "polyMesh")
    if run == "closed":
        p = c / "constant" / "polyMesh" / "boundary"
        p.write_text(re.sub(r"(register_spare\s*\{\s*type\s+)patch", r"\1wall", p.read_text()))
    t = CASE / "template"
    for f in sorted((t / "constant").iterdir()):
        shutil.copy(f, c / "constant" / f.name)
    shutil.copytree(t / "system", c / "system")
    d = c / "system" / "decomposeParDict"
    d.write_text(d.read_text().replace("numberOfSubdomains 8;", f"numberOfSubdomains {a.nprocs};"))
    (c / "0").mkdir()

    T0 = cfg["T0"]
    p0 = cfg["pRef"] * np.exp(-9.81 * (C[:, 1] - cfg["yRef"]) / (GAS_R * T0))
    rho0 = p0 / (GAS_R * T0)
    REG = list(cfg["registers"])
    flows = cfg["runs"][run]["massFlow"]
    Ts = cfg["runs"][run]["Tsupply"]
    W = cfg["walls"]
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    vals = {"U": "(0 0 0)", "T": f"{T0:g}", "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    for n in dims:
        s = hdr(n, "volVectorField" if n == "U" else "volScalarField") + f"dimensions [{dims[n]}];\n"
        if n in ("p", "p_rgh"):
            v = p0 if n == "p" else p0 + rho0 * 9.81 * C[:, 1]
            s += "internalField nonuniform List<scalar>\n" + str(len(C)) + "\n(\n" + "\n".join(f"{x:.15g}" for x in v) + "\n);\n"
        else:
            s += f"internalField uniform {vals[n]};\n"
        s += "boundaryField\n{\n"
        for w in HEATS + REG + ["return"]:
            inlet = w in REG and flows[REG.index(w)] > 0
            if n == "U":
                b = "type noSlip;"
            elif n == "T":
                b = "type zeroGradient;"
                if w in HEATS:
                    lw = W["floor"] if w == "floor" else W["walls"]
                    h, Ta, nl = (W["windows"]["h"], W["windows"]["Ta"], 0) if w == "windows" else (0, 0, W["nLayers"])
                    b = (f"type storedLayerWall; kappaMethod fluidThermo; Tinit {T0:g}; Q 0; h {h}; Ta {Ta}; nLayers {nl}; "
                         f"thickness {lw['thickness']}; conductivity {lw['conductivity']}; rhoCp {lw['rhoCp']}; emissivity 0.9; "
                         f"value uniform {T0:g};")
            elif n == "p":
                b = "type calculated; value uniform 100000;"
            elif n == "p_rgh":
                b = "type fixedFluxPressure; value uniform 100000;"
            elif n == "k":
                b = "type kLowReWallFunction; value uniform 1e-4;"
            elif n == "omega":
                b = "type omegaWallFunction; value uniform 1;"
            elif n == "nut":
                b = "type nutkWallFunction; value uniform 0;"
            else:
                b = "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;"
            if inlet:
                b = {"U": f"type flowRateInletVelocity; massFlowRate {flows[REG.index(w)]}; rho rho; rhoInlet 1.2; value uniform (0 1 0);",
                     "T": f"type fixedValue; value uniform {Ts};",
                     "k": "type turbulentIntensityKineticEnergyInlet; intensity 0.05; value uniform 0.01;",
                     "omega": "type turbulentMixingLengthFrequencyInlet; mixingLength 0.01; value uniform 10;"}.get(
                    n, b if n in ("p", "p_rgh") else "type calculated; value uniform 0;")
            if w == "return":
                b = {"U": "type pressureInletOutletVelocity; value uniform (0 0 0);",
                     "p_rgh": "type prghPressure; p uniform 100000; value uniform 100000;",
                     "T": f"type inletOutlet; inletValue uniform {T0:g}; value uniform {T0:g};",
                     "k": "type inletOutlet; inletValue uniform 0.0001; value uniform 0.0001;",
                     "omega": "type inletOutlet; inletValue uniform 1; value uniform 1;"}.get(
                    n, b if n == "p" else "type calculated; value uniform 0;")
            s += w + " { " + b + " }\n"
        (c / "0" / n).write_text(s + "}\n")

    (c / "system" / "functions").write_text(METRICS + (CASE / "scripts" / "monitor.C").read_text() + "\n#};\n}\n" + PLANES)
    (c / "system" / "controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
 libs ("libstoredLayerWall.so");
 startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']:g};
 deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
 writeControl adjustableRunTime; writeInterval 30; purgeWrite 0;
 writeFormat binary; writePrecision 10; writeCompression on;
 timeFormat general; timePrecision 10; runTimeModifiable false;
 functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(c)


if __name__ == "__main__":
    main()
