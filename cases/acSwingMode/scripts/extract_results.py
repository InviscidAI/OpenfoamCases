#!/usr/bin/env python3
"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv of held and swing, written by the coded
monitor (scripts/monitor.C; the columns are COLS below): one row at the first step and then one
every 0.375 s to 180 s. Writes:

  summary.txt          the unit and its jet, the rooms, the sleeper's zones over 90-180 s and at
                       180 s, the face number in C, the surfaces, the heat budgets and the checks
  zones.csv            90-180 s time means of every zone's temperature and speed, and at 180 s
  <run>/history.csv    every 1.5 s: the unit, the vane and the jet, the zones and the surfaces' heat

Means over an interval are time-weighted (trapezoids, the ends interpolated). Temperatures in
the files are in C (and F where marked), the monitor's in K. The heat removed is the monitor's:
the outlet's mass flow x 1005 x (intake mean - outlet mean), both flow-weighted, positive when
the unit cools. The surfaces' heat is into the air, so positive when a surface warmer than the
air gives up heat; their stored heat is relative to the 32 C start, so negative as they cool.
The heat budget is from 10 s: the change of the air's internal energy, (cv/R) integral of p dV,
plus the change of the heat stored in the walls', floor's and ceiling's layers (read from the
layers themselves), against the heat the unit removed, summed step by step.
"""
import csv
import sys
from pathlib import Path

import numpy as np

COLS = ["time", "dt", "wall_s", "slot_out", "slot_in_signed", "slot_Tarea", "slot_Tflow", "intake_out",
        "intake_in_signed", "intake_Tarea", "intake_Tflow", "direction_deg", "jet_Ux", "jet_Uy", "jet_Uz",
        "mass", "internal_energy", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z",
        "torso_T", "torso_speed", "face_T", "face_speed", "feet_T", "feet_speed", "occupied_T", "occupied_speed",
        "floor_T", "floor_speed", "ceiling_T", "ceiling_speed", "room_T", "room_speed", "bed_T", "bed_speed"]
WALLS = ["unitSideWall", "farWall", "sideWall", "floor", "ceiling"]
for w in WALLS:
    COLS += [f"Q_{w}", f"Tw_{w}", f"E_{w}", f"I_{w}"]
COLS += ["heat", "heat_integral", "imposed_deg", "outlet_max_phi"]
K = {c: i for i, c in enumerate(COLS)}
ZONES = ["face", "torso", "feet", "bed", "occupied", "floor", "ceiling", "room"]
RUNS = ("held", "swing")
T0 = 305.15
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
    A = {r: load(runs / r / "postProcessing" / "metrics" / "metrics.csv") for r in RUNS}
    for r, a in A.items():
        if a[-1, 0] < HI - 1e-6:
            raise SystemExit(f"{r} ends at {a[-1, 0]} s, not {HI:g} s")
    mz = lambda r, z: mean(A[r][:, 0], A[r][:, K[z]], LO, HI)
    L = []
    p = L.append
    p("Subject: a wall-mounted split unit cooling a 32 C bedroom, vane held at 10 deg down or swinging 10-40 deg every 24 s")
    p("3-D half room, 0-180 s from rest; figures for the half room unless noted\n")

    p("The unit                               held                  swing")
    first = lambda a: a[1:]  # the rows from 0.375 s
    late = lambda a: a[a[:, 0] >= 1.0]
    rows = [
        ("mass flow in, kg/s (min-max)", lambda a: f"{(-first(a)[:, K['slot_in_signed']]).min():.7f}-{(-first(a)[:, K['slot_in_signed']]).max():.7f}"),
        ("mass flow out of outlet, kg/s (max)", lambda a: f"{first(a)[:, K['slot_out']].max():.2e}"),
        ("largest outlet face flux, kg/s", lambda a: f"{a[:, K['outlet_max_phi']].max():.3e}"),
        ("intake out, kg/s at 180 s", lambda a: f"{at(a, 'intake_out', 180):.7f}"),
        ("heat removed, W (min-max)", lambda a: f"{first(a)[:, K['heat']].min():.3f}-{first(a)[:, K['heat']].max():.3f}"),
        ("intake less supply, K at 180 s", lambda a: f"{at(a, 'intake_Tflow', 180) - at(a, 'slot_Tflow', 180):.3f}"),
        ("supply, C at 3 s", lambda a: f"{at(a, 'slot_Tflow', 3) - C0:.2f}"),
        ("supply, C at 180 s", lambda a: f"{at(a, 'slot_Tflow', 180) - C0:.2f}"),
        ("imposed angle, deg down (min-max)", lambda a: f"{first(a)[:, K['imposed_deg']].min():.2f} to {first(a)[:, K['imposed_deg']].max():.2f}"),
        ("jet angle, deg down (min-max)", lambda a: f"{first(a)[:, K['direction_deg']].min():.2f} to {first(a)[:, K['direction_deg']].max():.2f}"),
        ("jet less imposed, deg, from 1 s", lambda a: f"{(late(a)[:, K['direction_deg']] - late(a)[:, K['imposed_deg']]).min():+.2f} to {(late(a)[:, K['direction_deg']] - late(a)[:, K['imposed_deg']]).max():+.2f}"),
        ("time step, ms at 180 s", lambda a: f"{1000 * at(a, 'dt', 180):.3f}"),
    ]
    for name, f in rows:
        p(f"  {name:35s} {f(A['held']):>22s} {f(A['swing']):>22s}")
    p("  (min-max over the rows from 0.375 s; the first-step row at 0.0006 s is left out)")

    p("\nThe rooms, C                 t s     held    swing  held-swing")
    for t in (3, 9, 30, 60, 90, 120, 150, 180):
        u, d = at(A["held"], "room_T", t) - C0, at(A["swing"], "room_T", t) - C0
        p(f"  room mean                  {t:4d}  {u:7.3f}  {d:7.3f}  {u - d:+7.3f}")
    for z, name in (("floor_T", "floor layer, y < 0.1 m"), ("ceiling_T", "ceiling layer, y > 2.2 m"),
                    ("occupied_T", "occupied zone")):
        p(f"  {name:25s} 180  " + "  ".join(f"{at(A[r], z, 180) - C0:7.3f}" for r in RUNS))

    p("\nThe sleeper's zones, 90-180 s means    held    swing  held-swing")
    for z in ("face", "torso", "feet", "bed"):
        u, d = mz("held", z + "_T") - C0, mz("swing", z + "_T") - C0
        su, sd = mz("held", z + "_speed"), mz("swing", z + "_speed")
        p(f"  {z:5s} air, C                       {u:7.3f}  {d:7.3f}  {u - d:+7.3f}   ({F(u):.1f} and {F(d):.1f} F)")
        p(f"  {z:5s} speed, m/s                   {su:7.4f}  {sd:7.4f}  {su - sd:+7.4f}")
    p("\nThe sleeper's zones at 180 s, C        held    swing  held-swing")
    for z in ("face", "torso", "feet"):
        u, d = at(A["held"], z + "_T", 180) - C0, at(A["swing"], z + "_T", 180) - C0
        p(f"  {z:5s} air                          {u:7.3f}  {d:7.3f}  {u - d:+7.3f}   ({F(u):.1f} and {F(d):.1f} F)")

    # the clip's number: the face in C, rounded, at t = 0 (the room at rest) and every 0.375 s
    tt = np.arange(481) * 0.375
    face = {}
    for r in RUNS:
        a = A[r][1:]
        if len(a) != 480 or not np.allclose(a[:, 0], tt[1:]):
            raise SystemExit(f"{r}: the monitor's rows are not every 0.375 s to 180 s")
        face[r] = np.r_[T0, a[:, K["face_T"]]] - C0
    rh, rs = np.round(face["held"]), np.round(face["swing"])
    p(f"\nThe face in C, rounded, at t = 0 and every 0.375 s ({len(tt)} writes)")
    p(f"  held warmer {int((rh > rs).sum())}, equal {int((rh == rs).sum())}, swing warmer {int((rs > rh).sum())}")
    p(f"  the two first differ at {tt[np.argmax(rh != rs)]:g} s")
    p("  unrounded, from the first row (0.375 s on):")
    for z in ("face", "torso", "feet"):
        a, b = A["held"][1:], A["swing"][1:]
        dT = a[:, K[z + "_T"]] - b[:, K[z + "_T"]]
        t = a[:, 0]
        colder = dT > 0
        changes = int((np.diff(np.sign(dT)) != 0).sum())
        share = integral(t, colder.astype(float), 0.375, 180) / (180 - 0.375)
        nc = np.where(~colder)[0]
        p(f"    {z:5s} swing colder at {int(colder.sum())} of {len(t)} rows, {100 * share:.1f}% of 0.375-180 s; "
          f"the lead changes {changes} times; "
          + (f"held last as cold or colder at {t[nc[-1]]:g} s" if len(nc) else "held never as cold"))
        if len(nc):
            p(f"          held as cold or colder at: " + ", ".join(f"{x:g}" for x in t[nc]) if len(nc) <= 40 else
              f"          held as cold or colder at {len(nc)} rows")
    for s in (0, 9, 30, 60, 90, 120, 150, 180):
        k = int(round(s / 0.375))
        p(f"  {s:4d} s   held {face['held'][k]:6.2f} C ({rh[k]:.0f}, {F(face['held'][k]):.1f} F)"
          f"   swing {face['swing'][k]:6.2f} C ({rs[k]:.0f}, {F(face['swing'][k]):.1f} F)")
    for r in RUNS:
        a = A[r]
        i = int(np.argmin(a[:, K["face_T"]]))
        p(f"  {r:5s} lowest face reading {a[i, K['face_T']] - C0:.2f} C at {a[i, 0]:g} s, {a[i, K['face_speed']]:.3f} m/s")

    p("\nThe surfaces at 180 s       heat into the air, W   mean surface, C     stored, kJ")
    p("                                held    swing       held   swing      held    swing")
    for w in WALLS:
        p(f"  {w:14s}          {at(A['held'], 'Q_' + w, 180):7.1f} {at(A['swing'], 'Q_' + w, 180):8.1f}"
          f"   {at(A['held'], 'Tw_' + w, 180) - C0:7.2f} {at(A['swing'], 'Tw_' + w, 180) - C0:7.2f}"
          f"   {at(A['held'], 'E_' + w, 180) / 1e3:7.2f} {at(A['swing'], 'E_' + w, 180) / 1e3:7.2f}")
    tq = {r: sum(at(A[r], "Q_" + w, 180) for w in WALLS) for r in A}
    te = {r: sum(at(A[r], "E_" + w, 180) for w in WALLS) / 1e3 for r in A}
    p(f"  {'total':14s}          {tq['held']:7.1f} {tq['swing']:8.1f}                       {te['held']:7.2f} {te['swing']:7.2f}")

    p("\nChecks                                         held          swing")
    B = {}
    for r in RUNS:
        a = A[r]
        de = at(a, "internal_energy", 180) - at(a, "internal_energy", 10)
        ds = sum(at(a, "E_" + w, 180) - at(a, "E_" + w, 10) for w in WALLS)
        q = at(a, "heat_integral", 180) - at(a, "heat_integral", 10)
        B[r] = (de, ds, q, 100 * (de + ds + q) / q)
    p("  10-180 s change of the air's internal energy, J " + "  ".join(f"{B[r][0]:13.1f}" for r in RUNS))
    p("  10-180 s change of the layers' stored heat, J   " + "  ".join(f"{B[r][1]:13.1f}" for r in RUNS))
    p("  10-180 s heat removed by the unit, J            " + "  ".join(f"{B[r][2]:13.1f}" for r in RUNS))
    p("  unaccounted, % of the heat removed              " + "  ".join(f"{B[r][3]:13.4f}" for r in RUNS))
    p("  air mass, kg (first and last row)     " + "  ".join(f"{A[r][0, K['mass']]:.9f}/{A[r][-1, K['mass']]:.9f}" for r in RUNS))
    p("  air mass, largest relative change between rows  " + "  ".join(f"{abs(A[r][:, K['mass']] / A[r][0, K['mass']] - 1).max():13.2e}" for r in RUNS))
    for r in RUNS:
        a = A[r]
        p(f"  {r}: warmest air above the 32 C start, K (max over the rows): {max(0.0, (a[:, K['Tmax']] - T0).max()):.3f}"
          f" (first-step row {max(0.0, a[0, K['Tmax']] - T0):.3f})")
        p(f"  {r}: coldest air below the supply, K (max over the rows): {max(0.0, (a[:, K['slot_Tflow']] - a[:, K['Tmin']]).max()):.3f}")

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    with open(out / "zones.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "zone", "T_90_180_C", "speed_90_180_m_s", "T_180_C", "speed_180_m_s"])
        for r in RUNS:
            a = A[r]
            for z in ZONES:
                w.writerow([r, z, f"{mz(r, z + '_T') - C0:.3f}", f"{mz(r, z + '_speed'):.4f}",
                            f"{at(a, z + '_T', 180) - C0:.3f}", f"{at(a, z + '_speed', 180):.4f}"])
    for r in RUNS:
        a = A[r]
        (out / r).mkdir(exist_ok=True)
        with open(out / r / "history.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_s", "imposed_deg", "jet_deg", "outlet_kg_s", "supply_C", "intake_C", "heat_removed_W"]
                       + [f"{z}_C" for z in ZONES] + ["face_m_s", "torso_m_s", "feet_m_s"]
                       + [f"{c}_W" for c in WALLS] + ["dt_ms"])
            for t in np.arange(1.5, HI + 1e-9, 1.5):
                g = lambda c: at(a, c, t)
                w.writerow([f"{t:g}", f"{g('imposed_deg'):.2f}", f"{g('direction_deg'):.2f}", f"{-g('slot_in_signed'):.7f}",
                            f"{g('slot_Tflow') - C0:.3f}", f"{g('intake_Tflow') - C0:.3f}", f"{g('heat'):.2f}"]
                           + [f"{g(z + '_T') - C0:.3f}" for z in ZONES]
                           + [f"{g(z + '_speed'):.4f}" for z in ("face", "torso", "feet")]
                           + [f"{g('Q_' + c):.2f}" for c in WALLS] + [f"{1000 * g('dt'):.4f}"])
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
