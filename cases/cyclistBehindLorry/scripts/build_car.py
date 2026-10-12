#!/usr/bin/env python3
"""Build a generic mid-size car as closed CFD surfaces, for the car behind the lorry.

No brand and no downloaded model: a five-door liftback drawn here from the published
dimensions of a 2020 Skoda Octavia (autotijd.be, "Dimensions Skoda Octavia 2020-2024",
read 9 Oct 2026). Only the dimensions are borrowed; the shape is our own:
  * length 4.689 m, width 1.829 m without mirrors, height 1.470 m
  * wheelbase 2.686 m, front overhang 0.910 m, rear overhang 1.094 m
  * track 1.543 m front, 1.535 m rear
Our own choices, typical of the class: 0.14 m ground clearance, 205/55 R16 tyres
(0.632 m), the bonnet, windscreen, roof and liftback lines below, and no mirrors (the
lorry it follows has none either).

The body is two convex hulls of spheres, the lower body and the glasshouse, joined, with
the wheel arches cut out. The wheels are separate solids, one per wheel, sitting in the
arches with a 44 mm gap and 10 mm into the ground.

Output (metres; x forward, y left, z up; ground z = 0; the front bumper's foremost
point at x = 0, the car extending to x = -4.689; centred on y = 0):
  geometry/car.stl         body
  geometry/car_wheels.stl  four wheels
  geometry/car_build.json, geometry/preview_car_*.png

Run:  python3 scripts/build_car.py   (from the case directory; Allrun does it)
"""
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np
import manifold3d as m3d

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "geometry"

SPEC = OrderedDict(source="Skoda Octavia 2020-2024, autotijd.be dimensions page, read 9 Oct 2026",
                   length=4.689, width=1.829, height=1.470, wheelbase=2.686,
                   front_overhang=0.910, rear_overhang=1.094, track_front=1.543, track_rear=1.535)
OWN = OrderedDict(ground_clearance=0.14, tyre="205/55 R16", tyre_d=0.632, tyre_w=0.205,
                  arch_r=0.36, arch_inner_y=0.60, beltline=0.95, bonnet_nose=0.76, boot_lip=1.02,
                  roof_half_width=0.65, mirrors=False)
SINK = 0.010


def spheres(points, r, seg=48):
    out = []
    for x, y, z in points:
        for s in ((1, -1) if y else (1,)):
            out.append(m3d.Manifold.sphere(r, seg).translate((x, s * y, z)))
    return out


def tyre(d, w, x, y, seg=96):
    """A tyre with rounded shoulders and a hub face, axle along y, centred at (x, y, d/2 - SINK)."""
    R, r_in, sh = d / 2, 0.32 * d, 0.03
    prof = [(r_in, -w / 2), (R - sh, -w / 2)]
    for a in np.linspace(-np.pi / 2, 0, 7)[1:]:
        prof.append((R - sh + sh * np.cos(a), -w / 2 + sh + sh * np.sin(a)))
    for a in np.linspace(0, np.pi / 2, 7)[1:]:
        prof.append((R - sh + sh * np.cos(a), w / 2 - sh + sh * np.sin(a)))
    prof += [(r_in, w / 2)]
    P = np.array(prof)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    P = P if area > 0 else P[::-1]
    t = m3d.Manifold.revolve(m3d.CrossSection([P]), seg).rotate((90, 0, 0))
    hub = m3d.Manifold.cylinder(w * 0.9, r_in + 0.01, -1, seg, True).rotate((90, 0, 0))
    return (t + hub).translate((x, y, R - SINK))


def main():
    L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
    gc, belt = OWN["ground_clearance"], OWN["beltline"]
    r = 0.18                                   # lower body's corner radius
    ys = W / 2 - r                             # side spheres reach the full width
    xf, xr = -r, -L + r                        # sphere centres at the bumpers
    lower = m3d.Manifold.batch_hull(spheres([
        (xf, 0.62, gc + 0.22),                 # nose, low and rounded in plan
        (xf - 0.10, 0.62, OWN["bonnet_nose"] - r),
        (-0.55, ys, gc + r),                   # flat floor
        (-4.30, ys, gc + r),
        (-0.70, ys, 0.80 - r),                 # bonnet rising to the windscreen
        (-1.70, ys, belt - r),
        (-3.60, ys, belt - r),                 # beltline
        (xr, ys - 0.04, OWN["boot_lip"] - r),  # tail, slightly tucked in plan
        (xr, ys - 0.04, gc + 0.26),            # rear bumper's lower edge rises
    ], r))
    rg = 0.10                                  # glasshouse radius
    yb, yt = W / 2 - 0.08 - rg, OWN["roof_half_width"] - rg
    glass = m3d.Manifold.batch_hull(spheres([
        (-1.62, yb, belt - 0.10),              # cowl, at the windscreen's foot
        (-2.55, yt, H - rg),                   # windscreen top / roof front
        (-3.30, yt, H - rg),                   # roof rear
        (-4.42, yb - 0.04, OWN["boot_lip"] - 0.07),  # liftback's lip
    ], rg))
    body = lower + glass
    xa = (-SPEC["front_overhang"], -SPEC["front_overhang"] - SPEC["wheelbase"])
    zc = OWN["tyre_d"] / 2 - SINK
    for x in xa:
        for s in (1, -1):
            arch = m3d.Manifold.cylinder(1.0, OWN["arch_r"], -1, 96).rotate((-90, 0, 0)).translate(
                (x, OWN["arch_inner_y"] if s > 0 else -OWN["arch_inner_y"] - 1.0, zc))
            body = body - arch
    wheels = OrderedDict()
    for name, x, tr in (("front", xa[0], SPEC["track_front"]), ("rear", xa[1], SPEC["track_rear"])):
        for side, s in (("left", 1), ("right", -1)):
            wheels[f"wheel_{name}_{side}"] = tyre(OWN["tyre_d"], OWN["tyre_w"], x, s * tr / 2)

    import trimesh

    def tri(M):
        mm = M.to_mesh()
        return np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts).astype(int)
    V, Tt = tri(body)
    mt = trimesh.Trimesh(V, Tt, process=True)
    res = OrderedDict(published=SPEC, own_choices=OWN, tyre_sink_m=SINK,
                      axles_x=list(xa),
                      body=dict(triangles=len(Tt), watertight=bool(mt.is_watertight),
                                bodies=len(mt.split(only_watertight=False)),
                                bbox_min=V.min(0).tolist(), bbox_max=V.max(0).tolist(),
                                volume_m3=float(mt.volume)),
                      wheels={})
    solids = [("car", V, Tt)]
    WV = []
    for k, w in wheels.items():
        v, t = tri(w)
        mw = trimesh.Trimesh(v, t, process=True)
        res["wheels"][k] = dict(watertight=bool(mw.is_watertight), bbox_min=v.min(0).tolist(),
                                bbox_max=v.max(0).tolist(),
                                gap_to_body_m=float(mt.nearest.on_surface(v[::7])[1].min()))
        solids.append((k, v, t))
        WV.append((v, t))
    allV = np.vstack([V] + [v for v, _ in WV])
    res["overall_bbox_min"], res["overall_bbox_max"] = allV.min(0).tolist(), allV.max(0).tolist()
    import shapely
    polys = []
    for v, t in [(V, Tt)] + WV:
        P = v[:, [1, 2]][t]
        d1, d2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
        keep = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) > 1e-12
        polys.append(shapely.polygons(np.concatenate([P[keep], P[keep][:, :1]], axis=1)))
    res["frontal_area_m2"] = float(shapely.union_all(np.concatenate(polys), grid_size=1e-5).area)
    # the centreline section, which is what the side panels cut
    sec = mt.section(plane_origin=(0, 0, 0), plane_normal=(0, 1, 0))
    if sec is not None:
        pts = np.asarray(sec.vertices)
        res["centreline_section"] = dict(x=[float(pts[:, 0].min()), float(pts[:, 0].max())],
                                         z=[float(pts[:, 2].min()), float(pts[:, 2].max())])
    write_stl(OUT / "car.stl", solids[:1])
    write_stl(OUT / "car_wheels.stl", solids[1:])
    (OUT / "car_build.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    previews([(V, Tt, "#c23b22")] + [(v, t, "#333333") for v, t in WV])


def write_stl(path, solids):
    with open(path, "w") as f:
        for name, V, T in solids:
            f.write(f"solid {name}\n")
            P = V[T]
            n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-30)
            for (a, b, c), nn in zip(P, n):
                f.write(f" facet normal {nn[0]:.6e} {nn[1]:.6e} {nn[2]:.6e}\n  outer loop\n")
                for p in (a, b, c):
                    f.write(f"   vertex {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
                f.write("  endloop\n endfacet\n")
            f.write(f"endsolid {name}\n")


def previews(items):
    try:
        import pyvista as pv
    except ImportError:
        print("PyVista not found: previews skipped")
        return
    pv.OFF_SCREEN = True
    for view, (cdir, up) in {"side": ((0, -1, 0), (0, 0, 1)), "front": ((1, 0, 0), (0, 0, 1)),
                             "top": ((0, 0, 1), (1, 0, 0)), "iso": ((0.7, -0.6, 0.4), (0, 0, 1))}.items():
        p = pv.Plotter(off_screen=True, window_size=(1600, 900))
        p.set_background("white")
        for V, T, c in items:
            faces = np.c_[np.full(len(T), 3), T].ravel()
            p.add_mesh(pv.PolyData(V, faces), color=c, smooth_shading=False)
        c = np.array([-SPEC["length"] / 2, 0, 0.7])
        p.camera.focal_point = c
        p.camera.position = c + 20 * np.array(cdir, float)
        p.camera.up = up
        if view != "iso":
            p.enable_parallel_projection()
        p.reset_camera()
        p.screenshot(str(OUT / f"preview_car_{view}.png"))
        p.close()


if __name__ == "__main__":
    main()
