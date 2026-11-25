#!/usr/bin/env python3
"""Write one hall's mesh directly as an OpenFOAM polyMesh.

    python3 scripts/make_mesh.py open|contained runs/<run>

The hall is 15.6 m across the rows (x), 16.2 m along them (y) and 3.2 m high (z), on a
rectilinear grid of about 0.2 m. The cells inside the 120 racks and inside the cooling units'
cabinets along both end walls are left out, so the racks and the cabinets are holes in the mesh;
everything else is air. On the holes' faces:

  supply_south, supply_north   the cooling units' grilles, the end-wall cabinets' inner faces at
                               y 0.9 and 15.3 m, z 0.1-1.9 m, the hall's full width
  return_00 .. return_02       the ceiling over each hot aisle, x 2.4-3.6 m (+4.8 m a row pair),
                               y 2.1-14.1 m
  <row>_r<rack>_s<server>_intake / _exhaust
                               each server's front (cold aisle) and back (hot aisle) face on its
                               rack, 1,200 pairs: six rows L00, R00, L01, R01, L02, R02 of twenty
                               racks (r01-r20, 0.6 m wide along y from y 2.1 m) of ten servers
                               (s01-s10, 0.2 m high from z 0.1 m)
  walls                        everything else: floor, ceiling, walls, the racks' tops, ends and
                               the 0.1 m below and above their servers

In contained, three more sets of walls close each hot aisle without cells: zero-thickness baffles
(both sides of an internal face become wall faces) from the rack tops (z 2.2 m) to the ceiling
along both rows (panel_L0k, panel_R0k) and doors across both ends of the aisle, floor to ceiling
(end_0k_south, end_0k_north). The cold side, the hall outside the hot aisles, then has no
fixed-pressure boundary: the supplies push in what the intakes take out.

The racks are solid from the floor (z = 0) to 2.2 m: nothing passes under them. The grid keeps
the lines at z 0.02 and 0.04 m that the mesh it was cut from had for a 4 cm gap under the racks;
with the racks sealed they only split the air's cells next to the floor.

Writes runs/<run>/constant/polyMesh/{points,faces,owner,neighbour,boundary}, runs/<run>/mesh.npz
(the cell centres, the cell volumes, the faces and the points, for make_case.py) and
runs/<run>/mesh_report.json (cells, points, air volume, every patch's faces and area, and the
air regions with the boundaries each touches). Stops if an air region has no inflow or no
outflow.
"""
import collections
import json
import pathlib
import sys

import numpy as np

P = 3                       # row pairs (hot aisles)
L = 1.2 + 4.8 * P           # 15.6 m across the rows
SEP = 0.002                 # the source grid's server separators, 2 mm; their lines are dropped again in grid()


def grid():
    # The source grid of the study (a 0.2 m grid plus lines at every server's edges), less the
    # lines 1 mm either side of each server separator, which the solved mesh (b) dropped.
    x = np.unique(np.round(np.r_[np.arange(round(L / .2) + 1) * .2,
                                 [4.8 * k + a for k in range(P) for a in [2.4, 2.42, 3.58, 3.6]]], 8))
    y = np.unique(np.round(np.r_[np.linspace(0, .9, 6), np.linspace(.9, 2.1, 7), 2.1 + np.arange(61) * .2,
                                 np.linspace(14.1, 15.3, 7), np.linspace(15.3, 16.2, 6),
                                 [2.1 + .6 * j + d for j in range(1, 20) for d in [-SEP / 2, SEP / 2]], 2.08, 14.12], 8))
    z = np.unique(np.round(np.r_[0, .02, .04, .07, .1, .1 + np.arange(21) * .1,
                                 [.1 + .2 * i + d for i in range(1, 10) for d in [-SEP / 2, SEP / 2]],
                                 2.2, np.linspace(2.2, 3.2, 6), 1.9, 1.95], 8))

    def remove(a, vals):
        return a[~np.any(np.isclose(a[:, None], np.array(vals)[None, :], atol=1e-8, rtol=0), axis=1)]
    x = remove(x, [4.8 * k + a for k in range(P) for a in (2.42, 3.58)])
    y = remove(y, [2.1 + .6 * j + s for j in range(1, 20) for s in (-.001, .001)] + [2.08, 14.12])
    z = remove(z, [.1 + .2 * i + s for i in range(1, 10) for s in (-.001, .001)])
    return x, y, z


def header(obj, cls):
    return 'FoamFile\n{\n version 2.0;\n format ascii;\n class ' + cls + ';\n object ' + obj + ';\n}\n'


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ('open', 'contained'):
        raise SystemExit('usage: make_mesh.py open|contained runs/<run>')
    mode, root = sys.argv[1], pathlib.Path(sys.argv[2])
    root.mkdir(parents=True, exist_ok=True)
    x, y, z = grid()
    xc, yc, zc = [(a[:-1] + a[1:]) / 2 for a in (x, y, z)]
    X, Y, Z = np.meshgrid(xc, yc, zc, indexing='ij')
    # the cooling units' cabinets along both end walls, 0.9 m deep and 1.95 m high
    solid = ((Y < .9) | (Y > 15.3)) & (Z < 1.95)
    # the racks, 1.2 m deep, y 2.1-14.1 m, solid from the floor to 2.2 m
    for k in range(P):
        for a in (4.8 * k + 1.2, 4.8 * k + 3.6):
            solid |= (X > a) & (X < a + 1.2) & (Y > 2.1) & (Y < 14.1) & (Z < 2.2)
    air = ~solid
    ijk = np.array(np.where(air)).T
    nc = len(ijk)
    ids = np.full(air.shape, -1, dtype=np.int32)
    ids[air] = np.arange(nc)
    I, J, K = ijk.T
    nx, ny, nz = map(len, (x, y, z))

    def node(i, j, k):
        return (i * ny + j) * nz + k
    conn = np.stack([node(I, J, K), node(I + 1, J, K), node(I + 1, J + 1, K), node(I, J + 1, K),
                     node(I, J, K + 1), node(I + 1, J, K + 1), node(I + 1, J + 1, K + 1), node(I, J + 1, K + 1)], 1)
    used = np.unique(conn)
    remap = np.full(nx * ny * nz, -1, np.int32)
    remap[used] = np.arange(len(used))
    conn = remap[conn]
    points = np.stack([x[used // (ny * nz)], y[(used // nz) % ny], z[used % nz]], 1)

    patches = collections.defaultdict(list)
    areas = collections.defaultdict(float)
    intern, owners, neighbours = [], [], []
    patchowners = collections.defaultdict(list)
    # the six faces of a hex: axis, outward sign, its vertices in OpenFOAM's order
    spec = [(0, -1, [0, 4, 7, 3]), (0, 1, [1, 2, 6, 5]), (1, -1, [0, 1, 5, 4]),
            (1, 1, [3, 7, 6, 2]), (2, -1, [0, 3, 2, 1]), (2, 1, [4, 5, 6, 7])]
    for axis, sign, fids in spec:
        nei = ijk.copy()
        nei[:, axis] += sign
        valid = (nei[:, axis] >= 0) & (nei[:, axis] < air.shape[axis])
        nb = np.full(nc, -1, np.int32)
        nb[valid] = ids[tuple(nei[valid].T)]
        centers = np.stack([xc[I], yc[J], zc[K]], 1)
        centers[:, axis] = [x, y, z][axis][ijk[:, axis] + (sign > 0)]
        Cx, Cy, Cz = centers.T
        # contained: zero-thickness baffles, each internal face split into two wall faces
        baff = np.zeros(nc, bool)
        names = np.full(nc, 'walls', dtype=object)
        if mode == 'contained':
            for k in range(P):
                lo = 4.8 * k + 2.4
                hi = lo + 1.2
                for side, pos in [('L', lo), ('R', hi)]:
                    m = (axis == 0) & np.isclose(Cx, pos) & (Cy > 2.1) & (Cy < 14.1) & (Cz > 2.2)
                    baff |= m
                    names[m] = f'panel_{side}{k:02}'
                for end, pos in [('south', 2.1), ('north', 14.1)]:
                    m = (axis == 1) & np.isclose(Cy, pos) & (Cx > lo) & (Cx < hi)
                    baff |= m
                    names[m] = f'end_{k:02}_{end}'
        internal = (nb >= 0) & ~baff
        if sign > 0:
            q = np.where(internal)[0]
            intern.append(conn[q][:, fids])
            owners.append(q)
            neighbours.append(nb[q])
        q = np.where((nb < 0) | baff)[0]
        c = centers[q]
        tags = names[q].copy()
        if axis == 1:
            m = (np.isclose(c[:, 1], .9) | np.isclose(c[:, 1], 15.3)) & (c[:, 2] > .1) & (c[:, 2] < 1.9)
            tags[m] = np.where(c[m, 1] < 8, 'supply_south', 'supply_north')
        if axis == 2 and sign == 1:
            for k in range(P):
                m = np.isclose(c[:, 2], 3.2) & (c[:, 0] > 4.8 * k + 2.4) & (c[:, 0] < 4.8 * k + 3.6) & (c[:, 1] > 2.1) & (c[:, 1] < 14.1)
                tags[m] = f'return_{k:02}'
        if axis == 0:
            for k in range(P):
                for side, a in [('L', 4.8 * k + 1.2), ('R', 4.8 * k + 3.6)]:
                    for kind, pos in [('intake', a if side == 'L' else a + 1.2), ('exhaust', a + 1.2 if side == 'L' else a)]:
                        m = np.isclose(c[:, 0], pos) & (c[:, 1] > 2.1) & (c[:, 1] < 14.1) & (c[:, 2] > .1) & (c[:, 2] < 2.1) & (nb[q] < 0)
                        for h in np.where(m)[0]:
                            j = min(20, int(np.floor((c[h, 1] - 2.1) / .6 + 1e-7)) + 1)
                            i = min(10, int(np.floor((c[h, 2] - .1) / .2 + 1e-7)) + 1)
                            tags[h] = f'{side}{k:02}_r{j:02}_s{i:02}_{kind}'
        ds = [np.diff(x)[I[q]], np.diff(y)[J[q]], np.diff(z)[K[q]]]
        ar = ds[(axis + 1) % 3] * ds[(axis + 2) % 3]
        for name in np.unique(tags):
            m = tags == name
            patches[name].append(conn[q[m]][:, fids])
            patchowners[name].append(q[m])
            areas[name] += float(ar[m].sum())

    fi = np.concatenate(intern)
    ow = np.concatenate(owners)
    ne = np.concatenate(neighbours)
    order = np.lexsort((ne, ow))       # internal faces by owner, then neighbour
    fi, ow, ne = fi[order], ow[order], ne[order]
    pnames = ['walls'] + sorted(n for n in patches if n != 'walls')
    start = len(fi)
    boundary = []
    faces = [fi]
    own = [ow]
    for name in pnames:
        f = np.concatenate(patches[name])
        o = np.concatenate(patchowners[name])
        nf = len(f)
        boundary.append(dict(name=name, nFaces=nf, startFace=start,
                             type='wall' if name == 'walls' or name.startswith(('panel_', 'end_')) else 'patch',
                             area_m2=areas[name]))
        start += nf
        faces.append(f)
        own.append(o)
    faces = np.concatenate(faces)
    own = np.concatenate(own)

    mesh = root / 'constant/polyMesh'
    mesh.mkdir(parents=True, exist_ok=True)
    (mesh / 'points').write_text(header('points', 'vectorField') + str(len(points)) + '\n(\n'
                                 + '\n'.join('(%s %s %s)' % tuple(p) for p in points) + '\n)\n')
    (mesh / 'faces').write_text(header('faces', 'faceList') + str(len(faces)) + '\n(\n'
                                + '\n'.join('4(%d %d %d %d)' % tuple(f) for f in faces) + '\n)\n')
    for name, v in [('owner', own), ('neighbour', ne)]:
        (mesh / name).write_text(header(name, 'labelList') + str(len(v)) + '\n(\n' + '\n'.join(map(str, v)) + '\n)\n')
    (mesh / 'boundary').write_text(header('boundary', 'polyBoundaryMesh') + str(len(boundary)) + '\n(\n'
                                   + ''.join(b['name'] + '\n{\n type ' + b['type'] + ';\n nFaces ' + str(b['nFaces'])
                                             + ';\n startFace ' + str(b['startFace']) + ';\n}\n' for b in boundary) + '\n)\n')

    # air regions, connected through internal faces (the baffles split them)
    parent = np.arange(nc)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in zip(ow, ne):
        a = find(a)
        b = find(b)
        if a != b:
            parent[b] = a
    reg = np.array([find(i) for i in range(nc)])
    regions = []
    for r in np.unique(reg):
        touches = [n for n in pnames if np.any(reg[np.concatenate(patchowners[n])] == r)]
        regions.append(dict(cells=int((reg == r).sum()),
                            inflows=[n for n in touches if n.startswith('supply') or n.endswith('exhaust')],
                            outflows=[n for n in touches if n.startswith('return') or n.endswith('intake')],
                            boundaries=touches))
    cent = np.stack([xc[I], yc[J], zc[K]], 1)
    vols = np.diff(x)[I] * np.diff(y)[J] * np.diff(z)[K]
    np.savez_compressed(root / 'mesh.npz', centers=cent, volumes=vols, faces=faces, points=points, nInternalFaces=len(fi))
    report = dict(mode=mode, cells=nc, points=len(points), air_volume_m3=float(vols.sum()),
                  boundaries=boundary, regions=regions)
    (root / 'mesh_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(mode=mode, cells=nc, points=len(points), air_volume_m3=report['air_volume_m3'],
                          patches=len(boundary), air_regions=len(regions)), indent=1), flush=True)
    if any(not r['inflows'] or not r['outflows'] for r in regions):
        raise SystemExit('STOP: an air region without an inflow or an outflow')


if __name__ == '__main__':
    main()
