#!/usr/bin/env python3
"""Write one configuration's case: mesh (blockMeshDict), initial and boundary fields,
dictionaries. Called by Allrun; usage: generate_case.py single|dual [low|central|high] [dir]."""
import os,sys,shutil
import config as c
mode=sys.argv[1] if len(sys.argv)>1 else ''
load_name=sys.argv[2] if len(sys.argv)>2 else c.CENTRAL_LOAD
if mode not in ('single','dual') or load_name not in c.LOADS_W: raise SystemExit('usage: generate_case.py single|dual [low|central|high] [case]')
case=os.path.abspath(sys.argv[3] if len(sys.argv)>3 else f'run_{mode}')
heat_gain=c.LOADS_W[load_name]
if os.path.isdir(case): shutil.rmtree(case)
for d in ('0','constant','system'): os.makedirs(case+'/'+d)
qev=c.REPRESENTED_EVAPORATOR_M3S
qex=c.EXHAUST_CFM*c.CFM_TO_M3S
qout=0 if mode=='single' else c.DUAL_OUTDOOR_INTAKE_CFM*c.CFM_TO_M3S
qcond=qex-qout
scale=c.PLANE_THICKNESS/c.ROOM_HEIGHT
qev2=qev*scale; qcond2=qcond*scale
area_sum=c.DOOR_EFFECTIVE_AREA+c.WINDOW_EFFECTIVE_AREA
qdoor2=qcond2*c.DOOR_EFFECTIVE_AREA/area_sum
qwindow2=qcond2*c.WINDOW_EFFECTIVE_AREA/area_sum
crack_dp=0.5*(qcond/area_sum)**2
dT=c.SENSIBLE_COOLING_W/(c.RHO_REF*c.CP*qev)
H=lambda cls,obj,loc='0':f'''FoamFile\n{{ version 2.0; format ascii; class {cls}; location "{loc}"; object {obj}; }}\n'''
D=lambda obj:f'''FoamFile\n{{ version 2.0; format ascii; class dictionary; object {obj}; }}\n'''
# Conforming tensor grid with unit omitted. Door patch is on west wall; window patch remains north.
slot_c=0.5*(c.UNIT_X[0]+c.UNIT_X[1])
slot=(slot_c-0.5*c.SUPPLY_SLOT_WIDTH,slot_c+0.5*c.SUPPLY_SLOT_WIDTH)
bands1=(slot_c-0.05,slot_c+0.05)
bands2=(slot_c-0.20,slot_c+0.20)
bands3=(slot_c-0.40,slot_c+0.40)
xs=sorted(set([0,c.ROOM_X,*c.UNIT_X,c.UNIT_BACK_SPLIT,*slot,*c.WINDOW_GAP_X]))
ys=sorted(set([0,c.ROOM_Y,*c.UNIT_Y,c.UNIT_Y[0]-0.10,c.UNIT_Y[0]-0.50,*c.DOOR_GAP_Y]))
verts=[]; vid={}
for k,z in enumerate((0,c.PLANE_THICKNESS)):
 for j,y in enumerate(ys):
  for i,x in enumerate(xs): vid[i,j,k]=len(verts); verts.append((x,y,z))
def solid(x,y): return c.UNIT_X[0]-1e-10 < x < c.UNIT_X[1]+1e-10 and c.UNIT_Y[0]-1e-10 < y < c.UNIT_Y[1]+1e-10
def inrng(v,r): return r[0]-1e-9 <= v <= r[1]+1e-9
blocks=[]; patch={n:[] for n in ('doorGap','windowGap','evapSupply','evapReturn','condenserIntake','walls','unitWall','frontAndBack')}
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  x0,x1=xs[i:i+2]; y0,y1=ys[j:j+2]; xm=(x0+x1)/2; ym=(y0+y1)/2
  if solid(xm,ym): continue
  a=vid[i,j,0]; b=vid[i+1,j,0]; cc=vid[i+1,j+1,0]; d=vid[i,j+1,0]
  A=vid[i,j,1]; B=vid[i+1,j,1]; C=vid[i+1,j+1,1]; DD=vid[i,j+1,1]
  # Outlet-scale Cartesian mesh: 12 cells across the 0.30 m supply.
  if x0 >= slot[0]-1e-10 and x1 <= slot[1]+1e-10:
   nx=max(1,round((x1-x0)/(c.SUPPLY_SLOT_WIDTH/c.SUPPLY_CELLS)))
  else:
   nx=max(1,round((x1-x0)/c.DX))
  # 25 mm for the first 0.10 m of throw, then the 50 mm room grid.
  dy=0.025 if (ym >= c.UNIT_Y[0]-0.10-1e-10 and ym <= c.UNIT_Y[0]+1e-10) else c.DY
  ny=max(1,round((y1-y0)/dy))
  blocks.append(((a,b,cc,d,A,B,C,DD),nx,ny))
  patch['frontAndBack'] += [(a,d,cc,b),(A,B,C,DD)]
  # Add a face only where there is no neighbouring fluid block.
  faces=[('S',(a,b,B,A),xm,y0,0,-1),('N',(d,DD,C,cc),xm,y1,0,1),('W',(a,A,DD,d),x0,ym,-1,0),('E',(b,cc,C,B),x1,ym,1,0)]
  for side,face,xf,yf,di,dj in faces:
   ni,nj=i+di,j+dj
   neigh=(0<=ni<len(xs)-1 and 0<=nj<len(ys)-1 and not solid((xs[ni]+xs[ni+1])/2,(ys[nj]+ys[nj+1])/2))
   if neigh: continue
   name='walls'
   if side=='W' and abs(xf)<1e-9 and inrng(yf,c.DOOR_GAP_Y): name='doorGap'
   elif side=='N' and abs(yf-c.ROOM_Y)<1e-9 and inrng(xf,c.WINDOW_GAP_X): name='windowGap'
   elif side=='N' and abs(yf-c.UNIT_Y[0])<1e-9 and inrng(xf,slot): name='evapSupply'
   elif side=='N' and abs(yf-c.UNIT_Y[0])<1e-9 and inrng(xf,c.UNIT_X): name='unitWall'
   elif side=='S' and abs(yf-c.UNIT_Y[1])<1e-9 and inrng(xf,c.UNIT_X): name='evapReturn' if xf<c.UNIT_BACK_SPLIT else 'condenserIntake'
   elif (abs(xf-c.UNIT_X[0])<1e-9 or abs(xf-c.UNIT_X[1])<1e-9) and inrng(yf,c.UNIT_Y): name='unitWall'
   patch[name].append(face)
with open(case+'/system/blockMeshDict','w') as f:
 f.write(D('blockMeshDict')+'convertToMeters 1;\nvertices\n(\n')
 for v in verts:f.write(f' ({v[0]} {v[1]} {v[2]})\n')
 f.write(');\nblocks\n(\n')
 for vv,nx,ny in blocks:f.write(' hex ('+' '.join(map(str,vv))+f') ({nx} {ny} 1) simpleGrading (1 1 1)\n')
 f.write(');\nedges ();\nboundary\n(\n')
 for n,faces in patch.items():
  typ='empty' if n=='frontAndBack' else ('wall' if n in ('walls','unitWall') else 'patch')
  f.write(f' {n} {{ type {typ}; faces (\n')
  for face in faces:f.write('  ('+' '.join(map(str,face))+')\n')
  f.write(' ); }\n')
 f.write(');\nmergePatchPairs ();\n')
empty='frontAndBack { type empty; }'
U=H('volVectorField','U')+f'''dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0); boundaryField
{{ doorGap {{ type fixedValue; value uniform ({qdoor2/((c.DOOR_GAP_Y[1]-c.DOOR_GAP_Y[0])*c.PLANE_THICKNESS):.14g} 0 0); }} windowGap {{ type fixedValue; value uniform (0 {-qwindow2/((c.WINDOW_GAP_X[1]-c.WINDOW_GAP_X[0])*c.PLANE_THICKNESS):.14g} 0); }}
 evapSupply {{ type flowRateInletVelocity; volumetricFlowRate constant {qev2:.12g}; value uniform (0 {-c.SUPPLY_VELOCITY} 0); }}
 evapReturn {{ type flowRateOutletVelocity; volumetricFlowRate constant {qev2:.12g}; value uniform (0 -0.39 0); }}
 condenserIntake {{ type flowRateOutletVelocity; volumetricFlowRate constant {qcond2:.12g}; value uniform (0 -0.3 0); }}
 walls {{ type noSlip; }} unitWall {{ type noSlip; }} {empty} }}\n'''
T=H('volScalarField','T')+f'''dimensions [0 0 0 1 0 0 0]; internalField uniform {c.T_ROOM}; boundaryField
{{ doorGap {{ type inletOutlet; inletValue uniform {c.T_OUTDOOR}; value uniform {c.T_ROOM}; }} windowGap {{ type inletOutlet; inletValue uniform {c.T_OUTDOOR}; value uniform {c.T_ROOM}; }}
 evapSupply {{ type codedFixedValue; value uniform {c.T_ROOM-dT}; name fixedSensibleCapacity; code #{{ const fvMesh& mesh=patch().boundaryMesh().mesh(); const label id=mesh.boundaryMesh().findPatchID("evapReturn"); const fvPatchScalarField& Tr=mesh.lookupObject<volScalarField>("T").boundaryField()[id]; const scalarField& ar=mesh.boundary()[id].magSf(); const volScalarField& Tf=mesh.lookupObject<volScalarField>("T"); const scalar Troom=gSum(Tf.primitiveField()*mesh.V().field())/gSum(mesh.V().field()); static bool cooling=true; static scalar lastSwitch=scalar(0); const scalar now=mesh.time().value(); const scalar setpoint=scalar({c.THERMOSTAT_SETPOINT_C+273.15:.14g}); const scalar halfDB=scalar({c.THERMOSTAT_DEADBAND_K/2:.14g}); if (cooling && Troom <= setpoint-halfDB && now-lastSwitch >= scalar({c.MIN_ON_TIME_S:.14g})) {{ cooling=false; lastSwitch=now; }} else if (!cooling && Troom >= setpoint+halfDB && now-lastSwitch >= scalar({c.MIN_OFF_TIME_S:.14g})) {{ cooling=true; lastSwitch=now; }} operator==(gSum(Tr*ar)/gSum(ar)-(cooling ? scalar({dT:.14g}) : scalar(0))); #}}; }}
 evapReturn {{ type zeroGradient; }} condenserIntake {{ type zeroGradient; }} walls {{ type zeroGradient; }} unitWall {{ type zeroGradient; }} {empty} }}\n'''
p_rgh=H('volScalarField','p_rgh')+f'''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField
{{ doorGap {{ type fixedFluxPressure; rho rhok; value uniform 0; }} windowGap {{ type fixedFluxPressure; rho rhok; value uniform 0; }} evapSupply {{ type fixedFluxPressure; rho rhok; value uniform 0; }} evapReturn {{ type fixedFluxPressure; rho rhok; value uniform 0; }} condenserIntake {{ type fixedFluxPressure; rho rhok; value uniform 0; }} walls {{ type fixedFluxPressure; rho rhok; value uniform 0; }} unitWall {{ type fixedFluxPressure; rho rhok; value uniform 0; }} {empty} }}\n'''
p=H('volScalarField','p')+f'''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField {{ doorGap {{type calculated; value uniform 0;}} windowGap {{type calculated; value uniform 0;}} evapSupply {{type calculated; value uniform 0;}} evapReturn {{type calculated; value uniform 0;}} condenserIntake {{type calculated; value uniform 0;}} walls {{type calculated; value uniform 0;}} unitWall {{type calculated; value uniform 0;}} {empty} }}\n'''
def tf(name,dim,iv,wt,inn): return H('volScalarField',name)+f'''dimensions {dim}; internalField uniform {iv}; boundaryField {{ doorGap {{type inletOutlet; inletValue uniform {inn}; value uniform {iv};}} windowGap {{type inletOutlet; inletValue uniform {inn}; value uniform {iv};}} evapSupply {{type fixedValue; value uniform {inn};}} evapReturn {{type inletOutlet; inletValue uniform {inn}; value uniform {iv};}} condenserIntake {{type inletOutlet; inletValue uniform {inn}; value uniform {iv};}} walls {{type {wt}; value uniform {iv};}} unitWall {{type {wt}; value uniform {iv};}} {empty} }}\n'''
k_amb=1e-8; eps_amb=0.09**0.75*k_amb**1.5/0.10
k_in=1.5*(0.05*c.SUPPLY_VELOCITY)**2; eps_in=0.09**0.75*k_in**1.5/c.SUPPLY_SLOT_WIDTH
k=tf('k','[0 2 -2 0 0 0 0]',k_amb,'kqRWallFunction',k_in)
epsilon=tf('epsilon','[0 2 -3 0 0 0 0]',eps_amb,'epsilonWallFunction',eps_in)
nut=tf('nut','[0 2 -1 0 0 0 0]',0,'nutkWallFunction',0)
alphat=H('volScalarField','alphat')+f'''dimensions [0 2 -1 0 0 0 0]; internalField uniform 0; boundaryField {{ doorGap {{type calculated; value uniform 0;}} windowGap {{type calculated; value uniform 0;}} evapSupply {{type calculated; value uniform 0;}} evapReturn {{type calculated; value uniform 0;}} condenserIntake {{type calculated; value uniform 0;}} walls {{type alphatJayatillekeWallFunction; Prt {c.PRT}; value uniform 0;}} unitWall {{type alphatJayatillekeWallFunction; Prt {c.PRT}; value uniform 0;}} {empty} }}\n'''
for n,s in [('U',U),('T',T),('p_rgh',p_rgh),('p',p),('k',k),('epsilon',epsilon),('nut',nut),('alphat',alphat)]:open(case+'/0/'+n,'w').write(s)
open(case+'/constant/g','w').write('FoamFile {version 2.0; format ascii; class uniformDimensionedVectorField; object g;}\ndimensions [0 1 -2 0 0 0 0]; value (0 0 0);\n')
open(case+'/constant/transportProperties','w').write(D('transportProperties')+f'transportModel Newtonian; nu {c.NU}; beta {c.BETA}; TRef {c.T_ROOM}; Pr {c.PR}; Prt {c.PRT};\n')
# Final frozen gain representation: the full 900 W (or selected sensitivity load)
# is a uniform volumetric source over all room-air cells.  The plane/full-room
# mapping preserves total physical watts.
source_scale=c.PLANE_THICKNESS/c.ROOM_HEIGHT
absolute_T_source=heat_gain/(c.RHO_REF*c.CP)*source_scale
fvo=D('fvOptions') + f"""roomHeat
{{
 type scalarSemiImplicitSource;
 active true;
 selectionMode all;
 volumeMode absolute;
 sources {{ T ({absolute_T_source:.14g} 0); }}
}}
"""
open(case+'/constant/fvOptions','w').write(fvo)
open(case+'/constant/turbulenceProperties','w').write(D('turbulenceProperties')+'simulationType RAS; RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }\n')
open(case+'/system/fvSchemes','w').write(D('fvSchemes')+'''ddtSchemes {default Euler;} gradSchemes {default cellLimited Gauss linear 1;} divSchemes {default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,T) bounded Gauss limitedLinear 1; div(phi,k) bounded Gauss upwind; div(phi,epsilon) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear;} laplacianSchemes {default Gauss linear corrected;} interpolationSchemes {default linear;} snGradSchemes {default corrected;} wallDist {method meshWave;}\n''')
open(case+'/system/fvSolution','w').write(D('fvSolution')+'''solvers { p_rgh {solver GAMG; smoother DIC; tolerance 1e-7; relTol 0.03;} p_rghFinal {$p_rgh; relTol 0;} "(U|T|k|epsilon)" {solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.03;} "(U|T|k|epsilon)Final" {$U; relTol 0;} } PIMPLE {momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0;} relaxationFactors {equations {"(U|T|k|epsilon).*" 0.8;}}\n''')
func='''roomMean {type volFieldValue; libs (fieldFunctionObjects); regionType all; operation volAverage; fields (T); writeControl writeTime; writeFields false;} evapReturnMean {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name evapReturn; operation areaAverage; fields (T); writeControl writeTime; writeFields false;} evapSupplyMean {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name evapSupply; operation areaAverage; fields (T); writeControl writeTime; writeFields false;} doorNet {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name doorGap; operation sum; fields (phi); writeControl writeTime; writeFields false;} doorMag {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name doorGap; operation sumMag; fields (phi); writeControl writeTime; writeFields false;} windowNet {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name windowGap; operation sum; fields (phi); writeControl writeTime; writeFields false;} windowMag {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name windowGap; operation sumMag; fields (phi); writeControl writeTime; writeFields false;} condenserIntakeMean {type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name condenserIntake; operation areaAverage; fields (T); writeControl writeTime; writeFields false;}'''
open(case+'/system/controlDict','w').write(D('controlDict')+f'''application buoyantBoussinesqPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {c.END_TIME}; deltaT {c.DT}; adjustTimeStep yes; maxCo {c.MAX_CO}; maxDeltaT {c.DT}; writeControl adjustableRunTime; writeInterval {c.WRITE_INTERVAL}; purgeWrite 0; writeFormat binary; writeCompression off; timeFormat general; timePrecision 8; runTimeModifiable false; functions {{{func}}}\n''')
open(case+'/system/decomposeParDict','w').write(D('decomposeParDict')+f'numberOfSubdomains {c.NPROCS}; method scotch;\n')
open(case+'/CASE_META.txt','w').write(f'mode={mode}\nload_name={load_name}\nheat_gain_W={heat_gain}\nthermostat_setpoint_C={c.THERMOSTAT_SETPOINT_C}\nthermostat_deadband_K={c.THERMOSTAT_DEADBAND_K}\nminimum_off_time_s={c.MIN_OFF_TIME_S}\nminimum_on_time_s={c.MIN_ON_TIME_S}\nheat_placement=uniform_whole_room_air\nflux_scale={c.ROOM_HEIGHT/c.PLANE_THICKNESS}\nevaporator_m3s={qev}\nfixed_cooling_W={c.SENSIBLE_COOLING_W}\nevaporator_deltaT_K={dT}\ncondenser_exhaust_m3s={qex}\noutdoor_intake_m3s={qout}\nexpected_infiltration_m3s={qcond}\ndoor_effective_area_m2={c.DOOR_EFFECTIVE_AREA}\nwindow_effective_area_m2={c.WINDOW_EFFECTIVE_AREA}\nparallel_crack_pressure_drop_kinematic={crack_dp}\nleak_model=distributed_parallel_crack_network\nreal_evaporator_m3s={c.REAL_EVAPORATOR_M3S}\nreal_outlet_velocity_mps={c.REAL_OUTLET_VELOCITY}\ntarget_momentum_flux_N={c.TARGET_MOMENTUM_N}\nrepresented_evaporator_m3s={c.REPRESENTED_EVAPORATOR_M3S}\nrepresented_to_real_flow_ratio={c.REPRESENTED_EVAPORATOR_M3S/c.REAL_EVAPORATOR_M3S}\nsupply_plan_area_m2={c.SUPPLY_SLOT_WIDTH*c.ROOM_HEIGHT}\nsupply_velocity_mps={c.SUPPLY_VELOCITY}\nsupply_slot_width_m={c.SUPPLY_SLOT_WIDTH}\nsupply_cells_across={c.SUPPLY_CELLS}\nambient_k={k_amb}\nambient_epsilon={eps_amb}\nsupply_k={k_in}\nsupply_epsilon={eps_in}\n')
print(case,mode,load_name,heat_gain,'W; Qleak expected',qcond,'m3/s')
