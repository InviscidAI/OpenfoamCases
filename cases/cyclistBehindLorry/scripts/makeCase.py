#!/usr/bin/env python3
"""Write runs/<run>/ for one of the three runs: alone, close (the lorry's doors 1.5 m ahead
of the front tyre) or far (10 m). Called by Allrun after `source config.sh`; it needs the
STLs in geometry/ (scripts/build_rider.py, scripts/build_truck.py) and OpenFOAM's
surfaceTransformPoints, which moves the lorry forward by the gap. The dictionaries are
written as the solved runs had them; most numbers in them are literals that config.sh
records."""
import os,sys,shutil,subprocess
from pathlib import Path
run=sys.argv[1]
if run not in ('alone','close','far'): raise SystemExit('usage: makeCase.py alone|close|far')
root=Path(__file__).resolve().parent.parent; case=root/'runs'/run
E=os.environ; speed=float(E.get('SPEED',25)); endTime=float(E.get('END_TIME',4)); deltaT=float(E.get('DELTA_T',.001)); maxCo=float(E.get('MAX_CO',.9)); nprocs=int(E.get('NPROCS',5)); nu=float(E.get('NU',1.5e-5)); rho=float(E.get('RHO',1.225)); kin=float(E.get('KINLET',.09375)); oin=float(E.get('OMEGAINLET',1.12))
if case.exists(): shutil.rmtree(case)
for d in ['0','constant/triSurface','system']: (case/d).mkdir(parents=True,exist_ok=True)
shutil.copy(root/'geometry/rider.stl',case/'constant/triSurface/rider.stl')
shutil.copy(root/'geometry/bike_wheels.stl',case/'constant/triSurface/bike_wheels.stl')
if run!='alone':
 gap=1.5 if run=='close' else 10.0
 for src,out in [('truck.stl','truck.stl'),('truck_wheels.stl','truck_wheels.stl')]:
  subprocess.run(['surfaceTransformPoints','-translate',f'({gap} 0 0)',str(root/'geometry'/src),str(case/'constant/triSurface'/out)],check=True,stdout=subprocess.DEVNULL)
try: os.symlink('../../config.sh',case/'config.sh')
except: shutil.copy(root/'config.sh',case/'config.sh')
H='''FoamFile { format ascii; class dictionary; object %s; }\n'''
def w(rel,obj,txt):
 cls={'U':'volVectorField','p':'volScalarField','k':'volScalarField','omega':'volScalarField','nut':'volScalarField'}.get(obj,'dictionary')
 (case/rel).write_text((H%obj).replace('class dictionary','class '+cls)+txt)
w('system/blockMeshDict','blockMeshDict','''convertToMeters 1;
vertices
(
 (-14 -8 0) (32 -8 0) (32 8 0) (-14 8 0)
 (-14 -8 10) (32 -8 10) (32 8 10) (-14 8 10)
);
blocks (hex (0 1 2 3 4 5 6 7) (46 16 10) simpleGrading (1 1 1));
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
''')
geom='''rider.stl { type triSurfaceMesh; name rider; }
bike_wheels.stl { type triSurfaceMesh; name bike_wheels; }
'''
refs='''rider { level (4 4); patchInfo { type wall; } }
bike_wheels { level (5 5); patchInfo { type wall; } }
'''
if run!='alone':
 geom+='''truck.stl { type triSurfaceMesh; name truck; }\ntruck_wheels.stl { type triSurfaceMesh; name truck_wheels; }\n'''
 refs+='''truck { level (4 4); patchInfo { type wall; } }\ntruck_wheels { level (4 4); patchInfo { type wall; } }\n'''
# boxes fixed in rider coordinates; truck box extends over both possible positions
geom+='''riderWake { type searchableBox; min (-10 -3 0); max (14 3 5); }\ntruckZone { type searchableBox; min (-2 -3 0); max (29 3 5); }\n'''
regions='''riderWake { mode inside; levels ((1e15 2)); }\n'''+('''truckZone { mode inside; levels ((1e15 2)); }\n''' if run!='alone' else '')
w('system/snappyHexMeshDict','snappyHexMeshDict',f'''castellatedMesh true; snap true; addLayers false;
geometry {{ {geom} }}
castellatedMeshControls
{{
 maxLocalCells 900000; maxGlobalCells 3000000; minRefinementCells 0; nCellsBetweenLevels 2;
 features ();
 refinementSurfaces {{ {refs} }}
 resolveFeatureAngle 35;
 refinementRegions {{ {regions} }}
 locationInMesh (-12 0 8);
 allowFreeStandingZoneFaces true;
}}
snapControls {{ nSmoothPatch 3; tolerance 2.0; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap false; explicitFeatureSnap false; multiRegionFeatureSnap false; }}
addLayersControls {{ relativeSizes true; layers {{}}; expansionRatio 1.2; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 20; }}
meshQualityControls {{ #include "meshQualityDict" }}
mergeTolerance 1e-6;
''')
w('system/meshQualityDict','meshQualityDict','''#includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"\n''')
w('system/decomposeParDict','decomposeParDict',f'''numberOfSubdomains {nprocs}; method scotch;\n''')
w('constant/transportProperties','transportProperties','''transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] 1.5e-5;\n''')
w('constant/turbulenceProperties','turbulenceProperties','''simulationType RAS;
RAS
{
 RASModel kOmegaSSTSAS;
 delta cubeRootVol;
 turbulence on;
 printCoeffs on;
}
''')
w('system/fvSchemes','fvSchemes','''ddtSchemes { default backward; }
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
''')
w('system/fvSolution','fvSolution','''solvers
{
 p { solver GAMG; tolerance 1e-7; relTol 0.05; smoother GaussSeidel; }
 pFinal { $p; relTol 0; }
 "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
 "(U|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { ".*" 1; } }
''')
# fields
common={'U':('volVectorField','[0 1 -1 0 0 0 0]','uniform (-25 0 0)'), 'p':('volScalarField','[0 2 -2 0 0 0 0]','uniform 0'), 'k':('volScalarField','[0 2 -2 0 0 0 0]','uniform 0.09375'), 'omega':('volScalarField','[0 0 -1 0 0 0 0]','uniform 1.12'), 'nut':('volScalarField','[0 2 -1 0 0 0 0]','uniform 0')}
for fld,(cls,dims,internal) in common.items():
 if fld=='U': b='''inlet { type fixedValue; value uniform (-25 0 0); } outlet { type inletOutlet; inletValue uniform (-25 0 0); value uniform (-25 0 0); } ground { type movingWallVelocity; value uniform (-25 0 0); } "(rider|bike_wheels.*|truck|truck_wheels.*)" { type noSlip; } "(sideA|sideB|top)" { type symmetryPlane; }'''
 elif fld=='p': b='''inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } ground { type zeroGradient; } "(rider|bike_wheels.*|truck|truck_wheels.*)" { type zeroGradient; } "(sideA|sideB|top)" { type symmetryPlane; }'''
 elif fld=='k': b='''inlet { type fixedValue; value uniform 0.09375; } outlet { type inletOutlet; inletValue uniform 0.09375; value uniform 0.09375; } ground { type kqRWallFunction; value uniform 0.09375; } "(rider|bike_wheels.*|truck|truck_wheels.*)" { type kqRWallFunction; value uniform 0.09375; } "(sideA|sideB|top)" { type symmetryPlane; }'''
 elif fld=='omega': b='''inlet { type fixedValue; value uniform 1.12; } outlet { type inletOutlet; inletValue uniform 1.12; value uniform 1.12; } ground { type omegaWallFunction; value uniform 1.12; } "(rider|bike_wheels.*|truck|truck_wheels.*)" { type omegaWallFunction; value uniform 1.12; } "(sideA|sideB|top)" { type symmetryPlane; }'''
 else: b='''inlet { type calculated; value uniform 0; } outlet { type calculated; value uniform 0; } ground { type nutkWallFunction; value uniform 0; } "(rider|bike_wheels.*|truck|truck_wheels.*)" { type nutkWallFunction; value uniform 0; } "(sideA|sideB|top)" { type symmetryPlane; }'''
 w('0/'+fld,fld,f'''dimensions {dims};\ninternalField {internal};\nboundaryField {{ {b} }}\n''')
lorryFns=''
if run!='alone': lorryFns='''
 lorryForces { type forces; libs (forces); patches (truck "truck_wheels.*"); rho rhoInf; rhoInf 1.225; CofR (0 0 0); writeControl timeStep; writeInterval 1; log false; }
 lorryCoeff { type forceCoeffs; libs (forces); patches (truck "truck_wheels.*"); rho rhoInf; rhoInf 1.225; magUInf 25; lRef 4; Aref 9.78; CofR (0 0 0); dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); writeControl timeStep; writeInterval 1; log false; }
'''
# Plane surfaces, no bounds: crop script writes exact requested rider-coordinate bounds afterward.
w('system/controlDict','controlDict',f'''application pimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime {endTime:g};
deltaT {deltaT}; writeControl runTime; writeInterval {endTime:g}; purgeWrite 0;
writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 7;
runTimeModifiable true; adjustTimeStep true; maxCo {maxCo}; maxDeltaT {deltaT};
functions
{{
 riderForces {{ type forces; libs (forces); patches (rider "bike_wheels.*"); rho rhoInf; rhoInf 1.225; CofR (0 0 0); writeControl timeStep; writeInterval 1; log false; }}
 riderCoeff {{ type forceCoeffs; libs (forces); patches (rider "bike_wheels.*"); rho rhoInf; rhoInf 1.225; magUInf 25; lRef 1.75; Aref 0.448; CofR (0 0 0); dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); writeControl timeStep; writeInterval 1; log false; }}
 {lorryFns}
 side {{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.008333333333333; surfaceFormat vtk; formatOptions {{ vtk {{ format binary; }} }}; fields (U p); interpolationScheme cellPoint; surfaces {{ side {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (0 1 0); }} interpolate true; }} }} }}
 topPlane {{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.033333333333333; surfaceFormat vtk; formatOptions {{ vtk {{ format binary; }} }}; fields (U p); interpolationScheme cellPoint; surfaces {{ top {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 1.15); normal (0 0 1); }} interpolate true; }} }} }}
}}
''')
print(case)
