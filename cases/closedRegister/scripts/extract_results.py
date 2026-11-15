#!/usr/bin/env python3
"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv of open and closed, written by the coded
monitor (scripts/monitor.C; the columns are COLS below): one row at the first step and one every
0.625 s from 0.625 s to 300 s. Writes:

  summary.txt          the registers and the return, the spare room's door, the rooms, the rest
                       of the house against the spare room, the heat into the surfaces, the checks
  rooms.csv            every room's mean, ankle, seated, head and ceiling air temperature at
                       15, 30, 60, 120, 150, 180, 240 and 300 s
  <run>/history.csv    every 2.5 s: the supply's heat, the return, the spare room's door gap, the
                       rooms' head-height air, the rest of the house and the spare room, the
                       surfaces' heat and the time step

Temperatures in the files are in C (and F where said), the monitor's in K. The supply's heat is
cp (T - 289.82 K) carried in through the registers less any carried out, cp 1005 J/kg K; the
return's the same carried out. The surfaces' heat is the wall heat flux with the energy
equation's own diffusivity (the energyFluxObserver in constant/fvOptions), positive out of the
air, into the walls, floor and ceiling or out through the glass. The heat budget, from 10 s as in
the study, is the change of the air's enthalpy, the integral of rho cp (T - 289.82 K) dV, against
the supply's heat less the return's and the surfaces', each summed by the monitor at every step;
it is given as a share of the supply's heat over the same interval. The gap's flows are gross,
each way, in kg/s: "out" is out of the spare room into the hall.
"""
import csv
import sys
from pathlib import Path

import numpy as np

REG = ["register_" + s for s in ("livingW", "livingE", "kitchen", "bedroom", "bath", "spare")]
OPENINGS = ["gap", "bedDoor", "bathDoor", "livingDoor", "kitchenDoor"]
ROOMS = ["living", "kitchen", "hall", "bedroom", "bath", "spare", "rest"]
LAYERS = ["mean", "ankle", "seated", "head", "ceiling"]
HEATS = ["floor", "ceiling", "walls", "windows"]
COLS = ["time", "dt", "wall_s"]
for _n in REG + ["return"]:
    COLS += [_n + "_" + _k for _k in ("mout", "min", "T", "hout", "hin")]
for _n in OPENINGS:
    COLS += [_n + "_" + _k for _k in ("mplus", "mminus", "hplus", "hminus")]
COLS += ["mass", "enthalpy", "intp", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z"]
for _r in ROOMS:
    COLS += [_r + "_" + _l + "_T" for _l in LAYERS]
for _n in HEATS:
    COLS += ["Q_" + _n, "I_" + _n, "Qraw_" + _n]
COLS += ["I_supply", "I_return", "I_min", "I_mout"]
K = {c: i for i, c in enumerate(COLS)}
RUNS = ("open", "closed")
C0 = 273.15
END = 300.0
TIMES = (15, 30, 60, 120, 150, 180, 240, 300)


def F(c):
    return c * 1.8 + 32


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

    def col(r, c):
        return A[r][:, K[c]]

    def t(r):
        return A[r][:, 0]

    def at(r, c, x):
        return float(np.interp(x, t(r), col(r, c)))

    def T(r, c, x):
        return at(r, c, x) - C0

    supply = {r: sum(col(r, n + "_hin") - col(r, n + "_hout") for n in REG) for r in RUNS}
    others = {r: sum(col(r, n + "_hin") - col(r, n + "_hout") for n in REG[:5]) for r in RUNS}
    inflow = {r: sum(col(r, n + "_min") for n in REG) for r in RUNS}

    def mean(r, y, a, b):
        m = (t(r) >= a - 1e-9) & (t(r) <= b + 1e-9)
        return float(np.trapezoid(y[m], t(r)[m]) / (t(r)[m][-1] - t(r)[m][0]))

    def from0(r, y, x):
        # the heat from t = 0, where nothing flows yet, to x: the supply is constant from the
        # first step, so the trapezoids of the rows are exact for it
        m = t(r) <= x + 1e-9
        return float(np.trapezoid(np.r_[y[m][0], y[m]], np.r_[0.0, t(r)[m]]))

    L = []
    p = L.append
    p("Subject: a small one-storey house with forced-air heating, warming from a 62 F setback once the blower starts,")
    p("every register open against the spare room's register closed (its door shut in both); the whole house in 3-D, 0-300 s")
    p("")
    p("The registers and the return                    open        closed")
    for n in REG:
        p(f"  {n[9:]:9s} mass flow in, kg/s           " + "  ".join(f"{mean(r, col(r, n + '_min'), 10, END):10.5f}" for r in RUNS))
    p("  all registers, kg/s                    " + "  ".join(f"{mean(r, inflow[r], 10, END):10.5f}" for r in RUNS))
    p("  supply temperature, C                  " + "  ".join(f"{at(r, 'register_livingW_T', END) - C0:10.2f}" for r in RUNS))
    p("  supply's heat, W, 20-30 s mean         " + "  ".join(f"{mean(r, supply[r], 20, 30):10.2f}" for r in RUNS))
    p("  the spare room's register, W           " + "  ".join(f"{mean(r, col(r, 'register_spare_hin') - col(r, 'register_spare_hout'), 20, 30):10.2f}" for r in RUNS))
    p("  the other five registers, W            " + "  ".join(f"{mean(r, others[r], 20, 30):10.2f}" for r in RUNS))
    p("  the other five, MJ from 0 to 150 s     " + "  ".join(f"{from0(r, others[r], 150) / 1e6:10.4f}" for r in RUNS))
    p("  the other five, MJ from 0 to 300 s     " + "  ".join(f"{from0(r, others[r], 300) / 1e6:10.4f}" for r in RUNS))
    for x in (15, 150, 300):
        p(f"  return, kg/s out at {x:3d} s               " + "  ".join(f"{at(r, 'return_mout', x):10.5f}" for r in RUNS))
    for x in (60, 150, 300):
        p(f"  return, C at {x:3d} s                      " + "  ".join(f"{at(r, 'return_T', x) - C0:10.3f}" for r in RUNS))
    for r in RUNS:
        m = t(r) > 10
        ex = col(r, "return_mout")[m] - col(r, "return_min")[m] - inflow[r][m]
        p(f"  {r}: return less registers after 10 s, kg/s: mean {ex.mean():.5f}, at most {100 * np.max(np.abs(ex / inflow[r][m])):.2f}% of the inflow")

    p("\nThe spare room's door (the 5 cm gap under it), kg/s     open (out / in)        closed (out / in)")
    for x in (15, 60, 150, 300):
        p(f"  at {x:3d} s                      " + "     ".join(
            f"{at(r, 'gap_mplus', x):.5f} / {at(r, 'gap_mminus', x):.5f}" for r in RUNS))

    p("\nThe rest of the house and the spare room, air at head height (y 1.5-1.8 m) and whole-room means")
    p("   t s   rest head C (F)            spare head C (F)            rest mean C          spare mean C")
    p("         open        closed         open        closed          open    closed      open    closed")
    for x in (0,) + TIMES:
        rh = [T(r, "rest_head_T", x) for r in RUNS]
        sh = [T(r, "spare_head_T", x) for r in RUNS]
        rm = [T(r, "rest_mean_T", x) for r in RUNS]
        sm = [T(r, "spare_mean_T", x) for r in RUNS]
        p(f"  {x:4d}  {rh[0]:6.3f} ({F(rh[0]):4.1f})  {rh[1]:6.3f} ({F(rh[1]):4.1f})   {sh[0]:6.3f} ({F(sh[0]):4.1f})  {sh[1]:6.3f} ({F(sh[1]):4.1f})"
          f"    {rm[0]:6.3f}  {rm[1]:6.3f}    {sm[0]:6.3f}  {sm[1]:6.3f}")
    p("  closed less open, K:  t s   rest head   rest mean   spare head   spare mean")
    for x in (60, 150, 300):
        d = [T("closed", c, x) - T("open", c, x) for c in ("rest_head_T", "rest_mean_T", "spare_head_T", "spare_mean_T")]
        p(f"                       {x:4d}   {d[0]:+8.3f}    {d[1]:+8.3f}     {d[2]:+8.3f}     {d[3]:+8.3f}")
    p("  rest less spare at head height at 60 s, K: " + "  ".join(f"{r} {T(r, 'rest_head_T', 60) - T(r, 'spare_head_T', 60):+.3f}" for r in RUNS))
    rf = {r: np.round(F(col(r, "rest_head_T") - C0)) for r in RUNS}
    tt = t("open")
    rc = np.round(F(np.interp(tt, t("closed"), col("closed", "rest_head_T")) - C0))
    first = tt[np.argmax(rc != rf["open"])]
    p(f"  rest of the house at head height, rounded F, at 0, 150, 300 s: open "
      + ", ".join(f"{F(T('open', 'rest_head_T', x)):.0f}" for x in (0, 150, 300))
      + "; closed " + ", ".join(f"{F(T('closed', 'rest_head_T', x)):.0f}" for x in (0, 150, 300)))
    p(f"  the two rounded numbers first differ at {first:g} s; closed's below open's at {int((rc < rf['open']).sum())} of {len(tt)} rows")

    p("\nThe heat out of the air into the surfaces, W (positive out of the air)   open      closed")
    for n in HEATS:
        for x in (15, 150, 300):
            p(f"  {n:8s} at {x:3d} s                                           " + "  ".join(f"{at(r, 'Q_' + n, x):9.1f}" for r in RUNS))
        p(f"  {n:8s} 10-300 s mean                                      " + "  ".join(f"{mean(r, col(r, 'Q_' + n), 10, END):9.1f}" for r in RUNS))
    p("  share of the supply's heat (0-300 s) still in the air at 300 s   " + "  ".join(
        f"{100 * at(r, 'enthalpy', END) / at(r, 'I_supply', END):8.1f}%" for r in RUNS))

    p("\nChecks                                       open              closed")
    bud = {}
    for r in RUNS:
        net = col(r, "I_supply") - col(r, "I_return") - sum(col(r, "I_" + n) for n in HEATS)
        dE = at(r, "enthalpy", END) - at(r, "enthalpy", 10)
        dN = float(np.interp(END, t(r), net) - np.interp(10, t(r), net))
        dS = at(r, "I_supply", END) - at(r, "I_supply", 10)
        bud[r] = (dS, dE, dN, 100 * (dE - dN) / dS)
    p("  10-300 s supply's heat, J               " + "  ".join(f"{bud[r][0]:16.1f}" for r in RUNS))
    p("  10-300 s change of the air's enthalpy, J" + "  ".join(f"{bud[r][1]:16.1f}" for r in RUNS))
    p("  10-300 s supply less return and surfaces" + "  ".join(f"{bud[r][2]:16.1f}" for r in RUNS))
    p("  unaccounted, % of the supply's heat     " + "  ".join(f"{bud[r][3]:16.4f}" for r in RUNS))
    p("  air mass, kg (first and last row)       " + "  ".join(f"{col(r, 'mass')[0]:.4f}/{col(r, 'mass')[-1]:.4f}" for r in RUNS))
    p("  integral of p dV, relative range        " + "  ".join(
        f"{(col(r, 'intp').max() - col(r, 'intp').min()) / col(r, 'intp')[0]:16.2e}" for r in RUNS))
    for r in RUNS:
        i, j = np.argmin(col(r, "Tmin")), np.argmax(col(r, "Tmax"))
        p(f"  {r}: coldest air {col(r, 'Tmin')[i] - C0:.3f} C at {t(r)[i]:g} s, ({col(r, 'Tmin_x')[i]:g}, {col(r, 'Tmin_y')[i]:g}, {col(r, 'Tmin_z')[i]:g}) m;"
          f" warmest {col(r, 'Tmax')[j] - C0:.3f} C at {t(r)[j]:g} s, ({col(r, 'Tmax_x')[j]:g}, {col(r, 'Tmax_y')[j]:g}, {col(r, 'Tmax_z')[j]:g}) m"
          f" (rows every 0.625 s; supply {at(r, 'register_livingW_T', END) - C0:.2f} C)")
    p("  time step, ms at 300 s, and the rows' least and largest   " + "  ".join(
        f"{1000 * at(r, 'dt', END):.2f} ({1000 * col(r, 'dt').min():.2f}-{1000 * col(r, 'dt').max():.2f})" for r in RUNS))

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    with open(out / "rooms.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "room"] + [f"{l}_{x}s_C" for x in TIMES for l in LAYERS])
        for r in RUNS:
            for room in ROOMS:
                w.writerow([r, room] + [f"{T(r, room + '_' + l + '_T', x):.3f}" for x in TIMES for l in LAYERS])
    for r in RUNS:
        (out / r).mkdir(exist_ok=True)
        with open(out / r / "history.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_s", "supply_W", "return_out_kg_s", "return_C", "gap_out_kg_s", "gap_in_kg_s"]
                       + [f"{room}_head_C" for room in ROOMS] + ["rest_mean_C", "spare_mean_C"]
                       + [f"{n}_W" for n in HEATS] + ["dt_ms"])
            for x in np.arange(2.5, END + 1e-9, 2.5):
                w.writerow([f"{x:g}", f"{np.interp(x, t(r), supply[r]):.2f}", f"{at(r, 'return_mout', x):.5f}",
                            f"{T(r, 'return_T', x):.3f}", f"{at(r, 'gap_mplus', x):.5f}", f"{at(r, 'gap_mminus', x):.5f}"]
                           + [f"{T(r, room + '_head_T', x):.3f}" for room in ROOMS]
                           + [f"{T(r, 'rest_mean_T', x):.3f}", f"{T(r, 'spare_mean_T', x):.3f}"]
                           + [f"{at(r, 'Q_' + n, x):.2f}" for n in HEATS] + [f"{1000 * at(r, 'dt', x):.4f}"])
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
