#!/usr/bin/env python3
"""Closed STL surfaces of the unit's casing and of the cover, for snappyHexMesh.

The casing is a closed box from the coil to the grille whose only openings are the coil's
back face and the grille; the cover is the lid, the corner post and the sloped boards.
Solids that touch the symmetry plane (z = 0) or the house wall (x = 0) are carried 0.05 m
past it, so that snappyHexMesh cuts them with the domain boundary.
The top board of each louvred panel is filled out to the lid with a 7 mm x 10 mm wedge,
so that board and lid share a face instead of a single edge.
Needs the gmsh Python module (4.15.2 wrote the solved runs' surfaces).
Usage: python3 make_stl.py <output dir>
"""
import math, sys
import gmsh

out = sys.argv[1]
E = 0.05                       # overshoot past the symmetry plane and the house wall
gmsh.initialize()
gmsh.option.setNumber('General.Terminal', 0)
occ = gmsh.model.occ


def box(x0, y0, z0, x1, y1, z1):
    return (3, occ.addBox(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0))


def write(name, parts, size):
    occ.synchronize()
    if len(parts) > 1:
        fused, _ = occ.fuse([parts[0]], parts[1:])
    else:
        fused = parts
    occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', size)
    gmsh.option.setNumber('Mesh.MeshSizeMin', size / 4)
    gmsh.model.mesh.generate(2)
    gmsh.write(f'{out}/{name}.stl')
    vols = gmsh.model.getEntities(3)
    print(name, 'volumes after fuse:', len(vols),
          'volume', sum(occ.getMass(d, t) for d, t in vols))
    gmsh.model.mesh.clear()
    occ.remove(gmsh.model.getEntities(3), recursive=True)
    occ.synchronize()


# Casing: back strips round the coil, plenum plates, forward block less the fan duct.
gmsh.model.add('casing')
casing = [
    box(.250, .300, -E, .290, .3125, .442), box(.250, 1.0275, -E, .290, 1.040, .442),
    box(.250, .3125, .430, .290, 1.0275, .442),
    box(.290, .300, -E, .450, .3125, .442), box(.290, 1.0275, -E, .450, 1.040, .442),
    box(.290, .3125, .430, .450, 1.0275, .442),
]
fwd = box(.450, .300, -E, .638, 1.040, .442)
duct = box(.449, .315, -2 * E, .639, .960, .3225)
fcut, _ = occ.cut([fwd], [duct])
casing += fcut
write('casing', casing, 0.02)

# Cover: lid, corner post, front and side louvre boards (Kreg plan: 0.089 x 0.0127 m boards,
# 0.0826 m pitch, 35 degrees down outward).
gmsh.model.add('cover')
cover = [box(-E, 1.100, -E, .775, 1.120, .625), box(.700, .030, .550, .775, 1.100, .625)]
a = math.radians(35)
rise = .075 * math.tan(a)
nx = -math.sin(a) * .0127
ny = -math.cos(a) * .0127
for side in ('front', 'side'):
    i = 0
    while True:
        yi = 1.1 - i * .0826
        if yi + ny < .03:
            break
        # (u, y): u is x for the front boards, z for the side boards
        poly = [(.700, yi), (.775, yi - rise), (.775 + nx, yi - rise + ny), (.700 + nx, yi + ny)]
        if i == 0:
            poly = [(.700 + nx, 1.1)] + poly       # wedge up to the lid
        if side == 'front':
            pts = [occ.addPoint(u, y, -E) for u, y in poly]
        else:
            pts = [occ.addPoint(-E, y, u - .700 + .550) for u, y in poly]
        ls = [occ.addLine(pts[j], pts[(j + 1) % len(pts)]) for j in range(len(pts))]
        face = occ.addPlaneSurface([occ.addCurveLoop(ls)])
        ex = occ.extrude([(2, face)], 0, 0, .550 + E) if side == 'front' else occ.extrude([(2, face)], .700 + E, 0, 0)
        cover += [q for q in ex if q[0] == 3]
        i += 1
    print(side, 'boards:', i)
write('cover', cover, 0.01)
gmsh.finalize()
