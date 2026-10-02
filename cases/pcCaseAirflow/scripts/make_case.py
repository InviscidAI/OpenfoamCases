#!/usr/bin/env python3
"""Generate one layout case from config/model.json and the common generated mesh."""
import json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'config/model.json').read_text())
layout=sys.argv[1] if len(sys.argv)>1 else 'positive'
if layout not in C['layouts']: raise SystemExit('layout must be positive, negative, or even')
out=ROOT/'runs'/layout
if out.exists(): shutil.rmtree(out)
(out/'constant').mkdir(parents=True); (out/'system').mkdir(); (out/'0').mkdir()
shutil.copytree(ROOT/'mesh/constant/polyMesh',out/'constant/polyMesh')
# snappy leaves an empty frozenPoints zone; omit it (and avoid simplified-mesh dry-run bug).
for z in ('pointZones','faceZones','cellZones'):
    (out/'constant/polyMesh'/z).unlink(missing_ok=True)

hdr=lambda cls,obj: f'''FoamFile\n{{\n version 2.0; format ascii; class {cls}; object {obj};\n}}\n'''
# Merge black-box openings so mapped heat BC sees all source/sink faces together.
cp=hdr('dictionary','createPatchDict')+'''pointSync false;\npatches\n(\n { name gpu_in; patchInfo { type patch; } constructFrom patches; patches (gpu_in_1 gpu_in_2 gpu_in_3); }\n { name gpu_out; patchInfo { type patch; } constructFrom patches; patches (gpu_out_board_side gpu_out_flow_through gpu_out_front_end gpu_out_glass_side); }\n);\n'''
(out/'system/createPatchDict').write_text(cp)

allfans=['front_low','front_mid','front_high','rear','top_front','top_rear']
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
(out/'system/fvSchemes').write_text(hdr('dictionary','fvSchemes')+'''ddtSchemes { default backward; }\ngradSchemes { default cellLimited Gauss linear 1; }\ndivSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,T) bounded Gauss limitedLinear 1; div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }\nlaplacianSchemes { default Gauss linear limited 0.5; }\ninterpolationSchemes { default linear; }\nsnGradSchemes { default limited 0.5; }\nwallDist { method meshWave; }\n''')
(out/'system/fvSolution').write_text(hdr('dictionary','fvSolution')+'''solvers\n{\n p { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.05; } pFinal { $p; relTol 0; }\n "(U|T|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }\n "(U|T|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }\n}\nPIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; transonic no; consistent no; }\nrelaxationFactors { equations { ".*" 1; } }\n''')
(out/'system/decomposeParDict').write_text(hdr('dictionary','decomposeParDict')+f'''numberOfSubdomains {C['mpiRanksPerLayout']}; method scotch;\n''')
# Monitoring snippets
common='''type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; writeControl adjustableRunTime; writeInterval 0.02; log false; writeFields false;'''
fos=['''temperatureTransport { type scalarTransport; libs (solverFunctionObjects); field T; nut nut; alphaD 1.40845; alphaDt 1.17647; bounded01 false; nCorr 0; resetOnStartUp false; write false; executeControl timeStep; executeInterval 1; writeControl none; }''']
for name,patch in [('gpuIntake','gpu_in'),('cpuIntake','cpu_in')]: fos.append(f'''{name} {{ {common} name {patch}; operation weightedAverage; weightField phi; fields (T); }}''')
for patch in ('vent_front','vent_top','vent_slots'):
    fos.append(f'''{patch}_net {{ {common} name {patch}; operation sum; fields (phi); }}''')
    fos.append(f'''{patch}_absolute {{ {common} name {patch}; operation sumMag; fields (phi); }}''')
fos.append('''casePressure { type volFieldValue; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval 0.02; log false; writeFields false; operation volAverage; fields (p); }''')
fos.append('''planes { type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.02; surfaceFormat ensight; formatOptions { ensight { format binary; collateTimes true; } } fields (U T p); interpolationScheme cellPoint; surfaces { cardMid { type cuttingPlane; point (0 0 0.082); normal (0 0 1); interpolate true; } belowCard { type cuttingPlane; point (0 0.145 0); normal (0 1 0); interpolate true; } } }''')
(out/'system/controlDict').write_text(hdr('dictionary','controlDict')+f'''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {C['endTime_s']}; deltaT 0.0002; writeControl runTime; writeInterval {C['endTime_s']}; purgeWrite 1; writeFormat binary; writePrecision 7; writeCompression on; timeFormat general; timePrecision 7; runTimeModifiable true; adjustTimeStep yes; maxCo {C['maxCo']}; maxDeltaT {C['maxDeltaT_s']}; functions {{ {' '.join(fos)} }}\n''')
print(out)
