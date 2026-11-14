#!/usr/bin/env python3
"""Sort the house's boundary into its patches and write the fan and doorway zones.

    python3 scripts/house_patches.py runs/mesh

snappyHexMesh leaves the blockMesh faces (symmetry, sideWall, floor, ceiling, unitSideWall,
farWall) and the cut-out solids (solids) as patches that do not follow the rooms. This sorts
every boundary face by its centre (config/case.json, "patches") into

    symmetry        z = 0, the plane through the doorway, the fan and the stove
    stove           the stove's faces, x 0.60-1.12, y 0.12-0.84, z < 0.28 m (2000 W)
    flue            the flue's faces, x 0.80-0.96, y > 0.84, z < 0.08 m (500 W)
    stoveRoomWalls  every other face with x <= 4.00 m: the stove room's walls, floor, ceiling
                    and its face of the partition (held at 24 C)
    coldRoomWalls   every face with x >= 4.08 m (held at 14 C)
    doorwayReveal   the faces in the partition's thickness: the doorway's jamb and lintel

and rewrites constant/polyMesh/faces, owner and boundary in that order (points and neighbour are
unchanged). It writes the cellZones fanHigh (y 1.52-2.04 m) and fanLow (y 0.04-0.56 m), the cells
in the doorway's plane x 4.00-4.08 m with z < 0.26 m, and the faceZones the monitor sums the flux
over: each fan zone's two x faces (<zone>Left at x = 4.00, <zone>Right at x = 4.08), the doorway's
face at x = 4.08 (doorway, z < 0.44, y < 2.04 m) and its halves above and below 1.02 m (doorUpper,
doorLower), all oriented +x, from the stove room into the cold room. It checks the stove's, the
flue's, the doorway's and each fan face's areas to 1%, and writes cells.npz (each cell's centre,
the middle of its bounding box, and its volume, used for the starting fields) and patches.json
beside the mesh. The polyMesh must be ASCII, as template/mesh/system/controlDict writes it.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
TOL = 1e-6


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: house_patches.py runs/mesh")
    mesh = Path(sys.argv[1])
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

    if "stoveRoomWalls" in content("boundary"):
        raise SystemExit(f"{m} already has the house's patches")
    pts = np.array([np.fromstring(x, sep=" ") for x in re.findall(r"\(([^()]+)\)", body("points"))])
    faces = [np.fromstring(x, sep=" ", dtype=int) for x in re.findall(r"\d+\(([^()]*)\)", body("faces"))]
    owner = np.fromstring(body("owner"), sep=" ", dtype=int)
    nei = np.fromstring(body("neighbour"), sep=" ", dtype=int)
    ni = len(nei)
    fc = np.array([pts[f].mean(axis=0) for f in faces])
    sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(axis=0) / 2 for f in faces])
    areas = np.linalg.norm(sf, axis=1)

    pc = cfg["patches"]
    x0, x1 = pc["partition"]

    def inbox(p, b):
        return all(b[i] - TOL < p[i] < b[i + 3] + TOL for i in range(3))

    patches = {n: [] for n in ("symmetry", "stoveRoomWalls", "coldRoomWalls", "doorwayReveal", "stove", "flue")}
    for i in range(ni, len(faces)):
        p = fc[i]
        if abs(p[2]) < 1e-7:
            n = "symmetry"
        elif inbox(p, pc["stove"]["box"]):
            n = "stove"
        elif inbox(p, pc["flue"]["box"]):
            n = "flue"
        elif p[0] <= x0 + 1e-7:
            n = "stoveRoomWalls"
        elif p[0] >= x1 - 1e-7:
            n = "coldRoomWalls"
        else:
            n = "doorwayReveal"
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
    N = owner.max() + 1
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

    fans = cfg["fans"]
    h, zf = fans["height"], fans["zMax"]
    cellzones = {n: np.where((C[:, 0] > x0) & (C[:, 0] < x1) & (C[:, 1] > fans[n]) & (C[:, 1] < fans[n] + h)
                             & (C[:, 2] < zf))[0] for n in ("fanHigh", "fanLow")}
    s = header("cellZones", "regIOobject") + str(len(cellzones)) + "\n(\n"
    for n, ids in cellzones.items():
        s += n + "\n{\ntype cellZone;\ncellLabels List<label>\n" + str(len(ids)) + "\n(\n" + "\n".join(map(str, ids)) + "\n);\n}\n"
    (m / "cellZones").write_text(s + ")\n")

    xface = np.abs(sf[:, 0]) > 0.99 * areas
    zones = {}
    for n in ("fanHigh", "fanLow"):
        for side, x in (("Left", x0), ("Right", x1)):
            zones[n + side] = np.where((np.abs(fc[:, 0] - x) < 1e-7) & (fc[:, 1] > fans[n]) & (fc[:, 1] < fans[n] + h)
                                       & (fc[:, 2] < zf) & xface)[0]
    dw = cfg["doorway"]
    door = np.where((np.abs(fc[:, 0] - x1) < 1e-7) & (fc[:, 1] < dw["yMax"]) & (fc[:, 2] < dw["zMax"]) & xface)[0]
    zones["doorway"] = door
    zones["doorUpper"] = door[fc[door, 1] > dw["split"]]
    zones["doorLower"] = door[fc[door, 1] < dw["split"]]
    s = header("faceZones", "regIOobject") + str(len(zones)) + "\n(\n"
    for n, ids in zones.items():
        report[n] = {"faces": len(ids), "area": float(areas[ids].sum()), "orientation": "+x"}
        s += (n + "\n{\ntype faceZone;\nfaceLabels List<label>\n" + str(len(ids)) + "\n(\n" + "\n".join(map(str, ids))
              + "\n);\nflipMap List<bool>\n" + str(len(ids)) + "\n(\n" + "\n".join("1" if sf[i, 0] < 0 else "0" for i in ids) + "\n);\n}\n")
    (m / "faceZones").write_text(s + ")\n")

    checks = [("stove", pc["stove"]["area"]), ("flue", pc["flue"]["area"]), ("doorway", dw["area"])]
    checks += [(n, fans["faceArea"]) for n in zones if n.startswith("fan")]
    for n, a in checks:
        assert abs(report[n]["area"] / a - 1) < 0.01, (n, report[n], a)
    np.savez_compressed(mesh / "cells.npz", C=C, V=V)
    (mesh / "patches.json").write_text(json.dumps(report, indent=2))
    for n, r in report.items():
        print(f"{n:15s} {r['faces']:6d} faces {r['area']:10.6f} m2")
    for n, ids in cellzones.items():
        print(f"{n:15s} {len(ids):6d} cells")
    print("cells", N, "volume", V.sum())


if __name__ == "__main__":
    main()
