#!/usr/bin/env python3
"""Generate one layout case from config/model.json and the common generated mesh.

    python3 make_case.py <layout>          # runs/<layout>
    python3 make_case.py <layout> --dust   # runs/<layout>_dust: the same case with two
                                           # passive dust fields carried on its flow
"""
import json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'config/model.json').read_text())
layout=sys.argv[1] if len(sys.argv)>1 else 'positive'
dust=sys.argv[2:]==['--dust']
if sys.argv[2:] and not dust: raise SystemExit('usage: make_case.py <layout> [--dust]')
if layout not in C['layouts']: raise SystemExit('layout must be positive, negative, even, viewer, or twoInTwoOut')
# A layout with its own geometry (the viewer's turned cooler and bottom fans) has its own mesh.
variant=C['layouts'][layout].get('geometry','')
MESH=ROOT/'mesh'/variant if variant else ROOT/'mesh'
out=ROOT/'runs'/(layout+('_dust' if dust else ''))
if out.exists(): shutil.rmtree(out)
(out/'constant').mkdir(parents=True); (out/'system').mkdir(); (out/'0').mkdir()
shutil.copytree(MESH/'constant/polyMesh',out/'constant/polyMesh')
# snappy leaves an empty frozenPoints zone; omit it (and avoid simplified-mesh dry-run bug).
for z in ('pointZones','faceZones','cellZones'):
    (out/'constant/polyMesh'/z).unlink(missing_ok=True)

hdr=lambda cls,obj: f'''FoamFile\n{{\n version 2.0; format ascii; class {cls}; object {obj};\n}}\n'''
# Merge black-box openings so mapped heat BC sees all source/sink faces together.
cp=hdr('dictionary','createPatchDict')+'''pointSync false;\npatches\n(\n { name gpu_in; patchInfo { type patch; } constructFrom patches; patches (gpu_in_1 gpu_in_2 gpu_in_3); }\n { name gpu_out; patchInfo { type patch; } constructFrom patches; patches (gpu_out_board_side gpu_out_flow_through gpu_out_front_end gpu_out_glass_side); }\n);\n'''
(out/'system/createPatchDict').write_text(cp)

bottom=['bottom_front','bottom_rear'] if variant=='viewer' else []
allfans=['front_low','front_mid','front_high']+bottom+['rear','top_front','top_rear']
active=C['layouts'][layout]; intake=set(active['intake']); exhaust=set(active['exhaust'])
Q120=C['fan120Flow_m3_s']; Q140=C['fan140Flow_m3_s']
def qfan(n): return Q140 if n.startswith('top_') else Q120

def openU(): return '''type pressureInletOutletVelocity; value uniform (0 0 0);'''
def flowU(q): return f'''type flowRateInletVelocity; volumetricFlowRate constant {q:.8g}; extrapolateProfile no; value uniform (0 0 0);'''
def pLoss(K): return f'''type codedFixedValue; name ventLossK{int(K)}; value uniform 0;\n code\n #{{\n   const fvPatchVectorField& Up = patch().lookupPatchField<volVectorField, vector>("U");\n   const scalarField Un(Up & patch().nf());\n   operator==(0.5*{K}*Un*mag(Un));\n #}};'''
def scalarOpen(inlet): return f'''type inletOutlet; inletValue uniform {inlet}; value uniform {inlet};'''

def field(obj,dims,internal,entries):
    return hdr('vol'+('Vector' if str(internal).startswith('(') else 'Scalar')+'Field',obj)+f'''dimensions {dims};\ninternalField uniform {internal};\nboundaryField\n{{\n{entries}\n}}\n'''

# velocity
E=['walls { type noSlip; }','gpu_in { '+flowU(-C['gpuFlow_m3_s'])+' }','gpu_out { '+flowU(C['gpuFlow_m3_s'])+' }','cpu_in { '+flowU(-C['cpuFlow_m3_s'])+' }','cpu_out { '+flowU(C['cpuFlow_m3_s'])+' }']
for v in ('vent_front','vent_top','vent_slots'): E.append(v+' { '+openU()+' }')
for n in allfans:
    q=qfan(n) if n in intake else (-qfan(n) if n in exhaust else None)
    E.append('fan_'+n+' { '+(flowU(q) if q is not None else openU())+' }')
(out/'0/U').write_text(field('U','[0 1 -1 0 0 0 0]','(0 0 0)','\n'.join(E)))
# pressure: active fixed-flow boundaries Neumann; room-connected openings quadratic loss
E=['walls { type zeroGradient; }','gpu_in { type zeroGradient; }','gpu_out { type zeroGradient; }','cpu_in { type zeroGradient; }','cpu_out { type zeroGradient; }']
for v,K in [('vent_front',C['filterLossCoefficient']),('vent_top',C['filterLossCoefficient']),('vent_slots',C['slotLossCoefficient'])]: E.append(v+' { '+pLoss(K)+' }')
for n in allfans: E.append('fan_'+n+' { '+('type zeroGradient;' if n in intake or n in exhaust else pLoss(C['filterLossCoefficient']))+' }')
(out/'0/p').write_text(field('p','[0 2 -2 0 0 0 0]',0,'\n'.join(E)))
# temperature. Positive Q enters domain at gpu_out/cpu_out and maps flow-weighted source outlet.
T0=C['roomTemperature_K']
def mappedT(patch,source,heat,flow):
    rise=heat/(C['rhoReference_kg_m3']*C['cp_J_kgK']*flow)
    return f'''{patch} {{ type codedFixedValue; name mappedHeat{patch.title().replace('_','')}; value uniform {T0}; code #{{ const volScalarField& Tf=db().lookupObject<volScalarField>("T"); const label id=patch().boundaryMesh().findPatchID("{source}"); const scalarField& Ts=Tf.boundaryField()[id]; const scalarField& a=patch().boundaryMesh()[id].magSf(); operator==(gSum(a*Ts)/gSum(a) + {rise}); #}}; }}'''
E=['walls { type zeroGradient; }','gpu_in { type zeroGradient; }',mappedT('gpu_out','gpu_in',C['gpuHeat_W'],C['gpuFlow_m3_s']), 'cpu_in { type zeroGradient; }',mappedT('cpu_out','cpu_in',C['cpuHeat_W'],C['cpuFlow_m3_s'])]
for v in ('vent_front','vent_top','vent_slots'): E.append(v+' { '+scalarOpen(T0)+' }')
for n in allfans:
    if n in intake: bc=f'type fixedValue; value uniform {T0};'
    elif n in exhaust: bc='type zeroGradient;'
    else: bc=scalarOpen(T0)
    E.append('fan_'+n+' { '+bc+' }')
(out/'0/T').write_text(field('T','[0 0 0 1 0 0 0]',T0,'\n'.join(E)))
# Passive dust, with --dust only: two fields, as a fraction of the room's dust. dustF is the
# dust that entered through filter mesh or a filtered fan position, counted at the room's
# full concentration; dustU the dust that entered through an unfiltered opening. The card
# and the cooler return the flow-weighted mean of what they draw in, capturing nothing.
# A filter capturing a fraction eta then gives (1-eta)*dustF + dustU, for any eta, from one
# solve.
def mappedDust(patch,source,obj):
    return f'''{patch} {{ type codedFixedValue; name mapped{obj}{patch.title().replace('_','')}; value uniform 0; code #{{ const volScalarField& sf=db().lookupObject<volScalarField>("{obj}"); const label id=patch().boundaryMesh().findPatchID("{source}"); const scalarField& ss=sf.boundaryField()[id]; const scalarField& a=patch().boundaryMesh()[id].magSf(); operator==(gSum(a*ss)/gSum(a)); #}}; }}'''
if dust:
    # The front and top panels are filter mesh, with their fan positions behind it (and the
    # viewer layout's bottom fans take in air as through a filtered floor); the slot covers
    # and the rear fan position have no filter.
    filtered={'vent_front','vent_top','fan_front_low','fan_front_mid','fan_front_high','fan_top_front','fan_top_rear','fan_bottom_front','fan_bottom_rear'}
    unfiltered={'vent_slots','fan_rear'}
    for obj in ('dustF','dustU'):
        E=['walls { type zeroGradient; }','gpu_in { type zeroGradient; }',mappedDust('gpu_out','gpu_in',obj),
           'cpu_in { type zeroGradient; }',mappedDust('cpu_out','cpu_in',obj)]
        for patch in ('vent_front','vent_top','vent_slots')+tuple('fan_'+x for x in allfans):
            inlet = 1 if ((obj == 'dustF' and patch in filtered) or (obj == 'dustU' and patch in unfiltered)) else 0
            E.append(patch+' { '+scalarOpen(inlet)+' }')
        (out/f'0/{obj}').write_text(field(obj,'[0 0 0 0 0 0 0]',0,'\n'.join(E)))
# turbulence fields
opens=['gpu_in','gpu_out','cpu_in','cpu_out','vent_front','vent_top','vent_slots']+['fan_'+x for x in allfans]
def turbField(name,dims,internal,wallbc,openbc):
    es=[f'walls {{ {wallbc} }}']+[f'{p} {{ {openbc} }}' for p in opens]
    (out/f'0/{name}').write_text(field(name,dims,internal,'\n'.join(es)))
turbField('k','[0 2 -2 0 0 0 0]',0.02,'type kqRWallFunction; value uniform 0.02;','type inletOutlet; inletValue uniform 0.02; value uniform 0.02;')
turbField('omega','[0 0 -1 0 0 0 0]',20,'type omegaWallFunction; value uniform 20;','type inletOutlet; inletValue uniform 20; value uniform 20;')
turbField('nut','[0 2 -1 0 0 0 0]',0,'type nutkWallFunction; value uniform 0;','type calculated; value uniform 0;')
# constants
(out/'constant/transportProperties').write_text(hdr('dictionary','transportProperties')+'''transportModel Newtonian;\nnu 1.52e-05;\n''')
(out/'constant/turbulenceProperties').write_text(hdr('dictionary','turbulenceProperties')+'''simulationType RAS;\nRAS { model kOmegaSSTSAS; turbulence on; printCoeffs on; delta cubeRootVol; cubeRootVolCoeffs { deltaCoeff 1; } }\n''')
# numerical controls
(out/'system/fvSchemes').write_text(hdr('dictionary','fvSchemes')+'''ddtSchemes { default backward; }\ngradSchemes { default cellLimited Gauss linear 1; }\ndivSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,T) bounded Gauss limitedLinear 1; '''+('div(phi,dustF) bounded Gauss upwind; div(phi,dustU) bounded Gauss upwind; ' if dust else '')+'''div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }\nlaplacianSchemes { default Gauss linear limited 0.5; }\ninterpolationSchemes { default linear; }\nsnGradSchemes { default limited 0.5; }\nwallDist { method meshWave; }\n''')
# The dust solves converge to an absolute 1e-8, so the dust budget closes.
dustSolvers=('\n "(dustF|dustU)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0; }','\n "(dustF|dustU)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0; }') if dust else ('','')
(out/'system/fvSolution').write_text(hdr('dictionary','fvSolution')+'''solvers\n{\n p { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.05; } pFinal { $p; relTol 0; }\n "(U|T|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }'''+dustSolvers[0]+'''\n "(U|T|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }'''+dustSolvers[1]+'''\n}\nPIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; transonic no; consistent no; }\nrelaxationFactors { equations { ".*" 1; } }\n''')
(out/'system/decomposeParDict').write_text(hdr('dictionary','decomposeParDict')+f'''numberOfSubdomains {C['mpiRanksPerLayout']}; method scotch;\n''')
# Monitoring snippets
# The openings the dust log reports on, in this order (scripts/summarize_dust.py reads them).
dustOpenings=['vent_front','vent_top','vent_slots']+['fan_'+x for x in allfans]
dustHistory=r'''dustHistory { type coded; libs (utilityFunctionObjects); name dustHistory; executeControl timeStep; executeInterval 1; writeControl none;
 codeExecute #{
   const fvMesh& m=mesh();
   const surfaceScalarField& ph=m.lookupObject<surfaceScalarField>("phi");
   const volScalarField& df=m.lookupObject<volScalarField>("dustF");
   const volScalarField& du=m.lookupObject<volScalarField>("dustU");
   const volScalarField& nut=m.lookupObject<volScalarField>("nut");
   const scalar nu=1.52e-5, aD=1e-6, aDt=1.1764705882352942;
   scalar Vf=gSum(m.V()*df.primitiveField());
   scalar Vu=gSum(m.V()*du.primitiveField());
   scalar Vol=gSum(m.V());
   const wordList opens({@OPENS@});
   auto deviceMean=[&](const word& pn,const volScalarField& s)->scalar {
      label id=m.boundaryMesh().findPatchID(pn); const scalarField& q=ph.boundaryField()[id]; const scalarField& x=s.boundaryField()[id];
      return gSum(mag(q)*x)/(gSum(mag(q))+VSMALL);
   };
   auto budgetFlux=[&](const volScalarField& s)->scalar {
      scalar local=0;
      forAll(m.boundary(),id) { if(m.boundary()[id].coupled()) continue; const scalarField& q=ph.boundaryField()[id]; const fvPatchScalarField& x=s.boundaryField()[id]; const fvPatchScalarField& nt=nut.boundaryField()[id]; const scalarField sn(x.snGrad()); const scalarField& A=m.magSf().boundaryField()[id]; local += sum(q*x-(aD*nu+aDt*nt)*sn*A); }
      reduce(local,sumOp<scalar>()); return local;
   };
   scalar gf=deviceMean("gpu_in",df), gu=deviceMean("gpu_in",du), cf=deviceMean("cpu_in",df), cu=deviceMean("cpu_in",du), bf=budgetFlux(df), bu=budgetFlux(du);
   if (Pstream::master()) Info<< "DUSTCSV," << m.time().value() << ',' << Vf << ',' << Vu << ',' << Vol << ',' << gf << ',' << gu << ',' << cf << ',' << cu << ',' << bf << ',' << bu;
   forAll(opens,j) {
      label id=m.boundaryMesh().findPatchID(opens[j]);
      const scalarField& q=ph.boundaryField()[id]; const scalarField& xf=df.boundaryField()[id]; const scalarField& xu=du.boundaryField()[id];
      scalar fi=sum(max(-q*xf,scalar(0))), fo=sum(max(q*xf,scalar(0)));
      scalar ui=sum(max(-q*xu,scalar(0))), uo=sum(max(q*xu,scalar(0)));
      reduce(fi,sumOp<scalar>()); reduce(fo,sumOp<scalar>()); reduce(ui,sumOp<scalar>()); reduce(uo,sumOp<scalar>());
      if(Pstream::master()) Info<< ',' << fi << ',' << fo << ',' << ui << ',' << uo;
   }
   if(Pstream::master()) Info<< nl;
 #}; }'''
common='''type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; writeControl adjustableRunTime; writeInterval 0.02; log false; writeFields false;'''
fos=['''temperatureTransport { type scalarTransport; libs (solverFunctionObjects); field T; nut nut; alphaD 1.40845; alphaDt 1.17647; bounded01 false; nCorr 0; resetOnStartUp false; write false; executeControl timeStep; executeInterval 1; writeControl none; }''']
# The dust, with --dust: bounded first-order upwind (above), Brownian diffusion negligible
# (alphaD 1e-6 of nu) and turbulent diffusion nut/0.85 (turbulent Schmidt number 0.85).
if dust:
    for obj in ('dustF','dustU'): fos.append(f'''{obj}Transport {{ type scalarTransport; libs (solverFunctionObjects); field {obj}; alphaD 1e-6; alphaDt 1.1764705882352942; bounded01 false; nCorr 0; resetOnStartUp false; write false; executeControl timeStep; executeInterval 1; writeControl none; }}''')
scalars='T dustF dustU' if dust else 'T'
for name,patch in [('gpuIntake','gpu_in'),('cpuIntake','cpu_in')]: fos.append(f'''{name} {{ {common} name {patch}; operation weightedAverage; weightField phi; fields ({scalars}); }}''')
for patch in ('vent_front','vent_top','vent_slots'):
    fos.append(f'''{patch}_net {{ {common} name {patch}; operation sum; fields (phi); }}''')
    fos.append(f'''{patch}_absolute {{ {common} name {patch}; operation sumMag; fields (phi); }}''')
# The case's mean dust every 0.02 s, with --dust.
if dust:
    fos.append('''dustVolumeMean { type volFieldValue; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval 0.02; log false; writeFields false; operation volAverage; fields (dustF dustU); }''')
fos.append('''casePressure { type volFieldValue; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval 0.02; log false; writeFields false; operation volAverage; fields (p); }''')
if dust:
    # Every time step, a DUSTCSV line in the log: the dust each field holds, the card's and
    # the cooler's intake, the net flux out through every boundary (advection and diffusion,
    # for the budget), and the dust in and out through each opening.
    # scripts/summarize_dust.py reads them.
    fos.append(dustHistory.replace('@OPENS@',','.join(f'"{x}"' for x in dustOpenings)))
fos.append('''planes { type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.02; surfaceFormat ensight; formatOptions { ensight { format binary; collateTimes true; } } fields (U T p'''+(' dustF dustU' if dust else '')+'''); interpolationScheme cellPoint; surfaces { cardMid { type cuttingPlane; point (0 0 0.082); normal (0 0 1); interpolate true; } belowCard { type cuttingPlane; point (0 0.145 0); normal (0 1 0); interpolate true; } } }''')
(out/'system/controlDict').write_text(hdr('dictionary','controlDict')+f'''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {C['endTime_s']}; deltaT 0.0002; writeControl runTime; writeInterval {C['endTime_s']}; purgeWrite 1; writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 7; runTimeModifiable true; adjustTimeStep yes; maxCo {C['maxCo']}; maxDeltaT {C['maxDeltaT_s']}; functions {{ {' '.join(fos)} }}\n''')
print(out)
