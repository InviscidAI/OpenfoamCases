#!/usr/bin/env python3
"""Rebuild the OpenFOAM v2512 PC-case air mesh from the unchanged local geometry STLs.

    python3 rebuild_mesh.py           # geometry/ -> mesh/ (positive, negative, even)
    python3 rebuild_mesh.py viewer    # geometry/ with geometry/viewer/ over it -> mesh/viewer/
"""
from pathlib import Path
import os, sys, shutil, subprocess, json, tempfile
import numpy as np
import pyvista as pv
variant=sys.argv[1] if len(sys.argv)>1 else ''
if variant not in ('','viewer'): raise SystemExit('usage: rebuild_mesh.py [viewer]')
HERE=Path(__file__).resolve().parent
GEOM=HERE.parent/'geometry'
if not (GEOM/'solids').is_dir() or not (GEOM/'faces').is_dir(): raise SystemExit('Missing ../geometry/solids or ../geometry/faces')
CASE=HERE/variant if variant else HERE
if variant:
    # The variant's PC: the shared geometry with the variant's own files laid over it.
    merged=Path(tempfile.mkdtemp(prefix='pcCase_geometry_'))
    for sub in ('solids','faces'):
        (merged/sub).mkdir()
        for p in (GEOM/sub).glob('*.stl'): shutil.copy2(p,merged/sub/p.name)
        for p in (GEOM/variant/sub).glob('*.stl'): shutil.copy2(p,merged/sub/p.name)
    shutil.copy2(GEOM/variant/'dimensions_mm.json',merged/'dimensions_mm.json')
    GEOM=merged
CASE.mkdir(exist_ok=True)
os.chdir(CASE)
def run(args):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run(list(map(str,args)),check=True)
def write_obj(path, groups):
    off=0
    with open(path,'w') as f:
        for name,mesh in groups:
            mesh=mesh.triangulate(); f.write(f'g {name}\n')
            for x,y,z in mesh.points: f.write(f'v {x:.12g} {y:.12g} {z:.12g}\n')
            for a,b,c in mesh.faces.reshape(-1,4)[:,1:]: f.write(f'f {a+1+off} {b+1+off} {c+1+off}\n')
            off += mesh.n_points
def disk_mesh(c,axis,r,N=128):
    c=np.array(c,float); pts=[c]
    for i in range(N):
        a=2*np.pi*i/N; q=c.copy(); ids=[j for j in range(3) if j!=axis]
        q[ids[0]]+=r*np.cos(a); q[ids[1]]+=r*np.sin(a); pts.append(q)
    faces=[]
    for i in range(N): faces += [3,0,1+i,1+(i+1)%N]
    return pv.PolyData(np.array(pts),np.array(faces))

# OpenFOAM dictionaries (metres)
Path("system").mkdir(exist_ok=True); Path("0").mkdir(exist_ok=True)
Path("system/controlDict").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object controlDict; }\napplication simpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT 1; writeControl timeStep; writeInterval 1; runTimeModifiable true;\n')
Path("system/fvSchemes").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object fvSchemes; }\nddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; }\n')
Path("system/fvSolution").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object fvSolution; }\nsolvers {} PIMPLE {} relaxationFactors {}\n')
Path("system/blockMeshDict").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object blockMeshDict; }\nscale 1;\nvertices ((0 0 0)(0.44 0 0)(0.44 0.46 0)(0 0.46 0)(0 0 0.21)(0.44 0 0.21)(0.44 0.46 0.21)(0 0.46 0.21));\nblocks (hex (0 1 2 3 4 5 6 7) (55 58 26) simpleGrading (1 1 1)); edges ();\nboundary (walls { type wall; faces ((0 4 7 3)(1 2 6 5)(0 1 5 4)(3 7 6 2)(0 3 2 1)(4 5 6 7)); }); mergePatchPairs ();\n')
Path("system/snappyHexMeshDict").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object snappyHexMeshDict; }\ncastellatedMesh true; snap true; addLayers false;\ngeometry { upperRefine { type searchableBox; min (0 0.1 0); max (0.44 0.46 0.18); }  cpu_cooler { type triSurfaceMesh; file "cpu_cooler.stl"; name cpu_cooler; }\n gpu { type triSurfaceMesh; file "gpu.stl"; name gpu; }\n io_stack { type triSurfaceMesh; file "io_stack.stl"; name io_stack; }\n motherboard { type triSurfaceMesh; file "motherboard.stl"; name motherboard; }\n psu_shroud { type triSurfaceMesh; file "psu_shroud.stl"; name psu_shroud; }\n ram { type triSurfaceMesh; file "ram.stl"; name ram; } }\ncastellatedMeshControls { maxLocalCells 1000000; maxGlobalCells 1500000; minRefinementCells 0; maxLoadUnbalance 0.10; nCellsBetweenLevels 2; features (); refinementSurfaces {  cpu_cooler { level (1 1); patchInfo { type wall; } }\n gpu { level (1 1); patchInfo { type wall; } }\n io_stack { level (1 1); patchInfo { type wall; } }\n motherboard { level (1 1); patchInfo { type wall; } }\n psu_shroud { level (1 1); patchInfo { type wall; } }\n ram { level (1 1); patchInfo { type wall; } } } resolveFeatureAngle 30; refinementRegions { upperRefine { mode inside; levels ((1e15 1)); } } locationInMesh (0.05 0.15 0.10); allowFreeStandingZoneFaces true; }\nsnapControls { nSmoothPatch 3; tolerance 2.0; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap true; explicitFeatureSnap false; multiRegionFeatureSnap false; }\naddLayersControls { relativeSizes true; layers {}; expansionRatio 1; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50; }\nmeshQualityControls { #include "meshQualityDict"; relaxed { maxNonOrtho 75; } } mergeTolerance 1e-6;\n')
Path("system/meshQualityDict").write_text('maxNonOrtho 70; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-15; minTetQuality 1e-30; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.02; minVolRatio 0.01; minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75;\n')
Path("system/createPatchDict").write_text('FoamFile\n{ version 2.0; format ascii; class dictionary; object createPatchDict; }\npointSync false;\npatches\n(\n { name walls; patchInfo { type wall; } constructFrom patches; patches (walls cpu_cooler gpu io_stack motherboard psu_shroud ram); }\n);\n')

# Clean only generated mesh products inside this case.
shutil.rmtree('constant/polyMesh',ignore_errors=True); shutil.rmtree('constant/triSurface',ignore_errors=True)
for p in CASE.iterdir():
    if p.is_dir() and p.name not in ('0',) and p.name.replace('.','',1).isdigit(): shutil.rmtree(p)
Path('constant/triSurface').mkdir(parents=True)
for p in (GEOM/'solids').glob('*.stl'): shutil.copy2(p,Path('constant/triSurface')/p.name)
run(['blockMesh']); run(['snappyHexMesh','-overwrite'])
# Named patch helper surfaces retain supplied coordinates; source STLs are never edited.
fd=GEOM/'faces'; names=sorted(p.stem for p in fd.glob('*.stl'))
dev=[n for n in names if not n.startswith('fan_') and not n.startswith('vent_')]
vents=[n for n in names if n.startswith('vent_')]; fans=[n for n in names if n.startswith('fan_')]
write_obj('named_devices.obj',[(n,pv.read(fd/f'{n}.stl')) for n in dev])
write_obj('named_vents.obj',[(n,pv.read(fd/f'{n}.stl')) for n in vents])
write_obj('named_fans.obj',[(n,pv.read(fd/f'{n}.stl')) for n in fans])
d=json.loads((GEOM/'dimensions_mm.json').read_text()); disks=[]
for _,y in d['FRONT_FANS']: disks.append(('walls',disk_mesh((0,y/1000,d['FAN_Z']/1000),0,0.057)))
for _,x in d['TOP_FANS']: disks.append(('walls',disk_mesh((x/1000,d['HEIGHT']/1000,d['FAN_Z']/1000),1,0.067)))
_,y,z=d['REAR_FAN']; disks.append(('walls',disk_mesh((d['DEPTH']/1000,y/1000,z/1000),0,0.057)))
for _,x in d.get('BOTTOM_FANS',[]): disks.append(('walls',disk_mesh((x/1000,d['SHROUD_TOP']/1000,d['FAN_Z']/1000),1,0.057)))
write_obj('fan_footprints_to_walls.obj',disks)
# Priority: devices; vents; full fan disks reset to walls; annuli win last.
for obj in ('named_devices.obj','named_vents.obj','fan_footprints_to_walls.obj','named_fans.obj'):
    shutil.rmtree('1',ignore_errors=True); run(['surfaceToPatch',obj,'-tol','0.001'])
    shutil.rmtree('constant/polyMesh'); shutil.copytree('1/polyMesh','constant/polyMesh')
shutil.rmtree('1',ignore_errors=True)
run(['createPatch','-overwrite'])
with open('checkMesh.log','w') as f: subprocess.run(['checkMesh'],stdout=f,stderr=subprocess.STDOUT,check=True)
if 'Mesh OK.' not in Path('checkMesh.log').read_text(): raise SystemExit('Binding checkMesh did not report Mesh OK')
with open('checkMesh_all.log','w') as f: subprocess.run(['checkMesh','-allGeometry','-allTopology'],stdout=f,stderr=subprocess.STDOUT)
if variant: shutil.rmtree(GEOM,ignore_errors=True)
print('Rebuilt mesh; see checkMesh.log and checkMesh_all.log')
