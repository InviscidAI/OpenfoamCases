#!/usr/bin/env python3
"""Select the internal Cartesian faces crossed by the requested zero-thickness curtain."""
import re, sys
from pathlib import Path
import numpy as np
case=Path(sys.argv[1]); run=sys.argv[2]
pm=case/'constant/polyMesh'

def body(path,obj):
 s=path.read_text(errors='strict'); pos=s.index('object      '+obj); a=s.index('\n(',pos)+2; b=s.rfind(')'); return s[a:b]
pts=np.array([tuple(map(float,m)) for m in re.findall(r'\(([-+.0-9eE]+) ([-+.0-9eE]+) ([-+.0-9eE]+)\)',body(pm/'points','points'))])
faces=[list(map(int,m.split())) for m in re.findall(r'\d+\(([^()]*)\)',body(pm/'faces','faces'))]
def labels(path,obj): return list(map(int,re.findall(r'(?m)^\s*(\d+)\s*$',body(path,obj))))
owner=labels(pm/'owner','owner'); neigh=labels(pm/'neighbour','neighbour')
nc=max(owner)+1
cellverts=[set() for _ in range(nc)]
for fi,fs in enumerate(faces):
 cellverts[owner[fi]].update(fs)
 if fi<len(neigh): cellverts[neigh[fi]].update(fs)
cc=np.array([pts[list(v)].mean(axis=0) for v in cellverts])
sel=[]
for fi in range(len(neigh)):
 fs=faces[fi]; xyz=pts[fs]; fc=xyz.mean(axis=0); a,b=owner[fi],neigh[fi]
 # Exclude front/back faces. Select the centreline of the Cartesian staircase.
 if np.ptp(xyz[:,2]) < 0.9: continue
 if run=='hanging':
  if np.max(np.abs(xyz[:,0]-0.15))<1e-8 and 0.01 <= fc[1] <= 2.20: sel.append(fi)
 elif run=='tucked':
  y=fc[1]
  hit=False
  if 0.90 < y < 2.20 and fc[0] < 0.151:
   def level(c): return c[0] - 0.15*(c[1]-0.90)/1.30
   hit=level(cc[a])*level(cc[b]) < 0
  # Extend the digital line to the exact sill endpoint and through the face
  # containing the rail endpoint. These are the only endpoint corrections.
  xmin,xmax=xyz[:,0].min(),xyz[:,0].max(); ymin,ymax=xyz[:,1].min(),xyz[:,1].max()
  if xmax-xmin < 1e-9 and abs(xmin-0.005)<1e-9 and ymin >= 0.90-1e-9 and ymax <= 0.924+1e-9: hit=True
  if xmax-xmin < 1e-9 and abs(xmin-0.15)<1e-9 and ymin <= 2.20 <= ymax: hit=True
  if hit: sel.append(fi)
 else: raise SystemExit(run)
out=pm/'sets'; out.mkdir(exist_ok=True)
text='''FoamFile\n{\n    version 2.0;\n    format ascii;\n    class faceSet;\n    location "constant/polyMesh/sets";\n    object curtainFaces;\n}\n\n%d\n(\n%s\n)\n'''%(len(sel),'\n'.join(map(str,sel)))
(out/'curtainFaces').write_text(text)
# report face bounding geometry before splitting
allp=np.vstack([pts[faces[i]] for i in sel]); areas=[]
for i in sel:
 q=pts[faces[i]]
 # rectangular face has one in-plane edge along z and one in x/y
 areas.append(0.5*np.linalg.norm(np.cross(q[2]-q[0],q[3]-q[1])))
(case/'curtain_geometry.txt').write_text(f'run {run}\nfaces {len(sel)}\nvertices_min {allp.min(0)}\nvertices_max {allp.max(0)}\narea_m2_per_m {sum(areas):.12g}\n')
print((case/'curtain_geometry.txt').read_text())
