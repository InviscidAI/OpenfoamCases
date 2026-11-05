"""The excluder's cells: python3 scripts/block_gap.py <mesh> <run>.

<mesh> is the blockMesh case (runs/mesh), whose ascii polyMesh is read; <run> is the blocked run,
into whose constant/polyMesh/sets the cellSet is written. The cell labels are the same in both,
since createPatch, which Allrun runs first on the run, only adds an empty patch (and clears sets/).

The excluder is a circle 95 mm across (radius 47.5 mm) resting on the floor against the leaf's
room face, centre (3.9525, 0.0475). Every cell whose bounding box meets the circle is removed, not
only those whose centre is inside it, so that the staircase touches the floor and the leaf and
seals the undercut. Cells left with fewer than two air neighbours by that staircase (one-cell tips
with no resolved passage) are removed too. Writes the cells as the cellSet excluderCells; Allrun
then takes them out (topoSet with system/blockSetDict, subsetMesh kept -patch excluder) and the
solid's faces become the wall patch excluder that createPatch made.

This is the study's selection (958 cells at N = 10) with its reader changed: the study read the
mesh through pyvista; this reads the ascii polyMesh that blockMesh writes, with numpy only.
"""
import re
import sys
from pathlib import Path

import numpy as np

XC, YC, R = 3.9525, 0.0475, 0.0475


def body(path):
    """The list in an ascii OpenFOAM file, after its header, as text."""
    s = Path(path).read_text()
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'//[^\n]*', '', s)
    s = s[s.index('}', s.index('FoamFile')) + 1:]
    m = re.search(r'^\s*(\d+)\s*\(', s, flags=re.M)
    return int(m[1]), s[m.end():s.rindex(')')]


def main(meshCase, runCase):
    mesh = Path(meshCase) / 'constant/polyMesh'
    for f in ('points', 'faces', 'owner', 'neighbour'):
        if not re.search(r'format\s+ascii;', (mesh / f).read_text()[:2000]):
            raise SystemExit(f'{mesh/f} is not ascii; give the mesh as blockMesh wrote it')
    n, s = body(mesh / 'points')
    pts = np.array(re.findall(r'\(([^()]*)\)', s), dtype=object)
    pts = np.array([list(map(float, p.split())) for p in pts])
    assert len(pts) == n
    n, s = body(mesh / 'faces')
    faces = [list(map(int, f.split())) for f in re.findall(r'\d+\(([^()]*)\)', s)]
    assert len(faces) == n
    n, s = body(mesh / 'owner')
    owner = np.array(s.split(), dtype=int)
    n, s = body(mesh / 'neighbour')
    neigh = np.array(s.split(), dtype=int)
    nCells = owner.max() + 1
    nInternal = len(neigh)

    # each cell's points, from its faces
    cellPts = [set() for _ in range(nCells)]
    for f, verts in enumerate(faces):
        cellPts[owner[f]].update(verts)
        if f < nInternal:
            cellPts[neigh[f]].update(verts)
    nbrs = [[] for _ in range(nCells)]
    for f in range(nInternal):
        nbrs[owner[f]].append(neigh[f])
        nbrs[neigh[f]].append(owner[f])

    # candidates by the mean of each cell's eight vertices, as the study's reader gave them
    candidate = []
    for i in range(nCells):
        p = pts[sorted(cellPts[i])]
        c = p.mean(axis=0)
        if abs(c[0] - XC) < .07 and c[1] < .12:
            candidate.append(i)
    remove = set()
    for i in candidate:
        p = pts[sorted(cellPts[i])]
        lo, hi = p.min(axis=0), p.max(axis=0)
        dx = max(lo[0] - XC, 0, XC - hi[0])
        dy = max(lo[1] - YC, 0, YC - hi[1])
        if dx * dx + dy * dy <= R ** 2 + 1e-15:
            remove.add(i)
    changed = True
    while changed:
        changed = False
        for i in candidate:
            if i not in remove and sum(j not in remove for j in nbrs[i]) < 2:
                remove.add(i)
                changed = True
    remove = sorted(remove)
    sets = Path(runCase) / 'constant/polyMesh/sets'
    sets.mkdir(exist_ok=True)
    (sets / 'excluderCells').write_text(
        'FoamFile {version 2.0; format ascii; class cellSet; object excluderCells;}\n'
        + str(len(remove)) + '\n(\n' + '\n'.join(map(str, remove)) + '\n)\n')
    print('excluder: removing', len(remove), 'cells')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
