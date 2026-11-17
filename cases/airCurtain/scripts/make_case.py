#!/usr/bin/env python3
"""Write one run of the doorway: the air curtain off or on.

    python3 scripts/make_case.py off|on runs/<run> [--nprocs 4] [--mesh runs/mesh] [--end 60]

Copies the shared mesh (scripts/make_mesh.py), template/constant/ (g, thermophysicalProperties,
turbulenceProperties, fvOptions) and template/system/ (fvSchemes, fvSolution, initialSurfaces and
the coded monitor), and writes:

  0/        U, T, outdoor, p, p_rgh, k, omega, nut, alphat and phi. From rest: the street at
            0 C (273.15 K) and outdoor = 1 for x < 0.1 m (the street and the doorway's outer half),
            the shop at 20 C (293.15 K) and outdoor = 0. p hydrostatic in each, equal at y = 1.1 m
            across the door line, p_rgh = p + rho g y, on the cells and on every boundary face.
            The face flux phi is zero.
            street and sky: open, pressureInletOutletVelocity and prghTotalPressure with the
            outdoor hydrostatic p0 on each face; air coming in at 0 C, outdoor = 1, k 1e-4,
            omega 0.1826. Every wall no-slip and adiabatic with wall functions.
            on: the slot blows a fixed (-2.0521, -5.6382) m/s, 6 m/s aimed 20 degrees out to the
            street, 0.33829 m3/s per metre, with k from 5% intensity and omega from a 6 mm mixing
            length; the intake draws the same 0.33829 m3/s (flowRateOutletVelocity); the slot's T
            and outdoor are the intake's mean (outletMappedUniformInlet), so the jet is unheated
            room air recirculated. nut and alphat calculated on both.
            off: the slot and the intake are walls like the rest of the unit.
  system/controlDict  0-60 s from rest, a first step of 0.1 ms, maxCo 1, maxDeltaT 0.02 s, the
            fields every 10 s; the outdoor tracer (scalarTransport, alphaD 1/0.71, alphaDt 1, the
            bulk turbulent Prandtl number of SST in v2512), the field extremes, the planes (T, U
            and outdoor on z = 0.5, as point and as cell values, every 0.125 s) and the monitor.
  system/decomposeParDict  scotch on nProcs ranks.

These are the solved runs' files byte for byte, but for the monitor's name (`monitor`, which the
solved runs called by a number of ours) and an abort function object the solved runs had and never
used, which is left out.
"""
import argparse
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
R = 8314.46261815324 / 28.96          # the perfect gas's R from molWeight 28.96
T_OUT, T_IN = 273.15, 293.15


def header(obj, cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'


def lst(a):
    return 'nonuniform List<scalar>\n' + str(len(a)) + '\n(\n' + '\n'.join(str(float(v)) for v in a) + '\n)'


def hydrostatic(px, py):
    """p of the street (x < 0.1) and of the shop at rest, equal at y = 1.1 m."""
    out = 1e5 * np.exp(-9.81 * py / (287.1 * T_OUT))
    inside = 1e5 * np.exp(-9.81 * 1.1 / (287.1 * T_OUT)) * np.exp(-9.81 * (py - 1.1) / (287.1 * T_IN))
    return np.where(px < .1, out, inside)


WALL = {'U': 'type noSlip;', 'T': 'type zeroGradient;', 'outdoor': 'type zeroGradient;',
        'p': 'type calculated; value uniform 1e5;', 'p_rgh': 'type fixedFluxPressure; value uniform 1e5;',
        'k': 'type kLowReWallFunction; value uniform 1e-4;', 'omega': 'type omegaWallFunction; value uniform 1;',
        'nut': 'type nutkWallFunction; value uniform 0;',
        'alphat': 'type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;'}
OPEN = {'U': 'type pressureInletOutletVelocity; value uniform (0 0 0);',
        'T': 'type inletOutlet; inletValue uniform 273.15; value uniform 273.15;',
        'outdoor': 'type inletOutlet; inletValue uniform 1; value uniform 1;',
        'k': 'type inletOutlet; inletValue uniform 1e-4; value uniform 1e-4;',
        'omega': 'type inletOutlet; inletValue uniform 0.1825741858; value uniform 0.1825741858;',
        'nut': 'type calculated; value uniform 0;', 'alphat': 'type calculated; value uniform 0;',
        'p': 'type calculated; value uniform 1e5;'}
MAPPED = 'type outletMappedUniformInlet; phi phi; outlets { curtainIntake {offset 0; fraction 1; timeDelay 0;} } value uniform '
SLOT = {'U': 'type fixedValue; value uniform (-2.0521 -5.6382 0);', 'T': MAPPED + '293.15;', 'outdoor': MAPPED + '0;',
        'k': 'type turbulentIntensityKineticEnergyInlet; intensity 0.05; value uniform 0.135;',
        'omega': 'type turbulentMixingLengthFrequencyInlet; mixingLength 0.006; value uniform 111.8;',
        'nut': 'type calculated; value uniform 0;', 'alphat': 'type calculated; value uniform 0;',
        'p': 'type calculated; value uniform 1e5;', 'p_rgh': 'type fixedFluxPressure; value uniform 1e5;'}
INTAKE = {'U': 'type flowRateOutletVelocity; volumetricFlowRate 0.33829; value uniform (-1.610904762 0 0);',
          'T': 'type zeroGradient;', 'outdoor': 'type zeroGradient;', 'k': 'type zeroGradient;',
          'omega': 'type zeroGradient;', 'nut': 'type calculated; value uniform 0;',
          'alphat': 'type calculated; value uniform 0;', 'p': 'type calculated; value uniform 1e5;',
          'p_rgh': 'type fixedFluxPressure; value uniform 1e5;'}
DIMS = {'U': '0 1 -1 0 0 0 0', 'T': '0 0 0 1 0 0 0', 'outdoor': '0 0 0 0 0 0 0', 'p': '1 -1 -2 0 0 0 0',
        'p_rgh': '1 -1 -2 0 0 0 0', 'k': '0 2 -2 0 0 0 0', 'omega': '0 0 -1 0 0 0 0', 'nut': '0 2 -1 0 0 0 0',
        'alphat': '1 -1 -1 0 0 0 0'}
PATCHES = ['curtainSlot', 'curtainIntake', 'curtainBody', 'street', 'sky', 'pavement', 'facade',
           'doorHead', 'wallInside', 'floor', 'ceiling', 'backWall', 'frontAndBack']

PLANES = """planes {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval 0.125; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor); surfaces {
 section {type cuttingPlane; point (0 0 .5); normal (0 0 1); interpolate true;}
 sectionCells {type cuttingPlane; point (0 0 .5); normal (0 0 1); interpolate false;}
 } }
"""
FUNCTIONS = ''' tracer {type scalarTransport; libs (solverFunctionObjects); field outdoor; phi phi; rho rho; alphaD 1.40845; alphaDt 1.0; executeControl timeStep; executeInterval 1; writeControl writeTime; }
 extrema {type fieldMinMax; libs (fieldFunctionObjects); fields (T outdoor U); mode component; location true; executeControl timeStep; executeInterval 1; writeControl timeStep; writeInterval 1; log false;}
 '''


def make(run, path, nprocs, mesh, end):
    on = run == 'on'
    c, mesh = Path(path), Path(mesh)
    c.mkdir(parents=True, exist_ok=True)
    shutil.copytree(mesh / 'constant/polyMesh', c / 'constant/polyMesh', dirs_exist_ok=True)
    for d in ['0', 'system']:
        (c / d).mkdir(exist_ok=True)
    g = np.load(mesh / 'cells.npz')
    cc = g['cc']

    t = np.where(cc[:, 0] < .1, T_OUT, T_IN)
    y = cc[:, 1]
    p = hydrostatic(cc[:, 0], y)
    rho = p / (R * t)
    initial = {'T': lst(t), 'outdoor': lst((cc[:, 0] < .1).astype(float)), 'p': lst(p), 'p_rgh': lst(p + rho * 9.81 * y),
               'U': 'uniform (0 0 0)', 'k': 'uniform 1e-4', 'omega': 'uniform 1', 'nut': 'uniform 0', 'alphat': 'uniform 0'}
    for fld in DIMS:
        text = (header(fld, 'volVectorField' if fld == 'U' else 'volScalarField') + f'dimensions [{DIMS[fld]}];\n'
                'internalField ' + initial[fld] + ';\nboundaryField\n{\n')
        for pn in PATCHES:
            bc = WALL[fld]
            if pn == 'frontAndBack':
                bc = 'type empty;'
            elif pn in ['street', 'sky']:
                if fld == 'p_rgh':
                    fy = g['face_' + pn][:, 1]
                    bc = ('type prghTotalPressure; p0 ' + lst(1e5 * np.exp(-9.81 * fy / (287.1 * T_OUT)))
                          + '; gamma 1; value uniform 1e5;')
                else:
                    bc = OPEN[fld]
            elif on and pn == 'curtainSlot':
                bc = SLOT[fld]
            elif on and pn == 'curtainIntake':
                bc = INTAKE[fld]
            if pn != 'frontAndBack' and fld in ['p', 'p_rgh']:
                fc = g['face_' + pn]
                fy, ft = fc[:, 1], np.where(fc[:, 0] < .1, T_OUT, T_IN)
                pp = hydrostatic(fc[:, 0], fy)
                val = pp if fld == 'p' else pp + pp / (R * ft) * 9.81 * fy
                bc = bc.replace('value uniform 1e5;', 'value ' + lst(val) + ';')
            text += pn + '\n{' + bc + '}\n'
        (c / '0' / fld).write_text(text + '}\n')
    # At rest: the inlet and outlet velocities impose the full flow at the first pressure correction.
    phi = header('phi', 'surfaceScalarField') + 'dimensions [1 0 -1 0 0 0 0]; internalField uniform 0; boundaryField {\n'
    for pn in PATCHES:
        phi += pn + ' {type ' + ('empty;' if pn == 'frontAndBack' else 'calculated; value uniform 0;') + '}\n'
    (c / '0/phi').write_text(phi + '}\n')

    shutil.copytree(CASE / 'template/constant', c / 'constant', dirs_exist_ok=True)
    for f in ['fvSchemes', 'fvSolution', 'initialSurfaces', 'monitor']:
        shutil.copy(CASE / 'template/system' / f, c / 'system' / f)
    (c / 'system/decomposeParDict').write_text(header('decomposeParDict') + f'numberOfSubdomains {nprocs}; method scotch;')
    (c / 'system/controlDict').write_text(
        header('controlDict') + f'application buoyantPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; '
        f'endTime {end}; deltaT .0001; adjustTimeStep yes; maxCo 1; maxDeltaT .02; writeControl adjustableRunTime; '
        'writeInterval 10; purgeWrite 0; writeFormat binary; writePrecision 12; writeCompression on; timeFormat general; '
        'timePrecision 12; runTimeModifiable false; functions {\n' + FUNCTIONS + PLANES + '\n#include "monitor"\n\n}\n')
    (c / 'case.foam').touch()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run', choices=['off', 'on'])
    ap.add_argument('path')
    ap.add_argument('--nprocs', type=int, default=4)
    ap.add_argument('--mesh', default='runs/mesh')
    ap.add_argument('--end', default='60')
    a = ap.parse_args()
    make(a.run, a.path, a.nprocs, a.mesh, a.end)
