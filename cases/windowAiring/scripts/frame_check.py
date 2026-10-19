#!/usr/bin/env python3
"""One mid-plane frame per run with the solved geometry traced on it.

    python3 frame_check.py <out.png> <time> <run dir> [<run dir> ...] [--plane mid|side]

The cells are drawn as they are (no interpolation), coloured by temperature on 0-22 C;
the wall, the opening, the sash, the radiator box and the room's outline are drawn from the
coordinates make_case.py draws, so any gap between them and the coloured cells shows.
"""
import sys
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_case import TILT_TOP, SASH_IN, SASH_D

args = sys.argv[1:]
plane = "mid"
if "--plane" in args:
    i = args.index("--plane"); plane = args[i + 1]; del args[i:i + 2]
out, t, runs = args[0], args[1], args[2:]
fig, axs = plt.subplots(len(runs), 1, figsize=(11, 5.2 * len(runs)))
for ax, run in zip(np.atleast_1d(axs), runs):
    m = pv.read(f"{run}/postProcessing/planes/{t}/{plane}.vtp")
    pts = m.points[:, :2]
    faces = m.faces if hasattr(m, "faces") else m.polys
    polys, i = [], 0
    while i < len(faces):
        n = faces[i]; polys.append(pts[faces[i + 1:i + 1 + n]]); i += n + 1
    T = m.cell_data["T"] - 273.15
    pc = PolyCollection(polys, array=T, cmap="coolwarm", clim=(0, 22), edgecolors="none")
    ax.add_collection(pc)
    # outlines as make_case.py draws them
    k = dict(color="k", lw=1.2)
    ax.plot([0, 4, 4, 0, 0], [0, 0, 2.4, 2.4, 0.0], **k)                       # room
    ax.plot([-0.24, -0.24, 0, 0], [-1, 0.9, 0.9, 0], **k)                      # wall below
    ax.plot([-0.24, -0.24, 0, 0], [3.4, 2.1, 2.1, 2.4], **k)                   # wall above
    ax.add_patch(plt.Rectangle((0.040, 0.15), 0.083, 0.60, fill=False, ec="m", lw=1.2))
    if run.rstrip("/").endswith("tilted-thin"):
        ax.plot([0, 0.14], [0.9, 2.1], color="lime", lw=2)                     # thin sash
    elif "tilted" in run:                                                      # solid sash
        x0 = -SASH_IN
        ax.add_patch(plt.Polygon([(x0, 0.9), (x0 + SASH_D, 0.9), (x0 + SASH_D + TILT_TOP, 2.1),
                                  (x0 + TILT_TOP, 2.1)], fill=False, ec="lime", lw=1.5))
    ax.set_xlim(-1.74, 4.0); ax.set_ylim(-1.0, 3.4); ax.set_aspect("equal")
    s = m.cell_data["s"]; c = m.cell_centers().points
    room = c[:, 0] > 0
    ax.set_title(f"{run.rstrip('/').split('/')[-1]}, {plane} plane, t = {t} s: T {T.min():.1f}..{T.max():.1f} C, "
                 f"plane's room cells mean s {s[room].mean():.3f}")
    fig.colorbar(pc, ax=ax, label="T (C)")
fig.tight_layout(); fig.savefig(out, dpi=100)
