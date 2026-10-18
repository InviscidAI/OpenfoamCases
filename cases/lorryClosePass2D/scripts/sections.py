#!/usr/bin/env python3
"""Cut cyclistBehindLorry's lorry and rider at his shoulder height -> geometry/*_r_outline.csv.

    python3 scripts/sections.py [../cyclistBehindLorry/geometry] [geometry]

The 2-D case is the horizontal section z = 1.3 m (the rider's shoulders are at 1.258 m,
rider_build.json). The lorry and the rider are cyclistBehindLorry's, built there by
scripts/build_truck.py and scripts/build_rider.py (geometry/truck.stl, rider.stl and
rider_build.json); run those first. The rider is moved so his shoulder centre sits at the
origin; the lorry keeps its own axes (doors at x = 0, cab front at x = 16.5 m, sides at
y = +-1.275 m).

A slice of an STL leaves vertices as little as 0.04 mm apart, and a mesher that makes
every vertex a node puts slivers there (a first mesh held the time step at 2e-5 s). So
each outline is resampled by arc length, keeping every corner that turns by more than
30 degrees: the lorry at 1 cm (its finest cells) and the rider at 4 mm. These `*_r`
outlines are what the case uses: the lorry's is meshed (scripts/make_mesh.py), the rider's
is the drag term's outline (constant/riderOutline, scripts/rider_outline.py). Each lies
within 0.6 mm of the raw section with the same area; sections.json records both.
Needs trimesh and shapely.
"""
import json
import pathlib
import sys

import numpy as np
import trimesh
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

Z = 1.3


def section(stl, z):
    mesh = trimesh.load(stl)
    path = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    loops = [Polygon(d[:, :2]) for d in path.discrete]
    shape = unary_union([p.buffer(0) for p in loops])
    return [shape] if shape.geom_type == "Polygon" else list(shape.geoms)


def resample(poly, step, corner_deg=30.0):
    """Points every `step` m along the outline, keeping corners sharper than corner_deg."""
    p = np.asarray(poly.exterior.coords)[:-1]
    d = np.roll(p, -1, 0) - p
    keep = d.dot(d.T).diagonal() > 1e-12
    p, d = p[keep], d[keep]
    a = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    turn = np.abs((a - np.roll(a, 1) + 180) % 360 - 180)
    corners = np.where(turn > corner_deg)[0]
    if len(corners) == 0:
        corners = np.array([0])
    out = []
    for k, c in enumerate(corners):
        e = corners[(k + 1) % len(corners)]
        idx = np.arange(c, e + (len(p) if e <= c else 0) + 1) % len(p)
        seg = p[idx]
        s_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(seg, axis=0).T))])
        n = max(1, int(round(s_[-1] / step)))
        t = np.linspace(0, s_[-1], n + 1)[:-1]
        out += list(np.column_stack([np.interp(t, s_, seg[:, 0]), np.interp(t, s_, seg[:, 1])]))
    return Polygon(out)


def write_outline(polys, path):
    with open(path, "w") as f:
        f.write("loop,x_m,y_m\n")
        for i, p in enumerate(polys):
            for x, y in np.asarray(p.exterior.coords):
                f.write(f"{i},{x:.5f},{y:.5f}\n")


def main(src, out):
    src, out = pathlib.Path(src), pathlib.Path(out)
    build = json.loads((src / "rider_build.json").read_text())
    sx, sy, _ = build["shoulder_centre_m"]
    lorry = section(src / "truck.stl", Z)
    rider = [translate(p, -sx, -sy) for p in section(src / "rider.stl", Z)]
    info = {"z_m": Z, "rider_shoulder_centre_m": [sx, sy],
            "rider_origin": "shoulder centre moved to (0, 0)"}
    for name, raw, step in (("lorry_z1p3", lorry, 0.01), ("rider_z1p3", rider, 0.004)):
        res = [resample(p, step) for p in raw]
        segs = [np.hypot(*np.diff(np.asarray(p.exterior.coords), axis=0).T) for p in res]
        b = unary_union(raw).bounds
        info[name + "_r"] = {
            "segment_mm": [round(min(x.min() for x in segs) * 1e3, 2),
                           round(max(x.max() for x in segs) * 1e3, 2)],
            "vertices": [len(p.exterior.coords) - 1 for p in res],
            "area_m2": round(sum(p.area for p in res), 4),
            "raw_area_m2": round(sum(p.area for p in raw), 4),
            "hausdorff_to_raw_mm": round(max(q.hausdorff_distance(r) for q, r in zip(raw, res)) * 1e3, 3),
            "x_m": [round(b[0], 4), round(b[2], 4)], "y_m": [round(b[1], 4), round(b[3], 4)]}
        write_outline(res, out / f"{name}_r_outline.csv")
    (out / "sections.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent.parent
    main(sys.argv[1] if len(sys.argv) > 1 else here.parent / "cyclistBehindLorry" / "geometry",
         sys.argv[2] if len(sys.argv) > 2 else here / "geometry")
