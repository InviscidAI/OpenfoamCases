#!/usr/bin/env python3
"""Write one run of the two-room house: the fan high in the doorway or low.

    python3 scripts/make_case.py high|low runs/<run> [--nprocs 8] [--mesh runs/mesh]

Copies the shared mesh (made by make_mesh.py, blockMesh, snappyHexMesh and house_patches.py) and
template/constant/ and template/system/ (fvSchemes, fvSolution, topoSetDict, decomposeParDict,
planesT0), and writes, from config/case.json:

  0/        U, T, p, p_rgh, k, omega, nut, alphat. The air at rest, 24 C in the stove room and
            14 C in the cold room (split at x = 4.04 m, the middle of the doorway's depth), p in
            hydrostatic balance with each room's temperature and 1e5 Pa at y = 1.02 m, p_rgh =
            p + rho g y (from the mesh's cells.npz). The walls held at each room's temperature,
            the doorway's reveal adiabatic, and the stove's and flue's faces given a uniform heat
            flux (externalWallHeatFluxTemperature, mode flux): 2000 W over the stove's 1.056 m2
            and 500 W over the flue's 0.4992 m2.
  constant/fvOptions  buoyancyTurbSource, and the fan: meanVelocityForce in fanHigh with Ubar
            +2.084 m/s (high, blowing into the cold room) or in fanLow with -2.027 m/s (low,
            blowing into the stove room). The other zone is plain air.
  system/functions   wallHeatFlux, the coded monitor metrics (scripts/monitor.C, one row every
            0.625 s into postProcessing/metrics/metrics.csv), the planes (the section and plans
            at ankle, head and ceiling height, T and U every 0.625 s) and the stove's and flue's
            face temperature, area mean and maximum.
  system/controlDict  0-190 s from rest.

These are the solved runs' files byte for byte, but for controlDict's endTime (190 here, 200 in
the solved runs, which an abort file stopped at their 190 s write) and that abort function object,
which is left out.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
GAS_R = 8314.46261815324 / 28.96


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


PLANES = (CASE / "template" / "system" / "planesT0").read_text()
PLANES = PLANES[PLANES.index("planes\n"):PLANES.rindex("}")]

METRICS = """wallHeatFlux { type wallHeatFlux; libs (fieldFunctionObjects); patches (stoveRoomWalls coldRoomWalls doorwayReveal stove flue); executeControl timeStep; executeInterval 1; writeControl none; log false; }
metrics { type coded; libs (utilityFunctionObjects); name metrics71;
 executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval 0.625;
 codeInclude #{
 #include "fvCFD.H"
 #include <fstream>
 #include <iomanip>
 #include <vector>
 #include <algorithm>
 #};
 codeWrite #{
"""

FACE_T = """{patch}T_{op}
{{
 type surfaceFieldValue; libs (fieldFunctionObjects);
 writeFields false; regionType patch; name {patch}; fields (T); operation {op};
 writeControl adjustableRunTime; writeInterval 0.625; log true;
}}
"""

WALLS = ("stoveRoomWalls", "coldRoomWalls", "doorwayReveal", "stove", "flue")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("high", "low"))
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
    t = CASE / "template"
    for f in sorted((t / "constant").iterdir()):
        shutil.copy(f, c / "constant" / f.name)
    shutil.copytree(t / "system", c / "system")
    d = c / "system" / "decomposeParDict"
    d.write_text(d.read_text().replace("numberOfSubdomains 8;", f"numberOfSubdomains {a.nprocs};"))
    (c / "0").mkdir()

    zone = "fanHigh" if run == "high" else "fanLow"
    (c / "constant" / "fvOptions").write_text(
        hdr("fvOptions") + "buoyancyTurb { type buoyancyTurbSource; selectionMode all; }\n"
        f"fanForce {{ type meanVelocityForce; selectionMode cellZone; cellZone {zone}; fields (U); "
        f"Ubar ({cfg['Ubar'][run]!r} 0 0); relaxation 1.0; }}\n")

    T0 = cfg["T0"]
    Tcell = np.where(C[:, 0] < T0["split"], T0["stoveRoom"], T0["coldRoom"])
    p0 = cfg["pRef"] * np.exp(-9.81 * (C[:, 1] - cfg["yRef"]) / (GAS_R * Tcell))
    rho0 = p0 / (GAS_R * Tcell)
    wallT = {"stoveRoomWalls": T0["stoveRoom"], "coldRoomWalls": T0["coldRoom"]}
    area = {p: cfg["patches"][p]["area"] for p in ("stove", "flue")}
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    values = {"U": "(0 0 0)", "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    for n in dims:
        s = hdr(n, "volVectorField" if n == "U" else "volScalarField") + f"dimensions [{dims[n]}];\n"
        if n in ("T", "p", "p_rgh"):
            v = {"T": Tcell, "p": p0, "p_rgh": p0 + rho0 * 9.81 * C[:, 1]}[n]
            s += "internalField nonuniform List<scalar>\n" + str(len(C)) + "\n(\n" + "\n".join(f"{x:.15g}" for x in v) + "\n);\n"
        else:
            s += f"internalField uniform {values[n]};\n"
        s += "boundaryField\n{\nsymmetry { type symmetry; }\n"
        for w in WALLS:
            if n == "U":
                b = "type noSlip;"
            elif n == "T":
                if w in wallT:
                    b = f"type fixedValue; value uniform {wallT[w]};"
                elif w == "doorwayReveal":
                    b = "type zeroGradient;"
                else:
                    b = (f"type externalWallHeatFluxTemperature; mode flux; q uniform {cfg['Q'][w] / area[w]:.10f}; "
                         f"kappaMethod fluidThermo; qr none; value uniform {T0['stoveRoom']};")
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
            s += w + " { " + b + " }\n"
        (c / "0" / n).write_text(s + "}\n")

    functions = METRICS + (CASE / "scripts" / "monitor.C").read_text() + "\n#};\n}\n" + PLANES + "\n"
    for patch in ("stove", "flue"):
        for op in ("areaAverage", "max"):
            functions += FACE_T.format(patch=patch, op=op)
    (c / "system" / "functions").write_text(functions)
    (c / "system" / "controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
 startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']:g};
 deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
 writeControl adjustableRunTime; writeInterval 10; purgeWrite 0;
 writeFormat binary; writePrecision 10; writeCompression on;
 timeFormat general; timePrecision 10; runTimeModifiable false;
 functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(c)


if __name__ == "__main__":
    main()
