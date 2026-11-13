"""Adelie penguin in a glide posture: body plus two flippers held straight out.

Writes, into the folder given as the first argument (default ../geometry):
  penguin.stl          closed surface, metres, bill tip at x = 0, x towards the tail,
                       y to the right flipper, z up; the bird at 0 degrees (body axis level)
  penguin_profile.csv  the side outline in the plane y = 0 (the 2-D section), closed polyline
  penguin_dims.json    length, depth, width, span, areas and aspect ratios measured off the mesh
  penguin_views.png    side, top and front views for checking by eye

Sizes (sources in ../README.md, "The bird"):
  length bill tip to tail tip 0.70 m; body depth 0.145 m and width 0.140 m at x = 0.30 m;
  bill 40 mm long and 20 mm deep at its base; flippers 0.205 m from root to tip, root chord
  65 mm, mean chord about 48 mm (aspect ratio about 4.2), 6.5 mm thick at the root.
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon
from shapely.ops import unary_union

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "geometry"
OUT.mkdir(parents=True, exist_ok=True)

L = 0.70
# x, upper outline z, lower outline z, half-width (all metres)
CP = np.array([
    [0.000, 0.000, -0.002, 0.0010],
    [0.040, 0.010, -0.010, 0.0100],
    [0.055, 0.030, -0.022, 0.0250],
    [0.080, 0.048, -0.034, 0.0360],
    [0.110, 0.052, -0.043, 0.0400],
    [0.145, 0.049, -0.053, 0.0460],
    [0.220, 0.062, -0.075, 0.0660],
    [0.300, 0.068, -0.087, 0.0750],
    [0.380, 0.066, -0.085, 0.0730],
    [0.460, 0.055, -0.070, 0.0620],
    [0.540, 0.038, -0.045, 0.0450],
    [0.600, 0.022, -0.022, 0.0320],
    [0.650, 0.010, -0.004, 0.0300],
    [0.700, 0.003, 0.000, 0.0150],
])
# slimmed by 6.5% from the first drawing so that a 4.8 kg bird comes out near 0.86 kg/L
# (penguins are near neutral in water with the air in their plumage); bill rows unchanged
CP[2:, 1:] *= 0.935
zu_f = PchipInterpolator(CP[:, 0], CP[:, 1])
zl_f = PchipInterpolator(CP[:, 0], CP[:, 2])
w_f = PchipInterpolator(CP[:, 0], CP[:, 3])


def body_mesh(nx=220, nt=96):
    s = np.linspace(0.0, np.pi, nx)
    xs = 0.5 * L * (1 - np.cos(s))           # clustered at the bill and the tail
    xs = xs[1:-1]
    th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    verts = [[0.0, 0.0, 0.5 * (zu_f(0.0) + zl_f(0.0))]]
    for x in xs:
        zc = 0.5 * (zu_f(x) + zl_f(x))
        a = 0.5 * (zu_f(x) - zl_f(x))
        w = w_f(x)
        for t in th:
            verts.append([x, w * np.sin(t), zc + a * np.cos(t)])
    verts.append([L, 0.0, 0.5 * (zu_f(L) + zl_f(L))])
    verts = np.array(verts)
    faces = []
    nr = len(xs)
    tip0, tip1 = 0, len(verts) - 1
    ring = lambda i, j: 1 + i * nt + (j % nt)
    for j in range(nt):
        faces.append([tip0, ring(0, j + 1), ring(0, j)])
    for i in range(nr - 1):
        for j in range(nt):
            a, b, c, d = ring(i, j), ring(i, j + 1), ring(i + 1, j + 1), ring(i + 1, j)
            faces += [[a, b, c], [a, c, d]]
    for j in range(nt):
        faces.append([tip1, ring(nr - 1, j), ring(nr - 1, j + 1)])
    m = trimesh.Trimesh(verts, np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


FL_SPAN = 0.205         # root to tip, exposed
FL_Z = 0.015            # height of the flipper's chord plane
FL_XLE_ROOT = 0.170
FL_SWEEP = 0.020        # leading edge moves back this much from root to tip
FL_C_ROOT, FL_C_80 = 0.065, 0.040
FL_TC_ROOT, FL_TC_TIP = 0.10, 0.07


def flipper_chord(s):
    c = FL_C_ROOT + (FL_C_80 - FL_C_ROOT) * np.minimum(s, 0.8) / 0.8
    tip = np.where(s > 0.8, np.sqrt(np.clip(1 - ((s - 0.8) / 0.2) ** 2, 0, 1)), 1.0)
    return np.maximum(c * tip, 0.0)


def naca00(xc, tc):
    return 5 * tc * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1036 * xc**4)


def flipper_mesh(side=+1, ns=70, nc=60):
    y_root_exposed = float(w_f(FL_XLE_ROOT + 0.5 * FL_C_ROOT))
    y_in = 0.45 * y_root_exposed          # starts inside the body so the union is clean
    ss = np.concatenate([[-(y_root_exposed - y_in) / FL_SPAN], np.linspace(0, 1, ns)])
    ss[-1] = 0.9995
    beta = np.linspace(0, np.pi, nc)
    xc = 0.5 * (1 - np.cos(beta))
    verts, rings = [], []
    for s in ss:
        se = max(s, 0.0)
        c = flipper_chord(np.array(se)).item()
        c = max(c, 1e-4)
        xle = FL_XLE_ROOT + FL_SWEEP * se
        tc = FL_TC_ROOT + (FL_TC_TIP - FL_TC_ROOT) * se
        yt = naca00(xc, tc) * c
        yt[-1] = max(yt[-1], 2.5e-4)      # blunt trailing edge, 0.5 mm
        y = y_root_exposed + s * FL_SPAN
        upper = [[xle + c * xc[k], side * y, FL_Z + yt[k]] for k in range(nc)]
        lower = [[xle + c * xc[k], side * y, FL_Z - yt[k]] for k in range(nc - 2, 0, -1)]
        r0 = len(verts)
        verts += upper + lower
        rings.append((r0, len(upper) + len(lower)))
    faces = []
    for i in range(len(rings) - 1):
        (a0, n), (b0, _) = rings[i], rings[i + 1]
        for j in range(n):
            p, q = a0 + j, a0 + (j + 1) % n
            r, t = b0 + (j + 1) % n, b0 + j
            faces += [[p, q, r], [p, r, t]]
    # caps
    for (r0, n), flip in ((rings[0], True), (rings[-1], False)):
        cen = np.mean(np.array(verts[r0:r0 + n]), axis=0)
        ci = len(verts)
        verts.append(list(cen))
        for j in range(n):
            f = [ci, r0 + j, r0 + (j + 1) % n]
            faces.append(f[::-1] if flip else f)
    m = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
    m.fix_normals()
    if m.volume < 0:
        m.invert()
    return m


body = body_mesh()
fr = flipper_mesh(+1)
fl = flipper_mesh(-1)
for name, m in (("body", body), ("flipper_r", fr), ("flipper_l", fl)):
    assert m.is_watertight, f"{name} not closed"
bird = trimesh.boolean.union([body, fr, fl], engine="manifold")
assert bird.is_watertight and bird.is_winding_consistent
bird.export(OUT / "penguin.stl")

# the 2-D section: outline in y = 0
xs = np.linspace(0, L, 701)
up = np.c_[xs, zu_f(xs)]
lo = np.c_[xs[::-1], zl_f(xs[::-1])]
prof = np.vstack([up, lo[1:-1]])
np.savetxt(OUT / "penguin_profile.csv", prof, delimiter=",", header="x_m,z_m (closed, bill tip first, upper then lower)", comments="")

# measurements off the mesh
def proj_area(m, axes):
    polys = [Polygon(t[:, axes]) for t in m.triangles]
    polys = [p for p in polys if p.is_valid and p.area > 0]
    return unary_union(polys)

top = proj_area(bird, [0, 1])
side_poly = Polygon(prof)
fl_top = proj_area(fr, [0, 1])
y_root = float(w_f(FL_XLE_ROOT + 0.5 * FL_C_ROOT))
fl_exposed = fl_top.intersection(Polygon([(0, y_root), (L, y_root), (L, 1), (0, 1)]))
span = float(bird.bounds[1][1] - bird.bounds[0][1])
s_flippers = 2 * fl_exposed.area
s_strip = FL_C_ROOT * 2 * y_root          # body strip between the flipper roots (Pennycuick)
dims = {
    "length_m": float(bird.bounds[1][0] - bird.bounds[0][0]),
    "depth_max_m": float(np.max(zu_f(xs) - zl_f(xs))),
    "width_max_m": float(2 * np.max(w_f(xs))),
    "span_m": span,
    "flipper_exposed_span_m": FL_SPAN,
    "flipper_area_each_m2": fl_exposed.area,
    "flipper_mean_chord_m": fl_exposed.area / FL_SPAN,
    "flipper_aspect_ratio": FL_SPAN**2 / fl_exposed.area,
    "planform_area_whole_bird_m2": top.area,
    "wing_area_pennycuick_m2": s_flippers + s_strip,
    "aspect_ratio_pennycuick": span**2 / (s_flippers + s_strip),
    "side_section_area_m2": side_poly.area,
    "volume_m3": float(bird.volume),
    "surface_area_m2": float(bird.area),
    "stl_triangles": int(len(bird.faces)),
}
(OUT / "penguin_dims.json").write_text(json.dumps(dims, indent=1))
print(json.dumps(dims, indent=1))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(8, 10))
ax[0].fill(prof[:, 0], prof[:, 1], color="0.2"); ax[0].set_title("side (the 2-D section, y = 0)")
for g in getattr(top, "geoms", [top]):
    ax[1].fill(*g.exterior.xy, color="0.2")
ax[1].set_title(f"top, span {span:.3f} m")
fr_ = proj_area(bird, [1, 2])
for g in getattr(fr_, "geoms", [fr_]):
    ax[2].fill(*g.exterior.xy, color="0.2")
ax[2].set_title("front")
for a in ax:
    a.set_aspect("equal"); a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(OUT / "penguin_views.png", dpi=110)
