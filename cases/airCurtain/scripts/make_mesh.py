#!/usr/bin/env python3
"""Write the shared 2-D mesh of the doorway, street and shop as an OpenFOAM polyMesh.

    python3 scripts/make_mesh.py runs/mesh

A tensor grid one cell (1 m) deep in z, less the solids, written directly as points, faces,
owner, neighbour, boundary and faceZones, with no blockMesh. x runs from the street (x = -5)
through the door (the facade at x = 0, the door's inner face at x = 0.2) to the shop's back wall
(x = 8.2); y is up from the pavement and floor. Metres.

  air       the street, x -5 to 0, y 0 to 6; the doorway, x 0 to 0.2, y 0 to 2.2; the shop,
            x 0.2 to 8.2, y 0 to 3.2, less the curtain unit, x 0.2 to 0.5, y 2.25 to 2.5,
            mounted on the inside wall over the door with a 5 cm gap above the door head.
  patches   curtainSlot (the unit's underside, x 0.21-0.27, 6 cm), curtainIntake (its room face,
            x = 0.5, y 2.27-2.48, 21 cm), curtainBody (the rest of the unit), street (x = -5) and
            sky (y = 6), both open, pavement, facade, doorHead, wallInside, floor, ceiling,
            backWall, and frontAndBack (empty).
  faceZones door (x = 0.1), doorInner (x = 0.2) and doorOuter (x = 0), the door's height of
            internal faces, which the monitor sums the flow over. Their flipMap is true, so each
            zone's normal is -x, out of the shop.

The cell sizes follow piecewise-linear targets between fixed lines: 1 cm across the slot and down
the jet's first metres, 1.0-1.9 cm in the doorway, 3.4 cm in the shop to x = 3 m and 4.1 cm beyond,
9.5 cm far out in the street and the sky. 430 x 247 lines, 88,890 cells. Also writes
<mesh>/cells.npz (the grid lines and the cell centres in cell order), which make_case.py reads, and
<mesh>/mesh.json (the patch areas and the cell-size checks).
"""
import json
import sys
from pathlib import Path

import numpy as np


def header(obj, cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'


def graded(lines, px, ph):
    """Grid lines between the fixed lines, the size following h(x) (piecewise linear in px, ph)."""
    out = []
    for a, b in zip(lines[:-1], lines[1:]):
        t = np.linspace(a, b, 10001)
        h = np.interp(t, px, ph)
        s = np.r_[0, np.cumsum((1 / h[:-1] + 1 / h[1:]) * .5 * np.diff(t))]
        n = int(np.ceil(s[-1] - 1e-9))
        out.extend(np.interp(np.linspace(0, s[-1], n + 1)[:-1], s, t))
    return np.r_[out, lines[-1]]


x = graded([-5, -2, -1.5, 0, .1, .2, .21, .27, .5, 1.5, 3, 8.2],
           [-5, -2, -1.5, -.05, .1, .5, .65, 1.5, 1.8, 3, 3.6, 8.2],
           [.095, .035, .019, .019, .01, .01, .019, .019, .034, .034, .041, .041])
y = graded([0, .15, .3, 2.2, 2.25, 2.27, 2.48, 2.5, 3.2, 6],
           [0, .3, .45, 2, 2.2, 2.5, 2.75, 3.2, 6],
           [.0145, .0145, .019, .019, .01, .01, .024, .024, .095])
nx, ny = len(x) - 1, len(y) - 1

PATCHES = ['curtainSlot', 'curtainIntake', 'curtainBody', 'street', 'sky', 'pavement', 'facade',
           'doorHead', 'wallInside', 'floor', 'ceiling', 'backWall', 'frontAndBack']


def is_air(a, b):
    return a < 0 or (a < .2 and b < 2.2) or (a > .2 and b < 3.2 and not (.2 < a < .5 and 2.25 < b < 2.5))


def classify(a, b):
    """The patch of a boundary face whose centre is (a, b)."""
    if abs(a + 5) < 1e-9:
        return 'street'
    if abs(b - 6) < 1e-9:
        return 'sky'
    if abs(b) < 1e-9:
        return 'pavement' if a < 0 else 'floor'
    if abs(a - 8.2) < 1e-9:
        return 'backWall'
    if abs(b - 3.2) < 1e-9 and a > .2:
        return 'ceiling'
    if abs(b - 2.25) < 1e-9 and .21 < a < .27:
        return 'curtainSlot'
    if abs(a - .5) < 1e-9 and 2.27 < b < 2.48:
        return 'curtainIntake'
    if .2 - 1e-9 <= a <= .5 + 1e-9 and 2.25 - 1e-9 <= b <= 2.5 + 1e-9:
        return 'curtainBody'
    if abs(a) < 1e-9 and b > 2.2:
        return 'facade'
    if abs(b - 2.2) < 1e-9 and 0 < a < .2:
        return 'doorHead'
    if abs(a - .2) < 1e-9 and b > 2.2:
        return 'wallInside'
    raise ValueError((a, b))


def main(out):
    out = Path(out)
    cells, cc, sizes = {}, [], []
    for j in range(ny):
        for i in range(nx):
            a, b = (x[i] + x[i + 1]) / 2, (y[j] + y[j + 1]) / 2
            if is_air(a, b):
                cells[i, j] = len(cc)
                cc.append([a, b, .5])
                sizes.append([x[i + 1] - x[i], y[j + 1] - y[j], 1])
    cc, sizes = np.array(cc), np.array(sizes)

    patch = {p: [] for p in PATCHES}
    internal, zones = [], {z: [] for z in ['door', 'doorInner', 'doorOuter']}
    points, pmap = [], {}

    def point(i, j, k):
        if (i, j, k) not in pmap:
            pmap[i, j, k] = len(points)
            points.append([x[i], y[j], k])
        return pmap[i, j, k]

    for (i, j), c in cells.items():
        faces = [('left', (i - 1, j), [(i, j, 0), (i, j, 1), (i, j + 1, 1), (i, j + 1, 0)], x[i], cc[c, 1]),
                 ('right', (i + 1, j), [(i + 1, j, 0), (i + 1, j + 1, 0), (i + 1, j + 1, 1), (i + 1, j, 1)], x[i + 1], cc[c, 1]),
                 ('bottom', (i, j - 1), [(i, j, 0), (i + 1, j, 0), (i + 1, j, 1), (i, j, 1)], cc[c, 0], y[j]),
                 ('top', (i, j + 1), [(i, j + 1, 0), (i, j + 1, 1), (i + 1, j + 1, 1), (i + 1, j + 1, 0)], cc[c, 0], y[j + 1])]
        for side, nb, pts, a, b in faces:
            if nb in cells:
                n = cells[nb]
                if c > n:
                    continue
                fi = len(internal)
                internal.append(([point(*q) for q in pts], c, n))
                if side == 'right' and b < 2.2:
                    for name, v in [('door', .1), ('doorInner', .2), ('doorOuter', 0)]:
                        if abs(a - v) < 1e-9:
                            zones[name].append(fi)
            else:
                patch[classify(a, b)].append(([point(*q) for q in pts], c))
        for pts in ([(i, j, 0), (i, j + 1, 0), (i + 1, j + 1, 0), (i + 1, j, 0)],
                    [(i, j, 1), (i + 1, j, 1), (i + 1, j + 1, 1), (i, j + 1, 1)]):
            patch['frontAndBack'].append(([point(*q) for q in pts], c))

    poly = out / 'constant/polyMesh'
    poly.mkdir(parents=True, exist_ok=True)

    def write_list(name, cls, lines):
        (poly / name).write_text(header(name, cls) + str(len(lines)) + '\n(\n' + '\n'.join(lines) + '\n)\n')

    write_list('points', 'vectorField', ['(' + ' '.join(map(str, p)) + ')' for p in points])
    allfaces = internal + sum([patch[p] for p in PATCHES], [])
    write_list('faces', 'faceList', ['4(' + ' '.join(map(str, f[0])) + ')' for f in allfaces])
    write_list('owner', 'labelList', [str(f[1]) for f in allfaces])
    write_list('neighbour', 'labelList', [str(f[2]) for f in internal])

    bound = header('boundary', 'polyBoundaryMesh') + str(len(patch)) + '\n(\n'
    start, areas, pts = len(internal), {}, np.array(points)
    for p, fs in patch.items():
        typ = 'empty' if p == 'frontAndBack' else ('patch' if p in ['street', 'sky'] else 'wall')
        bound += f'{p}\n{{type {typ}; nFaces {len(fs)}; startFace {start};}}\n'
        start += len(fs)
        areas[p] = float(sum(np.linalg.norm(np.cross(pts[f[0][1]] - pts[f[0][0]], pts[f[0][3]] - pts[f[0][0]])) for f in fs))
    (poly / 'boundary').write_text(bound + ')\n')

    fz = header('faceZones', 'regIOobject') + '3\n(\n'
    for name, fs in zones.items():
        fz += (name + '\n{ type faceZone; faceLabels List<label>\n' + str(len(fs)) + '\n(\n' + '\n'.join(map(str, fs))
               + '\n);\nflipMap List<bool>\n' + str(len(fs)) + '\n(\n' + '\n'.join(['true'] * len(fs)) + '\n);}\n')
    (poly / 'faceZones').write_text(fz + ')\n')

    # Boundary face centres, in patch order, for the hydrostatic pressure on each face.
    face_centres = {p: np.array([np.mean([points[q] for q in f[0]], axis=0) for f in fs]) for p, fs in patch.items()}
    np.savez(out / 'cells.npz', x=x, y=y, cc=cc, sizes=sizes, **{'face_' + p: v for p, v in face_centres.items()})

    dx, dy = np.diff(x), np.diff(y)
    report = dict(
        cells=len(cc), nx=nx, ny=ny, patch_areas_m2=areas, faceZone_areas_m2={n: 2.2 for n in zones},
        min_dx_m=float(dx.min()), min_dy_m=float(dy.min()), max_dx_m=float(dx.max()), max_dy_m=float(dy.max()),
        max_adjacent_x_ratio=float(np.max(np.maximum(dx[1:] / dx[:-1], dx[:-1] / dx[1:]))),
        max_adjacent_y_ratio=float(np.max(np.maximum(dy[1:] / dy[:-1], dy[:-1] / dy[1:]))),
        slot_dx_m=dx[(x[:-1] >= .21 - 1e-8) & (x[1:] <= .27 + 1e-8)].tolist(),
        doorway_dx_max_m=float(dx[(x[:-1] >= 0) & (x[1:] <= .2 + 1e-8)].max()),
        doorway_dy_max_m=float(dy[y[1:] <= 2.2 + 1e-8].max()))
    (out / 'mesh.json').write_text(json.dumps(report, indent=2))
    (out / 'system').mkdir(exist_ok=True)
    (out / 'system/controlDict').write_text(header('controlDict') + 'application buoyantPimpleFoam; startFrom startTime; '
                                            'startTime 0; endTime 60; deltaT .001; writeControl timeStep; writeInterval 1;')
    for f in ['fvSchemes', 'fvSolution']:
        (out / 'system' / f).write_text((Path(__file__).resolve().parents[1] / 'template/system' / f).read_text())
    print(f'{len(cc)} cells, {nx} x {ny} lines')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'runs/mesh')
