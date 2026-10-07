#!/usr/bin/env python3
"""Build a road cyclist on a simplified road bike, as closed CFD surfaces.

The rider is MakeHuman's CC0 base mesh, posed by linear blend skinning with the
functions of scripts/build_runners.py (the builder of the marathonDrafting case's
runners, imported unchanged): a 1.75 m male, seated, hands on the drops, cranks
horizontal (right foot forward). The pose is solved from the bike: hip on the saddle,
ankles from the pedals by two-link inverse kinematics, hands on the drops with the
trunk flexion chosen so the elbows bend 25 degrees. A simple helmet is added.

The bike is built here from published size-56 road geometry (stack 565, reach
385, head tube 120 mm at 73 deg, seat tube 73.5 deg, chainstay 410, BB drop 70, fork offset
45, 172.5 mm cranks, 700x25c tyres): tubes as capsules, wheels as revolved
rim-and-tyre rings without spokes, saddle, bar, hoods, cranks and pedals.

Output (metres, x forward, y left, z up, ground at z = 0, the leading point of
the front tyre at x = 0, centred on y = 0):
  geometry/rider.stl           rider, helmet and bike frame as one closed surface
  geometry/bike_wheels.stl     the two wheels, solids 'front_wheel', 'rear_wheel'
  geometry/rider_build.json    measures and checks
  geometry/preview_rider_*.png

Run:  python3 scripts/build_rider.py   (from the case directory; Allrun does it)
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
import manifold3d as m3d  # noqa: E402

OUT = CASE / "geometry"

FIGURE = dict(gender=1.0, age=0.5, muscle=0.65, weight=0.45,
              african=1 / 3, asian=1 / 3, caucasian=1 / 3, height_m=1.75)

# ----------------------------------------------------------------------------
# Bike, size 56 (metres; x forward, z up; BB-relative unless said otherwise)
# ----------------------------------------------------------------------------
BIKE = OrderedDict(
    stack=0.565, reach=0.385, head_angle=73.0, seat_angle=73.5,
    head_tube=0.120, chainstay=0.410, bb_drop=0.070, fork_offset=0.045,
    crank=0.1725, q_half=0.075, pedal_out=0.055,
    rim_bsd=0.622, rim_depth=0.030, rim_width=0.020, tyre=0.025, tyre_sink=0.003,
    stem=0.110, stem_rise_deg=7.0, spacers=0.035, bar_width=0.42,
    bar_reach=0.080, bar_drop=0.125,
)

# Pose (degrees).  Trunk flexion is solved; these are fixed.
POSE = OrderedDict(
    pelvis_tilt=20.0,          # root rotated forward (anterior pelvic tilt)
    spine_share=(0.40, 0.25, 0.20, 0.15),   # of the trunk flexion, spine05..spine02
    neck_from_vertical=50.0,   # neck (neck01 to the skull base), forward of the vertical
    head_from_vertical=35.0,   # head axis, forward of the vertical: eyes ahead
    elbow_target=25.0,         # elbow flexion the trunk flexion is solved for
    grip="drops",              # hands on the lower, straight part of the bar
    right_sole_toe_down=10.0,  # crank forward (3 o'clock)
    left_sole_toe_down=30.0,   # crank back (9 o'clock)
    hip_behind_saddle=0.030,   # hip joint behind the seat-tube/saddle point
    seat_sink=0.015,           # buttocks pressed into the saddle top (solved hip height)
    saddle_height=0.720,       # BB centre to saddle top, along the seat tube
    pedal_top=0.012,           # pedal top above the spindle axis
    foot_sink=0.004,           # sole pressed into the pedal top
    grip_beyond_wrist=0.070,   # palm centre beyond the wrist, along the forearm
    finger_curl=(55.0, 60.0, 40.0),
    thumb_curl=(10.0, 25.0, 25.0),
)

TARGET_TRIS = 60000
SEG = 48     # circular segments for tubes


def rad(d):
    return np.radians(d)


def bike_points():
    b = BIKE
    R = b["rim_bsd"] / 2 + b["tyre"]                          # outer radius 0.336
    bb_z = R - b["bb_drop"]
    s_head = np.array([-np.cos(rad(b["head_angle"])), 0, np.sin(rad(b["head_angle"]))])
    s_seat = np.array([-np.cos(rad(b["seat_angle"])), 0, np.sin(rad(b["seat_angle"]))])
    BB = np.array([0.0, 0.0, 0.0])
    rear = np.array([-np.sqrt(b["chainstay"] ** 2 - b["bb_drop"] ** 2), 0, b["bb_drop"]])
    ht_top = np.array([b["reach"], 0, b["stack"]])
    ht_bot = ht_top - b["head_tube"] * s_head
    # front axle: on z = drop, fork offset normal to the steering axis
    t = (b["bb_drop"] - ht_top[2]) / s_head[2]
    on_axis = ht_top + t * s_head
    front = on_axis + np.array([b["fork_offset"] / np.sin(rad(b["head_angle"])), 0, 0])
    stem_base = ht_top + b["spacers"] * s_head
    bar = stem_base + b["stem"] * np.array([np.cos(rad(b["stem_rise_deg"])), 0, np.sin(rad(b["stem_rise_deg"]))])
    drop_grip = bar + np.array([0.010, 0, -b["bar_drop"] + 0.025])   # palm centre on the drops
    saddle = POSE["saddle_height"] * s_seat
    seat_top = 0.54 * s_seat
    return OrderedDict(R=R, bb_z=bb_z, s_head=s_head, s_seat=s_seat, BB=BB, rear=rear, front=front,
                       ht_top=ht_top, ht_bot=ht_bot, stem_base=stem_base, bar=bar, drop_grip=drop_grip,
                       saddle=saddle, seat_top=seat_top)


# ----------------------------------------------------------------------------
# Manifold helpers
# ----------------------------------------------------------------------------
def to_m(V, T):
    mesh = m3d.Mesh(vert_properties=np.asarray(V, np.float32), tri_verts=np.asarray(T, np.uint32))
    M = m3d.Manifold(mesh)
    assert M.status() == m3d.Error.NoError, M.status()
    return M


def from_m(M):
    mesh = M.to_mesh()
    return np.asarray(mesh.vert_properties)[:, :3].astype(float), np.asarray(mesh.tri_verts).astype(int)


def capsule(p, q, r, seg=SEG):
    a = m3d.Manifold.sphere(r, seg).translate(tuple(map(float, p)))
    b = m3d.Manifold.sphere(r, seg).translate(tuple(map(float, q)))
    return m3d.Manifold.batch_hull([a, b])


def tube_path(pts, r, seg=SEG):
    return m3d.Manifold.batch_boolean([capsule(pts[i], pts[i + 1], r, seg) for i in range(len(pts) - 1)],
                                      m3d.OpType.Add)


def rounded_box(lo, hi, r, seg=24):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    sph = []
    for x in (lo[0] + r, hi[0] - r):
        for y in (lo[1] + r, hi[1] - r):
            for z in (lo[2] + r, hi[2] - r):
                sph.append(m3d.Manifold.sphere(r, seg).translate((x, y, z)))
    return m3d.Manifold.batch_hull(sph)


def ring(profile_rz, seg=180):
    """Revolve a closed (radius, axial) profile about the y axis (an axle along y)."""
    cs = m3d.CrossSection([np.asarray(profile_rz, float)])
    M = m3d.Manifold.revolve(cs, seg)          # axis = z after revolve
    return M.rotate((90.0, 0.0, 0.0))          # z -> -y: axle along y


def wheel_profile():
    """Rim and tyre section, (radius, axial) in metres: a box-section rim from the
    rim's inner edge to the bead seat, and a round 25 mm tyre on the bead seat."""
    b = BIKE
    r_in = b["rim_bsd"] / 2 - b["rim_depth"]
    r_bead = b["rim_bsd"] / 2
    w = b["rim_width"] / 2
    tr = b["tyre"] / 2
    c = r_bead + tr
    arc = [(c + tr * np.cos(a), tr * np.sin(a)) for a in np.linspace(-np.pi * 0.62, np.pi * 0.62, 33)]
    prof = [(r_in, -0.004), (r_bead - 0.012, -w), (r_bead, -w)] + arc + \
           [(r_bead, w), (r_bead - 0.012, w), (r_in, 0.004)]
    P = np.array(prof)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P if area > 0 else P[::-1]


# ----------------------------------------------------------------------------
# Pose
# ----------------------------------------------------------------------------
X, Y, Z = np.eye(3)            # MakeHuman frame: x left, y up, z forward


def mh(v):                     # output (x fwd, y left, z up, m) -> MH (x left, y up, z fwd, dm)
    v = np.asarray(v, float)
    return 10.0 * np.array([v[1], v[2], v[0]])


def out(v):
    v = np.asarray(v, float)
    return 0.1 * np.array([v[2], v[0], v[1]])


def two_link(hip, target, a, b, pole):
    """Knee/elbow position for a two-link chain from hip to target, lengths a, b,
    bending towards pole (a direction)."""
    d = target - hip
    L = np.linalg.norm(d)
    L = min(L, a + b - 1e-6)
    u = d / np.linalg.norm(d)
    x = (a * a - b * b + L * L) / (2 * L)
    h = np.sqrt(max(a * a - x * x, 0.0))
    p = pole - np.dot(pole, u) * u
    p = p / np.linalg.norm(p)
    return hip + x * u + h * p


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


def solve_pose(skel, V, flex, targets_fn):
    """flex: total spine flexion (deg).  targets_fn(posed joints) -> dict of
    world targets (MH frame) for ankles, grips."""
    P = POSE
    J = lambda b, end="head": skel.joint(skel.defs[b][end], V)
    R = {}
    R["root"] = br.rot(X, P["pelvis_tilt"])
    for b, sh in zip(("spine05", "spine04", "spine03", "spine02"), P["spine_share"]):
        R[b] = br.rot(X, flex * sh)
    # neck and head: all rotations so far are pitches about MH x, so angles add
    tilt = lambda v: np.degrees(np.arctan2(v[2], v[1]))        # forward of vertical
    W_sp = chain_world(skel, R, "spine01")
    pitch_sp = np.degrees(np.arctan2(W_sp[2, 1], W_sp[1, 1]))
    k = (P["neck_from_vertical"] - tilt(J("head") - J("neck01")) - pitch_sp) / 3
    for b in ("neck01", "neck02", "neck03"):
        R[b] = br.rot(X, k)
    R["head"] = br.rot(X, P["head_from_vertical"] - tilt(J("head", "tail") - J("head")) - pitch_sp - 3 * k)
    PV = skel.pose_matrices(R)
    pj = lambda b: (PV[b] @ np.r_[J(b), 1.0])[:3]
    tg = targets_fn(pj)
    info = {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        # legs
        hip, knee, ank = J(f"upperleg01.{side}"), J(f"lowerleg01.{side}"), J(f"foot.{side}")
        a, b = np.linalg.norm(knee - hip), np.linalg.norm(ank - knee)
        hip_p = pj(f"upperleg01.{side}")
        ank_t = tg[f"ankle.{side}"]
        pole = 10 * np.array([0.0, 0.6, 1.0])        # knee up and forward (MH: y up, z fwd)
        knee_t = two_link(hip_p, ank_t, a, b, pole)
        u0, s0 = knee - hip, ank - knee
        Wt = br.frame_match(u0, X, knee_t - hip_p, X)
        Ws = br.frame_match(s0, X, ank_t - knee_t, X)
        Wpar = chain_world(skel, R, f"pelvis.{side}")
        R[f"upperleg01.{side}"] = Wpar.T @ Wt
        R[f"lowerleg01.{side}"] = Wt.T @ Ws
        toe = P["right_sole_toe_down"] if side == "R" else P["left_sole_toe_down"]
        Wf = br.rot(X, toe)
        R[f"foot.{side}"] = Ws.T @ Wf
        info[f"knee_flex.{side}"] = float(180 - br.angle(hip_p - knee_t, ank_t - knee_t))
        # arms
        sh, el, wr = J(f"upperarm01.{side}"), J(f"lowerarm01.{side}"), J(f"wrist.{side}")
        a0, f0 = el - sh, wr - el
        a, b = np.linalg.norm(a0), np.linalg.norm(f0) + 10 * P["grip_beyond_wrist"]
        sh_p = pj(f"upperarm01.{side}")
        g = tg[f"grip.{side}"]
        pole = 10 * np.array([sgn * 0.7, -0.5, -0.3])  # elbow out, down, back
        el_t = two_link(sh_p, g, a, b, pole)
        f_dir = (g - el_t) / np.linalg.norm(g - el_t)
        wr_t = el_t + np.linalg.norm(f0) * f_dir
        h0 = br.normalize(np.cross(a0, f0))
        h1 = br.normalize(np.cross(el_t - sh_p, wr_t - el_t))
        Wa = br.frame_match(a0, h0, el_t - sh_p, h1)
        Wf_ = br.frame_match(f0, h0, wr_t - el_t, h1)
        Wpar = chain_world(skel, R, f"shoulder01.{side}")
        R[f"upperarm01.{side}"] = Wpar.T @ Wa
        R[f"lowerarm01.{side}"] = Wa.T @ Wf_
        info[f"elbow_flex.{side}"] = float(180 - br.angle(sh_p - el_t, g - el_t))
        info[f"grip_reach_short.{side}"] = float(max(0.0, np.linalg.norm(g - sh_p) - (a + b)) / 10)
        for f in range(1, 6):
            curls = P["thumb_curl"] if f == 1 else P["finger_curl"]
            for k in range(3):
                bn = f"finger{f}-{k + 1}.{side}"
                R[bn] = br.rot(skel.rest[bn][:3, 0], curls[k])
    return R, info


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for rel in br.FETCH:
        br.fetch(rel)
    base, F, G = br.load_obj(br.fetch(br.D + "3dobjs/base.obj"))
    skel = br.Skeleton(br.fetch(br.D + "rigs/default.mhskel"), br.fetch(br.D + "rigs/default_weights.mhw"), len(base))
    params = {k: v for k, v in FIGURE.items() if k != "height_m"}
    Q = br.body_quads(F, G)
    bv = np.unique(Q)
    h_param, h_cm = br.solve_height(base, bv, params, 100 * FIGURE["height_m"])
    V = br.morph(base, br.macro_vals(height=h_param, **params))
    skel.build(V)
    J = lambda b, end="head": skel.joint(skel.defs[b][end], V)

    bk = bike_points()
    P = POSE
    # foot geometry at rest (output frame, metres): ankle relative to the ball's sole point
    Vo_rest = br.to_output_frame(V[bv])
    sole_z = Vo_rest[:, 2].min()

    def ankle_target(side, spindle, toe_down):
        ank = out(J(f"foot.{side}"))
        ball = out(J(f"toe1-1.{side}"))
        ball_sole = np.array([ball[0], ball[1], sole_z])
        v = ank - ball_sole
        c_, s_ = np.cos(rad(toe_down)), np.sin(rad(toe_down))
        Ry = np.array([[c_, 0, s_], [0, 1, 0], [-s_, 0, c_]])
        v = Ry @ v               # heel up (ankle raised) for toe-down > 0
        contact = spindle + np.array([0, 0, P["pedal_top"] - P["foot_sink"]])
        return contact + v, ball[1]

    def make_targets(flex, hip_c):
        def fn(pj):
            hipc_p = 0.5 * (out(pj("upperleg01.L")) + out(pj("upperleg01.R")))
            shift = hip_c - hipc_p          # posed output frame -> BB frame
            tg = {}
            for side, sgn in (("L", 1.0), ("R", -1.0)):
                fwd = 1.0 if side == "R" else -1.0
                foot_y = sgn * (BIKE["q_half"] + BIKE["pedal_out"])
                spindle = np.array([fwd * BIKE["crank"], foot_y, 0.0])
                toe = P["right_sole_toe_down"] if side == "R" else P["left_sole_toe_down"]
                a_t, _ = ankle_target(side, spindle, toe)
                tg[f"ankle.{side}"] = mh(a_t - shift)
                grip = bk["drop_grip"] + np.array([0, sgn * BIKE["bar_width"] / 2, 0])
                tg[f"grip.{side}"] = mh(grip - shift)
            return tg
        return fn

    def solve_all(hip_c):
        """Trunk flexion for the target elbow bend, by bisection."""
        lo, hi = 0.0, 80.0
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            R, info = solve_pose(skel, V, mid, make_targets(mid, hip_c))
            e = 0.5 * (info["elbow_flex.L"] + info["elbow_flex.R"])
            short = info["grip_reach_short.L"] + info["grip_reach_short.R"]
            # more flexion brings the shoulders forward and down: elbows bend more
            if short > 0 or e < P["elbow_target"]:
                lo = mid
            else:
                hi = mid
        flex = 0.5 * (lo + hi)
        R, info = solve_pose(skel, V, flex, make_targets(flex, hip_c))
        PV = skel.pose_matrices(R)
        return R, info, flex, PV, skel.skin(V, PV)

    # hip height: the buttocks sink seat_sink into the saddle top (coarse posed mesh)
    saddle_z = bk["saddle"][2]
    hip_above, sink_log = 0.10, []
    for _ in range(4):
        hip_c = bk["saddle"] + np.array([-P["hip_behind_saddle"], 0, hip_above])
        R, info, flex, PV, posed = solve_all(hip_c)
        pj = lambda b, end="head": out((PV[b] @ np.r_[J(b, end), 1.0])[:3])
        sh = hip_c - 0.5 * (pj("upperleg01.L") + pj("upperleg01.R"))
        C = br.to_output_frame(posed[bv]) + sh
        sx = bk["saddle"][0]
        m = (np.abs(C[:, 1]) < 0.06) & (C[:, 0] > sx - 0.12) & (C[:, 0] < sx + 0.03) & (C[:, 2] > hip_c[2] - 0.3)
        d = hip_c[2] - C[m, 2].min()
        sink_log.append((hip_above, float(saddle_z - C[m, 2].min())))
        if abs(saddle_z - C[m, 2].min() - P["seat_sink"]) < 5e-4:
            break
        hip_above = d - P["seat_sink"]

    # smooth closed body surface, as 08
    Vb, Qb, _ = br.compact(posed, Q)
    Vs, Qs = br.catmull_clark(Vb, Qb)
    Ts = br.triangulate_quads(Vs, Qs)
    Vd, Td = br.decimate(Vs, Ts, TARGET_TRIS)
    Vo = br.to_output_frame(Vd)
    pre_fix = int(br.self_intersections(Vo, Td).sum())
    Vo, fix_log = br.fix_self_intersections(Vo, Td)

    hipc_p = 0.5 * (pj("upperleg01.L") + pj("upperleg01.R"))
    shift = hip_c - hipc_p
    Vo = Vo + shift
    PJ = lambda b, end="head": pj(b, end) + shift

    # ---- helmet: an ellipsoid on the cranium, cut above the brow, posed with the head
    Mh = PV["head"]
    def head_to_world(p_out_rest):
        return out((Mh @ np.r_[mh(p_out_rest), 1.0])[:3]) + shift
    centre_rest = np.array([0.045, 0.0, 0.865])
    sph = m3d.Manifold.sphere(1.0, 96).scale((0.132, 0.104, 0.098)).translate(tuple(centre_rest))
    # cut plane through (0.16, 0.885) front and (-0.07, 0.80) back, keep above
    p1, p2 = np.array([0.16, 0, 0.885]), np.array([-0.07, 0, 0.80])
    t = p1 - p2
    nrm = br.normalize(np.array([-t[2], 0, t[0]]))      # normal pointing up-ish
    if nrm[2] < 0:
        nrm = -nrm
    helmet_rest = sph.trim_by_plane(tuple(nrm), float(np.dot(nrm, p1)))
    hv, ht = from_m(helmet_rest)
    hv_w = np.array([head_to_world(p) for p in hv])
    helmet = to_m(hv_w, ht)

    # ---- the bike ---------------------------------------------------------------
    seat_z = saddle_z
    parts = []
    # saddle body: hull of two ellipsoids, top at the saddle point, nose forward
    s0 = np.array([bk["saddle"][0] - 0.03, 0, seat_z])
    saddle = m3d.Manifold.batch_hull([
        m3d.Manifold.sphere(1.0, 48).scale((0.05, 0.068, 0.022)).translate(tuple(s0 + [-0.06, 0, -0.022])),
        m3d.Manifold.sphere(1.0, 48).scale((0.05, 0.02, 0.018)).translate(tuple(s0 + [0.13, 0, -0.020])),
    ])
    parts.append(saddle)
    # seat post from the seat-tube top to under the saddle
    s_seat = bk["s_seat"]
    t_post = (seat_z - 0.03) / s_seat[2]
    post_top = t_post * s_seat
    parts.append(capsule(bk["seat_top"], post_top, 0.0135))
    parts.append(capsule(post_top, s0 + [-0.03, 0, -0.03], 0.012))
    # frame tubes
    top_join = bk["ht_top"] - 0.02 * bk["s_head"]
    dt_join = bk["ht_bot"] + 0.03 * bk["s_head"]
    parts += [capsule(bk["ht_bot"], bk["ht_top"], 0.0185),
              capsule(bk["seat_top"], top_join, 0.016),
              capsule(bk["BB"], dt_join, 0.020),
              capsule(bk["BB"], bk["seat_top"], 0.016)]
    for s in (1, -1):
        drop_r = bk["rear"] + [0, s * 0.065, 0]
        drop_f = bk["front"] + [0, s * 0.050, 0]
        parts += [capsule(bk["BB"] + [0, s * 0.035, 0], drop_r, 0.011),
                  capsule(bk["seat_top"] + [0, s * 0.012, -0.03], drop_r, 0.009),
                  capsule(bk["ht_bot"] - 0.012 * bk["s_head"] + [0, s * 0.045, 0], drop_f, 0.012)]
    parts.append(capsule(bk["ht_bot"] - 0.012 * bk["s_head"] + [0, 0.045, 0],
                         bk["ht_bot"] - 0.012 * bk["s_head"] + [0, -0.045, 0], 0.012))  # fork crown
    for ax, half in ((bk["rear"], 0.065), (bk["front"], 0.050)):
        parts.append(capsule(ax + [0, half, 0], ax + [0, -half, 0], 0.010))            # hub/axle
    # steerer, stem, bar
    parts.append(capsule(bk["ht_top"], bk["stem_base"], 0.016))
    parts.append(capsule(bk["stem_base"], bk["bar"], 0.016))
    # drop bar: tops, ramp, hoods, and a curve whose lower straight runs under the posed palm
    hb = BIKE["bar_width"] / 2
    rch = BIKE["bar_reach"]
    grips = {}
    bar_parts = []
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        palm = 0.5 * (PJ(f"wrist.{side}") + PJ(f"finger3-1.{side}"))
        b0 = bk["bar"]
        zd = palm[2] - 0.025                      # drop tube centre under the palm centre
        y = np.array([0, sgn * hb, 0])
        pts = [b0, b0 + [0, sgn * (hb - 0.04), 0], b0 + y + [rch - 0.03, 0, 0.005],
               b0 + y + [rch, 0, -0.03], np.array([b0[0] + rch - 0.005, sgn * hb, zd + 0.05]),
               np.array([b0[0] + rch - 0.04, sgn * hb, zd + 0.004]),
               np.array([palm[0] - 0.07, sgn * hb, zd])]
        bar_parts.append(tube_path(pts, 0.0120))
        hood_a = b0 + y + [rch - 0.035, 0, 0.012]
        hood_b = b0 + y + [rch + 0.012, 0, 0.030]
        bar_parts.append(m3d.Manifold.batch_hull([
            m3d.Manifold.sphere(1.0, 32).scale((0.022, 0.016, 0.020)).translate(tuple(hood_a)),
            m3d.Manifold.sphere(1.0, 32).scale((0.016, 0.014, 0.022)).translate(tuple(hood_b))]))
        bar_parts.append(capsule(hood_b + [0, 0, -0.01], np.array([b0[0] + rch + 0.005, sgn * hb, zd + 0.06]), 0.008))
        grips[side] = dict(palm=palm.tolist(), drop_tube_z=float(zd), palm_ahead_of_bar_m=float(palm[0] - b0[0]))
    parts += bar_parts
    # cranks, pedals, chainring
    pedal_info, pedal_parts = {}, []
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        fwd = 1.0 if side == "R" else -1.0
        arm_y = sgn * BIKE["q_half"]
        sp = np.array([fwd * BIKE["crank"], arm_y, 0.0])
        parts.append(capsule(np.array([0, arm_y, 0]), sp, 0.012))
        ball = PJ(f"toe1-1.{side}")
        foot_y = sgn * (BIKE["q_half"] + BIKE["pedal_out"])
        lo_ = np.array([sp[0] - 0.045, foot_y - 0.045, -0.010])
        hi_ = np.array([sp[0] + 0.045, foot_y + 0.045, P["pedal_top"]])
        pedal_parts.append(rounded_box(lo_, hi_, 0.006, 16))
        parts.append(pedal_parts[-1])
        parts.append(capsule(sp, np.array([sp[0], foot_y, 0.0]), 0.008))
        sole = Vo[(np.abs(Vo[:, 0] - sp[0]) < 0.03) & (np.abs(Vo[:, 1] - foot_y) < 0.04), 2]
        pedal_info[side] = dict(spindle=sp.tolist(), ball=ball.tolist(),
                                ball_ahead_of_spindle_m=float(ball[0] - sp[0]),
                                sole_min_over_pedal_m=float(sole.min()) if len(sole) else None)
    parts.append(m3d.Manifold.cylinder(0.008, 0.100, 0.100, 96, True).rotate((90, 0, 0))
                 .translate((0, -0.050, 0)))                                             # chainring
    parts.append(m3d.Manifold.cylinder(0.140, 0.020, 0.020, 48, True).rotate((90, 0, 0)))   # BB shell+spindle

    bike = m3d.Manifold.batch_boolean(parts, m3d.OpType.Add)
    # to ground frame: BB at z = bb_z
    lift = np.array([0, 0, bk["bb_z"]])
    body = to_m(Vo, Td)
    contacts = OrderedDict(
        saddle_overlap_cm3=1e6 * (body ^ saddle).volume(),
        bar_overlap_cm3={s_: 1e6 * (body ^ bp).volume() for s_, bp in zip(("L", "R"), bar_parts[0::3])},
        pedal_overlap_cm3={s_: 1e6 * (body ^ pp).volume() for s_, pp in zip(("L", "R"), pedal_parts)},
    )
    rider = m3d.Manifold.batch_boolean([body, helmet, bike], m3d.OpType.Add).translate(tuple(lift))

    # wheels
    prof = wheel_profile()
    wheels = {}
    for name, ax in (("rear_wheel", bk["rear"]), ("front_wheel", bk["front"])):
        w = ring(prof).translate(tuple(ax + lift + np.array([0, 0, -BIKE["tyre_sink"]])))
        wheels[name] = w

    contacts["wheel_overlap_with_rider_cm3"] = {
        k: 1e6 * (w ^ m3d.Manifold.batch_boolean([body, helmet, bike], m3d.OpType.Add).translate(tuple(lift))).volume()
        for k, w in wheels.items()}
    # leading point of the front tyre at x = 0
    Vr, Tr = from_m(rider)
    xmax = max(Vr[:, 0].max(), max(from_m(w)[0][:, 0].max() for w in wheels.values()))
    dx = np.array([-xmax, 0, 0])
    rider = rider.translate(tuple(dx))
    wheels = {k: w.translate(tuple(dx)) for k, w in wheels.items()}

    # ---- checks ---------------------------------------------------------------
    import trimesh
    Vr, Tr = from_m(rider)
    mr = trimesh.Trimesh(Vr, Tr, process=True)
    allV = [Vr] + [from_m(w)[0] for w in wheels.values()]
    allT, off = [], 0
    for M in [rider] + list(wheels.values()):
        v, t = from_m(M)
        allT.append(t + off)
        off += len(v)
    VA, TA = np.vstack(allV), np.vstack(allT)
    wheel_check = {}
    for k, w in wheels.items():
        v, t = from_m(w)
        mw = trimesh.Trimesh(v, t, process=True)
        wheel_check[k] = dict(watertight=bool(mw.is_watertight), zmin=float(v[:, 2].min()),
                              zmax=float(v[:, 2].max()), xmin=float(v[:, 0].min()), xmax=float(v[:, 0].max()),
                              gap_to_rider_m=float(trimesh.proximity.signed_distance(mr, v[::50]).max() * -1))
    hip_abs = hip_c + lift + dx
    sh_c = 0.5 * (PJ("upperarm01.L") + PJ("upperarm01.R")) + lift + dx
    trunk = sh_c - hip_abs
    res = OrderedDict(
        figure=FIGURE, bike=BIKE, pose=POSE, trunk_flexion_solved_deg=flex,
        standing_height_m=h_cm / 100,
        trunk_angle_from_horizontal_deg=float(np.degrees(np.arctan2(trunk[2], trunk[0]))),
        hip_joint_centre_m=hip_abs.tolist(), shoulder_centre_m=sh_c.tolist(),
        head_top_z_m=float(Vr[:, 2].max()), saddle_top_z_m=float(seat_z + lift[2]),
        saddle_height_along_seat_tube_m=float(seat_z / bk["s_seat"][2]),
        knee_flex_deg={k: v for k, v in info.items() if k.startswith("knee")},
        elbow_flex_deg={k: v for k, v in info.items() if k.startswith("elbow")},
        grip_short_m={k: v for k, v in info.items() if k.startswith("grip")},
        pedals=pedal_info, grips=grips, contacts=contacts, hip_height_iterations=sink_log,
        body_self_intersections_before_fix=pre_fix, body_fix_passes=fix_log,
        rider=dict(triangles=int(len(Tr)), watertight=bool(mr.is_watertight),
                   winding_consistent=bool(mr.is_winding_consistent), volume_m3=float(mr.volume),
                   bodies=int(len(mr.split(only_watertight=False))),
                   bbox_min=Vr.min(0).tolist(), bbox_max=Vr.max(0).tolist(),
                   self_intersecting_faces=int(br.self_intersections(Vr, Tr).sum())),
        wheels=wheel_check,
        frontal_area_rider_m2=br.projected_area(Vr, Tr, 0),
        frontal_area_with_wheels_m2=br.projected_area(VA, TA, 0),
        side_area_with_wheels_m2=br.projected_area(VA, TA, 1),
        overall_bbox_min=VA.min(0).tolist(), overall_bbox_max=VA.max(0).tolist(),
        bike_points_ground_frame={k: (np.asarray(v) + lift + dx).tolist() for k, v in bk.items()
                                  if isinstance(v, np.ndarray) and k not in ("s_head", "s_seat")},
    )
    write_stl(OUT / "rider.stl", [("rider", Vr, Tr)])
    write_stl(OUT / "bike_wheels.stl", [(k, *from_m(w)) for k, w in wheels.items()])
    (OUT / "rider_build.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("trunk_flexion_solved_deg", "trunk_angle_from_horizontal_deg",
                                          "knee_flex_deg", "elbow_flex_deg", "grip_short_m",
                                          "saddle_height_along_seat_tube_m", "head_top_z_m",
                                          "frontal_area_rider_m2", "frontal_area_with_wheels_m2",
                                          "rider", "wheels", "pedals", "grips", "contacts",
                                          "hip_height_iterations", "hip_joint_centre_m", "overall_bbox_min",
                                          "overall_bbox_max")}, indent=1))
    previews(Vr, Tr, wheels)


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


def previews(Vr, Tr, wheels):
    try:
        import pyvista as pv
    except ImportError:
        print("PyVista not found: previews skipped")
        return
    pv.OFF_SCREEN = True
    meshes = [(br._polydata(Vr, Tr), "#c9a27e")] + [(br._polydata(*from_m(w)), "#444444") for w in wheels.values()]
    for view, (cdir, up) in {"side": ((0, -1, 0), (0, 0, 1)), "front": ((1, 0, 0), (0, 0, 1)),
                             "top": ((0, 0, 1), (1, 0, 0)), "iso": ((0.6, -0.8, 0.45), (0, 0, 1))}.items():
        p = pv.Plotter(off_screen=True, window_size=(1200, 900))
        p.set_background("white")
        for m, c in meshes:
            p.add_mesh(m, color=c, smooth_shading=True)
        p.camera_position = "xz"
        c = np.array([Vr[:, 0].mean(), 0, 0.6])
        p.camera.focal_point = c
        p.camera.position = c + 4 * np.array(cdir, float)
        p.camera.up = up
        if view != "iso":
            p.enable_parallel_projection()
        p.reset_camera()
        p.screenshot(str(OUT / f"preview_rider_{view}.png"))
        p.close()


if __name__ == "__main__":
    main()
