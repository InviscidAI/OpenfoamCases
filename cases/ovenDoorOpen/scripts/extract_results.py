#!/usr/bin/env python3
"""Summarise the two solved runs from their monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/postProcessing/metrics/metrics.csv (scripts/monitor.C's rows, every 0.625 s),
runs/mesh-<run>/cells.npz and patches.json and config/case.json (for the oven's stored heat and
the air's mass at t = 0) and, if they
are there, runs/<run>/log.buoyantPimpleFoam (for the step count and the solver's messages), and
writes

  results/summary.txt         the oven's heat, the kitchen's, the zones' temperatures, the
                              surfaces' heat, the mouth's exchange, the checks
  results/<run>/history.csv   every 2.5 s (the cavity's and the mouth's columns in open only)

All heats, flows and masses are for the half kitchen; double them for the whole. Heat into the
air is positive. The oven's heat still in it is, open, the liner's steel above 20 C less the heat
the liner has given the air (summed at every step) plus the cavity air's heat above 20 C; shut,
the open oven's starting heat less the prescribed 118.5 W times t. The heat the kitchen has gained
is the starting heat less that.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

CASE = Path(__file__).resolve().parents[1]
HEATS = ["liner", "door", "rangeFront", "cooktop", "walls", "ceiling", "floor", "cabinets"]
ZONES = ["mean", "floor", "seated", "head", "ceiling", "farHead", "rangeHead", "cavity"]
COLS = ["time", "dt", "wall_s"]
for z in ["mouth", "mouthUpper", "mouthLower"]:
    COLS += [z + "_" + n for n in ["mplus", "mminus", "qplus", "qminus", "hplus", "hminus"]]
COLS += ["mass", "internal_energy", "Tmin", "Tmin_x", "Tmin_y", "Tmin_z", "Tmax", "Tmax_x", "Tmax_y", "Tmax_z"]
for z in ZONES:
    COLS += [z + "_" + n for n in ["T", "speed", "energy", "mass", "excess_internal_energy"]]
COLS += ["Q_" + n for n in HEATS] + ["I_" + n for n in HEATS] + ["E_" + n for n in ["liner", "walls", "ceiling", "floor"]]
COLS += ["Qraw_" + n for n in HEATS]
COLS += ["Tanymax", "Tanymax_x", "Tanymax_y", "Tanymax_z", "Tanymax_p", "liner_Tmax"]
TIMES = [15, 30, 60, 120, 150, 180, 240, 300]
K = 273.15


def load(runs, run):
    a = np.loadtxt(runs / run / "postProcessing" / "metrics" / "metrics.csv", delimiter=",", ndmin=2)
    if a.shape[1] != len(COLS):
        raise SystemExit(f"{run}: {a.shape[1]} columns in metrics.csv, expected {len(COLS)}")
    return {n: a[:, i] for i, n in enumerate(COLS)}


def at(d, k, t):
    return float(np.interp(t, d["time"], d[k] if isinstance(k, str) else k))


def log_stats(path):
    if not path.is_file():
        return None
    s = path.read_text(errors="replace")
    k = [float(x) for x in re.findall(r"bounding k, min: (\S+)", s)]
    return {"steps": len(re.findall(r"^Time = ", s, re.M)), "k_bounding": len(k), "k_min": min(k) if k else None,
            "p_rgh_cap": len(re.findall(r"p_rgh[^\n]*No Iterations 100\b", s)),
            "end": bool(re.search(r"^End\s*$", s, re.M))}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_results.py runs results")
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads((CASE / "config" / "case.json").read_text())
    lin, T0 = cfg["liner"], cfg["T0"]
    gasR = 8314.46261815324 / cfg["molWeight"]
    cp = 1005.0

    # The oven's heat above 20 C at t = 0, from the open run's starting fields
    cells = np.load(runs / "mesh-open" / "cells.npz")
    C, V = cells["C"], cells["V"]
    b = cfg["cavity"]
    cav = (C[:, 0] < b[3]) & (C[:, 1] > b[1]) & (C[:, 1] < b[4]) & (C[:, 2] < b[5])
    p0 = cfg["pRef"] * np.exp(-9.81 * (C[:, 1] - cfg["yRef"]) / (gasR * T0))
    Tc = np.where(cav, lin["Tinit"], T0)
    steel = lin["mass"] * lin["cp"] * (lin["Tinit"] - T0)
    air = float(np.sum(p0 / (gasR * Tc) * V * (cp - gasR) * (Tc - T0)))
    E0 = steel + air
    area = {}
    for run in ("open", "shut"):
        pj = runs / f"mesh-{run}" / "patches.json"
        area[run] = json.loads(pj.read_text()) if pj.is_file() else {}
    A_liner = area["open"].get("liner", {}).get("area", cfg["expected_areas"]["open"]["liner"])

    D, left, gain, source, check, logs = {}, {}, {}, {}, {}, {}
    for run in ("open", "shut"):
        d = load(runs, run)
        D[run] = d
        if run == "open":
            left[run] = steel - d["I_liner"] + d["cavity_excess_internal_energy"]
            source[run] = d["Q_liner"]
            qsrc = d["I_liner"]
        else:
            left[run] = E0 - cfg["shutQ"] * d["time"]
            source[run] = d["Q_rangeFront"] + d["Q_cooktop"]
            qsrc = d["I_rangeFront"] + d["I_cooktop"]
        gain[run] = E0 - left[run]
        isum = sum(d["I_" + p] for p in HEATS)
        e10, i10, s10 = (at(d, k, 10) for k in ("internal_energy", isum, qsrc))
        closure = (d["internal_energy"][-1] - e10 - (isum[-1] - i10)) / abs(qsrc[-1] - s10) * 100
        cr = np.load(runs / f"mesh-{run}" / "cells.npz")
        Cr, Vr = cr["C"], cr["V"]
        Tr = np.full(len(Cr), T0)
        if run == "open":
            Tr[(Cr[:, 0] < b[3]) & (Cr[:, 1] > b[1]) & (Cr[:, 1] < b[4]) & (Cr[:, 2] < b[5])] = lin["Tinit"]
        m0 = float(np.sum(cfg["pRef"] * np.exp(-9.81 * (Cr[:, 1] - cfg["yRef"]) / (gasR * T0)) / (gasR * Tr) * Vr))
        check[run] = {"closure": closure, "m0": m0, "drift0": float(np.max(np.abs(d["mass"] / m0 - 1))),
                      "drift": float(np.max(np.abs(d["mass"] / d["mass"][0] - 1))),
                      "mass": float(d["mass"][0]), "end": float(d["time"][-1])}
        logs[run] = log_stats(runs / run / "log.buoyantPimpleFoam")

    o, s = D["open"], D["shut"]
    L = []
    w = L.append
    w("Subject: an electric oven just switched off after roasting at 325 F, its door dropped open or kept shut,")
    w("in a sealed kitchen at 20 C; a 3-D half kitchen on the range's centreline, 0-300 s from switch-off.")
    w("Every heat, flow and mass is for the half kitchen; double it for the whole.")
    w("")
    w(f"The oven's heat above 20 C at switch-off (both runs): {E0 / 1e3:.3f} kJ")
    w(f"  steel, {lin['mass']} kg at {lin['Tinit'] - K:.2f} C             {steel / 1e3:10.3f} kJ")
    w(f"  the cavity's air                         {air / 1e3:10.3f} kJ")
    w("")
    w("   t s   heat still in the oven, %   heat the kitchen has gained, kJ")
    w("           open     shut             open      shut   open - shut")
    for t in [0] + TIMES:
        lo = 100.0 if t == 0 else at(o, left["open"], t) / E0 * 100
        ls = 100.0 if t == 0 else at(s, left["shut"], t) / E0 * 100
        go = 0.0 if t == 0 else at(o, gain["open"], t) / 1e3
        gs = 0.0 if t == 0 else at(s, gain["shut"], t) / 1e3
        w(f"  {t:4d}   {lo:7.3f}  {ls:7.3f}         {go:8.3f}  {gs:8.3f}  {go - gs:+8.3f}")
    w("")
    w("Air temperature, C, volume means outside the cavity: the whole kitchen, the floor layer (y < 0.1 m),")
    w("the seated zone (0.1-1.1 m), standing head height (1.5-1.8 m), the ceiling layer (y > 2.2 m), a cook's")
    w("head in front of the range (x < 0.3, y 1.5-1.8, z 1.0-1.4 m) and a head across the kitchen (z 2.0-2.4 m)")
    names = [("mean", "kitchen"), ("floor", "floor"), ("seated", "seated"), ("head", "head"),
             ("ceiling", "ceiling"), ("rangeHead", "cook"), ("farHead", "across")]
    w("   t s  " + "".join(f"{n:>16s}" for _, n in names))
    w("        " + "".join(f"{'open   shut':>16s}" for _ in names))
    for t in TIMES:
        w(f"  {t:4d}  " + "".join(f"   {at(o, z + '_T', t) - K:6.2f} {at(s, z + '_T', t) - K:6.2f}" for z, _ in names))
    w(f"  open less shut at standing head height, K: " + ", ".join(
        f"{at(o, 'head_T', t) - at(s, 'head_T', t):+.3f} at {t} s" for t in (60, 150, 300)))
    w("")
    w("Heat into the air, W (negative: out of the air into the surface)")
    w("   t s        oven              walls            ceiling             floor")
    w("           open     shut      open    shut      open    shut      open    shut")
    for t in TIMES:
        w(f"  {t:4d}  {at(o, source['open'], t):7.2f}  {at(s, source['shut'], t):7.2f}  "
          + "  ".join(f"{at(o, 'Q_' + p, t):7.2f} {at(s, 'Q_' + p, t):7.2f}" for p in ("walls", "ceiling", "floor")))
    q2030 = (at(o, "I_liner", 30) - at(o, "I_liner", 20)) / 10
    Tsteel = T0 + np.interp(25, o["time"], o["E_liner"]) / (lin["mass"] * lin["cp"])
    h = q2030 / (A_liner * (Tsteel - at(o, "cavity_T", 25)))
    w(f"  open: the liner's mean over 20-30 s {q2030:.2f} W; at 25 s the steel at {Tsteel - K:.2f} C and the cavity's air at "
      f"{at(o, 'cavity_T', 25) - K:.2f} C, so {h:.2f} W/m2K over the liner's {A_liner:.4f} m2")
    w(f"  shut: the front {at(s, 'Q_rangeFront', 150):.3f} W and the cooktop {at(s, 'Q_cooktop', 150):.3f} W, "
      f"{at(s, source['shut'], 150):.4f} W in all at 150 s")
    w("")
    w("Where the oven's heat is at 300 s, kJ                 open      shut")
    for lab, fn in [("given to the kitchen", lambda d, r: at(d, gain[r], 300)),
                    ("  in the walls' layers", lambda d, r: at(d, "E_walls", 300)),
                    ("  in the ceiling's layers", lambda d, r: at(d, "E_ceiling", 300)),
                    ("  in the floor's layers", lambda d, r: at(d, "E_floor", 300)),
                    ("  in the air outside the cavity", lambda d, r: at(d, gain[r], 300) - sum(at(d, "E_" + p, 300) for p in ("walls", "ceiling", "floor")))]:
        w(f"  {lab:44s} {fn(o, 'open') / 1e3:8.3f}  {fn(s, 'shut') / 1e3:8.3f}")
    w(f"  (the air's share is the remainder; the cavity's own air is counted with the oven)")
    w("")
    w("The open oven's mouth (x < 0.30, y 0.24-0.72 m at z = 0.64 m), gross flows, L/s, and heat carried out, W")
    w("   t s   out, upper half   in, upper half   in, lower half   out, lower half   heat out   cavity C   out / Cd 0.6 opening flow")
    for t in TIMES:
        Tcav = at(o, "cavity_T", t)
        g = 9.81 * max(0.0, 1 - T0 / Tcav)
        Qcd = 0.6 / 3 * 0.30 * 0.48 * np.sqrt(g * 0.48)
        w(f"  {t:4d}   {at(o, 'mouthUpper_qplus', t) * 1e3:14.2f}   {at(o, 'mouthUpper_qminus', t) * 1e3:14.2f}   "
          f"{at(o, 'mouthLower_qminus', t) * 1e3:14.2f}   {at(o, 'mouthLower_qplus', t) * 1e3:15.2f}   {at(o, 'mouth_hplus', t):8.1f}"
          f"   {Tcav - K:8.2f}   {at(o, 'mouth_qplus', t) / Qcd:6.3f}")
    w("")
    w("Checks                                                   open          shut")
    w(f"  end of the monitor, s                              {check['open']['end']:10.3f}    {check['shut']['end']:10.3f}")
    w(f"  heat budget 10 s to the end, % of the oven's heat  {check['open']['closure']:+10.4f}    {check['shut']['closure']:+10.4f}")
    w("    (the change of the air's (cv/R) int p dV against the heat through every surface, each summed at every step)")
    w(f"  air's mass in the t = 0 fields, kg                 {check['open']['m0']:10.6f}    {check['shut']['m0']:10.6f}")
    w(f"  air's mass at the first row, kg                    {check['open']['mass']:10.6f}    {check['shut']['mass']:10.6f}")
    w(f"  largest change of the air's mass from t = 0        {check['open']['drift0']:10.2e}    {check['shut']['drift0']:10.2e}")
    w(f"  largest change of the air's mass from the first row {check['open']['drift']:9.2e}    {check['shut']['drift']:10.2e}")
    disc = steel - o["E_liner"][-1] - o["I_liner"][-1]
    w(f"  open: the steel's heat lost less the liner's heat given, at the end, J   {disc:+.3f}")
    for r, d in (("open", o), ("shut", s)):
        i, j = int(np.argmin(d["Tmin"])), int(np.argmax(d["Tanymax"]))
        w(f"  {r}: coldest air {d['Tmin'][i] - K:.3f} C at {d['time'][i]:g} s, ({d['Tmin_x'][i]:.2f}, {d['Tmin_y'][i]:.2f}, "
          f"{d['Tmin_z'][i]:.2f}) m; warmest {d['Tanymax'][j]:.6f} K at {d['time'][j]:g} s, ({d['Tanymax_x'][j]:.2f}, "
          f"{d['Tanymax_y'][j]:.2f}, {d['Tanymax_z'][j]:.2f}) m")
        w(f"        time step {d['dt'].min() * 1e3:.2f}-{d['dt'].max() * 1e3:.2f} ms at the rows, {d['dt'][-1] * 1e3:.2f} ms at the end")
    w(f"  open: the liner's surface, hottest {o['liner_Tmax'].max():.6f} K (starts at {lin['Tinit']} K)")
    for r in ("open", "shut"):
        g = logs[r]
        if g:
            w(f"  {r}: log: {g['steps']} steps, 'End' {'found' if g['end'] else 'MISSING'}, k bounded {g['k_bounding']} times"
              + (f" (lowest {g['k_min']:.3g} m2/s2)" if g["k_min"] is not None else "")
              + f", final p_rgh solve at its 100-iteration cap {g['p_rgh_cap']} times")
    (out).mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text("\n".join(L) + "\n")

    for run, d in D.items():
        (out / run).mkdir(exist_ok=True)
        hdr = ["t_s", "oven_left_pct", "kitchen_gain_kJ", "oven_W", "walls_W", "ceiling_W", "floor_W", "layers_kJ",
               "mean_C", "floor_C", "seated_C", "head_C", "ceiling_C", "rangeHead_C", "farHead_C", "cavity_C",
               "mouth_out_L_s", "mouth_in_L_s", "mouth_heat_out_W", "dt_ms"]
        rows = [",".join(n for n in hdr if run == "open" or not n.startswith(("cavity", "mouth")))]
        for t in np.arange(2.5, check[run]["end"] + 1e-9, 2.5):
            layers = sum(at(d, "E_" + p, t) for p in ("walls", "ceiling", "floor"))
            v = [t, at(d, left[run], t) / E0 * 100, at(d, gain[run], t) / 1e3, at(d, source[run], t)]
            v += [at(d, "Q_" + p, t) for p in ("walls", "ceiling", "floor")] + [layers / 1e3]
            v += [at(d, z + "_T", t) - K for z in ("mean", "floor", "seated", "head", "ceiling", "rangeHead", "farHead", "cavity")]
            v += [at(d, "mouth_qplus", t) * 1e3, at(d, "mouth_qminus", t) * 1e3, at(d, "mouth_hplus", t), at(d, "dt", t) * 1e3]
            fmt = ["{:g}", "{:.4f}", "{:.4f}", "{:.3f}", "{:.3f}", "{:.3f}", "{:.3f}", "{:.4f}"] + ["{:.4f}"] * 8 + ["{:.3f}"] * 3 + ["{:.4f}"]
            keep = [i for i, n in enumerate(hdr) if run == "open" or not n.startswith(("cavity", "mouth"))]
            rows.append(",".join(fmt[i].format(v[i]) for i in keep))
        (out / run / "history.csv").write_text("\n".join(rows) + "\n")
    print((out / "summary.txt").read_text())


if __name__ == "__main__":
    main()
