"""Build both run meshes in runs/mesh/.

    python3 scripts/build.py

A background of 0.16 m cubes over the domain (blockMesh), refined by one serial castellated
snappyHexMesh to 0.08 m round the car and 0.04 m over the car and the door's swing, written
in runs/mesh/base/. For each run the car's solid cells (scripts/common.py, by cell centre) are
removed with topoSet and subsetMesh, the cut faces are sorted into patches with createPatch, the
head boxes, rows and cabin are written as cell zones and the openings as face zones on the side
walls' inner planes (y = -0.72 and 0.72, positive into the cabin), and checkMesh is run, plain
(log.checkMesh) and with -allTopology -allGeometry (log.checkMesh.extended). Writes
runs/mesh/<run>/mesh.json and mesh_arrays.npz, which prepare.py reads.
"""
from common import *
base=ROOT/'mesh'/'base'
for f in ['fvSchemes','fvSolution']:
 write(base/'system'/f,(TEMPLATE/'system'/f).read_text())
write(base/'system/controlDict',header('controlDict')+'''application buoyantPimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime 60; deltaT .0001;
writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 12; writeCompression off; runTimeModifiable false;
''')
write(base/'system/blockMeshDict',header('blockMeshDict')+'''scale 1;
vertices
(
(-2.56 -2.88 0)
(7.52 -2.88 0)
(7.52 3.84 0)
(-2.56 3.84 0)
(-2.56 -2.88 3.52)
(7.52 -2.88 3.52)
(7.52 3.84 3.52)
(-2.56 3.84 3.52)
);
blocks (hex (0 1 2 3 4 5 6 7) (63 42 22) simpleGrading (1 1 1));
edges ();
boundary
(
ground {type wall; faces ((0 3 2 1));}
open {type patch; faces ((0 4 7 3) (1 2 6 5) (0 1 5 4) (3 7 6 2) (4 5 6 7));}
);
mergePatchPairs ();
''')
write(base/'system/snappyHexMeshDict',header('snappyHexMeshDict')+'''castellatedMesh true; snap false; addLayers false;
geometry
{
car {type searchableBox; min (-.08 -1.16 .08); max (5.00 1.16 1.52);}
swing {type searchableBox; min (1.88 .92 .16); max (3.04 2.04 1.40);}
near {type searchableBox; min (-.56 -1.64 0); max (5.52 2.60 2.24);}
}
castellatedMeshControls
{
maxLocalCells 1500000; maxGlobalCells 2000000; minRefinementCells 0; maxLoadUnbalance .1; nCellsBetweenLevels 2;
features (); refinementSurfaces {}; resolveFeatureAngle 30;
refinementRegions
{
car {mode inside; levels ((1e15 2));}
swing {mode inside; levels ((1e15 2));}
near {mode inside; levels ((1e15 1));}
}
locationInMesh (-2 0 2); allowFreeStandingZoneFaces true;
}
'''+QUALITY)
if not (base/'constant/polyMesh/points').exists():
 run('blockMesh',base);run('snappyHexMesh -overwrite',base)
_,_,_,_,_,_,C,V=readmesh(base)
print('background refined cells',len(C),flush=True)
for name in ['fourWindows','doorFan']:
 case=ROOT/'mesh'/name
 shutil.copytree(base,case,dirs_exist_ok=True)
 ids=np.where(~solids(C,name))[0]
 write(case/'system/topoSetDict',header('topoSetDict')+'actions\n(\n{name fluid; type cellSet; action new; source labelToCell; value\n'+listfoam(ids)+';}\n);\n')
 run('topoSet',case);run('subsetMesh fluid -overwrite',case)
 _,_,owner,nei,cf,sf,cc,vv=readmesh(case)
 nb=len(nei);faces=np.arange(nb,len(owner));c=cf[faces];n=sf[faces]/np.linalg.norm(sf[faces],axis=1)[:,None]
 # a point just across each wall face, inside the removed solid, says which solid it belongs to
 across=c+n*.002
 pn=np.full(len(faces),'bodyExterior',dtype=object)
 pn[c[:,2]<1e-7]='ground'
 domain=(abs(c[:,0]+2.56)<1e-7)|(abs(c[:,0]-7.52)<1e-7)|(abs(c[:,1]+2.88)<1e-7)|(abs(c[:,1]-3.84)<1e-7)|(abs(c[:,2]-3.52)<1e-7)
 pn[domain]='open'
 # every face bounding cabin air, the steps of both raked glasses included, is inside the cabin;
 # the reveals across the wall's thickness are bodyExterior
 interior=cabin(cc[owner[faces]],.72001)
 pn[interior]='cabinInterior'
 pn[interior&dash(across)]='dashboard'
 pn[interior&seats(across)]='seats'
 entries=[]
 for p in ['ground','open','dashboard','seats','cabinInterior','bodyExterior']:
  ids=faces[pn==p];setfile(case,p+'Faces',ids)
  entries.append('{name '+p+'; patchInfo {type '+('patch' if p=='open' else 'wall')+';} constructFrom set; set '+p+'Faces;}')
 write(case/'system/createPatchDict',header('createPatchDict')+'pointSync false; patches\n(\n'+'\n'.join(entries)+'\n);\n')
 run('createPatch -overwrite',case)
 # the zones are written from the final mesh, so that the face labels and orientation are exact
 _,_,owner,nei,cf,sf,cc,vv=readmesh(case)
 heads={}
 for j,(a,b) in enumerate([(-.52,-.28),(.28,.52),(-.56,-.32),(-.12,.12),(.32,.56)]):
  x0,x1=(2.52,2.72) if j<2 else (3.4,3.6)
  heads['head'+str(j+1)]=np.where(box(cc,(x0,a,1.04),(x1,b,1.24)))[0]
 zones=dict(heads);zones['row1']=np.concatenate(list(heads.values())[:2]);zones['row2']=np.concatenate(list(heads.values())[2:]);zones['heads']=np.concatenate(list(heads.values()));zones['cabin']=np.where(cabin(cc))[0]
 write(case/'constant/polyMesh/cellZones',header('cellZones','regIOobject')+str(len(zones))+'\n(\n'+''.join(n+'\n{type cellZone; cellLabels List<label>\n'+listfoam(ids)+';}\n' for n,ids in zones.items())+')\n')
 openings=[('rearLeft',-.72,2.96,3.60,.96,1.32)]
 if name=='fourWindows':openings += [('frontLeft',-.72,2.16,2.84,.96,1.32),('frontRight',.72,2.16,2.84,.96,1.32),('rearRight',.72,2.96,3.60,.96,1.32)]
 else:openings += [('doorAperture',.72,1.96,2.96,.24,1.32)]
 fzones=[];areas={}
 for n,y,a,b,z0,z1 in openings:
  ids=np.where((abs(cf[:len(nei),1]-y)<1e-7)&box(cf[:len(nei)],(a,y-1e-6,z0),(b,y+1e-6,z1))&(abs(sf[:len(nei),1])>1e-8))[0]
  flip=(sf[ids,1]*(1 if y<0 else -1)<0).astype(int)
  areas[n]=float(np.linalg.norm(sf[ids],axis=1).sum())
  fzones.append(n+'\n{type faceZone; faceLabels List<label>\n'+listfoam(ids)+'; flipMap List<bool>\n'+listfoam(flip)+';}\n')
 write(case/'constant/polyMesh/faceZones',header('faceZones','regIOobject')+str(len(fzones))+'\n(\n'+''.join(fzones)+')\n')
 run('checkMesh',case)
 run('checkMesh -allTopology -allGeometry',case,'log.checkMesh.extended')
 text=(case/'constant/polyMesh/boundary').read_text();patches={}
 for n,body in re.findall(r'(\w+)\s*\{([^{}]+)\}',text):
  if 'nFaces' not in body:continue
  start=int(re.search(r'startFace\s+(\d+)',body)[1]);nn=int(re.search(r'nFaces\s+(\d+)',body)[1]);patches[n]=float(np.linalg.norm(sf[start:start+nn],axis=1).sum())
 audit=dict(cells=len(cc),cabin_volume=float(vv[zones['cabin']].sum()),patch_areas=patches,opening_areas=areas,head_zones={n:dict(cells=len(ids),volume=float(vv[ids].sum())) for n,ids in heads.items()})
 write(case/'mesh.json',json.dumps(audit,indent=2));print(name,audit,flush=True)
 np.savez_compressed(case/'mesh_arrays.npz',C=cc,V=vv,cf=cf,sf=sf,owner=owner,neighbour=nei)
