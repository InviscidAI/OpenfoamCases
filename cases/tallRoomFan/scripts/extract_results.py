"""Write results/ from the solved runs' monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

Reads, for nofan, fan_ceiling and (if it has run) fan_radiator, each run's
postProcessing/heatAccounting/heat.csv (every step: the panel's convection and radiation,
the convector zone's enthalpy flux, diffusion, internal and kinetic energy, every wall's heat,
the air's mass and internal energy), postProcessing/diagnostics66/diagnostics.csv (every
step: the four line means, the room's air, the fans' gross flows, every wall layer's stored
heat), postProcessing/convectorT/0/volFieldValue.dat (every step: the integral of T over the
convector zone), postProcessing/convectorAir/air.csv and log.buoyantPimpleFoam. With runs/bare
it adds the convector's check against the catalogue.

The radiator's heat is the panel's convection and radiation plus the fins' heat to the
convector's air, hv (328.15 V - integral of T dV) with V = 0.0378 m3 per metre, hv from
config/caseSettings. The convector air's own energy balance (enthalpy out of the zone,
diffusion, the rise of its internal and kinetic energy) is the check on it.

Writes results/<run>/history.csv (2.5 s windows), results/minutes.csv and results/summary.txt.
"""
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
sys.path.insert(0, str(HERE))
from make_case import initial_integrals  # noqa: E402

TAMB = 289.15
VZONE = .0378
WALLS = ["floor", "ceiling", "innerWall", "outerWall"]
FANS = {"fan_radiator": "rad", "fan_ceiling": "ceil"}
LABEL = {"nofan": "no fan", "fan_ceiling": "fan aimed at the ceiling", "fan_radiator": "fan aimed at the radiator"}
HV = float(re.search(r"^hv\s+([^;]+);", (CASE / "config/caseSettings").read_text(), re.M)[1])


def table(path):
    d = np.atleast_1d(np.genfromtxt(path, delimiter=",", names=True))
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def weights(t, a, b):
    """Each step's share of [a, b]: a value written at t stands for (previous t, t]."""
    prev = np.r_[0, t[:-1]]
    w = np.maximum(0, np.minimum(t, b) - np.maximum(prev, a))
    assert abs(w.sum() - (b - a)) < 1e-6, (a, b, w.sum())
    return w


def wmean(t, q, a, b):
    return float(np.average(q, weights=weights(t, a, b)))


def cum(t, q):
    return np.cumsum(np.diff(np.r_[0, t]) * q)


def at(t, q, s):
    return float(np.interp(s, t, q))


def load(run_dir, ini):
    h = table(run_dir / "postProcessing/heatAccounting/heat.csv")
    g = table(run_dir / "postProcessing/diagnostics66/diagnostics.csv")
    ct = np.atleast_2d(np.loadtxt(next((run_dir / "postProcessing/convectorT").glob("*/volFieldValue.dat"))))
    ct = ct[np.r_[True, np.diff(ct[:, 0]) > 0]]
    air = table(run_dir / "postProcessing/convectorAir/air.csv")
    t = h["time"]
    dt = np.diff(np.r_[0, t])
    # the convector air's energy balance: enthalpy out, diffusion, rise of Cv-internal energy
    # referenced to Cp Tamb and of kinetic energy, from the hydrostatic start
    z = h["Uzone"] - 1005 * TAMB * h["zoneMass"]
    z0 = ini["zoneU"] - 1005 * TAMB * ini["zoneMass"]
    balance = h["zoneEnthalpy"] + h["zoneDiffusion"] + np.diff(np.r_[z0, z]) / dt + np.diff(np.r_[0, h["KEzone"]]) / dt
    src = np.interp(t, ct[:, 0], HV * (328.15 * VZONE - ct[:, 1]))
    r = dict(t=t, panelC=h["panelConvection"], panelR=h["panelRadiation"], conv=src, balance=balance,
             out=h["panelConvection"] + h["panelRadiation"] + src,
             outBalance=h["panelConvection"] + h["panelRadiation"] + balance,
             glass=-(h["glassConv"] + h["glassRad"]), Uroom=h["Uroom"], mass=h["mass"], massT=h["massT"],
             g=g, air=air, wallsHeat={w: -(h[w + "Conv"] + h[w + "Rad"]) for w in WALLS})
    steps, wall, caps, capres = 0, 0., 0, []
    log = run_dir / "log.buoyantPimpleFoam"
    if log.exists():
        with log.open() as f:
            for line in f:
                if line.startswith("Time = "):
                    steps += 1
                elif line.startswith("ExecutionTime"):
                    wall = float(re.search(r"ClockTime = ([\d.eE+-]+)", line)[1])
                elif "Solving for p_rgh" in line and "No Iterations 100" in line:
                    caps += 1
                    capres.append(float(re.search(r"Final residual = ([^,]+),", line)[1]))
    r.update(steps=steps, wall=wall, caps=caps, capres=capres)
    return r


def history(r, out_dir, fan):
    g, t, tg = r["g"], r["t"], r["g"]["time"]
    a = r["air"]
    rows = []
    cols = ["start_s", "end_s", "panel_convection_W", "panel_radiation_W", "convector_W", "output_W",
            "output_energy_balance_W", "output_since_0_kJ", "glass_W", "line010_C", "line110_C", "line150_C",
            "line320_C", "room_C", "below18_C", "above18_C", "convector_air_C", "fan_out_Ls", "fan_in_Ls",
            "up_150_Ls", "down_150_Ls"]
    co = cum(t, r["out"])
    for s in np.arange(0, 300, 2.5):
        e = s + 2.5
        m = lambda q: wmean(t, q, s, e)  # noqa: E731
        mg = lambda q: wmean(tg, q, s, e)  # noqa: E731
        row = [s, e, m(r["panelC"]), m(r["panelR"]), m(r["conv"]), m(r["out"]), m(r["outBalance"]),
               at(t, co, e) / 1000, m(r["glass"])]
        row += [at(tg, g[k], e) - 273.15 for k in ["line010_K", "line110_K", "line150_K", "line320_K", "roomT_K", "belowT_K", "aboveT_K"]]
        row += [wmean(a["time"], a["massT_kgK"] / a["mass_kg"], s, e) - 273.15]
        row += [1000 * mg(g[fan + "OutPositive"]), 1000 * mg(g[fan + "InPositive"])] if fan else ["", ""]
        row += [1000 * mg(g["up_m3s"]), 1000 * mg(g["down_m3s"])]
        rows.append(row)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = lambda v: v if isinstance(v, str) else f"{v:.3f}" if abs(v) < 1e4 else f"{v:.1f}"  # noqa: E731
    (out_dir / "history.csv").write_text(",".join(cols) + "\n" + "".join(",".join(fmt(v) for v in row) + "\n" for row in rows))


def budget(r, ini):
    t, g = r["t"], r["g"]
    tg = g["time"]
    stored = sum(g[w + "Storage_J"] for w in WALLS)
    d = lambda tt, q: at(tt, q, 300) - at(tt, q, 10)  # noqa: E731
    inp = d(t, cum(t, r["outBalance"]))
    air = d(t, r["Uroom"])
    lay = d(tg, stored)
    gl = d(t, cum(t, r["glass"]))
    layer_err = {w: (d(tg, g[w + "Storage_J"]) - d(t, cum(t, r["wallsHeat"][w]))) / d(t, cum(t, r["wallsHeat"][w])) for w in WALLS}
    return inp, air, lay, gl, inp - air - lay - gl, layer_err, float(np.max(np.abs(r["mass"] / ini["mass"] - 1)))


def main():
    runs, res = Path(sys.argv[1]), Path(sys.argv[2])
    ini = initial_integrals()
    R = {n: load(runs / n, ini) for n in ["nofan", "fan_ceiling"]}
    for n in R:
        assert R[n]["t"][-1] >= 300 - 1e-6, f"{n} has not reached 300 s"
    if (runs / "fan_radiator/postProcessing/heatAccounting/heat.csv").exists():
        r = load(runs / "fan_radiator", ini)
        if r["t"][-1] >= 300 - 1e-6:  # left out until it has solved
            R["fan_radiator"] = r
    names = list(R)
    for n in names:
        history(R[n], res / n, FANS.get(n))
    L = []
    w = L.append
    w("tallRoomFan: figures from the runs' monitors (scripts/extract_results.py)")
    w("A 2-D section of a 5.0 x 3.3 m Altbau room, radiatorCover's radiator with its fin-gap convector")
    w("under a box window, 0-300 s from switch-on at 16 C, 0 C outside, W and J per metre of section")
    w(f"hv {HV} W/m3K (config/caseSettings)")
    w("")
    for n in names:
        r = R[n]
        cap = f", {r['caps']} pressure solves at 100 iterations (final residual {min(r['capres']):.2e} to {max(r['capres']):.2e})" if r["caps"] else ""
        w(f"{n}: monitored to t = {r['t'][-1]:g} s, {r['steps']} steps, {r['wall']:.0f} s of wall time{cap}")
    w("")
    w("The radiator's heat, mean W/m: the panel's convection and radiation and the fins' heat to the")
    w("convector's air, hv (55 C - T) over the zone; against no fan in the same window")
    w("  window s    run                          panel conv  panel rad  convector    total   / no fan")
    wins = [(0, 60), (60, 120), (120, 180), (180, 240), (240, 300), (0, 300)]
    for a, b in wins:
        base = wmean(R["nofan"]["t"], R["nofan"]["out"], a, b)
        for n in names:
            r = R[n]
            m = [wmean(r["t"], r[k], a, b) for k in ["panelC", "panelR", "conv", "out"]]
            w(f"  {a:3d}-{b:3d}    {LABEL[n]:<28s} {m[0]:9.1f} {m[1]:10.1f} {m[2]:10.1f} {m[3]:9.1f}   {100 * m[3] / base:6.1f}%")
    w("")
    w("Gain over no fan, 240-300 s: " + ", ".join(
        f"{LABEL[n]} {100 * (wmean(R[n]['t'], R[n]['out'], 240, 300) / wmean(R['nofan']['t'], R['nofan']['out'], 240, 300) - 1):+.2f}%"
        f" (by the convector air's own balance {100 * (wmean(R[n]['t'], R[n]['outBalance'], 240, 300) / wmean(R['nofan']['t'], R['nofan']['outBalance'], 240, 300) - 1):+.2f}%)"
        for n in names[1:]))
    if "fan_radiator" in R:
        f, o = R["fan_radiator"], R["nofan"]
        dd = [wmean(f["t"], f[k], 240, 300) - wmean(o["t"], o[k], 240, 300) for k in ["panelC", "conv", "panelR"]]
        w(f"  fan aimed at the radiator, 240-300 s, against no fan: panel convection {dd[0]:+.1f} W/m, convector {dd[1]:+.1f}, panel radiation {dd[2]:+.1f}")
    w("From switch-on to 300 s, kJ/m: " + ", ".join(f"{n} {cum(R[n]['t'], R[n]['out'])[-1] / 1000:.2f}" for n in names))
    w("The fins' heat against the convector air's own balance, every window above after 10 s: largest difference "
      + f"{max(abs(wmean(R[n]['t'], R[n]['balance'], a, b) / wmean(R[n]['t'], R[n]['conv'], a, b) - 1) for n in names for a, b in wins[1:] + [(10, 300)]) * 100:.3f}%")
    w("")
    w("The air, C: the mean along a line across the room (x = 0.5-4.5 m) at each height, and the room's")
    w("air mass-weighted without the convector's cells; instantaneous")
    w("     t   run                            0.1 m    1.1 m    1.5 m    3.2 m     room")
    for s in [10, 30, 60, 120, 180, 240, 300]:
        for n in names:
            g = R[n]["g"]
            v = [at(g["time"], g[k], s) - 273.15 for k in ["line010_K", "line110_K", "line150_K", "line320_K", "roomT_K"]]
            w(f"  {s:4d}   {LABEL[n]:<28s} " + " ".join(f"{x:8.2f}" for x in v))
    w("")
    for n in names[1:]:
        g, g0 = R[n]["g"], R["nofan"]["g"]
        v = [at(g["time"], g[k], 300) - at(g0["time"], g0[k], 300) for k in ["line010_K", "line110_K", "line150_K", "line320_K", "roomT_K"]]
        w(f"At 300 s, {LABEL[n]} minus no fan, K: 0.1 m {v[0]:+.2f}, 1.1 m {v[1]:+.2f}, 1.5 m {v[2]:+.2f}, 3.2 m {v[3]:+.2f}, room {v[4]:+.2f}")
        tt = g0["time"]
        diff = np.interp(tt, g["time"], g["line010_K"]) - g0["line010_K"]
        w(f"  0.1 m line, {LABEL[n]} minus no fan over every no-fan step: lowest {diff.min():+.3f} K at {tt[np.argmin(diff)]:.2f} s")
        w(f"  1.5 m line, mean over 240-300 s: {wmean(g['time'], g['line150_K'], 240, 300) - 273.15:.2f} C against {wmean(tt, g0['line150_K'], 240, 300) - 273.15:.2f} C;"
          f" room {wmean(g['time'], g['roomT_K'], 240, 300) - 273.15:.2f} against {wmean(tt, g0['roomT_K'], 240, 300) - 273.15:.2f} C")
    w("")
    w("The fans' air through the zone's outlet and inlet faces, gross, l/s per metre (target at the outlet 226)")
    for n in names[1:]:
        g, p = R[n]["g"], FANS[n]
        for a, b in [(4, 10), (240, 300)]:
            w(f"  {LABEL[n]:<28s} {a:3d}-{b:3d} s  out {1000 * wmean(g['time'], g[p + 'OutPositive'], a, b):6.1f}  in {1000 * wmean(g['time'], g[p + 'InPositive'], a, b):6.1f}")
    w("The convector's air, 240-300 s: mass-weighted mean C, gross upward flow in at its bottom and out at its top, g/s per metre")
    for n in names:
        a = R[n]["air"]
        w(f"  {LABEL[n]:<28s} {wmean(a['time'], a['massT_kgK'] / a['mass_kg'], 240, 300) - 273.15:6.1f}"
          f"  {1000 * wmean(a['time'], a['bottom_up_kgs'], 240, 300):6.2f}  {1000 * wmean(a['time'], a['top_up_kgs'], 240, 300):6.2f}")
    w("")
    w("Heat budget over 10-300 s, kJ/m: the radiator's heat (by the convector air's balance) = rise of the")
    w("air's internal energy, (cv/R) integral p dV, + heat stored in the wall layers + heat out through the glass")
    w("                                 radiator      air   layers    glass   residual")
    for n in names:
        inp, air, lay, gl, res_, lerr, drift = budget(R[n], ini)
        w(f"  {LABEL[n]:<28s} {inp / 1e3:9.3f} {air / 1e3:8.3f} {lay / 1e3:8.3f} {gl / 1e3:8.3f} {res_ / 1e3:9.3f} ({100 * res_ / inp:+.3f}%)")
        w(f"      each layer's stored heat against its wall heat flux: " + ", ".join(f"{k} {100 * v:+.3f}%" for k, v in lerr.items())
          + f"; the air's mass within {drift:.1e} of the start")
    bare = runs / "bare"
    if (bare / "postProcessing/heatAccounting/heat.csv").exists():
        r = load(bare, ini)
        tm = wmean(r["t"], r["massT"] / r["mass"], 25, 40)
        q, qb = wmean(r["t"], r["out"], 25, 40), wmean(r["t"], r["outBalance"], 25, 40)
        rating = 980 * ((328.15 - tm) / 50) ** 1.3
        w("")
        w(f"bare, the convector's check, 25-40 s: {q:.1f} W/m ({qb:.1f} by the air's balance) against the catalogue's {rating:.1f} W/m"
          f" at the room's mean air temperature then, {tm - 273.15:.3f} C (980 W x ((55 - T)/50)^1.3): {q / rating:.3f}")
    (res / "summary.txt").write_text("\n".join(L) + "\n")

    rows = ["start_s,end_s," + ",".join(f"{n}_output_W" for n in names) + "," + ",".join(f"{n}_over_nofan" for n in names[1:])
            + "," + ",".join(f"{n}_since_0_kJ" for n in names)]
    for a, b in wins[:5]:
        m = {n: wmean(R[n]["t"], R[n]["out"], a, b) for n in names}
        c = {n: at(R[n]["t"], cum(R[n]["t"], R[n]["out"]), b) / 1000 for n in names}
        rows.append(f"{a},{b}," + ",".join(f"{m[n]:.2f}" for n in names) + "," + ",".join(f"{m[n] / m['nofan']:.4f}" for n in names[1:])
                    + "," + ",".join(f"{c[n]:.3f}" for n in names))
    (res / "minutes.csv").write_text("\n".join(rows) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
