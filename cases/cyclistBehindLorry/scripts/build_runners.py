#!/usr/bin/env python3
"""Build two posed, CFD-ready runner surfaces from MakeHuman's CC0 assets.

No MakeHuman install: the needed CC0 data files are fetched from the official
repository (pinned commit) and MakeHuman's own algorithms are re-implemented
here, following the source at that commit:

  * macro targets    apps/humanmodifier.py (MacroModifier, getTargetWeights),
                     apps/human.py (_set*Vals), lib/targets.py (_cat_data)
  * height in cm     apps/human.py getHeightCm (body bbox y-extent * 10)
  * skeleton         shared/skeleton.py (fromFile, getJointPosition, get_normal,
                     getMatrix, Bone.build / Bone.update)
  * vertex weights   shared/animation.py VertexBoneWeights._build_vertex_weights_data
  * skinning         shared/skeleton.py Skeleton.skinMesh (linear blend skinning
                     with matPoseVerts = matPoseGlobal . inv(matRestGlobal))

This is the builder of the marathonDrafting case's runners, unchanged but for this
docstring and the build-script line of the README its main() writes; here
scripts/build_rider.py imports its functions and its main() is not used.

Output of main(): {runner_female,pacer_male}.{stl,obj}, previews and a README in
assets/makehuman/ at the repository's root.

Run:  python3 scripts/build_runners.py
"""
import json
import os
import sys
import urllib.request
from collections import OrderedDict
from pathlib import Path

import numpy as np

REPO = "makehumancommunity/makehuman"
COMMIT = "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"
RAW = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/"
CACHE = Path(os.environ.get("MH_CACHE", Path.home() / ".cache" / "makehuman-cc0" / COMMIT))
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "makehuman"
D = "makehuman/data/"

# ----------------------------------------------------------------------------
# Figures (MakeHuman macro slider values, 0..1).  Height is solved for.
# ----------------------------------------------------------------------------
FIGURES = OrderedDict([
    ("runner_female", dict(gender=0.0, age=0.5, muscle=0.65, weight=0.45,
                           african=1 / 3, asian=1 / 3, caucasian=1 / 3,
                           height_m=1.65)),
    ("pacer_male", dict(gender=1.0, age=0.5, muscle=0.65, weight=0.45,
                        african=1 / 3, asian=1 / 3, caucasian=1 / 3,
                        height_m=1.75)),
])

# ----------------------------------------------------------------------------
# Pose, in degrees.  Sagittal angles are measured from the vertical in the
# rest (standing) frame; "flex" = forward.  See pose_rotations().
# ----------------------------------------------------------------------------
POSE = OrderedDict(
    trunk_lean_fwd=5.0,        # spine05 (lumbar) rotated forward
    head_level=True,           # neck01 counter-rotates the trunk lean
    thigh_frontal=-5.0,        # thighs adducted to 5 deg inside vertical (feet under the body)
    r_hip_flex=30.0,           # right thigh forward of vertical
    r_knee_flex=40.0,          # right shank 10 deg behind vertical
    l_hip_ext=20.0,            # left thigh behind vertical
    l_knee_flex=65.0,          # left shank 85 deg behind vertical
    r_sole_toe_up=5.0,         # right sole pitched 5 deg toe-up: heel is the lowest point
    l_ankle_plantar=0.0,       # left foot keeps its rest angle to the shank
    arm_abduction=20.0,        # upper arm angle out from the vertical (frontal plane)
    l_shoulder_flex=25.0,      # left upper arm forward of vertical
    r_shoulder_ext=25.0,       # right upper arm behind vertical
    elbow_flex=85.0,           # 180 - included angle at the elbow
    finger_curl=(45.0, 50.0, 35.0),  # MCP, PIP, DIP of fingers 2-5
    thumb_curl=(10.0, 20.0, 20.0),
    finger_sign=1.0,
)

BODY_GROUP = "body"
TARGET_TRIS = 50000
SURFACE_DENSITY = 1000.0  # kg/m3, for the mass estimate only


# ----------------------------------------------------------------------------
# Fetching
# ----------------------------------------------------------------------------
def target_files():
    files = []
    for g in ("female", "male"):
        for e in ("african", "asian", "caucasian"):
            files.append(f"{D}targets/macrodetails/{e}-{g}-young.target")
        for m in ("min", "average", "max"):
            for w in ("min", "average", "max"):
                files.append(f"{D}targets/macrodetails/universal-{g}-young-{m}muscle-{w}weight.target")
                for h in ("min", "max"):
                    files.append(f"{D}targets/macrodetails/height/{g}-young-{m}muscle-{w}weight-{h}height.target")
    return files


FETCH = [f"{D}3dobjs/base.obj", f"{D}rigs/default.mhskel", f"{D}rigs/default_weights.mhw",
         "LICENSE.ASSETS.md", "LICENSE.md"] + target_files()


def fetch(rel):
    p = CACHE / rel
    if not p.exists() or p.stat().st_size == 0:
        p.parent.mkdir(parents=True, exist_ok=True)
        print("fetch", rel)
        with urllib.request.urlopen(RAW + rel) as r:
            p.write_bytes(r.read())
    return p


# ----------------------------------------------------------------------------
# Base mesh and targets
# ----------------------------------------------------------------------------
def load_obj(path):
    V, F, G, g = [], [], [], None
    for line in open(path, encoding="utf-8"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g "):
            g = line.split()[1]
        elif line.startswith("f "):
            F.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
            G.append(g)
    return np.array(V), F, G


def load_target(path):
    """algos3d.Target._load_text: lines 'index dx dy dz'."""
    idx, vec = [], []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("#"):
            continue
        t = line.split()
        if len(t) != 4:
            continue
        idx.append(int(t[0]))
        vec.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(idx, dtype=int), np.array(vec, dtype=float).reshape(-1, 3)


_TCACHE = {}


def target(rel):
    if rel not in _TCACHE:
        _TCACHE[rel] = load_target(fetch(rel))
    return _TCACHE[rel]


def macro_vals(gender, age, muscle, weight, height, african, asian, caucasian):
    """human.py _setGenderVals/_setAgeVals/_setWeightVals/_setMuscleVals/_setHeightVals."""
    v = {}
    v["male"], v["female"] = gender, 1 - gender
    if age < 0.5:
        v["old"] = 0.0
        v["baby"] = max(0.0, 1 - age * 5.333)
        v["young"] = max(0.0, (age - 0.1875) * 3.2)
        v["child"] = max(0.0, min(1.0, 5.333 * age) - v["young"])
    else:
        v["child"] = v["baby"] = 0.0
        v["old"] = max(0.0, age * 2 - 1)
        v["young"] = 1 - v["old"]
    for name, x in (("weight", weight), ("muscle", muscle)):
        v["max" + name] = max(0.0, x * 2 - 1)
        v["min" + name] = max(0.0, 1 - x * 2)
        v["average" + name] = 1 - (v["max" + name] + v["min" + name])
    v["maxheight"] = max(0.0, height * 2 - 1)
    v["minheight"] = max(0.0, 1 - height * 2)
    v["african"], v["asian"], v["caucasian"] = african, asian, caucasian
    return v


def target_weights(vals):
    """Weight of each macro target = product of the factor values named in its
    file name (getTargetWeights with the group factor = 1).  Only targets for
    'young' are fetched: both figures have age = 0.5 (25 y), so the baby, child
    and old factors are exactly zero."""
    assert abs(vals["young"] - 1.0) < 1e-12
    w = {}
    for rel in target_files():
        name = Path(rel).stem
        parts = [p for p in name.split("-") if p != "universal"]
        f = 1.0
        for p in parts:
            f *= vals[p]
        if f > 1e-9:
            w[rel] = f
    return w


def morph(base, vals):
    V = base.copy()
    for rel, f in target_weights(vals).items():
        idx, vec = target(rel)
        V[idx] += f * vec
    return V


# ----------------------------------------------------------------------------
# Skeleton (shared/skeleton.py)
# ----------------------------------------------------------------------------
def normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def get_matrix(head, tail, normal):
    mat = np.identity(4)
    y = normalize(tail - head)
    normal = normalize(normal)
    z = normalize(np.cross(normal, y))
    x = normalize(np.cross(y, z))
    mat[:3, 0], mat[:3, 1], mat[:3, 2], mat[:3, 3] = x, y, z, head
    return mat


class Skeleton:
    def __init__(self, skel_path, weights_path, nverts):
        sk = json.load(open(skel_path, encoding="utf-8"), object_pairs_hook=OrderedDict)
        self.joints = {k: v for k, v in sk["joints"].items() if isinstance(v, list) and v}
        self.planes = sk["planes"]
        bones = sk["bones"]
        order = []
        while len(order) != len(bones):
            for name, b in bones.items():
                if name not in order and (not b.get("parent") or b["parent"] in order):
                    order.append(name)
        self.order = order
        self.defs = bones
        self.weights = self._load_weights(weights_path, nverts, order[0])

    @staticmethod
    def _load_weights(path, nverts, root):
        """VertexBoneWeights._build_vertex_weights_data: normalise per vertex,
        drop weights <= 1e-4, unweighted vertices go to the root bone."""
        data = json.load(open(path, encoding="utf-8"), object_pairs_hook=OrderedDict)["weights"]
        wtot = np.zeros(nverts)
        for grp in data.values():
            for vn, w in grp:
                wtot[vn] += w
        out = OrderedDict()
        for b, grp in data.items():
            if not grp:
                continue
            acc = {}
            for vn, w in grp:
                acc[vn] = acc.get(vn, 0.0) + w / wtot[vn]
            vs = np.array(sorted(acc), dtype=int)
            ws = np.array([acc[v] for v in vs])
            keep = ws > 1e-4
            out[b] = (vs[keep], ws[keep])
        unweighted = np.where(wtot == 0)[0]
        if root not in out and len(unweighted):
            out[root] = (unweighted, np.ones(len(unweighted)))
        return out

    def joint(self, name, coords):
        return coords[self.joints[name]].mean(axis=0)

    def build(self, coords):
        """Bone.build for every bone, rest pose from the morphed coordinates."""
        self.rest = {}
        for name in self.order:
            b = self.defs[name]
            head = self.joint(b["head"], coords)
            tail = self.joint(b["tail"], coords)
            j1, j2, j3 = self.planes[b["rotation_plane"]]
            p1, p2, p3 = (self.joint(j, coords) for j in (j1, j2, j3))
            normal = normalize(np.cross(normalize(p3 - p2), normalize(p2 - p1)))
            if np.allclose(normal, 0, atol=1e-5):
                normal = np.array([0.0, 1.0, 0.0])
            self.rest[name] = get_matrix(head, tail, normal)

    def pose_matrices(self, world_rot):
        """world_rot: bone -> 3x3 rotation expressed in rest-world axes, about the
        bone head, applied in the parent's posed frame.  Converted to the bone-local
        matPose exactly as Skeleton.setPose does, then Bone.update()."""
        glob, verts = {}, {}
        for name in self.order:
            R = self.rest[name]
            pose = np.identity(4)
            if name in world_rot:
                Rr = R[:3, :3]
                pose[:3, :3] = Rr.T @ world_rot[name] @ Rr
            parent = self.defs[name].get("parent")
            if parent:
                rel = np.linalg.inv(self.rest[parent]) @ R
                glob[name] = glob[parent] @ rel @ pose
            else:
                glob[name] = R @ pose
            verts[name] = glob[name] @ np.linalg.inv(R)
        return verts

    def skin(self, coords, pose_verts):
        """Skeleton.skinMesh (linear blend skinning)."""
        out = np.zeros_like(coords)
        h = np.c_[coords, np.ones(len(coords))]
        for b, (vs, ws) in self.weights.items():
            out[vs] += (h[vs] @ pose_verts[b].T)[:, :3] * ws[:, None]
        return out


def rot(axis, deg):
    a = np.radians(deg)
    axis = normalize(np.asarray(axis, float))
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.identity(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


# MakeHuman frame: y up, figure faces +z, figure's left is +x.
X, Y, Z = np.eye(3)


def frame_match(u0, h0, u1, h1):
    """Rotation taking direction u0 to u1 and (the part of h0 normal to u0) to
    (the part of h1 normal to u1)."""
    def frame(u, h):
        u = normalize(u)
        h = normalize(h - np.dot(h, u) * u)
        return np.c_[u, h, np.cross(u, h)]
    return frame(u1, h1) @ frame(u0, h0).T


def sag_dir(frontal_deg, sagittal_deg):
    """Unit vector pointing down, tilted sideways by frontal_deg (+ = towards +x)
    and then forwards by sagittal_deg (+ = towards +z), MH frame."""
    f, s = np.radians(frontal_deg), np.radians(sagittal_deg)
    d = np.array([np.sin(f), -np.cos(f), 0.0])
    return rot(X, -sagittal_deg) @ d


def angle(a, b):
    return np.degrees(np.arccos(np.clip(np.dot(normalize(a), normalize(b)), -1, 1)))


def pose_rotations(skel, coords, P):
    """Bone rotations for the running pose, MH frame (x = figure's left, y up,
    z forward).  Each entry is a rotation in rest-world axes about the bone
    head, composed down the hierarchy (child world = parent world . child).

    Limb segments are aimed at target directions measured from the vertical in
    the world (not increments on MakeHuman's A-pose rest, whose elbows are
    already bent ~50 deg and whose knees ~7 deg); twist is fixed by keeping the
    knee/elbow hinge axis lateral."""
    J = lambda b, end="head": skel.joint(skel.defs[b][end], coords)
    R = {}
    lean = rot(X, P["trunk_lean_fwd"])          # +x rotation tilts 'up' forwards
    R["spine05"] = lean
    if P["head_level"]:
        R["neck01"] = lean.T                    # head chain: lean . lean^T = I
    world = {}
    for side, sgn in (("L", 1.0), ("R", -1.0)):  # sgn: lateral = sgn * +x
        # ---- legs: thigh upperleg01, shank lowerleg01, foot -------------------
        hip, knee, ankle = J(f"upperleg01.{side}"), J(f"lowerleg01.{side}"), J(f"foot.{side}")
        u0, s0 = knee - hip, ankle - knee
        rest_dfront = np.degrees(np.arctan2(sgn * s0[0], -s0[1]) - np.arctan2(sgn * u0[0], -u0[1]))
        thigh_sag = P["r_hip_flex"] if side == "R" else -P["l_hip_ext"]
        knee_flex = P["r_knee_flex"] if side == "R" else P["l_knee_flex"]
        u1 = sag_dir(sgn * P["thigh_frontal"], thigh_sag)
        s1 = sag_dir(sgn * (P["thigh_frontal"] + rest_dfront), thigh_sag - knee_flex)
        Rt = frame_match(u0, X, u1, X)
        Rs = frame_match(s0, X, s1, X)
        R[f"upperleg01.{side}"] = Rt
        R[f"lowerleg01.{side}"] = Rt.T @ Rs
        if side == "R":
            Rf = rot(X, -P["r_sole_toe_up"])    # rest sole is flat; -x lifts the toes
        else:
            Rf = Rs @ rot(X, P["l_ankle_plantar"])
        R[f"foot.{side}"] = Rs.T @ Rf
        world[f"thigh.{side}"], world[f"shank.{side}"] = u1, s1
        # ---- arms: upperarm01, lowerarm01 -----------------------------------
        sh, el, wr = J(f"upperarm01.{side}"), J(f"lowerarm01.{side}"), J(f"wrist.{side}")
        a0, f0 = el - sh, wr - el
        h0 = normalize(np.cross(a0, f0))        # elbow hinge (= MH bone local x)
        swing = P["l_shoulder_flex"] if side == "L" else -P["r_shoulder_ext"]
        a1 = sag_dir(sgn * P["arm_abduction"], swing)
        h1 = -X                                  # flexion then carries the forearm forwards
        Ra = frame_match(a0, h0, a1, h1)
        R[f"upperarm01.{side}"] = lean.T @ Ra    # arm chain hangs off the leaning spine
        R[f"lowerarm01.{side}"] = rot(h0, P["elbow_flex"] - angle(a0, f0))
        # ---- fingers: curl about each bone's own local x (MakeHuman's hinge) --
        for f in range(1, 6):
            curls = P["thumb_curl"] if f == 1 else P["finger_curl"]
            for k in range(3):
                b = f"finger{f}-{k + 1}.{side}"
                R[b] = rot(skel.rest[b][:3, 0], P["finger_sign"] * curls[k])
    return R


# ----------------------------------------------------------------------------
# Mesh processing
# ----------------------------------------------------------------------------
def body_triangles(F, G):
    tris = []
    for f, g in zip(F, G):
        if g != BODY_GROUP:
            continue
        if len(f) == 4:
            tris += [[f[0], f[1], f[2]], [f[0], f[2], f[3]]]
        else:
            tris.append(f[:3])
    return np.array(tris)


def to_output_frame(V):
    """MH (x left, y up, z forward, decimetres) -> (x forward, y left, z up, metres)."""
    return 0.1 * np.c_[V[:, 2], V[:, 0], V[:, 1]]


def self_intersections(V, T):
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(V, T))
    ms.compute_selection_by_self_intersections_per_face()
    return ms.current_mesh().face_selection_array().copy()


def body_quads(F, G):
    Q = np.array([f for f, g in zip(F, G) if g == BODY_GROUP])
    assert Q.shape[1] == 4
    return Q


def catmull_clark(V, Q):
    """One Catmull-Clark step on a closed quad mesh (what MakeHuman's
    'smooth' / apps/catmull_clark_subdivision.py does for display)."""
    nv, nf = len(V), len(Q)
    fp = V[Q].mean(axis=1)
    e = np.stack([Q, np.roll(Q, -1, axis=1)], axis=2).reshape(-1, 2)     # (nf*4, 2)
    es = np.sort(e, axis=1)
    uniq, inv = np.unique(es, axis=0, return_inverse=True)
    inv = inv.ravel()
    face_of = np.repeat(np.arange(nf), 4)
    ne = len(uniq)
    fsum = np.zeros((ne, 3))
    np.add.at(fsum, inv, fp[face_of])
    cnt = np.bincount(inv, minlength=ne)
    assert (cnt == 2).all(), "mesh must be closed and manifold"
    ep = (V[uniq[:, 0]] + V[uniq[:, 1]] + fsum) / 4
    # vertex update
    val = np.bincount(uniq.ravel(), minlength=nv).astype(float)
    Fav = np.zeros((nv, 3)); fc = np.zeros(nv)
    np.add.at(Fav, Q.ravel(), np.repeat(fp, 4, axis=0)); np.add.at(fc, Q.ravel(), 1)
    Fav /= fc[:, None]
    mid = (V[uniq[:, 0]] + V[uniq[:, 1]]) / 2
    Rav = np.zeros((nv, 3))
    np.add.at(Rav, uniq[:, 0], mid); np.add.at(Rav, uniq[:, 1], mid)
    Rav /= val[:, None]
    n = val[:, None]
    Vn = (Fav + 2 * Rav + (n - 3) * V) / n
    newV = np.vstack([Vn, ep, fp])
    E = (nv + inv).reshape(nf, 4)            # E[:, i] = edge (v_i, v_i+1)
    Fi = nv + ne + np.arange(nf)
    quads = []
    for i in range(4):
        quads.append(np.c_[Q[:, i], E[:, i], Fi, E[:, (i - 1) % 4]])
    return newV, np.vstack(quads)


def triangulate_quads(V, Q):
    d02 = np.linalg.norm(V[Q[:, 0]] - V[Q[:, 2]], axis=1)
    d13 = np.linalg.norm(V[Q[:, 1]] - V[Q[:, 3]], axis=1)
    a = d02 <= d13
    t1 = np.where(a[:, None], Q[:, [0, 1, 2]], Q[:, [0, 1, 3]])
    t2 = np.where(a[:, None], Q[:, [0, 2, 3]], Q[:, [1, 2, 3]])
    return np.vstack([t1, t2])


def compact(V, T):
    used = np.unique(T)
    remap = -np.ones(len(V), dtype=int)
    remap[used] = np.arange(len(used))
    return V[used], remap[T], used


def adjacency(n, T):
    import scipy.sparse as sp
    e = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return ((A + A.T) > 0).astype(float).tocsr()


def fold_faces(V, T, deg_lim=150.0):
    import trimesh
    m = trimesh.Trimesh(V, T, process=False)
    ang = np.degrees(m.face_adjacency_angles)
    sel = np.zeros(len(T), bool)
    sel[m.face_adjacency[ang > deg_lim].ravel()] = True
    return sel


def fix_self_intersections(V, T, rings=3, steps=5, max_iter=40):
    """Local umbrella-Laplacian relaxation of every vertex within `rings` of an
    intersecting face or of a fold (adjacent normals > 150 deg apart),
    repeated until pymeshlab finds no intersecting faces and no folds remain."""
    V = V.copy()
    A = adjacency(len(V), T)
    deg = np.asarray(A.sum(1)).ravel()
    log = []
    for it in range(max_iter):
        sel = self_intersections(V, T)
        fold = fold_faces(V, T)
        log.append((int(sel.sum()), int(fold.sum())))
        if not sel.any() and not fold.any():
            return V, log
        mask = np.zeros(len(V), bool)
        mask[T[sel | fold].ravel()] = True
        for _ in range(rings):
            mask |= (A @ mask.astype(float)) > 0
        for _ in range(steps):
            L = (A @ V) / deg[:, None] - V
            V[mask] += 0.5 * L[mask]
    raise RuntimeError(f"self-intersections remain after {max_iter} passes: {log}")


def decimate(V, T, target):
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(V, T))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target), qualitythr=0.6,
                                                preservenormal=True, preservetopology=True,
                                                optimalplacement=True, planarquadric=True,
                                                autoclean=True)
    m = ms.current_mesh()
    return m.vertex_matrix().copy(), m.face_matrix().copy()


def topology(V, T):
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(V, T))
    t = ms.get_topological_measures()
    return {k: (int(v) if isinstance(v, (int, np.integer, bool)) else v) for k, v in t.items()}


def fold_count(V, T, deg_lim=150.0):
    """Adjacent faces whose normals differ by more than deg_lim (fold-overs,
    which a face-face intersection test between non-adjacent faces misses)."""
    import trimesh
    m = trimesh.Trimesh(V, T, process=False)
    ang = np.degrees(m.face_adjacency_angles)
    return int((ang > deg_lim).sum()), float(ang.max())


def projected_area(V, T, axis=0):
    """Exact area of the silhouette seen along `axis` (0: x, i.e. frontal area
    on the y-z plane): union of the projected triangles."""
    import shapely
    keep = [i for i in range(3) if i != axis]
    P = V[:, keep][T]                                   # (n, 3, 2)
    d1, d2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    a2 = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    P = P[a2 > 1e-14]
    polys = shapely.polygons(np.concatenate([P, P[:, :1]], axis=1))
    return float(shapely.union_all(polys, grid_size=1e-6).area)


# ----------------------------------------------------------------------------
# Build one figure
# ----------------------------------------------------------------------------
ARM_DISTAL = ("lowerarm", "wrist", "finger", "metacarpal")
TORSO_LEGS = ("spine", "root", "pelvis", "upperleg", "breast")


def solve_height(base, bv, params, target_cm):
    def h_cm(h):
        V = morph(base, macro_vals(height=h, **params))
        return 10 * (V[bv, 1].max() - V[bv, 1].min())
    lo, hi = 0.0, 1.0
    assert h_cm(lo) < target_cm < h_cm(hi), "target height outside MakeHuman's range"
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if h_cm(mid) < target_cm else (lo, mid)
    return 0.5 * (lo + hi), h_cm(0.5 * (lo + hi))


def sag(v):      # output frame: angle from the downward vertical, + = forward (x)
    return float(np.degrees(np.arctan2(v[0], -v[2])))


def included(a, b, c):
    return float(angle(a - b, c - b))


def build_figure(name, spec, base, F, G, skel):
    params = {k: v for k, v in spec.items() if k != "height_m"}
    Q = body_quads(F, G)
    bv = np.unique(Q)
    h_param, h_cm = solve_height(base, bv, params, 100 * spec["height_m"])
    vals = macro_vals(height=h_param, **params)
    V = morph(base, vals)
    # MakeHuman's own estimates on the standing (rest) body
    import trimesh
    rest_tri = trimesh.Trimesh(to_output_frame(V), triangulate_quads(V, Q), process=False)
    bsa = rest_tri.area
    mh_weight_kg = bsa * bsa * 3600 / h_cm          # human.getWeightKg (Mosteller)
    rest_vol = rest_tri.volume

    skel.build(V)
    R = pose_rotations(skel, V, POSE)
    PV = skel.pose_matrices(R)
    posed = skel.skin(V, PV)

    def pj(b, end="head"):  # posed joint, output frame
        p = skel.joint(skel.defs[b][end], V)
        return to_output_frame((PV[b] @ np.r_[p, 1.0])[None, :3])[0]

    # ---- smooth surface: Catmull-Clark once, triangulate, decimate ----------
    Vb, Qb, used = compact(posed, Q)
    Vs, Qs = catmull_clark(Vb, Qb)
    Ts = triangulate_quads(Vs, Qs)
    Vd, Td = decimate(Vs, Ts, TARGET_TRIS)
    Vo = to_output_frame(Vd)
    pre_fix = int(self_intersections(Vo, Td).sum())
    Vo_fixed, fix_log = fix_self_intersections(Vo, Td)
    fix_moved = float(np.linalg.norm(Vo_fixed - Vo, axis=1).max())
    Vo = Vo_fixed

    # ---- placement: x = 0 at the hip-joint centre, y centred, ground z = 0 --
    hipc = 0.5 * (pj("upperleg01.L") + pj("upperleg01.R"))
    shift = np.array([-hipc[0], -0.5 * (Vo[:, 1].min() + Vo[:, 1].max()), -Vo[:, 2].min()])
    Vo = Vo + shift
    P = lambda b, end="head": pj(b, end) + shift

    # ---- region labels (dominant bone) mapped from the coarse posed mesh ----
    from scipy.spatial import cKDTree
    W = np.zeros((len(base), len(skel.order)))
    bidx = {b: i for i, b in enumerate(skel.order)}
    for b, (vs, ws) in skel.weights.items():
        W[vs, bidx[b]] = ws
    dom = np.array(skel.order)[W.argmax(1)]
    coarse = to_output_frame(posed[bv]) + shift
    _, nn = cKDTree(coarse).query(Vo)
    label = dom[bv][nn]

    def group(prefixes, side=None):
        m = np.zeros(len(Vo), bool)
        for p in prefixes:
            m |= np.array([l.startswith(p) and (side is None or l.endswith("." + side)) for l in label])
        return m
    torso = group(TORSO_LEGS)
    tree_t = cKDTree(Vo[torso])
    clear = {}
    for side in ("L", "R"):
        arm = group(ARM_DISTAL, side)
        clear[f"forearm_hand.{side}"] = float(tree_t.query(Vo[arm])[0].min())
        # upper arm below the armpit (more than 12 cm below the shoulder joint)
        up = group(("upperarm",), side) & (Vo[:, 2] < P(f"upperarm01.{side}")[2] - 0.12)
        clear[f"upperarm_below_axilla.{side}"] = float(tree_t.query(Vo[up])[0].min())
    footL = group(("foot", "toe"), "L")
    footR = group(("foot", "toe"), "R")
    lowest = Vo[np.argmin(Vo[:, 2])]

    # ---- achieved pose angles from posed joints -----------------------------
    ang = OrderedDict()
    tr = P("neck01") - P("spine05")          # lumbar base to neck base
    tr0 = to_output_frame((skel.joint(skel.defs["neck01"]["head"], V) - skel.joint(skel.defs["spine05"]["head"], V))[None])[0]
    ang["trunk_lean_fwd_change"] = float(np.degrees(np.arctan2(tr[0], tr[2]) - np.arctan2(tr0[0], tr0[2])))
    ang["trunk_line_from_vertical"] = float(np.degrees(np.arctan2(tr[0], tr[2])))
    hd_rest = to_output_frame((skel.joint(skel.defs["head"]["tail"], V) - skel.joint(skel.defs["head"]["head"], V))[None])[0]
    hd = P("head", "tail") - P("head")
    ang["head_pitch_change"] = float(np.degrees(np.arctan2(hd[0], hd[2]) - np.arctan2(hd_rest[0], hd_rest[2])))
    for side, lab in (("R", "right"), ("L", "left")):
        hip, knee, ank = P(f"upperleg01.{side}"), P(f"lowerleg01.{side}"), P(f"foot.{side}")
        ang[f"{lab}_thigh_from_vertical"] = sag(knee - hip)
        ang[f"{lab}_knee_flex"] = 180 - included(hip, knee, ank)
        ang[f"{lab}_shank_from_vertical"] = sag(ank - knee)
        sh, el, wr = P(f"upperarm01.{side}"), P(f"lowerarm01.{side}"), P(f"wrist.{side}")
        ang[f"{lab}_upperarm_from_vertical"] = sag(el - sh)
        d = el - sh
        ang[f"{lab}_upperarm_abduction"] = float(np.degrees(np.arctan2(abs(d[1]), -d[2])))
        ang[f"{lab}_elbow_flex"] = 180 - included(sh, el, wr)
        ang[f"{lab}_hand_height_m"] = float(P(f"finger3-1.{side}")[2])
    ang["hip_joint_height_m"] = float(hipc[2] + shift[2])

    # ---- checks and measures ------------------------------------------------
    m = trimesh.Trimesh(Vo, Td, process=False)
    topo = topology(Vo, Td)
    nfold, maxdihed = fold_count(Vo, Td)
    tri_area = m.area_faces
    angles = np.degrees(m.face_angles)
    sel_final = int(self_intersections(Vo, Td).sum())
    res = OrderedDict(
        name=name,
        macro=dict(params, height=h_param),
        standing_height_m=h_cm / 100,
        posed_height_m=float(Vo[:, 2].max() - Vo[:, 2].min()),
        bbox_min=Vo.min(0).tolist(), bbox_max=Vo.max(0).tolist(),
        bbox_size=(Vo.max(0) - Vo.min(0)).tolist(),
        area_m2=float(m.area), volume_m3=float(m.volume),
        mass_kg_at_1000=float(m.volume * SURFACE_DENSITY),
        rest_area_m2=float(bsa), rest_volume_m3=float(rest_vol),
        mh_weight_kg_mosteller=float(mh_weight_kg),
        frontal_area_m2=projected_area(Vo, Td, 0),
        side_area_m2=projected_area(Vo, Td, 1),
        triangles=int(len(Td)), vertices=int(len(Vo)),
        watertight=bool(m.is_watertight), winding_consistent=bool(m.is_winding_consistent),
        outward=bool(m.volume > 0), euler=int(m.euler_number), bodies=int(len(m.split(only_watertight=False))),
        topology=topo, self_intersecting_faces=sel_final,
        self_intersections_before_fix=pre_fix, fix_passes=fix_log, fix_max_move_m=fix_moved,
        folds_over_150deg=nfold, max_dihedral_deg=maxdihed,
        min_face_area_m2=float(tri_area.min()), min_angle_deg=float(angles.min()),
        degenerate_faces=int((tri_area < 1e-10).sum()),
        mean_edge_m=float(m.edges_unique_length.mean()), max_edge_m=float(m.edges_unique_length.max()),
        clearance_to_torso_m=clear,
        lowest_point=lowest.tolist(), lowest_label=str(label[np.argmin(Vo[:, 2])]),
        left_foot_min_z_m=float(Vo[footL, 2].min()), right_foot_min_z_m=float(Vo[footR, 2].min()),
        angles=ang,
        coarse_selfint=int(self_intersections(to_output_frame(Vb), triangulate_quads(Vb, Qb)).sum()),
    )
    return Vo, Td, res


# ----------------------------------------------------------------------------
# Previews (pyvista, off screen, orthographic)
# ----------------------------------------------------------------------------
COLORS = {"runner_female": "#d9a58c", "pacer_male": "#8fb3d9"}
VIEWS = {  # camera direction (from the focal point towards the camera), view-up
    "side": ((0, -1, 0), (0, 0, 1)),     # from the figure's right; +x to the right
    "top": ((0, 0, 1), (0, 1, 0)),       # from above; +x to the right, +y (left) up
    "front": ((1, 0, 0), (0, 0, 1)),     # from ahead, facing the figure
}


def _polydata(V, T):
    import pyvista as pv
    return pv.PolyData(V, np.c_[np.full(len(T), 3), T].ravel())


def render(panels, path, size=(900, 1000), scale=None):
    """panels: list of (view, [(V, T, color, offset)], title)."""
    import pyvista as pv
    pv.OFF_SCREEN = True
    pl = pv.Plotter(shape=(1, len(panels)), window_size=(size[0] * len(panels), size[1]),
                    off_screen=True, lighting="three lights")
    pl.set_background("white")
    for i, (view, items, title) in enumerate(panels):
        pl.subplot(0, i)
        allv = []
        for V, T, color, off in items:
            Vp = V + np.asarray(off)
            allv.append(Vp)
            pl.add_mesh(_polydata(Vp, T), color=color, smooth_shading=True,
                        ambient=0.25, diffuse=0.75, specular=0.1)
        allv = np.vstack(allv)
        lo, hi = allv.min(0), allv.max(0)
        # ground line / plane for side and front views
        if view in ("side", "front"):
            ext = hi - lo
            g = pv.Plane(center=((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0), direction=(0, 0, 1),
                         i_size=ext[0] + 0.3, j_size=ext[1] + 0.3)
            pl.add_mesh(g, color="#bbbbbb", opacity=1.0, ambient=1.0, diffuse=0.0)
        d, up = VIEWS[view]
        c = (lo + hi) / 2
        pl.camera.focal_point = c
        pl.camera.position = c + 10 * np.asarray(d, float)
        pl.camera.up = up
        pl.enable_parallel_projection()
        if scale is None:
            half = 0.55 * max(np.delete(hi - lo, [0, 1, 2].index(int(np.argmax(np.abs(d)))))) + 0.05
        else:
            half = scale
        pl.camera.parallel_scale = half
        pl.add_text(title, font_size=11, color="black")
    pl.screenshot(str(path), transparent_background=False)
    pl.close()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def write_stl_obj(V, T, stem):
    import trimesh
    m = trimesh.Trimesh(V, T, process=False)
    m.export(OUT / f"{stem}.stl", file_type="stl")             # binary STL
    with open(OUT / f"{stem}.obj", "w") as f:
        f.write(f"# {stem}: MakeHuman CC0 base mesh ({REPO}@{COMMIT[:12]}), posed; metres, z up, +x forward\n")
        f.write(f"o {stem}\n")
        np.savetxt(f, V, fmt="v %.6f %.6f %.6f")
        np.savetxt(f, T + 1, fmt="f %d %d %d")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for rel in FETCH:
        fetch(rel)
    base, F, G = load_obj(fetch(D + "3dobjs/base.obj"))
    skel = Skeleton(fetch(D + "rigs/default.mhskel"), fetch(D + "rigs/default_weights.mhw"), len(base))
    results, meshes = OrderedDict(), OrderedDict()
    for name, spec in FIGURES.items():
        print("building", name)
        V, T, res = build_figure(name, spec, base, F, G, skel)
        write_stl_obj(V, T, name)
        results[name], meshes[name] = res, (V, T)
        print(json.dumps(res, indent=1))
    (OUT / "LICENSE.ASSETS.md").write_bytes(fetch("LICENSE.ASSETS.md").read_bytes())
    (OUT / "build_report.json").write_text(json.dumps(dict(commit=COMMIT, pose=POSE, figures=results), indent=1))

    # previews: both figures side by side, same scale per view
    r, p = meshes["runner_female"], meshes["pacer_male"]
    for view in ("side", "top", "front"):
        off = {"side": (0, 0, 0), "top": (0, 0, 0), "front": (0, 0, 0)}[view]
        sc = {"side": 1.0, "top": 0.55, "front": 1.0}[view]
        render([(view, [(r[0], r[1], COLORS["runner_female"], off)], f"runner (female, 1.65 m) - {view}"),
                (view, [(p[0], p[1], COLORS["pacer_male"], off)], f"pacer (male, 1.75 m) - {view}")],
               OUT / f"preview_{view}.png", size=(800, 1000) if view != "top" else (800, 600), scale=sc)
    gap = 1.3
    items = [(p[0], p[1], COLORS["pacer_male"], (0, 0, 0)),
             (r[0], r[1], COLORS["runner_female"], (-gap, 0, 0))]
    render([("side", items, f"runner {gap} m behind pacer (hip to hip) - side"),
            ("top", items, "top")], OUT / "preview_drafting.png", size=(1200, 800), scale=None)
    # clearances in the drafting arrangement
    pacer_rear = float(p[0][:, 0].min())
    runner_front = float(r[0][:, 0].max() - gap)
    print("drafting: pacer rearmost x", pacer_rear, "runner frontmost x", runner_front,
          "gap", pacer_rear - runner_front)
    write_readme(results, dict(pacer_rear=pacer_rear, runner_front=runner_front, gap=gap))


def write_readme(results, draft):
    r = results
    f = lambda x, n=3: f"{x:.{n}f}"
    rows = [
        ("macro: gender / age / muscle / weight", lambda d: f"{d['macro']['gender']:.2f} / {d['macro']['age']:.2f} / {d['macro']['muscle']:.2f} / {d['macro']['weight']:.2f}"),
        ("macro: height slider (solved)", lambda d: f(d["macro"]["height"], 4)),
        ("standing height, rest A-pose (m)", lambda d: f(d["standing_height_m"])),
        ("posed height (m)", lambda d: f(d["posed_height_m"])),
        ("bbox min x, y, z (m)", lambda d: ", ".join(f(v) for v in d["bbox_min"])),
        ("bbox max x, y, z (m)", lambda d: ", ".join(f(v) for v in d["bbox_max"])),
        ("bbox size (m)", lambda d: ", ".join(f(v) for v in d["bbox_size"])),
        ("surface area (m2)", lambda d: f(d["area_m2"])),
        ("volume (m3)", lambda d: f(d["volume_m3"], 4)),
        ("mass at 1000 kg/m3 (kg)", lambda d: f(d["mass_kg_at_1000"], 1)),
        ("MakeHuman getWeightKg, standing (kg)", lambda d: f(d["mh_weight_kg_mosteller"], 1)),
        ("frontal area, y-z plane (m2)", lambda d: f(d["frontal_area_m2"])),
        ("side area, x-z plane (m2)", lambda d: f(d["side_area_m2"])),
        ("triangles / vertices", lambda d: f"{d['triangles']} / {d['vertices']}"),
        ("mean / max edge (mm)", lambda d: f"{1000 * d['mean_edge_m']:.1f} / {1000 * d['max_edge_m']:.1f}"),
        ("min triangle angle (deg)", lambda d: f(d["min_angle_deg"], 2)),
        ("watertight / manifold / consistent / outward", lambda d: f"{d['watertight']} / {bool(d['topology']['is_mesh_two_manifold'])} / {d['winding_consistent']} / {d['outward']}"),
        ("genus / components / boundary edges", lambda d: f"{d['topology']['genus']} / {d['topology']['connected_components_number']} / {d['topology']['boundary_edges']}"),
        ("self-intersecting faces (final)", lambda d: str(d["self_intersecting_faces"])),
        ("intersecting faces before repair, passes", lambda d: f"{d['self_intersections_before_fix']}, {d['fix_passes']}"),
        ("max vertex move by repair (mm)", lambda d: f(1000 * d["fix_max_move_m"], 1)),
        ("degenerate faces", lambda d: str(d["degenerate_faces"])),
        ("left foot lowest z (m)", lambda d: f(d["left_foot_min_z_m"])),
        ("lowest point (x, y, z) / bone", lambda d: ", ".join(f(v) for v in d["lowest_point"]) + " / " + d["lowest_label"]),
    ]
    for k in r["runner_female"]["clearance_to_torso_m"]:
        rows.append((f"clearance {k} to torso/legs (m)", lambda d, k=k: f(d["clearance_to_torso_m"][k])))
    for k in r["runner_female"]["angles"]:
        rows.append((f"measured: {k}", lambda d, k=k: f(d["angles"][k], 2)))
    table = "| quantity | runner_female | pacer_male |\n|---|---|---|\n" + "\n".join(
        f"| {n} | {fn(r['runner_female'])} | {fn(r['pacer_male'])} |" for n, fn in rows)
    pose = "\n".join(f"| {k} | {v} |" for k, v in POSE.items())
    files = "\n".join(f"- `{x}`" for x in FETCH)
    txt = f"""# MakeHuman runner surfaces (CC0)

Two posed, closed triangle surfaces of human runners for the marathon-drafting
OpenFOAM case (snappyHexMesh) and for the side/top drawings.

| file | what |
|---|---|
| `runner_female.stl`, `runner_female.obj` | female, young adult (25 y), slim, 1.65 m standing |
| `pacer_male.stl`, `pacer_male.obj` | male, young adult (25 y), slim, 1.75 m standing |
| `preview_side.png`, `preview_top.png`, `preview_front.png` | orthographic previews, both figures |
| `preview_drafting.png` | runner 1.3 m (hip centre to hip centre) behind the pacer, side and top |
| `build_report.json` | every number below, machine readable |
| `LICENSE.ASSETS.md` | CC0 1.0, copied from the MakeHuman repository |

Build script: `scripts/build_runners.py` (re-runnable;
downloads into `~/.cache/makehuman-cc0/<commit>/`).

## Frame and units

Metres. z up, running direction +x, the figure's left is +y. x = 0 at the
centre of the two hip joints, y centred on the bounding box, z = 0 at the lowest
point of the grounded (right) foot. STL is binary; OBJ has the same vertices
and triangles.

## Source

- Repository: https://github.com/{REPO}, commit `{COMMIT}`
- Licence: `LICENSE.md` section on assets: base mesh, proxies, targets,
  modifiers, poses and rigs are CC0 1.0 (`LICENSE.ASSETS.md`).
- The `makehuman` application/PyPI package was not installed or run. Its
  algorithms were re-implemented from the source at this commit:
  `apps/humanmodifier.py` (MacroModifier, getTargetWeights), `apps/human.py`
  (`_set*Vals`, `getHeightCm`, `getWeightKg`), `lib/targets.py` (target-name
  factor categories), `core/algos3d.py` (target text format),
  `shared/skeleton.py` (joint positions, bone planes and `getMatrix`,
  `Bone.build/update`, `skinMesh`), `shared/animation.py`
  (`VertexBoneWeights` normalisation).
- Files fetched (raw text, not the compiled `.npz`):

{files}

## Modelling

- Macro targets: weight of each target = product of the factors in its file
  name (gender, age, race, muscle, weight, height), exactly as
  `getTargetWeights`. Ethnicity is MakeHuman's default 1/3 each. Age 0.5 = 25
  years, so only the `young` targets are non-zero. Proportions, breast and all
  other modifiers stay at MakeHuman's defaults (no displacement).
- Height: the height slider is solved by bisection until `getHeightCm`
  (y-extent of the `body` group in the rest A-pose) equals 165.0 / 175.0 cm.
- Body only: the `body` face group of `base.obj` (13 378 quads). All helper
  geometry (joint cubes, eyes, eyelashes, eyebrows, teeth, tongue, genital,
  hair/skirt/tights helpers) is dropped. The body group is already a closed,
  genus-0 surface (eye sockets and mouth are closed in the base mesh), so no
  holes had to be closed. No proxy mesh was used: the base body is closed and
  is the mesh the default skeleton weights belong to.

## Pose

Linear blend skinning with `default.mhskel` and `default_weights.mhw`, using
MakeHuman's bone matrices (`matPoseVerts = matPoseGlobal . inv(matRestGlobal)`).
Bone rotations were set so that the limb segments point in target directions
measured from the vertical (MakeHuman's rest pose is an A-pose with the elbows
already bent about 50 deg and knees about 7 deg, so increments on the rest pose
would not give the stated angles). Inputs:

| parameter (deg) | value |
|---|---|
{pose}

Notes: `trunk_lean_fwd` is a 5 deg forward rotation at the lumbar joint
(spine05); MakeHuman's standing trunk line is not exactly vertical, so the
measured neck-to-lumbar line ends at the value in the table below. Arm angles
are from the vertical in the world frame (the trunk lean is compensated).
`arm_abduction` was raised from 13 to 20 deg to keep the upper arm 2.5-4 cm off
the torso. The thighs are adducted 5 deg so the feet fall under the body
instead of MakeHuman's wide A-pose stance. Fingers are curled about each
phalanx bone's own hinge axis; the thumb is only lightly curled.

## Processing

1. Morph the full base mesh (all 19 158 vertices, helpers included because
   joint positions come from them), build the skeleton, pose by LBS.
2. Take the `body` quads, apply one Catmull-Clark subdivision (as MakeHuman's
   smooth display does), triangulate along the shorter diagonal.
3. Quadric edge-collapse decimation to {TARGET_TRIS} triangles (pymeshlab,
   topology and normals preserved).
4. Convert MakeHuman's decimetres, y-up, +z-facing frame to metres, z-up, +x.
5. Self-intersection and fold repair: LBS makes the elbow and knee creases and
   the curled fingers interpenetrate. Every vertex within 3 rings of an
   intersecting face (pymeshlab face-face test) or of a fold (adjacent normals
   more than 150 deg apart) is relaxed with 5 umbrella-Laplacian steps, repeated
   until both counts are zero.
6. Place in the frame above and check.

## Results and checks

{table}

Drafting arrangement (preview_drafting.png): with the runner's hip centre
{draft['gap']} m behind the pacer's, the pacer's rearmost point (trailing foot)
is at x = {draft['pacer_rear']:.3f} m and the runner's frontmost point (leading
hand) at x = {draft['runner_front']:.3f} m: a {draft['pacer_rear'] - draft['runner_front']:.3f} m gap. Both figures are in the
same phase of the stride.

## Known limitations

- Runner mass and frontal area: with a slim weight slider (0.45) the female is
  about 50 kg (posed volume x 1000 kg/m3; MakeHuman's own Mosteller estimate on
  the standing body is about 52 kg) and her frontal area is about 0.38 m2,
  below the literature model's 55 kg and 0.44 m2. Reaching 55 kg needs weight
  about 0.7, which is above MakeHuman's average and no longer "low weight". The
  literature area probably also includes hair and clothing; these figures are
  bald and unclothed.
- LBS loses about 2-3 % of volume at the bent joints, and the repair locally
  smooths the elbow and knee creases and finger contacts (largest move in the
  table). The repair targets surface validity, not anatomical accuracy there.
- Fingers are separate with small gaps (millimetres) between them and against
  the palm. At a 1 cm surface cell snappyHexMesh will not resolve these and
  will treat the hand roughly as a closed fist; refine there if hands matter.
- The grounded foot is pitched 5 deg toe-up so the heel is one lowest point
  instead of a flat sole lying on z = 0; the sole is within a few millimetres of
  the ground near the heel, which gives thin cells against a moving-ground
  wall. Lift the figure by a few millimetres or cut a contact pad if
  snappyHexMesh struggles there.
- Self-intersection testing uses pymeshlab's face-face test plus the fold
  check above; no second independent intersection checker was run.
"""
    (OUT / "README.md").write_text(txt)


if __name__ == "__main__":
    main()
