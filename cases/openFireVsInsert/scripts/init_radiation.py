#!/usr/bin/env python3
"""The radiation the runs start from: the converged 192-direction fvDOM field of the house at rest,
every surface at 289.15 K and the fire's panel (open) or the glass (insert) at its calibrated
temperature, written into RUNDIR/0 as the 192 ILambda_*_0 fields, G and qr.

    python3 scripts/init_radiation.py open|insert RUNDIR [nProcs]

It solves radiation alone, in a scratch copy (RUNDIR/radiationInit), with src/radiationInit:
eight fvDOM solves of one iteration each, the rays' linear solver allowed ten sweeps, on a T field
that holds every patch fixed. No air moves. This is the cloud study's compare_case(run,
'angular6_verified10', 10, 8, 6) and adopt6.py, whose output the solved runs started from; the
cloud ran it on 4 ranks. It prints the panel's or glass's net radiation into the room, which
should be 1,802 W (open) or 3,500 W (insert).
"""
from pathlib import Path
import csv, re, shutil, subprocess, sys

PANEL = {'open': ('firePanel', 624.7310458891628, 1800), 'insert': ('glass', 708.8792438672974, 3500)}


def hdr(n, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {n};}}\n'


def run(cmd, c, log):
    with (c / ('log.' + log)).open('w') as f:
        p = subprocess.run(cmd, cwd=c, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode:
        sys.exit(f'{cmd[0]} failed: {c}/log.{log}')


def main(house, rundir, nprocs=4):
    r = Path(rundir); c = r / 'radiationInit'; source, temp, target = PANEL[house]
    shutil.rmtree(c, ignore_errors=True); c.mkdir()
    for part in ['constant', 'system']:
        shutil.copytree(r / part, c / part, symlinks=True)
    (c / '0').mkdir()
    for f in ['IDefault']:
        shutil.copy(r / '0' / f, c / '0' / f)
    patches = re.findall(r'^(\w+)\n\{type', (r / 'constant/polyMesh/boundary').read_text(), re.M)
    (c / '0/T').write_text(hdr('T', 'volScalarField') + 'dimensions [0 0 0 1 0 0 0]; internalField uniform 289.15; boundaryField\n{\n'
                           + ''.join(f'{p} {{type fixedValue; value uniform {temp if p == source else 289.15};}}\n' for p in patches) + '}\n')
    f = c / 'system/fvSolution'; f.write_text(re.sub(r'maxIter\s+\d+;', 'maxIter 10;', f.read_text(), count=1))   # the rays' sweeps
    (c / 'constant/radiationProperties').write_text(hdr('radiationProperties') + 'radiation on; radiationModel fvDOM; fvDOMCoeffs {nPhi 6; nTheta 8; maxIter 1; tolerance 1e-5;} solverFreq 1; absorptionEmissionModel none; scatterModel none; sootModel none;\n')
    (c / 'system/calibrationConfig').write_text(hdr('calibrationConfig') + f'target {target}; iterations 8; earlyStop false;\n')
    (c / 'system/controlDict').write_text(hdr('controlDict') + 'application buoyantPimpleFoam;\nlibs (radLayerWall);\nstartFrom startTime; startTime 0; stopAt endTime; endTime 0.1;\n'
                                          'deltaT 0.0005; adjustTimeStep yes; maxCo 1; maxDeltaT 0.05;\nwriteControl adjustableRunTime; writeInterval 30; purgeWrite 3;\n'
                                          'writeFormat binary; writeCompression on; writePrecision 12; timeFormat general; timePrecision 10; runTimeModifiable false;\nfunctions {\n}\n')
    s = (c / 'system/decomposeParDict').read_text(); (c / 'system/decomposeParDict').write_text(re.sub(r'numberOfSubdomains \d+', f'numberOfSubdomains {nprocs}', s))
    run(['decomposePar', '-fileHandler', 'collated'], c, 'decomposePar')
    run(['mpirun', '-np', str(nprocs), 'radiationInit', '-parallel', '-fileHandler', 'collated'], c, 'radiationInit')
    run(['reconstructPar', '-fileHandler', 'collated', '-latestTime'], c, 'reconstructPar')
    last = max((d for d in c.iterdir() if d.is_dir() and re.fullmatch(r'[0-9.e-]+', d.name) and d.name != '0'), key=lambda d: float(d.name))
    for g in (r / '0').glob('ILambda*'):
        g.unlink()
    n = 0
    for g in last.iterdir():
        if g.name in ['qr', 'G'] or g.name.startswith('ILambda'):
            shutil.copy(g, r / '0' / g.name); n += 1
    rows = {row['patch']: float(row['power_absorbed_W']) for row in csv.DictReader(open(c / 'postProcessing/radiation.csv'))}
    power = -rows[source] - (rows['recess'] + rows['throat'] if house == 'open' else 0)
    print(f'{house}: {n} radiation fields into 0/ from t = {last.name}; {source} at {temp:.6f} K gives {power:.2f} W net into the room '
          f'(target {target}), closure {sum(rows.values()) / target:+.5%}')
    if abs(power / target - 1) > .01:
        sys.exit('the radiation into the room is more than 1% off its target')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4) or sys.argv[1] not in ('open', 'insert'):
        sys.exit('usage: init_radiation.py open|insert RUNDIR [nProcs]')
    main(sys.argv[1], sys.argv[2], *(int(a) for a in sys.argv[3:]))
