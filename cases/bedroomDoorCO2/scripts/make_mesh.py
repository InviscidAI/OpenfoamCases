#!/usr/bin/env python3
"""The 2-D section's mesh for one run, written straight into RUNDIR/constant/polyMesh.

    python3 scripts/make_mesh.py shut|ajar RUNDIR

A tensor grid of quads, one cell deep in z (0 to 1 m, the empty frontAndBack), x from the outside
wall's inner face (x = 0) to the house boundary at x = 4.80 m and y from the floor to the ceiling
at 2.44 m. Every listed x and y is a mesh line; between them the cells are at most 2 cm within
0.10 m of the floor, the ceiling and the window and over the bed and the breath zones
(x 0.95-2.55, y 0.55-1.25), at most 2.5 cm round the doorway, at most 3 cm elsewhere, no cell under
2 cm (each 5 cm breath zone becomes two 2.5 cm cells), adjacent ratios at most 1.15. Cells whose
centre is inside a solid (the bed to y = 0.55, the two sleepers' humps, the wall over the doorway
and, in "shut", the door leaf) are left out, and their faces become the wall patches. The cell
zones and the face zones at x = 3.55 and 3.50 are what constant/fvOptions, the CO2 sources and the
monitor name. It also writes RUNDIR/mesh.npz (the grid and the cell centres) and RUNDIR/mesh.json
(patch areas, each wall face's centre-to-wall distance and the zones' volumes), which
scripts/make_case.py reads.

This is build87.py of the cloud study, the mesh both solved runs used, with only its output
paths changed and the geometry picture it also drew left out.
"""
from pathlib import Path
import numpy as np,json,math,shutil,sys
def H(o,c='dictionary'):return f'FoamFile {{ version 2.0; format ascii; class {c}; object {o}; }}\n'
def lst(vals):return str(len(vals))+'\n(\n'+'\n'.join(map(str,vals))+'\n)\n'
def grid(anchors,target):
 a=np.array(sorted(set(anchors)));length=np.diff(a);tar=np.array([target((v+w)/2) for v,w in zip(a[:-1],a[1:])]);cap=np.where(tar<=.020001,.025,.03)
 counts=np.minimum(np.ceil(length/tar-1e-8).astype(int),np.floor(length/.02+1e-8).astype(int));counts=np.maximum(counts,np.ceil(length/cap-1e-8).astype(int))
 for trial in range(100):
  sid=np.repeat(np.arange(len(length)),counts);d=np.concatenate([np.full(n,L/n) for n,L in zip(counts,length)])
  for it in range(2500):
   for j in range(len(d)-1):
    u,v=d[j:j+2]
    if max(u/v,v/u)>1.149:
     total=u+v;lo=total/2.149;hi=total-lo
     d[j:j+2]=[hi,lo] if u>v else [lo,hi]
   for k,L in enumerate(length):
    mask=sid==k;z=d[mask];lo=-.05;hi=.05
    for _ in range(25):
     mid=(lo+hi)/2
     if np.clip(z+mid,.02,cap[k]).sum()>L:hi=mid
     else:lo=mid
    d[mask]=np.clip(z+(lo+hi)/2,.02,cap[k])
   ratios=np.maximum(d[1:]/d[:-1],d[:-1]/d[1:])
   if ratios.max()<=1.1499:break
  if ratios.max()<=1.1499:break
  j=int(np.argmax(ratios));small=j if d[j]<d[j+1] else j+1;k=sid[small]
  if counts[k]>math.ceil(length[k]/cap[k]-1e-8):counts[k]-=1
  else:
   k=sid[j+1 if small==j else j]
   if counts[k]<math.floor(length[k]/.02+1e-8):counts[k]+=1
   else:raise RuntimeError('No bounded graded division at '+str(a[k:k+2]))
 out=[a[0]]
 for k,L in enumerate(length):
  z=d[sid==k];z*=L/z.sum();out.extend(a[k]+np.cumsum(z));out[-1]=a[k+1]
 out=np.array(out);assert np.diff(out).min()>=.02-1e-7
 return out
coarse=1.0
x=grid([0,.10,.98,1,1.2,1.3,1.5,2,2.2,2.3,2.5,2.52,3.3,3.5,3.55,3.6,3.8,4.8],lambda v:.02 if v<.10 or .95<=v<=2.55 else (.025 if 3.3<=v<=3.8 else .03))
y=grid([0,.02,.10,.55,.85,.90,1.20,1.22,1.95,2.01,2.03,2.10,2.20,2.44],lambda v:.03 if .10<v<.55 else .02)
if len(sys.argv)!=3 or sys.argv[1] not in ('shut','ajar'):sys.exit('usage: make_mesh.py shut|ajar RUNDIR')
shut=sys.argv[1]=='shut'
C=Path(sys.argv[2]);(C/'constant/polyMesh').mkdir(parents=True,exist_ok=True)
nx=len(x)-1;ny=len(y)-1;ids={};kind={};cent=[];vol=[]
def solid(xx,yy):
 if .98<xx<2.52 and yy<.55:return 'bed'
 for a,name in [(1,'sleeperMan'),(2,'sleeperWoman')]:
  if a<xx<a+.5 and yy>.55:
   top=.55+.30*math.sqrt(max(0,1-((xx-a-.25)/.25)**2))
   if yy<top:return name
 if 3.5<xx<3.6 and yy>2.03:return 'doorWall'
 if shut and 3.5<xx<3.6 and .02<yy<2.01:return 'doorLeafWall'
 return None
for j in range(ny):
 for i in range(nx):
  xx=(x[i]+x[i+1])/2;yy=(y[j]+y[j+1])/2;k=solid(xx,yy);kind[i,j]=k
  if k is None:ids[i,j]=len(cent);cent.append([xx,yy,.5]);vol.append((x[i+1]-x[i])*(y[j+1]-y[j]))
cent=np.array(cent);vol=np.array(vol);pts=[];pids={}
def pt(i,j,k):
 key=(i,j,k)
 if key not in pids:pids[key]=len(pts);pts.append(f'({x[i]:.14g} {y[j]:.14g} {k})')
 return pids[key]
patches={p:[] for p in ['window','outsideWall','floor','ceiling','doorWall','bed','sleeperMan','sleeperWoman','hallFloor','hallCeiling','house','doorLeafWall','frontAndBack']};internal=[];pmeasure={p:0 for p in patches};pcent={p:[] for p in patches};pdist={p:[] for p in patches};facepos=[]
for (i,j),cid in ids.items():
 v=[pt(i,j,0),pt(i+1,j,0),pt(i+1,j+1,0),pt(i,j+1,0),pt(i,j,1),pt(i+1,j,1),pt(i+1,j+1,1),pt(i,j+1,1)]
 faces=[([v[k] for k in ks],di,dj,axis) for ks,di,dj,axis in [([0,4,7,3],-1,0,'x'),([1,2,6,5],1,0,'x'),([0,1,5,4],0,-1,'y'),([3,7,6,2],0,1,'y')]]
 for fv,di,dj,axis in faces:
  nei=ids.get((i+di,j+dj));xx=x[i+(di>0)] if axis=='x' else cent[cid,0]; yy=y[j+(dj>0)] if axis=='y' else cent[cid,1];area=y[j+1]-y[j] if axis=='x' else x[i+1]-x[i]
  if nei is not None:
   if cid<nei:internal.append((fv,cid,nei,[xx,yy,.5],axis))
  else:
   name=kind.get((i+di,j+dj))
   if name is None:
    if di<0:name='window' if .9<yy<2.2 else 'outsideWall'
    elif di>0:name='house'
    elif dj<0:name='floor' if xx<3.6 else 'hallFloor'
    else:name='ceiling' if xx<3.5 else 'hallCeiling'
   patches[name].append((fv,cid));pmeasure[name]+=area;pcent[name].append([xx,yy,.5]);pdist[name].append((x[i+1]-x[i])/2 if axis=='x' else (y[j+1]-y[j])/2)
 for ks in [[0,3,2,1],[4,5,6,7]]:patches['frontAndBack'].append(([v[k] for k in ks],cid));pmeasure['frontAndBack']+=vol[cid];pcent['frontAndBack'].append(cent[cid]);pdist['frontAndBack'].append(.5)
faces=[f[0] for f in internal];own=[f[1] for f in internal];neigh=[f[2] for f in internal];bounds=[]
for p,fs in patches.items():
 bounds.append((p,len(fs),len(faces)));faces.extend(f[0] for f in fs);own.extend(f[1] for f in fs)
M=C/'constant/polyMesh'
(M/'points').write_text(H('points','vectorField')+lst(pts));(M/'faces').write_text(H('faces','faceList')+lst(['4('+' '.join(map(str,f))+')' for f in faces]));(M/'owner').write_text(H('owner','labelList')+lst(own));(M/'neighbour').write_text(H('neighbour','labelList')+lst(neigh))
(M/'boundary').write_text(H('boundary','polyBoundaryMesh')+str(len(bounds))+'\n(\n'+''.join(f'{p}\n{{ type '+('empty' if p=='frontAndBack' else 'patch' if p=='house' else 'wall')+f'; nFaces {n}; startFace {s}; }}\n' for p,n,s in bounds)+')\n')
xx=cent[:,0];yy=cent[:,1]
zones={'bedroom':xx<3.5,'doorway':(xx>3.5)&(xx<3.6)&(yy<2.03),'doorUnder':(xx>3.5)&(xx<3.6)&(yy<.02),'doorLeaf':(xx>3.5)&(xx<3.6)&(yy>.02)&(yy<2.01),'doorHead':(xx>3.5)&(xx<3.6)&(yy>2.01)&(yy<2.03),'breathMan':(xx>1.2)&(xx<1.3)&(yy>.85)&(yy<.90),'breathWoman':(xx>2.2)&(xx<2.3)&(yy>.85)&(yy<.90),'heads':(xx>1)&(xx<2.5)&(yy>.9)&(yy<1.2),'hall':xx>3.6,'hallUpper':(xx>3.6)&(yy>1.22),'bedroomUpper':(xx<3.5)&(yy>1.22),'bedroomLower':(xx<3.5)&(yy<1.22)}
(M/'cellZones').write_text(H('cellZones','regIOobject')+str(len(zones))+'\n(\n'+''.join(f'{z}\n{{ type cellZone; cellLabels List<label>\n'+lst(np.where(mask)[0])+'; }\n' for z,mask in zones.items())+')\n')
fzones={}
for name,xp,yl,yh in [('doorPlane',3.55,0,2.03),('doorPlaneUnder',3.55,0,.02),('doorPlaneLeaf',3.55,.02,2.01),('doorPlaneHead',3.55,2.01,2.03),('bedroomSide',3.5,0,2.03)]:fzones[name]=[k for k,f in enumerate(internal) if f[4]=='x' and abs(f[3][0]-xp)<1e-8 and yl<f[3][1]<yh]
(M/'faceZones').write_text(H('faceZones','regIOobject')+str(len(fzones))+'\n(\n'+''.join(f'{z}\n{{ type faceZone; faceLabels List<label>\n'+lst(fs)+'; flipMap List<bool>\n'+lst(['false']*len(fs))+'; }\n' for z,fs in fzones.items())+')\n')
np.savez(C/'mesh.npz',x=x,y=y,centres=cent,volumes=vol)
meta={'cells':len(cent),'nx':nx,'ny':ny,'coarsening':coarse,'adjacent_ratios':{'x':float(max(np.maximum(np.diff(x)[1:]/np.diff(x)[:-1],np.diff(x)[:-1]/np.diff(x)[1:]))),'y':float(max(np.maximum(np.diff(y)[1:]/np.diff(y)[:-1],np.diff(y)[:-1]/np.diff(y)[1:])))} ,'patch_areas_m2_per_m':pmeasure,'zone_volumes_m3_per_m':{z:float(vol[mask].sum()) for z,mask in zones.items()},'patch_centres':{p:np.array(v).tolist() for p,v in pcent.items()},'patch_distance':pdist,'door_dx':np.diff(x)[(x[:-1]>=3.5-1e-8)&(x[1:]<=3.6+1e-8)].tolist(),'under_dy':np.diff(y)[y[1:]<=.02+1e-8].tolist(),'head_dy':np.diff(y)[(y[:-1]>=2.01-1e-8)&(y[1:]<=2.03+1e-8)].tolist()}
(C/'mesh.json').write_text(json.dumps(meta,indent=2));print({k:v for k,v in meta.items() if k not in ['patch_centres','patch_distance']})
