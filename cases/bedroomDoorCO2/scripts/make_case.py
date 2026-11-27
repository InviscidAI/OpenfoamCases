#!/usr/bin/env python3
"""Write one run's case around its mesh: template/common and template/<run> copied into RUNDIR,
and 0/ written from the mesh (scripts/make_mesh.py's RUNDIR/mesh.npz and mesh.json).

    python3 scripts/make_case.py shut|ajar RUNDIR

0/: the air at rest at 291.15 K (18 C) and 500 ppm of CO2, in hydrostatic balance (p = 1e5 Pa at
the floor, an isothermal 291.15 K column). The house boundary (x = 4.80 m) is a total pressure
equal to that column's at each face's height, at 291.15 K, its CO2 for inflow a table every 600 s of
706 - 206 exp(-t / 9000 s). The window and the outside wall lose heat to 273.15 K (0 C) and the
floor, the ceiling and the door wall exchange it with the house at 291.15 K, each through an
overall U (0.81, 0.34 and 1.5 W/m2K) given as externalWallHeatFluxTemperature's coefficient h on
each face, h = 1 / (1/U - d/kappa), d the face's cell-centre distance and kappa = Cp mu / Pr the
air's laminar conductivity, so that the wall's own film is not counted twice. Each sleeper's hump
gives the air 14.2857 W per metre of depth (50 W in the 3.5 m deep room); the bed and the door
leaf are adiabatic. k starts at 1e-5 m2/s2, 1e-10 in the doorway cells, where fvOptions holds it.

This is case87.py of the cloud study, the 0/ part, unchanged; its fields match the solved runs'
0/ byte for byte. The rest of constant/ and system/ are the solved runs' own files (template/),
and this script stops if template/<run>/constant/fvOptions does not carry the door resistances
the free areas give.
"""
from pathlib import Path
import json, math, re, shutil, sys
import numpy as np

HERE = Path(__file__).resolve().parents[1]
RGAS = 8314.46261815324 / 28.96


def H(o, c='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {c}; object {o}; }}\n'


def lst(vals):
    return str(len(vals)) + '\n(\n' + '\n'.join(map(str, vals)) + '\n)\n'


def field(name, dim, init, bcs, cl='volScalarField'):
    return H(name, cl) + f'dimensions {dim};\ninternalField ' + init + ';\nboundaryField\n{\n' + ''.join(p + ' { ' + bc + ' }\n' for p, bc in bcs.items()) + '}\n'


def door_resistance(door):
    """DarcyForchheimer f per band (doorUnder, doorLeaf, doorHead), 1/m: a band of height h whose
    real free area per metre of depth is a passes the gap law Q = 0.6 a sqrt(2 dp / rho) through
    its 0.1 m thickness when f = 1 / (0.1 (0.6 a / h)^2). Shut: 12 mm undercut (9,600 mm2), 3 mm
    head gap (2,400 mm2) and 3 mm side gaps (12,180 mm2) on a 0.80 x 2.03 m door, the side gaps'
    area moved 80:20 into the undercut and the head, the leaf solid. Ajar: a 10 cm latch gap,
    0.203 m2 plus the undercut, over the doorway's height."""
    heights = [.02, 1.99, .02]
    if door == 'shut':
        areas = [.0096 / 3.5 + .00348 * .8, 0, .0024 / 3.5 + .00348 * .2]
        return [1 / (.1 * (.6 * a / h) ** 2) if a else 0 for a, h in zip(areas, heights)]
    return [1 / (.1 * (.6 * ((.203 + .0096) / 3.5) / 2.03) ** 2)] * 3


def main(door, rundir):
    c = Path(rundir)
    for part in ['constant', 'system']:
        for src in [HERE / 'template/common' / part, HERE / 'template' / door / part]:
            if src.exists():
                shutil.copytree(src, c / part, dirs_exist_ok=True)
    fv = (c / 'constant/fvOptions').read_text()
    for z, f in zip(['doorUnder', 'doorLeaf', 'doorHead'], door_resistance(door)):
        m = re.search(r'resistance_' + z + r' .*?f \(([\d.e+-]+) ', fv)
        if (m is None) != (f == 0) or (m and abs(float(m[1]) / f - 1) > 1e-9):
            sys.exit(f'template/{door}/constant/fvOptions: resistance_{z} is not f = {f:.12g} 1/m')
    meta = json.loads((c / 'mesh.json').read_text()); cc = np.load(c / 'mesh.npz')['centres']
    p = 1e5 * np.exp(-9.81 * cc[:, 1] / (RGAS * 291.15)); rho = p / (RGAS * 291.15)
    (c / '0').mkdir(exist_ok=True)
    for f, d, init in [('U', '[0 1 -1 0 0 0 0]', 'uniform (0 0 0)'), ('T', '[0 0 0 1 0 0 0]', 'uniform 291.15'),
                       ('CO2', '[0 0 0 0 0 0 0]', 'uniform 500'), ('k', '[0 2 -2 0 0 0 0]', 'uniform 1e-5'),
                       ('omega', '[0 0 -1 0 0 0 0]', 'uniform .0577350269'), ('nut', '[0 2 -1 0 0 0 0]', 'uniform 0'),
                       ('alphat', '[1 -1 -1 0 0 0 0]', 'uniform 0'),
                       ('p', '[1 -1 -2 0 0 0 0]', 'nonuniform List<scalar>\n' + lst(p)),
                       ('p_rgh', '[1 -1 -2 0 0 0 0]', 'nonuniform List<scalar>\n' + lst(p + rho * 9.81 * cc[:, 1]))]:
        bcs = {}
        for patch in meta['patch_areas_m2_per_m']:
            bc = 'zeroGradient;'
            if patch == 'frontAndBack':
                bc = 'type empty;'
            elif patch == 'house':
                if f == 'U':
                    bc = 'type pressureInletOutletVelocity; value uniform (0 0 0);'
                elif f == 'p_rgh':
                    pc = np.array(meta['patch_centres'][patch]); ph = 1e5 * np.exp(-9.81 * pc[:, 1] / (RGAS * 291.15))
                    bc = 'type prghTotalPressure; rho rho; p0 nonuniform List<scalar>\n' + lst(ph) + '; value uniform 1e5;'
                elif f == 'p':
                    bc = 'type calculated; value uniform 1e5;'
                elif f in ['T', 'k', 'omega']:
                    bc = f'type inletOutlet; inletValue {init}; value {init};'
                elif f == 'CO2':
                    table = '\n'.join(f'({t} {706 - 206 * math.exp(-t / 9000):.12g})' for t in range(0, 28801, 600))
                    bc = 'type uniformInletOutlet; uniformInletValue table\n(\n' + table + '\n); value uniform 500;'
                else:
                    bc = 'type calculated; value uniform 0;'
            elif f == 'U':
                bc = 'type noSlip;'
            elif f == 'p_rgh':
                bc = 'type fixedFluxPressure; value uniform 1e5;'
            elif f == 'p':
                bc = 'type calculated; value uniform 1e5;'
            elif f == 'k':
                bc = 'type kLowReWallFunction; value uniform 1e-5;'
            elif f == 'omega':
                bc = 'type omegaWallFunction; value uniform .0577350269;'
            elif f == 'nut':
                bc = 'type nutkWallFunction; value uniform 0;'
            elif f == 'alphat':
                bc = 'type compressible::alphatJayatillekeWallFunction; Prt .85; value uniform 0;'
            elif f == 'T' and patch not in ['bed', 'doorLeafWall']:
                if patch.startswith('sleeper'):
                    bc = 'type externalWallHeatFluxTemperature; mode power; Q 14.2857; kappaMethod fluidThermo; value uniform 291.15;'
                else:
                    overall = .81 if patch == 'window' else .34 if patch == 'outsideWall' else 1.5
                    ta = 273.15 if patch in ['window', 'outsideWall'] else 291.15
                    kappa = 1005 * 1.82e-5 / .71; dist = np.array(meta['patch_distance'][patch]); ht = 1 / (1 / overall - dist / kappa)
                    bc = f'type externalWallHeatFluxTemperature; mode coefficient; Ta constant {ta}; h nonuniform List<scalar>\n' + lst(ht) + '; kappaMethod fluidThermo; value uniform 291.15;'
            else:
                bc = 'type zeroGradient;'
            bcs[patch] = bc
        kinitial = 'nonuniform List<scalar>\n' + lst(np.where((cc[:, 0] > 3.5) & (cc[:, 0] < 3.6) & (cc[:, 1] < 2.03), 1e-10, 1e-5)) if f == 'k' else init
        (c / '0' / f).write_text(field(f, d, kinitial, bcs, 'volVectorField' if f == 'U' else 'volScalarField'))
    (c / 'case.foam').touch()


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('shut', 'ajar'):
        sys.exit('usage: make_case.py shut|ajar RUNDIR')
    main(*sys.argv[1:])
