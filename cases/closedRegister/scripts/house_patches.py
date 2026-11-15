#!/usr/bin/env python3
"""Sort the house's boundary into its patches and write the openings' face zones.

    python3 scripts/house_patches.py runs/mesh

snappyHexMesh leaves the blockMesh faces (front, back, floor, ceiling, west, east) and the cut-out
solids (solids) as patches that do not follow the house. This sorts every boundary face by its
centre (config/case.json) into

    floor             y = 0, but for the registers (layered wood)
    ceiling           y = 2.4 m (layered gypsum)
    walls             every other face: the outer walls, the interior walls, the closets and the
                      spare room's shut door (layered gypsum)
    windows           the six windows' faces in the front (z = 0) and back (z = 8.8 m) walls
    return            the return grille, 0.6 x 0.6 m on the furnace closet's west face at x = 7.6 m
    register_<room>   each floor register, 0.30 x 0.10 m: livingW, livingE, kitchen, bedroom, bath,
                      spare

and rewrites constant/polyMesh/faces, owner and boundary in that order (points and neighbour are
unchanged; return and the registers are of type patch, the rest wall). It writes the faceZones the
monitor sums the flow over: gap (under the spare room's door, z = 5.5 m), bedDoor, bathDoor
(z = 5.5 m), livingDoor (the hall's opening to the living room, z = 4.5 m) and kitchenDoor
(x = 5.7 m), oriented along -z (-x for the kitchen). It checks each register's (0.03 m2), the
windows' (6.48 m2), the return's (0.36 m2) and the gap's (0.04 m2) areas to 1%, and writes
cells.npz (each cell's centre, the middle of its bounding box, and its volume, used for the
starting pressure) and patches.json beside the mesh. The polyMesh must be ASCII, as
template/mesh/system/controlDict writes it.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]


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

    if "register_spare" in content("boundary"):
        raise SystemExit(f"{m} already has the house's patches")
    pts = np.array([np.fromstring(x, sep=" ") for x in re.findall(r"\(([^()]+)\)", body("points"))])
    faces = [np.fromstring(x, sep=" ", dtype=int) for x in re.findall(r"\d+\(([^()]*)\)", body("faces"))]
    owner = np.fromstring(body("owner"), sep=" ", dtype=int)
    nei = np.fromstring(body("neighbour"), sep=" ", dtype=int)
    ni = len(nei)
    fc = np.array([pts[f].mean(axis=0) for f in faces])
    sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(axis=0) / 2 for f in faces])
    areas = np.linalg.norm(sf, axis=1)

    H = cfg["house"]
    registers = cfg["registers"]
    ret = cfg["return"]
    win = cfg["windows"]

    def in_window(x, y, rects):
        return any(x0 < x < x1 and y0 < y < y1 for x0, x1, y0, y1 in rects)

    patches = {n: [] for n in ["floor", "ceiling", "walls", "windows", "return"] + list(registers)}
    for i in range(ni, len(faces)):
        x, y, z = fc[i]
        n = "walls"
        if abs(y) < 1e-7:
            n = "floor"
            for r, (xx, zz) in registers.items():
                if abs(x - xx) < .15000001 and abs(z - zz) < .05000001:
                    n = r
        elif abs(y - H[1]) < 1e-7:
            n = "ceiling"
        elif abs(x - ret["x"]) < 1e-7 and ret["z"][0] < z < ret["z"][1] and ret["y"][0] < y < ret["y"][1]:
            n = "return"
        elif abs(z) < 1e-7 and in_window(x, y, win["front"]):
            n = "windows"
        elif abs(z - H[2]) < 1e-7 and in_window(x, y, win["back"]):
            n = "windows"
        patches[n].append(i)

    report = {}
    idx = list(range(ni))
    out = []
    start = ni
    for n, ids in patches.items():
        aa = areas[ids]
        report[n] = {"faces": len(ids), "area": float(aa.sum()),
                     "face_edge_sizes_m": sorted(set(np.round(np.sqrt(aa), 6).tolist()))}
        out.append(f"{n}\n{{\n type " + ("patch" if n == "return" or n.startswith("register") else "wall")
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
    for name, (d, pos, a, b, h) in cfg["openings"].items():
        cross = 0 if d == 2 else 2
        ids = np.where((np.abs(fc[:, d] - pos) < 1e-7) & (fc[:, cross] > a) & (fc[:, cross] < b) & (fc[:, 1] < h)
                       & (np.abs(sf[:, d]) > .99 * areas))[0]
        zones[name] = (ids, d)
    s = header("faceZones", "regIOobject") + str(len(zones)) + "\n(\n"
    for n, (ids, d) in zones.items():
        report[n] = {"faces": len(ids), "area": float(areas[ids].sum()), "orientation": "-z" if d == 2 else "-x"}
        s += (n + "\n{\ntype faceZone;\nfaceLabels List<label>\n" + str(len(ids)) + "\n(\n" + "\n".join(map(str, ids))
              + "\n);\nflipMap List<bool>\n" + str(len(ids)) + "\n(\n" + "\n".join("1" if sf[i, d] > 0 else "0" for i in ids)
              + "\n);\n}\n")
    (m / "faceZones").write_text(s + ")\n")

    for n, a in [(r, .03) for r in registers] + [("windows", win["area"]), ("return", ret["area"]), ("gap", .04)]:
        assert abs(report[n]["area"] / a - 1) < .01, (n, report[n], a)
    rooms = {n: float(V[(C[:, 0] > a) & (C[:, 0] < b) & (C[:, 2] > d) & (C[:, 2] < e)].sum())
             for n, (a, b, d, e) in cfg["rooms"].items()}
    report["room_volumes_m3"] = rooms
    np.savez_compressed(mesh / "cells.npz", C=C, V=V)
    (mesh / "patches.json").write_text(json.dumps(report, indent=2))
    for n, r in report.items():
        if "faces" in r:
            print(f"{n:17s} {r['faces']:6d} faces {r['area']:10.6f} m2")
    for n, v in rooms.items():
        print(f"{n:17s} {v:8.3f} m3")
    print("cells", N, "volume", V.sum())


if __name__ == "__main__":
    main()
