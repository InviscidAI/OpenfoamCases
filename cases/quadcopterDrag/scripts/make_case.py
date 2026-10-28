#!/usr/bin/env python3
"""Write the OpenFOAM case into run/: snappyHexMesh around geometry/airframe.stl, then
steady simpleFoam with k-omega SST.

    python3 scripts/make_case.py [nprocs]

Every number the run depends on is at the top of this file. run/case.json carries the
ones scripts/forces.py needs.

Frame: +x downstream, +y left, +z up; the nose points to -x. The airframe is built level
and flies 10 degrees nose-down, so in its own frame the wind comes from ahead and from
10 degrees above: U = 15 (cos 10, 0, -sin 10) m/s. Drag is the force along that wind,
and the vertical force is the force at right angles to it in the x-z plane, positive up.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "run"

# ---- flight
U_MAG = 15.0               # m/s, forward flight
PITCH_DEG = 10.0           # nose-down attitude
RHO = 1.225                # kg/m3, sea level
NU = 1.5e-5                # m2/s
TURB_I = 0.005             # 0.5% free-stream turbulence intensity
NUT_RATIO = 10.0           # free-stream eddy to molecular viscosity

# ---- solve
ITERATIONS = 2000          # SIMPLE iterations
AVERAGE_FROM = 1000        # forces are averaged over iterations after this one

# ---- domain and mesh (m)
X0, X1 = -1.40, 3.60       # 1.2 m of air ahead of the arms' tips, 3.4 m behind
Y0, Y1 = -1.40, 1.40
Z0, Z1 = -1.20, 1.20
BG = 0.05                  # background cell; level n is BG / 2**n
SURFACE_LEVELS = (4, 5)    # 3.1 mm to 1.6 mm on the airframe
FEATURE_LEVEL = 5
DISTANCE_LEVELS = [(0.025, 4), (0.09, 3), (0.30, 2)]
NEAR_BOX = ((-0.30, -0.30, -0.16), (0.45, 0.30, 0.12), 2)
WAKE_BOX = ((-0.35, -0.45, -0.42), (1.60, 0.45, 0.18), 2)   # 12.5 mm cells, 1.4 m of wake
LAYERS = 3
PARTS = ["body", "arms", "cans", "hubs", "legs"]

a = math.radians(PITCH_DEG)
UX, UZ = U_MAG * math.cos(a), -U_MAG * math.sin(a)
DRAG_DIR = (math.cos(a), 0.0, -math.sin(a))
LIFT_DIR = (math.sin(a), 0.0, math.cos(a))
K_INF = 1.5 * (TURB_I * U_MAG) ** 2
OMEGA_INF = K_INF / (NUT_RATIO * NU)


def write(rel: str, cls: str, body: str):
    p = CASE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    obj = p.name
    loc = f'    location    "{p.parent.name}";\n' if p.parent.name in ("0", "constant", "system") else ""
    p.write_text("FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
                 f"    class       {cls};\n{loc}    object      {obj};\n}}\n\n" + body)


def pt(v):
    return "(" + " ".join(f"{x:g}" for x in v) + ")"


def mesh_dicts(nprocs: int):
    nx, ny, nz = (round((X1 - X0) / BG), round((Y1 - Y0) / BG), round((Z1 - Z0) / BG))
    write("system/blockMeshDict", "dictionary", f"""scale 1;
vertices
(
    ({X0} {Y0} {Z0}) ({X1} {Y0} {Z0}) ({X1} {Y1} {Z0}) ({X0} {Y1} {Z0})
    ({X0} {Y0} {Z1}) ({X1} {Y0} {Z1}) ({X1} {Y1} {Z1}) ({X0} {Y1} {Z1})
);
blocks ( hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1) );
edges ();
boundary
(
    inlet  {{ type patch; faces ((0 4 7 3)); }}
    outlet {{ type patch; faces ((1 2 6 5)); }}
    ymin   {{ type patch; faces ((0 1 5 4)); }}
    ymax   {{ type patch; faces ((3 7 6 2)); }}
    zmin   {{ type patch; faces ((0 3 2 1)); }}
    zmax   {{ type patch; faces ((4 5 6 7)); }}
);
""")
    write("system/surfaceFeatureExtractDict", "dictionary", """airframe.stl
{
    extractionMethod    extractFromSurface;
    extractFromSurfaceCoeffs { includedAngle 150; }
    subsetFeatures { nonManifoldEdges no; openEdges yes; }
    writeObj            no;
}
""")
    smin, smax = SURFACE_LEVELS
    regions = "\n".join(f"                {p} {{ level ({smin} {smax}); patchInfo {{ type wall; }} }}"
                        for p in PARTS)
    names = "\n".join(f"            {p} {{ name {p}; }}" for p in PARTS)
    dist = " ".join(f"({d} {l})" for d, l in DISTANCE_LEVELS)
    write("system/snappyHexMeshDict", "dictionary", f"""castellatedMesh true;
snap            true;
addLayers       true;

geometry
{{
    airframe.stl
    {{
        type triSurfaceMesh;
        name airframe;
        regions
        {{
{names}
        }}
    }}
    nearBox {{ type searchableBox; min {pt(NEAR_BOX[0])}; max {pt(NEAR_BOX[1])}; }}
    wakeBox {{ type searchableBox; min {pt(WAKE_BOX[0])}; max {pt(WAKE_BOX[1])}; }}
}}

castellatedMeshControls
{{
    maxLocalCells       10000000;
    maxGlobalCells      60000000;
    minRefinementCells  10;
    nCellsBetweenLevels 3;
    maxLoadUnbalance    0.10;
    resolveFeatureAngle 30;
    allowFreeStandingZoneFaces true;
    features ( {{ file "airframe.eMesh"; level {FEATURE_LEVEL}; }} );
    refinementSurfaces
    {{
        airframe
        {{
            level ({smin} {smax});
            regions
            {{
{regions}
            }}
        }}
    }}
    refinementRegions
    {{
        airframe {{ mode distance; levels ({dist}); }}
        nearBox  {{ mode inside; levels ((1.0 {NEAR_BOX[2]})); }}
        wakeBox  {{ mode inside; levels ((1.0 {WAKE_BOX[2]})); }}
    }}
    locationInMesh (-1.113 0.877 0.663);
}}

snapControls
{{
    nSmoothPatch        3;
    tolerance           2.0;
    nSolveIter          60;
    nRelaxIter          6;
    nFeatureSnapIter    12;
    implicitFeatureSnap false;
    explicitFeatureSnap true;
    multiRegionFeatureSnap false;
}}

addLayersControls
{{
    relativeSizes       true;
    expansionRatio      1.25;
    finalLayerThickness 0.40;
    minThickness        0.05;
    layers {{ "({'|'.join(PARTS)})" {{ nSurfaceLayers {LAYERS}; }} }}
    nGrow               0;
    featureAngle        130;
    slipFeatureAngle    30;
    nRelaxIter          6;
    nSmoothSurfaceNormals 1;
    nSmoothNormals      3;
    nSmoothThickness    10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle  90;
    nBufferCellsNoExtrude 0;
    nLayerIter          50;
    nRelaxedIter        20;
}}

meshQualityControls
{{
    #includeEtc "caseDicts/meshQualityDict"
    nSmoothScale 4;
    errorReduction 0.75;
}}

writeFlags ();
mergeTolerance 1e-6;
""")
    write("system/meshQualityDict", "dictionary", '#includeEtc "caseDicts/meshQualityDict"\n')
    write("system/decomposeParDict", "dictionary", f"numberOfSubdomains {nprocs};\nmethod scotch;\n")


def fields():
    far = "(inlet|outlet|ymin|ymax|zmin|zmax)"
    walls = f"({'|'.join(PARTS)})"
    u = f"({UX:.6f} 0 {UZ:.6f})"

    def scalar(name, dims, value, far_bc, wall_bc):
        write(f"0/{name}", "volScalarField", f"""dimensions      {dims};
internalField   uniform {value:.6g};
boundaryField
{{
    "{far}" {{ {far_bc} }}
    "{walls}" {{ {wall_bc} }}
}}
""")
    write("0/U", "volVectorField", f"""dimensions      [0 1 -1 0 0 0 0];
internalField   uniform {u};
boundaryField
{{
    "{far}" {{ type freestreamVelocity; freestreamValue uniform {u}; }}
    "{walls}" {{ type noSlip; }}
}}
""")
    scalar("p", "[0 2 -2 0 0 0 0]", 0, "type freestreamPressure; freestreamValue uniform 0;",
           "type zeroGradient;")
    io = lambda v: f"type inletOutlet; inletValue uniform {v:.6g}; value uniform {v:.6g};"
    scalar("k", "[0 2 -2 0 0 0 0]", K_INF, io(K_INF),
           f"type kLowReWallFunction; value uniform {K_INF:.6g};")
    scalar("omega", "[0 0 -1 0 0 0 0]", OMEGA_INF, io(OMEGA_INF),
           f"type omegaWallFunction; value uniform {OMEGA_INF:.6g};")
    scalar("nut", "[0 2 -1 0 0 0 0]", NUT_RATIO * NU, f"type calculated; value uniform {NUT_RATIO*NU:.6g};",
           "type nutUSpaldingWallFunction; value uniform 0;")


def physics():
    write("constant/transportProperties", "dictionary", f"transportModel  Newtonian;\nnu              {NU};\n")
    write("constant/turbulenceProperties", "dictionary",
          "simulationType RAS;\nRAS\n{\n    RASModel        kOmegaSST;\n    turbulence      on;\n"
          "    printCoeffs     on;\n}\n")


def solver_dicts():
    forces = "\n".join(f"""    force_{name}
    {{
        type            forces;
        libs            (forces);
        patches         ({patches});
        rho             rhoInf;
        rhoInf          {RHO};
        CofR            (0 0 0);
        writeControl    timeStep;
        writeInterval   1;
        log             false;
    }}""" for name, patches in [("total", " ".join(PARTS))] + [(p, p) for p in PARTS])
    write("system/controlDict", "dictionary", f"""application     simpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {ITERATIONS};
deltaT          1;
writeControl    timeStep;
writeInterval   {ITERATIONS};
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
{forces}

    residuals
    {{
        type            solverInfo;
        libs            (utilityFunctionObjects);
        fields          (U p k omega);
        writeResidualFields false;
        writeControl    timeStep;
        writeInterval   1;
    }}

    yPlus
    {{
        type            yPlus;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        log             true;
    }}

    // Two sections and the airframe's surface at the last iteration, for pictures:
    // horizontal through the arms' axes, and vertical along the centreline.
    sections
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    writeTime;
        surfaceFormat   vtk;
        fields          (U p);
        interpolationScheme cellPoint;
        surfaces
        {{
            horizontal
            {{
                type        cuttingPlane;
                point       (0 0 0);
                normal      (0 0 1);
                interpolate true;
            }}
            centreline
            {{
                type        cuttingPlane;
                point       (0 0 0);
                normal      (0 1 0);
                interpolate true;
            }}
            airframe
            {{
                type        patch;
                patches     ({' '.join(PARTS)});
                interpolate true;
            }}
        }}
    }}
}}
""")
    write("system/fvSchemes", "dictionary", """ddtSchemes      { default steadyState; }
gradSchemes
{
    default         cellLimited Gauss linear 1;
    grad(U)         cellLimited Gauss linear 1;
}
divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss limitedLinear 1;
    div(phi,omega)  bounded Gauss limitedLinear 1;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited corrected 0.33; }
interpolationSchemes { default linear; }
snGradSchemes   { default limited corrected 0.33; }
wallDist        { method meshWave; }
""")
    write("system/fvSolution", "dictionary", """solvers
{
    p
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-7;
        relTol          0.01;
        nPreSweeps      0;
        nPostSweeps     2;
        cacheAgglomeration on;
        agglomerator    faceAreaPair;
        nCellsInCoarsestLevel 200;
        mergeLevels     1;
    }
    "(U|k|omega)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
        nSweeps         1;
    }
}
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent      no;
}
relaxationFactors
{
    fields          { p 0.3; }
    equations       { U 0.7; "(k|omega)" 0.7; }
}
cache { grad(U); }
""")


def main():
    nprocs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    stl = ROOT / "geometry" / "airframe.stl"
    if not stl.exists():
        raise SystemExit("no geometry/airframe.stl: run scripts/build_airframe.py first")
    if CASE.exists():
        shutil.rmtree(CASE)
    (CASE / "constant" / "triSurface").mkdir(parents=True)
    shutil.copy(stl, CASE / "constant" / "triSurface" / "airframe.stl")
    mesh_dicts(nprocs)
    fields()
    physics()
    solver_dicts()
    (CASE / "run.foam").write_text("")
    json.dump({"U_mag": U_MAG, "pitch_deg": PITCH_DEG, "rho": RHO, "nu": NU,
               "drag_dir": DRAG_DIR, "lift_dir": LIFT_DIR, "parts": PARTS,
               "iterations": ITERATIONS, "average_from": AVERAGE_FROM, "nprocs": nprocs},
              open(CASE / "case.json", "w"), indent=2)
    print(f"wrote {CASE} for {nprocs} ranks")
    print(f"  wind in the airframe's frame U = ({UX:.4f} 0 {UZ:.4f}) m/s, |U| = {U_MAG}")
    print(f"  Re on the body length 0.16 m = {U_MAG*0.16/NU:.3g}")


if __name__ == "__main__":
    main()
