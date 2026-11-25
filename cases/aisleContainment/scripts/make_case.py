#!/usr/bin/env python3
"""Write one hall's 0/, constant/ and system/ next to the mesh make_mesh.py wrote.

    python3 scripts/make_case.py open|contained runs/<run> [--nprocs 4] [--planes]

Reads runs/<run>/mesh_report.json and mesh.npz (make_mesh.py) and config/case.json, and copies
template/constant and template/system. Writes:

  0/T U p p_rgh k omega nut alphat phi
      the air at rest at 293.15 K in isothermal hydrostatic balance, 1e5 Pa at the ceiling
      (p = 1e5 exp(g (3.2 - z) / (R T0)), R = 287.05 J/kg K), on every cell and every boundary
      face, and the boundary conditions:
        supply_south/north  flowRateInletVelocity at the supply's mass flow, 293.15 K
        <server>_intake     flowRateOutletVelocity at the server's mass flow, zeroGradient T
        <server>_exhaust    flowRateInletVelocity at the same mass flow; T is
                            outletMappedUniformInlet, the intake's flux-weighted mean + 15 K
        return_0k           prghPressure at 1e5 Pa, pressureInletOutletVelocity, inletOutlet T
                            (308.15 K if anything comes back in)
        walls, panels, end doors  no-slip, adiabatic, wall functions
      phi carries the fixed flows on the supply and server faces from the first step, so that the
      heat is on from t = 0 (the "seeded" flux)
  system/controlDict   0-30 s, with the hallMonitor function object (src/hallMonitor)
  system/decomposeParDict  simple, as the solved runs (4 ranks, 2 x 2 x 1)

--planes turns on the monitor's plane export (planes every 0.125 s and 0.5 s, about 10 GB a run
over 120 s); without it only the monitor's CSV files are written.
"""
import argparse
import json
import pathlib
import shutil

import numpy as np

CASE = pathlib.Path(__file__).resolve().parents[1]
R = 287.05
G = 9.81


def header(obj, cls='dictionary'):
    return f'FoamFile\n{{\n version 2.0;\n format ascii;\n class {cls};\n object {obj};\n}}\n'


def arr(a, kind='scalar'):
    return ('nonuniform List<' + kind + '>\n' + str(len(a)) + '\n(\n'
            + '\n'.join(str(float(v)) if kind == 'scalar' else '(' + ' '.join(map(str, v)) + ')' for v in a) + '\n)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['open', 'contained'])
    ap.add_argument('root')
    ap.add_argument('--nprocs', type=int, default=4)
    ap.add_argument('--planes', action='store_true')
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    cfg = json.loads((CASE / 'config/case.json').read_text())
    T0, ztop = cfg['T0'], cfg['hall'][2]
    report = json.loads((root / 'mesh_report.json').read_text())
    d = np.load(root / 'mesh.npz')
    cent, points, faces, vols = d['centers'], d['points'], d['faces'], d['volumes']

    def write(rel, txt, cls='dictionary'):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(header(p.name, cls) + txt)

    p = 1e5 * np.exp(G * (ztop - cent[:, 2]) / (R * T0))
    rho = p / (R * T0)
    dims = {'U': '0 1 -1 0 0 0 0', 'T': '0 0 0 1 0 0 0', 'p': '1 -1 -2 0 0 0 0', 'p_rgh': '1 -1 -2 0 0 0 0',
            'k': '0 2 -2 0 0 0 0', 'omega': '0 0 -1 0 0 0 0', 'nut': '0 2 -1 0 0 0 0', 'alphat': '1 -1 -1 0 0 0 0',
            'phi': '1 0 -1 0 0 0 0'}
    internal = {'U': 'uniform (0 0 0)', 'T': 'uniform 293.15', 'p': arr(p), 'p_rgh': arr(p + rho * G * cent[:, 2]),
                'k': 'uniform 0.0001', 'omega': 'uniform 1', 'nut': 'uniform 0', 'alphat': 'uniform 0', 'phi': 'uniform 0'}
    server, supply, rhoRef = cfg['serverMassFlow'], cfg['supplyMassFlow'], cfg['rhoRef']
    rise, back = cfg['serverRise'], cfg['returnBackflowT']
    bcs = {f: [] for f in dims}
    for b in report['boundaries']:
        n, nf = b['name'], b['nFaces']
        f = faces[b['startFace']:b['startFace'] + nf]
        pc = points[f].mean(1)
        v = points[f]
        sf = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
        ar = np.linalg.norm(sf, axis=1)
        normal = sf / ar[:, None]
        pp = 1e5 * np.exp(G * (ztop - pc[:, 2]) / (R * T0))
        rr = pp / (R * T0)
        wall = b['type'] == 'wall'
        intake, exhaust = n.endswith('_intake'), n.endswith('_exhaust')
        sup, ret = n.startswith('supply'), n.startswith('return')
        flow = server if intake or exhaust else supply if sup else 0
        sign = 1 if intake else -1
        initU = normal * (sign * flow / (rr * b['area_m2']))[:, None] if flow else np.zeros((nf, 3))
        vals = {}
        if wall:
            vals['U'] = 'type fixedValue; value uniform (0 0 0);'
        elif ret:
            vals['U'] = 'type pressureInletOutletVelocity; value uniform (0 0 0);'
        else:
            vals['U'] = ('type ' + ('flowRateOutletVelocity' if intake else 'flowRateInletVelocity') + f'; massFlowRate {flow}; '
                         + ('rhoOutlet' if intake else 'rhoInlet') + f' {rhoRef}; value ' + arr(initU, 'vector') + ';')
        if wall or intake:
            vals['T'] = 'type zeroGradient;'
        elif sup:
            vals['T'] = 'type fixedValue; value uniform 293.15;'
        elif ret:
            vals['T'] = f'type inletOutlet; inletValue uniform {back}; value uniform 293.15;'
        elif exhaust:
            vals['T'] = ('type outletMappedUniformInlet; outlets\n{\n' + n.replace('_exhaust', '_intake')
                         + f'\n{{\n offset {rise:g};\n}}\n}}\n value uniform {T0 + rise:g};')
        vals['p'] = 'type calculated; value ' + arr(pp) + ';'
        vals['p_rgh'] = ('type prghPressure; p uniform 100000; value uniform 100000;' if ret
                         else 'type fixedFluxPressure; value ' + arr(pp + rr * G * pc[:, 2]) + ';')
        vals['k'] = ('type kqRWallFunction; value uniform 0.0001;' if wall else 'type zeroGradient;' if intake
                     else 'type inletOutlet; inletValue uniform 0.02; value uniform 0.02;' if ret else 'type fixedValue; value uniform 0.02;')
        vals['omega'] = ('type omegaWallFunction; value uniform 1;' if wall else 'type zeroGradient;' if intake
                         else 'type inletOutlet; inletValue uniform 10; value uniform 10;' if ret else 'type fixedValue; value uniform 10;')
        vals['nut'] = 'type nutkWallFunction; value uniform 0;' if wall else 'type calculated; value uniform 0;'
        vals['alphat'] = ('type compressible::alphatWallFunction; Prt 0.85; value uniform 0;' if wall
                          else 'type calculated; value uniform 0;')
        vals['phi'] = 'type calculated; value ' + (arr(sign * flow * ar / b['area_m2']) if flow else 'uniform 0') + ';'
        for field in dims:
            bcs[field].append(n + '\n{\n' + vals[field] + '\n}\n')
    for field in dims:
        cls = 'surfaceScalarField' if field == 'phi' else 'volVectorField' if field == 'U' else 'volScalarField'
        write('0/' + field, 'dimensions [' + dims[field] + '];\ninternalField ' + internal[field] + ';\nboundaryField\n{\n'
              + ''.join(bcs[field]) + '}\n', cls)

    for sub in ('constant', 'system'):
        (root / sub).mkdir(parents=True, exist_ok=True)
        for src in sorted((CASE / 'template' / sub).iterdir()):
            shutil.copyfile(src, root / sub / src.name)

    # the cold side's air mass at rest, the monitor's reference for its drift (contained)
    x0 = [4.8 * k + 2.4 for k in range(3)]
    hot = np.zeros(len(cent), bool)
    for lo in x0:
        hot |= (cent[:, 0] > lo) & (cent[:, 0] < lo + 1.2) & (cent[:, 1] > 2.1) & (cent[:, 1] < 14.1)
    cold_mass = float((rho * vols)[~hot].sum())
    lib = '"libhallMonitor.so"'
    write('system/controlDict',
          'application buoyantPimpleFoam;\n'
          'startFrom startTime; startTime 0; stopAt endTime; endTime 30;\n'
          'deltaT 0.0001; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;\n'
          'writeControl adjustableRunTime; writeInterval 30; purgeWrite 0;\n'
          'writeFormat binary; writePrecision 10; writeCompression off;\n'
          'timeFormat general; timePrecision 12; runTimeModifiable yes;\n'
          '\nlibs (' + lib + ');\nfunctions\n{\n hall\n {\n type hallMonitor; planes ' + ('true' if a.planes else 'false')
          + '; contained ' + ('true' if a.mode == 'contained' else 'false') + f'; coldInitialMass {cold_mass!r}; interval 0.125;'
          ' executeControl timeStep; executeInterval 1; writeControl none;\n }\n}\n')
    n = a.nprocs
    split = {1: (1, 1, 1), 2: (2, 1, 1), 4: (2, 2, 1), 8: (4, 2, 1), 16: (4, 4, 1)}.get(n)
    if split is None:
        raise SystemExit('nprocs must be 1, 2, 4, 8 or 16 (the solved runs used 4)')
    write('system/decomposeParDict', f'numberOfSubdomains {n};\nmethod simple;\nsimpleCoeffs\n{{\n n ({split[0]} {split[1]} {split[2]}); delta 0.001;\n}}\n')
    (root / 'case.foam').touch()
    print(f'{root}: written, cold-side air mass at rest {cold_mass!r} kg', flush=True)


if __name__ == '__main__':
    main()
