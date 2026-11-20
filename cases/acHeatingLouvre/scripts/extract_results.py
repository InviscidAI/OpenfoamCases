#!/usr/bin/env python3
"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv of up and down, written by the coded monitor
(scripts/monitor.C; the columns are COLS below): one row at the first step and then one every
0.375 s to 180 s. Writes:

  summary.txt          the unit, the rooms, the seated zones over 90-180 s, the surfaces, the heat
                       budgets and the checks
  zones.csv            90-180 s time means of every zone's temperature and speed, and at 180 s
  <run>/history.csv    every 1.5 s: the unit, the jet, the zones and the surfaces' heat

Means over an interval are time-weighted (trapezoids, the ends interpolated). Temperatures in
the files are in C (and F where marked), the monitor's in K. The unit's heat is the monitor's:
the slot's mass flow x 1005 x (slot mean - intake mean), both flow-weighted. The surfaces' heat
is into the surface, so positive when the air warms them. The heat budget is from 10 s: the rise
of the air's internal energy, (cv/R) integral of p dV, plus the rise of the heat stored in the
walls', floor's and ceiling's layers (read from the layers themselves), against the unit's heat
summed step by step.
"""
import csv
import sys
from pathlib import Path

import numpy as np

COLS = ["time", "dt", "wall_s", "slot_out", "slot_in_signed", "slot_Tarea", "slot_Tflow", "intake_out",
        "intake_in_signed", "intake_Tarea", "intake_Tflow", "direction_deg", "jet_Ux", "jet_Uy", "jet_Uz",
        "mass", "internal_energy", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z",
        "torso_T", "torso_speed", "head_T", "head_speed", "feet_T", "feet_speed", "occupied_T", "occupied_speed",
        "floor_T", "floor_speed", "ceiling_T", "ceiling_speed", "room_T", "room_speed"]
WALLS = ["unitSideWall", "farWall", "sideWall", "floor", "ceiling"]
for w in WALLS:
    COLS += [f"Q_{w}", f"Tw_{w}", f"E_{w}", f"I_{w}"]
COLS += ["heat", "heat_integral"]
K = {c: i for i, c in enumerate(COLS)}
ZONES = ["torso", "head", "feet", "occupied", "floor", "ceiling", "room"]
T0 = 288.15
C0 = 273.15
LO, HI = 90.0, 180.0


def F(c):
    return c * 9 / 5 + 32


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
        if a[-1, 0] < HI - 1e-6:
            raise SystemExit(f"{r} ends at {a[-1, 0]} s, not {HI:g} s")
    mz = lambda r, z: mean(A[r][:, 0], A[r][:, K[z]], LO, HI)
    L = []
    p = L.append
    p("Subject: a wall-mounted split unit heating a 15 C home office, vane up (15 deg) or down (60 deg)")
    p("3-D half room, 0-180 s from rest; figures for the half room unless noted\n")

    p("The unit                         up          down")
    rows = [
        ("mass flow in, kg/s (min-max)", lambda r, a: f"{(-a[1:, K['slot_in_signed']]).min():.7f}-{(-a[1:, K['slot_in_signed']]).max():.7f}"),
        ("intake out, kg/s at 180 s", lambda r, a: f"{at(a, 'intake_out', 180):.7f}"),
        ("heat, W (min-max)", lambda r, a: f"{a[1:, K['heat']].min():.2f}-{a[1:, K['heat']].max():.2f}"),
        ("supply less intake, K at 180 s", lambda r, a: f"{at(a, 'slot_Tflow', 180) - at(a, 'intake_Tflow', 180):.3f}"),
        ("supply, C at 3 s", lambda r, a: f"{at(a, 'slot_Tflow', 3) - C0:.2f}"),
        ("supply, C at 180 s", lambda r, a: f"{at(a, 'slot_Tflow', 180) - C0:.2f}"),
        ("jet angle, deg (min-max)", lambda r, a: f"{a[1:, K['direction_deg']].min():.2f} to {a[1:, K['direction_deg']].max():.2f}"),
        ("time step, ms at 180 s", lambda r, a: f"{1000 * at(a, 'dt', 180):.3f}"),
    ]
    for name, f in rows:
        p(f"  {name:31s} {f('up', A['up']):>22s} {f('down', A['down']):>22s}")
    p("  (min-max over the rows from 0.375 s; the first-step row at 0.0006 s is left out)")

    p("\nThe rooms, C                 t s      up      down   up-down")
    for t in (3, 9, 30, 60, 90, 120, 150, 180):
        u, d = at(A["up"], "room_T", t) - C0, at(A["down"], "room_T", t) - C0
        p(f"  room mean                  {t:4d}  {u:7.3f}  {d:7.3f}  {u - d:+7.3f}")
    for z, name in (("floor_T", "floor layer, y < 0.1 m"), ("ceiling_T", "ceiling layer, y > 2.2 m")):
        p(f"  {name:25s} 180  " + "  ".join(f"{at(A[r], z, 180) - C0:7.3f}" for r in ("up", "down")))
    for r in ("up", "down"):
        a = A[r]
        i = int(np.argmax(a[:, K["room_T"]] >= 294.261111))
        p(f"  {r:4s} room mean first at or above 70 F (21.11 C): {a[i, 0]:g} s")

    p("\nSeated zones, 90-180 s means      up       down    up-down")
    for z in ("torso", "head", "feet"):
        u, d = mz("up", z + "_T") - C0, mz("down", z + "_T") - C0
        su, sd = mz("up", z + "_speed"), mz("down", z + "_speed")
        p(f"  {z:5s} air, C                  {u:7.3f}  {d:7.3f}  {u - d:+7.3f}   ({F(u):.1f} and {F(d):.1f} F)")
        p(f"  {z:5s} speed, m/s              {su:7.4f}  {sd:7.4f}  {su - sd:+7.4f}")
    p("\nSeated zones at 180 s, C           up       down    up-down")
    for z in ("torso", "head", "feet"):
        u, d = at(A["up"], z + "_T", 180) - C0, at(A["down"], z + "_T", 180) - C0
        p(f"  {z:5s} air                     {u:7.3f}  {d:7.3f}  {u - d:+7.3f}   ({F(u):.1f} and {F(d):.1f} F, "
          f"rounded {round(F(u))} and {round(F(d))})")

    # the clip's number: the torso in F, rounded, at t = 0 (the room at rest) and every 0.375 s
    tt = np.arange(481) * 0.375
    tor = {}
    for r in ("up", "down"):
        a = A[r][1:]
        if len(a) != 480 or not np.allclose(a[:, 0], tt[1:]):
            raise SystemExit(f"{r}: the monitor's rows are not every 0.375 s to 180 s")
        tor[r] = np.r_[T0, a[:, K["torso_T"]]] - C0
    ru, rd = np.round(F(tor["up"])), np.round(F(tor["down"]))
    p(f"\nThe torso in F, rounded, at t = 0 and every 0.375 s ({len(tt)} writes)")
    p(f"  up above down {int((ru > rd).sum())}, equal {int((ru == rd).sum())}, down above up {int((rd > ru).sum())}")
    if (rd > ru).any():
        p(f"  down above up first at {tt[np.argmax(rd > ru)]:g} s")
    first = tt[np.argmax(ru != rd)]
    p(f"  the two first differ at {first:g} s")
    p("  unrounded, which run's air is warmer, from the first row (0.375 s on):")
    for z in ("torso", "head", "feet"):
        a = A["up"][1:]
        d = a[:, K[z + "_T"]] - A["down"][1:, K[z + "_T"]]
        sg = np.sign(d)
        parts = [f"{'up' if sg[0] > 0 else 'down'} from {a[0, 0]:g} s"]
        parts += [f"{'up' if sg[i + 1] > 0 else 'down'} from {a[i + 1, 0]:g} s" for i in np.where(np.diff(sg) != 0)[0]]
        p(f"    {z:5s} " + ", ".join(parts))
    for s in (0, 9, 30, 60, 90, 120, 150, 171, 180):
        k = int(round(s / 0.375))
        p(f"  {s:4d} s   up {F(tor['up'][k]):5.1f} F ({ru[k]:.0f})   down {F(tor['down'][k]):5.1f} F ({rd[k]:.0f})")

    p("\nThe surfaces at 180 s        heat into it, W     mean surface, C     stored, kJ")
    p("                                up      down        up     down       up     down")
    for w in WALLS:
        p(f"  {w:14s}          {at(A['up'], 'Q_' + w, 180):7.1f} {at(A['down'], 'Q_' + w, 180):8.1f}"
          f"   {at(A['up'], 'Tw_' + w, 180) - C0:7.2f} {at(A['down'], 'Tw_' + w, 180) - C0:7.2f}"
          f"   {at(A['up'], 'E_' + w, 180) / 1e3:7.2f} {at(A['down'], 'E_' + w, 180) / 1e3:7.2f}")
    tq = {r: sum(at(A[r], "Q_" + w, 180) for w in WALLS) for r in A}
    te = {r: sum(at(A[r], "E_" + w, 180) for w in WALLS) / 1e3 for r in A}
    p(f"  {'total':14s}          {tq['up']:7.1f} {tq['down']:8.1f}                       {te['up']:7.2f} {te['down']:7.2f}")

    p("\nChecks                                         up            down")
    B = {}
    for r in ("up", "down"):
        a = A[r]
        de = at(a, "internal_energy", 180) - at(a, "internal_energy", 10)
        ds = sum(at(a, "E_" + w, 180) - at(a, "E_" + w, 10) for w in WALLS)
        q = at(a, "heat_integral", 180) - at(a, "heat_integral", 10)
        B[r] = (de, ds, q, 100 * (de + ds - q) / q)
    p("  10-180 s rise of the air's internal energy, J " + "  ".join(f"{B[r][0]:13.1f}" for r in ("up", "down")))
    p("  10-180 s rise of the layers' stored heat, J   " + "  ".join(f"{B[r][1]:13.1f}" for r in ("up", "down")))
    p("  10-180 s the unit's heat, J                   " + "  ".join(f"{B[r][2]:13.1f}" for r in ("up", "down")))
    p("  unaccounted, % of the unit's heat             " + "  ".join(f"{B[r][3]:13.4f}" for r in ("up", "down")))
    p("  air mass, kg (first and last row)     " + "  ".join(f"{A[r][0, K['mass']]:.9f}/{A[r][-1, K['mass']]:.9f}" for r in ("up", "down")))
    p("  air mass, largest relative change between rows" + "  ".join(f"{abs(A[r][:, K['mass']] / A[r][0, K['mass']] - 1).max():13.2e}" for r in ("up", "down")))
    for r in ("up", "down"):
        a = A[r]
        p(f"  {r}: coldest air below 15 C at the first step (0.0006 s), K: {T0 - a[0, K['Tmin']]:.3f} at "
          f"({a[0, K['Tmin_x']]:g}, {a[0, K['Tmin_y']]:g}, {a[0, K['Tmin_z']]:g}) m; from 0.375 s on: "
          f"{max(0.0, (T0 - a[1:, K['Tmin']]).max()):.3f}")
        p(f"  {r}: warmest air above the supply, K (max over the rows): {max(0.0, (a[:, K['Tmax']] - a[:, K['slot_Tflow']]).max()):.3f}")

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    with open(out / "zones.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "zone", "T_90_180_C", "speed_90_180_m_s", "T_180_C", "speed_180_m_s"])
        for r in ("up", "down"):
            a = A[r]
            for z in ZONES:
                w.writerow([r, z, f"{mz(r, z + '_T') - C0:.3f}", f"{mz(r, z + '_speed'):.4f}",
                            f"{at(a, z + '_T', 180) - C0:.3f}", f"{at(a, z + '_speed', 180):.4f}"])
    for r in ("up", "down"):
        a = A[r]
        (out / r).mkdir(exist_ok=True)
        with open(out / r / "history.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_s", "slot_in_kg_s", "supply_C", "intake_C", "heat_W", "jet_deg"]
                       + [f"{z}_C" for z in ZONES] + ["torso_m_s", "head_m_s", "feet_m_s"]
                       + [f"{c}_W" for c in WALLS] + ["dt_ms"])
            for t in np.arange(1.5, HI + 1e-9, 1.5):
                g = lambda c: at(a, c, t)
                w.writerow([f"{t:g}", f"{-g('slot_in_signed'):.7f}", f"{g('slot_Tflow') - C0:.3f}", f"{g('intake_Tflow') - C0:.3f}",
                            f"{g('heat'):.2f}", f"{g('direction_deg'):.2f}"]
                           + [f"{g(z + '_T') - C0:.3f}" for z in ZONES]
                           + [f"{g(z + '_speed'):.4f}" for z in ("torso", "head", "feet")]
                           + [f"{g('Q_' + c):.2f}" for c in WALLS] + [f"{1000 * g('dt'):.4f}"])
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
