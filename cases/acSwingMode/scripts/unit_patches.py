#!/usr/bin/env python3
"""Cut the unit's intake and its corner outlet out of snappyHexMesh's unitWall patch.

    python3 scripts/unit_patches.py runs/mesh

snappyHexMesh leaves the whole unit as one wall patch, unitWall. This moves its faces, by face
centre, into two patches (config/case.json, "ports"):

    intake    the grille on the unit's top, y = 2.30 m, x 0.02-0.22 m, z < 0.38 m
    outlet    one opening round the box's front-bottom corner, used by every vane angle:
              a strip of the front face, x = 0.24 m, y 2.00-2.06 m, z < 0.30 m, and
              a strip of the underside at the front edge, y = 2.00 m, x 0.20-0.24 m, z < 0.24 m

and rewrites constant/polyMesh/faces, owner and boundary in that order (points and neighbour are
unchanged). It checks the intake's, each outlet strip's, the outlet's and the bed's areas
against the geometry to 1% and each strip's normal, checks that the pressure reference point
lies strictly inside one cell, and writes cells.npz (cell centres and volumes, used for the
hydrostatic start) and patches.json beside the mesh. The polyMesh must be ASCII, as
template/mesh/system/controlDict writes it.

This is the study's audit_mesh.py with its paths made arguments and its numbers read from
config/case.json; it moves the same faces in the same order.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: unit_patches.py runs/mesh")
    mesh = Path(sys.argv[1])
    m = mesh / "constant" / "polyMesh"
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    ports = cfg["ports"]

    def content(n):
        s = (m / n).read_text()
        return s[s.index("}", s.index("FoamFile")) + 1:]

    def body(n):
        s = content(n)
        return s[s.index("(") + 1:s.rindex(")")]

    def header(n, cls):
        return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {n}; }}\n"

    pts = np.array([np.fromstring(x, sep=" ") for x in re.findall(r"\(([^()]+)\)", body("points"))])
    faces = [np.fromstring(x, sep=" ", dtype=int) for x in re.findall(r"\d+\(([^()]*)\)", body("faces"))]
    owner = np.fromstring(body("owner"), sep=" ", dtype=int)
    nei = np.fromstring(body("neighbour"), sep=" ", dtype=int)
    ni = len(nei)
    patches = {}
    for n, b in re.findall(r"(\w+)\s*\{([^{}]+)\}", content("boundary")):
        a = re.search(r"nFaces\s+(\d+)", b)
        q = re.search(r"startFace\s+(\d+)", b)
        if a and q:
            patches[n] = list(range(int(q[1]), int(q[1]) + int(a[1])))
    if "intake" in patches:
        raise SystemExit(f"{m} already has the unit's ports")
    fc = np.array([pts[f].mean(axis=0) for f in faces])
    sf = np.array([np.cross(pts[f], np.roll(pts[f], -1, axis=0)).sum(axis=0) / 2 for f in faces])
    areas = np.linalg.norm(sf, axis=1)

    pi, pf, pu = ports["intake"], ports["outletFront"], ports["outletUnder"]
    u = patches["unitWall"]
    patches["intake"] = [i for i in u if abs(fc[i, 1] - pi["y"]) < 1e-7 and pi["x"][0] < fc[i, 0] < pi["x"][1] and fc[i, 2] < pi["zMax"]]
    front = [i for i in u if abs(fc[i, 0] - pf["x"]) < 1e-7 and pf["y"][0] < fc[i, 1] < pf["y"][1] and fc[i, 2] < pf["zMax"]]
    under = [i for i in u if abs(fc[i, 1] - pu["y"]) < 1e-7 and pu["x"][0] < fc[i, 0] < pu["x"][1] and fc[i, 2] < pu["zMax"]]
    patches["outlet"] = front + under
    used = set(patches["intake"] + patches["outlet"])
    patches["unitWall"] = [i for i in u if i not in used]

    # each strip's area, and its normal out of the room (into the unit): -x for the front strip,
    # +y for the underside strip
    for name, ids, want, normal in (("front", front, pf["area"], (-1, 0, 0)), ("underside", under, pu["area"], (0, 1, 0))):
        assert abs(areas[ids].sum() / want - 1) < 0.01, (name, areas[ids].sum(), want)
        n = sf[ids].sum(axis=0) / areas[ids].sum()
        assert np.max(abs(n - normal)) < 1e-7, (name, n)

    report = {}
    idx = list(range(ni))
    out = []
    start = ni
    for n, ids in patches.items():
        aa = areas[ids]
        report[n] = {"faces": len(ids), "area": float(aa.sum()),
                     "face_edge_sizes_m": sorted(set(np.round(np.sqrt(aa), 6).tolist())),
                     "areaVector": sf[ids].sum(axis=0).tolist()}
        typ = "symmetry" if n == "symmetry" else ("patch" if n in ("intake", "outlet") else "wall")
        out.append(f"{n}\n{{\n type {typ};\n nFaces {len(ids)};\n startFace {start};\n}}\n")
        idx += ids
        start += len(ids)
    assert len(idx) == len(set(idx)) == len(faces)
    for n, a in (("intake", pi["area"]), ("outlet", ports["outletArea"]), ("bed", ports["bedArea"])):
        assert abs(report[n]["area"] / a - 1) < 0.01, (n, report[n], a)

    (m / "faces").write_text(header("faces", "faceList") + str(len(idx)) + "\n(\n"
                             + "\n".join(str(len(faces[i])) + "(" + " ".join(map(str, faces[i])) + ")" for i in idx) + "\n)\n")
    (m / "owner").write_text(header("owner", "labelList") + str(len(idx)) + "\n(\n" + "\n".join(map(str, owner[idx])) + "\n)\n")
    (m / "boundary").write_text(header("boundary", "polyBoundaryMesh") + str(len(out)) + "\n(\n" + "".join(out) + ")\n")

    # Cell centres (area-weighted face centres) and volumes (divergence theorem), in the face
    # order snappyHexMesh wrote, as the solved runs' hydrostatic start was computed.
    vol = np.zeros(max(owner.max(), nei.max()) + 1)
    cs = np.zeros((len(vol), 3))
    for d in range(3):
        np.add.at(cs[:, d], owner, fc[:, d] * areas)
        np.add.at(cs[:, d], nei, fc[:ni, d] * areas[:ni])
    w = np.zeros(len(vol))
    np.add.at(w, owner, areas)
    np.add.at(w, nei, areas[:ni])
    cs /= w[:, None]
    v = (sf * fc).sum(axis=1) / 3
    np.add.at(vol, owner, v)
    np.add.at(vol, nei, -v[:ni])

    # the pressure reference point must lie strictly inside one cell, not on a face
    ref = np.array([float(x) for x in cfg["pRefPoint"].split()])
    lo = np.full((len(vol), 3), np.inf)
    hi = -lo.copy()
    for f, o in zip(faces, owner):
        lo[o] = np.minimum(lo[o], pts[f].min(axis=0))
        hi[o] = np.maximum(hi[o], pts[f].max(axis=0))
    for f, o in zip(faces[:ni], nei):
        lo[o] = np.minimum(lo[o], pts[f].min(axis=0))
        hi[o] = np.maximum(hi[o], pts[f].max(axis=0))
    cells = np.where(np.all((ref > lo + 1e-8) & (ref < hi - 1e-8), axis=1))[0]
    assert len(cells) == 1, ("pRefPoint is not strictly inside one cell", cells)
    report["_pRefCell"] = {"point": ref.tolist(), "cell": int(cells[0]), "lo": lo[cells[0]].tolist(), "hi": hi[cells[0]].tolist()}

    np.savez_compressed(mesh / "cells.npz", C=cs, V=vol)
    (mesh / "patches.json").write_text(json.dumps(report, indent=2))
    for n, r in report.items():
        if not n.startswith("_"):
            print(f"{n:13s} {r['faces']:6d} faces {r['area']:10.6f} m2")
    print("pRefPoint", ref.tolist(), "in cell", int(cells[0]))
    print("cells", len(vol), "volume", vol.sum())


if __name__ == "__main__":
    main()
