#!/usr/bin/env python3
"""Write results/ from both runs' monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv (columns in scripts/columns.json's order),
runs/<run>/log.buoyantPimpleFoam if it is there (the pressure solves at their iteration cap) and
runs/mesh/cells.npz (the air's starting mass and integral of p for the budgets), and writes

    results/<run>/history.csv   a row every 2.5 s of flow: the supply, the return, the zones' mean
                                air, the sofa's boxes, the surfaces and the budgets
    results/summary.txt         the figures the README quotes

Temperatures are in K unless the column says F; differences in F are 1.8 x those in K. Means over
time are trapezoidal over the monitor's rows (every 0.625 s). The heat over a cycle is the
monitor's running sum of the register's heat above the return's enthalpy, carried from the last
row before the cycle's end at that row's power (both runs' power is constant across those gaps:
the furnace is off at 744 s and 1488 s).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
T0, CP, GAS_R = 292.04, 1005.0, 8314.46261815324 / 28.96
COLS = json.loads((CASE / "scripts/columns.json").read_text())
WALLS = ["outerWall", "innerWall", "floor", "ceiling", "sideWall", "sofa", "window"]
REPORT = [15, 60, 150, 300, 435, 438, 440, 500, 600, 740, 744, 800, 1180, 1182, 1240, 1300, 1487.5]
F = 1.8


def toF(k):
    return (k - 273.15) * 1.8 + 32


def load(run_dir):
    a = np.loadtxt(run_dir / "postProcessing/metrics/metrics.csv", delimiter=",")
    return {c: a[:, i] for i, c in enumerate(COLS)}


def start_state(mesh):
    cells = np.load(mesh / "cells.npz")
    C, V = cells["C"], cells["V"]
    p0 = 1e5 * np.exp(-9.81 * C[:, 1] / (287.1 * T0))
    return float(np.sum(p0 / (GAS_R * T0) * V)), float(np.sum(p0 * V))


def budgets(d, mass0, intp0):
    walls = sum(d[w + "_Iair_J"] for w in WALLS)
    resid = d["enthalpy_J"] - (d["intp_J"] - intp0) - d["I_supply_J"] + d["I_return_J"] + walls
    i10 = int(np.argmin(np.abs(d["time"] - 10)))
    closure10 = (resid[-1] - resid[i10]) / (d["I_heater_J"][-1] - d["I_heater_J"][i10])
    mass_resid = d["mass_kg"] - mass0 - d["I_mass_in_kg"] + d["I_mass_out_kg"]
    return resid, closure10, mass_resid


def heat_to(d, t):
    i = int(np.searchsorted(d["time"], t + 1e-9) - 1)
    if i < 0:
        return 0.0
    return d["I_heater_J"][i] + d["heater_W"][i] * (t - d["time"][i])


def tmean(t, y, lo, hi):
    m = (t >= lo - 1e-9) & (t <= hi + 1e-9)
    tt, yy = t[m], y[m]
    return float(np.sum(0.5 * (yy[1:] + yy[:-1]) * np.diff(tt)) / (tt[-1] - tt[0]))


def at(d, t):
    return int(np.argmin(np.abs(d["time"] - t)))


def backflow_T(d):
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(d["return_min"] > 1e-6, T0 + d["return_hin"] / (CP * d["return_min"]), np.nan)


def pressure_hits(log):
    if not log.exists():
        return None
    hits, t, last = 0, 0.0, None
    for line in log.read_text(errors="replace").splitlines():
        if line.startswith("Time = "):
            t = float(line.split("=")[1])
        elif "Solving for p_rgh" in line and "No Iterations 100" in line:
            hits += 1
            last = t
    return hits, last


def history(d, path):
    keep = np.isclose(np.mod(d["time"] + 1e-9, 2.5), 0, atol=1e-6) | (d["time"] == d["time"][0]) | (d["time"] == d["time"][-1])
    bt = backflow_T(d)
    cols = [
        ("time_s", d["time"]),
        ("register_kg_s", d["register_min"]), ("register_T_K", d["register_T"]),
        ("heat_above_return_W", d["heater_W"]), ("heat_above_return_sum_J", d["I_heater_J"]),
        ("return_out_kg_s", d["return_mout"]), ("return_in_kg_s", d["return_min"]),
        ("return_out_mean_T_K", d["return_reference_T"]), ("return_in_T_K", bt),
        ("air_T_K", d["air_T_K"]),
        ("occupied_ankle_T_K", d["occupied_ankle_T_K"]), ("occupied_seatedHead_T_K", d["occupied_seatedHead_T_K"]),
        ("occupied_standingHead_T_K", d["occupied_standingHead_T_K"]), ("occupied_ceiling_T_K", d["occupied_ceiling_T_K"]),
        ("sofa_ankle_T_K", d["sofa_ankle_T_K"]), ("sofa_head_T_K", d["sofa_head_T_K"]),
        ("sofa_head_minus_ankle_K", d["sofa_head_minus_ankle_K"]), ("sofa_head_minus_ankle_F", F * d["sofa_head_minus_ankle_K"]),
        ("sofa_ankle_Umean_m_s", d["sofa_ankle_Umean_m_s"]), ("sofa_ankle_Umax_m_s", d["sofa_ankle_Umax_m_s"]),
        ("sofa_head_Umean_m_s", d["sofa_head_Umean_m_s"]), ("sofa_head_Umax_m_s", d["sofa_head_Umax_m_s"]),
        ("floor_surface_T_K", d["floor_Tsurface_K"]), ("ceiling_surface_T_K", d["ceiling_Tsurface_K"]),
        ("window_surface_T_K", d["window_Tsurface_K"]),
        ("heat_into_surfaces_W", sum(d[w + "_Qair_W"] for w in WALLS)), ("heat_out_window_W", d["window_Qair_W"]),
        ("jet_y2.2_Umax_m_s", d["jet_y2.2_Umax_m_s"]), ("jet_y2.2_Tmax_K", d["jet_y2.2_Tmax_K"]),
        ("air_Tmin_K", d["Tmin_K"]), ("air_Tmax_K", d["Tmax_K"]),
        ("energy_residual_J", d["energy_residual_J"]), ("mass_residual_kg", d["mass_residual_kg"]),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(",".join(n for n, _ in cols) + "\n")
        for i in np.nonzero(keep)[0]:
            f.write(",".join("" if np.isnan(v[i]) else f"{v[i]:.10g}" for _, v in cols) + "\n")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    mass0, intp0 = start_state(runs / "mesh")
    data, lines = {}, []
    for run in ("furnace", "heatPump"):
        d = load(runs / run)
        resid, closure10, mres = budgets(d, mass0, intp0)
        d["energy_residual_J"], d["mass_residual_kg"] = resid, mres
        data[run] = (d, closure10)
        history(d, out / run / "history.csv")

    w = lines.append
    w("Furnace against heat pump, the half living room (4.5 x 2.4 x 2.4 m; the whole room is 4.8 m wide).")
    w("All heats and flows are the half room's; double them for the whole. From scripts/extract_results.py.")
    w(f"Air at the start: {mass0:.6f} kg at {T0} K, hydrostatic.")
    w("")
    for run, (d, closure10) in data.items():
        t = d["time"]
        w(f"== {run}: {len(t)} monitor rows, {t[0]:g} to {t[-1]:g} s")
        w("  time s | air K | sofa head K | sofa feet K | head-feet K (F) | occupied seated head K | occupied ankle K | heat W | return in kg/s at K")
        bt = backflow_T(d)
        for tt in REPORT:
            i = at(d, tt)
            back = f"{d['return_min'][i]:.6f} at {bt[i]:.3f}" if d["return_min"][i] > 1e-6 else "0"
            w(f"  {t[i]:7.3f} | {d['air_T_K'][i]:.3f} | {d['sofa_head_T_K'][i]:.3f} | {d['sofa_ankle_T_K'][i]:.3f} | "
              f"{d['sofa_head_minus_ankle_K'][i]:.3f} ({F * d['sofa_head_minus_ankle_K'][i]:.2f}) | {d['occupied_seatedHead_T_K'][i]:.3f} | "
              f"{d['occupied_ankle_T_K'][i]:.3f} | {d['heater_W'][i]:.2f} | {back}")
        for label, lo, hi in (("whole run", 0, t[-1]), ("last cycle", 744, t[-1])):
            gap = d["sofa_head_minus_ankle_K"]
            m = (t >= lo - 1e-9)
            w(f"  {label} ({lo:g}-{hi:g} s): sofa head mean {tmean(t, d['sofa_head_T_K'], lo, hi):.4f} K ({toF(tmean(t, d['sofa_head_T_K'], lo, hi)):.2f} F),"
              f" feet mean {tmean(t, d['sofa_ankle_T_K'], lo, hi):.4f} K ({toF(tmean(t, d['sofa_ankle_T_K'], lo, hi)):.2f} F),"
              f" head-feet mean {tmean(t, gap, lo, hi):.4f} K ({F * tmean(t, gap, lo, hi):.2f} F), head-feet {gap[m].min():.3f} to {gap[m].max():.3f} K"
              f" ({F * gap[m].min():.2f} to {F * gap[m].max():.2f} F); sofa head {toF(d['sofa_head_T_K'][m].min()):.2f} to {toF(d['sofa_head_T_K'][m].max()):.2f} F")
        late = t >= 60
        w(f"  sofa head after 60 s: {toF(d['sofa_head_T_K'][late].min()):.2f} to {toF(d['sofa_head_T_K'][late].max()):.2f} F")
        w(f"  the room's mean air: {d['air_T_K'][0]:.4f} K at the start, {d['air_T_K'][-1]:.4f} K at {t[-1]:g} s, up {d['air_T_K'][-1] - T0:.4f} K ({F * (d['air_T_K'][-1] - T0):.2f} F)")
        w(f"  supply: register {d['register_T'][at(d, 15)]:.3f} K ({toF(d['register_T'][at(d, 15)]):.1f} F) at 15 s,"
          f" {np.nanmax(np.where(d['register_min'] > 1e-6, d['register_T'], np.nan)):.3f} K ({toF(np.nanmax(np.where(d['register_min'] > 1e-6, d['register_T'], np.nan))):.1f} F) at most while it blows")
        w(f"  fastest air in the sofa's boxes: {max(d['sofa_head_Umax_m_s'].max(), d['sofa_ankle_Umax_m_s'].max()):.4f} m/s;"
          f" mean speed at the feet {tmean(t, d['sofa_ankle_Umean_m_s'], 0, t[-1]):.4f} m/s, at the head {tmean(t, d['sofa_head_Umean_m_s'], 0, t[-1]):.4f} m/s over the run")
        h1, h2 = heat_to(d, 744), heat_to(d, 1488) - heat_to(d, 744)
        w(f"  heat above the return: {h1:.2f} J over 0-744 s, {h2:.2f} J over 744-1488 s")
        inflow = d["return_min"] > 1e-6
        if inflow.any():
            err = np.abs(bt[inflow] - d["return_reference_T"][inflow])
            w(f"  return inflow in {inflow.sum()} rows ({t[inflow][0]:g}-{t[inflow][-1]:g} s), at most {d['return_min'].max():.6f} kg/s;"
              f" its temperature within {err.max():.4g} K of the return's outward mean")
        else:
            w(f"  no air came in through the return after the first row (largest inflow {d['return_min'][1:].max():.3g} kg/s)")
        w(f"  energy budget: residual {d['energy_residual_J'][-1]:+.3f} J at {t[-1]:g} s; over 10-{t[-1]:g} s it closes to {closure10:+.3e} of the heat given ({100 * closure10:+.4f}%)")
        w(f"  air mass budget: residual {d['mass_residual_kg'][-1]:+.3e} kg ({d['mass_residual_kg'][-1] / mass0:+.2e} of the air)")
        w(f"  coldest and hottest air over the run: {d['Tmin_K'].min():.4f} and {d['Tmax_K'].max():.4f} K")
        ph = pressure_hits(runs / run / "log.buoyantPimpleFoam")
        if ph:
            w(f"  final pressure solves at their 100-iteration cap: {ph[0]}, the last at {ph[1]} s" if ph[0] else "  no final pressure solve at its cap")
        w("")
    (df, _), (dh, _) = data["furnace"], data["heatPump"]
    w("== furnace against heatPump")
    for lo, hi in ((0, 744), (744, 1488)):
        a = heat_to(df, hi) - heat_to(df, lo)
        b = heat_to(dh, hi) - heat_to(dh, lo)
        w(f"  heat over {lo}-{hi} s: furnace {a / 1e3:.3f} kJ, heat pump {b / 1e3:.3f} kJ, apart by {100 * abs(a - b) / b:.3f}% of the heat pump's")
    g = df["sofa_head_minus_ankle_K"] - np.interp(df["time"], dh["time"], dh["sofa_head_minus_ankle_K"])
    late = df["time"] >= 60
    w(f"  after 60 s the furnace's head-feet gap is the larger at {np.mean(g[late] > 0) * 100:.1f}% of the furnace's rows,"
      f" by {F * g[late].min():+.2f} to {F * g[late].max():+.2f} F")
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
