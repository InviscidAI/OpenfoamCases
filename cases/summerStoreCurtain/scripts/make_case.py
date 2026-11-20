#!/usr/bin/env python3
"""Write one run of the store's doorway: the air curtain off or on.

    python3 scripts/make_case.py off|on runs/<run> [--nprocs 4] [--mesh runs/mesh] [--end 60]

Copies the shared mesh (scripts/make_mesh.py), template/constant/ (g, thermophysicalProperties,
turbulenceProperties, fvOptions) and template/system/ (fvSchemes, fvSolution, initialSurfaces and
the coded monitor), and writes:

  0/        U, T, outdoor, p, p_rgh, k, omega, nut, alphat and phi. From rest: the street at
            35 C (308.15 K, 95 F) and outdoor = 1 for x < 0.075 m (the street and the doorway's outer
            half), the store at 21.111 C (294.261 K, 70 F) and outdoor = 0. p hydrostatic in each,
            equal at y = 1.065 m (the door's mid-height) across the door line, p_rgh = p + rho g y,
            on the cells and on every boundary face. The face flux phi is zero.
            street and sky: open, pressureInletOutletVelocity and prghTotalPressure with the
            outdoor hydrostatic p0 on each face; air coming in at 35 C, outdoor = 1, k 1e-4,
            omega 0.1826 (a 0.1 m mixing length). Every wall no-slip and adiabatic with wall
            functions.
            on: the slot blows a fixed (-2.0521, -5.6382) m/s, 6 m/s aimed 20 degrees out to the
            street, 0.33829 m3/s per metre, with k from 5% intensity and omega from a 6 mm mixing
            length; the intake draws the same 0.33829 m3/s (flowRateOutletVelocity); the slot's T
            and outdoor are the intake's mean (outletMappedUniformInlet), so the jet is the store's
            own air, recirculated and unheated. nut and alphat calculated on both.
            off: the slot and the intake are walls like the rest of the unit.
  system/controlDict  0 to --end s from the latest time (0 at first), a first step of 0.1 ms
            (deltaT 8.33e-5 s, which OpenFOAM's adjustment makes 1e-4 s), maxCo 1, maxDeltaT 0.02 s,
            the fields every 10 s; the outdoor tracer (scalarTransport, alphaD 1/0.71, alphaDt 1,
            the bulk turbulent Prandtl number of SST in v2512), the field extremes, the planes (T, U
            and outdoor on z = 0.5, as point and as cell values, every 0.125 s) and the monitor.
  system/decomposeParDict  scotch on nProcs ranks.

These are the solved runs' files, but for the monitor's name (`monitor`, which the solved runs called
monitor81) and an abort function object the solved runs had and never used, which is left out; the
hydrostatic p and p_rgh can differ from the solved runs' in their last printed digit (see README).
"""
import argparse
import shutil
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
R = 8314.46261815324 / 28.96          # the perfect gas's R from molWeight 28.96
T_OUT, T_IN = 308.15, 294.261         # 95 F and 70 F
X_DOOR, Y_MID = .075, 1.065           # the door leaf's plane and the door's mid-height


def header(obj, cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'


def lst(a):
    return 'nonuniform List<scalar>\n' + str(len(a)) + '\n(\n' + '\n'.join('%.15g' % v for v in a) + '\n)'


def hydrostatic(px, py):
    """p of the street (x < 0.075) and of the store at rest, equal at y = 1.065 m."""
    out = 1e5 * np.exp(-9.81 * py / (287.1 * T_OUT))
    inside = 1e5 * np.exp(-9.81 * Y_MID / (287.1 * T_OUT)) * np.exp(-9.81 * (py - Y_MID) / (287.1 * T_IN))
    return np.where(px < X_DOOR, out, inside)


def prgh(px, py):
    p = hydrostatic(px, py)
    return p + p / (R * np.where(px < X_DOOR, T_OUT, T_IN)) * 9.81 * py


WALL = {'U': 'type noSlip;', 'T': 'type zeroGradient;', 'outdoor': 'type zeroGradient;',
        'k': 'type kLowReWallFunction; value uniform 1e-4;', 'omega': 'type omegaWallFunction; value uniform 1;',
        'nut': 'type nutkWallFunction; value uniform 0;',
        'alphat': 'type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;'}
OPEN = {'U': 'type pressureInletOutletVelocity; value uniform (0 0 0);',
        'T': 'type inletOutlet; inletValue uniform 308.15; value uniform 308.15;',
        'outdoor': 'type inletOutlet; inletValue uniform 1; value uniform 1;',
        'k': 'type inletOutlet; inletValue uniform 1e-4; value uniform 1e-4;',
        'omega': 'type inletOutlet; inletValue uniform 0.18257418583505536; value uniform 1;',
        'nut': 'type calculated; value uniform 0;', 'alphat': 'type calculated; value uniform 0;'}
MAPPED = ('type outletMappedUniformInlet; outlets { curtainIntake { offset 0; fraction 1; timeDelay 0; } } '
          'phi phi; value uniform ')
SLOT = {'U': 'type fixedValue; value uniform (-2.0521 -5.6382 0);', 'T': MAPPED + '294.261;', 'outdoor': MAPPED + '0;',
        'k': 'type turbulentIntensityKineticEnergyInlet; intensity 0.05; value uniform .135;',
        'omega': 'type turbulentMixingLengthFrequencyInlet; mixingLength .006; value uniform 100;',
        'nut': 'type calculated; value uniform 0;', 'alphat': 'type calculated; value uniform 0;'}
INTAKE = {'U': 'type flowRateOutletVelocity; volumetricFlowRate 0.33829; value uniform (-1.6109047619 0 0);',
          'T': 'type zeroGradient;', 'outdoor': 'type zeroGradient;', 'k': 'type zeroGradient;',
          'omega': 'type zeroGradient;', 'nut': 'type calculated; value uniform 0;',
          'alphat': 'type calculated; value uniform 0;'}
DIMS = {'U': '0 1 -1 0 0 0 0', 'T': '0 0 0 1 0 0 0', 'outdoor': '0 0 0 0 0 0 0', 'p': '1 -1 -2 0 0 0 0',
        'p_rgh': '1 -1 -2 0 0 0 0', 'k': '0 2 -2 0 0 0 0', 'omega': '0 0 -1 0 0 0 0', 'nut': '0 2 -1 0 0 0 0',
        'alphat': '1 -1 -1 0 0 0 0'}
PATCHES = ['street', 'sky', 'sidewalk', 'storefront', 'doorHead', 'frontInside', 'floor', 'ceiling', 'backWall',
           'curtainSlot', 'curtainIntake', 'curtainBody', 'frontAndBack']

PLANES = """ planes {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval 0.125; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor); surfaces {
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
    cx, cy = g['cc'][:, 0], g['cc'][:, 1]

    initial = {'T': lst(np.where(cx < X_DOOR, T_OUT, T_IN)), 'outdoor': lst((cx < X_DOOR).astype(float)),
               'p': lst(hydrostatic(cx, cy)), 'p_rgh': lst(prgh(cx, cy)), 'U': 'uniform (0 0 0)',
               'k': 'uniform 0.0001', 'omega': 'uniform 1', 'nut': 'uniform 0', 'alphat': 'uniform 0'}
    for fld in DIMS:
        text = (header(fld, 'volVectorField' if fld == 'U' else 'volScalarField') + f'dimensions [{DIMS[fld]}];\n'
                'internalField ' + initial[fld] + ';\nboundaryField\n{\n')
        for pn in PATCHES:
            if pn == 'frontAndBack':
                bc = 'type empty;'
            elif fld in ['p', 'p_rgh']:
                fx, fy = g['face_' + pn][:, 0], g['face_' + pn][:, 1]
                if fld == 'p':
                    bc = 'type calculated; value ' + lst(hydrostatic(fx, fy)) + ';'
                elif pn in ['street', 'sky']:
                    bc = ('type prghTotalPressure; p0 ' + lst(1e5 * np.exp(-9.81 * fy / (287.1 * T_OUT)))
                          + '; value ' + lst(prgh(fx, fy)) + ';')
                else:
                    bc = 'type fixedFluxPressure; value ' + lst(prgh(fx, fy)) + ';'
            elif pn in ['street', 'sky']:
                bc = OPEN[fld]
            elif on and pn == 'curtainSlot':
                bc = SLOT[fld]
            elif on and pn == 'curtainIntake':
                bc = INTAKE[fld]
            else:
                bc = WALL[fld]
            text += pn + '\n{\n' + bc + '\n}\n'
        (c / '0' / fld).write_text(text + '}\n')
    phi = header('phi', 'surfaceScalarField') + 'dimensions [1 0 -1 0 0 0 0];\ninternalField uniform 0;\nboundaryField\n{\n'
    for pn in PATCHES:
        phi += pn + '\n{\n' + ('type empty;' if pn == 'frontAndBack' else 'type calculated; value uniform 0;') + '\n}\n'
    (c / '0/phi').write_text(phi + '}\n')

    shutil.copytree(CASE / 'template/constant', c / 'constant', dirs_exist_ok=True)
    for f in ['fvSchemes', 'fvSolution', 'initialSurfaces', 'monitor']:
        shutil.copy(CASE / 'template/system' / f, c / 'system' / f)
    (c / 'system/decomposeParDict').write_text(header('decomposeParDict') + f'numberOfSubdomains {nprocs}; method scotch;\n')
    (c / 'system/controlDict').write_text(
        header('controlDict') + f'application buoyantPimpleFoam; startFrom latestTime; startTime 0; stopAt endTime; '
        f'endTime {end}; deltaT 0.0000833333333333333; adjustTimeStep yes; maxCo 1; maxDeltaT .02; '
        'writeControl adjustableRunTime; writeInterval 10; purgeWrite 0; writeFormat binary; writePrecision 12; '
        'writeCompression on; timeFormat general; timePrecision 12; runTimeModifiable false; functions {\n'
        + FUNCTIONS + PLANES + '\n#include "monitor"\n\n}\n')
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
