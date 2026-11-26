#!/usr/bin/env python3
"""Build the half living room's mesh, shared by both runs.

    python3 scripts/make_mesh.py runs/mesh

One blockMesh box of graded lines, structured hexahedra with no snapping and no split faces, the
lines at the cell sizes below so that every edge of the sofa, the register, the window and the
return lies on one:

    x  2.5 cm over 0-0.3, 5 cm over 0.3-0.6, 10 cm over 0.6-4.3, 5 cm over 4.3-4.5 m  (59 cells)
    y  5 cm over 0-0.4, 10 cm over 0.4-2.2, 5 cm over 2.2-2.4 m                    (30 cells)
    z  2.5 cm over 0-0.2, 5 cm over 0.2-0.4, 10 cm over 0.4-2.4 m                  (32 cells)

x runs from the window wall's inner face to the inner wall, y up from the floor and z from the
symmetry plane through the register to the side wall. topoSet and subsetMesh then take out the
sofa's cells (the seat x 3.0-3.9, y 0-0.4, z 0-1.0 and its back x 3.7-3.9, y 0.4-0.8, z 0-1.0),
their faces becoming the sofa patch, and createPatch moves the register (floor, x 0.10-0.20,
z 0-0.10), the window (x = 0, y 0.9-2.1, z 0-1.2) and the return (x = 4.5, y 0.10-0.30,
z 0-0.30) out of the floor, the window wall and the inner wall: 55,200 cells.

Writes the mesh case in the given folder, runs the utilities there (logs log.<utility>), and
writes cells.npz with the cell centres and volumes, cell by cell in the mesh's order, and the
return's face centres, face by face, which scripts/make_case.py needs for the hydrostatic start
and the return's pressure. The centres are those of the structured lines, which the solved mesh
has to float32 rounding.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

X = [(0.3, 12), (0.3, 6), (3.7, 37), (0.2, 4)]
Y = [(0.4, 8), (1.8, 18), (0.2, 4)]
Z = [(0.2, 8), (0.2, 4), (2.0, 20)]
SOFA = [(3.0, 3.9, 0.0, 0.4, 0.0, 1.0), (3.7, 3.9, 0.4, 0.8, 0.0, 1.0)]
NEW_PATCHES = [  # name, type, the patch it comes out of, its box
    ("register", "patch", "floor", (0.10, 0.20, 0.0, 0.0, 0.0, 0.10)),
    ("window", "wall", "outerWall", (0.0, 0.0, 0.9, 2.1, 0.0, 1.2)),
    ("return", "patch", "innerWall", (4.5, 4.5, 0.10, 0.30, 0.0, 0.30)),
]
EPS = 1e-4


def hdr(obj, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def lines(sections):
    edges = [0.0]
    for length, n in sections:
        start = edges[-1]
        edges += [start + length * (i + 1) / n for i in range(n)]
    return np.array(edges)


def grading(sections):
    total = sum(length for length, _ in sections)
    return "(" + " ".join(f"({length / total:.12g} {n} 1)" for length, n in sections) + ")"


def box(b, pad=EPS):
    return f"({b[0] - pad:g} {b[2] - pad:g} {b[4] - pad:g}) ({b[1] + pad:g} {b[3] + pad:g} {b[5] + pad:g})"


def write_dicts(case):
    (case / "system").mkdir(parents=True, exist_ok=True)
    (case / "constant").mkdir(exist_ok=True)
    nx, ny, nz = (sum(n for _, n in s) for s in (X, Y, Z))
    (case / "system/controlDict").write_text(hdr("controlDict") + "application blockMesh;\nstartFrom startTime; startTime 0; stopAt endTime; endTime 0; deltaT 1;\nwriteControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 12; timeFormat general; timePrecision 6;\n")
    (case / "system/fvSchemes").write_text(hdr("fvSchemes") + "ddtSchemes { default steadyState; }\ngradSchemes { default Gauss linear; }\ndivSchemes { default none; }\nlaplacianSchemes { default Gauss linear corrected; }\ninterpolationSchemes { default linear; }\nsnGradSchemes { default corrected; }\n")
    (case / "system/fvSolution").write_text(hdr("fvSolution"))
    (case / "system/blockMeshDict").write_text(hdr("blockMeshDict") + f"""scale 1;
vertices ((0 0 0) (4.5 0 0) (4.5 2.4 0) (0 2.4 0) (0 0 2.4) (4.5 0 2.4) (4.5 2.4 2.4) (0 2.4 2.4));
blocks (hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading ({grading(X)} {grading(Y)} {grading(Z)}));
edges ();
boundary
(
    outerWall {{ type wall; faces ((0 4 7 3)); }}
    innerWall {{ type wall; faces ((1 2 6 5)); }}
    floor     {{ type wall; faces ((0 1 5 4)); }}
    ceiling   {{ type wall; faces ((3 7 6 2)); }}
    sideWall  {{ type wall; faces ((4 5 6 7)); }}
    symmetry  {{ type symmetryPlane; faces ((0 3 2 1)); }}
    sofa      {{ type wall; faces (); }}
);
mergePatchPairs ();
""")
    cells = "\n".join(f"    {{ name air; type cellSet; action delete; source boxToCell; boxes ({box(b, -EPS)}); }}" for b in SOFA)
    (case / "system/topoSetDict.cells").write_text(hdr("topoSetDict") + f"""actions
(
    {{ name air; type cellSet; action new; source boxToCell; boxes ((-1 -1 -1) (10 10 10)); }}
{cells}
);
""")
    faces = "\n".join(
        f"    {{ name {n}Faces; type faceSet; action new; source patchToFace; patch {parent}; }}\n"
        f"    {{ name {n}Faces; type faceSet; action subset; source boxToFace; boxes ({box(b)}); }}"
        for n, _, parent, b in NEW_PATCHES)
    (case / "system/topoSetDict.faces").write_text(hdr("topoSetDict") + "actions\n(\n" + faces + "\n);\n")
    patches = "\n".join(f"    {{ name {n}; patchInfo {{ type {t}; }} constructFrom set; set {n}Faces; }}" for n, t, _, _ in NEW_PATCHES)
    (case / "system/createPatchDict").write_text(hdr("createPatchDict") + "pointSync false;\npatches\n(\n" + patches + "\n);\n")


def run(case, cmd, log):
    with open(case / log, "w") as f:
        subprocess.run(cmd, shell=True, cwd=case, stdout=f, stderr=subprocess.STDOUT, check=True)


def centres():
    ex, ey, ez = lines(X), lines(Y), lines(Z)
    cx, cy, cz = ((e[:-1] + e[1:]) / 2 for e in (ex, ey, ez))
    dx, dy, dz = np.diff(ex), np.diff(ey), np.diff(ez)
    Z3, Y3, X3 = np.meshgrid(cz, cy, cx, indexing="ij")  # x fastest, then y, then z: blockMesh's order
    V = np.einsum("k,j,i->kji", dz, dy, dx).ravel()
    C = np.stack([X3.ravel(), Y3.ravel(), Z3.ravel()], axis=1)
    keep = np.ones(len(C), bool)
    for b in SOFA:
        keep &= ~((C[:, 0] > b[0]) & (C[:, 0] < b[1]) & (C[:, 1] > b[2]) & (C[:, 1] < b[3]) & (C[:, 2] > b[4]) & (C[:, 2] < b[5]))
    return C[keep], V[keep]


def return_faces(case):
    """The return's face centres in the patch's own order, read from the mesh."""
    poly = case / "constant/polyMesh"
    boundary = (poly / "boundary").read_text()
    block = boundary[boundary.index("    return\n"):]
    n = int(block.split("nFaces")[1].split(";")[0])
    start = int(block.split("startFace")[1].split(";")[0])
    def body(name):
        text = (poly / name).read_text()
        text = text[text.index("FoamFile"):]
        text = text[text.index("}") + 1:]
        return text
    pts_text = body("points")
    count = int(pts_text.split("(", 1)[0].split()[-1])
    pts = np.array([tuple(map(float, l.strip("()").split())) for l in pts_text.split("(", 1)[1].strip().splitlines()[:count]])
    fc_text = body("faces")
    nf = int(fc_text.split("(", 1)[0].split()[-1])
    rows = fc_text.split("(", 1)[1].strip().splitlines()[:nf]
    out = []
    for row in rows[start:start + n]:
        ids = [int(i) for i in row.split("(")[1].rstrip(")").split()]
        out.append(pts[ids].mean(axis=0))
    return np.array(out)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    case = Path(sys.argv[1])
    write_dicts(case)
    run(case, "blockMesh", "log.blockMesh")
    run(case, "topoSet -dict system/topoSetDict.cells", "log.topoSet.cells")
    run(case, "subsetMesh air -patch sofa -overwrite", "log.subsetMesh")
    run(case, "topoSet -dict system/topoSetDict.faces", "log.topoSet.faces")
    run(case, "createPatch -overwrite", "log.createPatch")
    C, V = centres()
    ret = return_faces(case)
    n_cells = int((case / "constant/polyMesh/owner").read_text().split("nCells:")[1].split()[0])
    if n_cells != len(C):
        sys.exit(f"the mesh has {n_cells} cells, the lines give {len(C)}")
    np.savez(case / "cells.npz", C=C, V=V, returnFaces=ret)
    print(f"{len(C)} cells, air volume {V.sum():.6f} m3, return faces {len(ret)}")


if __name__ == "__main__":
    main()
