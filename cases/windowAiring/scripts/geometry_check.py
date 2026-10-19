#!/usr/bin/env python3
"""Read the solved sash, opening and radiator off a run's mesh (0/C from
`postProcess -func writeCellCentres -time 0`), and write their extents.

    python3 geometry_check.py <run dir> [--thin]

On the solid tilted sash (run `tilted`), also give each face row's distance from the
sash's two faces as make_case.py draws them, and the widths of the gaps the mesh leaves: the
side gap at each height, between the frame's plane x = 0 and the sash's outer face, and the
top gap. `--thin` reads the superseded first build's thin sash, a baffle (patches sashA and sashB).
"""
import re, sys
import numpy as np

run = sys.argv[1]
thin = "--thin" in sys.argv
b = open(f"{run}/0/C", "rb").read()


def vecs(start):
    m = re.compile(rb"List<vector>\s*(\d+)\s*\(").search(b, start)
    n = int(m.group(1)); s = m.end()
    return np.frombuffer(b[s:s + 24 * n], dtype="<f8").reshape(n, 3)


bf = b.find(b"boundaryField")
faces = {}
for patch in (b"sashA", b"sash", b"walls", b"outerWalls", b"outside"):
    i = b.find(b"\n    " + patch + b"\n", bf)
    if i < 0 or b.find(b"nonuniform", i) > b.find(b"}", i):
        print(patch.decode(), "none"); continue
    f = faces[patch.decode()] = vecs(i)
    print(f"{patch.decode():10s} {len(f):6d} faces  x {f[:,0].min():.4f}..{f[:,0].max():.4f}"
          f"  y {f[:,1].min():.4f}..{f[:,1].max():.4f}  z {f[:,2].min():.4f}..{f[:,2].max():.4f}")

if thin and "sashA" in faces:
    f = faces["sashA"]
    d = f[:, 0] - 0.14 * (f[:, 1] - 0.90) / 1.20
    print(f"   sash faces off the line x = 0.14 (y - 0.9)/1.2: {d.min()*1000:+.1f} .. {d.max()*1000:+.1f} mm")
elif "sash" in faces:
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    from make_case import TILT_TOP, SASH_IN, SASH_D, WIN_Y0, WIN_Y1, WIN_HZ
    h = WIN_Y1 - WIN_Y0
    f = faces["sash"]
    xo = -SASH_IN + TILT_TOP * (f[:, 1] - WIN_Y0) / h            # the outer face as drawn
    xi = xo + SASH_D                                              # the room face as drawn
    mid = np.abs(f[:, 2]) < WIN_HZ - 1e-3                         # not the sash's ends
    d = np.minimum(np.abs(f[:, 0] - xo), np.abs(f[:, 0] - xi))
    print(f"   faces off the drawn outer or room face: {np.percentile(d[mid], 50)*1000:.1f} mm median, "
          f"{d[mid].max()*1000:.1f} mm at most (cells 20 mm across, 30 mm tall)")
    # the outer face as solved: in each 30 mm row, the smallest x of the sash's faces in the
    # room that face outdoors, against the frame's plane
    rows = np.round((f[:, 1] - WIN_Y0) / 0.03 - 0.5).astype(int)
    print("   row (y m): solved outer face x (mm) | drawn | gap to the frame's plane (mm)")
    for r in range(0, 40, 4):
        sel = (rows == r) & mid
        if not sel.any():
            continue
        y = WIN_Y0 + 0.03 * (r + 0.5)
        x = f[sel, 0].min()
        print(f"   {y:.3f}: {x*1000:+6.1f} | {(-SASH_IN + TILT_TOP*(y - WIN_Y0)/h)*1000:+6.1f} | {max(x, 0)*1000:5.1f}")
