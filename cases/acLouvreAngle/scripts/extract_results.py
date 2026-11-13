#!/usr/bin/env python3
"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv of up and down, one row every 0.375 s
written by the coded monitor (scripts/monitor.C; the columns are COLS below). Writes:

  summary.txt          the unit, the rooms, the seated zones over 120-180 s, the heat budgets
  zones.csv            120-180 s time means of every zone's temperature and speed
  <run>/history.csv    every 1.5 s: the unit, the jet, the zones and the walls' heat

Means over an interval are time-weighted (trapezoids, the ends interpolated). Temperatures in
the files are in C, the monitor's in K. Cooling is the unit's: mass flow x 1005 x (intake
mean - slot mean), both flow-weighted. The heat budget is the rise of the air's internal
energy, (cv/R) integral of p dV, against the walls' heat into the air less the cooling, from
10 s (the first rows' start-up transient excluded, as in the study).
"""
import csv
import sys
from pathlib import Path

import numpy as np

COLS = ["time", "dt", "wall_s", "slot_out", "slot_in_signed", "slot_Tarea", "slot_Tflow", "intake_out",
        "intake_in_signed", "intake_Tarea", "intake_Tflow", "direction_deg", "jet_Ux", "jet_Uy", "jet_Uz",
        "mass", "internal_energy", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z",
        "head_T", "head_speed", "ankle_T", "ankle_speed", "occupied_T", "occupied_speed", "floor_T",
        "floor_speed", "ceiling_T", "ceiling_speed", "room_T", "room_speed", "Q_unitSideWall", "Q_farWall",
        "Q_sideWall", "Q_floor", "Q_ceiling"]
K = {c: i for i, c in enumerate(COLS)}
ZONES = ["head", "ankle", "occupied", "floor", "ceiling", "room"]
WALLS = ["Q_unitSideWall", "Q_farWall", "Q_sideWall", "Q_floor", "Q_ceiling"]
CP = 1005.0
C0 = 273.15


def integral(t, y, a, b):
    mask = (t > a) & (t < b)
    tx = np.r_[a, t[mask], b]
    yy = np.r_[np.interp(a, t, y), y[mask], np.interp(b, t, y)]
    return float(np.trapezoid(yy, tx))


def mean(t, y, a, b):
    return integral(t, y, a, b) / (b - a)


def at(a, col, t):
    return float(np.interp(t, a[:, 0], a[:, K[col]]))


def load(path):
    a = np.loadtxt(path, delimiter=",", ndmin=2)
    if a.shape[1] != len(COLS):
        raise SystemExit(f"{path}: {a.shape[1]} columns, expected {len(COLS)}")
    return a


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_results.py runs results")
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    A = {r: load(runs / r / "postProcessing" / "metrics" / "metrics.csv") for r in ("up", "down")}
    for r, a in A.items():
        if a[-1, 0] < 180 - 1e-6:
            raise SystemExit(f"{r} ends at {a[-1, 0]} s, not 180 s")
    cool = {r: -a[:, K["slot_in_signed"]] * CP * (a[:, K["intake_Tflow"]] - a[:, K["slot_Tflow"]]) for r, a in A.items()}
    walls = {r: a[:, [K[w] for w in WALLS]].sum(axis=1) for r, a in A.items()}
    L = []
    p = L.append
    p("Subject: a wall-mounted split unit cooling a 30 C room, vane up (15 deg) or down (60 deg)")
    p("3-D half room, 0-180 s from rest; figures for the half room unless noted\n")

    p("The unit                         up          down")
    rows = [
        ("mass flow in, kg/s (min-max)", lambda r, a: f"{(-a[:, K['slot_in_signed']]).min():.8f}-{(-a[:, K['slot_in_signed']]).max():.8f}"),
        ("intake out, kg/s at 180 s", lambda r, a: f"{at(a, 'intake_out', 180):.8f}"),
        ("cooling, W (min-max)", lambda r, a: f"{cool[r].min():.1f}-{cool[r].max():.1f}"),
        ("supply, C at 3 s", lambda r, a: f"{at(a, 'slot_Tflow', 3) - C0:.2f}"),
        ("supply, C at 180 s", lambda r, a: f"{at(a, 'slot_Tflow', 180) - C0:.2f}"),
        ("jet angle, deg (min-max)", lambda r, a: f"{a[:, K['direction_deg']].min():.2f} to {a[:, K['direction_deg']].max():.2f}"),
        ("time step, ms at 180 s", lambda r, a: f"{1000 * at(a, 'dt', 180):.3f}"),
    ]
    for name, f in rows:
        p(f"  {name:31s} {f('up', A['up']):>22s} {f('down', A['down']):>22s}")

    p("\nThe rooms, C                 t s      up      down   up-down")
    for t in (3, 9, 30, 60, 90, 120, 150, 180):
        u, d = at(A["up"], "room_T", t) - C0, at(A["down"], "room_T", t) - C0
        p(f"  room mean                  {t:4d}  {u:7.3f}  {d:7.3f}  {u - d:+7.3f}")
    diff = A["up"][:, K["room_T"]] - np.interp(A["up"][:, 0], A["down"][:, 0], A["down"][:, K["room_T"]])
    i = int(np.argmax(abs(diff)))
    p(f"  largest |up - down| of the room means at any write: {abs(diff[i]):.3f} K at {A['up'][i, 0]:g} s")
    p(f"  |up - down| at 180 s: {abs(diff[-1]):.3f} K")

    p("\nSeated zones, 120-180 s means      up       down    up-down")
    for z in ("head", "ankle"):
        u, d = mean(A["up"][:, 0], A["up"][:, K[z + "_T"]], 120, 180) - C0, mean(A["down"][:, 0], A["down"][:, K[z + "_T"]], 120, 180) - C0
        su, sd = mean(A["up"][:, 0], A["up"][:, K[z + "_speed"]], 120, 180), mean(A["down"][:, 0], A["down"][:, K[z + "_speed"]], 120, 180)
        p(f"  {z:5s} air, C                  {u:7.3f}  {d:7.3f}  {u - d:+7.3f}")
        p(f"  {z:5s} speed, m/s              {su:7.4f}  {sd:7.4f}  {su - sd:+7.4f}")
    p("  ankle air at 180 s, C            " + "  ".join(f"{at(A[r], 'ankle_T', 180) - C0:7.3f}" for r in ("up", "down"))
      + "   (rounded " + " and ".join(f"{round(at(A[r], 'ankle_T', 180) - C0):.0f}" for r in ("up", "down")) + ")")
    p("  head air at 180 s, C             " + "  ".join(f"{at(A[r], 'head_T', 180) - C0:7.3f}" for r in ("up", "down")))
    ru = np.round(A["up"][:, K["ankle_T"]] - C0)
    rd = np.round(np.interp(A["up"][:, 0], A["down"][:, 0], A["down"][:, K["ankle_T"]]) - C0)
    p(f"  writes at which down's rounded ankle is above up's: {int((rd > ru).sum())} of {len(ru)}")

    p("\nWalls' heat into the air, W at 180 s   up       down")
    for w in WALLS:
        p(f"  {w[2:]:14s}                 {at(A['up'], w, 180):8.2f} {at(A['down'], w, 180):8.2f}")
    p(f"  {'total':14s}                 {walls['up'][-1]:8.2f} {walls['down'][-1]:8.2f}")

    p("\nChecks                                         up            down")
    for r in ("up", "down"):
        a = A[r]
        t = a[:, 0]
        de = at(a, "internal_energy", 180) - at(a, "internal_energy", 10)
        net = integral(t, walls[r] - cool[r], 10, 180)
        qc = integral(t, cool[r], 10, 180)
        A[r + "_budget"] = (de, net, 100 * (de - net) / qc)
    p("  10-180 s change of internal energy, J " + "  ".join(f"{A[r + '_budget'][0]:13.3f}" for r in ("up", "down")))
    p("  10-180 s walls less cooling, J        " + "  ".join(f"{A[r + '_budget'][1]:13.3f}" for r in ("up", "down")))
    p("  unaccounted, % of the cooling         " + "  ".join(f"{A[r + '_budget'][2]:13.4f}" for r in ("up", "down")))
    p("  air mass, kg (first and last write)   " + "  ".join(f"{A[r][0, K['mass']]:.10f}/{A[r][-1, K['mass']]:.10f}" for r in ("up", "down")))
    p("  coldest air below the supply, K (max) " + "  ".join(f"{(A[r][:, K['slot_Tarea']] - A[r][:, K['Tmin']]).max():13.3f}" for r in ("up", "down")))
    p("  warmest air above 30 C, K (max)       " + "  ".join(f"{max(0.0, (A[r][:, K['Tmax']] - 303.15).max()):13.3f}" for r in ("up", "down")))

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    with open(out / "zones.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "zone", "T_120_180_C", "speed_120_180_m_s", "T_180_C", "speed_180_m_s"])
        for r in ("up", "down"):
            a = A[r]
            for z in ZONES:
                w.writerow([r, z, f"{mean(a[:, 0], a[:, K[z + '_T']], 120, 180) - C0:.3f}",
                            f"{mean(a[:, 0], a[:, K[z + '_speed']], 120, 180):.4f}",
                            f"{at(a, z + '_T', 180) - C0:.3f}", f"{at(a, z + '_speed', 180):.4f}"])
    for r in ("up", "down"):
        a = A[r]
        (out / r).mkdir(exist_ok=True)
        with open(out / r / "history.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_s", "slot_in_kg_s", "supply_C", "intake_C", "cooling_W", "jet_deg"]
                       + [f"{z}_C" for z in ZONES] + ["head_m_s", "ankle_m_s"] + [c[2:] + "_W" for c in WALLS]
                       + ["walls_W", "dt_ms"])
            for t in np.arange(1.5, 180 + 1e-9, 1.5):
                g = lambda c: at(a, c, t)
                w.writerow([f"{t:g}", f"{-g('slot_in_signed'):.8f}", f"{g('slot_Tflow') - C0:.3f}", f"{g('intake_Tflow') - C0:.3f}",
                            f"{np.interp(t, a[:, 0], cool[r]):.2f}", f"{g('direction_deg'):.2f}"]
                           + [f"{g(z + '_T') - C0:.3f}" for z in ZONES] + [f"{g('head_speed'):.4f}", f"{g('ankle_speed'):.4f}"]
                           + [f"{g(c):.2f}" for c in WALLS] + [f"{np.interp(t, a[:, 0], walls[r]):.2f}", f"{1000 * g('dt'):.4f}"])
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
