import os,sys,json,time,subprocess,shutil,re
from pathlib import Path
import numpy as np
# The case folder, its committed inputs, and runs/, where everything is built and solved.
CASE=Path(__file__).resolve().parents[1]
TEMPLATE=CASE/'template'
SCRIPTS=CASE/'scripts'
ROOT=CASE/'runs'
# snappyHexMeshDict's snapping, layer and quality controls, as weldingFumeExtraction's (case 77).
# Castellation only is used here, so only the quality controls act.
QUALITY='''snapControls {nSmoothPatch 3; tolerance 1.5; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap true; explicitFeatureSnap false; multiRegionFeatureSnap true;}
addLayersControls {}
meshQualityControls {maxNonOrtho 65; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-13; minTetQuality 1e-15; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.02; minVolRatio 0.01; minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75;}
writeFlags (scalarLevels);
mergeTolerance 1e-6;
'''
def run(cmd,cwd):
 ROOT.mkdir(exist_ok=True);t=time.monotonic(); name=cmd.split()[0]; log=cwd/('log.'+name)
 print(str(cwd),cmd,flush=True)
 if log.exists():
  j=1
  while log.with_name(log.name+'.previous'+str(j)).exists():j+=1
  shutil.copy(log,log.with_name(log.name+'.previous'+str(j)))
 with open(log,'w') as f: p=subprocess.run(cmd,shell=True,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
 elapsed=time.monotonic()-t
 with open(ROOT/'timing.jsonl','a') as f:f.write(json.dumps(dict(stage=name,case=str(cwd),wall_s=elapsed,exit=p.returncode))+'\n')
 if p.returncode: print(log.read_text()[-6000:],flush=True);raise RuntimeError(cmd)
 print('finished',name,round(elapsed,2),'s',flush=True)
def header(obj,cls='dictionary'):return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'
def box(c,lo,hi,eps=1e-8):return np.all((c>=np.array(lo)-eps)&(c<=np.array(hi)+eps),axis=1)
seatboxes=[]
for yl,yh in [(.12,.72),(-.72,-.12)]:
 seatboxes += [((2.56,yl,.44),(3.04,yh,.80)),((3.04,yl,.44),(3.20,yh,1.40))]
for yl,yh in [(.32,.56),(-.56,-.32)]:seatboxes += [((3.08,yl,1.40),(3.16,yh,1.60))]
for xc,xb,xh,zb,zh in [(3.44,3.96,4.,1.36,1.56),(4.36,4.76,4.8,1.32,1.52)]:
 seatboxes += [((xc,-.84,.44),(xb,.84,.80)),((xb,-.84,.44),(xb+.16,.84,zb))]
 for yl,yh in [(-.64,-.40),(-.12,.12),(.40,.64)]:seatboxes += [((xh,yl,zb),(xh+.08,yh,zh))]
dash=((1.76,-.84,.88),(2.24,.84,1.12))
def cabin(c,wide=.84):
 return box(c,(1.76,-wide,.44),(5.56,wide,1.84)) & ((c[:,2]<=1.12+1e-8)|(c[:,0]>=1.80+(c[:,2]-1.12)*.60/.72-1e-8))
def geometry(c,kind):
 body=box(c,(0,-1.04,.24),(5.76,1.04,1.92)) & ((c[:,2]<=1.12)|(c[:,0]>=1.68+(c[:,2]-1.12)*.68/.80))
 solid=body & ~cabin(c)
 for lo,hi in seatboxes+[dash]:solid |=box(c,lo,hi)
 if kind=='precursor':return solid | cabin(c)
 for name,x,sign in [('frontLeft',2.28,-1),('rearLeft',3.36,-1),('frontRight',2.28,1),('rearRight',3.36,1)]:
  if kind=='fourWindows' or name=='rearLeft':solid &=~box(c,(x,-1.04 if sign<0 else .84,1.20),(x+.76,-.84 if sign<0 else 1.04,1.68))
 if kind=='doorFan':solid &=~box(c,(2.16,.84,.44),(3.20,1.04,1.72))
 return solid

def scalarlist(path):
 s=Path(path).read_text();s=s[s.index('internalField'):]; a=s.index('(');b=s.index(')',a);return np.fromstring(s[a+1:b],sep=' ')
def centers(case):
 run('postProcess -func writeCellCentres -time 0',case)
 return np.column_stack([scalarlist(case/'0'/('C'+d)) for d in 'xyz'])
def mesh_arrays(case):
 p=case/'constant/polyMesh'
 def body(name):
  s=(p/name).read_text();s=s[s.index('}',s.index('FoamFile'))+1:];s=re.sub(r'//[^\n]*','',s).strip();a=s.index('(');return s[a+1:s.rfind(')')]
 pts=np.fromstring(body('points').replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
 face=[np.fromstring(x,sep=' ',dtype=int) for x in re.findall(r'\d+\(([^)]*)\)',body('faces'))]
 owner=np.fromstring(body('owner'),sep=' ',dtype=int);nei=np.fromstring(body('neighbour'),sep=' ',dtype=int)
 fc=np.array([pts[f].mean(axis=0) for f in face]); av=[]
 for f in face:
  a=pts[f];av.append(.5*np.cross(a,np.roll(a,-1,axis=0)).sum(axis=0))
 return pts,face,owner,nei,fc,np.array(av)
def native_volumes(arr):
 C=arr['C'];owner=arr['owner'];nei=arr['neighbour'];q=np.einsum('ij,ij->i',arr['fc'],arr['sf'])
 return (np.bincount(owner,weights=q,minlength=len(C))-np.bincount(nei,weights=q[:len(nei)],minlength=len(C)))/3

def write_set(case,name,ids,cls):
 p=case/'constant/polyMesh/sets';p.mkdir(exist_ok=True)
 (p/name).write_text(header(name,cls)+str(len(ids))+'\n(\n'+'\n'.join(map(str,ids))+'\n)\n')
def setup_background():
 case=ROOT/'mesh/background';(case/'system').mkdir(parents=True,exist_ok=True);(case/'constant').mkdir(exist_ok=True);(case/'0').mkdir(exist_ok=True)
 (case/'system/controlDict').write_text(header('controlDict')+'application buoyantPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 60; deltaT 1e-4; writeControl timeStep; writeInterval 1; writeFormat ascii; writeCompression off; runTimeModifiable false;\n')
 for f in ['fvSchemes','fvSolution']:shutil.copy(TEMPLATE/'system'/f,case/'system'/f)
 verts=[(-7.68,-9.60,0),(13.44,-9.60,0),(13.44,19.20,0),(-7.68,19.20,0),(-7.68,-9.60,9.60),(13.44,-9.60,9.60),(13.44,19.20,9.60),(-7.68,19.20,9.60)]
 (case/'system/blockMeshDict').write_text(header('blockMeshDict')+'scale 1;\nvertices\n(\n'+'\n'.join('(%g %g %g)'%v for v in verts)+'\n);\nblocks\n(\nhex (0 1 2 3 4 5 6 7) (66 90 30) simpleGrading (1 1 1)\n);\nedges (); boundary\n(\nground {type wall; faces ((0 3 2 1));}\ninlet {type patch; faces ((0 1 5 4));}\noutlet {type patch; faces ((3 7 6 2));}\nsides {type symmetry; faces ((0 4 7 3) (1 2 6 5));}\ntop {type symmetry; faces ((4 5 6 7));}\n); mergePatchPairs ();\n')
 quality=QUALITY
 regions=[('cabinFine',(1.68,-1.28,.40),(5.68,1.28,1.92),3),('doorFine',(2.08,1.04,.40),(3.28,2.08,1.80),3),('near',(-.48,-1.68,0),(6.24,2.56,2.40),2),('wake',(-2.56,-3.20,0),(8.32,8.00,4.16),1)]
 text=header('snappyHexMeshDict')+'castellatedMesh true; snap false; addLayers false;\ngeometry\n{\n'
 for n,lo,hi,l in regions:text+=f'{n} {{type searchableBox; min ({" ".join(map(str,lo))}); max ({" ".join(map(str,hi))});}}\n'
 text+='}\ncastellatedMeshControls {maxLocalCells 1000000; maxGlobalCells 2000000; minRefinementCells 0; maxLoadUnbalance .1; nCellsBetweenLevels 2; features (); refinementSurfaces {}; resolveFeatureAngle 30; refinementRegions {\n'
 for n,lo,hi,l in regions:text+=f'{n} {{mode inside; levels ((1e15 {l}));}}\n'
 text+='} locationInMesh (-2 0 2); allowFreeStandingZoneFaces true;}\n'+quality
 (case/'system/snappyHexMeshDict').write_text(text)
 run('blockMesh',case);run('snappyHexMesh -overwrite',case)
 centers(case)
 return case

def build(kind,bg):
 case=ROOT/'mesh'/kind
 if case.exists():shutil.rmtree(case)
 shutil.copytree(bg,case,dirs_exist_ok=True)
 C=np.column_stack([scalarlist(case/'0'/('C'+d)) for d in 'xyz'])
 # Use topoSet to construct an air cellSet from explicit native labels selected by geometry.
 write_set(case,'airSeed',np.flatnonzero(~geometry(C,kind)),'cellSet')
 (case/'system/topoSetDict').write_text(header('topoSetDict')+'actions\n(\n{name air; type cellSet; action new; source cellToCell; set airSeed;}\n);\n')
 run('topoSet',case);run('subsetMesh air -overwrite -patch bodyExterior',case)
 for f in list((case/'0').iterdir()):f.unlink()
 for f in ['cellLevel','pointLevel']:
  for p in [case/'constant'/f,case/'0'/f]:
   if p.exists():p.unlink()
 C=centers(case);pts,faces,owner,nei,fc,sf=mesh_arrays(case)
 interior=np.arange(len(nei),len(owner)); sets={n:[] for n in ['dashboard','seats','cabinInterior']}
 boundary=(case/'constant/polyMesh/boundary').read_text();m=re.search(r'bodyExterior\s*\{[^}]*nFaces\s+(\d+);[^}]*startFace\s+(\d+);',boundary,re.S)
 nf,start=map(int,m.groups());ids=np.arange(start,start+nf);f=fc[ids]
 ds=box(f,*dash);ss=np.zeros(len(f),bool)
 for lo,hi in seatboxes:ss|=box(f,lo,hi)
 ci=cabin(C[owner[ids]])&~ss&~ds
 for n,mask in [('dashboard',ds),('seats',ss&~ds),('cabinInterior',ci)]:write_set(case,n+'Faces',ids[mask],'faceSet')
 (case/'system/createPatchDict').write_text(header('createPatchDict')+'pointSync false; patches\n(\n'+''.join(f'{{name {n}; patchInfo {{type wall;}} constructFrom set; set {n}Faces;}}\n' for n in sets)+');\n')
 run('createPatch -overwrite',case)
 bpath=case/'constant/polyMesh/boundary'; btext=bpath.read_text(); btext=re.sub(r'(bodyExterior\s*\{\s*)type\s+empty;\s*inGroups\s+1\(empty\);',r'\1type wall;\n        inGroups 1(wall);',btext);bpath.write_text(btext)
 C=centers(case);pts,faces,owner,nei,fc,sf=mesh_arrays(case)
 # All sampling zones use internal faces; flip from mesh's owner orientation to cabin-inward.
 openings=[('frontLeft',2.28,-.84,1.2,3.04,1.68,1),('rearLeft',3.36,-.84,1.2,4.12,1.68,1),('frontRight',2.28,.84,1.2,3.04,1.68,-1),('rearRight',3.36,.84,1.2,4.12,1.68,-1)] if kind=='fourWindows' else [('rearLeft',3.36,-.84,1.2,4.12,1.68,1),('doorAperture',2.16,.84,.44,3.20,1.72,-1)]
 zones=[];metrics={'openings':{},'heads':{}}
 for n,x0,y,z0,x1,z1,sign in openings:
  ids=np.flatnonzero(box(fc[:len(nei)],(x0,y-1e-6,z0),(x1,y+1e-6,z1))&(abs(sf[:len(nei),1])>1e-8))
  flip=sf[ids,1]*sign<0
  zones.append(f'{n}\n{{type faceZone; faceLabels List<label> {len(ids)}\n(\n'+ '\n'.join(map(str,ids))+'\n); flipMap List<bool> '+str(len(ids))+'\n(\n'+'\n'.join('1' if v else '0' for v in flip)+'\n);}\n')
  metrics['openings'][n]={'area_m2':float(np.linalg.norm(sf[ids],axis=1).sum()),'faces':len(ids),'positive_flow':'into cabin (+y)' if sign>0 else 'into cabin (-y)'}
 (case/'constant/polyMesh/faceZones').write_text(header('faceZones','regIOobject')+str(len(zones))+'\n(\n'+''.join(zones)+')\n')
 cellzones=[]
 for row,x in [(1,2.80),(2,3.72),(3,4.52)]:
  ys=[(.32,.56),(-.56,-.32)] if row==1 else [(-.64,-.40),(-.12,.12),(.40,.64)]
  for j,(yl,yh) in enumerate(ys):
   n=f'head{row}_{j+1}';ids=np.flatnonzero(box(C,(x,yl,1.40),(x+.20,yh,1.60)))
   cellzones.append((n,ids));metrics['heads'][n]={'cells':len(ids),'volume_m3':len(ids)*.04**3}
 cellzones.append(('cabin',np.flatnonzero(cabin(C))))
 (case/'constant/polyMesh/cellZones').write_text(header('cellZones','regIOobject')+str(len(cellzones))+'\n(\n'+''.join(n+'\n{type cellZone; cellLabels List<label> '+str(len(ids))+'\n(\n'+'\n'.join(map(str,ids))+'\n);}\n' for n,ids in cellzones)+')\n')
 metrics['cells']=len(C);metrics['cabin_air_volume_m3']=len(cellzones[-1][1])*.04**3
 metrics['patch_area_m2']={}
 b=(case/'constant/polyMesh/boundary').read_text()
 for n,nf,st in re.findall(r'(\w+)\s*\{[^}]*nFaces\s+(\d+);[^}]*startFace\s+(\d+);',b,re.S):metrics['patch_area_m2'][n]=float(np.linalg.norm(sf[int(st):int(st)+int(nf)],axis=1).sum())
 (case/'mesh_metrics.json').write_text(json.dumps(metrics,indent=2));np.savez_compressed(case/'mesh_arrays.npz',C=C,points=pts,fc=fc,sf=sf,owner=owner,neighbour=nei)
 run('checkMesh',case)
 print(json.dumps(metrics,indent=2),flush=True)
if __name__=='__main__':
 bg=setup_background() if not (ROOT/'mesh/background/0/Cx').exists() else ROOT/'mesh/background'
 for k in ['fourWindows','doorFan','precursor']:build(k,bg)
