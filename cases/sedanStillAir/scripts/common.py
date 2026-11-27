"""Paths, the car's geometry on the 4 cm lattice, an ASCII mesh reader and small helpers.

Every solid is chosen by cell centre, so the functions below take an (n, 3) array of cell
centres and return a mask. x runs rearward from the front bumper, y towards the passenger side
(the driver sits at -y), z up from the ground; metres.
"""
from pathlib import Path
import numpy as np,re,subprocess,time,json,os,sys,shutil
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
def header(obj,cls='dictionary'):
 return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'
def write(p,s):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def run(cmd,case,log=None):
 case=Path(case);start=time.time();log=log or 'log.'+cmd.split()[0]
 print(str(case),cmd,flush=True)
 with (case/log).open('w') as f:
  r=subprocess.run(cmd,shell=True,cwd=case,stdout=f,stderr=subprocess.STDOUT,executable='/bin/bash')
 ROOT.mkdir(exist_ok=True)
 with (ROOT/'timing.jsonl').open('a') as f:f.write(json.dumps(dict(cmd=cmd,case=str(case),seconds=time.time()-start,code=r.returncode))+'\n')
 if r.returncode:raise RuntimeError((case/log).read_text()[-4000:])
def content(p):
 s=Path(p).read_text();m=re.search(r'\n\s*\d+\s*\n\s*\(',s);return s[m.end():s.rfind(')')]
def readmesh(case):
 """Points, faces, owner, neighbour, face centres and area vectors, cell centres and volumes."""
 p=Path(case)/'constant/polyMesh'
 pts=np.fromstring(content(p/'points').replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
 faces=[np.fromstring(x,sep=' ',dtype=int) for x in re.findall(r'\d+\(([^()]*)\)',content(p/'faces'))]
 own=np.fromstring(content(p/'owner'),sep=' ',dtype=int);nei=np.fromstring(content(p/'neighbour'),sep=' ',dtype=int)
 cf=np.array([pts[f].mean(axis=0) for f in faces])
 # the faces are axis-aligned polygons (split faces at the refinement steps have more than four
 # points), so the area vector is the shoelace sum
 sf=np.array([np.cross(pts[f],np.roll(pts[f],-1,axis=0)).sum(axis=0)/2 for f in faces])
 nc=max(own.max(),nei.max())+1;C=np.zeros((nc,3));count=np.zeros(nc)
 np.add.at(C,own,cf);np.add.at(count,own,1);np.add.at(C,nei,cf[:len(nei)]);np.add.at(count,nei,1);C/=count[:,None]
 V=np.zeros(nc);d=np.einsum('ij,ij->i',cf,sf)/3;np.add.at(V,own,d);np.add.at(V,nei,-d[:len(nei)])
 return pts,faces,own,nei,cf,sf,C,V

def box(c,lo,hi):return ((c>np.array(lo)-1e-7)&(c<np.array(hi)+1e-7)).all(axis=1)
def cabin(c,width=.72):
 """The cabin's air: x 1.48-4.12, |y| <= width, z 0.24-1.36, behind the windscreen's inner face
 through (1.48, 0.92) and (2.36, 1.44) and in front of the rear glass's through (4.20, 1.00) and
 (3.48, 1.44). width 0.82 takes in the inner half of the side walls, for the hot start."""
 x,y,z=c.T
 return box(c,(1.48,-width,.24),(4.12,width,1.36)) & (x>=1.48+(z-.92)*.88/.52-1e-8)&(x<=4.20-(z-1)*.72/.44+1e-8)
# The seats: two front buckets, each a cushion, a back and a headrest, and a three-seat rear bench
# with three headrests.
seatboxes=[]
for y0,y1 in [(.12,.64),(-.64,-.12)]:
 seatboxes += [((2.24,y0,.24),(2.72,y1,.48)),((2.72,y0,.24),(2.88,y1,1.04))]
for y0,y1 in [(.28,.52),(-.52,-.28)]:seatboxes += [((2.76,y0,1.04),(2.84,y1,1.24))]
seatboxes += [((3.16,-.72,.24),(3.60,.72,.48)),((3.60,-.72,.24),(3.80,.72,1.00))]
for y0,y1 in [(-.56,-.32),(-.12,.12),(.32,.56)]:seatboxes += [((3.64,y0,1),(3.72,y1,1.16))]
def seats(c):return np.logical_or.reduce([box(c,*b) for b in seatboxes])
def dash(c):return box(c,(1.48,-.72,.68),(1.92,.72,.92))
def solids(c,name):
 """The car's solid cells for run `name`: the body round the cabin, less that run's openings,
 the dashboard, the seats and the trunk's bulkhead behind the rear seat back."""
 x,y,z=c.T
 body=box(c,(0,-.92,.16),(4.92,.92,1.44))
 body &= ~((z>.92)&(x<1.4+(z-.92)*.88/.52))   # the hood and the raked windscreen
 body &= ~((z>1)&(x>4.28-(z-1)*.72/.44))      # the rear glass and the trunk deck
 body &= ~cabin(c)
 openings={}
 for side,Y in [('Left',-.82),('Right',.82)]:
  for row,a,b in [('front',2.16,2.84),('rear',2.96,3.60)]:
   openings[row+side]=box(c,(a,Y-.1,.96),(b,Y+.1,1.32))
 if name=='fourWindows':body &= ~np.logical_or.reduce(list(openings.values()))
 else:body &= ~(openings['rearLeft']|box(c,(1.96,.72,.24),(2.96,.92,1.32)))
 return body|dash(c)|seats(c)|box(c,(3.8,-.72,.24),(4.12,.72,1))
def listfoam(a):return str(len(a))+'\n(\n'+'\n'.join(map(str,a))+'\n)\n'
def setfile(case,name,ids,cls='faceSet'):
 write(Path(case)/'constant/polyMesh/sets'/name,header(name,cls)+listfoam(ids))
