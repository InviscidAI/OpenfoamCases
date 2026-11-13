#!/usr/bin/env python3
"""Write one run of the pace-line case: four riders in single file, or one rider alone.

    python3 scripts/make_case.py line|alone runs/<run> [--nprocs 8] [--geometry DIR]

The rider (rider.stl) and the bike's wheels (bike_wheels.stl) are cyclistBehindLorry's,
built by ../cyclistBehindLorry/scripts/build_rider.py into ../cyclistBehindLorry/geometry/
(Allrun builds them if they are not there). Each rider is a copy translated along x by
config/case.json's offsets with surfaceTransformPoints, so OpenFOAM must be sourced.

From template/: system/ (blockMeshDict, fvSchemes, fvSolution, meshQualityDict,
decomposeParDict), constant/ (transportProperties, turbulenceProperties) and 0.orig/,
copied to 0/. Written here, because they list the riders: system/snappyHexMeshDict and
system/controlDict. Both are the solved runs' text but for the controlDict's start and end
lines (the solved runs were restarted from checkpoints; this one goes from 0 to endTime)
and the abort function object that stopped the solved runs at the study's time cap, which
is left out.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("line", "alone"))
    ap.add_argument("dest")
    ap.add_argument("--nprocs", type=int, default=8)
    ap.add_argument("--geometry", default=str(CASE.parent / "cyclistBehindLorry" / "geometry"))
    a = ap.parse_args()
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    geometry = Path(a.geometry)
    for f in ("rider.stl", "bike_wheels.stl"):
        if not (geometry / f).is_file():
            raise SystemExit(f"{geometry / f} is missing: run ../cyclistBehindLorry/scripts/build_rider.py")
    case = Path(a.dest)
    if case.exists():
        raise SystemExit(f"{case} exists; ./Allclean or move it away first")
    t = CASE / "template"
    shutil.copytree(t / "system", case / "system")
    shutil.copytree(t / "constant", case / "constant")
    shutil.copytree(t / "0.orig", case / "0")
    (case / "constant" / "triSurface").mkdir()
    d = case / "system" / "decomposeParDict"
    d.write_text(d.read_text().replace("numberOfSubdomains 8;", f"numberOfSubdomains {a.nprocs};"))

    n = cfg["riders"][a.run]
    vec = lambda v: "(" + " ".join(map(str, v)) + ")"
    geom, refs, regions = [], [], []
    for i, offset in enumerate(cfg["offsets"][:n], 1):
        for source, name, level in (("rider.stl", f"rider{i}", cfg["riderLevel"]),
                                    ("bike_wheels.stl", f"rider{i}_wheels", cfg["wheelLevel"])):
            subprocess.run(["surfaceTransformPoints", "-translate", f"({offset} 0 0)",
                            str(geometry / source), str(case / "constant" / "triSurface" / f"{name}.stl")],
                           check=True, stdout=subprocess.DEVNULL)
            geom.append(f"{name}.stl {{ type triSurfaceMesh; name {name}; }}")
            refs.append(f"{name} {{ level ({level} {level}); patchInfo {{ type wall; }} }}")
    for i, (lo, hi, level) in enumerate(cfg["boxes"]):
        geom.append(f"box{i} {{ type searchableBox; min {vec(lo)}; max {vec(hi)}; }}")
        regions.append(f"box{i} {{ mode inside; levels ((1e15 {level})); }}")

    (case / "system" / "snappyHexMeshDict").write_text(
        "FoamFile { format ascii; class dictionary; object snappyHexMeshDict; }\n"
        "castellatedMesh true; snap true; addLayers true;\n"
        "geometry\n{\n" + "\n".join(geom) + "\n}\n"
        "castellatedMeshControls\n{\n"
        " maxLocalCells 6000000; maxGlobalCells 6000000; minRefinementCells 0; nCellsBetweenLevels 2;\n"
        " features ();\n"
        " refinementSurfaces\n{\n" + "\n".join(refs) + "\n}\n"
        " resolveFeatureAngle 35;\n"
        " refinementRegions\n{\n" + "\n".join(regions) + "\n}\n"
        " locationInMesh (15 6 8);\n"
        " allowFreeStandingZoneFaces true;\n}\n"
        "snapControls { nSmoothPatch 3; tolerance 2.0; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; "
        "implicitFeatureSnap false; explicitFeatureSnap false; multiRegionFeatureSnap false; }\n"
        "addLayersControls\n{\n"
        " relativeSizes true;\n"
        ' layers { "rider[1-5]" { nSurfaceLayers 3; } }\n'
        " expansionRatio 1.25; finalLayerThickness 0.3; minThickness 0.05; nGrow 0;\n"
        " featureAngle 180; layerTerminationAngle 180; slipFeatureAngle 30; nRelaxIter 5; "
        "nSmoothSurfaceNormals 1; nSmoothNormals 3;\n"
        " nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 1.0;\n"
        " minMedialAxisAngle 130; nMedialAxisIter 10; nBufferCellsNoExtrude 0; nLayerIter 50; nRelaxedIter 50;\n}\n"
        'meshQualityControls { #include "meshQualityDict"\n'
        " relaxed { maxNonOrtho 75; minTetQuality -1e30; maxConcave 90; minTwist 0.001; "
        "minDeterminant 0.0001; minFaceWeight 0.01; minVolRatio 0.005; } }\n"
        "mergeTolerance 1e-6;\n")

    U = cfg["speed"]
    fns = []
    for i in range(1, n + 1):
        common = (f'libs (forces); patches (rider{i} "rider{i}_wheels.*"); rho rhoInf; rhoInf {cfg["rho"]}; '
                  "CofR (0 0 0); writeControl timeStep; writeInterval 1; log false;")
        fns.append(f"rider{i}Forces {{ type forces; {common} }}")
        fns.append(f"rider{i}Coeffs {{ type forceCoeffs; {common} magUInf {U}; lRef {cfg['lRef']}; "
                   f"Aref {cfg['Aref']}; dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); }}")
    fns.append(f"""plan
{{
 type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {cfg['planeInterval']};
 surfaceFormat vtk; formatOptions {{ vtk {{ format binary; }} }};
 fields (U); interpolationScheme cellPoint;
 surfaces {{ plan {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 1); normal (0 0 1); }} interpolate true; }} }}
}}""")
    fns.append("cellCo {type CourantNo; libs (fieldFunctionObjects); executeControl timeStep; "
               "executeInterval 1; writeControl writeTime;}")
    fns.append("extrema {type fieldMinMax; libs (fieldFunctionObjects); fields (Co U p k omega nut); "
               "mode magnitude; location true; log false; executeControl timeStep; executeInterval 1; "
               "writeControl timeStep; writeInterval 20;}")
    fns.append("yPlus { type yPlus; libs (fieldFunctionObjects); writeControl writeTime; }")
    points = " ".join(f"({x} {y} {cfg['probeZ']})" for x in cfg["probeX"] for y in cfg["probeY"])
    fns.append("wakeProbes { type probes; libs (sampling); fields (U); writeControl timeStep; "
               "writeInterval 1; probeLocations (" + points + "); }")
    (case / "system" / "controlDict").write_text(
        "FoamFile { format ascii; class dictionary; object controlDict; }\n"
        "application pimpleFoam;\n"
        f"startFrom startTime; startTime 0; stopAt endTime; endTime {cfg['endTime']};\n"
        f"deltaT {cfg['deltaT']}; writeControl adjustableRunTime; writeInterval {cfg['volumeInterval']}; "
        f"purgeWrite {cfg['purgeWrite']};\n"
        "writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 10;\n"
        f"runTimeModifiable false; adjustTimeStep true; maxCo {cfg['maxCo']}; maxDeltaT {cfg['maxDeltaT']};\n"
        "functions\n{\n" + "\n".join(fns) + "\n}\n")
    print(case)


if __name__ == "__main__":
    main()
