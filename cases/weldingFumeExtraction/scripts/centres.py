"""The mesh's cell centres and boundary face centres, as OpenFOAM computes them.

centres(case) runs `postProcess -func writeCellCentres -time 0` in the case (OpenFOAM must be
sourced, and system/controlDict must write ascii), reads 0/C and removes the files it wrote.
Returns the cell centres (n x 3), and the boundary face centres by patch in the boundary's order.
"""
import re
import subprocess
from pathlib import Path

import numpy as np


def _vectors(text):
    return np.array(text.replace('(', ' ').replace(')', ' ').split(), float).reshape(-1, 3)


def centres(case):
    case = Path(case)
    with (case / 'log.writeCellCentres').open('w') as log:
        subprocess.run(['postProcess', '-func', 'writeCellCentres', '-time', '0'], cwd=case, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    s = (case / '0/C').read_text()
    for f in ['C', 'Cx', 'Cy', 'Cz']:
        (case / '0' / f).unlink(missing_ok=True)
    m = re.search(r'internalField\s+nonuniform\s+List<vector>\s*(\d+)\s*\(', s)
    n = int(m[1])
    end = s.index('boundaryField', m.end())
    cells = _vectors(s[m.end():s.rindex(')', 0, end)])
    assert len(cells) == n
    faces = {}
    for p in re.finditer(r'\n\s*(\w+)\s*\n\s*\{\s*type\s+(\w+);\s*value\s+nonuniform\s+List<vector>\s*(\d+)\s*\(', s[end:]):
        start = end + p.end()
        stop = s.index('\n)', start)
        faces[p[1]] = _vectors(s[start:stop])
        assert len(faces[p[1]]) == int(p[3]), p[1]
    return cells, faces
