#!/usr/bin/env python3
import os,sys,shutil,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
mode=sys.argv[1]
if mode not in ('alone','behind','pair'): raise SystemExit('mode: alone|behind|pair')
# parse shell-style scalar config
cfg={}
for line in (root/'config.sh').read_text().splitlines():
 m=re.match(r'([A-Z0-9_]+)=(.*)',line.strip())
 if m: cfg[m.group(1)]=m.group(2).strip('"')
def f(k): return float(cfg[k])
def foam_header(cls,obj): return f'''FoamFile\n{{\n    format ascii;\n    class {cls};\n    object {obj};\n}}\n'''
case=root/'runs'/mode
if case.exists(): shutil.rmtree(case)
for d in ['0','constant/triSurface','system']: (case/d).mkdir(parents=True,exist_ok=True)
# Place runner fixed at hip x=0; STL geometry remains unaltered in published geometry.
shutil.copy(root/'geometry/runner_female.stl',case/'constant/triSurface/runner.stl')
# Transform STL with OpenFOAM utility later (binary-safe); these command records are run by Allrun.
if mode!='alone': shutil.copy(root/'geometry/pacer_male.stl',case/'constant/triSurface/pacerSource.stl')
if mode=='pair': shutil.copy(root/'geometry/pacer_male.stl',case/'constant/triSurface/pacer2Source.stl')
# block divisions at requested approximate base size
nx=round((f('XMAX')-f('XMIN'))/f('BASE_DX')); ny=round((f('YMAX')-f('YMIN'))/f('BASE_DX')); nz=round(f('ZMAX')/f('BASE_DX'))
x=max(nx,1);ny=max(ny,1);nz=max(nz,1)
x0,x1,y0,y1,z1=[f(k) for k in ('XMIN','XMAX','YMIN','YMAX','ZMAX')]
(case/'system/blockMeshDict').write_text(foam_header('dictionary','blockMeshDict')+f'''convertToMeters 1;\nvertices\n(\n ({x0} {y0} 0) ({x1} {y0} 0) ({x1} {y1} 0) ({x0} {y1} 0)\n ({x0} {y0} {z1}) ({x1} {y0} {z1}) ({x1} {y1} {z1}) ({x0} {y1} {z1})\n);\nblocks (hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1));\nedges ();\nboundary\n(\n outlet {{type patch; faces ((0 4 7 3));}}\n inlet {{type patch; faces ((1 2 6 5));}}\n sides {{type symmetry; faces ((0 1 5 4)(3 7 6 2));}}\n ground {{type wall; faces ((0 3 2 1));}}\n top {{type symmetry; faces ((4 5 6 7));}}\n);\n''')
geom='''runner.stl { type triSurfaceMesh; name runner; }\n'''
refs=f'''runner {{ level ({int(f('SURFACE_MIN_LEVEL'))} {int(f('SURFACE_MAX_LEVEL'))}); patchInfo {{ type wall; }} }}\n'''
layers='''runner { nSurfaceLayers 0; }\n'''
if mode!='alone':
 geom += 'pacer.stl { type triSurfaceMesh; name pacer; }\n'
 refs += f"pacer {{ level ({int(f('SURFACE_MIN_LEVEL'))} {int(f('SURFACE_MAX_LEVEL'))}); patchInfo {{ type wall; }} }}\n"
 layers += 'pacer { nSurfaceLayers 0; }\n'
if mode=='pair':
 geom += 'pacer2.stl { type triSurfaceMesh; name pacer2; }\n'
 refs += f"pacer2 {{ level ({int(f('SURFACE_MIN_LEVEL'))} {int(f('SURFACE_MAX_LEVEL'))}); patchInfo {{ type wall; }} }}\n"
 layers += 'pacer2 { nSurfaceLayers 0; }\n'
# Boxes are identical around the runner in all modes.
(case/'system/snappyHexMeshDict').write_text(foam_header('dictionary','snappyHexMeshDict')+f'''castellatedMesh true; snap true; addLayers false;\ngeometry\n{{\n{geom} corridor {{type searchableBox; min ({f('CORRIDOR_XMIN')} {f('CORRIDOR_YMIN')} 0); max ({f('CORRIDOR_XMAX')} {f('CORRIDOR_YMAX')} {f('CORRIDOR_ZMAX')});}}\n wake {{type searchableBox; min ({f('WAKE_XMIN')} {f('WAKE_YMIN')} {f('WAKE_ZMIN')}); max ({f('WAKE_XMAX')} {f('WAKE_YMAX')} {f('WAKE_ZMAX')});}}\n}}\ncastellatedMeshControls\n{{\n maxLocalCells 1800000; maxGlobalCells 6000000; minRefinementCells 0; nCellsBetweenLevels 2;\n features (); refinementSurfaces {{ {refs} }}\n resolveFeatureAngle 35;\n refinementRegions\n {{ corridor {{mode inside; levels ((1e15 {int(f('CORRIDOR_LEVEL'))}));}} wake {{mode inside; levels ((1e15 {int(f('WAKE_LEVEL'))}));}} }}\n locationInMesh (3.5 2.5 3.0); allowFreeStandingZoneFaces true;\n}}\nsnapControls {{nSmoothPatch 3; tolerance 2.0; nSolveIter 40; nRelaxIter 5; nFeatureSnapIter 0; implicitFeatureSnap false; explicitFeatureSnap false; multiRegionFeatureSnap false;}}\naddLayersControls {{relativeSizes true; layers {{ {layers} }} expansionRatio 1.2; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 20;}}\nmeshQualityControls {{#include "meshQualityDict"}}\nmergeTolerance 1e-6;\n''')
# Fields
U=-f('UINF'); k=1.5*(f('TURB_INTENSITY')*f('UINF'))**2; omega=(k**0.5)/(0.09**0.25*f('TURB_LENGTH'))
figs=['runner']+([] if mode=='alone' else ['pacer'])+([] if mode!='pair' else ['pacer2'])
wallU='\n'.join(f'    {p} {{type noSlip;}}' for p in figs)
wallK='\n'.join(f'    {p} {{type kqRWallFunction; value uniform {k};}}' for p in figs)
wallO='\n'.join(f'    {p} {{type omegaWallFunction; value uniform {omega};}}' for p in figs)
wallNut='\n'.join(f'    {p} {{type nutkWallFunction; value uniform 0;}}' for p in figs)
(case/'0/U').write_text(foam_header('volVectorField','U')+f'''dimensions [0 1 -1 0 0 0 0]; internalField uniform ({U} 0 0); boundaryField {{ inlet {{type fixedValue; value uniform ({U} 0 0);}} outlet {{type inletOutlet; inletValue uniform ({U} 0 0); value uniform ({U} 0 0);}} sides {{type symmetry;}} top {{type symmetry;}} ground {{type movingWallVelocity; value uniform ({U} 0 0);}}\n{wallU}\n}}\n''')
(case/'0/p').write_text(foam_header('volScalarField','p')+'''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField { inlet {type zeroGradient;} outlet {type fixedValue; value uniform 0;} sides {type symmetry;} top {type symmetry;} ground {type zeroGradient;} "(runner|pacer|pacer2)" {type zeroGradient;} }\n''')
(case/'0/k').write_text(foam_header('volScalarField','k')+f'''dimensions [0 2 -2 0 0 0 0]; internalField uniform {k}; boundaryField {{inlet {{type fixedValue; value uniform {k};}} outlet {{type inletOutlet; inletValue uniform {k}; value uniform {k};}} sides {{type symmetry;}} top {{type symmetry;}} ground {{type kqRWallFunction; value uniform {k};}}\n{wallK}\n}}\n''')
(case/'0/omega').write_text(foam_header('volScalarField','omega')+f'''dimensions [0 0 -1 0 0 0 0]; internalField uniform {omega}; boundaryField {{inlet {{type fixedValue; value uniform {omega};}} outlet {{type inletOutlet; inletValue uniform {omega}; value uniform {omega};}} sides {{type symmetry;}} top {{type symmetry;}} ground {{type omegaWallFunction; value uniform {omega};}}\n{wallO}\n}}\n''')
(case/'0/nut').write_text(foam_header('volScalarField','nut')+f'''dimensions [0 2 -1 0 0 0 0]; internalField uniform 0; boundaryField {{inlet {{type calculated; value uniform 0;}} outlet {{type calculated; value uniform 0;}} sides {{type symmetry;}} top {{type symmetry;}} ground {{type nutkWallFunction; value uniform 0;}}\n{wallNut}\n}}\n''')
(case/'constant/physicalProperties').write_text(foam_header('dictionary','physicalProperties')+f'''viscosityModel constant;\nnu {f('NU')};\n''')
(case/'constant/momentumTransport').write_text(foam_header('dictionary','momentumTransport')+'''simulationType RAS; RAS {model kOmegaSSTSAS; turbulence on; printCoeffs on; delta cubeRootVol; cubeRootVolCoeffs { deltaCoeff 1; }}\n''')
(case/'constant/transportProperties').write_text(foam_header('dictionary','transportProperties')+f'''transportModel Newtonian;\nnu {f('NU')};\n''')
(case/'constant/turbulenceProperties').write_text(foam_header('dictionary','turbulenceProperties')+'''simulationType RAS; RAS {RASModel kOmegaSSTSAS; turbulence on; printCoeffs on; delta cubeRootVol; cubeRootVolCoeffs { deltaCoeff 1; }}\n''')
# function objects. Forces output raw N with rhoInf, plus coefficients normalized consistently.
force_blocks=''
for p in figs:
 force_blocks+=f'''\nforceCoeffs_{p}\n{{ type forceCoeffs; libs (forces); patches ({p}); writeControl timeStep; writeInterval 1; rho rhoInf; rhoInf {f('RHO')}; CofR (0 0 0); dragDir (-1 0 0); liftDir (0 0 1); pitchAxis (0 1 0); magUInf {f('UINF')}; lRef {f('LREF')}; Aref {f('AREF')}; log true; }}\n'''
(case/'system/controlDict').write_text(foam_header('dictionary','controlDict')+f'''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {f('END_TIME')}; deltaT {f('DT0')}; writeControl adjustableRunTime; writeInterval {f('END_TIME')}; purgeWrite 0; writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 7; runTimeModifiable true; adjustTimeStep true; maxCo {f('MAX_CO')}; maxDeltaT {f('MAX_DT')}; functions\n{{\n{force_blocks}\nplanes\n{{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {f('SAMPLE_DT')}; surfaceFormat vtk; fields (U p); interpolationScheme cellPoint; surfaces\n( torsoHorizontal {{type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{point (0 0 {f('TORSO_PLANE_Z')}); normal (0 0 1);}} interpolate true;}} centreVertical {{type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{point (0 0 0); normal (0 1 0);}} interpolate true;}} ); }}\n}}\n''')
(case/'system/fvSchemes').write_text(foam_header('dictionary','fvSchemes')+'''ddtSchemes {default backward;} gradSchemes {default cellLimited Gauss linear 1;} divSchemes {default none; div(phi,U) bounded Gauss LUST grad(U); div(phi,k) bounded Gauss limitedLinear 1; div(phi,omega) bounded Gauss limitedLinear 1; div((nuEff*dev2(T(grad(U))))) Gauss linear;} laplacianSchemes {default Gauss linear limited 0.5;} interpolationSchemes {default linear;} snGradSchemes {default limited 0.5;} wallDist {method meshWave;}\n''')
(case/'system/fvSolution').write_text(foam_header('dictionary','fvSolution')+'''solvers {p {solver GAMG; tolerance 1e-6; relTol 0.05; smoother GaussSeidel;} pFinal {$p; relTol 0;} "(U|k|omega)" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1;} "(U|k|omega)Final" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0;}} PIMPLE {momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 1; pRefCell 0; pRefValue 0;} relaxationFactors {equations {".*" 1;}}\n''')
(case/'system/decomposeParDict').write_text(foam_header('dictionary','decomposeParDict')+f'''numberOfSubdomains {int(f('NPROCS'))}; method scotch;\n''')
# loose standard quality thresholds
(case/'system/meshQualityDict').write_text('''maxNonOrtho 70; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-18; minTetQuality 1e-20; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.02; minVolRatio 0.01; minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75; relaxed {maxNonOrtho 75;}\n''')
print(case)
