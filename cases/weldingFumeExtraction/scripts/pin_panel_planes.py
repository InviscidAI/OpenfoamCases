#!/usr/bin/env python3
"""Put the bench plenum's grille panel back on its planes after snappyHexMesh's smoothing.

    python3 scripts/pin_panel_planes.py runs/bench

The grille is a porous cell zone two 1.25 cm cells thick, x 0.175 to 0.2 m over y 0.9-1.4 and
z 1.4-2.6. snappyHexMesh's snapping bows the internal mesh planes there by up to about 3 mm, so a
box selection takes only part of the panel. This moves the points of the faces that separate the
cells either side of x = 0.175, 0.1875 and 0.2 within the panel's y-z extent onto those planes,
along x only. It adds no cells and moves no solid surface. Run topoSet and the extractor's
createPatch again afterwards, so the panel's zone and the grille face zone are taken from the
pinned mesh. Writes panel_plane_constraint.json (faces, points and the largest move per plane).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

from centres import centres


def hdr(obj, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'


def labels(p):
    s = Path(p).read_text()
    m = re.search(r'\n(\d+)\s*\(\s*', s)
    return np.fromstring(s[m.end():s.index(')', m.end())], sep=' ', dtype=np.int64)


def main(c):
    c = Path(c)
    C = centres(c)[0]
    owner, nei = labels(c / 'constant/polyMesh/owner'), labels(c / 'constant/polyMesh/neighbour')
    s = (c / 'constant/polyMesh/points').read_text()
    m = re.search(r'\n(\d+)\s*\(\s*', s)
    P = np.array([list(map(float, re.findall(r'[\d.eE+-]+', l))) for l in s[m.end():s.rindex(')')].splitlines() if l.strip()])
    s = (c / 'constant/polyMesh/faces').read_text()
    m = re.search(r'\n(\d+)\s*\(\s*', s)
    fl = [l for l in s[m.end():s.rindex(')')].splitlines() if l.strip()]
    yz = (C[:, 1] > .9) & (C[:, 1] < 1.4) & (C[:, 2] > 1.4) & (C[:, 2] < 2.6)
    report = []
    for x in [.175, .1875, .2]:
        inside = yz & (C[:, 0] < x)
        ff = np.flatnonzero(inside[owner[:len(nei)]] != inside[nei])
        vertices = []
        for f in ff:
            l = fl[f]
            vertices.extend(np.fromstring(l[l.index('(') + 1:l.index(')')], sep=' ', dtype=int))
        pp = np.unique(vertices)
        before = P[pp, 0].copy()
        P[pp, 0] = x
        report.append({'plane_x_m': x, 'faces': len(ff), 'points': len(pp), 'max_x_displacement_m': float(np.max(np.abs(before - x))),
                       'old_x_min': float(before.min()), 'old_x_max': float(before.max())})
    (c / 'constant/polyMesh/points').write_text(hdr('points', 'vectorField') + str(len(P)) + '\n(\n'
                                                + '\n'.join('(' + ' '.join(f'{v:.14g}' for v in p) + ')' for p in P) + '\n)\n')
    (c / 'panel_plane_constraint.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
