#!/usr/bin/env python3
"""Build the quadcopter airframe as CAD (build123d, OpenCASCADE) and write the STL the
mesher reads, split into one named region per part.

    python3 scripts/build_airframe.py

Frame, used everywhere in the case: +x downstream (the wind blows towards +x), +y to
the left, +z up. The nose points to -x. The airframe is built level; the 10 degree
nose-down attitude enters as the direction of the wind (scripts/make_case.py), not here.

Parts, in metres:
  body   160 x 100 x 50 mm box, edges rounded 4 mm, centred on the origin
  arms   4 round tubes 20 mm across, in an X at 45 degrees, horizontal at the body's
         mid-height, 180 mm of tube outboard of the body's side
  cans   4 motor cans, vertical cylinders 28 mm across and 30 mm tall, at the arm ends
  hubs   4 discs 60 mm across and 4 mm thick, horizontal, on top of the cans
  legs   4 rods 8 mm across, 60 mm below the body, under its corners
There are no rotor blades.

Writes, into geometry/:
  airframe.stl    the fused solid's triangles in five named solids, body arms cans hubs
                  legs, each triangle given to the part whose primitive it lies on
  geometry.json   bounding box, volume, wetted area per part, and the silhouette area
                  of each part and of the whole seen along the wind
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from build123d import Align, Box, Cylinder, Part, Plane, Pos, Vector, export_stl, fillet

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "geometry"

BODY_L, BODY_W, BODY_H = 0.160, 0.100, 0.050
FILLET_R = 0.004
ARM_D, ARM_FREE = 0.020, 0.180
CAN_D, CAN_H = 0.028, 0.030
HUB_D, HUB_T = 0.060, 0.004
LEG_D, LEG_L = 0.008, 0.060
PITCH_DEG = 10.0          # only for the silhouette along the wind; make_case.py owns it

SQ = math.sqrt(0.5)
SIGNS = [(+1, +1), (+1, -1), (-1, +1), (-1, -1)]
T_EXIT = (BODY_W / 2) / SQ          # where a 45 degree ray from the centre leaves the body side
ARM_START = 0.025                   # each arm starts inside the body, so the fuse is clean
ARM_LEN = (T_EXIT - ARM_START) + ARM_FREE
ARM_END = T_EXIT + ARM_FREE         # 0.2507 m from the centre to the can's axis
CAN_Z0 = -0.005                     # the can overlaps the arm
HUB_Z0 = CAN_Z0 + CAN_H - 0.001     # the hub sits 1 mm into the can's top
LEG_XY = (0.070, 0.040)             # inside the rounded corners
LEG_TOP = -BODY_H / 2 + 0.005       # 5 mm up inside the body
LEG_BOT = -BODY_H / 2 - LEG_L
PARTS = ["body", "arms", "cans", "hubs", "legs"]


def can_xy(sx, sy):
    return sx * SQ * ARM_END, sy * SQ * ARM_END


def cyl(r, h):
    return Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


def union(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out + s
    return out


def build_parts():
    arms = []
    for sx, sy in SIGNS:
        u = Vector(sx * SQ, sy * SQ, 0)
        arms.append(Plane(origin=u * ARM_START, z_dir=u) * cyl(ARM_D / 2, ARM_LEN))
    return {
        "body": fillet(Box(BODY_L, BODY_W, BODY_H).edges(), radius=FILLET_R),
        "arms": union(arms),
        "cans": union([Pos(*can_xy(sx, sy), CAN_Z0) * cyl(CAN_D / 2, CAN_H) for sx, sy in SIGNS]),
        "hubs": union([Pos(*can_xy(sx, sy), HUB_Z0) * cyl(HUB_D / 2, HUB_T) for sx, sy in SIGNS]),
        "legs": union([Pos(sx * LEG_XY[0], sy * LEG_XY[1], LEG_BOT) * cyl(LEG_D / 2, LEG_TOP - LEG_BOT)
                       for sx, sy in SIGNS]),
    }


# Signed distance to each part's primitives, to give every fused triangle to its part.
def sd_box(p, half):
    q = np.abs(p) - np.asarray(half)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)


def sd_cyl(p, a, u, r, length):
    v = p - np.asarray(a, float)
    t = v @ np.asarray(u, float)
    dr = np.linalg.norm(v - np.outer(t, u), axis=1) - r
    dt = np.maximum(-t, t - length)
    return np.linalg.norm(np.maximum(np.stack([dr, dt], 1), 0), axis=1) + np.minimum(np.maximum(dr, dt), 0)


def part_distances(p):
    d = {"body": sd_box(p, (BODY_L / 2, BODY_W / 2, BODY_H / 2))}
    d["arms"] = np.min([sd_cyl(p, (sx * SQ * ARM_START, sy * SQ * ARM_START, 0), (sx * SQ, sy * SQ, 0),
                               ARM_D / 2, ARM_LEN) for sx, sy in SIGNS], axis=0)
    d["cans"] = np.min([sd_cyl(p, (*can_xy(sx, sy), CAN_Z0), (0, 0, 1), CAN_D / 2, CAN_H)
                        for sx, sy in SIGNS], axis=0)
    d["hubs"] = np.min([sd_cyl(p, (*can_xy(sx, sy), HUB_Z0), (0, 0, 1), HUB_D / 2, HUB_T)
                        for sx, sy in SIGNS], axis=0)
    d["legs"] = np.min([sd_cyl(p, (sx * LEG_XY[0], sy * LEG_XY[1], LEG_BOT), (0, 0, 1), LEG_D / 2,
                               LEG_TOP - LEG_BOT) for sx, sy in SIGNS], axis=0)
    return np.stack([d[n] for n in PARTS], axis=1)


def silhouette(points, tris, direction, res=2000):
    """Area of the shadow the triangles cast along `direction`, by rasterising them."""
    from PIL import Image, ImageDraw
    d = np.asarray(direction, float) / np.linalg.norm(direction)
    e1 = np.cross(d, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    P = points @ np.stack([e1, e2], axis=1)
    lo = P.min(axis=0)
    h = (P.max(axis=0) - lo).max() * 1.02 / res
    Q = (P - lo) / h
    img = Image.new("1", (res, res), 0)
    draw = ImageDraw.Draw(img)
    for t in tris:
        draw.polygon([tuple(Q[i]) for i in t], fill=1, outline=1)
    return float(np.asarray(img).sum()) * h * h


def main():
    OUT.mkdir(exist_ok=True)
    parts = build_parts()
    drone = Part(union([parts[n] for n in PARTS]).wrapped)
    n_solids = len(drone.solids())
    bb = drone.bounding_box()
    print(f"solids after fuse : {n_solids}")
    print(f"volume            : {drone.volume * 1e6:.1f} cm3")
    print(f"bbox              : x {bb.min.X:+.4f} {bb.max.X:+.4f}  y {bb.min.Y:+.4f} {bb.max.Y:+.4f}"
          f"  z {bb.min.Z:+.4f} {bb.max.Z:+.4f}")
    if n_solids != 1:
        raise SystemExit("the parts did not fuse into one solid")

    tmp = OUT / "airframe_fused.stl"
    export_stl(drone, str(tmp), tolerance=1.0e-4, angular_tolerance=0.15)
    import pyvista as pv
    m = pv.read(str(tmp)).clean().triangulate()
    tmp.unlink()
    if m.n_open_edges != 0:
        raise SystemExit(f"the fused surface has {m.n_open_edges} open edges")
    tri = m.faces.reshape(-1, 4)[:, 1:]
    pts = np.asarray(m.points)
    owner = np.argmin(part_distances(np.asarray(m.cell_centers().points)), axis=1)
    areas = m.compute_cell_sizes(length=False, area=True, volume=False)["Area"]

    lines = []
    for i, name in enumerate(PARTS):
        t = tri[owner == i]
        p0, p1, p2 = pts[t[:, 0]], pts[t[:, 1]], pts[t[:, 2]]
        n = np.cross(p1 - p0, p2 - p0)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
        lines.append(f"solid {name}\n")
        for k in range(len(t)):
            lines.append(f" facet normal {n[k,0]:.6e} {n[k,1]:.6e} {n[k,2]:.6e}\n  outer loop\n")
            for q in (p0[k], p1[k], p2[k]):
                lines.append(f"   vertex {q[0]:.8e} {q[1]:.8e} {q[2]:.8e}\n")
            lines.append("  endloop\n endfacet\n")
        lines.append(f"endsolid {name}\n")
    (OUT / "airframe.stl").write_text("".join(lines))

    a = math.radians(PITCH_DEG)
    wind = (math.cos(a), 0.0, -math.sin(a))
    shadow = {"total": silhouette(pts, tri, wind)}
    for i, name in enumerate(PARTS):
        shadow[name] = silhouette(pts, tri[owner == i], wind)
    wetted = {n: float(areas[owner == i].sum()) for i, n in enumerate(PARTS)}
    for n in PARTS:
        print(f"{n:5s} triangles {int((owner == PARTS.index(n)).sum()):6d}   wetted {wetted[n]*1e4:7.1f} cm2"
              f"   silhouette along the wind {shadow[n]*1e4:6.1f} cm2")
    print(f"whole airframe silhouette along the wind {shadow['total']*1e4:.1f} cm2")
    json.dump({
        "bbox_m": {"min": [bb.min.X, bb.min.Y, bb.min.Z], "max": [bb.max.X, bb.max.Y, bb.max.Z]},
        "volume_m3": drone.volume,
        "wetted_area_m2": wetted,
        "silhouette_along_wind_m2": shadow,
        "wind_direction": list(wind),
        "triangles": int(len(tri)),
    }, open(OUT / "geometry.json", "w"), indent=2)
    print("wrote geometry/airframe.stl and geometry/geometry.json")


if __name__ == "__main__":
    main()
