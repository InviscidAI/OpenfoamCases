#!/usr/bin/env python3
"""Write one house's case around its mesh: template/common and template/<house> copied into
RUNDIR, and the two fields that depend on the mesh, 0/p and 0/p_rgh, written from it.

    python3 scripts/make_case.py open|insert RUNDIR

The air starts at rest at 289.15 K (16 C) in hydrostatic balance: the pressure is 100,000 Pa at
y = 0 outdoors, carried up the outdoor air's 273.15 K column to y = 0.3 m and from there up the
room's 289.15 K column, cell by cell. Every gap's total pressure is the outdoor column's at its own
face's height, so the stack effect of 16 C inside against 0 C outside is in both houses from the
start. This is prepare84.py of the cloud study, the p and p_rgh part, unchanged; the rest of 0/,
constant/ and system/ are the solved runs' own files (template/). The 192 ray fields and G and qr
come next, from scripts/init_radiation.py.
"""
from pathlib import Path
import re, shutil, sys
import numpy as np

HERE = Path(__file__).resolve().parents[1]
GAPS = ['gapFrontDoor', 'gapBackDoor', 'gapWinLF', 'gapWinLB', 'gapWinS', 'gapWinK']
R_AIR, G, T_IN, T_OUT = 287.1, 9.81, 289.15, 273.15


def hdr(n, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {n};}}\n'


def scalars(v):
    return 'nonuniform List<scalar>\n' + str(len(v)) + '\n(\n' + '\n'.join(f'{x:.14g}' for x in v) + '\n)'


def main(house, rundir):
    r = Path(rundir)
    for part in ['0', 'constant', 'system']:
        for src in [HERE / 'template/common' / part, HERE / 'template' / house / part]:
            if src.exists():
                shutil.copytree(src, r / part, dirs_exist_ok=True)
    a = np.load(r / 'mesh.npz'); C = a['C']; fc = a['fc']
    boundary = (r / 'constant/polyMesh/boundary').read_text()
    patches = re.findall(r'^(\w+)\n\{type', boundary, re.M)
    p_base = 1e5 * np.exp(-G * .3 / (R_AIR * T_OUT))
    p = p_base * np.exp(-G * (C[:, 1] - .3) / (R_AIR * T_IN)); rho = p / (R_AIR * T_IN)
    for n in ['p', 'p_rgh']:
        s = hdr(n, 'volScalarField') + 'dimensions [1 -1 -2 0 0 0 0];\ninternalField ' + scalars(p if n == 'p' else p + rho * G * C[:, 1]) + ';\nboundaryField\n{\n'
        for w in patches:
            b = re.search(r'\b' + w + r'\s*\{([^}]+)', boundary)[1]
            nf = int(re.search(r'nFaces\s+(\d+)', b)[1]); st = int(re.search(r'startFace\s+(\d+)', b)[1])
            if n == 'p':
                bc = 'type calculated; value uniform 100000;'
            elif w in GAPS:
                bc = 'type prghTotalPressure; p0 ' + scalars(1e5 * np.exp(-G * fc[st:st + nf, 1] / (R_AIR * T_OUT))) + '; value uniform 100000;'
            else:
                bc = 'type fixedFluxPressure; value uniform 100000;'
            s += w + '\n{' + bc + '}\n'
        (r / '0' / n).write_text(s + '}\n')
    (r / 'case.foam').touch()


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('open', 'insert'):
        sys.exit('usage: make_case.py open|insert RUNDIR')
    main(*sys.argv[1:])
