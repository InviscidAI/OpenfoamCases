#!/usr/bin/env python3
"""Sort the half kitchen's boundary into its patches and write the oven mouth's face zones.

    python3 scripts/kitchen_patches.py open|shut runs/mesh-<run>

snappyHexMesh leaves the blockMesh faces (symmetry, walls, floor, ceiling) and the cut-out solids
(solids) as patches that do not follow the kitchen. This sorts every boundary face by its centre
into

    symmetry    x = 0, the plane through the range's centre
    walls       the kitchen's three walls, x = 1.84, z = 0 (the range's wall) and z = 3.04 m
    ceiling     y = 2.40 m
    floor       y = 0
    cabinets    every face of the solids not listed below: the base and wall cabinets, the
                hood, the backguard and, in open, the range's casing beside the cavity
    rangeFront  the range's front, z = 0.64 m, x < 0.38, y < 0.92 m (in open, round the mouth)
    cooktop     the range's top, y = 0.92 m, x < 0.38, z 0.08-0.64 m
    liner       (open) the cavity's five faces, x < 0.30, y 0.24-0.72, z 0.10-0.64 m
    door        (open) the door lying flat, x < 0.38, y 0.20-0.24, z 0.64-1.24 m

and rewrites constant/polyMesh/faces, owner and boundary in that order (points and neighbour are
unchanged). In open it writes the face zones the monitor sums the flow over: the oven's mouth,
the cavity's open face at z = 0.64 m (x < 0.30, y 0.24-0.72 m), and its halves above and below
0.48 m (mouthUpper, mouthLower), oriented +z, out of the oven. It checks the range's patches' and
the mouth's areas to 1% (config/case.json, "expected_areas"), and writes cells.npz (each cell's
centre, the middle of its bounding box, and its volume, used for the starting fields) and
patches.json beside the mesh. The polyMesh must be ASCII, as template/mesh/system/controlDict
writes it.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("open", "shut"):
        raise SystemExit("usage: kitchen_patches.py open|shut runs/mesh-<run>")
    run, mesh = sys.argv[1], Path(sys.argv[2])
    m = mesh / "constant" / "polyMesh"
    cfg = json.loads((CASE / "config" / "case.json").read_text())

    def content(n):
        s = (m / n).read_text()
        return s[s.index("}", s.index("FoamFile")) + 1:]

    def body(n):
        s = content(n)
        return s[s.index("(") + 1:s.rindex(")")]

    def header(n, cls):
        return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {n}; }}\n"

    if "rangeFront" in content("boundary"):
        raise SystemExit(f"{m} already has the kitchen's patches")
    pts = np.array([np.fromstring(x, sep=" ") for x in re.findall(r"\(([^()]+)\)", body("points"))])
    faces = [np.fromstring(x, sep=" ", dtype=int) for x in re.findall(r"\d+\(([^()]*)\)", body("faces"))]
    owner = np.fromstring(body("owner"), sep=" ", dtype=int)
    nei = np.fromstring(body("neighbour"), sep=" ", dtype=int)
    ni = len(nei)
    fc = np.array([pts[f].mean(axis=0) for f in faces])
    sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(axis=0) / 2 for f in faces])
    areas = np.linalg.norm(sf, axis=1)

    Lx, Ly, Lz = cfg["kitchen"]
    names = ["symmetry", "walls", "ceiling", "floor", "cabinets", "rangeFront", "cooktop"]
    if run == "open":
        names += ["liner", "door"]
    patches = {n: [] for n in names}
    for i in range(ni, len(faces)):
        x, y, z = fc[i]
        if abs(x) < 1e-7:
            n = "symmetry"
        elif abs(y - Ly) < 1e-7:
            n = "ceiling"
        elif abs(y) < 1e-7:
            n = "floor"
        elif abs(x - Lx) < 1e-7 or abs(z) < 1e-7 or abs(z - Lz) < 1e-7:
            n = "walls"
        elif run == "open" and x < .300001 and .239999 < y < .720001 and .099999 < z < .640001:
            n = "liner"
        elif run == "open" and x < .380001 and .199999 < y < .240001 and .639999 < z < 1.240001:
            n = "door"
        elif abs(z - .64) < 1e-7 and x < .38 and y < .92:
            n = "rangeFront"
        elif abs(y - .92) < 1e-7 and x < .38 and .08 < z < .64:
            n = "cooktop"
        else:
            n = "cabinets"
        patches[n].append(i)

    report = {}
    idx = list(range(ni))
    out = []
    start = ni
    for n, ids in patches.items():
        aa = areas[ids]
        report[n] = {"faces": len(ids), "area": float(aa.sum()),
                     "face_edge_sizes_m": sorted(set(np.round(np.sqrt(aa), 6).tolist()))}
        out.append(f"{n}\n{{\n type " + ("symmetry" if n == "symmetry" else "wall")
                   + f";\n nFaces {len(ids)};\n startFace {start};\n}}\n")
        idx += ids
        start += len(ids)
    assert len(idx) == len(set(idx)) == len(faces)
    (m / "faces").write_text(header("faces", "faceList") + str(len(idx)) + "\n(\n"
                             + "\n".join(str(len(faces[i])) + "(" + " ".join(map(str, faces[i])) + ")" for i in idx) + "\n)\n")
    (m / "owner").write_text(header("owner", "labelList") + str(len(idx)) + "\n(\n" + "\n".join(map(str, owner[idx])) + "\n)\n")
    (m / "boundary").write_text(header("boundary", "polyBoundaryMesh") + str(len(out)) + "\n(\n" + "".join(out) + ")\n")
    fc, sf, owner, areas = fc[idx], sf[idx], owner[idx], areas[idx]

    # Each cell's bounding box from its faces: the castellated cells are axis-aligned cubes, so
    # the box's middle is the cell centre and its volume the cell's (checked by the divergence
    # theorem below).
    N = max(owner.max(), nei.max()) + 1
    lo = np.full((N, 3), np.inf)
    hi = -lo.copy()
    for j, i in enumerate(idx):
        a, b = pts[faces[i]].min(axis=0), pts[faces[i]].max(axis=0)
        for o in ((owner[j], nei[j]) if j < ni else (owner[j],)):
            lo[o] = np.minimum(lo[o], a)
            hi[o] = np.maximum(hi[o], b)
    C = (lo + hi) / 2
    size = hi - lo
    V = np.zeros(N)
    v = (sf * fc).sum(axis=1) / 3
    np.add.at(V, owner, v)
    np.add.at(V, nei, -v[:ni])
    assert np.allclose(V, np.prod(size, axis=1))

    zones = {}
    if run == "open":
        mouth = np.where((np.abs(fc[:, 2] - .64) < 1e-7) & (fc[:, 0] < .30) & (fc[:, 1] > .24) & (fc[:, 1] < .72)
                         & (np.abs(sf[:, 2]) > .99 * areas))[0]
        zones = {"mouth": mouth, "mouthUpper": mouth[fc[mouth, 1] > .48], "mouthLower": mouth[fc[mouth, 1] < .48]}
    s = header("faceZones", "regIOobject") + str(len(zones)) + "\n(\n"
    for n, ids in zones.items():
        report[n] = {"faces": len(ids), "area": float(areas[ids].sum()), "orientation": "+z"}
        s += (n + "\n{\ntype faceZone;\nfaceLabels List<label>\n" + str(len(ids)) + "\n(\n" + "\n".join(map(str, ids))
              + "\n);\nflipMap List<bool>\n" + str(len(ids)) + "\n(\n" + "\n".join("1" if sf[i, 2] < 0 else "0" for i in ids) + "\n);\n}\n")
    (m / "faceZones").write_text(s + ")\n")

    for n, a in cfg["expected_areas"][run].items():
        assert abs(report[n]["area"] / a - 1) < 0.01, (n, report[n], a)
    report["summary"] = {"cells": int(N), "volume": float(V.sum())}
    np.savez_compressed(mesh / "cells.npz", C=C, V=V)
    (mesh / "patches.json").write_text(json.dumps(report, indent=2))
    for n, r in report.items():
        if "area" in r:
            print(f"{n:12s} {r['faces']:6d} faces {r['area']:10.6f} m2")
    print("cells", N, "volume", V.sum())


if __name__ == "__main__":
    main()
