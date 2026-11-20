#!/usr/bin/env python3
"""Write one run of the bedroom: the vane held at 10 degrees down, or swinging 10-40 degrees.

    python3 scripts/make_case.py held|swing runs/<run> [--nprocs 8] [--mesh runs/mesh]

Copies the shared mesh (made by make_mesh.py, blockMesh, snappyHexMesh and unit_patches.py),
template/constant/ (g, thermophysicalProperties, turbulenceProperties, fvOptions with the
buoyancy source and the diagnostic wall-flux observer) and template/system/ (fvSchemes,
fvSolution, decomposeParDict, planesT0) and writes, from config/case.json:

  0/        U, T, p, p_rgh, k, omega, nut, alphat. The air at rest at 32 C, p and p_rgh in
            isothermal hydrostatic balance with 1e5 Pa at y = 1.21 m (from the mesh's cells.npz).
            The intake draws the unit's mass flow out of the room (flowRateOutletVelocity); the
            outlet blows it back in along the vane's direction (a codedFixedValue: the direction
            is 10 degrees below horizontal in the held run and a triangle wave 10-40-10 degrees,
            24 s a cycle, in the swing run; each outlet face carries flow in proportion to d . n
            where d . n > 0, scaled every evaluation to the mass flow at the patch's own
            density), at the intake's mean temperature plus Q/(m cp) with Q negative
            (outletMappedUniformInletHeatAddition). The walls, floor and ceiling are
            storedLayerWall80 (src/storedLayerWall80): 24 layers of gypsum behind the walls and
            ceiling and of wood under the floor, at 32 C, adiabatic backs. The unit's casing and
            the bed are adiabatic.
  system/functions   thermalBoundarySync (re-evaluates the intake's and the outlet's T and h at
            the end of every step; see the README), wallHeatFlux, the coded monitor metrics
            (scripts/monitor.C, every step, one row every 0.375 s into
            postProcessing/metrics/metrics.csv, the twelve cells of highest Courant number into
            courant.csv) and the planes (the section and plans at 0.10, 0.76, 1.60 and 2.30 m,
            T and U every 0.375 s).
  system/controlDict  0-180 s from rest, loading libstoredLayerWall80.so.

These are the solved runs' files byte for byte, but for the library's path in controlDict and
the wall condition's header in the monitor (the solved runs named both by their full paths on
our machine), and an abort function object the solved runs had and never used, which is left
out. The two runs differ only in the jet's and the monitor's `swinging` switch and the coded
objects' names.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


PLANES = (CASE / "template" / "system" / "planesT0").read_text()
PLANES = PLANES[PLANES.index("planes\n"):PLANES.rindex("}")]

JET = """type codedFixedValue;
 value uniform (0 0 0);
 name exactMassJetRUN;
 codeInclude
 #{
 #include "fvCFD.H"
 #include <cmath>
 namespace Foam { using std::floor; }
 #};
 code
 #{
 const scalar t = this->db().time().value();
 const scalar mdot = MASSFLOW;
 const scalar thTop = THTOP, thBot = THBOT;
 const scalar P = PERIOD;
 const bool swinging = SWINGING;
 scalar thDeg = thTop;
 if (swinging)
 {
 const scalar f = t/P - Foam::floor(t/P);
 const scalar tri = (f < 0.5) ? 2.0*f : 2.0*(1.0 - f);
 thDeg = thTop + (thBot - thTop)*tri;
 }
 const scalar th = thDeg*constant::mathematical::pi/180.0;
 const vector d(Foam::cos(th), -Foam::sin(th), 0);
 scalarField rf(this->patch().size(), 1.15);
 if(this->db().foundObject<volScalarField>("rho")) rf=this->patch().lookupPatchField<volScalarField,scalar>("rho");
 else if(this->db().foundObject<volScalarField>("p") && this->db().foundObject<volScalarField>("T"))
 {
 const auto& pp=this->patch().lookupPatchField<volScalarField,scalar>("p");
 const auto& tt=this->patch().lookupPatchField<volScalarField,scalar>("T");
 rf=pp/((8314.46261815324/MOLWEIGHT)*tt);
 }
 const vectorField nIn(-this->patch().Sf());
 const scalarField dn(max(d & nIn, scalar(0)));
 const scalar den = gSum(rf*dn);
 vectorField Uf(this->patch().size(), Zero);
 forAll(Uf, i) { if (dn[i] > 0) { Uf[i] = d*(mdot/max(den, SMALL)); } }
 this->operator==(Uf);
 #};
"""

SYNC = """thermalBoundarySync
 {
 type coded; libs (utilityFunctionObjects); name thermalBoundarySync80;
 executeControl timeStep; executeInterval 1; writeControl none;
 codeOptions #{ -I$(LIB_SRC)/thermophysicalModels/basic/lnInclude #};
 codeInclude
 #{
 #include "fvCFD.H"
 #include "basicThermo.H"
 #};
 codeExecute
 #{
 // The pressure correction can change intake T after the energy solve.
 // Synchronize the actual intake/outlet T and he boundary state, not just metrics.
 auto& th=const_cast<basicThermo&>(mesh().lookupObject<basicThermo>(basicThermo::dictName));
 auto& Tb=th.T().boundaryFieldRef();
 label in=mesh().boundaryMesh().findPatchID("intake");
 label out=mesh().boundaryMesh().findPatchID("outlet");
 Tb[in].evaluate();Tb[in].evaluate();
 Tb[out].evaluate();Tb[out].evaluate();
 for(label id:labelList({in,out})) th.he().boundaryFieldRef()[id]==th.he(th.p().boundaryField()[id],Tb[id],id);
 #};
 }
 wallHeatFlux
 {
 type wallHeatFlux; libs (fieldFunctionObjects); patches (unitSideWall farWall sideWall floor ceiling); executeControl timeStep; executeInterval 1; writeControl none; log false;
 }
"""

METRICS = """metrics {
 type coded; libs (utilityFunctionObjects); name metricsRUN;
 executeControl timeStep; executeInterval 1;
 codeOptions #{ -I$(LIB_SRC)/thermoTools/lnInclude -I$(LIB_SRC)/TurbulenceModels/compressible/lnInclude #};
 writeControl adjustableRunTime; writeInterval 0.375;
 codeInclude
 #{
 #include "fvCFD.H"
 #include <cmath>
 namespace Foam { using std::floor; }
 #include <fstream>
 #include <iomanip>
 #include <algorithm>
 #include <vector>
 #include "LAYERHEADER"
 #};
 codeExecute
 #{
 MONITOR
 #};
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("held", "swing"))
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

    T0, p0, yRef, mdot, Q = cfg["T0"], cfg["pRef"], cfg["yRef"], cfg["massFlow"], cfg["Q"]
    RT = (8314.46261815324 / cfg["molWeight"]) * T0
    lay, vane = cfg["layers"], cfg["vane"]
    swinging = "true" if run == "swing" else "false"

    def layer(w):
        m = lay["floor"] if w == "floor" else lay["walls"]
        return (f"type storedLayerWall80; kappaMethod fluidThermo; Tinit {T0:g}; Q 0; h 0; Ta 0; nLayers {lay['nLayers']}; "
                f"thickness {m['thickness']}; conductivity {m['conductivity']}; rhoCp {m['rhoCp']}; emissivity .9; "
                f"value uniform {T0:g};")
    adi = '"(unitWall|bed)"'
    allwall = '"(unitSideWall|farWall|sideWall|floor|ceiling|unitWall|bed)"'
    allp = '"(unitSideWall|farWall|sideWall|floor|ceiling|unitWall|bed|intake|outlet)"'
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    values = {"U": "(0 0 0)", "T": f"{T0:g}", "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    # the solved runs' coded objects were named after the run and their folder, runs/
    code = (JET.replace("RUN", run + "runs").replace("MASSFLOW", f"{mdot:g}")
            .replace("THTOP", repr(float(vane["top"]))).replace("THBOT", repr(float(vane["bottom"])))
            .replace("PERIOD", repr(float(vane["period"]))).replace("SWINGING", swinging)
            .replace("MOLWEIGHT", f"{cfg['molWeight']:g}"))

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
                  + bc("outlet", code))
        if n == "T":
            s += ("".join(bc(w, layer(w)) for w in ("unitSideWall", "farWall", "sideWall", "floor", "ceiling"))
                  + bc(adi, "type zeroGradient;")
                  + bc("intake", "type zeroGradient;")
                  + bc("outlet", f"type outletMappedUniformInletHeatAddition; outletPatch intake; Q constant {Q:g}; "
                                 f"TMin 250; TMax 400; value uniform {T0:g};"))
        if n == "p":
            s += bc(allp, f"type calculated; value uniform {p0:g};")
        if n == "p_rgh":
            s += bc(allp, "type fixedFluxPressure; value uniform 100013.52;")
        if n == "k":
            s += (bc(allwall, "type kLowReWallFunction; value uniform 1e-4;") + bc("intake", "type zeroGradient;")
                  + bc("outlet", "type turbulentIntensityKineticEnergyInlet; intensity 0.05; value uniform 0.01;"))
        if n == "omega":
            s += (bc(allwall, "type omegaWallFunction; value uniform 1;") + bc("intake", "type zeroGradient;")
                  + bc("outlet", "type turbulentMixingLengthFrequencyInlet; mixingLength 0.01; value uniform 1;"))
        if n == "nut":
            s += (bc(allwall, "type nutkWallFunction; value uniform 0;")
                  + bc('"(intake|outlet)"', "type calculated; value uniform 0;"))
        if n == "alphat":
            s += (bc(allwall, "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;")
                  + bc('"(intake|outlet)"', "type calculated; value uniform 0;"))
        s += "}\n"
        (c / "0" / n).write_text(s)

    mon = ((CASE / "scripts" / "monitor.C").read_text()
           .replace("PERIOD", repr(float(vane["period"]))).replace("SWINGING", swinging))
    header = (CASE / "src" / "storedLayerWall80" / "storedLayerWall80.H").resolve()
    functions = SYNC + METRICS.replace("RUN", run).replace("MONITOR", mon).replace("LAYERHEADER", str(header))
    functions += PLANES
    (c / "system" / "functions").write_text(functions)
    (c / "system" / "controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
 startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']:g};
 deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
 writeControl adjustableRunTime; writeInterval 30; purgeWrite 0;
 writeFormat binary; writePrecision 10; writeCompression off;
 timeFormat general; timePrecision 10; runTimeModifiable false;
 libs ("libstoredLayerWall80.so");
 functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(c)


if __name__ == "__main__":
    main()
