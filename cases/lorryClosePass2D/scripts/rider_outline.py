#!/usr/bin/env python3
"""The rider's outline for the drag term: geometry/rider_z1p3_r_outline.csv -> constant/riderOutline.

    python3 scripts/rider_outline.py geometry/rider_z1p3_r_outline.csv runs/gap150/constant/riderOutline

An OpenFOAM list of 358 points (x, y, 0) in metres relative to his shoulder centre, x
forwards along his direction of travel, the closing point left out. The riderPenalty
source in constant/fvOptions reads it once and moves it with him.
"""
import csv
import sys


def main(src, out):
    with open(src) as f:
        pts = [(float(r["x_m"]), float(r["y_m"])) for r in csv.DictReader(f)]
    if pts[-1] == pts[0]:
        pts.pop()
    with open(out, "w") as f:
        f.write("// rider section at z = 1.3 m, relative to his shoulder centre (x forward), "
                "from rider_z1p3_r_outline.csv\n")
        f.write(f"{len(pts)}\n(\n")
        for x, y in pts:
            f.write(f"({x:.6f} {y:.6f} 0)\n")
        f.write(")\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__.split("\n\n")[1])
    main(*sys.argv[1:])
