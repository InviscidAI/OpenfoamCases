#!/usr/bin/env python3
"""Build a generic European articulated lorry as closed CFD surfaces.

No brand and no downloaded model: a cab-over tractor and a 13.6 m box
semi-trailer from published limits and typical dimensions.
  * overall length 16.5 m, width 2.55 m, height 4.0 m: the maxima for an
    articulated vehicle in Council Directive 96/53/EC, Annex I
  * a 13.6 m box trailer with its deck at 1.20 m, three axles 1.31 m apart with
    single 385/65 R22.5 tyres (1.07 m), the rear axle 3.0 m from the rear doors
  * a rear underrun bar 0.45-0.57 m above the ground, 0.12 m in from the rear
    (UN Regulation 58: at most 450 mm ground clearance)
  * a 4x2 tractor: cab 2.3 m long, roof deflector up to the trailer's height,
    wheelbase 3.7 m, 315/80 R22.5 tyres, twin tyres on the drive axle
  * no side skirts or side guards on the trailer: the space under it is open

Output (metres; x forward, y left, z up; ground z = 0; the trailer's rear
doors at x = 0, the lorry's front at x = +16.5; centred on y = 0):
  geometry/truck.stl         body (cab, chassis, tanks, trailer, legs, axles, underrun bar)
  geometry/truck_wheels.stl  wheels, one solid per axle; they overlap their axles
                             and sit 10 mm into the ground
  geometry/truck_build.json, geometry/preview_truck_*.png

Run:  python3 scripts/build_truck.py   (from the case directory; Allrun does it)
"""
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np
import manifold3d as m3d

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "geometry"

L, W, H = 16.5, 2.55, 4.0
TR = OrderedDict(length=13.6, deck=1.20, axle_from_rear=(3.0, 4.31, 5.62), track=2.04,
                 tyre_d=1.072, tyre_w=0.385, kingpin_from_front=1.6)
TRACTOR = OrderedDict(cab_len=2.3, gap=0.6, cab_floor=1.15, roof=3.95, front_axle_from_front=1.40,
                      wheelbase=3.70, tyre_d=1.0755, tyre_w=0.315, twin_gap=0.03,
                      front_track=2.06, rear_track_centre=1.86)
SINK = 0.010
UNDERRUN = dict(z=(0.45, 0.57), x=(0.12, 0.24), half_width=1.15)


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return m3d.Manifold.cube(tuple(hi - lo)).translate(tuple(lo))


def rbox(lo, hi, r):
    """Rounded box: hull of corner spheres; r is a scalar or a function (x, y, z) -> radius."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    sph = []
    for cx in (0, 1):
        for cy in (0, 1):
            for cz in (0, 1):
                rr = r(cx, cy, cz) if callable(r) else r
                c = [lo[0] + rr if cx == 0 else hi[0] - rr, lo[1] + rr if cy == 0 else hi[1] - rr,
                     lo[2] + rr if cz == 0 else hi[2] - rr]
                sph.append(m3d.Manifold.sphere(rr, 48).translate(tuple(c)))
    return m3d.Manifold.batch_hull(sph)


def tyre(d, w, x, y, seg=96):
    """A tyre with rounded shoulders and a 0.3 d hub face, axle along y, centred at (x, y, d/2 - SINK)."""
    R, r_in, sh = d / 2, 0.29 * d, 0.06
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
    OUT.mkdir(parents=True, exist_ok=True)
    body, wheels = [], OrderedDict()
    hw = W / 2
    # ---- trailer --------------------------------------------------------------
    tl = TR["length"]
    body.append(rbox((0, -hw, TR["deck"]), (tl, hw, H), 0.03))
    for s in (1, -1):                                         # chassis rails
        body.append(box((0.10, s * 0.57 if s < 0 else 0.43, 0.90), (tl - 0.4, s * 0.43 if s < 0 else 0.57, TR["deck"] + 0.01)))
    for xa in TR["axle_from_rear"]:                           # axles and wheels
        body.append(m3d.Manifold.cylinder(2 * 0.92, 0.075, -1, 32, True).rotate((90, 0, 0))
                    .translate((xa, 0, TR["tyre_d"] / 2 - SINK)))
        wheels[f"trailer_axle_{xa:.2f}"] = (tyre(TR["tyre_d"], TR["tyre_w"], xa, TR["track"] / 2) +
                                            tyre(TR["tyre_d"], TR["tyre_w"], xa, -TR["track"] / 2))
    ax = TR["axle_from_rear"]                                 # suspension under the axle group
    body.append(box((ax[0] - 0.6, -0.57, 0.50), (ax[-1] + 0.6, 0.57, 0.92)))
    x0, x1 = UNDERRUN["x"]                                    # rear underrun protection
    z0, z1 = UNDERRUN["z"]
    body.append(box((x0, -UNDERRUN["half_width"], z0), (x1, UNDERRUN["half_width"], z1)))
    for s in (1, -1):
        body.append(box((x0, min(s * 0.42, s * 0.58), z1 - 0.01), (x1, max(s * 0.42, s * 0.58), 0.91)))
    leg_x = tl - TR["kingpin_from_front"] - 2.4                # landing legs
    for s in (1, -1):
        body.append(box((leg_x - 0.06, s * 0.95 - 0.06, 0.32), (leg_x + 0.06, s * 0.95 + 0.06, TR["deck"] + 0.01)))
        body.append(box((leg_x - 0.15, s * 0.95 - 0.15, 0.27), (leg_x + 0.15, s * 0.95 + 0.15, 0.33)))
    # ---- tractor --------------------------------------------------------------
    T = TRACTOR
    cab_back = L - T["cab_len"]
    assert abs(cab_back - T["gap"] - tl) < 1e-9
    front_axle = L - T["front_axle_from_front"]
    drive_axle = front_axle - T["wheelbase"]
    kingpin = tl - TR["kingpin_from_front"]

    def cab_r(cx, cy, cz):                                    # rounded front, tighter at the back
        if cx == 1:
            return 0.30 if cz == 1 else 0.20
        return 0.06
    body.append(rbox((cab_back, -hw + 0.02, T["cab_floor"]), (L, hw - 0.02, T["roof"]), cab_r))
    body.append(rbox((L - 0.55, -hw + 0.06, 0.32), (L, hw - 0.06, T["cab_floor"] + 0.2), 0.10))  # bumper/grille
    for s in (1, -1):                                          # chassis rails
        body.append(box((drive_axle - 1.2, min(s * 0.43, s * 0.55), 0.70), (L - 0.4, max(s * 0.43, s * 0.55), 1.00)))
    body.append(box((kingpin - 0.6, -1.0, 0.98), (kingpin + 0.6, 1.0, TR["deck"] + 0.01)))   # fifth wheel
    for s in (1, -1):                                          # fuel and battery boxes
        body.append(rbox((drive_axle + 0.80, min(s * 0.50, s * 1.22), 0.45),
                         (front_axle - 0.75, max(s * 0.50, s * 1.22), 1.05), 0.08))
    for xa, half in ((front_axle, 0.95), (drive_axle, 0.80)):
        body.append(m3d.Manifold.cylinder(2 * half, 0.08, -1, 32, True).rotate((90, 0, 0))
                    .translate((xa, 0, T["tyre_d"] / 2 - SINK)))
        for s in (1, -1):                                      # springs: axle to rails
            body.append(box((xa - 0.45, min(s * 0.43, s * 0.55), T["tyre_d"] / 2 - SINK),
                            (xa + 0.45, max(s * 0.43, s * 0.55), 0.71)))
    wheels["tractor_front"] = (tyre(T["tyre_d"], T["tyre_w"], front_axle, T["front_track"] / 2) +
                               tyre(T["tyre_d"], T["tyre_w"], front_axle, -T["front_track"] / 2))
    off = T["tyre_w"] / 2 + T["twin_gap"] / 2
    yc = T["rear_track_centre"] / 2
    wheels["tractor_drive"] = m3d.Manifold.batch_boolean(
        [tyre(T["tyre_d"], T["tyre_w"], drive_axle, s * yc + d) for s in (1, -1) for d in (off, -off)], m3d.OpType.Add)

    truck = m3d.Manifold.batch_boolean(body, m3d.OpType.Add)
    import trimesh

    def tri(M):
        mm = M.to_mesh()
        return np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts).astype(int)
    V, Tt = tri(truck)
    mt = trimesh.Trimesh(V, Tt, process=True)
    res = OrderedDict(directive="96/53/EC Annex I: 16.5 m, 2.55 m, 4.0 m", trailer=TR, tractor=T,
                      underrun=UNDERRUN, tyre_sink_m=SINK,
                      body=dict(triangles=len(Tt), watertight=bool(mt.is_watertight), bodies=len(mt.split(only_watertight=False)),
                                bbox_min=V.min(0).tolist(), bbox_max=V.max(0).tolist(), volume_m3=float(mt.volume)),
                      wheels={})
    solids = [("truck", V, Tt)]
    WV = []
    for k, w in wheels.items():
        v, t = tri(w)
        mw = trimesh.Trimesh(v, t, process=True)
        res["wheels"][k] = dict(watertight=bool(mw.is_watertight), bbox_min=v.min(0).tolist(), bbox_max=v.max(0).tolist())
        solids.append((k, v, t))
        WV.append((v, t))
    allV = np.vstack([V] + [v for v, _ in WV])
    res["overall_bbox_min"], res["overall_bbox_max"] = allV.min(0).tolist(), allV.max(0).tolist()
    # frontal area of body + wheels
    import shapely
    polys = []
    for v, t in [(V, Tt)] + WV:
        P = v[:, [1, 2]][t]
        d1, d2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
        keep = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) > 1e-12
        polys.append(shapely.polygons(np.concatenate([P[keep], P[keep][:, :1]], axis=1)))
    res["frontal_area_m2"] = float(shapely.union_all(np.concatenate(polys), grid_size=1e-5).area)
    res["wheel_overlap_with_body_m3"] = {k: float((truck ^ w).volume()) for k, w in wheels.items()}
    write_stl(OUT / "truck.stl", solids[:1])
    write_stl(OUT / "truck_wheels.stl", solids[1:])
    (OUT / "truck_build.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    previews([(V, Tt, "#b8c4cc")] + [(v, t, "#333333") for v, t in WV])


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
    for view, (cdir, up) in {"side": ((0, -1, 0), (0, 0, 1)), "rear": ((-1, 0, 0), (0, 0, 1)),
                             "iso_rear": ((-0.7, -0.6, 0.35), (0, 0, 1))}.items():
        p = pv.Plotter(off_screen=True, window_size=(1600, 900))
        p.set_background("white")
        for V, T, c in items:
            faces = np.c_[np.full(len(T), 3), T].ravel()
            p.add_mesh(pv.PolyData(V, faces), color=c, smooth_shading=False)
        c = np.array([L / 2, 0, 2.0])
        p.camera.focal_point = c
        p.camera.position = c + 40 * np.array(cdir, float)
        p.camera.up = up
        if view != "iso_rear":
            p.enable_parallel_projection()
        p.reset_camera()
        p.screenshot(str(OUT / f"preview_truck_{view}.png"))
        p.close()


if __name__ == "__main__":
    main()
