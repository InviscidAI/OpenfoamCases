#!/usr/bin/env python3
"""Build a man in a skydiver's belly-down spread ("box" position), as one closed
CFD surface.

The figure is MakeHuman's CC0 base mesh, morphed, posed by linear blend
skinning and smoothed with the functions of scripts/build_runners.py, the
builder of marathonDrafting's runners (as in cyclistBehindLorry): a 1.75 m male
with marathonDrafting's pacer's macro values.  Only the pose is new:

  * the back arched (spine extended 20 degrees over spine05..spine02) and the
    head raised to look ahead;
  * upper arms out to the side, 10 degrees above the shoulder line and 15
    degrees behind the body's frontal plane; elbows bent about 90 degrees, so
    the forearms point towards the head, hands a little outside it; fingers
    straight;
  * thighs spread 22 degrees each side and extended 10 degrees, knees bent 50
    degrees, feet pointed.

Then the body is turned face down and levelled so its trunk is horizontal.

Output (metres; x towards the head, y the figure's left, z up, so the belly
faces -z and the fall is along -z; the origin is the figure's volume centroid):
  geometry/faller.stl          one closed surface, solid 'faller'
  geometry/faller_build.json   measures and checks
  geometry/preview_faller_*.png

Run:  python3 scripts/build_faller.py   (Allrun runs it if geometry/faller.stl is missing)
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
sys.path.insert(0, str(HERE))
import build_runners as br  # noqa: E402

OUT = CASE / "geometry"

FIGURE = dict(gender=1.0, age=0.5, muscle=0.65, weight=0.45,
              african=1 / 3, asian=1 / 3, caucasian=1 / 3, height_m=1.75)

# Pose, degrees.  MakeHuman frame: x = figure's left, y up, z forward (belly).
POSE = OrderedDict(
    spine_extension=20.0,                  # backward bend of the trunk, total
    spine_share=(0.35, 0.30, 0.20, 0.15),  # of it, spine05..spine02
    neck_extension=30.0,                   # head raised, over neck01..03
    arm_above_shoulder=10.0,               # upper arm above the horizontal, towards the head
    arm_behind=15.0,                       # upper arm behind the frontal plane
    forearm=(0.20, 1.0, -0.20),            # forearm direction (out, up, forward), unnormalised
    thigh_out=22.0,                        # each thigh, out from the vertical
    thigh_back=10.0,                       # each thigh, behind the vertical (hip extension)
    knee_flex=50.0,
    foot_point=35.0,                       # plantar flexion, toes pointed
)
DENSITY = 1000.0   # kg/m3, for the mass (the human body is 985-1070 depending on breath)


def chain_world(skel, R, b):
    W = np.identity(3)
    chain = []
    while b:
        chain.append(b)
        b = skel.defs[b].get("parent")
    for c in reversed(chain):
        if c in R:
            W = W @ R[c]
    return W


def pose_rotations(skel, coords, P):
    """Bone rotations in rest-world axes, composed down the hierarchy, as in
    build_runners.pose_rotations (whose signature this keeps)."""
    J = lambda b, end="head": skel.joint(skel.defs[b][end], coords)
    X = br.X
    R = {}
    for b, s in zip(("spine05", "spine04", "spine03", "spine02"), P["spine_share"]):
        R[b] = br.rot(X, -P["spine_extension"] * s)       # -x rotation tilts 'up' backwards
    for b in ("neck01", "neck02", "neck03"):
        R[b] = br.rot(X, -P["neck_extension"] / 3)
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        # ---- legs: world directions (the pelvis is not rotated) --------------
        hip, knee, ankle = J(f"upperleg01.{side}"), J(f"lowerleg01.{side}"), J(f"foot.{side}")
        u0, s0 = knee - hip, ankle - knee
        rest_dfront = np.degrees(np.arctan2(sgn * s0[0], -s0[1]) - np.arctan2(sgn * u0[0], -u0[1]))
        u1 = br.sag_dir(sgn * P["thigh_out"], -P["thigh_back"])
        s1 = br.sag_dir(sgn * (P["thigh_out"] + rest_dfront), -P["thigh_back"] - P["knee_flex"])
        Rt = br.frame_match(u0, X, u1, X)
        Rs = br.frame_match(s0, X, s1, X)
        R[f"upperleg01.{side}"] = Rt
        R[f"lowerleg01.{side}"] = Rt.T @ Rs
        R[f"foot.{side}"] = br.rot(X, P["foot_point"])     # +x rotation points the toes
        # ---- arms: world targets, undone through the arched spine ---------------
        sh, el, wr = J(f"upperarm01.{side}"), J(f"lowerarm01.{side}"), J(f"wrist.{side}")
        a0, f0 = el - sh, wr - el
        h0 = br.normalize(np.cross(a0, f0))
        e, b_ = np.radians(P["arm_above_shoulder"]), np.radians(P["arm_behind"])
        a1 = br.normalize(np.array([sgn * np.cos(e) * np.cos(b_), np.sin(e), -np.cos(e) * np.sin(b_)]))
        fx, fy, fz = P["forearm"]
        f1 = br.normalize(np.array([sgn * fx, fy, fz]))
        h1 = br.normalize(np.cross(a1, f1))
        if np.dot(h1, h0) < 0:
            h1 = -h1
        Wa = br.frame_match(a0, h0, a1, h1)
        Wf = br.frame_match(f0, h0, f1, h1)
        Wpar = chain_world(skel, R, f"shoulder01.{side}")
        R[f"upperarm01.{side}"] = Wpar.T @ Wa
        R[f"lowerarm01.{side}"] = Wa.T @ Wf
    return R


def to_fall_frame(V):
    """Standing output frame (x belly, y left, z head) -> fall frame (x head, y left,
    z = back, so the belly faces -z)."""
    return np.c_[V[:, 2], V[:, 1], -V[:, 0]]


def write_stl(path, name, V, T):
    with open(path, "w") as f:
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


def previews(V, T):
    import pyvista as pv
    pv.OFF_SCREEN = True
    m = br._polydata(V, T)
    views = {"side": ((0, -1, 0), (0, 0, 1)), "below": ((0, 0, -1), (1, 0, 0)),
             "head_on": ((1, 0, 0), (0, 0, 1)), "iso": ((0.5, -0.7, -0.5), (0, 0, 1))}
    for view, (cdir, up) in views.items():
        p = pv.Plotter(off_screen=True, window_size=(1200, 900))
        p.set_background("white")
        p.add_mesh(m, color="#c9a27e", smooth_shading=True)
        p.add_axes()
        p.camera.focal_point = (0, 0, 0)
        p.camera.position = 5 * np.array(cdir, float)
        p.camera.up = up
        if view != "iso":
            p.enable_parallel_projection()
        p.reset_camera()
        p.screenshot(str(OUT / f"preview_faller_{view}.png"))
        p.close()


def build_figure(base, F, G, skel):
    """The steps of build_runners.build_figure that apply here: morph to the
    height, pose, skin, Catmull-Clark once, decimate, remove self-intersections.
    Returns the standing output frame (x belly, y left, z head, metres)."""
    params = {k: v for k, v in FIGURE.items() if k != "height_m"}
    Q = br.body_quads(F, G)
    bv = np.unique(Q)
    h_param, h_cm = br.solve_height(base, bv, params, 100 * FIGURE["height_m"])
    V = br.morph(base, br.macro_vals(height=h_param, **params))
    skel.build(V)
    R = pose_rotations(skel, V, POSE)
    PV = skel.pose_matrices(R)
    posed = skel.skin(V, PV)
    Vb, Qb, _ = br.compact(posed, Q)
    Vs, Qs = br.catmull_clark(Vb, Qb)
    Vd, Td = br.decimate(Vs, br.triangulate_quads(Vs, Qs), br.TARGET_TRIS)
    Vo = br.to_output_frame(Vd)
    pre = int(br.self_intersections(Vo, Td).sum())
    Vo2, _ = br.fix_self_intersections(Vo, Td)

    def pj(b):
        p = skel.joint(skel.defs[b]["head"], V)
        return br.to_output_frame((PV[b] @ np.r_[p, 1.0])[None, :3])[0]
    trunk = pj("neck01") - pj("spine05")
    res = dict(standing_height_m=h_cm / 100, self_intersections_before_fix=pre,
               fix_max_move_m=float(np.linalg.norm(Vo2 - Vo, axis=1).max()),
               trunk_line_from_vertical=float(np.degrees(np.arctan2(trunk[0], trunk[2]))),
               joints={b: pj(b).tolist() for b in ("spine05", "neck01", "head", "upperleg01.L",
                                                   "lowerleg01.L", "foot.L", "upperarm01.L",
                                                   "lowerarm01.L", "wrist.L")})
    return Vo2, Td, res


def main():
    import trimesh
    OUT.mkdir(parents=True, exist_ok=True)
    for rel in br.FETCH:
        br.fetch(rel)
    base, F, G = br.load_obj(br.fetch(br.D + "3dobjs/base.obj"))
    skel = br.Skeleton(br.fetch(br.D + "rigs/default.mhskel"), br.fetch(br.D + "rigs/default_weights.mhw"), len(base))
    Vs, T, res = build_figure(base, F, G, skel)

    V = to_fall_frame(Vs)
    # level the trunk: the lumbar-base-to-neck line (marathonDrafting's trunk line, measured from
    # the vertical in the standing frame, + = towards the belly) turned horizontal
    tilt = -res["trunk_line_from_vertical"]
    V = V @ br.rot([0, 1, 0], tilt).T
    m = trimesh.Trimesh(V, T, process=False)
    V = V - m.center_mass
    m = trimesh.Trimesh(V, T, process=False)

    def area(axis):
        return br.projected_area(V, T, axis)
    mass = float(m.volume * DENSITY)
    report = OrderedDict(
        source=f"MakeHuman CC0 ({br.REPO}@{br.COMMIT[:12]}), posed by our own script",
        figure=FIGURE, pose=POSE,
        trunk_tilt_removed_deg=float(tilt),
        bbox_min=V.min(0).tolist(), bbox_max=V.max(0).tolist(),
        bbox_size=(V.max(0) - V.min(0)).tolist(),
        triangles=int(len(T)), watertight=bool(m.is_watertight),
        winding_consistent=bool(m.is_winding_consistent), outward=bool(m.volume > 0),
        bodies=int(len(m.split(only_watertight=False))),
        self_intersecting_faces=int(br.self_intersections(V, T).sum()),
        volume_m3=float(m.volume), density_kg_m3=DENSITY, mass_kg=mass,
        area_m2=float(m.area),
        plan_area_m2_seen_from_below=area(2),
        side_area_m2=area(1), head_on_area_m2=area(0),
        min_edge_m=float(m.edges_unique_length.min()), mean_edge_m=float(m.edges_unique_length.mean()),
        standing=res,
    )
    write_stl(OUT / "faller.stl", "faller", V, T)
    (OUT / "faller_build.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    previews(V, T)


if __name__ == "__main__":
    main()
