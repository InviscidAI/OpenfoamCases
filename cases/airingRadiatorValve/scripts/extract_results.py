#!/usr/bin/env python3
"""Both runs' figures from their per-step monitors.

    python3 extract_results.py <runs dir> <results dir>

Reads <runs>/<run>/postProcessing/budget/history_<start>.csv (the function object airingBudget:
the room's air, the wall layers, the opening, the glass, the window wall's back, the leaks and
the radiation onto the window wall) and radiator/trv_<start>.csv (the fv option trvRadiator: the
head, the valve, the radiator's body and the water's heat), for start 0 (the window open) and 300
(shut). A later start's rows replace the earlier ones from its first time on. Writes
<results>/<run>/history.csv, every 2.5 s, and <results>/summary.txt.

The heat lost since the window opened is the room's whole heat bill: the radiator's heat to the
air so far, plus the little the rooms next door give the layers' backs, less the change in the
air's internal energy and in the heat stored in the wall layers (each face's from its starting
profile). It is checked against what crosses the room's boundary: the enthalpy carried out
through the opening and the heat diffused across it, then the glass, the window wall's back to the
0 C outdoor air and the leaks.

The air's internal energy above 0 C at t = 0 is read from <run>/initial_air.json, which the run's
setup writes; without it (as for the solved runs, set up before that file was written) it is the
solved runs' own 573114.7064990867 J, which the setup's 573114.684 J matches to 4e-8.
"""
import json
import sys
from pathlib import Path

import numpy as np

WH = 3600.0
E0_SOLVED = 573114.7064990867          # J, the room's air at rest at 20 C, as the solved runs counted it
CRAD = 22469.5                          # J/K, the radiator's water and steel (design.py)
TIMES = (30, 60, 150, 300, 450, 600, 900)


def read(folder, prefix):
    fs = sorted(Path(folder).glob(prefix + "_*.csv"), key=lambda f: float(f.stem.split("_")[-1]))
    parts = []
    for f in fs:
        d = np.genfromtxt(f, delimiter=",", names=True)
        d = d[np.isfinite(d[d.dtype.names[-1]])]          # a row cut short at a stop
        parts = [p[p["t"] < d["t"].min() - 1e-9] for p in parts]
        parts.append(d)
    return np.concatenate(parts)


def run_data(run):
    b = read(run / "postProcessing/budget", "history")
    r = read(run / "postProcessing/radiator", "trv")
    assert len(b) == len(r) and np.allclose(b["t"], r["t"], rtol=0, atol=1e-9), "budget and radiator rows differ"
    f = run / "initial_air.json"
    e0 = json.loads(f.read_text())["Eair"] if f.exists() else E0_SOLVED
    t, dt = b["t"], b["dt"]
    d = {k: b[k] for k in b.dtype.names}
    d.update({k: r[k] for k in ("TsenAir", "Ta", "Tsen", "f", "q", "Trad", "Q", "Qwater")})
    d["radiator_Wh"] = np.cumsum(b["Qrad"] * dt) / WH
    d["water_Wh"] = np.cumsum(r["Qwater"] * dt) / WH
    d["nextdoor_Wh"] = np.cumsum(b["Qback"] * dt) / WH
    d["air_Wh"] = (b["Eair"] - e0) / WH                     # change in the air's internal energy
    d["walls_Wh"] = b["Ewall"] / WH                         # change in the layers' stored heat
    d["heat_lost_Wh"] = d["radiator_Wh"] + d["nextdoor_Wh"] - d["air_Wh"] - d["walls_Wh"]
    parts = {k: np.cumsum(b[k] * dt) / WH for k in ("Hout", "diffOut", "Qglass", "Qoutside", "Qinf")}
    d["opening_Wh"] = parts["Hout"] + parts["diffOut"]
    d["glass_Wh"], d["outer_wall_Wh"], d["leaks_Wh"] = parts["Qglass"], parts["Qoutside"], parts["Qinf"]
    d["boundary_Wh"] = sum(parts.values())
    d["closure_percent"] = 100 * (d["heat_lost_Wh"] - d["boundary_Wh"]) / np.maximum(np.abs(d["boundary_Wh"]), 1e-12)
    # the radiator body's stored heat above its start, from its temperature
    d["body_Wh"] = CRAD * (r["Trad"] - r["Trad"][0]) / WH
    return d


def at(d, s):
    """The row at time s (the first step ending at or after it)."""
    return min(int(np.searchsorted(d["t"], s - 1e-9)), len(d["t"]) - 1)


def reversals(f):
    """How many times the valve's opening changes direction, ignoring steps that do not move it."""
    df = np.diff(f)
    s = np.sign(df[np.abs(df) > 1e-12])
    return int(np.sum(s[1:] != s[:-1]))


HIST = [("t_s", "t", 1), ("room_air_C", "meanT", 1), ("air_replaced", "air", 1),
        ("radiator_W", "Qrad", 1), ("water_W", "Qwater", 1), ("valve_flow_per_nominal", "f", 1),
        ("head_C", "Tsen", 1), ("radiator_body_C", "Trad", 1), ("air_in_kg_s", "inflow", 1),
        ("air_out_kg_s", "outflow", 1), ("opening_W", "openingW", 1), ("glass_W", "Qglass", 1),
        ("window_wall_back_W", "Qoutside", 1), ("leaks_W", "Qinf", 1),
        ("radiation_onto_window_wall_W", "QwinRad", 1), ("radiator_Wh", "radiator_Wh", 1),
        ("water_Wh", "water_Wh", 1), ("walls_stored_Wh", "walls_Wh", 1), ("air_energy_Wh", "air_Wh", 1),
        ("heat_lost_Wh", "heat_lost_Wh", 1), ("boundary_loss_Wh", "boundary_Wh", 1),
        ("outer_wall_Wh", "outer_wall_Wh", 1), ("leaks_Wh", "leaks_Wh", 1),
        ("closure_percent", "closure_percent", 1)]


def write_history(d, path):
    d = dict(d)
    d["air"] = 1 - d["meanS"]
    d["openingW"] = d["Hout"] + d["diffOut"]
    for k in ("meanT", "Tsen", "Trad"):
        d[k] = d[k] - 273.15
    keep = np.abs(d["t"] / 2.5 - np.round(d["t"] / 2.5)) < 1e-6
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(",".join(h for h, _, _ in HIST) + "\n")
        for i in np.flatnonzero(keep):
            f.write(",".join(f"{d[k][i]:.6g}" for _, k, _ in HIST) + "\n")
    return int(keep.sum())


def main():
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    D = {n: run_data(runs / n) for n in ("off", "on")}
    L = ["airingRadiatorValve: figures from the two runs (scripts/extract_results.py)", ""]
    for n, d in D.items():
        rows = write_history(d, out / n / "history.csv")
        t = d["t"]
        k = t > 30 - 1e-9
        L += [f"{n}: {len(t)} steps to t = {t[-1]:g} s, largest step {d['dt'].max():.4f} s; "
              f"history.csv {rows} rows every 2.5 s",
              f"  heat budget from 30 s: heat lost against the boundary's loss within "
              f"{np.abs(d['closure_percent'][k]).max():.3f}% at every step (at 900 s {d['closure_percent'][-1]:+.3f}%)",
              "     t  room air  radiator  water  valve  head   body  opening  glass  wall back  leaks  radiation"
              "   heat lost  boundary  walls stored  radiator",
              "     s       C        W       W   /nominal   C      C       W      W       W       W       W"
              "         Wh        Wh       Wh          Wh"]
        for s in TIMES:
            i = at(d, s)
            L.append(f"{t[i]:6.1f} {d['meanT'][i] - 273.15:8.2f} {d['Qrad'][i]:8.1f} {d['Qwater'][i]:7.1f}"
                     f" {d['f'][i]:6.3f} {d['Tsen'][i] - 273.15:6.2f} {d['Trad'][i] - 273.15:6.2f}"
                     f" {d['Hout'][i] + d['diffOut'][i]:8.1f} {d['Qglass'][i]:6.1f} {d['Qoutside'][i]:9.1f}"
                     f" {d['Qinf'][i]:6.1f} {d['QwinRad'][i]:9.1f}   {d['heat_lost_Wh'][i]:8.2f}"
                     f"  {d['boundary_Wh'][i]:8.2f}  {d['walls_Wh'][i]:9.2f}  {d['radiator_Wh'][i]:9.2f}")
        i3 = at(d, 300)
        L += [f"  room's air replaced by 300 s: {100 * (1 - d['meanS'][i3]):.1f}%; gross inflow 0-300 s"
              f" {np.sum(d['inflow'][:i3 + 1] * d['dt'][:i3 + 1]) / t[i3]:.3f} kg/s on average",
              f"  room's mean air: lowest {d['meanT'].min() - 273.15:.2f} C at {t[np.argmin(d['meanT'])]:.0f} s;"
              f" over the last 225 s rising {60 * np.polyfit(t[t > 675], d['meanT'][t > 675], 1)[0]:+.3f} K a minute",
              f"  radiator: {d['radiator_Wh'][i3]:.1f} Wh by 300 s, {d['radiator_Wh'][-1]:.1f} Wh by 900 s;"
              f" water {d['water_Wh'][i3]:.1f} and {d['water_Wh'][-1]:.1f} Wh;"
              f" body {d['Trad'][0] - 273.15:.2f} C at 0 s, {d['Trad'][i3] - 273.15:.2f} C at 300 s,"
              f" {d['Trad'][-1] - 273.15:.2f} C at 900 s",
              f"  radiator's output, W: " + ", ".join(f"{s} s {d['Qrad'][at(d, s)]:.0f}" for s in (0.006, 30, 60, 120, 150, 200, 300))
              + f"; least over 0-300 s {d['Qrad'][:i3 + 1].min():.0f}, most {d['Qrad'][:i3 + 1].max():.0f}",
              f"  valve: {reversals(d['f'])} changes of direction; at its stop (1.233) from "
              + (f"{t[np.argmax(d['f'] > 1.2328)]:.1f} s" if (d['f'] > 1.2328).any() else "never")
              + f"; head {d['Tsen'][i3] - 273.15:.2f} C at 300 s, {d['Tsen'][-1] - 273.15:.2f} C at 900 s",
              f"  over 0-900 s: window wall's back {d['outer_wall_Wh'][-1]:.2f} Wh (mean {d['Qoutside'].mean():.1f} W,"
              f" {d['Qoutside'].min():.1f}-{d['Qoutside'].max():.1f}), leaks {d['leaks_Wh'][-1]:.2f} Wh,"
              f" opening {d['opening_Wh'][-1]:.2f} Wh, glass {d['glass_Wh'][-1]:.2f} Wh,"
              f" rooms next door {d['nextdoor_Wh'][-1]:+.4f} Wh",
              f"  drawn out of the walls, ceiling and floor: {-d['walls_Wh'][i3]:.1f} Wh by 300 s,"
              f" {-d['walls_Wh'][-1]:.1f} Wh by 900 s", ""]
    a, b = D["off"], D["on"]
    L.append("on less off")
    for s in (30, 150, 300, 600, 900):
        i, j = at(a, s), at(b, s)
        L.append(f"  {s:4d} s: heat lost {b['heat_lost_Wh'][j] - a['heat_lost_Wh'][i]:+.2f} Wh"
                 f" ({b['heat_lost_Wh'][j]:.2f} against {a['heat_lost_Wh'][i]:.2f},"
                 f" {100 * (b['heat_lost_Wh'][j] / a['heat_lost_Wh'][i] - 1):+.2f}%);"
                 f" radiator {b['radiator_Wh'][j] - a['radiator_Wh'][i]:+.2f} Wh; water {b['water_Wh'][j] - a['water_Wh'][i]:+.2f} Wh;"
                 f" room air {b['meanT'][j] - a['meanT'][i]:+.2f} K")
    i, j = len(a["t"]) - 1, len(b["t"]) - 1
    parts = {k: b[k][j] - a[k][i] for k in ("water_Wh", "heat_lost_Wh", "air_Wh", "walls_Wh", "body_Wh")}
    L += ["  where the water's extra heat by 900 s is (Wh): "
          f"water {parts['water_Wh']:+.2f} = lost {parts['heat_lost_Wh']:+.2f} + room's air {parts['air_Wh']:+.2f}"
          f" + walls {parts['walls_Wh']:+.2f} + radiator body {parts['body_Wh']:+.2f}"
          f" (sum {parts['heat_lost_Wh'] + parts['air_Wh'] + parts['walls_Wh'] + parts['body_Wh']:+.2f};"
          " the rest is the rooms next door's)"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
