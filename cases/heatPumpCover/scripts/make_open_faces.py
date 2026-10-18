#!/usr/bin/env python3
"""Write template/system/topoSetDict.openFaces and template/system/openFaces.inc: face zones, oriented
outward, on the grid faces of the open faces of the space behind the unit (x 0-0.250, y 0.300-1.040,
z 0-0.442), each with surfaceFieldValue sum and sumMag of phi (out = (sumMag + sum)/2,
in = (sumMag - sum)/2). The cover's front and side stay on the resultPlanes cut planes: under the
cover the grid has no face at x = 0.78, so a face zone there came out empty.

    python3 scripts/make_open_faces.py
"""
import os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = {
 'behindTop':     ((-1, 0.670, -1), (0.255, 1.20, 0.50), (0, 1, 0)),
 'behindBottom':  ((-1, 0.20, -1), (0.255, 0.670, 0.50), (0, -1, 0)),
 'behindEnd':     ((-1, 0.20, 0.30), (0.255, 1.20, 0.50), (0, 0, 1)),  # z > 0.3 leaves out the symmetry plane
}
f = lambda v: '(%s)' % ' '.join(f'{c:g}' for c in v)
# The refinement level changes across the space behind the unit, so no single grid plane lies near its faces
# everywhere (a box at y 1.035-1.042 caught 0.0145 of 0.1105 m2). Instead: the cells whose centres lie in the
# space, and the faces between them and the cells outside, oriented out of the space and split by the
# direction of their normals (top +-y above mid-height, bottom +-y below it, end +-z).
acts = ['  { name behind; type cellSet; action new; source boxToCell; box (0 0.300 -1) (0.250 1.040 0.442); }']
for n, (lo, hi, nv) in Z.items():
    acts += [f'  {{ name {n}A; type faceSet; action new; source cellToFace; set behind; option outside; }}',
             f'  {{ name {n}B; type faceSet; action new; source faceToFace; set {n}A; }}',
             f'  {{ name {n}A; type faceSet; action subset; source normalToFace; normal {f(nv)}; cos 0.05; }}',
             f'  {{ name {n}B; type faceSet; action subset; source normalToFace; normal {f(tuple(-c for c in nv))}; cos 0.05; }}',
             f'  {{ name {n}A; type faceSet; action add; source faceToFace; set {n}B; }}',
             f'  {{ name {n}A; type faceSet; action subset; source boxToFace; box {f(lo)} {f(hi)}; }}',
             f'  {{ name {n}; type faceZoneSet; action new; source setsToFaceZone; faceSet {n}A; cellSet behind; }}']
open(f'{R}/template/system/topoSetDict.openFaces', 'w').write(
    'FoamFile { format ascii; class dictionary; object topoSetDict; }\n// Written by scripts/make_open_faces.py\nactions\n(\n'
    + '\n'.join(acts) + '\n);\n')
fo = ['// Exact gross flows (17 Oct 2026, written by scripts/make_open_faces.py): phi oriented outward,',
      '// out = (sumMag + sum)/2, in = (sumMag - sum)/2.']
for n in Z:
    for op in ('sum', 'sumMag'):
        fo.append(f'{n}_{op} {{ type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name {n}; '
                  f'operation {op}; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }}')
open(f'{R}/template/system/openFaces.inc', 'w').write('\n'.join(fo) + '\n')
print('wrote', len(Z), 'face zones')
