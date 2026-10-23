#!/usr/bin/env python3
"""The attic room's mesh: a 2-D section meshed by gmsh, swept across the room's width.

    $PYTHON build_roof.py <run dir>

writes <run dir>/constant/polyMesh (points, faces, owner, neighbour, boundary, cellZones,
faceZones) and, beside it, mesh_measurements.json (the room's volume and the opening's areas,
read off the mesh), section.msh and mesh_section.npz (the section, for checks and drawing).
Needs gmsh 4.15.2 and NumPy; another gmsh version meshes the same outline, but not to the same
cells.

The section is the plane z = const through the room, x from the knee wall into the room and y up
from the floor. u runs up the roof's slope from the knee wall's top (0, 1.0) and v out of the
roof, normal to it: x = (u - v)/sqrt 2, y = 1 + (u + v)/sqrt 2. The roof's inner face is v = 0
and its outer face v = 0.24.

- the room: floor 4.0 m, a 1.0 m knee wall, the roof at 45 degrees up to a flat ceiling 2.8 m
  above the floor 1.8 m in from the knee wall, and the inner wall vertical at x = 4.0;
- the opening through the roof: u 0.30 to 1.639 m (the PK08's 1.339 m clear lining height),
  across the 0.24 m roof, and z 1.3065 to 2.1935 m (its 0.887 m clear width) across the room's
  3.5 m;
- the outdoor air over the roof: u -0.70 to 3.139 m, v 0.24 to 1.74 m, z -0.75 to 4.25 m;
- the sash: a slab 1.338 m long and 80 mm deep, flush with the roof's outer face when shut and
  turned about its centre (u 0.9695, v 0.20) the VELUX way, top edge into the room, by 45 degrees,
  so that in a 45-degree roof it lies horizontal: x -0.124 to 1.214, y 1.787 to 1.867 m; its
  cells are left out across the opening's width;
- the radiator box: x 0.040 to 0.123 m, y 0.15 to 0.75 m against the knee wall, z 1.25 to
  2.25 m.

gmsh meshes the section with quads (cells 20 mm at the opening and over the first 0.30 m round
it, growing to 90 mm in the room), and the section is swept over graded z layers (20 mm over
the opening's width and 0.30 m either side). Cells are kept where their centre is in the room
(between z 0 and 3.5), the outdoor air, or the opening (within its width), and not in the sash.
Patches: `outside` (the outdoor box's open faces), `walls` (every face of the room),
`outerWalls` (the roof's outer face, the opening's linings and the outdoor box's face on the
roof), `sash`. Zones: `room` and `indoor` (the room's cells), `radiator`, and three face zones
on the roof's inner face v = 0, oriented into the room: `opening1` (the whole opening),
`eaves` (below the sash's mid-plane, y < 1.827 m) and `ridge` (above it).
"""
import json
import math
import sys
from pathlib import Path

import gmsh
import numpy as np

CASE = Path(sys.argv[1]).resolve()
POLY = CASE / "constant/polyMesh"
POLY.mkdir(parents=True, exist_ok=True)
sq = math.sqrt(.5)


def xy(u, v):
    return ((u - v) * sq, 1 + (u + v) * sq)


def polygon(coords):
    pts = [gmsh.model.occ.addPoint(x, y, 0) for x, y in coords]
    lines = [gmsh.model.occ.addLine(a, b) for a, b in zip(pts, pts[1:] + pts[:1])]
    return gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop(lines)])


# ---------------------------------------------------------------- the section, meshed by gmsh
gmsh.initialize()
gmsh.model.add("roof_section")
room = polygon([(0, 0), (4, 0), (4, 2.8), (1.8, 2.8), (0, 1)])
out = polygon([xy(-.7, .24), xy(3.139, .24), xy(3.139, 1.74), xy(-.7, 1.74)])
reveal = polygon([xy(.3, 0), xy(1.639, 0), xy(1.639, .24), xy(.3, .24)])
# the sash turned the VELUX way, top edge into the room: horizontal in a 45-degree roof
sash = polygon([(-.124, 1.787), (1.214, 1.787), (1.214, 1.867), (-.124, 1.867)])
radiator = polygon([(.04, .15), (.123, .15), (.123, .75), (.04, .75)])
gmsh.model.occ.fragment([(2, room), (2, out), (2, reveal)], [(2, sash), (2, radiator)])
gmsh.model.occ.synchronize()
# cell size: 20 mm over the opening (the whole of its rectangle through the roof) and the first
# 0.30 m round it, then growing 0.10 m per metre to 90 mm
u = "((x+y-1)*0.7071067811865476)"
v = "((y-x-1)*0.7071067811865476)"
d = f"Sqrt((Max(0,Max(0.3-{u},{u}-1.639)))^2+(Max(0,Max(-{v},{v}-0.24)))^2)"
f = gmsh.model.mesh.field.add("MathEval")
gmsh.model.mesh.field.setString(f, "F", f"Min(0.09,0.02+0.10*Max(0,{d}-0.30))")
gmsh.model.mesh.field.setAsBackgroundMesh(f)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm", 8)
gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
gmsh.option.setNumber("General.NumThreads", 1)
for dim, tag in gmsh.model.getEntities(2):
    gmsh.model.mesh.setRecombine(dim, tag)
gmsh.model.mesh.generate(2)
gmsh.model.mesh.optimize("Relocate2D", niter=5)
nt, coords, _ = gmsh.model.mesh.getNodes()
coords = np.array(coords).reshape(-1, 3)[:, :2]
sort = np.argsort(nt)
nt = np.array(nt)[sort]
coords = coords[sort]
polys = []   # each 2-D cell's nodes, counter-clockwise
for typ, tags, nodes in zip(*gmsh.model.mesh.getElements(2)):
    n = gmsh.model.mesh.getElementProperties(typ)[3]
    assert n in (3, 4)
    for a in np.array(nodes).reshape(-1, n):
        ids = np.searchsorted(nt, a).tolist()
        p = coords[ids]
        area = np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))
        if area < 0:
            ids.reverse()
        polys.append(ids)
gmsh.write(str(CASE / "section.msh"))
gmsh.finalize()

n2 = len(polys)
nn = len(coords)
cent = np.array([coords[p].mean(axis=0) for p in polys])
X, Y = cent.T
U = (X + Y - 1) * sq
V = (Y - X - 1) * sq
isroom = (X >= -1e-8) & (X <= 4 + 1e-8) & (Y >= 0) & (Y <= 2.8 + 1e-8) & (V <= 1e-8)
isout = (U >= -.7 - 1e-8) & (U <= 3.139 + 1e-8) & (V >= .24 - 1e-8) & (V <= 1.74 + 1e-8)
isreveal = (U >= .3 - 1e-8) & (U <= 1.639 + 1e-8) & (V >= -1e-8) & (V <= .24 + 1e-8)
issash = (X > -.124) & (X < 1.214) & (Y > 1.787) & (Y < 1.867)


# ---------------------------------------------------------------- the sweep across the width
def segment(a, b, h0, h1):
    """Points from a to b with cells growing geometrically from about h0 to about h1."""
    n = max(1, round((b - a) / (math.sqrt(h0 * h1))))
    w = np.geomspace(h0, h1, n)
    return (a + np.r_[0, np.cumsum(w) * (b - a) / w.sum()]).tolist()


# 20 mm over the opening's width and 0.30 m either side, growing towards the side walls, and the
# 0.75 m of outdoor air beyond each side wall in four cells
z = []
for a, b, h0, h1 in [(-.75, 0, .25, .12), (0, 1.0065, .09, .02), (1.0065, 1.25, .02, .02),
                     (1.25, 1.3065, .02, .02), (1.3065, 2.1935, .02, .02),
                     (2.1935, 2.25, .02, .02), (2.25, 2.4935, .02, .02),
                     (2.4935, 3.5, .02, .09), (3.5, 4.25, .12, .25)]:
    z += segment(a, b, h0, h1)[:-1]
z = np.array(z + [4.25])
nz = len(z) - 1
zc = (z[:-1] + z[1:]) / 2
inwidth = (zc[:, None] > 1.3065) & (zc[:, None] < 2.1935)
keep = (isout[None, :]
        | ((zc[:, None] > 0) & (zc[:, None] < 3.5) & isroom[None, :])
        | (inwidth & isreveal[None, :])) & ~(inwidth & issash[None, :])
ids = np.full((nz, n2), -1, dtype=np.int32)
ids[keep] = np.arange(keep.sum())
nc = int(keep.sum())
print("section", nn, "points", n2, "cells;", nz, "layers;", nc, "cells kept", flush=True)

# the section's edges: [node a, node b, cell on the left, cell on the right or -1]
edges = {}
for c, poly in enumerate(polys):
    for a, b in zip(poly, poly[1:] + poly[:1]):
        key = tuple(sorted((a, b)))
        if key not in edges:
            edges[key] = [a, b, c, -1]
        else:
            edges[key][3] = c
faces, owners, neigh, patches = [], [], [], []
zones = {"opening1": [], "eaves": [], "ridge": []}
zoneflips = {"opening1": [], "eaves": [], "ridge": []}
patch_names = ["outside", "walls", "outerWalls", "sash"]
outer = {"opening_outer": [], "outer_eaves": [], "outer_ridge": []}


def patch_for(mid, cell2, sashside=False):
    """The patch of a boundary face from its centre, the sash first."""
    x, y, zz = mid
    uu = (x + y - 1) * sq
    vv = (y - x - 1) * sq
    e = 1e-6
    if sashside and 1.3065 - e <= zz <= 2.1935 + e:
        return 3
    if abs(zz + .75) < e or abs(zz - 4.25) < e or abs(uu + .7) < e or abs(uu - 3.139) < e or abs(vv - 1.74) < e:
        return 0
    if isroom[cell2]:
        return 1
    return 2


# side faces, one per section edge and layer
for a, b, c, d in edges.values():
    midxy = (coords[a] + coords[b]) / 2
    mu = (midxy[0] + midxy[1] - 1) * sq
    mv = (midxy[1] - midxy[0] - 1) * sq
    outerface = (abs(mv - .24) < 1e-7 and .3 - 1e-7 < mu < 1.639 + 1e-7 and d >= 0
                 and isreveal[c] != isreveal[d])
    opening = abs(mv) < 1e-7 and .3 - 1e-7 < mu < 1.639 + 1e-7 and d >= 0 and isroom[c] != isroom[d]
    for k in range(nz):
        ca = int(ids[k, c])
        cb = int(ids[k, d]) if d >= 0 else -1
        if ca < 0 and cb < 0:
            continue
        f = [k * nn + a, k * nn + b, (k + 1) * nn + b, (k + 1) * nn + a]
        if ca < 0 or (cb >= 0 and ca > cb):
            f.reverse()
            ca, cb = cb, ca
            first = d
        else:
            first = c
        other = d if first == c else c
        idx = len(faces)
        faces.append(f)
        owners.append(ca)
        neigh.append(cb)
        patches.append(-1 if cb >= 0 else patch_for((*midxy, zc[k]), first, other >= 0 and bool(issash[other])))
        if outerface and cb >= 0:
            outer["opening_outer"].append(idx)
            outer["outer_eaves" if midxy[1] < 1.827 else "outer_ridge"].append(idx)
        if opening and cb >= 0:
            # the face's normal points from its owner; flip it where the owner is the room's
            owner2 = c if int(ids[k, c]) == ca else d
            flip = bool(isroom[owner2])
            for zn in ["opening1", "eaves" if midxy[1] < 1.827 else "ridge"]:
                zones[zn].append(idx)
                zoneflips[zn].append(flip)
# caps, one per section cell and layer boundary
for c, poly in enumerate(polys):
    midxy = cent[c]
    for k in range(nz + 1):
        below = int(ids[k - 1, c]) if k > 0 else -1
        above = int(ids[k, c]) if k < nz else -1
        if below < 0 and above < 0:
            continue
        f = [k * nn + a for a in poly]   # counter-clockwise: normal +z, out of the cell below
        ca, cb = below, above
        if ca < 0 or (cb >= 0 and ca > cb):
            f.reverse()
            ca, cb = cb, ca
        faces.append(f)
        owners.append(ca)
        neigh.append(cb)
        patches.append(-1 if cb >= 0 else patch_for((*midxy, z[k]), c, bool(issash[c])))
print("faces", len(faces), flush=True)

# ---------------------------------------------------------------- OpenFOAM's polyMesh
# internal faces first, in owner then neighbour order, then each patch's faces together
O = np.array(owners, dtype=np.int32)
N = np.array(neigh, dtype=np.int32)
B = np.array(patches, dtype=np.int8)
intern = np.where(N >= 0)[0]
intern = intern[np.lexsort((N[intern], O[intern]))]
order = np.r_[intern, *[np.where(B == p)[0] for p in range(4)]]
inv = np.empty(len(order), np.int32)
inv[order] = np.arange(len(order))
used = np.unique(np.array([v for f in faces for v in f], dtype=np.int32))
nodemap = np.full(nn * (nz + 1), -1, np.int32)
nodemap[used] = np.arange(len(used))
pts = np.column_stack((coords[used % nn], z[used // nn]))


def hdr(cls, obj, fmt="binary"):
    return (f'FoamFile\n{{\n version 2.0;\n format {fmt};\n class {cls};\n object {obj};\n'
            f' arch "LSB;label=32;scalar=64";\n}}\n').encode()


def arrfile(name, cls, arr):
    with (POLY / name).open("wb") as fh:
        fh.write(hdr(cls, name))
        fh.write(f"\n{len(arr)}\n(".encode())
        fh.write(arr.tobytes())
        fh.write(b"\n)\n")


arrfile("points", "vectorField", pts.astype("<f8"))
arrfile("owner", "labelList", O[order])
arrfile("neighbour", "labelList", N[intern])
with (POLY / "faces").open("wb") as fh:   # a binary faceList: each face's size, then its labels
    fh.write(hdr("faceList", "faces"))
    fh.write(f"\n{len(order)}\n(\n".encode())
    for i in order:
        a = nodemap[faces[i]].astype("<i4")
        fh.write(str(len(a)).encode() + b"(" + a.tobytes() + b")\n")
    fh.write(b")\n")
off = len(intern)
text = hdr("polyBoundaryMesh", "boundary", "ascii").decode() + "\n4\n(\n"
for p, name in enumerate(patch_names):
    nfaces = int((B == p).sum())
    text += f'{name}\n{{\n type {"patch" if p == 0 else "wall"};\n nFaces {nfaces};\n startFace {off};\n}}\n'
    off += nfaces
text += ")\n"
(POLY / "boundary").write_text(text)
roomids = ids[:, isroom]
roomids = roomids[roomids >= 0]
rad = (X > .04) & (X < .123) & (Y > .15) & (Y < .75)
radids = ids[(zc > 1.25) & (zc < 2.25)][:, rad]
radids = radids[radids >= 0]


def labeltext(a):
    return f"{len(a)}\n(\n" + "\n".join(map(str, a)) + "\n)"


t = hdr("regIOobject", "cellZones", "ascii").decode() + "\n3\n(\n"
for name, a in [("room", roomids), ("indoor", roomids), ("radiator", radids)]:
    t += f"{name}\n{{ type cellZone; cellLabels List<label>\n{labeltext(a)};\n}}\n"
(POLY / "cellZones").write_text(t + ")\n")
t = hdr("regIOobject", "faceZones", "ascii").decode() + "\n3\n(\n"
for name in zones:
    a = inv[zones[name]]
    fl = zoneflips[name]
    t += (f"{name}\n{{ type faceZone; faceLabels List<label>\n{labeltext(a)};\n"
          f" flipMap List<bool>\n{labeltext([int(v) for v in fl])};\n}}\n")
(POLY / "faceZones").write_text(t + ")\n")

# ---------------------------------------------------------------- measured off the mesh
areas = np.array([abs(np.sum(coords[p, 0] * np.roll(coords[p, 1], -1) - coords[p, 1] * np.roll(coords[p, 0], -1))) / 2
                  for p in polys])
dz = np.diff(z)
centroid = []
for p in polys:
    q = coords[p]
    r = np.roll(q, -1, axis=0)
    cross = q[:, 0] * r[:, 1] - r[:, 0] * q[:, 1]
    centroid.append(np.sum((q + r) * cross[:, None], axis=0) / (3 * cross.sum()))
centroid = np.array(centroid)
vol = dz[:, None] * areas[None, :]
R = 8314.47 / 28.96
s0 = float((vol * keep * isroom[None, :] * 1e5 * np.exp(-9.81 * centroid[None, :, 1] / (R * 273.15))
            / (R * 293.15)).sum())
on_inner = ((np.abs((coords[:, 1] - coords[:, 0] - 1) * sq) < 1e-7)
            & ((coords[:, 0] + coords[:, 1] - 1) * sq >= .3 - 1e-7)
            & ((coords[:, 0] + coords[:, 1] - 1) * sq <= 1.639 + 1e-7))
lining_u = ((coords[:, 0] + coords[:, 1] - 1) * sq)[on_inner]
info = {
    "cells": nc, "points": len(pts), "cross_section_cells": n2, "z_layers": nz,
    "room_air_volume_m3": float((vol * keep * isroom[None, :]).sum()),
    "initial_scalar_inventory_kg": s0,
    "clear_lining_area_m2": float((z[np.argmin(abs(z - 2.1935))] - z[np.argmin(abs(z - 1.3065))])
                                  * (lining_u.max() - lining_u.min())),
    "opening_inner_area_m2": {}, "opening_outer_area_m2": {},
    "radiator_cell_count": len(radids),
    "z_opening_cell_width_m": float(np.diff(z)[(zc > 1.3065) & (zc < 2.1935)][0]),
}
for key, groups in (("opening_inner_area_m2", zones), ("opening_outer_area_m2", outer)):
    for name, ii in groups.items():
        area = 0
        for i in ii:
            f = faces[i]
            q = np.column_stack((coords[np.array(f) % nn], z[np.array(f) // nn]))
            area += np.linalg.norm(np.cross(q[1] - q[0], q[2] - q[0]))
        info[key][name] = area
(CASE / "mesh_measurements.json").write_text(json.dumps(info, indent=2))
print(json.dumps(info, indent=2), flush=True)
np.savez_compressed(CASE / "mesh_section.npz", points=coords, centres=centroid,
                    polygons=np.array([p + [-1] * (4 - len(p)) for p in polys]), room=isroom,
                    outdoor=isout, reveal=isreveal, sash=issash, z=z)
