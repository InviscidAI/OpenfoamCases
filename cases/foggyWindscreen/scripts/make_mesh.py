"""2-D mesh of the cabin section, one cell deep and 1 m thick, written by gmsh.

usage: $PYTHON make_mesh.py <geometry.json> <out.msh> [scale] [png]   (gmsh 4.15.2 for Python)

The rings come from geometry.py. The defrost duct is a structured block of square cells sharing its
mouth with the cabin (corner slivers in an unstructured slot set the time step).
The windscreen, the roof and the rear screen carry a layer of structured, graded quads 8.7 mm deep
whose first cell is 0.1 mm, y+ about 1 under a 3 m/s wall jet, so the heat and the vapour reaching
the glass come from the resolved gradient, not a wall function. The layer is three transfinite strips
meeting on the bisectors of the two roof corners and ending flush on the lips square to each screen's
foot; gmsh's BoundaryLayer field left a fan of sliver cells at the windscreen's foot that set the step.
`scale` multiplies every size except the layer's (a coarse smoke test).
"""
import json
import math
import sys

import gmsh

geo_json, out = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
png = sys.argv[4] if len(sys.argv) > 4 else None
G = json.load(open(geo_json))
NEAR, FAR, GLASS, DUCT = 0.008 * scale, 0.020 * scale, 0.006 * scale, 0.004 * scale
BL_FIRST, BL_RATIO, BL_N = 1.0e-4, 1.2, 16
BL_THICK = BL_FIRST * (BL_RATIO ** BL_N - 1) / (BL_RATIO - 1)

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("cabin")
geo = gmsh.model.geo

duct_bot = [tuple(p) for p in G["duct"]]
lines, names = [], []          # every boundary curve and its patch
pt_cache = {}


def P(x, y):
    k = (round(x, 6), round(y, 6))
    if k not in pt_cache:
        pt_cache[k] = geo.addPoint(x, y, 0)
    return pt_cache[k]


def L(a, b, name):
    l = geo.addLine(P(*a), P(*b))
    if name is not None:
        lines.append(l)
        names.append(name)
    return l


loops = []
duct_loop = None
W0, W1, R1, RF = [tuple(p) for p in G["layer"]]


def unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def inward(a, b):
    d = unit((b[0] - a[0], b[1] - a[1]))
    return (d[1], -d[0])           # the air lies to the right of the walls' direction of travel


def offset_corner(p, n1, n2):
    b = unit((n1[0] + n2[0], n1[1] + n2[1]))
    t = BL_THICK / (b[0] * n1[0] + b[1] * n1[1])
    return (p[0] + t * b[0], p[1] + t * b[1])


nW, nR, nB = inward(W0, W1), inward(W1, R1), inward(R1, RF)
I0 = (W0[0] + BL_THICK * nW[0], W0[1] + BL_THICK * nW[1])
I1 = offset_corner(W1, nW, nR)
I2 = offset_corner(R1, nR, nB)
I3 = (RF[0] + BL_THICK * nB[0], RF[1] + BL_THICK * nB[1])
inner = [geo.addLine(P(*I0), P(*I1)), geo.addLine(P(*I1), P(*I2)), geo.addLine(P(*I2), P(*I3))]
for ri, ring in enumerate(G["rings"]):
    n = len(ring)
    pts = [(r[0], r[1]) for r in ring]
    nm = [r[2] for r in ring]
    if ri == 0:
        # the duct: the inlet segment and its two walls leave the cabin's ring; the mouth closes it
        i_in = nm.index("defrost")
        i_rear, i_front = (i_in - 1) % n, (i_in + 1) % n      # top-rear -> bottom-rear, bottom-front -> top-front
        top_rear, bot_rear = pts[i_rear], pts[i_in]
        bot_front, top_front = pts[i_front], pts[(i_front + 1) % n]
        mouth = geo.addLine(P(*top_rear), P(*top_front))
        iw0 = min(range(n), key=lambda k: math.dist(pts[k], W0))
        irf = min(range(n), key=lambda k: math.dist(pts[k], RF))
        assert math.dist(pts[iw0], W0) < 1e-6 and math.dist(pts[irf], RF) < 1e-6
        ls = []
        i = (i_front + 1) % n
        while i != i_rear:
            if i == (iw0 - 1) % n:                     # the windscreen's lip, up to the layer
                ls.append(L(pts[i], I0, nm[i]))
                ls += inner
                i = irf
                ls.append(L(I3, pts[(i + 1) % n], nm[i]))  # the rear lip, below the layer
                i = (i + 1) % n
                continue
            ls.append(L(pts[i], pts[(i + 1) % n], nm[i]))
            i = (i + 1) % n
        ls.append(mouth)
        loops.append(geo.addCurveLoop(ls))
        dl = [L(top_rear, bot_rear, "trim"), L(bot_rear, bot_front, "defrost"),
              L(bot_front, top_front, "trim"), -mouth]
        duct_loop = dl
    else:
        ls = [L(pts[i], pts[(i + 1) % n], nm[i]) for i in range(n)]
        loops.append(geo.addCurveLoop(ls))

# the three strips: wall, far end, inner edge (shared with the core), near end
strips = []
glass_curves = []
for (a_, b_, ia, ib, wall, end_a, end_b) in ((W0, W1, I0, I1, "windscreen", "trim", None),
                                            (W1, R1, I1, I2, "roof", None, None),
                                            (R1, RF, I2, I3, "rearScreen", None, "trim")):
    cw = L(a_, b_, wall)
    ce = geo.addLine(P(*b_), P(*ib)) if end_b is None else L(b_, ib, end_b)
    ci = inner[len(strips)]
    ca = geo.addLine(P(*ia), P(*a_)) if end_a is None else L(ia, a_, end_a)
    s = geo.addPlaneSurface([geo.addCurveLoop([cw, ce, -ci, ca])])
    nl = max(2, round(math.dist(a_, b_) / GLASS)) + 1
    geo.mesh.setTransfiniteCurve(cw, nl)
    geo.mesh.setTransfiniteCurve(ci, nl)
    geo.mesh.setTransfiniteCurve(ce, BL_N + 1, "Progression", BL_RATIO)        # wall -> inner: growing
    geo.mesh.setTransfiniteCurve(ca, BL_N + 1, "Progression", 1 / BL_RATIO)    # inner -> wall: shrinking
    geo.mesh.setTransfiniteSurface(s)
    geo.mesh.setRecombine(2, s)
    strips.append(s)
    glass_curves.append(cw)

cabin = geo.addPlaneSurface(loops)
duct = geo.addPlaneSurface([geo.addCurveLoop(duct_loop)])
w = math.dist(top_rear, top_front)
h = math.dist(top_rear, bot_rear)
nw, nh = max(2, round(w / DUCT)) + 1, max(2, round(h / DUCT)) + 1
for l, k in zip(duct_loop, (nh, nw, nh, nw)):
    geo.mesh.setTransfiniteCurve(abs(l), k)
geo.mesh.setTransfiniteSurface(duct)
geo.mesh.setRecombine(2, duct)
geo.synchronize()

f = gmsh.model.mesh.field
walls = [l for l, n in zip(lines, names) if n not in ("windscreen", "rearScreen", "roof")]
fields = []


def threshold(curves, smin, dmin, dmax):
    d = f.add("Distance")
    f.setNumbers(d, "CurvesList", curves)
    f.setNumber(d, "Sampling", 400)
    t = f.add("Threshold")
    for k, v in (("InField", d), ("SizeMin", smin), ("SizeMax", FAR), ("DistMin", dmin),
                 ("DistMax", dmax), ("StopAtDistMax", 1)):
        f.setNumber(t, k, v)
    fields.append(t)


threshold(inner, GLASS, 0.05, 0.15)              # the wall jet up the screen and its edge
threshold(walls, NEAR, 0.01, 0.10)
threshold([mouth], DUCT, 0.01, 0.08)             # the jet leaving the duct
# a constant background: Threshold with StopAtDistMax returns a large value far away
bg = f.add("MathEval")
f.setString(bg, "F", f"{FAR}")
fields.append(bg)
mn = f.add("Min")
f.setNumbers(mn, "FieldsList", fields)
f.setAsBackgroundMesh(mn)


gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.Algorithm", 8)
gmsh.option.setNumber("Mesh.RecombineAll", 1)
gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)

ext = geo.extrude([(2, cabin), (2, duct)] + [(2, s) for s in strips], 0, 0, 1.0, numElements=[1], recombine=True)
geo.synchronize()
vols = [e[1] for e in ext if e[0] == 3]
gmsh.model.addPhysicalGroup(3, vols, name="air")
lat = {}
for dim, tag in gmsh.model.getEntities(2):
    bb = gmsh.model.getBoundingBox(dim, tag)
    if abs(bb[5] - bb[2]) > 0.5:
        lat[tag] = bb
front_back = [tag for dim, tag in gmsh.model.getEntities(2) if tag not in lat]
gmsh.model.addPhysicalGroup(2, front_back, name="frontAndBack")
groups = {}
for l, nm in zip(lines, names):
    b = gmsh.model.getBoundingBox(1, l)
    for tag, bb in lat.items():
        if all(abs(bb[k] - b[k]) < 1e-9 for k in (0, 1, 3, 4)):
            groups.setdefault(nm, []).append(tag)
            break
    else:
        raise SystemExit(f"no lateral surface for curve {l} ({nm})")
for nm, tags in groups.items():
    gmsh.model.addPhysicalGroup(2, tags, name=nm)
gmsh.model.mesh.generate(3)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write(out)

if png:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    polys = []
    for s in [cabin, duct] + strips:
        types, tags, nodes = gmsh.model.mesh.getElements(2, s)
        for t, nd in zip(types, nodes):
            k = gmsh.model.mesh.getElementProperties(t)[3]
            nd = np.array(nd).reshape(-1, k)
            for e in nd:
                polys.append([gmsh.model.mesh.getNode(int(i))[0][:2] for i in e])
    print(f"{len(polys)} cells in the section")
    for name, (x0, x1, y0, y1) in {"all": (-0.32, 2.65, -0.02, 1.3), "foot": (-0.03, 0.2, 0.69, 0.88), "rear": (2.2, 2.65, 0.85, 1.3),
                                  "top": (0.85, 1.1, 1.17, 1.3)}.items():
        fig, ax = plt.subplots(figsize=(12, 6) if name == "all" else (8, 6))
        ax.add_collection(PolyCollection(polys, facecolor="none", edgecolor="k", lw=0.15 if name == "all" else 0.4))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
        fig.savefig(png.replace(".png", f"_{name}.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)
gmsh.finalize()
