"""Write one run of the ceiling vent against floor register case.

    python3 scripts/make_case.py floor|ceiling <runDir> <meshDir> [--nprocs N]

copies <meshDir>'s polyMesh (scripts/make_mesh.py, then blockMesh) into <runDir> and writes
the run's fields and dictionaries:

- constant/polyMesh/boundary: the slot this run does not use becomes a wall (ceilingSlot in
  floor, floorSlot in ceiling); its cells and faces are the same in both runs.
- constant/g, turbulenceProperties, thermophysicalProperties: radiatorUnderWindow's
  template with its settings written in (Tamb 293.15 K): air a perfect gas, 28.96 kg/kmol,
  cp 1005 J/kg K, mu 1.82e-5 Pa s, Pr 0.71, k-omega SST.
- constant/fvOptions: buoyancyTurbSource only; no radiator and no heat source.
- system/fvSchemes: radiatorUnderWindow's. system/fvSolution: radiatorUnderWindow's with
  the two production settings, nOuterCorrectors 1 (from 2) and the p_rgh tolerance 1e-7
  (from 1e-8); README "How the case got here".
- 0/: the air at rest at 20 C (293.15 K). The supply slot gives 0.012903 m3/s per metre at
  117 F (320.37 K), ramped linearly from rest over the first 2 s: floor straight up at
  0.012903/0.0042 m/s, ceiling at 45 degrees down towards the window at 0.012903/0.0072 m/s
  over its 7.2 mm. The undercut opens onto the hall's still 20 C air at its hydrostatic
  pressure (prghTotalPressure; bedroomTools -prepare sets its p0). The glass loses heat to
  0 F (255.37 K) outside through h = 4.403 W/m2K; the rest of the window wall is adiabatic;
  the floor, the ceiling, the inner wall and the unused slot are bedroomLayer walls, a 1-D
  layer of 3/4 in wood (floor) or 1/2 in gypsum (the rest) with its heat capacity and an
  adiabatic back (src/bedroomLayer/wallLayer.C).
- system/controlDict: Courant 1, 0-300 s, fields every 30 s (the last two kept), the
  section every 0.625 s, bedroomMonitor's budget at every step and its zones every 0.625 s.
- system/plane0Dict: the section alone, for the t = 0 plane.
- system/setFieldsDict, topoSetDict, decomposeParDict.

This is the setup agent's own generator (its setup_cases.py) for one run, with the
production fvSolution written in rather than edited afterwards.
"""
import argparse
import re
import shutil
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
TEMPLATE = CASE.parent / "radiatorUnderWindow" / "template"

FLOW = .012903  # m3/s per metre: 100 CFM spread over a 12 ft (3.66 m) wide room
SLOT = {'floor': .0042, 'ceiling': .0072}  # m, the slots' widths in the mesh
patches = ['floor', 'ceiling', 'innerWall', 'outerWall', 'glass', 'floorSlot', 'ceilingSlot', 'undercut', 'frontAndBack']


def head(cls, obj):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'


def main(kind, run, meshdir, nprocs):
    p = Path(run)
    vels = {'floor': (0, FLOW / SLOT['floor'], 0), 'ceiling': (-FLOW / SLOT['ceiling'], -FLOW / SLOT['ceiling'], 0)}
    for sub in ['0', 'constant', 'system']:
        (p / sub).mkdir(parents=True, exist_ok=True)
    shutil.copytree(Path(meshdir) / 'constant/polyMesh', p / 'constant/polyMesh', dirs_exist_ok=True)
    # The slot not in use is a wall; its geometry is the same in the two runs.
    b = p / 'constant/polyMesh/boundary'
    inactive = 'ceilingSlot' if kind == 'floor' else 'floorSlot'
    b.write_text(re.sub(r'(' + inactive + r'\s*\{\s*type\s+)patch', r'\1wall', b.read_text()))
    for n in ['g', 'turbulenceProperties', 'thermophysicalProperties']:
        text = (TEMPLATE / 'constant' / n).read_text().replace('#include "../../config/caseSettings"', '').replace('$Tamb', '293.15')
        (p / 'constant' / n).write_text(text)
    # No radiator and no heat source; only the buoyancy production of k-omega SST.
    (p / 'constant/fvOptions').write_text(head('dictionary', 'fvOptions') + 'buoyancyTurb {type buoyancyTurbSource; selectionMode all;}\n')
    shutil.copy(TEMPLATE / 'system/fvSchemes', p / 'system/fvSchemes')
    fvSolution = (TEMPLATE / 'system/fvSolution').read_text()
    fvSolution = re.sub(r'(p_rgh\n    \{[^}]*?tolerance\s+)1e-8;', r'\g<1>1e-7;', fvSolution, count=1)
    fvSolution = re.sub(r'(nOuterCorrectors\s+)2;', r'\g<1>1;', fvSolution, count=1)
    (p / 'system/fvSolution').write_text(fvSolution)
    (p / 'system/decomposeParDict').write_text(head('dictionary', 'decomposeParDict') + f'numberOfSubdomains {nprocs}; method scotch;\n')
    (p / 'system/topoSetDict').write_text(head('dictionary', 'topoSetDict') + 'actions ();\n')
    (p / 'system/setFieldsDict').write_text(head('dictionary', 'setFieldsDict') + 'defaultFieldValues (volScalarFieldValue T 293.15 volVectorFieldValue U (0 0 0)); regions ();\n')

    active = kind + 'Slot'
    dimensions = {'T': '0 0 0 1 0 0 0', 'U': '0 1 -1 0 0 0 0', 'p': '1 -1 -2 0 0 0 0', 'p_rgh': '1 -1 -2 0 0 0 0', 'k': '0 2 -2 0 0 0 0', 'omega': '0 0 -1 0 0 0 0', 'alphat': '1 -1 -1 0 0 0 0', 'nut': '0 2 -1 0 0 0 0'}
    vals = {'T': '293.15', 'U': '(0 0 0)', 'p': '100000', 'p_rgh': '100000', 'k': '1e-4', 'omega': '1', 'alphat': '0', 'nut': '0'}
    wallBC = {'U': 'type noSlip;', 'p': 'type calculated; value uniform 100000;', 'p_rgh': 'type fixedFluxPressure; value uniform 100000;', 'k': 'type kLowReWallFunction; value uniform 1e-4;', 'omega': 'type omegaWallFunction; value uniform 1;', 'alphat': 'type compressible::alphatJayatillekeWallFunction; Prt .85; value uniform 0;', 'nut': 'type nutkWallFunction; value uniform 0;'}
    for name, dims in dimensions.items():
        txt = head('volVectorField' if name == 'U' else 'volScalarField', name) + f'dimensions [{dims}];\ninternalField uniform {vals[name]};\nboundaryField\n{{\n'
        for patch in patches:
            if patch == 'frontAndBack':
                bc = 'type empty;'
            elif patch == active:
                if name == 'T':
                    bc = 'type fixedValue; value uniform 320.37;'
                elif name == 'U':
                    vec = '(' + ' '.join(f'{v:.14g}' for v in vels[kind]) + ')'
                    bc = f'type uniformFixedValue; uniformValue table ((0 (0 0 0)) (2 {vec}) (300 {vec})); value uniform (0 0 0);'
                elif name == 'k':
                    bc = 'type turbulentIntensityKineticEnergyInlet; intensity .10; value uniform 1e-4;'
                elif name == 'omega':
                    bc = 'type turbulentMixingLengthFrequencyInlet; mixingLength .0005; value uniform 1;'
                elif name in ['alphat', 'nut']:
                    bc = 'type calculated; value uniform 0;'
                else:
                    bc = wallBC[name]
            elif patch == 'undercut':
                if name == 'T':
                    bc = 'type inletOutlet; inletValue uniform 293.15; value uniform 293.15;'
                elif name == 'U':
                    bc = 'type pressureInletOutletVelocity; value uniform (0 0 0);'
                elif name == 'p_rgh':
                    bc = 'type prghTotalPressure; p0 uniform 100000; value uniform 100000;'
                elif name in ['k', 'omega']:
                    bc = f'type inletOutlet; inletValue uniform {vals[name]}; value uniform {vals[name]};'
                elif name in ['alphat', 'nut']:
                    bc = 'type calculated; value uniform 0;'
                else:
                    bc = wallBC[name]
            elif name == 'T':
                if patch == 'glass':
                    bc = 'type externalWallHeatFluxTemperature; mode coefficient; h uniform 4.403; Ta uniform 255.37; kappaMethod fluidThermo; value uniform 293.15;'
                elif patch == 'outerWall':
                    bc = 'type zeroGradient;'
                else:
                    bc = 'type bedroomLayer; kappaMethod fluidThermo; value uniform 293.15;'
            else:
                bc = wallBC[name]
            txt += f'{patch}\n{{\n{bc}\n}}\n'
        (p / '0' / name).write_text(txt + '}\n')

    functions = '''
functions
{
 energyCheck {type volFieldValue; libs (fieldFunctionObjects); fields (p rho); operation volIntegrate; regionType all; writeFields false; writeControl timeStep; writeInterval 1; log false;}
 minMaxT {type fieldMinMax; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval .625; fields (T); log false;}
 probes {type probes; libs (sampling); writeControl adjustableRunTime; writeInterval .625; fields (T U); probeLocations ((.5 .1 .5) (1 .1 .5) (2 .1 .5) (.5 1.1 .5) (1 1.1 .5) (2 1.1 .5));}
 roomMeanT {type volFieldValue; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval .625; writeFields false; regionType all; operation volAverage; fields (T); log false;}
 glassTs {type surfaceFieldValue; libs (fieldFunctionObjects); writeControl adjustableRunTime; writeInterval .625; writeFields false; regionType patch; name glass; operation areaAverage; fields (T); log false;}
 wallHeatFlux {type wallHeatFlux; libs (fieldFunctionObjects); executeControl timeStep; executeInterval 1; writeControl writeTime; writeInterval 1; writeFields false; patches (glass floor ceiling innerWall outerWall); log false;}
 monitor {type bedroomMonitor; libs ("libbedroomLayer.so"); supply ACTIVE; executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval .625;}
 clip {type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval .625; surfaceFormat vtk; formatOptions {vtk {format binary;}} interpolate false; fields (T U); surfaces {clip {type cuttingPlane; point (2 1.2 .5); normal (0 0 1); interpolate false;}}}
}
'''.replace('ACTIVE', active)
    ctl = head('dictionary', 'controlDict') + '''application buoyantPimpleFoam;
libs ("libbedroomLayer.so");
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 300;
deltaT .0005;
adjustTimeStep yes;
maxCo 1;
maxDeltaT .25;
writeControl adjustableRunTime;
writeInterval 30;
purgeWrite 2;
writeFormat binary;
writePrecision 10;
writeCompression off;
timeFormat general;
timePrecision 10;
runTimeModifiable false;
''' + functions
    (p / 'system/controlDict').write_text(ctl)
    # The section alone, for the plane at t = 0 (postProcess, before the solve).
    (p / 'system/plane0Dict').write_text(head('dictionary', 'plane0Dict') + ctl[ctl.index('application'):ctl.index('functions')] + 'functions\n{\n' + functions[functions.index(' clip {'):functions.rfind('}')] + '\n}\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('kind', choices=['floor', 'ceiling'])
    ap.add_argument('run')
    ap.add_argument('mesh')
    ap.add_argument('--nprocs', type=int, default=8)
    a = ap.parse_args()
    main(a.kind, a.run, a.mesh, a.nprocs)
