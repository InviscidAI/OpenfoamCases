#!/usr/bin/env python3
"""Orthogonal Cartesian finite-volume mesh, local directional refinement, nested one-level grading (regrade, 3 Nov 2026).
Integer-micrometre geometry, split interface faces and conformal polygon edges.
Writes native OpenFOAM polyMesh; excludes each heater's solid volumes.

fanHeaterVsOilRadiator: the builder of the radiator run's (oilHot) mesh (3 Nov 2026), as solved, but for its output.
    python3 scripts/mesh_regrade.py <meshDir>
writes the background mesh, the whole room with no heater cut out, into <meshDir>/constant/polyMesh
(with the occupied zone's cellZones and frontOfHeater) and mesh_background.json and levels_background.json
into <meshDir>. Allrun then cuts the heater out with topoSet and subsetMesh. The fan and oil
branches of solid() are not used by that route.
"""
from pathlib import Path
import numpy as np, math, json, sys, collections, bisect, gc
OUT=None  # the mesh case directory, from the command line
S=1000000
def seq(a,b,h):
 n=math.ceil((b-a)/h-1e-9);return [round(S*(a+(b-a)*i/n)) for i in range(n+1)]
def lines(segs,extra=()):return sorted(set(sum([seq(*s) for s in segs],[])+[round(S*v) for v in extra]))
def gseq(a,b,h0,h1):
 # geometric spacing from about h0 at a to about h1 at b
 L=b-a;n=max(1,round(2*L/(h0+h1)))
 if n==1:return [round(S*a),round(S*b)]
 r=(h1/h0)**(1/(n-1));w=[r**i for i in range(n)];t=sum(w);out=[a];q=a
 for x in w:q+=L*x/t;out.append(q)
 return [round(S*v) for v in out[:-1]]+[round(S*b)]
def glines(segs,extra=()):
 pts=set(round(S*v) for v in extra)
 for s in segs:pts.update(seq(*s) if len(s)==3 else gseq(*s))
 return sorted(pts)
# Regrade, 3 Nov 2026 (operator's note): the first production's oil run grew a cold column in the 3.2 cm cells in
# front of the fins, where 36 mm cells met the fins' lattice four to one through split faces. Every interior face now
# joins cells whose lattices are nested, and no cell meets more than two neighbours along any edge (one level).
# x lines are unchanged from the rework (they set the fan run's step behind the intake).
X=glines([(0,.15,.02,.01),(.15,.30,.03),(.30,1.30,.03,.07),(1.30,2.0,.07,.09),(2,3.8,.09),(3.8,4,.05)])
# y: one lattice for every column at x < 1.30 m (behind, at and in front of the heaters), and above 0.63 m one
# 3 cm lattice for the whole room; the far room (x > 1.30 m) takes every other 1 cm line near the floor.
UP=[round(S*(.63+.03*k)) for k in range(60)]
MIDY=[round(S*(.234+(.63-.234)*k/14)) for k in range(15)]
YH=sorted(set([round(S*.01*k) for k in range(21)]+[217000,234000]+MIDY+UP))
YF=sorted(set([0,10000]+[round(S*.02*k) for k in range(1,11)]+[234000]+MIDY+UP))
def ys(x):return YH if x<1.30 else YF
# z: four nested lattices over |z| < 0.5 m; beyond it subject 51's 20 graded cells each side, common to all.
FIN=sorted(set([round(S*v) for k in range(7) for v in (-.134+.036*k,-.126+.036*k,-.118+.036*k)]+
 [round(S*(-.108+.036*k)) for k in range(6)]+[-89000,89000,128000,158000,188000])-{round(S*-.090),round(S*.090)})
JETS=[round(S*v) for v in (-.134,-.118,-.098,-.082,-.062,-.054,-.046,-.036,-.026,-.018,-.010,0,.010,.018,.026,.036,.046,.054,.062,.082,.098,.128,.158,.188)]
MIDS=[round(S*v) for v in (-.134,-.118,-.098,-.082,-.062,-.046,-.026,-.010,.010,.026,.046,.062,.082,.098,.128,.158,.188)]
COARSE=[round(S*v) for v in (-.134,-.098,-.062,-.026,.010,.046,.082,.128,.158,.188)]
def bisect_near(lines,edge,n):
 """Halve the n cells nearest the heater span's edge (lines sorted, edge one of its ends)."""
 cells=list(zip(lines[:-1],lines[1:]));cells.sort(key=lambda c:min(abs(c[0]-edge),abs(c[1]-edge)))
 return sorted(set(lines+[(a+b)//2 for a,b in cells[:n]]))
C_LO=gseq(-.5,-.134,.05,.036);C_HI=gseq(.188,.5,.036,.05)
M_LO=bisect_near(C_LO,-134000,len(C_LO));M_HI=bisect_near(C_HI,188000,len(C_HI))
F_LO=bisect_near(M_LO,-134000,2);F_HI=bisect_near(M_HI,188000,2)
OUTER=[]
_ratio=5**(1/19);_w=[_ratio**i for i in range(20)];_scale=1.25/sum(_w);_q=.5
for _x in _w:_q+=_scale*_x;OUTER+=[round(_q*S),-round(_q*S)]
# beside the fan casing and across the radiator's control column (z 0.098-0.188 m) the heaters' lattice has 3 cm
# cells; halve them so the step to the 9 mm cells beyond z = 0.188 m is under two to one.
COLUMN=[113000,143000,173000]
LATTICE={'F':sorted(set(F_LO+FIN+COLUMN+F_HI+OUTER)),'J':sorted(set(F_LO+JETS+F_HI+OUTER)),
 'M':sorted(set(M_LO+MIDS+M_HI+OUTER)),'C':sorted(set(C_LO+COARSE+C_HI+OUTER))}
def level(x,y):
 # F: the heaters' own lattice, from 6 cm behind to 10 cm in front of them and 9 cm above the fins.
 if .09<x<.40 and y<.72:return 'F'
 # J: the rework's jet lattice (1 cm across the grille's width) behind the intake and along the jet's first metre.
 if (x<.09 and y<.63) or (.40<x<1.30 and y<.30):return 'J'
 # M: one ring between the fine lattices and the room's.
 if (x<.50 and y<.84) or (x<1.45 and y<.40):return 'M'
 return 'C'
def zs(x,y):return LATTICE[level(x,y)]
def solid(x,y,z,run):
 if run=='background':return None
 if run=='fan':return 'fanCasing' if .150<x<.300 and 0<y<.234 and -.089<z<.089 else None
 if .150<x<.300 and .060<y<.630:
  if .098<z<.188:return 'column'
  for k in range(7):
   c=-.126+.036*k
   if c-.008<z<c+.008:return 'radiator'
 return None
# include fan z boundaries in background everywhere it intersects the casing;
# grille edges are face-only subdivisions, so fin-pack lattice stays exactly 4 mm.
def levels(run,faces,boxes):
 """Every interior face must join two cells whose extents are nested along both of the face's directions (no partial
 overlap, so no sliver), and no cell side may meet more than two neighbours along either direction (one level)."""
 B=np.asarray(boxes,dtype=np.int64)
 dims={0:(1,2),1:(2,0),2:(0,1)}
 partial=0;sides=collections.defaultdict(lambda:(set(),set()));worst_ratio=1.
 for axis,q,u0,u1,v0,v1,own,nei,sgn in faces:
  if nei<0:continue
  for k,d in enumerate(dims[axis]):
   a0,a1=B[own,2*d],B[own,2*d+1];b0,b1=B[nei,2*d],B[nei,2*d+1]
   if not ((a0<=b0 and b1<=a1) or (b0<=a0 and a1<=b1)):partial+=1;continue
   worst_ratio=max(worst_ratio,(a1-a0)/(b1-b0),(b1-b0)/(a1-a0))
   for c,o,lo,hi in ((own,nei,a0,a1),(nei,own,b0,b1)):
    side=+1 if (B[c,2*axis+1]==q) else -1
    sides[(c,axis,side)][k].add((B[o,2*d],B[o,2*d+1]))
 most=max(max(len(s0),len(s1)) for s0,s1 in sides.values())
 over=sum(1 for s0,s1 in sides.values() if len(s0)>2 or len(s1)>2)
 info=dict(run=run,interior_faces=sum(1 for f in faces if f[7]>=0),partial_overlaps=partial,cell_sides_over_one_level=over,most_neighbours_along_one_edge=most,largest_extent_ratio_across_a_face=round(worst_ratio,4))
 (OUT/f'levels_{run}.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
 assert partial==0 and over==0,info
def make(run):
 case=OUT; pm=case/'constant/polyMesh';pm.mkdir(parents=True,exist_ok=True)
 columns=[]; cells=[]; boxes=[]
 for ix,(a,b) in enumerate(zip(X[:-1],X[1:])):
  x=(a+b)/(2*S);Y=ys(x);col=[]
  for c,d in zip(Y[:-1],Y[1:]):
   y=(c+d)/(2*S);Z=zs(x,y)
   # fan casing extents are not on the fin lattice: split cells only outside oil fin pack.
   # Add casing z boundaries to the common mesh (these are away from fin faces).
   ids=[];sol=[]
   for e,f in zip(Z[:-1],Z[1:]):
    tag=solid(x,y,(e+f)/(2*S),run)
    if tag:ids.append(-1)
    else:ids.append(len(cells));cells.append(((a+b)//2,(c+d)//2,(e+f)//2));boxes.append((a,b,c,d,e,f))
    sol.append(tag)
   col.append((c,d,Z,ids,sol))
  columns.append(col)
 print(run,'cells',len(cells),flush=True)
 # Face records (axis, coordinate, u0,u1,v0,v1,owner,neighbour,patch).
 faces=[];boundary=collections.defaultdict(list)
 def emit(axis,q,u0,u1,v0,v1,lo,hi,lt=None,ht=None):
  if lo<0 and hi<0:return
  if lo>=0 and hi>=0:
   own,nei=(lo,hi) if lo<hi else (hi,lo);sgn=1 if own==lo else -1
   vs=sorted([v0,v1]+([v for v in [-57500,57500] if v0<v<v1] if axis==0 and q in (150000,300000) and u0>=30000 and u1<=190000 else []))
   for va,vb in zip(vs[:-1],vs[1:]):faces.append((axis,q,u0,u1,va,vb,own,nei,sgn))
   return
  own=lo if lo>=0 else hi;sgn=1 if lo>=0 else -1;patch=ht if lo>=0 else lt
  if patch is None:
   if axis==0:patch='windowWall' if q==0 else 'innerWall'
   elif axis==1:patch='floor' if q==0 else 'ceiling'
   else:patch='sideWalls'
  # glass and fan grilles split at specified edges, not approximate centroids.
  splitsU=[u0,u1];splitsV=[v0,v1]
  if axis==0 and q==0:
   splitsU+= [v for v in [900000,2100000] if u0<v<u1];splitsV += [v for v in [-500000,500000] if v0<v<v1]
  if patch=='fanCasing' and axis==0 and q in (150000,300000):
   splitsU += [v for v in [30000,190000] if u0<v<u1];splitsV += [v for v in [-57500,57500] if v0<v<v1]
  for l,r in zip(sorted(splitsU)[:-1],sorted(splitsU)[1:]):
   for s,t in zip(sorted(splitsV)[:-1],sorted(splitsV)[1:]):
    p=patch
    if axis==0 and q==0 and 900000<=(l+r)/2<=2100000 and abs((s+t)/2)<500000:p='glass'
    if patch=='fanCasing' and axis==0 and 30000<(l+r)/2<190000 and abs((s+t)/2)<57500:
     p='intake' if q==150000 else 'outlet'
    boundary[p].append((axis,q,l,r,s,t,own,-1,sgn))
 # x interfaces, overlay y intervals and then z intervals
 for i in range(len(X)):
  left=columns[i-1] if i else None;right=columns[i] if i<len(columns) else None
  if left is None or right is None:
   cc=right if left is None else left
   for c,d,Z,ids,sol in cc:
    for j,(e,f) in enumerate(zip(Z[:-1],Z[1:])):
     emit(0,X[i],c,d,e,f,-1 if left is None else ids[j],ids[j] if left is None else -1)
  else:
   il=ir=0
   while il<len(left) and ir<len(right):
    c,d,Z,ids,sol=left[il];C,D,ZZ,IDS,SOL=right[ir];u0=max(c,C);u1=min(d,D)
    jl=jr=0
    while jl<len(ids) and jr<len(IDS):
     e,f=Z[jl:jl+2];E,F=ZZ[jr:jr+2]
     if min(f,F)>max(e,E):emit(0,X[i],u0,u1,max(e,E),min(f,F),ids[jl],IDS[jr],sol[jl],SOL[jr])
     if f<=F:jl+=1
     if F<=f:jr+=1
    if d<=D:il+=1
    if D<=d:ir+=1
 # y interfaces (u=z,v=x gives +y)
 for ix,col in enumerate(columns):
  a,b=X[ix:ix+2]
  for iy in range(len(col)+1):
   low=col[iy-1] if iy else None;high=col[iy] if iy<len(col) else None
   if low is None or high is None:
    c,d,Z,ids,sol=high if low is None else low;q=c if low is None else d
    for j,(e,f) in enumerate(zip(Z[:-1],Z[1:])):emit(1,q,e,f,a,b,-1 if low is None else ids[j],ids[j] if low is None else -1)
   else:
    c,d,Z,ids,sol=low;C,D,ZZ,IDS,SOL=high;jl=jr=0
    while jl<len(ids) and jr<len(IDS):
     e,f=Z[jl:jl+2];E,F=ZZ[jr:jr+2]
     if min(f,F)>max(e,E):emit(1,d,max(e,E),min(f,F),a,b,ids[jl],IDS[jr],sol[jl],SOL[jr])
     if f<=F:jl+=1
     if F<=f:jr+=1
  # z native faces (u=x,v=y gives +z)
  for c,d,Z,ids,sol in col:
   for j,q in enumerate(Z):emit(2,q,a,b,c,d,ids[j-1] if j else -1,ids[j] if j<len(ids) else -1,sol[j-1] if j else None,sol[j] if j<len(ids) else None)
 del columns;gc.collect()
 levels(run,faces,boxes)
 patches=['windowWall','innerWall','floor','ceiling','sideWalls','glass']+(['fanCasing','intake','outlet'] if run=='fan' else [] if run=='background' else ['radiator','column'])
 faces.sort(key=lambda r:(r[6],r[7]))
 nint=len(faces);counts={p:len(boundary[p]) for p in patches};areas={};bounds={}
 for p in patches:
  ff=boundary[p];areas[p]=sum((r[3]-r[2])*(r[5]-r[4])/S**2 for r in ff)
  coords=[]
  for axis,q,u0,u1,v0,v1,*_ in ff:
   for u,v in [(u0,v0),(u1,v1)]:coords.append((q,u,v) if axis==0 else (v,q,u) if axis==1 else (u,v,q))
  arr=np.array(coords)/S;bounds[p]=[arr.min(0).tolist(),arr.max(0).tolist()]
  faces.extend(ff)
 del boundary;gc.collect()
 print(run,'faces',len(faces),'collecting edge breaks',flush=True)
 # Every rectangle edge is on one axis line; insert all coincident vertices so no hanging edges.
 edges=[collections.defaultdict(set) for _ in range(3)]
 def corners(r):
  ax,q,u0,u1,v0,v1,*_=r
  cs=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
  return [(q,u,v) if ax==0 else (v,q,u) if ax==1 else (u,v,q) for u,v in cs]
 for r in faces:
  cs=corners(r)
  for a,b in zip(cs,cs[1:]+cs[:1]):
   ax=next(i for i in range(3) if a[i]!=b[i]);key=tuple(a[i] for i in range(3) if i!=ax);edges[ax][key].update((a[ax],b[ax]))
 edges=[{k:sorted(v) for k,v in d.items()} for d in edges]
 points={};plist=[]
 def point(c):
  v=points.get(c)
  if v is None:v=len(points);points[c]=v;plist.append(c)
  return v
 def header(cls,obj):return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'
 with (pm/'faces').open('w') as out:
  out.write(header('faceList','faces')+f'{len(faces)}\n(\n')
  for r in faces:
   cs=corners(r);cs=cs if r[-1]==1 else cs[::-1];vs=[]
   for a,b in zip(cs,cs[1:]+cs[:1]):
    ax=next(i for i in range(3) if a[i]!=b[i]);key=tuple(a[i] for i in range(3) if i!=ax);vals=edges[ax][key]
    if a[ax]<b[ax]:vals=vals[bisect.bisect_left(vals,a[ax]):bisect.bisect_left(vals,b[ax])]
    else:vals=vals[bisect.bisect_right(vals,b[ax]):bisect.bisect_right(vals,a[ax])][::-1]
    for v in vals:
     c=list(a);c[ax]=v;vs.append(point(tuple(c)))
   out.write(str(len(vs))+'('+' '.join(map(str,vs))+')\n')
  out.write(')\n')
 del points,edges;gc.collect()
 with (pm/'points').open('w') as out:
  out.write(header('vectorField','points')+f'{len(plist)}\n(\n')
  for c in plist:out.write('('+' '.join(f'{v/S:.6f}' for v in c)+')\n')
  out.write(')\n')
 for name,col,nn in [('owner',6,len(faces)),('neighbour',7,nint)]:
  with (pm/name).open('w') as out:
   out.write(header('labelList',name)+f'{nn}\n(\n');out.writelines(str(r[col])+'\n' for r in faces[:nn]);out.write(')\n')
 with (pm/'boundary').open('w') as out:
  out.write(header('polyBoundaryMesh','boundary')+f'{len(patches)}\n(\n');start=nint
  for p in patches:
   typ='patch' if p in ('intake','outlet') else 'wall'
   out.write(f'{p}\n{{\n type {typ};\n'+(' inGroups 1(wall);\n' if typ=='wall' else '')+f' nFaces {counts[p]};\n startFace {start};\n}}\n');start+=counts[p]
  out.write(')\n')
 with (pm/'cellZones').open('w') as out:
  out.write(header('regIOobject','cellZones')+'5\n(\n')
  for name,y in [('ankle',.1),('knee',.6),('head',1.1),('standing',1.7)]:
   ids=[i for i,(x,Y,z) in enumerate(cells) if 1000000<x<3700000 and abs(z)<1450000 and abs(Y/S-y)<=.02+1e-8]
   out.write(f'occ_{name}\n{{\n type cellZone;\n cellLabels List<label>\n{len(ids)}\n(\n'+'\n'.join(map(str,ids))+'\n);\n}\n')
  # Regrade: the air in front of both heaters (x 0.30-0.40 m, y 0.06-0.70 m, |z| < 0.20 m), where the first production's
  # oil run held its cold column; its minimum is monitored every step.
  ids=[i for i,(x,Y,z) in enumerate(cells) if 300000<x<400000 and 60000<Y<700000 and abs(z)<200000]
  out.write(f'frontOfHeater\n{{\n type cellZone;\n cellLabels List<label>\n{len(ids)}\n(\n'+'\n'.join(map(str,ids))+'\n);\n}\n')
  out.write(')\n')
 info={'cells':len(cells),'faces':len(faces),'points':len(plist),'areas_m2':areas,'bounds_m':bounds,'section_z':.004,'ankle_y':.095,'method':'shared Cartesian columns; directional z refinement; conformal split polygon faces'}
 (OUT/f'mesh_{run}.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True)
if __name__=='__main__':
 # python3 scripts/<this>.py <meshDir>: the background mesh (no heater cut out) into <meshDir>/constant/polyMesh
 if len(sys.argv)!=2:raise SystemExit(__doc__+'\nusage: '+sys.argv[0]+' <meshDir>')
 OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=True)
 make('background')
