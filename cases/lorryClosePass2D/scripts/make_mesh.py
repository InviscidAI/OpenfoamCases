#!/usr/bin/env python3
"""The 2-D background mesh: the lorry's section at z = 1.3 m in a 132 x 70 m box, one cell thick.

    python3 scripts/make_mesh.py geometry/lorry_z1p3_r_outline.csv runs/mesh/background.msh

The plane z = 0.8 m is meshed with gmsh (Mesh.Algorithm 6, quads recombined where they
fit, triangles elsewhere) and extruded 1 m in z as one layer of hexahedra and prisms. The
cell size is the smallest of three fields:

- 2 cm in a corridor x -38 to 43 m, y -3.6 to -1.275 m, through which both riders pass,
  growing to 1 m over 2 m outside it;
- 1 cm in a band along the lorry's passing side, y -1.55 to -1.265 m, x -0.2 to 16.7 m,
  so the 30 cm gap holds about 30 cells across;
- 1 cm on the lorry's outline, growing to 0.4 m 3 m away.

The boxes carry z limits (0 to 3 m): a gmsh Box's z limits default to 0, and without them
both boxes lie 0.8 m off the meshed plane and refine nothing. Blossom recombination is
off (Mesh.RecombinationAlgorithm 0): with it, gmsh ran for over 20 minutes on 2.1 million
triangles. The solved runs' mesh is this script's output: 787,842 cells.

Physical groups, which gmshToFoam makes patches: inlet (x = 62 m), outlet (x = -70 m),
farSides (y = +-35 m), lorryWall, and frontAndBack (the two z faces, made empty by Allrun).
"""
import csv
import math
import sys

import gmsh


def readloops(fn):
    d = {}
    with open(fn) as f:
        for r in csv.DictReader(f):
            d.setdefault(int(r["loop"]), []).append((float(r["x_m"]), float(r["y_m"])))
    for k, p in d.items():
        if p[-1] == p[0]:
            p.pop()
        # keep the outline's points, less any closer than 2 mm to the last one kept
        q = [p[0]]
        for a in p[1:]:
            if math.hypot(a[0] - q[-1][0], a[1] - q[-1][1]) >= 0.002:
                q.append(a)
        if len(q) > 3 and math.hypot(q[-1][0] - q[0][0], q[-1][1] - q[0][1]) < 0.002:
            q.pop()
        d[k] = q
    return list(d.values())


def polyloop(points, z, lc):
    pts = [gmsh.model.geo.addPoint(x, y, z, lc) for x, y in points]
    lines = [gmsh.model.geo.addLine(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    return gmsh.model.geo.addCurveLoop(lines), lines


def classify_and_write(surf, outfile):
    # one cell, 1 m thick
    out = gmsh.model.geo.extrude([(2, surf)], 0, 0, 1.0, numElements=[1], recombine=True)
    gmsh.model.geo.synchronize()
    vols = [t for d, t in out if d == 3]
    horiz, inlet, outlet, sides, walls = [], [], [], [], []
    for _, t in gmsh.model.getEntities(2):
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(2, t)
        if zmax - zmin < 1e-7:
            horiz.append(t)
        elif xmin > 61.999:
            inlet.append(t)
        elif xmax < -69.999:
            outlet.append(t)
        elif ymin < -34.999 or ymax > 34.999:
            sides.append(t)
        else:
            walls.append(t)
    gmsh.model.addPhysicalGroup(3, vols, name="fluid")
    gmsh.model.addPhysicalGroup(2, horiz, name="frontAndBack")
    gmsh.model.addPhysicalGroup(2, inlet, name="inlet")
    gmsh.model.addPhysicalGroup(2, outlet, name="outlet")
    gmsh.model.addPhysicalGroup(2, sides, name="farSides")
    gmsh.model.addPhysicalGroup(2, walls, name="lorryWall")
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.RecombineAll", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.model.mesh.generate(3)
    gmsh.write(outfile)
    return {k: len(v) for k, v in [("horiz", horiz), ("inlet", inlet), ("outlet", outlet),
                                    ("sides", sides), ("walls", walls)]}


def background(outline, outfile):
    gmsh.initialize()
    gmsh.model.add("background")
    z = 0.8
    xmin, xmax, ymin, ymax = -70, 62, -35, 35
    po = [gmsh.model.geo.addPoint(x, y, z, 1.0)
          for x, y in [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]]
    ol = [gmsh.model.geo.addLine(po[i], po[(i + 1) % 4]) for i in range(4)]
    outer = gmsh.model.geo.addCurveLoop(ol)
    holes, allwall = [], []
    for p in readloops(outline):
        loop, lines = polyloop(p, z, 0.01)
        holes.append(loop)
        allwall += lines
    s = gmsh.model.geo.addPlaneSurface([outer] + holes)
    gmsh.model.geo.synchronize()
    # the riders' corridor at 2 cm, and a 1 cm band along the lorry's passing side
    fbox = gmsh.model.mesh.field.add("Box")
    for key, val in [("VIn", 0.02), ("VOut", 1.0), ("XMin", -38), ("XMax", 43), ("YMin", -3.6),
                     ("YMax", -1.275), ("ZMin", 0.0), ("ZMax", 3.0), ("Thickness", 2.0)]:
        gmsh.model.mesh.field.setNumber(fbox, key, val)
    fband = gmsh.model.mesh.field.add("Box")
    for key, val in [("VIn", 0.01), ("VOut", 1.0), ("XMin", -0.2), ("XMax", 16.7), ("YMin", -1.55),
                     ("YMax", -1.265), ("ZMin", 0.0), ("ZMax", 3.0), ("Thickness", 0.1)]:
        gmsh.model.mesh.field.setNumber(fband, key, val)
    fd = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(fd, "CurvesList", allwall)
    gmsh.model.mesh.field.setNumber(fd, "Sampling", 500)
    ft = gmsh.model.mesh.field.add("Threshold")
    for key, val in [("InField", fd), ("SizeMin", 0.01), ("SizeMax", 0.4), ("DistMin", 0.015),
                     ("DistMax", 3.0)]:
        gmsh.model.mesh.field.setNumber(ft, key, val)
    fm = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(fm, "FieldsList", [fbox, fband, ft])
    gmsh.model.mesh.field.setAsBackgroundMesh(fm)
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.003)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 1.0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 0)
    print(classify_and_write(s, outfile))
    gmsh.finalize()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__.split("\n\n")[1])
    background(sys.argv[1], sys.argv[2])
