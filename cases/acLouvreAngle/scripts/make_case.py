#!/usr/bin/env python3
"""Write one run of the air conditioner's room: the vane up or the vane down.

    python3 scripts/make_case.py up|down runs/<run> [--nprocs 8] [--mesh runs/mesh]

Copies the shared mesh (made by make_mesh.py, blockMesh, snappyHexMesh and unit_patches.py)
and makes the slot the run does not use a wall: slotDown in the up run, slotUp in the down
run. Copies template/constant/ and template/system/ (fvSchemes, fvSolution, topoSetDict,
decomposeParDict, planesT0) and writes, from config/case.json:

  0/        U, T, p, p_rgh, k, omega, nut, alphat. The air at rest at 30 C, p and p_rgh in
            isothermal hydrostatic balance with 1e5 Pa at y = 1.2 m (from the mesh's cells.npz).
            The intake draws the unit's mass flow out of the room (flowRateOutletVelocity); the
            active slot blows it back in along the vane's direction (a codedFixedValue that scales
            the velocity to the mass flow at the patch's own density every evaluation), at the
            intake's mean temperature plus Q/(m cp) (outletMappedUniformInletHeatAddition).
  system/functions   wallHeatFlux, the coded monitor metrics (scripts/monitor.C, one row every
            0.375 s into postProcessing/metrics/metrics.csv) and the planes (section, ankle, head
            and ceiling, T and U every 0.375 s).
  system/controlDict  0-180 s from rest.

These are the solved runs' files byte for byte, but for two things the solved runs changed for
their restart at 30 s (README.md, "How the case got here"): controlDict's startFrom and the
fvSolution's pRefValue, and an offset added to the monitor's clock column.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


PLANES = """planes
{
 type surfaces; libs (sampling);
 writeControl adjustableRunTime; writeInterval 0.375;
 surfaceFormat vtk;
 formatOptions { vtk { format ascii; } }
 interpolate true; fields (T U);
 surfaces
 {
 section { type patch; patches (symmetry); interpolate true; }
 ankle { type cuttingPlane; point (0 0.10 0); normal (0 1 0); interpolate true; }
 head { type cuttingPlane; point (0 1.10 0); normal (0 1 0); interpolate true; }
 ceiling { type cuttingPlane; point (0 2.30 0); normal (0 1 0); interpolate true; }
 }
}
"""

JET = """type codedFixedValue;
 value uniform (0 0 0);
 name exactMassJetRUN;
 codeInclude #{ #include "fvCFD.H" #};
 code
 #{
 const vector d(DIRECTION);
 scalarField rf(this->patch().size(),1.15);
 if(this->db().foundObject<volScalarField>("rho")) rf=this->patch().lookupPatchField<volScalarField,scalar>("rho");
 else if(this->db().foundObject<volScalarField>("p") && this->db().foundObject<volScalarField>("T"))
 {
 const auto& pp=this->patch().lookupPatchField<volScalarField,scalar>("p");
 const auto& tt=this->patch().lookupPatchField<volScalarField,scalar>("T");
 rf=pp/((8314.46261815324/MOLWEIGHT)*tt);
 }
 scalar den=gSum(rf*(d & (-this->patch().Sf())));
 this->operator==(d*(MASSFLOW/max(den,SMALL)));
 #};
"""

METRICS = """metrics {
 type coded; libs (utilityFunctionObjects); name metricsRUN;
 executeControl timeStep; executeInterval 1;
 writeControl adjustableRunTime; writeInterval 0.375;
 codeInclude
 #{
 #include "fvCFD.H"
 #include <fstream>
 #include <iomanip>
 #};
 codeWrite
 #{
 MONITOR
 #};
}
"""

# the active slot's outward normal and the cells of the first 4 cm outside it, over which the
# monitor measures the jet's direction
NEAR = {
    "up": ("1,0,0", "c.x()>.24&&c.x()<.28&&c.y()>=2&&c.y()<=2.06&&c.z()<=.30"),
    "down": ("0,-1,0", "c.y()>1.96&&c.y()<2&&c.x()>=.16&&c.x()<=.24&&c.z()<=.26"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("up", "down"))
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

    active = "slotUp" if run == "up" else "slotDown"
    inactive = "slotDown" if run == "up" else "slotUp"
    b = (c / "constant/polyMesh/boundary").read_text()
    b = re.sub(r"(" + inactive + r"\s*\{\s*type\s+)patch;", r"\1wall;", b)
    (c / "constant/polyMesh/boundary").write_text(b)

    direction = cfg["direction"][run]
    T0, p0, yRef, mdot, Q = cfg["T0"], cfg["pRef"], cfg["yRef"], cfg["massFlow"], cfg["Q"]
    RT = (8314.46261815324 / cfg["molWeight"]) * T0
    wall = '"(unitSideWall|farWall|sideWall|floor|ceiling)"'
    adi = '"(unitWall|sofa|' + inactive + ')"'
    allwall = '"(unitSideWall|farWall|sideWall|floor|ceiling|unitWall|sofa|' + inactive + ')"'
    allp = '"(unitSideWall|farWall|sideWall|floor|ceiling|unitWall|sofa|intake|slotUp|slotDown)"'
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    values = {"U": "(0 0 0)", "T": f"{T0:g}", "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    code = (JET.replace("RUN", run).replace("DIRECTION", direction.replace(" ", ","))
            .replace("MOLWEIGHT", f"{cfg['molWeight']:g}").replace("MASSFLOW", f"{mdot:g}"))

    def bc(p, b):
        return p + " { " + b + " }\n"

    for n in dims:
        cls = "volVectorField" if n == "U" else "volScalarField"
        s = hdr(n, cls) + f"dimensions [{dims[n]}];\n"
        if n in ("p", "p_rgh"):
            rho = p0 * np.exp(-9.81 * (C[:, 1] - yRef) / RT) / RT
            vals = rho * RT + (rho * 9.81 * C[:, 1] if n == "p_rgh" else 0)
            s += "internalField nonuniform List<scalar>\n" + str(len(C)) + "\n(\n" + "\n".join(f"{v:.12g}" for v in vals) + "\n);\n"
        else:
            s += f"internalField uniform {values[n]};\n"
        s += "boundaryField\n{\nsymmetry { type symmetry; }\n"
        if n == "U":
            s += (bc(allwall, "type noSlip;")
                  + bc("intake", f"type flowRateOutletVelocity; massFlowRate constant {mdot:g}; rho rho; value uniform (0 0 0);")
                  + bc(active, code))
        if n == "T":
            s += (bc(wall, f"type fixedValue; value uniform {T0:g};") + bc(adi, "type zeroGradient;")
                  + bc("intake", "type zeroGradient;")
                  + bc(active, f"type outletMappedUniformInletHeatAddition; outletPatch intake; Q constant {Q:g}; "
                               f"TMin 250; TMax 400; value uniform {T0:g};"))
        if n == "p":
            s += bc(allp, f"type calculated; value uniform {p0:g};")
        if n == "p_rgh":
            s += bc(allp, "type fixedFluxPressure; value uniform 100013.52;")
        if n == "k":
            s += (bc(allwall, "type kLowReWallFunction; value uniform 1e-4;") + bc("intake", "type zeroGradient;")
                  + bc(active, "type turbulentIntensityKineticEnergyInlet; intensity 0.05; value uniform 0.01;"))
        if n == "omega":
            s += (bc(allwall, "type omegaWallFunction; value uniform 1;") + bc("intake", "type zeroGradient;")
                  + bc(active, "type turbulentMixingLengthFrequencyInlet; mixingLength 0.01; value uniform 1;"))
        if n == "nut":
            s += (bc(allwall, "type nutkWallFunction; value uniform 0;")
                  + bc('"(intake|' + active + ')"', "type calculated; value uniform 0;"))
        if n == "alphat":
            s += (bc(allwall, "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;")
                  + bc('"(intake|' + active + ')"', "type calculated; value uniform 0;"))
        s += "}\n"
        (c / "0" / n).write_text(s)

    normal, near = NEAR[run]
    mon = (CASE / "scripts" / "monitor.C").read_text().replace("SLOT", active).replace("NORMAL", normal).replace("NEAR", near)
    functions = """wallHeatFlux
 {
 type wallHeatFlux; libs (fieldFunctionObjects); patches (unitSideWall farWall sideWall floor ceiling); executeControl timeStep; executeInterval 1; writeControl none; log false;
 }
"""
    functions += METRICS.replace("RUN", run).replace("MONITOR", mon)
    functions += PLANES
    (c / "system" / "functions").write_text(functions)
    (c / "system" / "controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
 startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']:g};
 deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
 writeControl adjustableRunTime; writeInterval 30; purgeWrite 0;
 writeFormat binary; writePrecision 10; writeCompression off;
 timeFormat general; timePrecision 10; runTimeModifiable false;
 functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(c)


if __name__ == "__main__":
    main()
