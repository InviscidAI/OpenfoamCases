#!/usr/bin/env python3
"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv of high and low, one row every 0.625 s from
0.625 s written by the coded monitor (scripts/monitor.C; the columns are COLS below). Writes:

  summary.txt          the stove (and its face temperature, from the stoveT_* and flueT_*
                       function objects' files), the fan, the doorway, the cold room, the walls, the heat budgets
  zones.csv            160-190 s time means of every zone's temperature and speed, and at 190 s
  <run>/history.csv    every 2.5 s: the stove's heat, the fan, the doorway, the zones, the walls

Means over an interval are time-weighted (trapezoids, the ends interpolated). Temperatures in
the files are in C, the monitor's in K. Flows are gross one-way flows through a face, each way,
in m3/s at the local density; positive x runs from the stove room into the cold room. The heat
through the doorway is the enthalpy cp (T - 14 C) carried each way; its net is into the cold
room. The walls' heat is wallHeatFlux, positive into the air. The heat budget is the rise of
the air's internal energy, (cv/R) integral of p dV, against the stove's, the flue's and the
walls' heat, from 10 s (the first rows' start-up transient excluded, as in the study). Before
the first row, at t = 0, the air is at rest and no heat has moved; integrals from 0 take every
flow and heat as zero there.
"""
import csv
import sys
from pathlib import Path

import numpy as np

COLS = ["time", "dt", "wall_s"]
for _z in ("fanHighLeft", "fanHighRight", "fanLowLeft", "fanLowRight", "doorway", "doorUpper", "doorLower"):
    COLS += [_z + "_" + _n for _n in ("mplus", "mminus", "qplus", "qminus", "hplus", "hminus")]
COLS += ["mass", "internal_energy", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z"]
ZONES = ["warm_mean", "warm_seated", "warm_floor", "warm_ceiling",
         "cold_mean", "cold_seated", "cold_floor", "cold_ceiling", "head", "ankle"]
for _z in ZONES:
    COLS += [_z + "_" + _n for _n in ("T", "speed", "energy", "mass")]
WALLS = ["Q_stoveRoomWalls", "Q_coldRoomWalls", "Q_doorwayReveal", "Q_stove", "Q_flue"]
COLS += WALLS
K = {c: i for i, c in enumerate(COLS)}
RUNS = ("high", "low")
C0 = 273.15
A0, A1 = 160.0, 190.0
END = 190.0


def integral(t, y, a, b):
    mask = (t > a) & (t < b)
    tx = np.r_[a, t[mask], b]
    yy = np.r_[np.interp(a, t, y), y[mask], np.interp(b, t, y)]
    return float(np.trapezoid(yy, tx))


def mean(t, y, a, b):
    return integral(t, y, a, b) / (b - a)


def load(path):
    a = np.loadtxt(path, delimiter=",", ndmin=2)
    if a.shape[1] != len(COLS):
        raise SystemExit(f"{path}: {a.shape[1]} columns, expected {len(COLS)}")
    return a


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_results.py runs results")
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    A = {r: load(runs / r / "postProcessing" / "metrics" / "metrics.csv") for r in RUNS}
    for r, a in A.items():
        if a[-1, 0] < END - 1e-6:
            raise SystemExit(f"{r} ends at {a[-1, 0]} s, not {END:g} s")
        A[r] = a[a[:, 0] <= END + 1e-6]

    def col(r, c):
        return A[r][:, K[c]]

    def t(r):
        return A[r][:, 0]

    def avg(r, c, a=A0, b=A1):
        return mean(t(r), col(r, c), a, b)

    def at(r, c, x):
        return float(np.interp(x, t(r), col(r, c)))

    def from0(r, y):
        # the integral from t = 0, where every flow and heat is zero, to 190 s
        return float(np.trapezoid(np.r_[0.0, y], np.r_[0.0, t(r)]))

    heat = {r: col(r, "Q_stove") + col(r, "Q_flue") for r in RUNS}
    walls = {r: sum(col(r, w) for w in WALLS[:3]) for r in RUNS}
    doornet = {r: col(r, "doorway_hplus") - col(r, "doorway_hminus") for r in RUNS}
    L = []
    p = L.append
    p("Subject: a wood stove in one room and a box fan in the doorway to the next, high (warm air out) or low (cold air in)")
    p("3-D half house, 0-190 s from the door opening and the fan coming on; figures for the half house unless noted")
    p(f"Last-window means over {A0:g}-{A1:g} s\n")

    p("The stove and the fan                         high          low")
    p("  stove, W (min-max over 10-190 s)    " + "  ".join(
        f"{col(r, 'Q_stove')[t(r) >= 10].min():6.1f}-{col(r, 'Q_stove')[t(r) >= 10].max():6.1f}" for r in RUNS))
    p("  flue, W (min-max over 10-190 s)     " + "  ".join(
        f"{col(r, 'Q_flue')[t(r) >= 10].min():6.1f}-{col(r, 'Q_flue')[t(r) >= 10].max():6.1f}" for r in RUNS))
    p("  stove + flue, W, 160-190 s mean     " + "  ".join(f"{avg(r, 'Q_stove'):6.1f} + {avg(r, 'Q_flue'):5.1f}" for r in RUNS))
    p("  stove + flue, kJ over 0-190 s       " + "  ".join(f"{from0(r, heat[r]) / 1000:13.1f}" for r in RUNS))
    fan = {"high": ("fanHighRight", "qplus"), "low": ("fanLowLeft", "qminus")}
    p("  fan, m3/s through its downstream face, 160-190 s  " + "  ".join(
        f"{avg(r, fan[r][0] + '_' + fan[r][1]):.4f}" for r in RUNS)
      + "   (fanHighRight +x, fanLowLeft -x; target 0.2950, half a Lasko 3733 on low)")

    face = {}
    for r in RUNS:
        for patch in ("stove", "flue"):
            for op in ("areaAverage", "max"):
                d = np.loadtxt(next((runs / r / "postProcessing" / f"{patch}T_{op}").glob("*/surfaceFieldValue.dat")), ndmin=2)
                face[r, patch, op] = d[(d[:, 0] > A0) & (d[:, 0] <= A1), 1].mean() - C0
    p("  face temperature, C, 160-190 s means: area mean (and the face maximum)")
    for patch in ("stove", "flue"):
        p(f"    {patch:5s}                             " + "  ".join(
            f"{face[r, patch, 'areaAverage']:6.0f} ({face[r, patch, 'max']:5.0f})" for r in RUNS))

    p("\nThe doorway, 160-190 s means                high        low")
    for z in ("doorway", "doorUpper", "doorLower"):
        p(f"  {z:10s} into the cold room, m3/s    " + "  ".join(f"{avg(r, z + '_qplus'):9.4f}" for r in RUNS))
        p(f"  {z:10s} into the stove room, m3/s   " + "  ".join(f"{avg(r, z + '_qminus'):9.4f}" for r in RUNS))
    p("  net heat into the cold room, W        " + "  ".join(f"{mean(t(r), doornet[r], A0, A1):9.1f}" for r in RUNS))
    p("  net heat into the cold room, kJ 0-190 " + "  ".join(f"{from0(r, doornet[r]) / 1000:9.1f}" for r in RUNS))
    rows = {r: (t(r) > A0) & (t(r) <= A1) for r in RUNS}
    p(f"  as the study's notes averaged them, the plain mean of the {int(rows['high'].sum())} rows after {A0:g} s:")
    p("    net heat into the cold room, W      " + "  ".join(f"{doornet[r][rows[r]].mean():9.1f}" for r in RUNS))
    p("    cold room's walls into the air, W   " + "  ".join(f"{col(r, 'Q_coldRoomWalls')[rows[r]].mean():9.1f}" for r in RUNS))

    p("\nThe cold room, C                  t s     high      low   high-low")
    for z, name in (("cold_mean", "room mean"), ("cold_seated", "seated, y 0.1-1.1"), ("head", "head"),
                    ("ankle", "ankles"), ("cold_floor", "floor, y < 0.1"), ("cold_ceiling", "ceiling, y > 2.2")):
        for x in (30, 60, 90, 120, 150, 190):
            h, l = at("high", z + "_T", x) - C0, at("low", z + "_T", x) - C0
            p(f"  {name:22s}     {x:4d}  {h:7.3f}  {l:7.3f}  {h - l:+7.3f}")
        h, l = avg("high", z + "_T") - C0, avg("low", z + "_T") - C0
        p(f"  {name:22s}  {A0:g}-{A1:g}  {h:7.3f}  {l:7.3f}  {h - l:+7.3f}")
    p("  mean air speed, m/s, 160-190 s        " + "  ".join(f"{avg(r, 'cold_mean_speed'):7.4f}" for r in RUNS))
    p("  air speed at the head, m/s, 160-190 s " + "  ".join(f"{avg(r, 'head_speed'):7.4f}" for r in RUNS))
    p("  ceiling less floor, K, at 190 s       " + "  ".join(
        f"{at(r, 'cold_ceiling_T', END) - at(r, 'cold_floor_T', END):7.3f}" for r in RUNS))
    rh = np.round(col("high", "head_T") - C0)
    rl = np.round(np.interp(t("high"), t("low"), col("low", "head_T")) - C0)
    p(f"  head rounded at 190 s: high {rh[-1]:.0f}, low {rl[-1]:.0f}; writes with low's rounded head above high's: "
      f"{int((rl > rh).sum())} of {len(rh)}, below: {int((rl < rh).sum())}")

    p("\nThe stove room, C, 160-190 s means      high      low")
    for z in ("warm_mean", "warm_seated", "warm_floor", "warm_ceiling"):
        p(f"  {z:22s}            " + "  ".join(f"{avg(r, z + '_T') - C0:7.3f}" for r in RUNS))

    p("\nThe walls' heat into the air, W, 160-190 s   high       low")
    for w in WALLS[:3]:
        p(f"  {w[2:]:16s}                  " + "  ".join(f"{avg(r, w):9.1f}" for r in RUNS))
    p("  coldRoomWalls, kJ over 0-190 s        " + "  ".join(f"{from0(r, col(r, 'Q_coldRoomWalls')) / 1000:9.1f}" for r in RUNS))

    p("\nChecks                                         high            low")
    bud = {}
    for r in RUNS:
        de = at(r, "internal_energy", END) - at(r, "internal_energy", 10)
        q = integral(t(r), heat[r], 10, END)
        net = q + integral(t(r), walls[r], 10, END)
        bud[r] = (de, q, net, 100 * (de - net) / q)
    p("  10-190 s stove + flue heat, J          " + "  ".join(f"{bud[r][1]:13.1f}" for r in RUNS))
    p("  10-190 s change of internal energy, J  " + "  ".join(f"{bud[r][0]:13.1f}" for r in RUNS))
    p("  10-190 s stove, flue and walls, J      " + "  ".join(f"{bud[r][2]:13.1f}" for r in RUNS))
    p("  unaccounted, % of the stove's heat     " + "  ".join(f"{bud[r][3]:13.4f}" for r in RUNS))
    p("  air mass, kg (first and last row)      " + "  ".join(f"{col(r, 'mass')[0]:.8f}/{col(r, 'mass')[-1]:.8f}" for r in RUNS))
    p("  coldest air, C (min over the run)      " + "  ".join(f"{col(r, 'Tmin').min() - C0:13.3f}" for r in RUNS))
    p("  warmest air, C (max over the run)      " + "  ".join(f"{col(r, 'Tmax').max() - C0:13.3f}" for r in RUNS))
    p("  time step, ms at 190 s                 " + "  ".join(f"{1000 * at(r, 'dt', END):13.3f}" for r in RUNS))

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    with open(out / "zones.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "zone", "T_160_190_C", "speed_160_190_m_s", "T_190_C", "speed_190_m_s"])
        for r in RUNS:
            for z in ZONES:
                w.writerow([r, z, f"{avg(r, z + '_T') - C0:.3f}", f"{avg(r, z + '_speed'):.4f}",
                            f"{at(r, z + '_T', END) - C0:.3f}", f"{at(r, z + '_speed', END):.4f}"])
    for r in RUNS:
        (out / r).mkdir(exist_ok=True)
        with open(out / r / "history.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_s", "stove_W", "flue_W", "fan_m3_s", "door_in_m3_s", "door_out_m3_s", "door_net_heat_W"]
                       + [f"{z}_C" for z in ZONES] + ["cold_mean_m_s", "head_m_s"] + [c[2:] + "_W" for c in WALLS[:3]]
                       + ["dt_ms"])
            for x in np.arange(2.5, END + 1e-9, 2.5):
                g = lambda c: at(r, c, x)
                w.writerow([f"{x:g}", f"{g('Q_stove'):.2f}", f"{g('Q_flue'):.2f}", f"{g(fan[r][0] + '_' + fan[r][1]):.5f}",
                            f"{g('doorway_qplus'):.5f}", f"{g('doorway_qminus'):.5f}",
                            f"{np.interp(x, t(r), doornet[r]):.2f}"]
                           + [f"{g(z + '_T') - C0:.3f}" for z in ZONES]
                           + [f"{g('cold_mean_speed'):.4f}", f"{g('head_speed'):.4f}"]
                           + [f"{g(c):.2f}" for c in WALLS[:3]] + [f"{1000 * g('dt'):.4f}"])
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
