#!/usr/bin/env python3
"""Write one run of the half living room from the mesh, template/ and the scripts' code.

    python3 scripts/make_case.py furnace|heatPump runs/<run> --mesh runs/mesh [--nprocs 4]

furnace   0.02830 kg/s at 32 K above the return, on 0-438 s and 744-1182 s, off 438-744 s and
          1182-1488 s, each switch a 2 s linear ramp of the flow; the return's backflow at the
          return's own outward flux-weighted mean temperature (src/returnMeanTemperature).
heatPump  0.03555 kg/s at 15 K above the return from t = 0, after a 2 s ramp; the return an
          inletOutlet at 292.04 K, through which no air came back in the solved run.

Writes 0/, constant/ and system/ as the solved runs had them. constant/ is template/constant/
(subject 74's air at Tref 292.04 K, k-omega SST, buoyancyTurbSource and the energy-flux observer
in fvOptions) and system/fvSchemes and fvSolution are template/system/'s. 0/ starts the air at rest
at 292.04 K (66 F), hydrostatic cell by cell, p = 1e5 exp(-9.81 y / (287.1 x 292.04)), with p_rgh
= p + rho g y. The register's temperature is a codedFixedValue (scripts/supply.C), its flow a
flowRateInletVelocity table; every wall is radLayerWall (src/radLayerWall85). The monitor
(scripts/monitor.C) is a coded function object compiled when the solve starts; the planes are
template/system/planes. The solved runs also carried an abort function object, which is left out.
"""
import argparse
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
T0 = 292.04
T_OUT = 270.35
GAS_R = 8314.46261815324 / 28.96
PATCHES = ["outerWall", "innerWall", "floor", "ceiling", "sideWall", "symmetry", "sofa", "register", "window", "return"]
WALLS = [p for p in PATCHES if p not in ("register", "return", "symmetry")]
RUNS = {
    # mass flow kg/s (half room), rise K, furnace schedule
    "furnace": dict(flow=0.02830, rise=32, furnace=True),
    "heatPump": dict(flow=0.03555, rise=15, furnace=False),
}
LIBS = {"furnace": '"libwall85.so" "libreturn85.so"', "heatPump": '"libwall85.so"'}


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def code(name):
    text = (CASE / "scripts" / name).read_text()
    if text.startswith("/*"):
        text = text[text.index("*/") + 2:].lstrip("\n")
    return text


def wall_T(w):
    thickness, k, rho_cp = (0.019, 0.106, 1237411) if w == "floor" else (0.05, 0.04, 49000) if w == "sofa" else (0.0127, 0.1587, 723991)
    h_back = 0.544 if w == "outerWall" else 0.317 if w == "ceiling" else 0
    return (f"type radLayerWall; kappaMethod fluidThermo; Tinit {T0}; Q 0; h {4.403 if w == 'window' else 0}; Ta {T_OUT}; "
            f"h_back {h_back}; Tback {T_OUT}; nLayers {0 if w == 'window' else 24}; thickness {thickness}; conductivity {k}; "
            f"rhoCp {rho_cp}; emissivity 0; value uniform {T0};")


def fields(run, C, return_y):
    cfg = RUNS[run]
    flow, rise, furnace = cfg["flow"], cfg["rise"], cfg["furnace"]
    table = f"(0 0) (2 {flow}) "
    if furnace:
        table += f"(438 {flow}) (440 0) (744 0) (746 {flow}) (1182 {flow}) (1184 0) (1488 0) (2000 0)"
    else:
        table += f"(2000 {flow})"
    speed = flow / (1e5 / (GAS_R * (T0 + rise))) / 0.01
    k_in = 1.5 * (0.05 * speed) ** 2
    omega_in = k_in ** 0.5 / (0.09 ** 0.25 * 0.01)
    p0 = 1e5 * np.exp(-9.81 * C[:, 1] / (287.1 * T0))
    rho0 = p0 / (GAS_R * T0)
    dims = {"U": "0 1 -1 0 0 0 0", "T": "0 0 0 1 0 0 0", "p": "1 -1 -2 0 0 0 0", "p_rgh": "1 -1 -2 0 0 0 0",
            "k": "0 2 -2 0 0 0 0", "omega": "0 0 -1 0 0 0 0", "nut": "0 2 -1 0 0 0 0", "alphat": "1 -1 -1 0 0 0 0"}
    vals = {"U": "(0 0 0)", "T": str(T0), "k": "1e-4", "omega": "1", "nut": "0", "alphat": "0"}
    out = {}
    for n in dims:
        s = hdr(n, "volVectorField" if n == "U" else "volScalarField") + f"dimensions [{dims[n]}];\n"
        if n in ("p", "p_rgh"):
            v = p0 if n == "p" else p0 + rho0 * 9.81 * C[:, 1]
            s += "internalField nonuniform List<scalar>\n" + str(len(C)) + "\n(\n" + "\n".join(f"{x:.15g}" for x in v) + "\n);\n"
        else:
            s += f"internalField uniform {vals[n]};\n"
        s += "boundaryField\n{\n"
        for w in PATCHES:
            if w == "symmetry":
                bc = "type symmetryPlane;"
            else:
                bc = {"U": "type noSlip;", "T": "type zeroGradient;", "p": "type calculated; value uniform 100000;",
                      "p_rgh": "type fixedFluxPressure; value uniform 100000;", "k": "type kLowReWallFunction; value uniform 1e-4;",
                      "omega": "type omegaWallFunction; value uniform 1;", "nut": "type nutkWallFunction; value uniform 0;",
                      "alphat": "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;"}[n]
                if n == "T" and w in WALLS:
                    bc = wall_T(w)
                if w == "register":
                    if n == "U":
                        bc = f"type flowRateInletVelocity; massFlowRate table\n(\n{table}\n); rho rho; rhoInlet 1.2; value uniform (0 0 0);"
                    if n == "T":
                        bc = ("type codedFixedValue; value uniform 292.04; name supplyTemperature85;\n"
                              "codeInclude #{ #include \"fvCFD.H\" #};\ncode #{\n" + code("supply.C") + "#};")
                    if n == "k":
                        bc = f"type fixedValue; value uniform {k_in};"
                    if n == "omega":
                        bc = f"type fixedValue; value uniform {omega_in};"
                    if n in ("nut", "alphat"):
                        bc = "type calculated; value uniform 0;"
                if w == "return":
                    if n == "U":
                        bc = "type pressureInletOutletVelocity; value uniform (0 0 0);"
                    if n == "p_rgh":
                        pv = 1e5 * np.exp(-9.81 * return_y / (287.1 * T0))
                        bc = ("type prghPressure; p nonuniform List<scalar>\n" + str(len(pv)) + "\n(\n"
                              + "\n".join(f"{x:.15g}" for x in pv) + "\n); value uniform 100000;")
                    if n in ("T", "k", "omega"):
                        v = dict(T=292.04, k=0.0001, omega=1)[n]
                        bc = f"type inletOutlet; inletValue uniform {v}; value uniform {v};"
                        if n == "T" and furnace:
                            bc = f"type returnMeanTemperature; inletValue uniform {v}; value uniform {v};"
                    if n in ("nut", "alphat"):
                        bc = "type calculated; value uniform 0;"
            s += w + "\n{\n" + bc + "\n}\n"
        out[n] = s + "}\n"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=sorted(RUNS))
    ap.add_argument("out")
    ap.add_argument("--mesh", default="runs/mesh")
    ap.add_argument("--nprocs", type=int, default=4)
    a = ap.parse_args()
    cfg = RUNS[a.run]
    mesh, c = Path(a.mesh), Path(a.out)
    cells = np.load(mesh / "cells.npz")
    for d in ("0", "constant", "system"):
        (c / d).mkdir(parents=True, exist_ok=True)
    shutil.copytree(mesh / "constant/polyMesh", c / "constant/polyMesh", dirs_exist_ok=True)
    for n in ("g", "thermophysicalProperties", "turbulenceProperties", "fvOptions"):
        shutil.copy(CASE / "template/constant" / n, c / "constant" / n)
    for n in ("fvSchemes", "fvSolution"):
        shutil.copy(CASE / "template/system" / n, c / "system" / n)
    for n, s in fields(a.run, cells["C"], cells["returnFaces"][:, 1]).items():
        (c / "0" / n).write_text(s)
    (c / "system/decomposeParDict").write_text(hdr("decomposeParDict") + f"numberOfSubdomains {a.nprocs}; method scotch;\n")
    planes = (CASE / "template/system/planes").read_text()
    funcs = ("wallHeatFlux { type wallHeatFlux; libs (fieldFunctionObjects); patches (outerWall innerWall floor ceiling sideWall sofa window); "
             "executeControl timeStep; executeInterval 1; writeControl none; log false; }\n"
             "metrics { type coded; libs (utilityFunctionObjects); name metrics85; executeControl timeStep; executeInterval 1; writeControl none;\n"
             "codeInclude #{\n#include \"fvCFD.H\"\n#include <fstream>\n#include <iomanip>\n#include <vector>\n#include <algorithm>\n#};\n"
             "codeExecute #{\n" + code("monitor.C") + "\n#};\n}\n" + planes)
    (c / "system/functions").write_text(funcs)
    (c / "system/planesT0").write_text(hdr("planesT0") + 'libs ("libwall85.so");\nfunctions {\n' + planes + "}\n")
    (c / "system/controlDict").write_text(hdr("controlDict") + f"""application buoyantPimpleFoam;
libs ({LIBS[a.run]}); supplyRise {cfg['rise']}; supplyMassFlow {cfg['flow']:g}; furnaceMode {'true' if cfg['furnace'] else 'false'};
startFrom startTime; startTime 0; stopAt endTime; endTime 1488;
deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;
writeControl adjustableRunTime; writeInterval 120; purgeWrite 3;
writeFormat binary; writePrecision 10; writeCompression on; timeFormat general; timePrecision 10; runTimeModifiable false;
functions {{ #include "functions" }}
""")
    (c / "case.foam").touch()
    print(f"written: {c}")


if __name__ == "__main__":
    main()
