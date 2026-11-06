"""Figures from the solved runs' monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

Reads <runsDir>/<run>/postProcessing/heatAccounting/heat.csv (one row a time step) and
diagnostics59/diagnostics.csv (one row a simulated second), and each run's
log.buoyantPimpleFoam, for legs and flat; and, if <runsDir>/bare has run, its heat.csv for the
convector's check against the catalogue. Writes <resultsDir>/<run>/history.csv (every 2.5 s),
<resultsDir>/minutes.csv and <resultsDir>/summary.txt.

The radiator's heat is the panel's convection and radiation plus the energy balance of the
convector's air held at 55 C, radiatorCover's total_W, with the sensible enthalpy referenced to
16 C, this room's start: the enthalpy carried and diffused out of the convector zone, less the
rise of its own energy and kinetic energy. The zone's energy and mass at t = 0 are integrated
from the hydrostatic start that scripts/make_case.py writes. Each step's heat is taken as constant
over the step, from the previous monitored time to its own; the heat since switch-on is their sum.

The flows are the diagnostics59 monitor's gross volume flows, each direction summed on its own,
through the line x = 0.70 m, y = 0-0.15 m under the sofa (0 in flat, where it is solid) and the
line y = 0.70 m, x = 0.123-0.273 m across the slot between the panel and the sofa's back (the
convector's passage behind the panel is not on it). The monitor's slot temperature, slotT_K,
averages a box that takes in the convector held at 55 C and is not written here.
"""
import argparse
import csv
import re
from pathlib import Path

import numpy as np

import make_case

R = 8314.46261815324 / 28.96
CV = 1005 - R
T0 = 289.15
CP = 1005
LAYERS = ["floor", "ceiling", "innerWall", "outerWall", "sofa"]
TIMES = [10, 30, 60, 120, 180, 240, 300]


def read_heat(run):
    d = np.genfromtxt(run / "postProcessing/heatAccounting/heat.csv", delimiter=",", names=True)
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def read_diag(run):
    """The per-second monitor; a last row cut short when the run ended is padded with nan."""
    lines = (run / "postProcessing/diagnostics59/diagnostics.csv").read_text().splitlines()
    names = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        v = [float(a) if a else np.nan for a in line.split(",")]
        rows.append(v + [np.nan] * (len(names) - len(v)))
    a = np.array(rows)
    return {n: a[:, k] for k, n in enumerate(names)}


def start(run=None):
    """The hydrostatic start: the cell centres, volumes (per metre) and pressures, and the cells
    of the convector zone and, with a run named, of that run's air."""
    x, y = make_case.x, make_case.y
    xc, yc = (x[1:] + x[:-1]) / 2, (y[1:] + y[:-1]) / 2
    X, Y = np.meshgrid(xc, yc)
    V = np.outer(np.diff(y), np.diff(x))
    zone = (X > .04) & (X < .103) & (Y > .15) & (Y < .75)
    p = 1e5 * np.exp(-9.81 * (Y - 1.174) / (R * T0))
    air = None if run is None else ~np.vectorize(lambda a, b: make_case.solid(run, a, b))(X, Y)
    return V, p, zone, air


def initial_zone():
    """The convector zone's air at t = 0: mass and internal energy, (cv/R) p V, per metre."""
    V, p, zone, _ = start()
    return float((p / (R * T0) * V)[zone].sum()), float((CV / R * p * V)[zone].sum())


def initial_mass(run):
    V, p, _, air = start(run)
    return float((p / (R * T0) * V)[air].sum())


def series(d):
    """The radiator's output, W/m: convection (convector zone + panel) and the panel's radiation."""
    t = d["time"]
    dt = np.diff(np.r_[0, t])
    M0, E0 = initial_zone()
    ez = d["Uzone"] - CP * T0 * d["zoneMass"]
    conv = (d["zoneEnthalpy"] + d["zoneDiffusion"] + np.diff(np.r_[E0 - CP * T0 * M0, ez]) / dt
            + np.diff(np.r_[0, d["KEzone"]]) / dt + d["panelConvection"])
    rad = d["panelRadiation"]
    return t, dt, conv, rad


def cum(t, dt, q):
    """The integral from 0 to each monitored time, and a function giving it at any time."""
    E = np.cumsum(q * dt)
    return E, lambda s: float(np.interp(s, np.r_[0, t], np.r_[0, E]))


def log_stats(run):
    log = run / "log.buoyantPimpleFoam"
    if not log.exists():
        return None
    txt = log.read_text()
    steps = len(re.findall(r"^deltaT = ", txt, re.M))
    clock = re.findall(r"ClockTime = ([\d.eE+-]+) s", txt)
    caps = re.findall(r"Solving for p_rgh, Initial residual = [^,]+, Final residual = ([^,]+), No Iterations 100\b", txt)
    return steps, float(clock[-1]) if clock else float("nan"), len(caps)


def run_results(run):
    M0 = initial_mass(run.name)
    d = read_heat(run)
    g = read_diag(run)
    t, dt, conv, rad = series(d)
    q = conv + rad
    E, Eat = cum(t, dt, q)
    _, Cat = cum(t, dt, conv)
    _, Rat = cum(t, dt, rad)
    glass = -(d["glassConv"] + d["glassRad"])
    _, Gat = cum(t, dt, glass)
    td = g["time"]

    def diag_at(key, s):
        ok = ~np.isnan(g[key])
        return float(np.interp(s, td[ok], g[key][ok]))

    def stored(s):
        return sum(diag_at(p + "Storage_J", s) for p in LAYERS)

    # each layered patch: what it stored against minus the integrated wall heat flux into it
    layers = {}
    a, b = float(td[0]), float(min(td[~np.isnan(g["sofaStorage_J"])][-1], t[-1]))
    for p in LAYERS:
        _, Fat = cum(t, dt, -(d[p + "Conv"] + d[p + "Rad"]))
        S = diag_at(p + "Storage_J", b) - diag_at(p + "Storage_J", a)
        F = Fat(b) - Fat(a)
        layers[p] = (S, F)
    # whole-section budget over 10-300 s: radiator in = air's internal energy + layers + glass out
    lo, hi = 10.0, 300.0
    Uroom = lambda s: float(np.interp(s, t, d["Uroom"]))
    budget = dict(inp=Eat(hi) - Eat(lo), air=Uroom(hi) - Uroom(lo), layers=stored(hi) - stored(lo),
                  glass=Gat(hi) - Gat(lo))
    budget["residual"] = budget["inp"] - budget["air"] - budget["layers"] - budget["glass"]
    return dict(t=t, dt=dt, q=q, conv=conv, rad=rad, glass=glass, Eat=Eat, Cat=Cat, Rat=Rat, Gat=Gat,
                diag_at=diag_at, layers=layers, layer_span=(a, b), budget=budget,
                mass_drift=float(np.max(np.abs(d["mass"] / M0 - 1))), last=float(t[-1]),
                airmin=float(np.nanmin(g["airMin_K"])) - 273.15, airmax=float(np.nanmax(g["airMax_K"])) - 273.15,
                sofa=(float(np.nanmin(g["sofaMin_K"])) - 273.15, float(np.nanmax(g["sofaMax_K"])) - 273.15),
                log=log_stats(run))


def mean(r, key, lo, hi):
    m = (r["t"] > lo + 1e-9) & (r["t"] <= hi + 1e-9)
    return float(np.sum(r[key][m] * r["dt"][m]) / np.sum(r["dt"][m]))


def write_history(r, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    da = r["diag_at"]
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["start_s", "end_s", "output_W", "convection_W", "radiation_W", "output_since_0_kJ",
                    "under_to_radiator_l_s", "under_away_l_s", "slot_up_l_s", "slot_down_l_s",
                    "room_C", "sofa_back_C", "glass_out_W"])
        for lo in np.arange(0, 300, 2.5):
            hi = lo + 2.5
            w.writerow([f"{lo:g}", f"{hi:g}", f"{mean(r, 'q', lo, hi):.2f}", f"{mean(r, 'conv', lo, hi):.2f}",
                        f"{mean(r, 'rad', lo, hi):.2f}", f"{r['Eat'](hi) / 1e3:.3f}",
                        f"{1e3 * da('underNegative_m3s', hi):.2f}", f"{1e3 * da('underPositive_m3s', hi):.2f}",
                        f"{1e3 * da('slotUp_m3s', hi):.2f}", f"{1e3 * da('slotDown_m3s', hi):.2f}",
                        f"{da('roomT_K', hi) - 273.15:.3f}", f"{da('sofaBack_K', hi) - 273.15:.3f}",
                        f"{mean(r, 'glass', lo, hi):.2f}"])


def bare_fit(run):
    """The convector's check: the bare room's output over 25-40 s against the catalogue rating,
    980 W at dT50 by EN 442's exponent 1.3, at the mean temperature of all the room's air."""
    d = read_heat(run)
    t, dt, conv, rad = series(d)
    q = conv + rad
    m = (t > 25) & (t <= 40)
    Tm = np.average(d["massT"][m] / d["mass"][m], weights=dt[m])
    out = np.average(q[m], weights=dt[m])
    rating = 980 * ((328.15 - Tm) / 50) ** 1.3
    return float(t[-1]), Tm - 273.15, out, rating


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs")
    ap.add_argument("results")
    a = ap.parse_args()
    runs, out = Path(a.runs), Path(a.results)
    out.mkdir(parents=True, exist_ok=True)
    rr = {n: run_results(runs / n) for n in ("legs", "flat")}
    for n, r in rr.items():
        write_history(r, out / n / "history.csv")
    L, F = rr["legs"], rr["flat"]

    with (out / "minutes.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["start_s", "end_s", "legs_output_W", "flat_output_W", "flat_over_legs_minute",
                    "legs_since_0_kJ", "flat_since_0_kJ", "flat_over_legs_since_0"])
        for lo in range(0, 300, 60):
            hi = lo + 60
            ml, mf = mean(L, "q", lo, hi), mean(F, "q", lo, hi)
            w.writerow([lo, hi, f"{ml:.2f}", f"{mf:.2f}", f"{mf / ml:.4f}", f"{L['Eat'](hi) / 1e3:.3f}",
                        f"{F['Eat'](hi) / 1e3:.3f}", f"{F['Eat'](hi) / L['Eat'](hi):.4f}"])

    s = []
    s.append("sofaLegsVsFlat: figures from the runs' monitors (scripts/extract_results.py)")
    s.append("A sofa on legs and the same sofa flat on the floor, its back 15 cm from a radiator held at 55 C,")
    s.append("0-300 s from switch-on, W and J per metre of section")
    s.append("")
    for n, r in rr.items():
        lg = r["log"]
        extra = f", {lg[0]} steps, {lg[1]:.0f} s of wall time on 8 ranks, {lg[2]} final pressure solves at 100 iterations" if lg else ""
        s.append(f"{n}: monitored to t = {r['last']:g} s{extra}")
    s.append("")
    s.append("The radiator's heat from switch-on to 300 s, kJ/m")
    s.append("            output  convection  radiation")
    for n, r in rr.items():
        s.append(f"  {n:5s}   {r['Eat'](300) / 1e3:8.2f}    {r['Cat'](300) / 1e3:8.2f}   {r['Rat'](300) / 1e3:8.2f}")
    s.append(f"  flat / legs  {100 * F['Eat'](300) / L['Eat'](300):.2f}%   convection {100 * F['Cat'](300) / L['Cat'](300):.1f}%"
             f"   radiation {100 * F['Rat'](300) / L['Rat'](300):.1f}%")
    s.append("")
    s.append("Since switch-on, flat as a share of legs")
    s.append("  " + "  ".join(f"{t:>3d} s {100 * F['Eat'](t) / L['Eat'](t):5.1f}%" for t in TIMES))
    s.append("Each minute on its own (mean W/m)")
    for lo in range(0, 300, 60):
        ml, mf = mean(L, "q", lo, lo + 60), mean(F, "q", lo, lo + 60)
        s.append(f"  {lo:3d}-{lo + 60:3d} s  legs {ml:6.1f}  flat {mf:6.1f}  {100 * mf / ml:5.1f}%")
    s.append("")
    s.append("At each time: the radiator's output now (W/m), the gross flows (l/s per metre), the air")
    s.append("(mass-weighted, the convector's cells left out) and the sofa's back (area mean), C")
    s.append("     t   output        under sofa,      slot top, legs     slot top, flat     room air       sofa back")
    s.append("         legs  flat    legs to rad.     up     down        up     down        legs   flat    legs   flat")
    for t in TIMES:
        lq = float(np.interp(t, L["t"], L["q"]))
        fq = float(np.interp(t, F["t"], F["q"]))
        la, fa = L["diag_at"], F["diag_at"]
        s.append(f"  {t:4d}  {lq:5.1f} {fq:5.1f}    {1e3 * la('underNegative_m3s', t):6.2f}        "
                 f"{1e3 * la('slotUp_m3s', t):6.2f} {1e3 * la('slotDown_m3s', t):6.2f}      "
                 f"{1e3 * fa('slotUp_m3s', t):6.2f} {1e3 * fa('slotDown_m3s', t):6.2f}      "
                 f"{la('roomT_K', t) - 273.15:5.2f}  {fa('roomT_K', t) - 273.15:5.2f}   "
                 f"{la('sofaBack_K', t) - 273.15:5.2f}  {fa('sofaBack_K', t) - 273.15:5.2f}")
    s.append("  Under the legged sofa the flow away from the radiator stays at "
             f"{1e3 * max(L['diag_at']('underPositive_m3s', t) for t in TIMES):.2f} l/s or less at these times; "
             "flat has no air there.")
    s.append("")
    s.append("Heat budget over 10-300 s, kJ/m: the radiator's heat = rise of the air's internal energy,")
    s.append("(cv/R) integral p dV, + heat stored in the wall and sofa layers + heat out through the glass")
    s.append("          radiator    air  layers  glass  residual")
    for n, r in rr.items():
        b = r["budget"]
        s.append(f"  {n:5s}   {b['inp'] / 1e3:7.3f} {b['air'] / 1e3:7.3f} {b['layers'] / 1e3:7.3f} {b['glass'] / 1e3:6.3f}"
                 f"  {b['residual'] / 1e3:+.4f} ({100 * b['residual'] / b['inp']:+.3f}%)")
    s.append("Each layer's stored heat against minus its integrated wall heat flux (convection and the")
    s.append("radiation it absorbs), from the first per-second row to the last, error %")
    for n, r in rr.items():
        s.append(f"  {n:5s} " + "  ".join(f"{p} {100 * (S - Fl) / Fl:+.3f}" for p, (S, Fl) in r["layers"].items()))
    s.append("")
    for n, r in rr.items():
        s.append(f"{n}: air mass within {r['mass_drift']:.2e} of the start's; air {r['airmin']:.2f} to {r['airmax']:.2f} C "
                 f"(each second, the convector at 55); sofa's surface {r['sofa'][0]:.2f} to {r['sofa'][1]:.2f} C")
    bare = runs / "bare"
    if (bare / "postProcessing/heatAccounting/heat.csv").exists():
        last, Tm, o, rating = bare_fit(bare)
        s.append("")
        s.append(f"bare, the convector's check (monitored to {last:g} s): over 25-40 s the radiator gives "
                 f"{o:.1f} W/m with the room's air at {Tm:.3f} C,")
        s.append(f"  against the catalogue's {rating:.1f} W/m at that temperature, {100 * (o / rating - 1):+.2f}%")
    (out / "summary.txt").write_text("\n".join(s) + "\n")
    print("\n".join(s))


if __name__ == "__main__":
    main()
