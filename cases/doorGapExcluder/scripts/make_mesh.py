"""The section's blockMesh case: python3 scripts/make_mesh.py N <dir>, then blockMesh -case <dir>.

N is the number of cells across each gap (the 10 mm undercut and the 3 mm head gap); the solved
runs used N = 10 (139,030 cells), the mesh study 5, 10 and 20. One tensor-product lattice of
graded blocks, one cell deep in z (1 m, empty front and back); the door leaf (x = 4.000-4.035 m,
y = 0.010-1.991 m) and the wall above it (x = 4.000-4.100 m, y > 1.994 m) are left out as blocks.
Sizes follow a seeded envelope of slope 0.12, so neighbouring cells differ by at most 1.2, and
both gaps are uniform across. Writes <dir>/system/blockMeshDict, a controlDict for blockMesh
(ascii, as for the solved runs), axis.npz and mesh_spec.json. This is the study's generator with
two changes: the far room's cap below, and its copy of fvSchemes and fvSolution into <dir>, which
blockMesh does not read, left out.
"""
import sys,math,json
from pathlib import Path
import numpy as np
def header(obj):return f'FoamFile {{version 2.0; format ascii; class dictionary; object {obj};}}\n'
def axis(keys,seeds,cap):
 # Size envelope has slope <=0.12, keeping geometric neighbour ratios below 1.2.
 for attempt in range(30):
  segments=[]
  for a,b in zip(keys[:-1],keys[1:]):
   t=np.linspace(a,b,10001);d=np.minimum(cap(t),np.min([s+.12*abs(t-c) for c,s in seeds],axis=0))
   integ=np.r_[0,np.cumsum(np.diff(t)*.5*(1/d[:-1]+1/d[1:]))]
   n=math.ceil(integ[-1]-1e-10);e=np.interp(np.linspace(0,integ[-1],n+1),integ,t);segments.append(e)
  bad=[]
  for i in range(len(segments)-1):
   l=np.diff(segments[i])[-1];r=np.diff(segments[i+1])[0]
   if max(l/r,r/l)>1.199:bad.append((keys[i+1],min(l,r)*1.01))
  if not bad:break
  seeds+=bad
 else:raise RuntimeError('grading not reconciled')
 return segments

def main(N,case):
 p=Path(case);(p/'system').mkdir(parents=True,exist_ok=True)
 X=[0,.04,.123,.2,1,3,3.7,4,4.0175,4.035,4.1,4.4,5.1,5.6]
 Y=[0,.010,.100,.150,.750,.900,1.991,1.994,2,2.1,2.4]
 # The far room's x cap is 0.020 m up to N = 10, as when L5 and L10 (the solved runs' mesh) were
 # built; the study then tied it to 60*0.003/N for L20, which at N = 10 would give 0.018 m and
 # 146,662 cells. With this line the script writes L5, L10 and L20 as the study did, byte for byte.
 sx=axis(X,[(0,.005),(.04,.005),(.123,.005),(3.7,.0048),(4,.003/N*1.7),(4.035,.003/N*1.7),(4.1,.0048),(4.4,.0048),(5.6,min(.005,30*.003/N))],lambda t:np.where((t>=4)&(t<=4.035),.0025,np.where((t>=3.7)&(t<=4.4),.005,.020 if N<=10 else min(.020,60*.003/N))))
 sy=axis(Y,[(0,.010/N),(.010,.010/N),(.100,.0025),(.150,.010),(.750,.010),(.900,.011),(1.991,.003/N),(1.994,.003/N),(2.4,.003)],lambda t:np.where(t<=.1,.0025,np.where((t>=.15)&(t<=.9),.010,np.where((t>=.9)&(t<=2.1),.012,min(.020,60*.003/N*1.7)))))
 # Force exact uniform slot heights independent of the envelope.
 sy[0]=np.linspace(0,.01,N+1);j=Y.index(1.991);sy[j]=np.linspace(1.991,1.994,N+1)
 # They already match the prescribed endpoint spacing; assert actual adjacency.
 for seg in [sx,sy]:
  d=np.concatenate([np.diff(e) for e in seg]);assert max(np.max(d[1:]/d[:-1]),np.max(d[:-1]/d[1:]))<=1.2+1e-6
 nx=len(X);ny=len(Y)
 def v(i,j,k):return k*nx*ny+j*nx+i
 vertices=['(%g %g %g)'%(x,y,z) for z in [0,1] for y in Y for x in X]
 def solid(i,j):return (X[i]>=4 and X[i+1]<=4.035 and Y[j]>=.010 and Y[j+1]<=1.991) or (X[i]>=4 and X[i+1]<=4.1 and Y[j]>=1.994)
 active={(i,j) for i in range(nx-1) for j in range(ny-1) if not solid(i,j)}
 patches={n:[] for n in ['roomFloor','hallFloor','roomCeiling','hallCeiling','glass','outerWall','frontDoor','hallWall','leafRoom','leafHall','wallRoom','wallHall','adiabaticEdges','frontAndBack']}
 blocks=[];count=0
 def grade(e):
  d=np.diff(e);return '('+' '.join('(%.14g 1 1)'%q for q in d)+')'
 for i,j in sorted(active):
  a,b,c,d,e,f,g,h=[v(i,j,0),v(i+1,j,0),v(i+1,j+1,0),v(i,j+1,0),v(i,j,1),v(i+1,j,1),v(i+1,j+1,1),v(i,j+1,1)]
  ni=len(sx[i])-1;nj=len(sy[j])-1;count+=ni*nj
  blocks.append(f'hex ({a} {b} {c} {d} {e} {f} {g} {h}) ({ni} {nj} 1) simpleGrading ({grade(sx[i])} {grade(sy[j])} 1)')
  for side,neighbor,ids in [('bottom',(i,j-1),[a,b,f,e]),('top',(i,j+1),[d,h,g,c]),('left',(i-1,j),[a,e,h,d]),('right',(i+1,j),[b,c,g,f])]:
   if neighbor in active:continue
   name='adiabaticEdges'
   if j==0 and side=='bottom':name='roomFloor' if X[i]<4 else 'hallFloor'
   elif j==ny-2 and side=='top':name='roomCeiling' if X[i]<4 else 'hallCeiling'
   elif i==0 and side=='left':name='glass' if Y[j]>=.9 and Y[j+1]<=2.1 else 'outerWall'
   elif i==nx-2 and side=='right':name='frontDoor' if Y[j+1]<=2 else 'hallWall'
   elif side=='right' and X[i+1]==4:name='leafRoom' if Y[j+1]<=1.991 else 'wallRoom'
   elif side=='left' and X[i]==4.035:name='leafHall'
   elif side=='left' and X[i]==4.1:name='wallHall'
   patches[name].append('('+' '.join(map(str,ids))+')')
  patches['frontAndBack']+=['(%d %d %d %d)'%(a,d,c,b),'(%d %d %d %d)'%(e,f,g,h)]
 boundary='\n'.join(n+'\n{\ntype '+('empty' if n=='frontAndBack' else 'wall')+';\nfaces\n(\n'+'\n'.join(f)+'\n);\n}' for n,f in patches.items())
 (p/'system/blockMeshDict').write_text(header('blockMeshDict')+'scale 1;\nvertices\n(\n'+'\n'.join(vertices)+'\n);\nblocks\n(\n'+'\n'.join(blocks)+'\n);\nedges ();\nboundary\n(\n'+boundary+'\n);\nmergePatchPairs ();\n')
 (p/'system/controlDict').write_text(header('controlDict')+'application blockMesh; startFrom startTime; startTime 0; stopAt endTime; endTime 10; deltaT .0001; writeControl timeStep; writeInterval 1;')
 np.savez(p/'axis.npz',x=np.concatenate([e[:-1] for e in sx]+[sx[-1][-1:]]),y=np.concatenate([e[:-1] for e in sy]+[sy[-1][-1:]]))
 data={'N':N,'cells':count,'nx':sum(len(e)-1 for e in sx),'ny':sum(len(e)-1 for e in sy),'max_adjacent_ratio':max(max(np.max(np.diff(np.concatenate([e[:-1] for e in s]+[s[-1][-1:]]))[1:]/np.diff(np.concatenate([e[:-1] for e in s]+[s[-1][-1:]]))[:-1]),np.max(np.diff(np.concatenate([e[:-1] for e in s]+[s[-1][-1:]]))[:-1]/np.diff(np.concatenate([e[:-1] for e in s]+[s[-1][-1:]]))[1:])) for s in [sx,sy])}
 (p/'mesh_spec.json').write_text(json.dumps(data,indent=2));print(data)
if __name__=='__main__':main(int(sys.argv[1]),sys.argv[2])
