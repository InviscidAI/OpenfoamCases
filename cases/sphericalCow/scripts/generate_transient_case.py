#!/usr/bin/env python3
import json, math, shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; mode=sys.argv[1]
if mode not in ('cow','sphere','isolated','cow-floating','sphere-floating'): raise SystemExit('mode: cow|sphere|isolated|cow-floating|sphere-floating')
c=json.load(open(root/'config.json')); g=json.load(open(root/'geometry/geometry.json'))
case=root/'runs'/mode
if case.exists(): shutil.rmtree(case)
for d in ('0','constant/triSurface','system'): (case/d).mkdir(parents=True,exist_ok=True)
floating=mode in ('cow-floating','sphere-floating')
is_cow=mode in ('cow','cow-floating')
if mode=='cow': geom='cow_grounded.stl'
elif mode=='cow-floating': geom='cow_floating.stl'
elif mode in ('isolated','sphere-floating'): geom='isolated.stl'
else: geom='sphere.stl'
shutil.copy2(root/'geometry'/geom,case/'constant/triSurface/body.stl')
# Ship the exact public-domain source and licence in every published case.
shutil.copy2(root/'geometry/spot/spot_triangulated.obj',case/'constant/triSurface/spot_triangulated.obj')
shutil.copy2(root/'geometry/spot/README.txt',case/'constant/triSurface/SPOT_README.txt')
D=g['equal_volume_sphere_diameter_m']; U=c['Uinf']; nu=c['nu']; rho=c['rho']
Aref=g['reference_frontal_area_m2'] if is_cow else math.pi*D**2/4
lref=g['measurements_m']['trunk_length_m'] if is_cow else D
xmin,xmax=[c['domain'][x] for x in ('xmin','xmax')]; ymin,ymax=[c['domain'][x] for x in ('ymin','ymax')]; zmin,zmax=[c['domain'][x] for x in ('zmin','zmax')]
nx=round((xmax-xmin)/c['baseCell']); ny=round((ymax-ymin)/c['baseCell']); nz=round((zmax-zmin)/c['baseCell'])
H='FoamFile\n{\n format ascii;\n class dictionary;\n object %s;\n}\n'
def wr(p,s): (case/p).write_text(s)
wr('system/blockMeshDict',H%'blockMeshDict'+f'''scale 1;
vertices
(
 ({xmin} {ymin} {zmin})
 ({xmax} {ymin} {zmin})
 ({xmax} {ymax} {zmin})
 ({xmin} {ymax} {zmin})
 ({xmin} {ymin} {zmax})
 ({xmax} {ymin} {zmax})
 ({xmax} {ymax} {zmax})
 ({xmin} {ymax} {zmax})
);
blocks
(
 hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);
edges ();
boundary
(
 inlet {{ type patch; faces ((0 4 7 3)); }}
 outlet {{ type patch; faces ((1 2 6 5)); }}
 sides {{ type symmetry; faces ((0 1 5 4) (3 7 6 2)); }}
 ground {{ type {'symmetry' if (mode=='isolated' or floating) else 'wall'}; faces ((0 3 2 1)); }}
 top {{ type symmetry; faces ((4 5 6 7)); }}
);
''')
# Refinement follows body and downstream wake. Isolated sphere center is z=3.
boxmin='(-2 -1.5 1.5)' if (mode=='isolated' or floating) else '(-2 -1.5 0)'
boxmax='(8 1.5 4.5)' if (mode=='isolated' or floating) else '(8 1.5 2.5)'
implicit='false' if is_cow else 'true'
# Floating cases share cow-sized volume/surface refinement. Spot uses two layers
# because three created restrictive local cells; the sphere retains three complete layers.
layers=(2 if mode=='cow-floating' else c['nLayers']) if floating else (2 if mode=='cow' else (0 if mode=='sphere' else c['nLayers']))
loc='(5 0 0.8)' if mode!='isolated' else '(5 0 0.8)'
wr('system/snappyHexMeshDict',H%'snappyHexMeshDict'+f'''castellatedMesh true;
snap true;
addLayers true;
geometry
{{
 body.stl {{ type triSurfaceMesh; name body; }}
 wake {{ type searchableBox; min {boxmin}; max {boxmax}; }}
}}
castellatedMeshControls
{{
 maxLocalCells 1200000;
 maxGlobalCells 5000000;
 minRefinementCells 0;
 nCellsBetweenLevels 3;
 features ();
 refinementSurfaces {{ body {{ level ({c['surfaceMinLevel']} {c['surfaceMaxLevel']}); patchInfo {{ type wall; }} }} }}
 resolveFeatureAngle 32;
 refinementRegions {{ wake {{ mode inside; levels ((1e15 {c['wakeLevel']})); }} }}
 locationInMesh {loc};
 allowFreeStandingZoneFaces true;
}}
snapControls
{{
 nSmoothPatch 5; tolerance 2.0; nSolveIter 60; nRelaxIter 5;
 nFeatureSnapIter 15; implicitFeatureSnap {implicit}; explicitFeatureSnap false;
 multiRegionFeatureSnap false;
}}
addLayersControls
{{
 relativeSizes true;
 layers {{ body {{ nSurfaceLayers {layers}; }} }}
 expansionRatio {c['expansionRatio']}; finalLayerThickness 0.45; minThickness 0.08; nGrow 0;
 featureAngle 50; nRelaxIter 5; nSmoothSurfaceNormals 3; nSmoothNormals 5;
 nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3;
 minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50;
}}
meshQualityControls
{{
 #includeEtc "caseDicts/mesh/generation/meshQualityDict.cfg"
 relaxed {{ maxNonOrtho 75; }}
}}
mergeTolerance 1e-6;
''')
k=1.5*(c['turbulenceIntensity']*U)**2; om=math.sqrt(k)/(0.09**0.25*c['turbulenceLengthScale'])
iso=(mode=='isolated' or floating)
wr('0/U',H%'U'+f'''dimensions [0 1 -1 0 0 0 0];
internalField uniform ({0 if floating else U} 0 0);
boundaryField
{{
 inlet {{ type fixedValue; value uniform ({U} 0 0); }}
 outlet {{ type inletOutlet; inletValue uniform ({U} 0 0); value uniform ({U} 0 0); }}
 sides {{ type symmetry; }}
 top {{ type symmetry; }}
 ground {{ type {'symmetry' if iso else 'noSlip'}; }}
 body {{ type noSlip; }}
}}
''')
wr('0/p',H%'p'+f'''dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{{
 inlet {{ type zeroGradient; }}
 outlet {{ type fixedValue; value uniform 0; }}
 sides {{ type symmetry; }}
 top {{ type symmetry; }}
 ground {{ type {'symmetry' if iso else 'zeroGradient'}; }}
 body {{ type zeroGradient; }}
}}
''')
def turb(name,val,wall):
    dim='[0 2 -2 0 0 0 0]' if name=='k' else '[0 0 -1 0 0 0 0]'
    wr('0/'+name,H%name+f'''dimensions {dim};
internalField uniform {val};
boundaryField
{{
 inlet {{ type fixedValue; value uniform {val}; }}
 outlet {{ type inletOutlet; inletValue uniform {val}; value uniform {val}; }}
 sides {{ type symmetry; }}
 top {{ type symmetry; }}
 ground {{ type {'symmetry' if iso else wall}; value uniform {val}; }}
 body {{ type {wall}; value uniform {val}; }}
}}
''')
turb('k',k,'kqRWallFunction'); turb('omega',om,'omegaWallFunction')
wr('0/nut',H%'nut'+f'''dimensions [0 2 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{{
 inlet {{ type calculated; value uniform 0; }}
 outlet {{ type calculated; value uniform 0; }}
 sides {{ type symmetry; }}
 top {{ type symmetry; }}
 ground {{ type {'symmetry' if iso else 'nutkWallFunction'}; value uniform 0; }}
 body {{ type nutkWallFunction; value uniform 0; }}
}}
''')
wr('constant/transportProperties',H%'transportProperties'+f'''transportModel Newtonian;
nu [0 2 -1 0 0 0 0] {nu};
''')
model='kOmegaSSTSAS' if floating else 'kOmegaSST'
delta_line=' delta cubeRootVol; cubeRootVolCoeffs { deltaCoeff 1; }' if floating else ''
wr('constant/turbulenceProperties',H%'turbulenceProperties'+'''simulationType RAS;
RAS
{
 RASModel %s;
%s
 turbulence on;
 printCoeffs on;
}
''' % (model,delta_line))
mom_scheme='LUST' if floating else 'linearUpwind'
turb_scheme='limitedLinear 1' if floating else 'upwind'
wr('system/fvSchemes',H%'fvSchemes'+'''ddtSchemes { default backward; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes
{
 default none;
 div(phi,U) bounded Gauss %s grad(U);
 div(phi,k) bounded Gauss %s;
 div(phi,omega) bounded Gauss %s;
 div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''' % (mom_scheme,turb_scheme,turb_scheme))
wr('system/fvSolution',H%'fvSolution'+'''solvers
{
 p { solver GAMG; tolerance 1e-6; relTol 0.05; smoother GaussSeidel; }
 pFinal { $p; tolerance 1e-4; relTol 0; }
 U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.05; }
 UFinal { $U; relTol 0; }
 "(k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.05; }
 kFinal { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0; }
 omegaFinal { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0; }
}
PIMPLE
{
 momentumPredictor yes;
 nOuterCorrectors 1;
 nCorrectors 2;
 nNonOrthogonalCorrectors 0;
 correctPhi yes;
}
relaxationFactors { equations { ".*" 1; } }
''')
mid=3.0 if iso else (D/2-c['sphereEmbed'] if mode=='sphere' else (g['measurements_m']['chest_floor_height_m']+g['measurements_m']['rump_height_m'])/2)
wr('system/controlDict',H%'controlDict'+f'''application pimpleFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime {c['settleEnd']+c['sampleWindow']};
deltaT {c['initialDeltaT']};
adjustTimeStep yes;
maxCo {1.0 if floating else c['maxCo']};
maxDeltaT {c['maxDeltaT']};
writeControl adjustableRunTime;
writeInterval 5;
purgeWrite 0;
writeFormat binary;
writePrecision 8;
runTimeModifiable true;
functions
{{
 forceCoeffs
 {{
  type forceCoeffs;
  libs (forces);
  patches (body);
  writeControl timeStep;
  writeInterval 1;
  rho rhoInf;
  rhoInf {rho};
  CofR (0 0 {mid});
  liftDir (0 0 1);
  dragDir (1 0 0);
  pitchAxis (0 1 0);
  magUInf {U};
  lRef {lref};
  Aref {Aref};
 }}
 residuals
 {{
  type solverInfo;
  libs (utilityFunctionObjects);
  fields (p U k omega);
  writeControl timeStep;
  writeInterval 1;
 }}
 planes
 {{
  type surfaces;
  libs (sampling);
  enabled {'true' if floating or not iso else 'false'};
  timeStart {c['settleEnd']};
  writeControl adjustableRunTime;
  writeInterval {1/c['sampleRateHz']};
  surfaceFormat vtk;
  fields (U p);
  surfaces
  {{
   vertical {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 {mid}); normal (0 1 0); }} interpolate true; }}
   horizontal {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 {mid}); normal (0 0 1); }} interpolate true; }}
  }}
 }}
}}
''')
wr('system/decomposeParDict',H%'decomposeParDict'+f'''numberOfSubdomains {c['mpiRanksPerCase']};
method scotch;
''')
for fld,cls in [('U','volVectorField'),('p','volScalarField'),('k','volScalarField'),('omega','volScalarField'),('nut','volScalarField')]:
    q=case/'0'/fld; q.write_text(q.read_text().replace('class dictionary','class '+cls,1))
info={'mode':mode,'cellsBackground':[nx,ny,nz],'Aref_m2':Aref,'lref_m':lref,
      'Re':U*lref/nu,'midPlaneZ_m':mid,'meshNominalMinSurface_m':c['baseCell']/2**c['surfaceMaxLevel']}
wr('caseInfo.json',json.dumps(info,indent=2)); print(case)
