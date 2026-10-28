"""How much of the flow goes round each loop, at the last written time of each run.

    python3 loop_split.py

Needs pyvista. For each loop it cuts the valve vertically through the top of the loop,
where the cut crosses the loop's arc and the channel below it, and integrates the
x-velocity over a 0.8 mm wide band of cells on each side of the cut. The loop's share
is the arc's flow over the total. A positive arc flow runs in +x over the top of the
loop: up from the mouth on the left, back down into the channel at the mouth on the
right, heading upstream against flow in +x. It is a snapshot, not a time average.
"""
import os

import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
LEADIN, PITCH, NSEG, HALF_W = 15.0, 25.0, 4, 2.5   # mm, as in build_valve.py
BAND = 0.8                                          # mm, width of the band of cells


def split(case):
    foam = os.path.join(case, "case.foam")
    open(foam, "a").close()
    rd = pv.OpenFOAMReader(foam)
    t = rd.time_values[-1]
    rd.set_active_time_value(t)
    m = rd.read()["internalMesh"]
    c = m.cell_centers().points * 1000.0
    ux = m.cell_data["U"][:, 0]
    vol = m.compute_cell_sizes()["Volume"] * 1e9    # mm3; the span is 1 mm
    rows = []
    for k in range(NSEG):
        x0 = LEADIN + k * PITCH
        in_loop = (c[:, 0] > x0) & (c[:, 0] < x0 + PITCH) & (c[:, 1] > HALF_W + 0.5)
        x_top = c[in_loop][np.argmax(c[in_loop][:, 1]), 0]
        band = np.abs(c[:, 0] - x_top) < BAND / 2
        arc = np.sum((ux * vol)[band & (c[:, 1] > HALF_W + 0.5)]) / BAND   # (m/s) mm
        chan = np.sum((ux * vol)[band & (c[:, 1] <= HALF_W + 0.5)]) / BAND
        rows.append((x_top, arc, chan))
    return t, rows


for direction in ("forward", "reverse"):
    case = os.path.join(HERE, "runs", direction)
    if not os.path.isdir(case):
        continue
    t, rows = split(case)
    print(f"{direction} at {t:g} s:")
    for k, (x, arc, chan) in enumerate(rows, 1):
        print(f"  loop {k} (top at x = {x:5.1f} mm): round the loop {arc / (arc + chan):5.1%}, "
              f"its flow {'+x' if arc > 0 else '-x'} over the top; "
              f"the cut carries {abs(arc + chan) / 2.5:.3f} of the inflow")
