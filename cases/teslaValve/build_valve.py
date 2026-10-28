"""Build the 2-D Tesla valve and mesh it with gmsh.

    python3 build_valve.py <cell size in mm> <output .msh>

The valve is a straight channel with NSEG loops above it. Each loop leaves the
channel at THETA to the +x direction, turns up and round through 180 degrees and
comes back into the channel heading against +x. A tongue on the bottom wall necks
the channel between each loop's two mouths. Flow in +x is steered into the loops
and meets itself coming back: that is the blocking direction. Flow in -x passes
the loops' mouths and takes the channel: that is the easy direction.

Lengths are in millimetres here and written to the mesh in metres. The mesh is one
cell thick in z. The patches are `left` (x = 0), `right` (x = XEND), `walls` and
`frontAndBack`.
"""
import math
import sys
from collections import Counter

import gmsh
import numpy as np

# ---- parameters, mm --------------------------------------------------------------
W = 5.0            # channel width
R = 6.0            # centreline radius of every bend
THETA = 30.0       # angle at which a loop leaves the channel, to +x, degrees
ALPHA = 50.0       # the loop's first turn, upward, before the 180 degree return
L0, L1 = 1.0, 2.0  # straight runs before and between the two bends
NSEG = 4           # number of loops
PITCH = 25.0       # loop spacing in x
LEADIN = 15.0      # straight channel before the first loop
LEADOUT = 15.0     # and after the last
THICK = 1.0        # span in z, one cell
# the tongue: a trapezoid on the bottom wall, from TX0 to TX1 after each loop's
# take-off, its flat top TFLAT wide at y = YAPEX, so the throat is W/2 - YAPEX
TX0, TX1, YAPEX, TFLAT = 3.0, 10.5, 0.5, 1.0

H = float(sys.argv[1])
OUT = sys.argv[2]
XEND = LEADIN + NSEG * PITCH + LEADOUT


def centreline(start, heading, segs, ds=0.5, dang=4.0):
    """Points and headings along straights ('s', length) and arcs ('a', r, sweep)."""
    p = np.array(start, float)
    h = math.radians(heading)
    pts, hds = [p.copy()], [h]
    for s in segs:
        if s[0] == "s":
            n = max(2, int(s[1] / ds) + 1)
            for t in np.linspace(0, s[1], n)[1:]:
                pts.append(p + t * np.array([math.cos(h), math.sin(h)]))
                hds.append(h)
            p = pts[-1].copy()
        else:
            r, sw = s[1], math.radians(s[2])
            sgn = 1.0 if sw > 0 else -1.0
            c = p + r * sgn * np.array([-math.sin(h), math.cos(h)])
            a0 = math.atan2(p[1] - c[1], p[0] - c[0])
            n = max(3, int(abs(s[2]) / dang) + 1)
            for t in np.linspace(0, sw, n)[1:]:
                pts.append(c + r * np.array([math.cos(a0 + t), math.sin(a0 + t)]))
                hds.append(h + t)
            p = pts[-1].copy()
            h += sw
    return np.array(pts), np.array(hds)


# one loop's centreline, cut where it comes back to the channel's centreline
cl, hd = centreline((0, 0), THETA,
                    [("s", L0), ("a", R, ALPHA), ("s", L1), ("a", R, -(180.0 + ALPHA)), ("s", 60.0)])
for i in range(5, len(cl)):
    if cl[i, 1] <= 0.0:
        f = cl[i - 1, 1] / (cl[i - 1, 1] - cl[i, 1])
        cl = np.vstack([cl[:i], cl[i - 1] + f * (cl[i] - cl[i - 1])])
        hd = np.append(hd[:i], hd[i - 1] + f * (hd[i] - hd[i - 1]))
        break
nrm = np.stack([-np.sin(hd), np.cos(hd)], 1)
upper, lower = cl + 0.5 * W * nrm, cl - 0.5 * W * nrm
print(f"loop: re-enters {cl[-1, 0]:.2f} mm after it leaves, heading {math.degrees(hd[-1]):.1f} deg; "
      f"top of loop {cl[:, 1].max() + W / 2:.2f} mm above the centreline; "
      f"throat {W / 2 - YAPEX:.2f} mm")

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("teslaValve")
occ = gmsh.model.occ


def spline(P, dx):
    tags = [occ.addPoint(x + dx, y, 0.0) for x, y in P]
    return occ.addSpline(tags), tags


loops = []
for k in range(NSEG):
    dx = LEADIN + k * PITCH
    sU, tU = spline(upper, dx)
    sL, tL = spline(lower, dx)
    c0 = occ.addLine(tL[0], tU[0])
    c1 = occ.addLine(tU[-1], tL[-1])
    loops.append((2, occ.addPlaneSurface([occ.addCurveLoop([c0, sU, c1, -sL])])))
channel = occ.addRectangle(0.0, -W / 2, 0.0, XEND, W)
fluid, _ = occ.fuse([(2, channel)], loops)

tongues = []
for k in range(NSEG):
    dx = LEADIN + k * PITCH
    xm = dx + 0.5 * (TX0 + TX1)
    p = [occ.addPoint(dx + TX0, -W / 2, 0.0), occ.addPoint(dx + TX1, -W / 2, 0.0),
         occ.addPoint(xm + TFLAT / 2, YAPEX, 0.0), occ.addPoint(xm - TFLAT / 2, YAPEX, 0.0)]
    edges = [occ.addLine(p[i], p[(i + 1) % 4]) for i in range(4)]
    tongues.append((2, occ.addPlaneSurface([occ.addCurveLoop(edges)])))
fluid, _ = occ.cut(fluid, tongues)
occ.synchronize()
faces = [t for d, t in fluid if d == 2]


def end_edge(x):
    for f in faces:
        for _, c in gmsh.model.getBoundary([(2, f)], oriented=False):
            com = occ.getCenterOfMass(1, c)
            if abs(com[0] - x) < 1e-7 and abs(com[1]) < 1e-7 and abs(occ.getMass(1, c) - W) < 1e-6:
                return c
    raise RuntimeError(f"no end edge at x = {x}")


c_left, c_right = end_edge(0.0), end_edge(XEND)

ext = occ.extrude([(2, f) for f in faces], 0, 0, THICK, numElements=[1], recombine=True)
occ.synchronize()
vols = [t for d, t in ext if d == 3]
count = Counter(t for v in vols for d, t in gmsh.model.getBoundary([(3, v)], oriented=False) if d == 2)
bnd = [t for t, n in count.items() if n == 1]
backs = [t for t in bnd if t not in faces and abs(occ.getCenterOfMass(2, t)[2] - THICK) < 1e-9]
sides = [t for t in bnd if t not in faces and t not in backs]


def side_of(curve):
    for s in sides:
        if curve in [c for d, c in gmsh.model.getBoundary([(2, s)], oriented=False) if d == 1]:
            return s
    raise RuntimeError("side not found")


s_left, s_right = side_of(c_left), side_of(c_right)
gmsh.model.addPhysicalGroup(2, [s_left], name="left")
gmsh.model.addPhysicalGroup(2, [s_right], name="right")
gmsh.model.addPhysicalGroup(2, [s for s in sides if s not in (s_left, s_right)], name="walls")
gmsh.model.addPhysicalGroup(2, faces + backs, name="frontAndBack")
gmsh.model.addPhysicalGroup(3, vols, name="fluid")

gmsh.option.setNumber("Mesh.MeshSizeMin", 0.6 * H)
gmsh.option.setNumber("Mesh.MeshSizeMax", H)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm", 5)        # Delaunay
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.ScalingFactor", 0.001)  # mm -> m
gmsh.model.mesh.generate(3)
gmsh.write(OUT)
print("cells:", len(gmsh.model.mesh.getElements(3)[1][0]))
gmsh.finalize()
