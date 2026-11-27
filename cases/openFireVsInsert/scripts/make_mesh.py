#!/usr/bin/env python3
"""Build one house's mesh: the solids as a union of boxes (STL), blockMesh, a castellated
snappyHexMesh (no snapping, no layers), then snappy's single wall patch split by face centre into
the named patches the case's boundary conditions use, and the doorway face zones.

    python3 scripts/make_mesh.py open|insert RUNDIR

Writes RUNDIR/mesh/ (the meshing case, with its logs) and RUNDIR/constant/polyMesh/, plus
RUNDIR/mesh.npz (cell centres, volumes and face centres in the final face order, read by
make_case.py) and RUNDIR/mesh.json (every patch's faces and area against its target, the rooms'
volumes). It stops if any patch's area is more than 1% off its target. This is the solved runs'
mesh: build84.py and audit84.py of the cloud study, merged, with the same boxes, the same
dictionaries and the same face classification.

x runs from the fireplace wall (x = 0) to the back door's wall (x = 10.8), y up, z across; metres.
"""
from pathlib import Path
import json, re, shutil, subprocess, sys
import numpy as np

HERE = Path(__file__).resolve().parents[1]
GAPS = ['gapFrontDoor', 'gapBackDoor', 'gapWinLF', 'gapWinLB', 'gapWinS', 'gapWinK']


def hdr(n, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {n};}}\n'


def run(cmd, c):
    with (c / ('log.' + cmd[0])).open('w') as f:
        p = subprocess.run(cmd, cwd=c, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode:
        sys.exit(f'{cmd[0]} failed: {c}/log.{cmd[0]}')


def union(boxes, path):
    """The boundary of a union of axis-aligned boxes, as an ASCII STL."""
    axes = [sorted(set(b[d] for b in boxes for d in [i, i + 3])) for i in range(3)]
    mid = [(np.array(a[1:]) + a[:-1]) / 2 for a in axes]
    occ = np.zeros(tuple(len(a) for a in mid), bool)
    for b in boxes:
        occ |= ((mid[0][:, None, None] > b[0]) & (mid[0][:, None, None] < b[3]) & (mid[1][None, :, None] > b[1])
                & (mid[1][None, :, None] < b[4]) & (mid[2][None, None, :] > b[2]) & (mid[2][None, None, :] < b[5]))
    with path.open('w') as f:
        f.write('solid boxes\n')
        for idx in zip(*np.where(occ)):
            for d in range(3):
                for side in [-1, 1]:
                    nb = list(idx); nb[d] += side
                    if 0 <= nb[d] < occ.shape[d] and occ[tuple(nb)]:
                        continue
                    uv = [j for j in range(3) if j != d]; v = []
                    for a, b in [(0, 0), (1, 0), (1, 1), (0, 1)]:
                        p = [0., 0., 0.]; p[d] = axes[d][idx[d] + (side == 1)]
                        p[uv[0]] = axes[uv[0]][idx[uv[0]] + a]; p[uv[1]] = axes[uv[1]][idx[uv[1]] + b]
                        v.append(np.array(p))
                    if np.cross(v[1] - v[0], v[2] - v[0])[d] * side < 0:
                        v = v[::-1]
                    for tri in [(0, 1, 2), (0, 2, 3)]:
                        n = np.zeros(3); n[d] = side
                        f.write('facet normal ' + ' '.join(map(str, n)) + '\nouter loop\n')
                        for j in tri:
                            f.write('vertex ' + ' '.join(map(str, v[j])) + '\n')
                        f.write('endloop\nendfacet\n')
        f.write('endsolid boxes\n')


def solids(house):
    """The solid boxes (x0 y0 z0 x1 y1 z1): the fireplace wall, the inner walls split at the
    doorways, the sofa, the table and the counter. They reach 0.1 m past the outer walls so no STL
    face lies on the background mesh's boundary."""
    if house == 'insert':   # the opening closed flush with the wall: the insert's face is x = 0
        boxes = [(-.5, -.1, -.1, 0, 2.5, 6.1)]
    else:                   # the open recess, x -0.4 to 0, z 2.55-3.45, 0.70 m high
        boxes = [(-.5, -.1, -.1, 0, 2.5, 2.55), (-.5, -.1, 3.45, 0, 2.5, 6.1), (-.5, .7, 2.55, 0, 2.5, 3.45)]
    boxes += [(5.2, -.1, -.1, 5.3, 2.5, .6), (5.2, -.1, 1.5, 5.3, 2.5, 2.6), (5.2, -.1, 3.5, 5.3, 2.5, 6.1),  # living | hall, kitchen
              (5.2, 2, .6, 5.3, 2.5, 1.5), (5.2, 2, 2.6, 5.3, 2.5, 3.5),                                  # lintels, 2.0 m
              (5.3, -.1, 2, 10.9, 2.5, 2.1),                                                              # hall, study | kitchen
              (7.7, -.1, -.1, 7.8, 2.5, .6), (7.7, -.1, 1.5, 7.8, 2.5, 2), (7.7, 2, .6, 7.8, 2.5, 1.5),   # hall | study
              (2.6, -.1, 2, 3.4, .4, 4), (3.2, .4, 2, 3.4, .8, 4),                                        # sofa: seat and back
              (7.6, .7, 3.8, 9, .8, 4.7),                                                                 # table top
              (6.8, -.1, 5.4, 9.6, .9, 6.1)]                                                              # kitchen counter
    return boxes


def read_list(m, n):
    s = (m / n).read_text(); s = s[s.index('}', s.index('FoamFile')) + 1:]
    return s[s.index('(') + 1:s.rindex(')')]


def split(house, m):
    """snappy's one 'solids' patch (and the background's six) into the named patches, by face centre."""
    pts = np.array([np.fromstring(s, sep=' ') for s in re.findall(r'\(([^()]+)\)', read_list(m, 'points'))])
    faces = [np.fromstring(s, sep=' ', dtype=int) for s in re.findall(r'\d+\(([^()]*)\)', read_list(m, 'faces'))]
    owner = np.fromstring(read_list(m, 'owner'), sep=' ', dtype=int)
    nei = np.fromstring(read_list(m, 'neighbour'), sep=' ', dtype=int); ni = len(nei)
    fc = np.array([pts[f].mean(0) for f in faces])
    sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(0) / 2 for f in faces]); areas = np.linalg.norm(sf, axis=1)
    names = ['hearth', 'floor', 'ceiling', 'walls', 'sofa', 'table', 'counter', 'windows'] + GAPS
    names += ['firePanel', 'throat', 'recess'] if house == 'open' else ['glass', 'jacketOut', 'jacketIn', 'combustionAir', 'insertFrame']
    patches = {n: [] for n in names}
    eps = 1e-7
    for i in range(ni, len(faces)):
        x, y, z = fc[i]; p = 'walls'
        if 2.6 - eps < x < 3.4 + eps and 2 - eps < z < 4 + eps and y < .8 + eps: p = 'sofa'
        elif 7.6 - eps < x < 9 + eps and 3.8 - eps < z < 4.7 + eps and .7 - eps < y < .8 + eps: p = 'table'
        elif 6.8 - eps < x < 9.6 + eps and 5.4 - eps < z < 6 + eps and y < .9 + eps: p = 'counter'
        elif abs(y) < eps and x > 0: p = 'hearth' if x < .6 and 2.2 < z < 3.8 else 'floor'
        elif abs(y - 2.4) < eps: p = 'ceiling'
        elif house == 'open' and x < -eps:
            p = 'recess'                                                    # the firebrick recess
            if abs(x + .4) < eps and 2.65 < z < 3.35 and .1 < y < .5: p = 'firePanel'   # 0.7 x 0.4 m on its back wall
            elif abs(y - .7) < eps and x < -.25: p = 'throat'               # 0.9 x 0.15 m in its top, to the chimney
        elif house == 'insert' and abs(x) < eps and 2.55 < z < 3.45 and y < .7:
            p = 'insertFrame'
            if 2.65 < z < 3.35 and .15 < y < .55: p = 'glass'               # 0.7 x 0.4 m glass door
            elif .6 < y < .7: p = 'jacketOut'                               # warm air out, 0.9 x 0.1 m
            elif y < .1: p = 'combustionAir' if z < 2.75 else 'jacketIn'    # 0.2 and 0.7 x 0.1 m
        if abs(z) < eps:                                                    # the front wall
            if .9 < y < 2.1 and (1.6 < x < 3.6 or 8.6 < x < 10): p = 'windows'
            if y < .025 and 6 < x < 6.9: p = 'gapFrontDoor'
            if 2.1 < y < 2.125:
                if 2.5 < x < 2.7: p = 'gapWinLF'
                if 9.2 < x < 9.4: p = 'gapWinS'
        if abs(z - 6) < eps:                                                # the back wall
            if .9 < y < 2.1 and (1.6 < x < 3.6 or 7.4 < x < 8.9): p = 'windows'
            if 2.1 < y < 2.125:
                if 2.5 < x < 2.7: p = 'gapWinLB'
                if 8 < x < 8.2: p = 'gapWinK'
        if abs(x - 10.8) < eps and y < .025 and 2.6 < z < 3.5: p = 'gapBackDoor'
        patches[p].append(i)
    idx = list(range(ni)); out = []; start = ni; report = {}
    for n, ids in patches.items():
        aa = areas[ids]; report[n] = dict(faces=len(ids), area_m2=float(aa.sum()), face_scales_m=sorted(set(np.round(np.sqrt(aa), 6))))
        typ = 'patch' if n in GAPS + ['throat', 'jacketOut', 'jacketIn', 'combustionAir'] else 'wall'
        out.append(f'{n}\n{{type {typ}; nFaces {len(ids)}; startFace {start};}}\n'); idx += ids; start += len(ids)
    assert len(idx) == len(set(idx)) == len(faces)
    (m / 'faces').write_text(hdr('faces', 'faceList') + str(len(idx)) + '\n(\n' + '\n'.join(str(len(faces[i])) + '(' + ' '.join(map(str, faces[i])) + ')' for i in idx) + '\n)\n')
    (m / 'owner').write_text(hdr('owner', 'labelList') + str(len(idx)) + '\n(\n' + '\n'.join(map(str, owner[idx])) + '\n)\n')
    (m / 'boundary').write_text(hdr('boundary', 'polyBoundaryMesh') + str(len(out)) + '\n(\n' + ''.join(out) + ')\n')
    fc = fc[idx]; sf = sf[idx]; owner = owner[idx]; areas = areas[idx]; N = max(owner.max(), nei.max()) + 1
    lo = np.full((N, 3), np.inf); hi = -lo.copy()
    for j, i in enumerate(idx):
        a = pts[faces[i]].min(0); b = pts[faces[i]].max(0); o = owner[j]; lo[o] = np.minimum(lo[o], a); hi[o] = np.maximum(hi[o], b)
        if j < ni: o = nei[j]; lo[o] = np.minimum(lo[o], a); hi[o] = np.maximum(hi[o], b)
    C = (lo + hi) / 2; size = hi - lo; V = np.zeros(N); v = (sf * fc).sum(1) / 3
    np.add.at(V, owner, v); np.add.at(V, nei, -v[:ni]); assert np.allclose(V, np.prod(size, axis=1))   # every cell a box
    zones = {}
    for name, pos, a, b, h in [('kitchenDoor', 5.3, 2.6, 3.5, 2), ('hallDoor', 5.3, .6, 1.5, 2), ('studyDoor', 7.8, .6, 1.5, 2)] + ([('opening', 0, 2.55, 3.45, .7)] if house == 'open' else []):
        zones[name] = np.where((np.abs(fc[:, 0] - pos) < eps) & (fc[:, 2] > a) & (fc[:, 2] < b) & (fc[:, 1] < h) & (np.abs(sf[:, 0]) > .99 * areas))[0]
    s = hdr('faceZones', 'regIOobject') + str(len(zones)) + '\n(\n'
    for n, ids in zones.items():
        s += n + '\n{type faceZone; faceLabels List<label>\n' + str(len(ids)) + '\n(\n' + '\n'.join(map(str, ids)) + '\n);\nflipMap List<bool>\n' + str(len(ids)) + '\n(\n' + '\n'.join('1' if sf[i, 0] < 0 else '0' for i in ids) + '\n);\n}\n'
    (m / 'faceZones').write_text(s + ')\n')
    target = {'floor': 59.48, 'ceiling': 63.45, 'walls': 123.175, 'sofa': 5.6, 'table': 2.98, 'counter': 5.28,
              'windows': 8.28, 'hearth': .96, **dict(zip(GAPS, [.0225, .0225, .005, .005, .005, .005])),
              **({'firePanel': .28, 'throat': .135, 'recess': 1.495} if house == 'open' else
                 {'glass': .28, 'jacketOut': .09, 'jacketIn': .07, 'combustionAir': .02, 'insertFrame': .17})}
    failures = []
    for n, a in target.items():
        report[n]['target_area_m2'] = a; report[n]['error_pct'] = 100 * (report[n]['area_m2'] / a - 1)
        if abs(report[n]['error_pct']) > 1: failures.append(n)
    rooms = {'living': (0, 5.2, 0, 6), 'kitchen': (5.3, 10.8, 2.1, 6), 'hall': (5.3, 7.7, 0, 2), 'study': (7.8, 10.8, 0, 2)}
    vol = {n: float(V[(C[:, 0] > a) & (C[:, 0] < b) & (C[:, 2] > d) & (C[:, 2] < e)].sum()) for n, (a, b, d, e) in rooms.items()}
    report['summary'] = dict(cells=int(N), volume_m3=float(V.sum()), rooms_m3=vol, failed_patches=failures,
                             zone_areas_m2={n: float(areas[ids].sum()) for n, ids in zones.items()})
    return report, dict(C=C, V=V, size=size, fc=fc, Sf=sf, owner=owner, neighbour=nei), failures


def main(house, rundir):
    r = Path(rundir); c = r / 'mesh'
    shutil.rmtree(c, ignore_errors=True); (c / 'constant/triSurface').mkdir(parents=True)
    shutil.copytree(HERE / 'template/mesh/system', c / 'system')
    union(solids(house), c / 'constant/triSurface/solids.stl')
    run(['blockMesh'], c)                    # 112 x 24 x 60 cells of 0.1 m over x -0.4..10.8, y 0..2.4, z 0..6
    run(['snappyHexMesh', '-overwrite'], c)  # castellated only: 0.05 m at the floor and fire, 0.025 m at the gaps
    m = c / 'constant/polyMesh'
    report, arrays, failures = split(house, m)
    (r / 'mesh.json').write_text(json.dumps(report, indent=2)); np.savez_compressed(r / 'mesh.npz', **arrays)
    run(['checkMesh', '-allTopology', '-allGeometry'], c)
    if failures:
        sys.exit(f'patch areas off target: {failures}')
    shutil.rmtree(r / 'constant/polyMesh', ignore_errors=True); (r / 'constant').mkdir(parents=True, exist_ok=True)
    shutil.copytree(m, r / 'constant/polyMesh')
    print(f'{house}: {report["summary"]["cells"]} cells, {report["summary"]["volume_m3"]:.3f} m3 of air')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('open', 'insert'):
        sys.exit('usage: make_mesh.py open|insert RUNDIR')
    main(*sys.argv[1:])
