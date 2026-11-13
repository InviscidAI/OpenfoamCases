#!/usr/bin/env python3
"""Each rider's mean drag over the averaging window, and the wake probes' statistics.

    python3 scripts/extract_results.py runs results

Reads runs/<line|alone>/postProcessing/rider<i>Forces and rider<i>Coeffs (every step)
and wakeProbes (every step). Where a run was restarted, its monitors have one directory
per start time; rows are merged by time, a later start winning at a repeated time.
Means are time-weighted (trapezoidal, the window's ends interpolated) over
config/case.json's window, 1.0-1.71 s. Drag is -Fx on the rider and both wheels.

Writes results/summary.txt, results/means.csv, results/history.csv (each rider's drag
averaged over 0.01 s bins from 0 to the window's end) and results/wake_probes.csv.
NumPy only.
"""
import json
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
cfg = json.loads((CASE / "config" / "case.json").read_text())
trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
START, END = cfg["window"]
MID = (START + END) / 2
Q = 0.5 * cfg["rho"] * cfg["speed"] ** 2 * cfg["Aref"]


def monitor(path, pattern):
    """Rows of every file matching pattern under path, merged by time, later starts winning."""
    def start(p):
        try:
            return float(p.parent.name)
        except ValueError:
            return -1.0
    rows = {}
    for f in sorted(path.rglob(pattern), key=lambda p: (start(p), p.name)):
        for line in f.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            vals = list(map(float, line.replace("(", " ").replace(")", " ").split()))
            rows[vals[0]] = vals
    a = np.asarray([rows[t] for t in sorted(rows)])
    if not np.isfinite(a).all():
        raise SystemExit(f"non-finite values in {path}")
    return a


def mean(t, y, a=START, b=END):
    if t[0] > a + 1e-7 or t[-1] < b - 1e-7:
        raise SystemExit(f"the window {a}-{b} s is not covered: {t[0]}-{t[-1]} s")
    ts = np.r_[a, t[(t > a) & (t < b)], b]
    return float(trap(np.interp(ts, t, y), ts) / (b - a))


def main():
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rows, hist, wakes = [], {}, []
    for run in ("alone", "line"):
        c = runs / run
        for i in range(1, cfg["riders"][run] + 1):
            f = monitor(c / "postProcessing" / f"rider{i}Forces", "force*.dat")
            cd = monitor(c / "postProcessing" / f"rider{i}Coeffs", "coefficient*.dat")
            t, d, p, v = f[:, 0], -f[:, 1], -f[:, 4], -f[:, 7]
            err = float(np.max(np.abs(np.interp(t, cd[:, 0], cd[:, 1]) - d / Q)))
            if err > 1e-4:
                raise SystemExit(f"{run} rider {i}: force and Cd disagree by {err}")
            rows.append(dict(run=run, rider=i, drag=mean(t, d), pressure=mean(t, p), viscous=mean(t, v),
                             first=mean(t, d, START, MID), second=mean(t, d, MID, END), cdError=err))
            hist[run, i] = (t, d)
        a = monitor(c / "postProcessing" / "wakeProbes", "U")
        t = a[:, 0]
        pts = [(x, y) for x in cfg["probeX"] for y in cfg["probeY"]]
        for j, (x, y) in enumerate(pts):
            ux, uy = a[:, 1 + 3 * j], a[:, 2 + 3 * j]
            mx, my = mean(t, ux), mean(t, uy)
            sx = np.sqrt(max(0.0, mean(t, ux ** 2) - mx ** 2))
            sy = np.sqrt(max(0.0, mean(t, uy ** 2) - my ** 2))
            # the lateral velocity's spectrum: detrended, Hann window, 2048 points over the window
            n = 2048
            tu = np.linspace(START, END, n, endpoint=False)
            u = np.interp(tu, t, uy)
            u -= np.polyval(np.polyfit(tu, u, 1), tu)
            pw = np.abs(np.fft.rfft(u * np.hanning(n))) ** 2
            fr = np.fft.rfftfreq(n, (END - START) / n)
            valid = np.flatnonzero((fr >= 3 / (END - START)) & (fr <= 100))
            k = valid[np.argmax(pw[valid])]
            frac = pw[max(1, k - 1):k + 2].sum() / max(pw[1:].sum(), 1e-30)
            peak = (float(fr[k]) if sy > 0.01 and frac > 0.25 and pw[k] > pw[k - 1] and pw[k] > pw[k + 1]
                    and pw[k] > 10 * max(np.median(pw[valid]), 1e-30) else None)
            wakes.append(dict(run=run, x=x, y=y, z=cfg["probeZ"], mUx=mx, sUx=float(sx), mUy=my, sUy=float(sy),
                              peak=peak))

    ref = rows[0]["drag"]
    for r in rows:
        r["share"] = 100 * r["drag"] / ref
    with open(out / "means.csv", "w") as f:
        f.write("run,rider,drag_N,pressure_drag_N,viscous_drag_N,Cd,share_of_alone_pct,saving_pct,"
                f"drag_{START:g}_{MID:g}_N,drag_{MID:g}_{END:g}_N\n")
        for r in rows:
            f.write(f"{r['run']},{r['rider']},{r['drag']:.3f},{r['pressure']:.3f},{r['viscous']:.3f},"
                    f"{r['drag'] / Q:.4f},{r['share']:.2f},{100 - r['share']:.2f},{r['first']:.3f},{r['second']:.3f}\n")

    edges = np.round(np.arange(0, END + 1e-9, 0.01), 10)
    if edges[-1] < END - 1e-9:
        edges = np.r_[edges, END]
    keys = list(hist)
    with open(out / "history.csv", "w") as f:
        f.write("t_start_s,t_end_s," + ",".join("alone_N" if r == "alone" else f"line{i}_N" for r, i in keys) + "\n")
        for a, b in zip(edges[:-1], edges[1:]):
            f.write(f"{a:.2f},{b:.2f}," + ",".join(f"{mean(*hist[k], a, b):.3f}" for k in keys) + "\n")

    with open(out / "wake_probes.csv", "w") as f:
        f.write("run,x_m,y_m,z_m,mean_Ux_m_s,rms_Ux_m_s,mean_Uy_m_s,rms_Uy_m_s,peak_Hz\n")
        for w in wakes:
            f.write(f"{w['run']},{w['x']:g},{w['y']:g},{w['z']:g},{w['mUx']:.3f},{w['sUx']:.3f},{w['mUy']:.3f},"
                    f"{w['sUy']:.3f}," + (f"{w['peak']:.2f}" if w["peak"] else "") + "\n")

    s = [f"Mean drag over {START:g}-{END:g} s, the rider and both wheels, -Fx (time-weighted)",
         f"Cd on Aref {cfg['Aref']} m2 at {cfg['speed']} m/s, rho {cfg['rho']} kg/m3 (q A = {Q:.3f} N)", "",
         f"{'':10s}{'drag N':>9s}{'Cd':>8s}{'share':>9s}{'saving':>9s}"
         f"{START:>8g}-{MID:g}{MID:>8g}-{END:g}{'2nd-1st':>9s}"]
    for r in rows:
        name = "alone" if r["run"] == "alone" else f"line {r['rider']}"
        s.append(f"{name:10s}{r['drag']:9.3f}{r['drag'] / Q:8.3f}{r['share']:8.1f}%{100 - r['share']:8.1f}%"
                 f"{r['first']:11.3f}{r['second']:12.3f}{r['second'] - r['first']:+9.3f}")
    behind = sorted((r for r in rows if r["run"] == "line" and r["rider"] > 1), key=lambda r: r["drag"])
    s += ["", "riders behind, lowest drag first: " + ", ".join(f"rider {r['rider']}" for r in behind),
          "largest force/Cd disagreement: %.1e" % max(r["cdError"] for r in rows), "",
          f"Wake probes at z = {cfg['probeZ']} m over {START:g}-{END:g} s (rms Uy > 0.01 m/s; peak = the spectral test "
          f"in this script, resolution {1 / (END - START):.2f} Hz)"]
    for run in ("alone", "line"):
        ws = [w for w in wakes if w["run"] == run]
        s.append(f"{run}: {sum(w['sUy'] > 0.01 for w in ws)}/{len(ws)} probes unsteady, "
                 f"{sum(w['peak'] is not None for w in ws)}/{len(ws)} with a peak")
        for w in ws:
            s.append(f"  x {w['x']:7g} y {w['y']:5g}  mean Ux {w['mUx']:8.3f}  rms Uy {w['sUy']:6.3f}  peak "
                     + (f"{w['peak']:.2f} Hz" if w["peak"] else "none"))
    (out / "summary.txt").write_text("\n".join(s) + "\n")
    print("\n".join(s))


if __name__ == "__main__":
    main()
