#!/usr/bin/env python3
"""Check that a written time's T still carries every wall's heat-transfer coefficient h and
ambient Ta as 0/T gives them, and stop if not.

    python3 scripts/check_coefficients.py RUNDIR TIME|latest

Run on a reconstructed time (RUNDIR/<TIME>/T). It reads both files with foamDictionary at 17
digits (so a binary T is read too) and compares, for each patch whose T is
externalWallHeatFluxTemperature in coefficient mode, every face's h to within 1e-9 relative and Ta
exactly. With OpenFOAM v2512's own externalWallHeatFluxTemperature, reconstructPar writes most of
these patches as "h constant 0" (the ConstantField takes its uniform metadata from a processor
whose part of the patch is empty), and a run restarted from them loses the window's, the walls'
and the floor's heat transfer without any message: the fault of the first production runs at
7,200 s. src/restartSafeConstant, which system/controlDict loads, writes the mapped values.
"""
from pathlib import Path
import re, subprocess, sys


def entry(case, time, path):
    out = subprocess.run(['foamDictionary', '-precision', '17', '-entry', path, '-value', str(case / str(time) / 'T')],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit(f'check_coefficients: cannot read {path} in {case}/{time}/T:\n{out.stderr[-800:]}')
    return out.stdout.strip()


def values(text):
    t = text.split()
    if t[0] in ('uniform', 'constant'):
        return None, float(t[1])
    m = re.search(r'(\d+)\s*\{\s*([^}\s]+)\s*\}', text)   # N{value}: N equal values
    if m:
        return [float(m[2])] * int(m[1]), None
    m = re.search(r'\(([^)]*)\)', text)
    return [float(v) for v in m[1].split()], None


def main(case, time):
    case = Path(case)
    if time == 'latest':
        times = [p.name for p in case.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.e+-]+', p.name) and p.name != '0']
        time = max(times, key=float)
    boundary = (case / 'constant/polyMesh/boundary').read_text()
    nfaces = {m[0]: int(m[1]) for m in re.findall(r'^(\w+)\n\{ type \w+; nFaces (\d+);', boundary, re.M)}
    bad = []; checked = 0
    for patch, n in nfaces.items():
        keys = subprocess.run(['foamDictionary', '-entry', f'boundaryField/{patch}', '-keywords', str(case / '0/T')],
                              capture_output=True, text=True).stdout.split()
        if 'mode' not in keys or entry(case, 0, f'boundaryField/{patch}/mode') != 'coefficient':
            continue
        for name in ['h', 'Ta']:
            a = entry(case, 0, f'boundaryField/{patch}/{name}'); b = entry(case, time, f'boundaryField/{patch}/{name}')
            la, ua = values(a); lb, ub = values(b)
            va = la if la is not None else [ua] * n; vb = lb if lb is not None else [ub] * n
            ok = len(va) == len(vb) == n and all(abs(x - y) <= 1e-9 * max(abs(x), 1e-30) if name == 'h' else x == y
                                                  for x, y in zip(va, vb))
            checked += 1
            if not ok:
                bad.append(f'  {patch}/{name}: 0/T {a[:60]!r}, {time}/T {b[:60]!r}')
    if bad:
        sys.exit(f'check_coefficients: {case}/{time}/T has lost walls\' coefficients:\n' + '\n'.join(bad))
    print(f'check_coefficients: {case}/{time}/T keeps h and Ta on all {checked // 2} coefficient walls')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: check_coefficients.py RUNDIR TIME|latest')
    main(*sys.argv[1:])
