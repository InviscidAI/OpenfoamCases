"""2-D mesh of the roof section for one variant, written by gmsh as a one-cell-deep mesh 1 m thick.

usage: make_mesh.py <vented|buried> <out.msh> [scale]   (Python with gmsh 4.15.2 from pip)

Quad-dominant (frontal-Delaunay for quads, recombined): 3 mm at the deck, the insulation and the
openings, growing to 12 mm in the attic's middle; 2.5 mm in the vent slots, 4 mm in the
overhangs and the airway under the baffle. `scale` multiplies every size: the solved runs used
1.5 (4.5 mm, 18 mm, 3.75 mm and 6 mm), the smoke tests 2.
"""
import sys
import gmsh
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import roof

variant, out = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
NEAR, FAR, SLOT, EAVE = 0.003 * scale, 0.012 * scale, 0.0025 * scale, 0.004 * scale

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.model.add("roof")
geo = gmsh.model.geo

poly = roof.polygon(variant)
n = len(poly)
P = [geo.addPoint(x, y, 0) for x, y, _ in poly]
# The vent slots are structured blocks of square cells joined to the rest at their mouths: in an
# unstructured slot the corner slivers set the time step (smoke test, 19 Oct 2026).
vents = [i for i, p in enumerate(poly) if p[2] == "soffitVent"]   # segment i -> i+1 is the vent
inner = {k for i in vents for k in (i, i + 1)}
main = [k for k in range(1, n - 1) if k not in inner]               # point 0 and n-1 are the ridge vent's top
lines, names = [], []
mouth = {}
loop_main = []
for a_, b_ in zip(main, main[1:] + main[:1]):
    if b_ == a_ + 1:
        l = geo.addLine(P[a_], P[b_])
        lines.append(l); names.append(poly[a_][2]); loop_main.append(l)
    else:                                                           # a slot's mouth, or the ridge's
        l = geo.addLine(P[a_], P[b_])
        mouth[(a_, b_)] = l; loop_main.append(l)
surfaces = [geo.addPlaneSurface([geo.addCurveLoop(loop_main)])]
slot_loops = []
for i in vents:                       # i-1 -> i -> i+1 -> i+2, closed by the mouth i+2 -> i-1
    slot_loops.append([(i - 1, i), (i, i + 1), (i + 1, i + 2), (i + 2, i - 1)])
slot_loops.append([(n - 2, n - 1), (n - 1, 0), (0, 1), (1, n - 2)])  # the ridge vent
for loop in slot_loops:
    ls = []
    for a_, b_ in loop:
        if (b_, a_) in mouth:
            ls.append(-mouth[(b_, a_)])
        else:
            l = geo.addLine(P[a_], P[b_])
            lines.append(l); names.append(poly[a_][2]); ls.append(l)
    surfaces.append(geo.addPlaneSurface([geo.addCurveLoop(ls)]))
    w = abs(poly[loop[1][0]][0] - poly[loop[1][1]][0]) or abs(poly[loop[0][0]][0] - poly[loop[0][1]][0])
    h = max(abs(poly[a_][1] - poly[b_][1]) for a_, b_ in loop)
    nw, nh = max(2, round(w / SLOT)) + 1, max(2, round(h / SLOT)) + 1
    for (a_, b_), l in zip(loop, ls):
        horizontal = abs(poly[a_][1] - poly[b_][1]) < 1e-9
        geo.mesh.setTransfiniteCurve(abs(l), nw if horizontal else nh)
    geo.mesh.setTransfiniteSurface(surfaces[-1])
    geo.mesh.setRecombine(2, surfaces[-1])
geo.synchronize()

walls = [l for l, n in zip(lines, names) if n in ("deck", "insulation", "wall", "fascia", "soffit", "ridgeSides")]
openings = [l for l, n in zip(lines, names) if n in ("soffitVent", "ridge")]
f = gmsh.model.mesh.field
dist = f.add("Distance")
f.setNumbers(dist, "CurvesList", walls + openings)
f.setNumber(dist, "Sampling", 2000)
thr = f.add("Threshold")
f.setNumber(thr, "InField", dist)
f.setNumber(thr, "SizeMin", NEAR)
f.setNumber(thr, "SizeMax", FAR)
f.setNumber(thr, "DistMin", 0.006)
f.setNumber(thr, "DistMax", 0.15)
fields = [thr]


def box(x0, x1, y0, y1, size):
    b = f.add("Box")
    for k, v in (("XMin", x0), ("XMax", x1), ("YMin", y0), ("YMax", y1), ("ZMin", -1), ("ZMax", 1),
                 ("VIn", size), ("VOut", FAR), ("Thickness", 0.02)):
        f.setNumber(b, k, v)
    fields.append(b)


# the ridge vent's slot and the air just under it
box(-0.05, 0.05, roof.deck(0.05) - 0.03, roof.RIDGE_TOP + 0.01, SLOT)
if variant == "vented":
    for s in (-1, 1):
        xs = s * (roof.W2 + roof.OH / 2)
        box(xs - 0.03, xs + 0.03, roof.SOFFIT_Y - roof.BOARD - 0.01, roof.SOFFIT_Y + 0.03, SLOT)
        lo, hi = sorted((s * (roof.x_full_vented() - 0.05), s * (roof.W2 + roof.OH + 0.01)))
        box(lo, hi, roof.SOFFIT_Y - 0.03, roof.D_INS + roof.CH + 0.03, EAVE)
mn = f.add("Min")
f.setNumbers(mn, "FieldsList", fields)
f.setAsBackgroundMesh(mn)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.Algorithm", 8)
gmsh.option.setNumber("Mesh.RecombineAll", 1)
gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)

ext = geo.extrude([(2, sf) for sf in surfaces], 0, 0, 1.0, numElements=[1], recombine=True)
geo.synchronize()
vols = [e[1] for e in ext if e[0] == 3]
gmsh.model.addPhysicalGroup(3, vols, name="air")
# each lateral surface is found by the curve it was swept from: same x-y end points
lat = {}
for dim, tag in gmsh.model.getEntities(2):
    bb = gmsh.model.getBoundingBox(dim, tag)
    if abs(bb[5] - bb[2]) > 0.5:                     # spans the 1 m depth: a lateral surface
        lat[tag] = bb
front_back = [tag for dim, tag in gmsh.model.getEntities(2) if tag not in lat]
gmsh.model.addPhysicalGroup(2, front_back, name="frontAndBack")
groups = {}
for l, nm in zip(lines, names):
    bl = gmsh.model.getBoundingBox(1, l)
    for tag, bb in lat.items():
        if all(abs(bb[k] - bl[k]) < 1e-9 for k in (0, 1, 3, 4)):
            groups.setdefault(nm, []).append(tag)
            break
    else:
        raise SystemExit(f"no lateral surface for curve {l} ({nm})")
for nm, tags in groups.items():
    gmsh.model.addPhysicalGroup(2, tags, name=nm)
gmsh.model.mesh.generate(3)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write(out)
gmsh.finalize()
