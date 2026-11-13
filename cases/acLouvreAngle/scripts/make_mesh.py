#!/usr/bin/env python3
"""Write the shared mesh case of the air conditioner's room, before blockMesh and snappyHexMesh.

    python3 scripts/make_mesh.py runs/mesh

Copies template/mesh/system/ (controlDict, blockMeshDict, snappyHexMeshDict: the solved mesh's,
byte for byte) and template/system/'s fvSchemes and fvSolution, and writes the unit and the sofa
as closed STL surfaces into constant/triSurface/ from config/case.json's boxes. Each surface is
the outer skin of the union of its boxes, two triangles to a face of the boxes' common grid, so it
lies on the background mesh's faces and the castellated mesh cuts it out exactly.

Allrun then runs blockMesh, snappyHexMesh -overwrite and scripts/unit_patches.py in it.
"""
import itertools
import json
import shutil
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]


def stl_union(path, name, boxes):
    axes = [sorted(set(b[i] for b in boxes) | set(b[i + 3] for b in boxes)) for i in range(3)]
    occupied = set()
    for ids in itertools.product(*[range(len(a) - 1) for a in axes]):
        p = [(axes[i][j] + axes[i][j + 1]) / 2 for i, j in enumerate(ids)]
        if any(all(b[i] < p[i] < b[i + 3] for i in range(3)) for b in boxes):
            occupied.add(ids)
    out = ["solid " + name]
    for ids in sorted(occupied):
        for d in range(3):
            other = [i for i in range(3) if i != d]
            for sign in (-1, 1):
                nb = list(ids)
                nb[d] += sign
                if tuple(nb) in occupied:
                    continue
                q = []
                for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    p = [axes[i][ids[i]] for i in range(3)]
                    p[d] = axes[d][ids[d] + (sign == 1)]
                    p[other[0]] = axes[other[0]][ids[other[0]] + u]
                    p[other[1]] = axes[other[1]][ids[other[1]] + v]
                    q.append(p)
                if (d == 1) == (sign == 1):
                    q = q[::-1]
                for t in ((0, 1, 2), (0, 2, 3)):
                    out += ["facet normal 0 0 0", "outer loop"]
                    out += ["vertex " + " ".join(map(str, q[j])) for j in t]
                    out += ["endloop", "endfacet"]
    out += ["endsolid " + name]
    path.write_text("\n".join(out) + "\n")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_mesh.py runs/mesh")
    case = Path(sys.argv[1])
    if case.exists():
        raise SystemExit(f"{case} exists; ./Allclean or move it away first")
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    shutil.copytree(CASE / "template" / "mesh" / "system", case / "system")
    for f in ("fvSchemes", "fvSolution"):
        shutil.copy(CASE / "template" / "system" / f, case / "system" / f)
    tri = case / "constant" / "triSurface"
    tri.mkdir(parents=True)
    stl_union(tri / "unit.stl", "unit", [tuple(b) for b in cfg["unit"]])
    stl_union(tri / "sofa.stl", "sofa", [tuple(b) for b in cfg["sofa"]])
    print(case)


if __name__ == "__main__":
    main()
