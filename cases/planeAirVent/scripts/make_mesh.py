#!/usr/bin/env python3
"""Build the cabin mesh in <case>: python3 scripts/make_mesh.py <case>

The cloud's scripts/build_mesh.py, audit_mesh.py and finalise_mesh.py in one, with only their paths
changed and their ledger entries and renders left out:
  blockMesh       a 2.40 x 2.20 x 3.52 m box of 4 cm cells (60 x 55 x 88)
  topoSet         every cell whose centre is outside the solids of scripts/geometry.json
  subsetMesh      keeps those cells, so the solids are holes with stair-free box faces
  snappyHexMesh   castellated refinement only (template/mesh/system/snappyHexMeshDict, as written on
                  the cloud): 2 cm in the jets, slots, exhausts and the cough's path, 1 cm at the mouth
  the patch split every boundary face is given to a rectangle of geometry.json's patches (nozzles,
                  slots, exhausts, mouth, the two periodic ends), to the people or seats, the floor,
                  or the rest of the shell (walls); each rectangle's area is checked to 1%
  createPatch     the two ends become a translational cyclic pair
  checkMesh       must report Mesh OK
It also writes <case>/mesh_arrays.npz (cell centres and volumes), which scripts/make_case.py reads.
"""
from pathlib import Path
import json, re, shutil, subprocess, sys
import numpy as np

here = Path(__file__).resolve().parents[1]
c = Path(sys.argv[1]).resolve()
g = json.loads((here / 'scripts/geometry.json').read_text())
(c / 'system').mkdir(parents=True, exist_ok=True)


def h(n, cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {n}; }}\n'


def v(a):
    return '(' + ' '.join(map(str, a)) + ')'


def run(cmd, log=None):
    with open(c / ('log.' + (log or cmd[0])), 'w') as f:
        p = subprocess.run(cmd, cwd=c, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode:
        sys.exit(f'{cmd[0]} failed, see {c}/log.{log or cmd[0]}')


# --- build_mesh.py ---------------------------------------------------------------------------------
for n in ['fvSchemes', 'fvSolution', 'snappyHexMeshDict']:
    shutil.copy(here / 'template/mesh/system' / n, c / 'system' / n)
(c / 'system/controlDict').write_text(h('controlDict') + 'application buoyantPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT 0.001; writeControl timeStep; writeInterval 1; writeFormat ascii; writeCompression off; runTimeModifiable false;\n')
verts = [(0, 0, -1.76), (2.4, 0, -1.76), (2.4, 2.2, -1.76), (0, 2.2, -1.76), (0, 0, 1.76), (2.4, 0, 1.76), (2.4, 2.2, 1.76), (0, 2.2, 1.76)]
(c / 'system/blockMeshDict').write_text(h('blockMeshDict') + 'scale 1;\nvertices\n(\n' + '\n'.join(map(v, verts)) + '\n);\nblocks\n(\nhex (0 1 2 3 4 5 6 7) (60 55 88) simpleGrading (1 1 1)\n);\nedges ();\nboundary\n(\nshell { type wall; faces ((0 4 7 3)(1 2 6 5)(0 1 5 4)(3 7 6 2)(0 3 2 1)(4 5 6 7)); }\n);\nmergePatchPairs ();\n')
run(['blockMesh'])
actions = 'actions\n(\n{ name air; type cellSet; action new; source boxToCell; box (0 0 -1.76) (2.4 2.2 1.76); }\n'
for s in g['solids']:
    b = s['box']
    actions += '{ name air; type cellSet; action delete; source boxToCell; box ' + v([b[0], b[2], b[4]]) + ' ' + v([b[1], b[3], b[5]]) + '; }\n'
(c / 'system/topoSetDict').write_text(h('topoSetDict') + actions + ');\n')
run(['topoSet'])
run(['subsetMesh', 'air', '-overwrite'])
run(['snappyHexMesh', '-overwrite'])

# --- audit_mesh.py: the patch split ----------------------------------------------------------------
m = c / 'constant/polyMesh'


def content(n):
    s = (m / n).read_text()
    return s[s.index('}', s.index('FoamFile')) + 1:]


def body(n):
    s = content(n)
    return s[s.index('(') + 1:s.rindex(')')]


pts = np.array([np.fromstring(x, sep=' ') for x in re.findall(r'\(([^()]+)\)', body('points'))])
faces = [np.fromstring(x, sep=' ', dtype=int) for x in re.findall(r'\d+\(([^()]*)\)', body('faces'))]
owner = np.fromstring(body('owner'), sep=' ', dtype=int)
nei = np.fromstring(body('neighbour'), sep=' ', dtype=int)
ni = len(nei)
fc = np.array([pts[f].mean(axis=0) for f in faces])
sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(axis=0) / 2 for f in faces])
areas = np.linalg.norm(sf, axis=1)
rect = {}
for n, b in g['patches'].items():
    if isinstance(b, list) and isinstance(b[0], dict):
        for p in b:
            rect[p['name']] = p['patch']
    else:
        rect['mouth' if n.startswith('mouth') else n] = b
patches = {n: [] for n in list(rect) + ['people', 'seats', 'floor', 'shell']}
for i in range(ni, len(faces)):
    p = fc[i]
    n = 'shell'
    if abs(p[1]) < 1e-7:
        n = 'floor'
    for s in g['solids']:
        if s['group'] not in ['person', 'seat']:
            continue
        b = np.array(s['box']).reshape(3, 2)
        lo = b[:, 0]
        hi = b[:, 1]
        if np.all(p >= lo - 1e-7) and np.all(p <= hi + 1e-7) and np.any((abs(p - lo) < 1e-7) | (abs(p - hi) < 1e-7)):
            n = 'people' if s['group'] == 'person' else 'seats'
            break
    for k, b in rect.items():
        b = np.array(b).reshape(3, 2)
        lo = b[:, 0]
        hi = b[:, 1]
        if np.all(p >= lo - 1e-7) and np.all(p <= hi + 1e-7):
            n = k
            break
    patches[n].append(i)
idx = list(range(ni))
out = []
start = ni
report = {}
for n, ids in patches.items():
    aa = areas[ids]
    report[n] = {'faces': len(ids), 'area_m2': float(aa.sum())}
    if n in rect:
        widths = np.diff(np.array(rect[n]).reshape(3, 2), axis=1).ravel()
        expected = float(np.prod(widths[widths > 0]))
        report[n]['rectangle_area_m2'] = expected
        if n.startswith('cyclic'):
            report[n]['rectangle_area_m2'] = None
        else:
            report[n]['relative_error'] = float(aa.sum() / expected - 1)
            assert abs(aa.sum() / expected - 1) < .01, (n, report[n])
    typ = 'patch' if n in rect else 'wall'
    outname = ('endAftInput' if n == 'cyclicAft' else 'endForeInput') if n.startswith('cyclic') else n
    out.append(f'{outname}\n{{\n type {typ};\n nFaces {len(ids)};\n startFace {start};\n}}\n')
    idx += ids
    start += len(ids)
assert len(idx) == len(set(idx)) == len(faces)
(m / 'faces').write_text(h('faces', 'faceList') + str(len(idx)) + '\n(\n' + '\n'.join(str(len(faces[i])) + '(' + ' '.join(map(str, faces[i])) + ')' for i in idx) + '\n)\n')
(m / 'owner').write_text(h('owner', 'labelList') + str(len(idx)) + '\n(\n' + '\n'.join(map(str, owner[idx])) + '\n)\n')
(m / 'boundary').write_text(h('boundary', 'polyBoundaryMesh') + str(len(out)) + '\n(\n' + ''.join(out) + ')\n')
fc = fc[idx]
sf = sf[idx]
owner = owner[idx]
N = max(owner.max(), nei.max()) + 1
lo = np.full((N, 3), np.inf)
hi = -lo.copy()
for j, i in enumerate(idx):
    a = pts[faces[i]].min(axis=0)
    b = pts[faces[i]].max(axis=0)
    o = owner[j]
    lo[o] = np.minimum(lo[o], a)
    hi[o] = np.maximum(hi[o], b)
    if j < ni:
        o = nei[j]
        lo[o] = np.minimum(lo[o], a)
        hi[o] = np.maximum(hi[o], b)
C = (lo + hi) / 2
size = hi - lo
V = np.zeros(N)
vv = (sf * fc).sum(axis=1) / 3
np.add.at(V, owner, vv)
np.add.at(V, nei, -vv[:ni])
assert np.allclose(V, np.prod(size, axis=1))
np.savez_compressed(c / 'mesh_arrays.npz', C=C, V=V, size=size)
(c / 'mesh_patches.json').write_text(json.dumps(report, indent=2))
print('cells', N, 'air volume', V.sum(), 'm3')

# --- finalise_mesh.py ------------------------------------------------------------------------------
(c / 'system/createPatchDict').write_text(h('createPatchDict') + 'pointSync false; patches (\n' + ''.join('{ name ' + n + '; patchInfo { type cyclic; neighbourPatch ' + other + '; transform translational; separationVector ' + vec + '; } constructFrom patches; patches (' + ('endAftInput' if n == 'cyclicAft' else 'endForeInput') + '); }\n' for n, other, vec in [('cyclicAft', 'cyclicFore', '(2.4 0 0)'), ('cyclicFore', 'cyclicAft', '(-2.4 0 0)')]) + ');\n')
run(['createPatch', '-overwrite'])
run(['checkMesh'])
if 'Mesh OK' not in (c / 'log.checkMesh').read_text():
    sys.exit(f'checkMesh did not pass, see {c}/log.checkMesh')
print('mesh done:', c)
