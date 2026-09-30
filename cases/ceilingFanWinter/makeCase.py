#!/usr/bin/env python3
import sys, math, shutil
from pathlib import Path
if len(sys.argv)!=4: raise SystemExit('usage: makeCase.py CASE down|up|off low|medium')
case=Path(sys.argv[1]); direction=sys.argv[2]; speed=sys.argv[3]
if direction not in ('down','up','off') or speed not in ('low','medium'): raise SystemExit('bad direction/speed')
cfg={}
for line in Path('config.sh').read_text().splitlines():
    s=line.split('#',1)[0].strip()
    if '=' in s:
        k,v=s.split('=',1); cfg[k.strip()]=v.strip().strip('"')
f=lambda k:float(cfg[k]); n=lambda k:int(cfg[k])
rbreak=list(map(float,cfg['R_BREAKS'].split())); nr=list(map(int,cfg['R_CELLS'].split()))
zbreak=list(map(float,cfg['Z_BREAKS'].split())); nz=list(map(int,cfg['Z_CELLS'].split()))
if case.exists(): shutil.rmtree(case)
for d in ('0','constant','system'): (case/d).mkdir(parents=True,exist_ok=True)
hdr=lambda cls,obj,loc='':f'''FoamFile\n{{\n version 2.0; format ascii; class {cls}; location "{loc}"; object {obj};\n}}\n'''
# Vertices: shared point on axis, separate +/- wedge points elsewhere.
a=math.radians(f('WEDGE_DEG')/2); verts=[]; idx={}
for j,z in enumerate(zbreak):
  for i,r in enumerate(rbreak):
    if i==0:
      idx[(i,j,-1)]=idx[(i,j,1)]=len(verts); verts.append((0,0,z))
    else:
      for s in (-1,1):
        idx[(i,j,s)]=len(verts); verts.append((r*math.cos(a),s*r*math.sin(a),z))
blocks=[]; wminus=[]; wplus=[]; floor=[]; ceil=[]; axis=[]; wall=[]
for j in range(len(zbreak)-1):
  for i in range(len(rbreak)-1):
    v=(idx[(i,j,-1)],idx[(i+1,j,-1)],idx[(i+1,j,1)],idx[(i,j,1)],idx[(i,j+1,-1)],idx[(i+1,j+1,-1)],idx[(i+1,j+1,1)],idx[(i,j+1,1)])
    blocks.append((v,nr[i],nz[j]))
    wminus.append((v[0],v[1],v[5],v[4])); wplus.append((v[3],v[7],v[6],v[2]))
    if j==0: floor.append((v[0],v[3],v[2],v[1]))
    if j==len(zbreak)-2: ceil.append((v[4],v[5],v[6],v[7]))
    if i==0: axis.append((v[0],v[4],v[7],v[3]))
    if i==len(rbreak)-2: wall.append((v[1],v[2],v[6],v[5]))
fmtv=lambda v:f'({v[0]:.12g} {v[1]:.12g} {v[2]:.12g})'
fmtf=lambda q:'('+' '.join(map(str,q))+')'
def patch(name,typ,faces): return f''' {name}\n {{\n  type {typ};\n  faces\n  (\n{chr(10).join('   '+fmtf(x) for x in faces)}\n  );\n }}\n'''
bm=hdr('dictionary','blockMeshDict','system')+'mergeType points;\nconvertToMeters 1;\nvertices\n(\n'+'\n'.join(' '+fmtv(v) for v in verts)+'\n);\nblocks\n(\n'
for v,ni,nj in blocks: bm+=f' hex {fmtf(v)} ({ni} 1 {nj}) simpleGrading (1 1 1)\n'
bm+=');\nedges ();\nboundary\n(\n'+patch('wedgeMinus','wedge',wminus)+patch('wedgePlus','wedge',wplus)+patch('floor','wall',floor)+patch('ceiling','wall',ceil)+patch('outerWall','wall',wall)+patch('axis','empty',axis)+');\n'
(case/'system/blockMeshDict').write_text(bm)
# cell zones use boxes spanning wedge extents. Box selection is adequate at this 5-degree slice.
R=f('ROOM_RADIUS'); tang=R*math.sin(a)+.01
(case/'system/topoSetDict').write_text(hdr('dictionary','topoSetDict','system')+f'''actions
(
 {{ name fanZone; type cellZoneSet; action new; source boxToCell; box (0 {-tang} {f('FAN_Z0')}) ({f('FAN_RADIUS')} {tang} {f('FAN_Z1')}); }}
 {{ name fanZone; type cellZoneSet; action delete; source boxToCell; box (-0.001 {-tang} {f('FAN_Z0')-.001}) ({f('FAN_HUB_RADIUS')} {tang} {f('FAN_Z1')+.001}); }}
 {{ name heaterZone; type cellZoneSet; action new; source boxToCell; box ({f('HEATER_R0')*math.cos(a)-.002} {-tang} {f('HEATER_Z0')}) ({R+.002} {tang} {f('HEATER_Z1')}); }}
);
''')
# Boundary dictionaries. Robin wall uses alpha and local representative first-cell distance.
# h/(rho Cp) is a velocity; mixed fraction h*delta/(alpha+h*delta).
alpha=f('NU')/f('PR'); heff=f('WALL_H')/(f('RHO')*f('CP'))
def vf(delta): return heff*delta/(alpha+heff*delta)
Tbc=f'''wedgeMinus {{ type wedge; }} wedgePlus {{ type wedge; }} axis {{ type empty; }}
floor {{ type mixed; refValue uniform {f('T_AMBIENT')}; refGradient uniform 0; valueFraction uniform {vf(0.010):.8g}; value uniform {f('T0')}; }}
ceiling {{ type mixed; refValue uniform {f('T_AMBIENT')}; refGradient uniform 0; valueFraction uniform {vf(0.009615):.8g}; value uniform {f('T0')}; }}
outerWall {{ type mixed; refValue uniform {f('T_AMBIENT')}; refGradient uniform 0; valueFraction uniform {vf(0.00961538):.8g}; value uniform {f('T0')}; }}'''
Ubc='''wedgeMinus { type wedge; } wedgePlus { type wedge; } axis { type empty; } floor { type noSlip; } ceiling { type noSlip; } outerWall { type noSlip; }'''
wallbc={
'k':'''floor { type kqRWallFunction; value uniform 1e-4; } ceiling { type kqRWallFunction; value uniform 1e-4; } outerWall { type kqRWallFunction; value uniform 1e-4; }''',
'epsilon':'''floor { type epsilonWallFunction; value uniform 1e-4; } ceiling { type epsilonWallFunction; value uniform 1e-4; } outerWall { type epsilonWallFunction; value uniform 1e-4; }''',
'nut':'''floor { type nutkWallFunction; value uniform 0; } ceiling { type nutkWallFunction; value uniform 0; } outerWall { type nutkWallFunction; value uniform 0; }''',
'alphat':'''floor { type alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; } ceiling { type alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; } outerWall { type alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; }'''}
for obj,dim,internal,bc in [
 ('U','[0 1 -1 0 0 0 0]','uniform (0 0 0)',Ubc),('T','[0 0 0 1 0 0 0]',f'uniform {f("T0")}',Tbc),
 ('p_rgh','[0 2 -2 0 0 0 0]','uniform 0','''wedgeMinus { type wedge; } wedgePlus { type wedge; } axis { type empty; } floor { type fixedFluxPressure; value uniform 0; } ceiling { type fixedFluxPressure; value uniform 0; } outerWall { type fixedFluxPressure; value uniform 0; }'''),
 ('k','[0 2 -2 0 0 0 0]',f'uniform {f("K0")}',None),('epsilon','[0 2 -3 0 0 0 0]',f'uniform {f("EPSILON0")}',None),
 ('nut','[0 2 -1 0 0 0 0]','uniform 0',None),('alphat','[0 2 -1 0 0 0 0]','uniform 0',None)]:
  if bc is None: bc='wedgeMinus { type wedge; } wedgePlus { type wedge; } axis { type empty; } '+wallbc[obj]
  cls='volVectorField' if obj=='U' else 'volScalarField'
  (case/f'0/{obj}').write_text(hdr(cls,obj,'0')+f'dimensions {dim};\ninternalField {internal};\nboundaryField {{ {bc} }}\n')
(case/'constant/g').write_text(hdr('uniformDimensionedVectorField','g','constant')+'dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);\n')
(case/'constant/transportProperties').write_text(hdr('dictionary','transportProperties','constant')+f'''transportModel Newtonian;
nu [0 2 -1 0 0 0 0] {f('NU')}; beta [0 0 0 -1 0 0 0] {f('BETA')}; TRef [0 0 0 1 0 0 0] {f('TREF')}; Pr [0 0 0 0 0 0 0] {f('PR')}; Prt [0 0 0 0 0 0 0] {f('PRT')};
''')
(case/'constant/turbulenceProperties').write_text(hdr('dictionary','turbulenceProperties','constant')+'simulationType RAS;\nRAS { RASModel realizableKE; turbulence on; printCoeffs on; }\n')
Q=f('FLOW_'+speed.upper()); A=math.pi*(f('FAN_RADIUS')**2-f('FAN_HUB_RADIUS')**2); uz=Q/A; ut=f('SWIRL_RATIO')*uz
sgn=-1 if direction=='down' else 1
# reversed operation flips both axial and tangential components. At center plane y is theta.
fan='' if direction=='off' else f'''axialDrive
{{ type meanVelocityForce; active true; selectionMode cellZone; cellZone fanZone; fields (U); Ubar (0 0 {sgn*uz:.10g}); }}
swirlDrive
{{ type meanVelocityForce; active true; selectionMode cellZone; cellZone fanZone; fields (U); Ubar (0 {sgn*ut:.10g} 0); }}
'''
# Absolute source must be wedge fraction of full-ring power.
frac=f('WEDGE_DEG')/360.; heat=f('HEATER_W')*frac/(f('RHO')*f('CP'))
(case/'constant/fvOptions').write_text(hdr('dictionary','fvOptions','constant')+fan+f'''heater
{{ type scalarSemiImplicitSource; active true; selectionMode cellZone; cellZone heaterZone; volumeMode absolute; sources {{ T ({heat:.12g} 0); }} }}
''')
(case/'system/fvSchemes').write_text(hdr('dictionary','fvSchemes','system')+'''ddtSchemes { default Euler; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,T) bounded Gauss linearUpwind grad(T); div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p_rgh; alphat; }
''')
(case/'system/fvSolution').write_text(hdr('dictionary','fvSolution','system')+'''solvers
{
 p_rgh { solver GAMG; tolerance 1e-7; relTol 0.05; smoother DICGaussSeidel; }
 p_rghFinal { $p_rgh; relTol 0; }
 "(U|T|k|epsilon)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.05; }
 "(U|T|k|epsilon)Final" { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; }
relaxationFactors { equations { ".*" 1; } }
''')
# Single solved half-face; y=0 means components are exactly (Ur,Utheta,Uz).
(case/'system/controlDict').write_text(hdr('dictionary','controlDict','system')+f'''application buoyantBoussinesqPimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime {f('END_TIME')}; deltaT {f('DT')};
writeControl runTime; writeInterval {f('END_TIME')}; writeFormat binary; writeCompression on; purgeWrite 1;
adjustTimeStep yes; maxCo {f('MAX_CO')}; maxDeltaT {f('DT')}; runTimeModifiable false;
functions
{{ rzFace {{ type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {f('SAMPLE_DT')}; surfaceFormat vtk; interpolationScheme cellPoint; fields (U T); surfaces ( rz {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (0 1 0); }} interpolate true; }} ); }} }}
''')
(case/'system/decomposeParDict').write_text(hdr('dictionary','decomposeParDict','system')+f'numberOfSubdomains {n("NPROCS")}; method scotch;\n')
(case/'caseInfo.txt').write_text(f'''dimensionality=axisymmetric 5-degree one-cell wedge\ndirection={direction}\nspeed={speed}\nflowTarget_m3s={0 if direction=='off' else Q}\nUzTarget_mps={0 if direction=='off' else sgn*uz}\nUthetaTarget_mps={0 if direction=='off' else sgn*ut}\nswirlRatio={f('SWIRL_RATIO')}\nfullHeater_W={f('HEATER_W')}\nwedgeHeater_W={f('HEATER_W')*frac}\nwindow_s={f('END_TIME')}\n''')
