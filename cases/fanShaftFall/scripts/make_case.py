#!/usr/bin/env python3
"""Write one run of the shaft: the man fixed, a uniform updraft from below.

    python3 scripts/make_case.py <run> <speed m/s> <endTime s> [curve|clip]

<run> is relative to runs/ (curve/U8, fan, float). Writes 0/, constant/, system/ and
config.json, and links constant/polyMesh to runs/mesh/constant/polyMesh. The inlet is a
constant (0 0 speed); scripts/make_clips.py replaces it with the fall's table for the clip
runs and adds the planes. Steady inflow at 8, 20, 40 and 55 m/s gives the drag curve, run
for 8 m of air past him (endTime 8/U).
"""
import sys, os, shutil, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'runs'
name=sys.argv[1]; speed=float(sys.argv[2]); end=float(sys.argv[3]); mode=sys.argv[4] if len(sys.argv)>4 else 'curve'
c=root/name
if c.exists(): shutil.rmtree(c)
for d in ['0','constant','system']: (c/d).mkdir(parents=True,exist_ok=True)
os.symlink(os.path.relpath(root/'mesh/constant/polyMesh',c/'constant'),c/'constant/polyMesh')
rho=1.204; nu=1.516e-5; I=.10; L=.09
k=1.5*(I*speed)**2; om=math.sqrt(k)/(0.09**0.25*L)
header=lambda cls,obj: f'FoamFile {{ format ascii; class {cls}; object {obj}; }}\n'
# input velocity: constant unless a prepared table string is supplied later
uval=f'(0 0 {speed:.10g})'
(c/'0/U').write_text(header('volVectorField','U')+f'''dimensions [0 1 -1 0 0 0 0]; internalField uniform {uval};
boundaryField {{
 inlet {{ type fixedValue; value uniform {uval}; }}
 outlet {{ type pressureInletOutletVelocity; value uniform {uval}; }}
 walls {{ type slip; }}
 faller {{ type fixedValue; value uniform (0 0 0); }}
}}
''')
(c/'0/p').write_text(header('volScalarField','p')+'''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
boundaryField { inlet { type zeroGradient; } outlet { type fixedValue; value uniform 0; } walls { type zeroGradient; } faller { type zeroGradient; } }
''')
(c/'0/k').write_text(header('volScalarField','k')+f'''dimensions [0 2 -2 0 0 0 0]; internalField uniform {k};
boundaryField {{ inlet {{ type fixedValue; value uniform {k}; }} outlet {{ type inletOutlet; inletValue uniform {k}; value uniform {k}; }} walls {{ type zeroGradient; }} faller {{ type kqRWallFunction; value uniform {k}; }} }}
''')
(c/'0/omega').write_text(header('volScalarField','omega')+f'''dimensions [0 0 -1 0 0 0 0]; internalField uniform {om};
boundaryField {{ inlet {{ type fixedValue; value uniform {om}; }} outlet {{ type inletOutlet; inletValue uniform {om}; value uniform {om}; }} walls {{ type zeroGradient; }} faller {{ type omegaWallFunction; value uniform {om}; }} }}
''')
(c/'0/nut').write_text(header('volScalarField','nut')+'''dimensions [0 2 -1 0 0 0 0]; internalField uniform 0;
boundaryField { inlet { type calculated; value uniform 0; } outlet { type calculated; value uniform 0; } walls { type calculated; value uniform 0; } faller { type nutkWallFunction; value uniform 0; } }
''')
(c/'constant/transportProperties').write_text(header('dictionary','transportProperties')+f'''transportModel Newtonian; nu [0 2 -1 0 0 0 0] {nu};
''')
(c/'constant/turbulenceProperties').write_text(header('dictionary','turbulenceProperties')+'''simulationType RAS;
RAS { RASModel kOmegaSSTSAS; turbulence on; printCoeffs on; delta cubeRootVol; cubeRootVolCoeffs { deltaCoeff 1; } }
''')
(c/'system/fvSchemes').write_text(header('dictionary','fvSchemes')+'''ddtSchemes { default backward; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss limitedLinear 1; div(phi,omega) bounded Gauss limitedLinear 1; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''')
(c/'system/fvSolution').write_text(header('dictionary','fvSolution')+'''solvers {
 p { solver GAMG; smoother DICGaussSeidel; tolerance 1e-6; relTol 0.05; cacheAgglomeration true; agglomerator faceAreaPair; }
 pFinal { $p; relTol 0; }
 U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
 UFinal { $U; relTol 0; }
 k { $U; } kFinal { $UFinal; } omega { $U; } omegaFinal { $UFinal; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; }
relaxationFactors { equations { U 0.9; k 0.8; omega 0.8; } }
''')
(c/'system/decomposeParDict').write_text(header('dictionary','decomposeParDict')+'''numberOfSubdomains 4; method scotch;
''')
forces='''forces
{
 type forces; libs (forces); patches (faller); rho rhoInf; rhoInf 1.204; CofR (0 0 0);
 writeControl timeStep; writeInterval 1; log yes;
}
forceCoeffs
{
 type forceCoeffs; libs (forces); patches (faller); rho rhoInf; rhoInf 1.204;
 magUInf %g; lRef 1.75; Aref 0.5014062289; CofR (0 0 0); liftDir (1 0 0); dragDir (0 0 1); pitchAxis (0 1 0);
 writeControl timeStep; writeInterval 1; log yes;
}
'''%speed
control=header('dictionary','controlDict')+f'''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end:.12g}; deltaT {min(0.001,0.015/speed):.8g};
adjustTimeStep yes; maxCo 3.0; maxDeltaT {min(.002,0.02/speed):.8g};
writeControl adjustableRunTime; writeInterval {end:.12g}; purgeWrite 1; writeFormat binary; writeCompression on; timeFormat general; timePrecision 10;
runTimeModifiable true;
functions {{ {forces} }}
'''
(c/'system/controlDict').write_text(control)
(c/'config.json').write_text(__import__('json').dumps(dict(speed_m_s=speed,end_s=end,air_density=1.204,nu=nu,inlet_turbulence_intensity=I,inlet_length_scale_m=L,model='kOmegaSSTSAS',walls='slip',averaging_window_s=[end/2,end]),indent=2)+'\n')
print(c)
