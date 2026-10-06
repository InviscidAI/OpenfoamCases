#!/usr/bin/env python3
"""The rotating zone's boundary -> constant/triSurface/AMI.stl.

A closed cylinder round the spin axis (z), radius 0.38 m, from 0.10 m below the floor to
0.45 m up, in 192 segments, ASCII STL with zero normals. snappyHexMesh makes the cells
inside it the zone that turns with the cat, and its surface the sliding (AMI) interface.

    python3 scripts/make_ami.py [out.stl]
"""
import math
import sys
from pathlib import Path

n, r, z0, z1 = 192, 0.38, -0.10, 0.45
out = Path(sys.argv[1] if len(sys.argv) > 1 else
           Path(__file__).resolve().parents[1] / "constant/triSurface/AMI.stl")
tris = []
for i in range(n):
    a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
    p0 = (r * math.cos(a), r * math.sin(a), z0)
    p1 = (r * math.cos(b), r * math.sin(b), z0)
    q0 = (p0[0], p0[1], z1)
    q1 = (p1[0], p1[1], z1)
    tris += [(p0, p1, q1), (p0, q1, q0), ((0, 0, z0), p1, p0), ((0, 0, z1), q0, q1)]
lines = ["solid AMI"]
for t in tris:
    lines += ["facet normal 0 0 0", " outer loop"]
    lines += ["  vertex " + " ".join(f"{c:.12g}" for c in v) for v in t]
    lines += [" endloop", "endfacet"]
lines.append("endsolid AMI")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + "\n")
