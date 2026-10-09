#!/usr/bin/env python3
"""Write runs/overtaking/: the lorry alone in its own frame, for the rider being overtaken.
Called by `./Allrun overtaking`; it needs geometry/truck.stl and geometry/truck_wheels.stl
(scripts/build_truck.py), which are copied unmoved: the doors at x = 0, the cab's front at
x = 16.5 m. The numbers come from config_overtaking.sh, which is copied into the run.

The dictionaries are written as the solved run had them. controlDict was last edited with
OpenFOAM's foamDictionary, which wrote it out in its own layout and to six significant
figures (the writes every 0.00833333 s, maxDeltaT 0.00416667 s), so it is written here in
that layout and with those numbers. meshQualityDict is read only by `checkMesh
-meshQuality`; snappyHexMesh takes OpenFOAM's own defaults (meshQualityDict.cfg) with
maxNonOrtho 70.

    python3 scripts/makeOvertaking.py
"""
import re
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
case = root / "runs" / "overtaking"
cfg = {}
for line in open(root / "config_overtaking.sh"):
    m = re.match(r"([A-Za-z]\w*)=([^#\s]+)", line)
    if m:
        cfg[m.group(1)] = m.group(2)

if case.exists():
    shutil.rmtree(case)
for d in ("0", "constant/triSurface", "system"):
    (case / d).mkdir(parents=True)
for stl in ("truck.stl", "truck_wheels.stl"):
    shutil.copy(root / "geometry" / stl, case / "constant/triSurface" / stl)
shutil.copy(root / "config_overtaking.sh", case / "config.sh")

H = "FoamFile { format ascii; class dictionary; object %s; }\n"


def W(rel, text):
    (case / rel).write_text(text)


x0, x1, y0, y1, z0, z1 = (cfg[k] for k in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"))
W("system/blockMeshDict", H % "blockMeshDict" + f"""convertToMeters 1;
vertices
(
({x0} {y0} {z0}) ({x1} {y0} {z0}) ({x1} {y1} {z0}) ({x0} {y1} {z0})
({x0} {y0} {z1}) ({x1} {y0} {z1}) ({x1} {y1} {z1}) ({x0} {y1} {z1})
);
blocks (hex (0 1 2 3 4 5 6 7) ({cfg['nx']} {cfg['ny']} {cfg['nz']}) simpleGrading (1 1 1));
edges ();
boundary
(
 inlet {{type patch; faces ((1 2 6 5));}}
 outlet {{type patch; faces ((0 4 7 3));}}
 ground {{type wall; faces ((0 3 2 1));}}
 sides {{type symmetry; faces ((0 1 5 4)(3 7 6 2));}}
 top {{type symmetryPlane; faces ((4 5 6 7));}}
);
""")
W("system/surfaceFeatureExtractDict", H % "surfaceFeatureExtractDict" + """truck.stl { extractionMethod extractFromSurface; extractFromSurfaceCoeffs { includedAngle 150; } writeObj no; }
truck_wheels.stl { extractionMethod extractFromSurface; extractFromSurfaceCoeffs { includedAngle 150; } writeObj no; }
""")
# 0.125 m on the lorry and in a corridor along the rider's side (y -4.5 to -1.5 m, up to
# 2 m), 0.25 m around the lorry and its wake.
sL, nL, pL = cfg["surfaceLevel"], cfg["nearLevel"], cfg["pathLevel"]
W("system/snappyHexMeshDict", H % "snappyHexMeshDict" + f"""castellatedMesh true; snap true; addLayers false;
geometry
{{
 truck.stl {{type triSurfaceMesh; name truck;}}
 truck_wheels.stl {{type triSurfaceMesh; name wheels;}}
 nearVehicle {{type searchableBox; min (-3 -4 0); max (20 4 6);}}
 wake {{type searchableBox; min (-42 -6 0); max (2 6 6);}}
 riderCorridor {{type searchableBox; min (-42 -4.5 0); max (38 -1.5 2);}}
}}
castellatedMeshControls
{{ maxLocalCells 1200000; maxGlobalCells 1800000; minRefinementCells 0; nCellsBetweenLevels 2;
 features ({{file "truck.eMesh"; level {sL};}}{{file "truck_wheels.eMesh"; level {sL};}});
 refinementSurfaces
 {{ truck {{level ({sL} {sL}); patchInfo {{type wall;}}}}
    wheels {{level ({sL} {sL}); patchInfo {{type wall;}}}} }}
 resolveFeatureAngle 35;
 refinementRegions
 {{ nearVehicle {{mode inside; levels ((1E15 {nL}));}}
    wake {{mode inside; levels ((1E15 {nL}));}}
    riderCorridor {{mode inside; levels ((1E15 {pL}));}} }}
 locationInMesh (30 10 10); allowFreeStandingZoneFaces true;
}}
snapControls {{nSmoothPatch 3; tolerance 2.0; nSolveIter 50; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap false; explicitFeatureSnap true; multiRegionFeatureSnap false;}}
addLayersControls {{relativeSizes true; layers {{}}; expansionRatio 1.2; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50;}}
meshQualityControls {{#includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"
 maxNonOrtho 70; relaxed {{maxNonOrtho 75;}}}}
debug 0; mergeTolerance 1e-6;
""")
W("system/meshQualityDict", """FoamFile {format ascii; class dictionary; object meshQualityDict;}
maxNonOrtho 65;
maxBoundarySkewness 20;
maxInternalSkewness 8;
maxConcave 80;
minVol 1e-13;
minTetQuality 1e-15;
minArea -1;
minTwist 0.02;
minDeterminant 0.001;
minFaceWeight 0.05;
minVolRatio 0.01;
minTriangleTwist -1;
minFlatness 0.5;
errorReduction 0.75;
relaxed {maxNonOrtho 75; maxInternalSkewness 8;}
""")

# Both spellings of the transport and turbulence dictionaries, as the run had them.
nu = cfg["nu"]
W("constant/physicalProperties", H % "physicalProperties" + f"viscosityModel constant; nu {nu};")
W("constant/transportProperties", H % "transportProperties"
  + f"transportModel Newtonian; nu [0 2 -1 0 0 0 0] {nu};")
W("constant/momentumTransport", H % "momentumTransport" + """simulationType RAS;
RAS { model kOmegaSSTSAS; delta cubeRootVol; turbulence on; printCoeffs on; }
""")
W("constant/turbulenceProperties", H % "turbulenceProperties" + """simulationType RAS;
RAS { RASModel kOmegaSSTSAS; delta cubeRootVol; turbulence on; printCoeffs on; }
""")

# The air and the ground at the lorry's speed, in -x; 1% turbulence, 0.5 m length scale.
U = float(cfg["U"])
k = 1.5 * (U * 0.01) ** 2
om = k ** 0.5 / (0.09 ** 0.25 * 0.5)
walls = "sides {type symmetry;} top {type symmetryPlane;}"
fields = {
    "U": ("volVectorField", "[0 1 -1 0 0 0 0]", f"({-U} 0 0)",
          f"inlet {{type fixedValue; value uniform ({-U} 0 0);}} outlet {{type inletOutlet; inletValue uniform ({-U} 0 0); value uniform ({-U} 0 0);}} ground {{type movingWallVelocity; value uniform ({-U} 0 0);}} {walls} truck {{type noSlip;}} \"wheels.*\" {{type noSlip;}}"),
    "p": ("volScalarField", "[0 2 -2 0 0 0 0]", "0",
          f"inlet {{type zeroGradient;}} outlet {{type fixedValue; value uniform 0;}} ground {{type zeroGradient;}} {walls} truck {{type zeroGradient;}} \"wheels.*\" {{type zeroGradient;}}"),
    "k": ("volScalarField", "[0 2 -2 0 0 0 0]", str(k),
          f"inlet {{type fixedValue; value uniform {k};}} outlet {{type inletOutlet; inletValue uniform {k}; value uniform {k};}} ground {{type kqRWallFunction; value uniform {k};}} {walls} truck {{type kqRWallFunction; value uniform {k};}} \"wheels.*\" {{type kqRWallFunction; value uniform {k};}}"),
    "omega": ("volScalarField", "[0 0 -1 0 0 0 0]", str(om),
              f"inlet {{type fixedValue; value uniform {om};}} outlet {{type inletOutlet; inletValue uniform {om}; value uniform {om};}} ground {{type omegaWallFunction; value uniform {om};}} {walls} truck {{type omegaWallFunction; value uniform {om};}} \"wheels.*\" {{type omegaWallFunction; value uniform {om};}}"),
    "nut": ("volScalarField", "[0 2 -1 0 0 0 0]", "0",
            f"inlet {{type calculated; value uniform 0;}} outlet {{type calculated; value uniform 0;}} ground {{type nutkWallFunction; value uniform 0;}} {walls} truck {{type nutkWallFunction; value uniform 0;}} \"wheels.*\" {{type nutkWallFunction; value uniform 0;}}"),
}
for name, (cls, dims, internal, bcs) in fields.items():
    W("0/" + name, (H.replace("class dictionary", f"class {cls}") % name)
      + f"dimensions {dims}; internalField uniform {internal}; boundaryField {{ {bcs} }}")

W("system/fvSchemes", H % "fvSchemes" + "ddtSchemes {default backward;} gradSchemes {default Gauss linear; grad(U) cellLimited Gauss linear 1;} divSchemes {default none; div(phi,U) bounded Gauss linearUpwindV grad(U); div(phi,k) bounded Gauss limitedLinear 1; div(phi,omega) bounded Gauss limitedLinear 1; div((nuEff*dev2(T(grad(U))))) Gauss linear;} laplacianSchemes {default Gauss linear limited 0.5;} interpolationSchemes {default linear;} snGradSchemes {default limited 0.5;} wallDist {method meshWave;}")
W("system/fvSolution", H % "fvSolution" + 'solvers {p {solver GAMG; smoother GaussSeidel; tolerance 1e-6; relTol 0.05;} pFinal {solver GAMG; smoother GaussSeidel; tolerance 1e-6; relTol 0;} "(U|k|omega)" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1;} "(U|k|omega)Final" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0;} } PIMPLE {momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1; correctPhi yes;} relaxationFactors {equations {".*" 1;}}')
W("system/decomposeParDict", H % "decomposeParDict"
  + f"numberOfSubdomains {cfg['nRanks']}; method scotch; distributed no; roots ();")

# controlDict, in foamDictionary's layout. Two horizontal planes over the whole domain
# (shoulders z = 1.3 m and knees z = 0.6 m), sparse before 4 s and dense over 4-8 s; nine
# lines along x at the rider's path (y = -3.0 m, the 1.5 m gap) and at y = -2.25 and
# -4.0 m (0.75 and 2.5 m), each at z = 0.6, 1.0 and 1.3 m, every write over 4-8 s, 1531
# points from x = -40 to 36.5 m (5 cm); and the lorry's forces every step.
BANNER = r"""/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2512                                  |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
FoamFile
{
    format          ascii;
    class           dictionary;
    object          controlDict;
}

"""


def entry(key, value, indent=0):
    pad = " " * indent
    return f"{pad}{key:<15} {value};\n" if len(key) < 16 else f"{pad}{key} {value};\n"


def plane(name, z, start, end, interval):
    tag = "z" + f"{z:g}".replace(".", "p")
    s = f"    {name}\n    {{\n"
    for k_, v in [("type", "surfaces"), ("libs", "( sampling )"), ("enabled", "true"),
                  ("timeStart", start), ("timeEnd", end), ("executeControl", "none"),
                  ("writeControl", "adjustableRunTime"), ("writeInterval", interval),
                  ("surfaceFormat", "vtk"), ("fields", "( U p )"),
                  ("interpolationScheme", "cellPoint")]:
        s += entry(k_, v, 8)
    s += "        surfaces\n        {\n"
    s += f"            {tag}\n            {{\n"
    for k_, v in [("type", "plane"), ("point", f"( 0 0 {z:g} )"), ("normal", "( 0 0 1 )"),
                  ("triangulate", "false"), ("interpolate", "true")]:
        s += entry(k_, v, 16)
    s += "            }\n        }\n    }\n"
    return s


def lines():
    sets = []
    for y in (-3, -2.25, -4):
        for z in (0.6, 1, 1.3):
            name = f"l_y{str(y).replace('-', 'm').replace('.', 'p')}_z{str(z).replace('.', 'p')}"
            sets.append(f"{name} {{ type uniform ; axis x ; start ( -40 {y} {z} ) ; "
                        f"end ( 36.5 {y} {z} ) ; nPoints 1531 ; }}")
    s = "    riderLines\n    {\n"
    for k_, v in [("type", "sets"), ("libs", "( sampling )"), ("timeStart", "4"),
                  ("timeEnd", "8"), ("executeControl", "none"),
                  ("writeControl", "adjustableRunTime"), ("writeInterval", "0.00833333"),
                  ("setFormat", "csv"), ("interpolationScheme", "cellPoint"),
                  ("fields", "( U p )"), ("sets", "( " + " ".join(sets) + " )")]:
        s += entry(k_, v, 8)
    return s + "    }\n"


def forces(name, extra):
    s = f"    {name}\n    {{\n"
    for k_, v in [("type", name), ("libs", "( forces )"), ("patches", '( truck "wheels.*" )'),
                  ("rho", "rhoInf"), ("rhoInf", cfg["rho"])] + extra + [
                  ("writeControl", "timeStep"), ("writeInterval", "1"), ("log", "true")]:
        s += entry(k_, v, 8)
    return s + "    }\n"


top = [("application", "pimpleFoam"), ("startFrom", "startTime"), ("startTime", "0"),
       ("stopAt", "endTime"), ("endTime", cfg["endTime"]), ("deltaT", "0.001"),
       ("writeControl", "adjustableRunTime"), ("writeInterval", cfg["endTime"]),
       ("purgeWrite", "0"), ("writeFormat", "binary"), ("writePrecision", "7"),
       ("writeCompression", "on"), ("timeFormat", "general"), ("timePrecision", "8"),
       ("runTimeModifiable", "true"), ("adjustTimeStep", "yes"), ("maxCo", cfg["maxCo"]),
       ("maxDeltaT", "0.00416667")]
text = BANNER + "\n".join(entry(k_, v) for k_, v in top) + "\nfunctions\n{\n"
text += plane("shoulderEarly", 1.3, "0", "4", "0.25")
text += plane("shoulderClip", 1.3, "4", "8", "0.00833333")
text += plane("kneeEarly", 0.6, "0", "4", "1")
text += plane("kneeClip", 0.6, "4", "8", "0.0333333")
text += lines()
text += forces("forces", [("CofR", "( 8.25 0 1 )")])
text += forces("forceCoeffs", [("magUInf", cfg["U"]), ("lRef", "16.5"), ("Aref", cfg["Aref"]),
                               ("CofR", "( 8.25 0 1 )"), ("dragDir", "( -1 0 0 )"),
                               ("liftDir", "( 0 0 1 )"), ("pitchAxis", "( 0 1 0 )")])
text += "}\n\n\n// " + "*" * 73 + " //\n"
W("system/controlDict", text)
print(case)
