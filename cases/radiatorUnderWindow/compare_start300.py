#!/usr/bin/env python3
"""Does the start300 re-solve (a write every 0.625 s) match the hour (a write every 7.5 s)
at the 40 times both wrote, 7.5, 15, ... 300 s?

The two are the same case from the same start, but with writeControl adjustableRunTime the
solver spreads the time to the next write over equal steps, so their steps differ from the
first (0.012 s against 0.012019 s) and the planes cannot be identical. For each run and
time: the temperature difference over the section's cells (RMS, 99th percentile, maximum,
and the share of cells off by more than 0.1 and 0.5 K), the RMS velocity difference against
the RMS speed, and each solve's room mean (roomMeanT).

    python3 compare_start300.py runs/hour runs/start300 > results/start300/vs_hour.txt
"""
import sys
from pathlib import Path

import numpy as np

from postprocess import monitor, section


def main():
    hour, start = Path(sys.argv[1]), Path(sys.argv[2])
    for run in ("window", "opposite"):
        mo, mn = monitor(hour / run, "roomMeanT"), monitor(start / run, "roomMeanT")
        print(f"{run}: hour (7.5 s writes) against start300 (0.625 s writes)")
        print("   t (s)  RMS dT  p99 |dT|  max |dT|  >0.1 K  >0.5 K  RMS dU / RMS U   "
              "room mean, hour / start300 (C)")
        worst = 0.0
        for k in range(1, 41):
            t = 7.5 * k
            fo = hour / run / "postProcessing/clip" / f"{t:g}" / "clip.vtp"
            fn = start / run / "postProcessing/clip" / f"{t:g}" / "clip.vtp"
            if not (fo.exists() and fn.exists()):
                continue
            xo, yo, Fo = section(fo)
            xn, yn, Fn = section(fn)
            if not (np.array_equal(xo, xn) and np.array_equal(yo, yn)):
                raise SystemExit(f"{run} {t:g}: the two planes' cells differ")
            dT = np.abs(Fn["T"] - Fo["T"])
            du = np.hypot(Fn["u"] - Fo["u"], Fn["v"] - Fo["v"])
            rel = np.sqrt((du ** 2).mean()) / np.sqrt((np.hypot(Fo["u"], Fo["v"]) ** 2).mean())
            worst = max(worst, dT.max())
            a, b = mo.get(round(t, 6), np.nan) - 273.15, mn.get(round(t, 6), np.nan) - 273.15
            print(f"  {t:6.1f}  {np.sqrt((dT ** 2).mean()):6.4f}  {np.percentile(dT, 99):8.4f}"
                  f"  {dT.max():8.4f}  {100 * (dT > 0.1).mean():5.2f}%  {100 * (dT > 0.5).mean():5.2f}%"
                  f"  {rel:14.3f}   {a:.4f} / {b:.4f}")
        print(f"  largest |dT| in any cell at any common time: {worst:.3f} K\n")


if __name__ == "__main__":
    main()
