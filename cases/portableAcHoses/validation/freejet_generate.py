#!/usr/bin/env python3
from pathlib import Path
import sys,shutil,math
level=sys.argv[1] if len(sys.argv)>1 else 'medium'
root=Path(__file__).resolve().parent; case=root/f'freejet_{level}'
if case.exists(): shutil.rmtree(case)
for d in ['0','constant','system']: (case/d).mkdir(parents=True,exist_ok=True)
b=0.30; U0=(1.36/(1.20*b*2.5))**0.5; nu=1.5e-5; I=.05
k0=1.5*(I*U0)**2; L=b; eps0=.09**.75*k0**1.5/L
ka=1e-8; La=.10; epsa=.09**.75*ka**1.5/La
# Domain has boundaries at least 1 m from the jet axis. Piecewise Cartesian mesh.
xs=[0,.30,1.0,3.0,4.0]; ys=[0.,b/2,.30,.60,1.50,5.]
base_x=[8,14,40,10]; base_y=[5,5,8,12,20]
fac={'coarse':1,'medium':2,'fine':3}[level]
nxs=[n*fac for n in base_x]; nys=[n*fac for n in base_y]
z=[0,.01]; verts=[]; vid={}
for kk,zz in enumerate(z):
 for j,y in enumerate(ys):
  for i,x in enumerate(xs):vid[i,j,kk]=len(verts);verts.append((x,y,zz))
blocks=[]; patches={n:[] for n in ['jetInlet','nozzleWall','farField','outlet','axis','frontAndBack']}
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  a=vid[i,j,0];bb=vid[i+1,j,0];c=vid[i+1,j+1,0];d=vid[i,j+1,0];A=vid[i,j,1];B=vid[i+1,j,1];C=vid[i+1,j+1,1];D=vid[i,j+1,1]
  blocks.append(((a,bb,c,d,A,B,C,D),nxs[i],nys[j]))
  patches['frontAndBack'] += [(a,d,c,bb),(A,B,C,D)]
  if i==0:
   p='jetInlet' if ys[j+1]<=b/2+1e-10 else 'nozzleWall'; patches[p].append((a,A,D,d))
  if i==len(xs)-2: patches['outlet'].append((bb,c,C,B))
  if j==0: patches['axis'].append((a,bb,B,A))
  if j==len(ys)-2: patches['farField'].append((d,D,C,c))
H=lambda cls,obj,loc='0':f'FoamFile\n{{ version 2.0; format ascii; class {cls}; location "{loc}"; object {obj}; }}\n'
D=lambda obj:H('dictionary',obj,'system')
with (case/'system/blockMeshDict').open('w') as f:
 f.write(D('blockMeshDict')+'convertToMeters 1;\nvertices\n(\n');[f.write(f' ({x} {y} {zz})\n') for x,y,zz in verts];f.write(');\nblocks\n(\n')
 for vv,nx,ny in blocks:f.write(' hex ('+' '.join(map(str,vv))+f') ({nx} {ny} 1) simpleGrading (1 1 1)\n')
 f.write(');\nedges ();\nboundary\n(\n')
 for name,faces in patches.items():
  typ='empty' if name=='frontAndBack' else ('symmetryPlane' if name in ('axis','farField') else 'patch');f.write(f' {name} {{ type {typ}; faces (\n');[f.write('  ('+' '.join(map(str,q))+')\n') for q in faces];f.write(' ); }\n')
 f.write(');\nmergePatchPairs ();\n')
empty='frontAndBack {type empty;} axis {type symmetryPlane;}'
(case/'0/U').write_text(H('volVectorField','U')+f'''dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0); boundaryField {{ jetInlet {{type fixedValue; value uniform ({U0} 0 0);}} farField {{type symmetryPlane;}} outlet {{type pressureInletOutletVelocity; value uniform (0 0 0);}} nozzleWall {{type fixedValue; value uniform (0.05 0 0);}} {empty} }}\n''')
(case/'0/p').write_text(H('volScalarField','p')+f'''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField {{jetInlet {{type zeroGradient;}} farField {{type symmetryPlane;}} outlet {{type fixedValue; value uniform 0;}} nozzleWall {{type zeroGradient;}} {empty}}}\n''')
def turb(n,dim,iv,jv):return H('volScalarField',n)+f'''dimensions {dim}; internalField uniform {iv}; boundaryField {{jetInlet {{type fixedValue; value uniform {jv};}} farField {{type symmetryPlane;}} outlet {{type inletOutlet; inletValue uniform {iv}; value uniform {iv};}} nozzleWall {{type fixedValue; value uniform {iv};}} {empty}}}\n'''
(case/'0/k').write_text(turb('k','[0 2 -2 0 0 0 0]',ka,k0));(case/'0/epsilon').write_text(turb('epsilon','[0 2 -3 0 0 0 0]',epsa,eps0));(case/'0/nut').write_text(turb('nut','[0 2 -1 0 0 0 0]',0,0))
(case/'constant/transportProperties').write_text(H('dictionary','transportProperties','constant')+f'transportModel Newtonian; nu {nu};\n')
(case/'constant/turbulenceProperties').write_text(H('dictionary','turbulenceProperties','constant')+'simulationType RAS; RAS {RASModel kEpsilon; turbulence on; printCoeffs on;}\n')
(case/'system/fvSchemes').write_text(D('fvSchemes')+'''ddtSchemes {default steadyState;} gradSchemes {default cellLimited Gauss linear 1;} divSchemes {default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear;} laplacianSchemes {default Gauss linear corrected;} interpolationSchemes {default linear;} snGradSchemes {default corrected;} wallDist {method meshWave;}\n''')
(case/'system/fvSolution').write_text(D('fvSolution')+'''solvers {p {solver GAMG; smoother DIC; tolerance 1e-8; relTol .05;} U {solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol .05;} "(k|epsilon)" {solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol .05;}} SIMPLE {nNonOrthogonalCorrectors 0; consistent yes;} relaxationFactors {fields {p .3;} equations {U .7; k .7; epsilon .7;}} residualControl {p 1e-6; U 1e-6; k 1e-6; epsilon 1e-6;}\n''')
(case/'system/controlDict').write_text(D('controlDict')+'''application simpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 3000; deltaT 1; writeControl timeStep; writeInterval 3000; purgeWrite 0; writeFormat binary; runTimeModifiable false;\n''')
(case/'system/decomposeParDict').write_text(D('decomposeParDict')+'numberOfSubdomains 8; method scotch;\n')
(case/'FREEJET_META.txt').write_text(f'b={b}\nU0={U0}\ninlet_intensity={I}\ninlet_k={k0}\ninlet_length_scale={L}\ninlet_epsilon={eps0}\nambient_k={ka}\nambient_length_scale={La}\nambient_epsilon={epsa}\nmesh_level={level}\ncells={sum(nxs)*sum(nys)}\n')
print(case, 'cells',sum(nxs)*sum(nys), 'k/eps inlet',k0,eps0)
