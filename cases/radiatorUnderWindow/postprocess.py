#!/usr/bin/env python3
"""Reduce a pair of solved runs to the small results in results/.

    python3 postprocess.py runs/hour results/hour
    python3 postprocess.py runs/start300 results/start300 --settled 0 0

Reads <runs>/{window,opposite}: the section written at every write
(postProcessing/clip/<t>/clip.vtp, cell data T and U on the 290 x 230 cells of the plane),
and the roomMeanT, glassTs, wallHeatFlux and energyCheck monitors. Writes, per run:

  <run>_history.csv      one row per write (see the column notes below)
  <run>_heat_budget.csv  the heat budget over each 7.5 s interval

and summary.md: means over the settled window, the floor draught against Heiselberg (1994)
there, and the floor layer against the room mean in 30 s windows.

Gross flux is one-way, max(v, 0) and max(-v, 0) integrated along a line, never the net.
On a horizontal line v is interpolated between the two rows of cell centres either side of
it, on a vertical line u likewise between columns. Fluxes are m3/s per metre of section.
"""
import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyvista as pv

RUNS = ("window", "opposite")
RADIATOR = {"window": (0.04, 0.125), "opposite": (3.875, 3.96)}   # x of each radiator zone
SOURCE = 60.0                     # W/m, radPowerPerM
CP, MW = 1005.0, 28.96            # thermophysicalProperties
R = 8314.462618 / MW
CV_R = (CP - R) / R               # internal energy of a closed perfect-gas box = cv/R * int p dV
E0 = CV_R * 1e5 * 9.6             # at rest: 1e5 Pa over the 9.6 m3 room


def section(path):
    m = pv.read(str(path))
    cc = m.cell_centers().points
    xs, ys = np.unique(cc[:, 0].round(7)), np.unique(cc[:, 1].round(7))
    ix, iy = np.searchsorted(xs, cc[:, 0].round(7)), np.searchsorted(ys, cc[:, 1].round(7))
    F = {}
    for name, src in (("T", np.asarray(m.cell_data["T"]) - 273.15),
                      ("u", np.asarray(m.cell_data["U"])[:, 0]),
                      ("v", np.asarray(m.cell_data["U"])[:, 1])):
        a = np.empty((len(ys), len(xs)))
        a[iy, ix] = src
        F[name] = a
    return xs, ys, F


def widths(c, lo, hi):
    e = np.r_[lo, (c[1:] + c[:-1]) / 2, hi]
    return np.diff(e)


def across_row(ys, a, y):
    j = np.searchsorted(ys, y)
    w = (y - ys[j - 1]) / (ys[j] - ys[j - 1])
    return (1 - w) * a[j - 1] + w * a[j]


def across_col(xs, a, x):
    i = np.searchsorted(xs, x)
    w = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return (1 - w) * a[:, i - 1] + w * a[:, i]


def measure(run, xs, ys, F):
    dx, dy = widths(xs, 0.0, 4.0), widths(ys, 0.0, 2.4)
    out = {}
    # the sill line, y = 0.90 m from the glass to x = 0.30 m
    v, T = across_row(ys, F["v"], 0.90), across_row(ys, F["T"], 0.90)
    s = xs < 0.30
    up, down = (np.maximum(v, 0) * dx)[s], (np.maximum(-v, 0) * dx)[s]
    out["sill_up"], out["sill_down"] = up.sum(), down.sum()
    out["sill_down_T_C"] = (T[s] * down).sum() / down.sum() if down.sum() > 1e-9 else np.nan
    # the floor line, x = 1.00 m from the floor to y = 0.30 m
    u = across_col(xs, F["u"], 1.00)
    f = ys < 0.30
    out["floor_away"] = (np.maximum(u, 0) * dy)[f].sum()
    out["floor_toward"] = (np.maximum(-u, 0) * dy)[f].sum()
    # air leaving the top of this run's radiator, y = 0.75 m over its width
    a, b = RADIATOR[run]
    r = (xs > a) & (xs < b)
    out["radiator_top_up"] = (np.maximum(across_row(ys, F["v"], 0.75), 0) * dx)[r].sum()
    # floor layer (y < 0.10 m) and seated head height (y 1.0-1.2 m), both x 0.3-2.0 m,
    # and the whole section; area-weighted
    A = np.outer(dy, dx)
    X, Y = np.meshgrid(xs, ys)
    band = (X > 0.3) & (X < 2.0)
    for name, mask in (("floor_layer_C", band & (Y < 0.10)),
                       ("head_height_C", band & (Y > 1.0) & (Y < 1.2)),
                       ("room_mean_C", np.ones_like(band))):
        out[name] = (F["T"] * A)[mask].sum() / A[mask].sum()
    # how far from the glass the cell row on the floor is 0.5 K below the section mean
    cold = F["T"][0] < out["room_mean_C"] - 0.5
    out["cold_floor_reach_m"] = xs[cold].max() if cold.any() else 0.0
    return out, A


def rows(path):
    """Monitor rows, oldest first. A run continued from a write has a second directory
    named by its start time; rows of the earlier directory past that time are superseded,
    and rows cut short are dropped."""
    files = sorted(path.glob("*/*.dat"), key=lambda q: float(q.parent.name))
    starts = [float(f.parent.name) for f in files[1:]] + [np.inf]
    for f, end in zip(files, starts):
        lines = [l.split() for l in f.read_text().splitlines() if l and not l.startswith("#")]
        width = max((len(r) for r in lines), default=0)
        for r in lines:
            if len(r) == width and float(r[0]) <= end + 1e-9:
                yield r


def monitor(run_dir, name):
    d = {}
    for r in rows(run_dir / "postProcessing" / name):
        d[round(float(r[0]), 6)] = float(r[1])
    return d


def budget(run_dir):
    """W/m over each 7.5 s interval: the radiator, each wall's heat flux into the air, the
    rise in internal energy, and what is left over (source + walls - rise)."""
    e = {float(r[0]): CV_R * float(r[1]) for r in rows(run_dir / "postProcessing/energyCheck")}
    walls = defaultdict(dict)
    for r in rows(run_dir / "postProcessing/wallHeatFlux"):
        walls[r[1]][float(r[0])] = float(r[4])
    te = np.array(sorted(e))
    ee = np.array([e[t] for t in te])
    out = []
    k = 1
    while te.size and te[-1] >= 7.5 * k - 1e-6:
        a, b = 7.5 * (k - 1), 7.5 * k
        row = {"t_start_s": a, "t_end_s": b, "radiator_W_per_m": SOURCE}
        total = SOURCE
        for patch in ("glass", "ceiling", "innerWall", "floor", "outerWall"):
            tw = np.array(sorted(walls[patch]))
            ww = np.array([walls[patch][t] for t in tw])
            m = (tw > a) & (tw <= b + 1e-9)
            # each sample holds over the time step that ends at it
            q = np.sum(ww[m] * np.diff(np.r_[a, tw[m]])) / (b - a)
            row[f"{patch}_W_per_m"] = q
            total += q
        e_a = E0 if a == 0 else np.interp(a, te, ee)
        row["stored_W_per_m"] = (np.interp(b, te, ee) - e_a) / (b - a)
        row["unaccounted_W_per_m"] = total - row["stored_W_per_m"]
        out.append(row)
        k += 1
    return out


def heiselberg(x, dT, H=1.2):
    """Heiselberg (1994): largest velocity in the cold floor flow at x m from a cold wall
    of height H m, dT the room air less the wall's surface."""
    g = np.sqrt(dT * H)
    return 0.055 * g if x <= 0.4 else (0.028 * g if x >= 2.0 else 0.095 * g / (x + 1.32))


def write_csv(path, recs, cols, fmt):
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in recs:
            f.write(",".join("" if np.isnan(r[c]) else fmt.get(c, "{:.6g}").format(r[c])
                             for c in cols) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("runs", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--settled", type=float, nargs=2, default=(3000.0, 3600.0),
                   help="settled averaging window, s; 0 0 for none")
    p.add_argument("--regimes", type=float, nargs="*",
                   default=[600, 1200, 1200, 1800, 1800, 2400, 2400, 3000, 3000, 3600])
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    lo, hi = a.settled
    settled = hi > lo
    summary = {}
    hist_cols = ["time_s", "room_mean_C", "floor_layer_C", "head_height_C", "glass_inside_C",
                 "sill_up", "sill_down", "sill_down_T_C", "floor_away", "floor_toward",
                 "radiator_top_up", "cold_floor_reach_m"] + (["pattern_rms_K"] if settled else [])
    for run in RUNS:
        rd = a.runs / run
        glass = monitor(rd, "glassTs")
        roomT = monitor(rd, "roomMeanT")
        dirs = sorted((rd / "postProcessing/clip").iterdir(), key=lambda d: float(d.name))
        recs, anom, prof = [], [], {x: [] for x in (0.5, 1.0, 2.0)}
        for d in dirs:
            t = float(d.name)
            xs, ys, F = section(d / "clip.vtp")
            m, A = measure(run, xs, ys, F)
            m["time_s"] = t
            m["glass_inside_C"] = glass.get(round(t, 6), np.nan) - 273.15
            recs.append(m)
            if settled:
                anom.append((F["T"] - m["room_mean_C"]).astype(np.float32))
                if lo <= t <= hi:
                    for x in prof:
                        prof[x].append(across_col(xs, F["u"], x)[ys < 0.30])
        t = np.array([r["time_s"] for r in recs])
        if settled:
            # how far each write's pattern (temperature less its own section mean) is from
            # the settled pattern, RMS over the section in K
            anom = np.array(anom)
            w = (A / A.sum()).astype(np.float32)
            ref = anom[(t >= lo) & (t <= hi)].mean(0)
            for r, an in zip(recs, anom):
                r["pattern_rms_K"] = float(np.sqrt((((an - ref) ** 2) * w).sum()))
        write_csv(a.out / f"{run}_history.csv", recs, hist_cols,
                  {"time_s": "{:g}", "cold_floor_reach_m": "{:.4f}"})
        bud = budget(rd)
        write_csv(a.out / f"{run}_heat_budget.csv", bud, list(bud[0]),
                  {"t_start_s": "{:g}", "t_end_s": "{:g}", "radiator_W_per_m": "{:g}",
                   **{c: "{:.4f}" for c in bud[0] if c.endswith("W_per_m")}})
        s = {"recs": recs, "t": t, "budget": bud}
        if settled:
            sel = lambda k, l0=lo, h0=hi, recs=recs: float(np.nanmean([r[k] for r in recs if l0 <= r["time_s"] <= h0]))
            s["sel"] = sel
            mon = lambda d: float(np.mean([v for k, v in d.items() if lo <= k <= hi])) - 273.15
            dT = mon(roomT) - mon(glass)
            model = {x: float(np.abs(np.mean(v, axis=0)).max()) for x, v in prof.items()}
            s["heiselberg"] = (dT, {x: (heiselberg(x, dT), model[x]) for x in prof})
        summary[run] = s
        print(f"{run}: {len(dirs)} writes, {len(bud)} budget intervals", flush=True)

    L = [f"# Results of the `{a.out.name}` runs", "",
         "Made by `postprocess.py`. Temperatures are area-weighted means over the section: the",
         "floor layer is y < 0.1 m and head height y 1.0-1.2 m, both over x 0.3-2.0 m from the",
         "glass. Fluxes are gross, one way, in m3/s per metre of section: the sill line is",
         "y = 0.90 m for x < 0.30 m, the floor line x = 1.0 m for y < 0.30 m.", ""]
    if settled:
        L += [f"## Settled, means over {lo:g}-{hi:g} s", "",
              "| | floor layer | head height | room mean | floor below room mean |",
              "|---|---:|---:|---:|---:|"]
        for run in RUNS:
            g = summary[run]["sel"]
            L.append(f"| {run} | {g('floor_layer_C'):.2f} C | {g('head_height_C'):.2f} C | "
                     f"{g('room_mean_C'):.3f} C | {g('room_mean_C') - g('floor_layer_C'):.2f} K |")
        L += ["", "| | sill up | sill down | air falling past the sill | floor line away | floor line toward |",
              "|---|---:|---:|---:|---:|---:|"]
        for run in RUNS:
            g = summary[run]["sel"]
            L.append(f"| {run} | {g('sill_up'):.4f} | {g('sill_down'):.4f} | "
                     f"{g('sill_down_T_C'):.1f} C | {g('floor_away'):.4f} | {g('floor_toward'):.4f} |")
        L += ["", "Heat flows over the last 1200 s, W/m (negative leaves the air):", "",
              "| | radiator | glass | ceiling | inner wall | stored | unaccounted |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for run in RUNS:
            b = [r for r in summary[run]["budget"] if r["t_start_s"] >= hi - 1200 - 1e-9 and r["t_end_s"] <= hi + 1e-9]
            mm = lambda k: np.mean([r[k] for r in b])
            L.append(f"| {run} | {mm('radiator_W_per_m'):.1f} | {mm('glass_W_per_m'):.1f} | "
                     f"{mm('ceiling_W_per_m'):.1f} | {mm('innerWall_W_per_m'):.1f} | "
                     f"{mm('stored_W_per_m'):.2f} | {mm('unaccounted_W_per_m'):.3f} |")
        L += ["", f"## The floor draught against Heiselberg (1994), {lo:g}-{hi:g} s", "",
              "dT is the room mean (roomMeanT) less the glass's inside surface (glassTs). The model",
              "figure is the largest |Ux| below y = 0.3 m in the velocity profile averaged over",
              "the window, m/s.", "",
              "| x from the glass | " + " | ".join(f"{r}: Heiselberg | {r}: model | ratio" for r in RUNS) + " |",
              "|---|" + "---:|" * 6]
        for x in (0.5, 1.0, 2.0):
            cells = []
            for run in RUNS:
                pr, mo = summary[run]["heiselberg"][1][x]
                cells += [f"{pr:.3f}", f"{mo:.3f}", f"{mo / pr:.2f}"]
            L.append(f"| {x:g} m | " + " | ".join(cells) + " |")
        L.append("")
        L.append("dT: " + ", ".join(f"{run} {summary[run]['heiselberg'][0]:.2f} K" for run in RUNS))
        if a.regimes:
            L += ["", "## Successive windows", "",
                  "| window (s) | " + " | ".join(f"{r}: room | {r}: floor layer | {r}: floor line away / toward" for r in RUNS) + " |",
                  "|---|" + "---:|" * 6]
            for r0, r1 in zip(a.regimes[::2], a.regimes[1::2]):
                cells = []
                for run in RUNS:
                    g = summary[run]["sel"]
                    cells += [f"{g('room_mean_C', r0, r1):.2f}", f"{g('floor_layer_C', r0, r1):.2f}",
                              f"{g('floor_away', r0, r1):.4f} / {g('floor_toward', r0, r1):.4f}"]
                L.append(f"| {r0:g}-{r1:g} | " + " | ".join(cells) + " |")
    tmax = min(summary[r]["t"].max() for r in RUNS)
    L += ["", "## The floor layer against the room mean, 30 s windows (first 600 s)", "",
          "| window (s) | " + " | ".join(f"{r}: floor below room mean (K)" for r in RUNS) + " |",
          "|---|---:|---:|"]
    for w0 in range(0, int(min(tmax, 600)), 30):
        cells = []
        for run in RUNS:
            rr = [r for r in summary[run]["recs"] if w0 < r["time_s"] <= w0 + 30]
            cells.append(f"{np.mean([r['room_mean_C'] - r['floor_layer_C'] for r in rr]):.2f}")
        L.append(f"| {w0}-{w0 + 30} | " + " | ".join(cells) + " |")
    L += ["", "## Heat budget", "",
          "Heat unaccounted for over each 7.5 s interval, W/m: the radiator plus the wall heat flux",
          "less the rise in internal energy, (cv/R) times the integral of p (energyCheck).", "",
          "| | mean | min | max |", "|---|---:|---:|---:|"]
    for run in RUNS:
        u = np.array([r["unaccounted_W_per_m"] for r in summary[run]["budget"]])
        L.append(f"| {run} | {u.mean():+.3f} | {u.min():+.2f} | {u.max():+.2f} |")
    (a.out / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
