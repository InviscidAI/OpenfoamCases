"""Write the blockMesh case for the one mesh both runs share.

    python3 scripts/make_mesh.py <meshDir>

writes <meshDir>/system/blockMeshDict, a minimal controlDict, and fvSchemes and fvSolution
copied from radiatorUnderWindow's template (checkMesh reads them). Allrun then runs
blockMesh and checkMesh there, and scripts/make_case.py copies the polyMesh into each run.

The section is radiatorUnderWindow's: x from the window wall (0) to the inner wall (4.0 m),
y from the floor (0) to the ceiling (2.4 m), one cell thick in z (0 to 1 m). It is cut into
graded blocks so that both supply slots have exact edges and four cells across:
- floorSlot, x = 0.1479-0.1521 m in the floor (4.2 mm, centre 0.15 m from the window wall);
- ceilingSlot, x = 3.5464-3.5536 m in the ceiling (7.2 mm, centre 0.45 m from the inner wall);
- undercut, the inner wall below y = 0.025 m (the door's 1 in undercut, ten cells);
- glass, the window wall from y = 0.90 to 2.10 m; outerWall, the rest of the window wall.
Both runs carry both slots; make_case.py makes the one not in use a wall.

Each segment below is (start, end, first cell, last cell) in metres; its cell count is the
length over the mean of the geometric grading, rounded up. 405 x 251 = 101,655 cells.
This is the setup agent's own generator (its build_mesh.py), unchanged but for this note,
the output directory and the omitted design report.
"""
import math
import shutil
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
TEMPLATE = CASE.parent / "radiatorUnderWindow" / "template"

xspec=[(0,.1,.005,.005),(.1,.1479,.005,.00105),(.1479,.1521,.00105,.00105),(.1521,.2,.00105,.005),(.2,1,.005,.020),(1,3,.020,.020),(3,3.48,.020,.005),(3.48,3.5464,.005,.0018),(3.5464,3.5536,.0018,.0018),(3.5536,3.62,.0018,.005),(3.62,3.8,.005,.005),(3.8,4,.005,.005)]
yspec=[(0,.025,.0025,.0025),(.025,.1,.0025,.010),(.1,.9,.010,.010),(.9,2.1,.012,.012),(2.1,2.4,.012,.003)]


def specs(seq):
    out = []
    for a, b, d0, d1 in seq:
        R = d1 / d0
        avg = d0 if abs(R - 1) < 1e-9 else (d1 - d0) / math.log(R)
        n = math.ceil(round((b - a) / avg, 10))
        out.append((a, b, n, R))
    return out


def main(meshdir):
    xs, ys = specs(xspec), specs(yspec)
    X = [s[0] for s in xs] + [4]
    Y = [s[0] for s in ys] + [2.4]
    nx, ny = len(X), len(Y)

    def v(i, j, k):
        return k * nx * ny + j * nx + i

    verts = ['(%.12g %.12g %d)' % (x, y, z) for z in (0, 1) for y in Y for x in X]
    blocks = []
    patches = {k: [] for k in ['floor', 'ceiling', 'innerWall', 'outerWall', 'glass', 'floorSlot', 'ceilingSlot', 'undercut', 'frontAndBack']}

    def face(k, ids):
        patches[k].append('(' + ' '.join(map(str, ids)) + ')')

    for j, (_, _, nj, rj) in enumerate(ys):
        for i, (_, _, ni, ri) in enumerate(xs):
            a, b, c, d, e, f, g, h = [v(i, j, 0), v(i + 1, j, 0), v(i + 1, j + 1, 0), v(i, j + 1, 0), v(i, j, 1), v(i + 1, j, 1), v(i + 1, j + 1, 1), v(i, j + 1, 1)]
            blocks.append(f'hex ({a} {b} {c} {d} {e} {f} {g} {h}) ({ni} {nj} 1) simpleGrading ({ri:.12g} {rj:.12g} 1)')
            if j == 0:
                face('floorSlot' if abs(X[i] - .1479) < 1e-8 else 'floor', [a, b, f, e])
            if j == len(ys) - 1:
                face('ceilingSlot' if abs(X[i] - 3.5464) < 1e-8 else 'ceiling', [d, h, g, c])
            if i == 0:
                face('glass' if abs(Y[j] - .9) < 1e-8 else 'outerWall', [a, e, h, d])
            if i == len(xs) - 1:
                face('undercut' if j == 0 else 'innerWall', [b, c, g, f])
            face('frontAndBack', [a, d, c, b])
            face('frontAndBack', [e, f, g, h])

    header = 'FoamFile {version 2.0; format ascii; class dictionary; object blockMeshDict;}\n'
    bound = '\n'.join(k + '\n{\ntype ' + ('empty' if k == 'frontAndBack' else 'patch' if k in ('floorSlot', 'ceilingSlot', 'undercut') else 'wall') + ';\nfaces\n(\n' + '\n'.join(faces) + '\n);\n}' for k, faces in patches.items())
    p = Path(meshdir) / 'system'
    p.mkdir(parents=True, exist_ok=True)
    (p / 'blockMeshDict').write_text(header + 'scale 1;\nvertices\n(\n' + '\n'.join(verts) + '\n);\nblocks\n(\n' + '\n'.join(blocks) + '\n);\nedges ();\nboundary\n(\n' + bound + '\n);\nmergePatchPairs ();\n')
    (p / 'controlDict').write_text(header.replace('blockMeshDict', 'controlDict') + 'application blockMesh; startFrom startTime; startTime 0; stopAt endTime; endTime 300; deltaT .001; writeControl timeStep; writeInterval 1;')
    for n in ['fvSchemes', 'fvSolution']:
        shutil.copy(TEMPLATE / 'system' / n, p / n)
    print(f"{meshdir}: {sum(s[2] for s in xs)} x {sum(s[2] for s in ys)} = "
          f"{sum(s[2] for s in xs) * sum(s[2] for s in ys)} cells")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
