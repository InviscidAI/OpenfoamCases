#!/usr/bin/env python3
"""Write runs/<run>/ for one of the three car runs, in the lorry's frame:

    carAlone   the car alone, its front bumper at x = -50 m
    tailgate   the lorry's doors at x = 0, the car's front 12.5 m behind them
    safe       the same lorry, the car's front 50 m behind them

Called by Allrun after `source config_car.sh`, which is copied into the run. It needs
geometry/car.stl and car_wheels.stl (scripts/build_car.py), and geometry/truck.stl and
truck_wheels.stl (scripts/build_truck.py) for the two lorry runs, and OpenFOAM's
surfaceTransformPoints, which moves the car back by its gap; the lorry is copied unmoved.
The car alone stands where the safe run's car stands, so the two meshes around it match.

The dictionaries are written as the solved runs had them, numbers as literals. The solves
wrote a field every 1 s (writeInterval 1) and ran on 3 ranks alone and 6 with the lorry,
so decomposeParDict asks for those.

    python3 scripts/makeCarCase.py carAlone|tailgate|safe
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RUNS = {"carAlone": (50.0, 3), "tailgate": (12.5, 6), "safe": (50.0, 6)}
run = sys.argv[1] if len(sys.argv) > 1 else ""
if run not in RUNS:
    raise SystemExit("usage: makeCarCase.py carAlone|tailgate|safe")
gap, nprocs = RUNS[run]
lorry = run != "carAlone"
root = Path(__file__).resolve().parent.parent
case = root / "runs" / run
E = os.environ
endTime = float(E.get("END_TIME", 8))
deltaT = float(E.get("DELTA_T", .001))
maxCo = float(E.get("MAX_CO", .9))

if case.exists():
    shutil.rmtree(case)
for d in ["0", "constant/triSurface", "system"]:
    (case / d).mkdir(parents=True, exist_ok=True)
# The STLs keep their triangles; the car's are only translated by the gap.
for src in ("car.stl", "car_wheels.stl"):
    subprocess.run(["surfaceTransformPoints", "-translate", f"({-gap} 0 0)",
                    str(root / "geometry" / src), str(case / "constant/triSurface" / src)],
                   check=True, stdout=subprocess.DEVNULL)
if lorry:
    for src in ("truck.stl", "truck_wheels.stl"):
        shutil.copy(root / "geometry" / src, case / "constant/triSurface" / src)
shutil.copy(root / "config_car.sh", case / "config.sh")

H = "FoamFile { format ascii; class dictionary; object %s; }\n"
CLS = {"U": "volVectorField", "p": "volScalarField", "k": "volScalarField",
       "omega": "volScalarField", "nut": "volScalarField"}


def w(rel, obj, txt):
    (case / rel).write_text((H % obj).replace("class dictionary", "class " + CLS.get(obj, "dictionary")) + txt)


w("system/blockMeshDict", "blockMeshDict", """convertToMeters 1;
vertices
(
 (-85 -8 0) (30 -8 0) (30 8 0) (-85 8 0)
 (-85 -8 10) (30 -8 10) (30 8 10) (-85 8 10)
);
blocks (hex (0 1 2 3 4 5 6 7) (115 16 10) simpleGrading (1 1 1));
edges ();
boundary
(
 outlet { type patch; faces ((0 4 7 3)); }
 inlet { type patch; faces ((1 2 6 5)); }
 sideA { type symmetryPlane; faces ((0 1 5 4)); }
 sideB { type symmetryPlane; faces ((3 7 6 2)); }
 ground { type wall; faces ((0 3 2 1)); }
 top { type symmetryPlane; faces ((4 5 6 7)); }
);
""")
geom = """car.stl { type triSurfaceMesh; name car; }
car_wheels.stl { type triSurfaceMesh; name car_wheels; }
"""
refs = """car { level (4 4); patchInfo { type wall; } }
car_wheels { level (5 5); patchInfo { type wall; } }
"""
if lorry:
    geom += """truck.stl { type triSurfaceMesh; name truck; }\ntruck_wheels.stl { type triSurfaceMesh; name truck_wheels; }\n"""
    refs += """truck { level (4 4); patchInfo { type wall; } }\ntruck_wheels { level (5 5); patchInfo { type wall; } }\n"""
# The same 0.25 m box around the car in every run, 8 m ahead of its front to 25 m behind
# it; with the lorry, a 0.25 m box from its doors to 20 m behind the car's rear.
geom += f"""carZone {{ type searchableBox; min ({-gap-25} -3 0); max ({-gap+8} 3 4); }}\n"""
regions = """carZone { mode inside; levels ((1e15 2)); }\n"""
if lorry:
    geom += f"""lorryWake {{ type searchableBox; min ({-gap-24.689} -3 0); max (2 3 5); }}\n"""
    regions += """lorryWake { mode inside; levels ((1e15 2)); }\n"""
w("system/snappyHexMeshDict", "snappyHexMeshDict", f"""castellatedMesh true; snap true; addLayers false;
geometry {{ {geom} }}
castellatedMeshControls
{{
 maxLocalCells 900000; maxGlobalCells 3000000; minRefinementCells 0; nCellsBetweenLevels 2;
 features ();
 refinementSurfaces {{ {refs} }}
 resolveFeatureAngle 35;
 refinementRegions {{ {regions} }}
 locationInMesh (-82 0 8);
 allowFreeStandingZoneFaces true;
}}
snapControls {{ nSmoothPatch 3; tolerance 2.0; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap false; explicitFeatureSnap false; multiRegionFeatureSnap false; }}
addLayersControls {{ relativeSizes true; layers {{}}; expansionRatio 1.2; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 20; }}
meshQualityControls {{ #include "meshQualityDict" }}
mergeTolerance 1e-6;
""")
w("system/meshQualityDict", "meshQualityDict", """#includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"\n""")
w("system/decomposeParDict", "decomposeParDict", f"""numberOfSubdomains {nprocs}; method scotch;\n""")
w("constant/transportProperties", "transportProperties", """transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] 1.5e-5;\n""")
w("constant/turbulenceProperties", "turbulenceProperties", """simulationType RAS;
RAS
{
 RASModel kOmegaSSTSAS;
 delta cubeRootVol;
 turbulence on;
 printCoeffs on;
}
""")
w("system/fvSchemes", "fvSchemes", """ddtSchemes { default backward; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes
{
 default none;
 div(phi,U) bounded Gauss linearUpwindV grad(U);
 div(phi,k) bounded Gauss limitedLinear 1;
 div(phi,omega) bounded Gauss limitedLinear 1;
 div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
""")
w("system/fvSolution", "fvSolution", """solvers
{
 p { solver GAMG; tolerance 1e-7; relTol 0.05; smoother GaussSeidel; }
 pFinal { $p; relTol 0; }
 "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
 "(U|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { ".*" 1; } }
""")
# Initial and boundary fields: the air and the ground at 25 m/s in -x, 1% turbulence
# intensity, a 0.5 m length scale.
walls = '"(car|car_wheels.*|truck|truck_wheels.*)"'
sym = '"(sideA|sideB|top)" { type symmetryPlane; }'
fields = {
    "U": ("[0 1 -1 0 0 0 0]", "uniform (-25 0 0)",
          f"inlet {{ type fixedValue; value uniform (-25 0 0); }} outlet {{ type inletOutlet; inletValue uniform (-25 0 0); value uniform (-25 0 0); }} ground {{ type movingWallVelocity; value uniform (-25 0 0); }} {walls} {{ type noSlip; }} {sym}"),
    "p": ("[0 2 -2 0 0 0 0]", "uniform 0",
          f"inlet {{ type zeroGradient; }} outlet {{ type fixedValue; value uniform 0; }} ground {{ type zeroGradient; }} {walls} {{ type zeroGradient; }} {sym}"),
    "k": ("[0 2 -2 0 0 0 0]", "uniform 0.09375",
          f"inlet {{ type fixedValue; value uniform 0.09375; }} outlet {{ type inletOutlet; inletValue uniform 0.09375; value uniform 0.09375; }} ground {{ type kqRWallFunction; value uniform 0.09375; }} {walls} {{ type kqRWallFunction; value uniform 0.09375; }} {sym}"),
    "omega": ("[0 0 -1 0 0 0 0]", "uniform 1.12",
              f"inlet {{ type fixedValue; value uniform 1.12; }} outlet {{ type inletOutlet; inletValue uniform 1.12; value uniform 1.12; }} ground {{ type omegaWallFunction; value uniform 1.12; }} {walls} {{ type omegaWallFunction; value uniform 1.12; }} {sym}"),
    "nut": ("[0 2 -1 0 0 0 0]", "uniform 0",
            f"inlet {{ type calculated; value uniform 0; }} outlet {{ type calculated; value uniform 0; }} ground {{ type nutkWallFunction; value uniform 0; }} {walls} {{ type nutkWallFunction; value uniform 0; }} {sym}"),
}
for fld, (dims, internal, b) in fields.items():
    w("0/" + fld, fld, f"""dimensions {dims};\ninternalField {internal};\nboundaryField {{ {b} }}\n""")
lorryFns = ""
if lorry:
    lorryFns = """
 lorryForces { type forces; libs (forces); patches (truck "truck_wheels.*"); rho rhoInf; rhoInf 1.225; CofR (0 0 0); writeControl timeStep; writeInterval 1; log false; }
 lorryCoeff { type forceCoeffs; libs (forces); patches (truck "truck_wheels.*"); rho rhoInf; rhoInf 1.225; magUInf 25; lRef 4; Aref 9.78; CofR (0 0 0); dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); writeControl timeStep; writeInterval 1; log false; }
"""
# The planes are cut across the whole domain. The car alone writes them every 0.25 s,
# the lorry runs the side plane every 1/120 s and the plane at 0.75 m every 1/30 s.
sideInterval = 0.25 if not lorry else 1 / 120
topInterval = 0.25 if not lorry else 1 / 30
w("system/controlDict", "controlDict", f"""application pimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime {endTime};
deltaT {deltaT}; writeControl runTime; writeInterval 1; purgeWrite 0;
writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 7;
runTimeModifiable true; adjustTimeStep true; maxCo {maxCo}; maxDeltaT {deltaT};
functions
{{
 carBodyForces {{ type forces; libs (forces); patches (car); rho rhoInf; rhoInf 1.225; CofR (0 0 0); writeControl timeStep; writeInterval 1; log false; }}
 carForces {{ type forces; libs (forces); patches (car "car_wheels.*"); rho rhoInf; rhoInf 1.225; CofR (0 0 0); writeControl timeStep; writeInterval 1; log false; }}
 carCoeff {{ type forceCoeffs; libs (forces); patches (car "car_wheels.*"); rho rhoInf; rhoInf 1.225; magUInf 25; lRef 4.689; Aref 2.265; CofR (0 0 0); dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); writeControl timeStep; writeInterval 1; log false; }}
 {lorryFns}
 side {{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {sideInterval}; surfaceFormat vtk; formatOptions {{ vtk {{ format binary; }} }}; fields (U p); interpolationScheme cellPoint; surfaces {{ side {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (0 1 0); }} interpolate true; }} }} }}
 topPlane {{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {topInterval}; surfaceFormat vtk; formatOptions {{ vtk {{ format binary; }} }}; fields (U p); interpolationScheme cellPoint; surfaces {{ top {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0.75); normal (0 0 1); }} interpolate true; }} }} }}
}}
""")
print(case)
