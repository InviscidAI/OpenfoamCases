#!/usr/bin/env python3
"""The air's force on the rider, every time step, from a run's riderForceIB -> one CSV.

    python3 scripts/rider_force.py runs/gap150 results/rider_force_gap150.csv

riderForceIB (system/riderForceIB) writes "t (Fx Fy Fz) cells" every step to
postProcessing/riderForceIB/<start time>/force.dat, in N per metre of height, + x forwards
(along his direction of travel) and + y towards the lorry. A restarted run writes a second
directory from its start time; its rows replace the earlier run's from that time on, so
gap150's rows from 6.2 s are the restart's. A row cut short by a stopped run is skipped.

The CSV keeps every step: time rounded to 1 ns (the step is about 50 us), the force to
0.1 mN/m, Fz (zero in 2-D) left out, and the number of cells the drag term touched.
"""
import glob
import os
import sys


def read_forces(run):
    rows = {}
    dirs = sorted(glob.glob(f"{run}/postProcessing/riderForceIB/*"),
                  key=lambda p: float(os.path.basename(p)))
    for d in dirs:
        start = float(os.path.basename(d))
        for k in [k for k in rows if k >= start]:
            del rows[k]
        for line in open(f"{d}/force.dat"):
            if line.startswith("#") or not line.strip():
                continue
            v = line.replace("(", " ").replace(")", " ").split()
            if len(v) < 5:
                continue
            try:
                rows[float(v[0])] = (float(v[1]), float(v[2]), int(float(v[4])))
            except ValueError:
                continue
    return [(t,) + rows[t] for t in sorted(rows)]


def main(run, out):
    rows = read_forces(run)
    if not rows:
        sys.exit(f"no riderForceIB rows under {run}/postProcessing")
    with open(out, "w") as f:
        f.write("t_s,Fx_N_per_m,Fy_N_per_m,cells\n")
        for t, fx, fy, n in rows:
            f.write(f"{t:.9f},{fx:.4f},{fy:.4f},{n}\n")
    print(f"{run}: {len(rows)} steps, {rows[0][0]:.6f} to {rows[-1][0]:.6f} s -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__.split("\n\n")[1])
    main(*sys.argv[1:])
