#!/usr/bin/env python3
"""Write one stage of a run, as the cloud's scripts/prepare.py and its production controllers did.

  python3 scripts/make_case.py prerun        <case> <mesh> <end>
  python3 scripts/make_case.py pre    <run>  <case> <mesh> <from> <start> <end>
  python3 scripts/make_case.py run    <run>  <case> <mesh> <from>         <end>

<run> is vents or noVents. prerun is the shared flow from rest with every nozzle shut (0-70 s on
the cloud, Courant 2); pre the 20 s that follow, from the prerun's last time, with the row's six
nozzles opened over 0.5 s in vents (70-90 s); run the cough, 0-60 s from the pre stage's last
time with the clock set back to 0. <from> must be reconstructed already; its last time's p,
p_rgh, phi, U, T, k, omega, nut and alphat are carried over byte for byte, with only the
boundaries that change (the nozzles opening, the mouth's cough) taken from the new 0/.
The cloud's continuation gate (largest speed under 12 m/s, exhausts 294-301 K) is not repeated.
"""
from pathlib import Path
import gzip, json, re, shutil, subprocess, sys
import numpy as np

here = Path(__file__).resolve().parents[1]
tpl = here / 'template'
g = json.loads((here / 'scripts/geometry.json').read_text())
zs = [1.48, 1.0, .66, -.66, -1.0, -1.48]


def h(o, cl='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cl}; object {o}; }}\n'


def vec(v):
    return '(' + ' '.join(map(str, v)) + ')'


def lst(a, typ='scalar'):
    return 'nonuniform List<' + typ + '>\n' + str(len(a)) + '\n(\n' + '\n'.join(vec(x) if typ == 'vector' else f'{x:.15g}' for x in a) + '\n)'


def source(n, force, ramp=False):
    direction = (0, -.9680, -.2509) if n == 'forceC' else ((0, -.9680, .2509) if n == 'forceD' else (0, -1, 0))
    norm = sum(q * q for q in direction) ** .5
    vv = vec([force * q / norm for q in direction])
    f = f'explicit table ((0 (0 0 0)) (0.5 {vv}) (1000 {vv}));' if ramp else f'explicit {vv};'
    return n + ' { type vectorSemiImplicitSource; selectionMode cellSet; cellSet ' + n + '; volumeMode absolute; sources { U { ' + f + ' implicit 0; } } }\n'


# the fitted force per nozzle (results/TESTS_PASSED.json on the cloud: attempt 2 of the still-air fit)
F = 0.03046304337312167


def prepare(c, mesh, kind, end, tracer=False, ramp=False):
    """prepare.py's prepare(name, kind, F, end, slots=True, heated=True, tracer, ramp)."""
    arr = np.load(mesh / 'mesh_arrays.npz')
    C = arr['C']
    for d in ['system', '0', 'constant']:
        (c / d).mkdir(parents=True, exist_ok=True)
    shutil.copytree(mesh / 'constant/polyMesh', c / 'constant/polyMesh', dirs_exist_ok=True)
    on = kind == 'vents'
    # Closed supply patches must be walls for SST wall functions.
    bp = c / 'constant/polyMesh/boundary'
    bs = bp.read_text()
    for n in ['nozzle' + k for k in 'ABCDEF']:
        if not on:
            bs = re.sub(r'(' + n + r'\s*\{\s*type\s+)patch', r'\1wall', bs)
    bp.write_text(bs)
    # explicit source and sink sets from cell centres
    sets = c / 'constant/polyMesh/sets'
    shutil.rmtree(sets, ignore_errors=True)
    sets.mkdir()
    selections = {'ceilingForce': (C[:, 1] > 2.16) & (abs(C[:, 2]) < .04)}
    for k, z in zip('ABCDEF', zs):
        selections['force' + k] = (C[:, 0] > 1.30) & (C[:, 0] < 1.34) & (C[:, 1] > 1.56) & (C[:, 1] < 1.60) & (abs(C[:, 2] - z) < .02)
    selections['sinkAft'] = C[:, 0] < .04
    selections['sinkFore'] = C[:, 0] > 2.36
    for n, mask in selections.items():
        ids = np.flatnonzero(mask)
        (sets / n).write_text(h(n, 'cellSet') + str(len(ids)) + '\n(\n' + '\n'.join(map(str, ids)) + '\n)\n')
    for n in ['g', 'thermophysicalProperties', 'turbulenceProperties']:
        shutil.copy(tpl / 'common/constant' / n, c / 'constant' / n)
    # buoyancy production, the energy observer (diagnostic only) and the ceiling slot's momentum
    options = (tpl / 'common/constant/fvOptions').read_text()
    if on:
        for k in 'ABCDEF':
            options += source('force' + k, F, ramp)
    (c / 'constant/fvOptions').write_text(options)
    for n in ['fvSchemes', 'fvSolution', 'decomposeParDict']:
        shutil.copy(tpl / 'common/system' / n, c / 'system' / n)
    T0 = 296.45
    gasR = 8314.46261815324 / 28.96
    p0 = 75262 * np.exp(-9.81 * C[:, 1] / (gasR * T0))
    rho0 = p0 / (gasR * T0)
    s = (c / 'constant/polyMesh/boundary').read_text()
    patches = {n: (int(nf), int(start)) for n, nf, start in re.findall(r'(\w+)\s*\{[^{}]*?nFaces\s+(\d+);\s*startFace\s+(\d+);', s)}

    def body(n):
        s = (c / 'constant/polyMesh' / n).read_text()
        s = s[s.index('}', s.index('FoamFile')) + 1:]
        return s[s.index('(') + 1:s.rindex(')')]
    pts = np.array([np.fromstring(x, sep=' ') for x in re.findall(r'\(([^()]+)\)', body('points'))])
    faces = [np.fromstring(x, sep=' ', dtype=int) for x in re.findall(r'\d+\(([^()]*)\)', body('faces'))]
    dims = {'U': '0 1 -1 0 0 0 0', 'T': '0 0 0 1 0 0 0', 'p': '1 -1 -2 0 0 0 0', 'p_rgh': '1 -1 -2 0 0 0 0', 'k': '0 2 -2 0 0 0 0', 'omega': '0 0 -1 0 0 0 0', 'nut': '0 2 -1 0 0 0 0', 'alphat': '1 -1 -1 0 0 0 0', 'cough': '0 0 0 0 0 0 0'}
    vals = {'U': '(0 0 0)', 'T': str(T0), 'k': '1e-4', 'omega': '1', 'nut': '0', 'alphat': '0', 'cough': '0'}
    for n in dims:
        s = h(n, 'volVectorField' if n == 'U' else 'volScalarField') + f'dimensions [{dims[n]}];\n'
        s += 'internalField ' + (lst(p0 if n == 'p' else p0 + rho0 * 9.81 * C[:, 1]) if n in ['p', 'p_rgh'] else 'uniform ' + vals[n]) + ';\nboundaryField\n{\n'
        for w, (nf, start) in patches.items():
            inlet = w in ['sideSlotR', 'sideSlotL', 'ceilingSlot'] or (on and w.startswith('nozzle'))
            out = w.startswith('exhaust')
            cyclic = w.startswith('cyclic')
            bc = {'U': 'type noSlip;', 'T': 'type zeroGradient;', 'p': 'type calculated; value uniform 75262;', 'p_rgh': 'type fixedFluxPressure; value uniform 75262;', 'k': 'type kLowReWallFunction; value uniform 1e-4;', 'omega': 'type omegaWallFunction; value uniform 1;', 'nut': 'type nutkWallFunction; value uniform 0;', 'alphat': 'type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;', 'cough': 'type zeroGradient;'}[n]
            if w == 'people' and n == 'T':
                bc = 'type externalWallHeatFluxTemperature; mode power; Q 720; kappaMethod fluidThermo; value uniform 296.45;'
            if inlet:
                q = .0012 if w.startswith('nozzle') else (.02707 if w == 'ceilingSlot' else .07105)
                mass = q * .8964
                area = .0016 if w.startswith('nozzle') else (.192 if w == 'ceilingSlot' else .048)
                speed = q / area
                length = .005 if w == 'ceilingSlot' else .002
                if n == 'U':
                    rate = f'table ((0 0) (0.5 {mass}) (1000 {mass}))' if ramp and w.startswith('nozzle') else str(mass)
                    bc = f'type flowRateInletVelocity; massFlowRate {rate}; rho rho; rhoInlet 0.8964; value uniform (0 0 0);'
                if n == 'T':
                    bc = 'type fixedValue; value uniform 292.45;'
                if n == 'k':
                    bc = f'type turbulentIntensityKineticEnergyInlet; intensity 0.10; value uniform {1.5 * (.1 * speed) ** 2};'
                if n == 'omega':
                    bc = f'type turbulentMixingLengthFrequencyInlet; mixingLength {length}; value uniform {(.15 ** .5 * speed) / (.09 ** .25 * length)};'
                if n in ['nut', 'alphat']:
                    bc = 'type calculated; value uniform 0;'
                if n == 'cough':
                    bc = 'type fixedValue; value uniform 0;'
            if out:
                if n == 'U':
                    bc = 'type pressureInletOutletVelocity; value uniform (0 0 0);'
                if n == 'p_rgh':
                    yy = np.array([pts[f].mean(axis=0)[1] for f in faces[start:start + nf]])
                    pp = 75262 * np.exp(-9.81 * yy / (287.1 * T0))
                    bc = 'type prghPressure; p ' + lst(pp) + '; value uniform 75262;'
                if n in ['T', 'k', 'omega', 'cough']:
                    value = {'T': T0, 'k': 1e-4, 'omega': 1, 'cough': 0}[n]
                    bc = f'type inletOutlet; inletValue uniform {value}; value uniform {value};'
                if n in ['nut', 'alphat']:
                    bc = 'type calculated; value uniform 0;'
            if w == 'mouth':
                if n == 'T':
                    bc = 'type inletOutlet; inletValue uniform 307.15; value uniform ' + str(T0) + ';'
                if n == 'cough':
                    bc = 'type inletOutlet; inletValue uniform 1; value uniform 0;'
                if n == 'U' and tracer:
                    a = np.loadtxt(here / 'scripts/cough_flow.csv', delimiter=',', skiprows=1)
                    a[:, 1] *= .001
                    total = np.trapezoid(a[:, 1], a[:, 0]) if hasattr(np, 'trapezoid') else np.trapz(a[:, 1], a[:, 0])
                    a[:, 1] *= .0007 / total
                    table = '\n'.join(f'({t:g} ({q / .0004:.15g} {-0.5206 * q / .0004:.15g} 0))' for t, q in a)
                    bc = 'type uniformFixedValue; uniformValue table\n(\n' + table + '\n(1000 (0 0 0))\n); value uniform (0 0 0);'
                if n in ['k', 'omega']:
                    bc = 'type zeroGradient;'
                if n in ['nut', 'alphat']:
                    bc = 'type calculated; value uniform 0;'
            if cyclic:
                bc = 'type cyclic;'
            s += w + ' { ' + bc + ' }\n'
        (c / '0' / n).write_text(s + '}\n')
    stage = 'run' if tracer else 'pre'
    for f in (tpl / stage / 'system').iterdir():
        shutil.copy(f, c / 'system' / f.name)
    (c / 'system/controlDict').write_text(h('controlDict') + f'''application buoyantPimpleFoam;
 startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT 0.0005;
 adjustTimeStep yes; maxCo {2 if kind == 'prerun' else 1}; maxDeltaT 0.02;
 writeControl adjustableRunTime; writeInterval 20; purgeWrite 3;
 writeFormat binary; writeCompression on; writePrecision 10; timeFormat general; timePrecision 10;
 runTimeModifiable false; functions {{ #include "functions" }}
''')
    (c / 'case.foam').touch()


def carry(source, dest, new_nozzles=False, cough=False):
    """production_controller.py's carry(): the last time's fields into dest/0, byte for byte."""
    dirs = [p for p in source.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.eE+-]+', p.name)]
    latest = max(dirs, key=lambda p: float(p.name))
    prepared = {p.name: p.read_bytes() for p in (dest / '0').iterdir() if p.is_file()}
    for n in ['p', 'p_rgh', 'phi', 'U', 'T', 'k', 'omega', 'nut', 'alphat']:
        src = latest / n
        if not src.exists():
            src = latest / (n + '.gz')
        if not src.exists():
            sys.exit('Missing carried restart field ' + n + ' in ' + str(latest))
        data = gzip.decompress(src.read_bytes()) if src.suffix == '.gz' else src.read_bytes()
        data = re.sub(rb'location\s+"[^"]+";', b'location "0";', data, count=1)

        def source_block(name):
            match = re.search(rb'\b' + name.encode() + rb'\s*\{.*?\n    \}', data, re.S)
            if not match:
                sys.exit('Missing restart boundary ' + n + '/' + name)
            return match

        def entry(block, key):
            q = re.search(rb'\b' + key.encode() + rb'\s+(uniform|nonuniform)\s+', block)
            if not q:
                return None
            if q.group(1) == b'uniform':
                end = block.index(b';', q.end()) + 1
            else:
                z = re.match(rb'List<(scalar|vector)>\s+(\d+)\s*\(', block[q.end():])
                if not z:
                    sys.exit('Binary patch list header ' + n)
                end = q.end() + z.end() + int(z.group(2)) * 8 * (3 if z.group(1) == b'vector' else 1)
                if block[end:end + 2] != b');':
                    sys.exit('Binary patch list terminator ' + n)
                end += 2
            return block[q.start():end]
        if new_nozzles and n in prepared and (not cough or n == 'U'):
            for k in 'ABCDEF':
                name = 'nozzle' + k
                original = source_block(name)
                target = re.search(rb'\b' + name.encode() + rb'\s*\{[^{}]*\}', prepared[n], re.S)
                if not target:
                    sys.exit('Missing prepared boundary ' + n + '/' + name)
                replacement = target.group(0)
                if n != 'T':
                    value = entry(original.group(0), 'value')
                    if value:
                        replacement = re.sub(rb'\bvalue\s+uniform[^;]+;', lambda _: value, replacement, count=1)
                data = data[:original.start()] + replacement + data[original.end():]
        if cough and n == 'U':
            original = source_block('mouth')
            target = re.search(rb'\bmouth\s*\{[^{}]*\}', prepared[n], re.S)
            data = data[:original.start()] + target.group(0) + data[original.end():]
        (dest / '0' / n).write_bytes(data)
    # buoyantPimpleFoam's rho is NO_READ/NO_WRITE; it is written from the carried p and T by the
    # solver's own thermodynamics, for the maps at t = 0
    shutil.copy(tpl / 'run/system/writeRho', dest / 'system/writeRho')
    with open(dest / 'log.buoyantPimpleFoam.rhoInit', 'w') as f:
        r = subprocess.run(['buoyantPimpleFoam', '-postProcess', '-dict', 'system/writeRho', '-time', '0'], cwd=dest, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode or not (dest / '0/rho').exists():
        sys.exit('rho from the carried p and T failed, see ' + str(dest / 'log.buoyantPimpleFoam.rhoInit'))
    return latest.name


def settime(c, start, end):
    p = c / 'system/controlDict'
    s = p.read_text()
    s = re.sub(r'startTime\s+[^;]+;', f'startTime {start};', s)
    s = re.sub(r'endTime\s+[^;]+;', f'endTime {end};', s)
    p.write_text(s)
    if float(start) != 0:
        shutil.move(c / '0', c / str(start))


def main(a):
    if a[0] == 'prerun':
        c, mesh, end = Path(a[1]), Path(a[2]), a[3]
        prepare(c, mesh, 'prerun', end)
    elif a[0] == 'pre':
        run, c, mesh, src, start, end = a[1], Path(a[2]), Path(a[3]), Path(a[4]), a[5], a[6]
        prepare(c, mesh, run, end, ramp=run == 'vents')
        got = carry(src, c, new_nozzles=run == 'vents')
        if abs(float(got) - float(start)) > 1e-7:
            sys.exit(f'{src} ends at {got} s, not {start} s')
        if run == 'vents':
            # the nozzles open over the first 0.5 s of this stage
            for fn in ['constant/fvOptions', '0/U']:
                p = c / fn
                b = p.read_bytes().replace(b'(0 (0 0 0))', f'({start} (0 0 0))'.encode()).replace(b'(0.5 ', f'({float(start) + .5:g} '.encode()).replace(b'table ((0 0)', f'table (({start} 0)'.encode())
                p.write_bytes(b)
        settime(c, start, end)
    elif a[0] == 'run':
        run, c, mesh, src, end = a[1], Path(a[2]), Path(a[3]), Path(a[4]), a[5]
        prepare(c, mesh, run, end, tracer=True)
        carry(src, c, new_nozzles=run == 'vents', cough=True)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
