"""Write results/ from the solved runs' monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir> [--earlier RUN DIR ...]

Reads, for bare and fan, each run's postProcessing/heatAccounting/heat.csv (every step: the
panels' convection and radiation, the fin zone's enthalpy flux, diffusion, internal and kinetic
energy, every wall's heat, the air's mass and internal energy),
postProcessing/diagnostics67/diagnostics.csv (every step: the gross flows through the fan's and
the fins' faces, every wall layer's stored heat, the glass's temperature, the line means across
the room) and postProcessing/convT/<t>/volFieldValue.dat (every step: the integral of T over the
fin zone).

A run solved in pieces has more than one postProcessing tree, because the coded monitors start
their files again on a restart. --earlier RUN DIR names an earlier piece's tree; it is used up to
the time at which the later tree's newest convT folder starts (the restart time) and the later
tree after it. The solved bare run of this case was continued from 60 s, so its results were
written with --earlier bare <its 0-60 s tree>. A run from Allrun is one piece and needs none.

The radiator's heat is the panels' convection and radiation plus the fins' heat to the fin zone's
air, hv (328.15 V - integral of T dV), with V the zone's volume (0.0384 m3 per metre) and hv from
the run's constant/convectorSettings. The fin zone air's own energy balance is the check on it.

Writes results/<run>/history.csv (2.5 s windows), results/minutes.csv and results/summary.txt.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_case import initial_integrals  # noqa: E402

TAMB = 289.15
RUNS = ["bare", "fan"]
LABEL = {"bare": "bare radiator", "fan": "with the fan bar"}
WALLS = ["floor", "ceiling", "innerWall", "outerWall"]


def table(path):
    d = np.atleast_1d(np.genfromtxt(path, delimiter=",", names=True))
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def dat(path):
    rows = [l.split() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]
    return np.array([[float(a), float(b)] for a, b in (r[:2] for r in rows if len(r) == 2)])


def joined(trees, rel):
    """One monitor's rows from a run's postProcessing trees, each tree from its start to the next's."""
    starts = [restart(tr) for tr in trees] + [np.inf]
    parts = []
    for k, tr in enumerate(trees):
        d = table(tr / rel)
        lo = starts[k] if k else -np.inf
        parts.append(d[(d["time"] > lo) & (d["time"] <= starts[k + 1])])
    return np.concatenate(parts)


def restart(tree):
    return max(float(f.name) for f in (tree / "convT").iterdir() if f.is_dir())


def convT(trees):
    """convT's rows: each time folder from its start to the next folder's, the later tree winning."""
    folders = {}
    for tr in trees:
        for f in (tr / "convT").iterdir():
            folders[float(f.name)] = f / "volFieldValue.dat"
    keys = sorted(folders) + [np.inf]
    parts = []
    for a, b in zip(keys[:-1], keys[1:]):
        q = dat(folders[a])
        parts.append(q[(q[:, 0] > (a if a > 0 else -1)) & (q[:, 0] <= b)])
    q = np.concatenate(parts)
    return q[np.r_[True, np.diff(q[:, 0]) > 0]]


def weights(t, a, b):
    """Each step's share of [a, b]: a value written at t stands for (previous t, t]."""
    prev = np.r_[0, t[:-1]]
    w = np.maximum(0, np.minimum(t, b) - np.maximum(prev, a))
    assert abs(w.sum() - (b - a)) < 1e-6, (a, b, w.sum())
    return w


def wmean(t, q, a, b):
    return float(np.average(q, weights=weights(t, a, b)))


def integral(t, q, a, b):
    return float(np.sum(weights(t, a, b) * q))


def at(t, q, s):
    return float(np.interp(s, t, q))


def load(run, run_dir, earlier):
    trees = ([Path(earlier)] if earlier else []) + [run_dir / "postProcessing"]
    hv = float(re.search(r"^hv\s+([^;]+);", (run_dir / "constant/convectorSettings").read_text(), re.M)[1])
    ini = initial_integrals(run)
    h = joined(trees, "heatAccounting/heat.csv")
    g = joined(trees, "diagnostics67/diagnostics.csv")
    ct = convT(trees)
    t = h["time"]
    dt = np.diff(np.r_[0, t])
    src = hv * (328.15 * ini["zoneVolume"] - np.interp(t, ct[:, 0], ct[:, 1]))
    # the fin zone air's energy balance: enthalpy out, diffusion, the rise of its Cv-internal
    # energy referenced to Cp Tamb and of its kinetic energy, from the hydrostatic start
    z = h["Uzone"] - 1005 * TAMB * h["zoneMass"]
    z0 = ini["zoneEnergy"] - 1005 * TAMB * ini["zoneMass"]
    balance = h["zoneEnthalpy"] + h["zoneDiffusion"] + np.diff(np.r_[z0, z]) / dt + np.diff(np.r_[0, h["KEzone"]]) / dt
    r = dict(t=t, hv=hv, ini=ini, trees=trees, steps=len(t),
             panelC=h["panelConvection"], panelR=h["panelRadiation"], fins=src, balance=balance,
             out=h["panelConvection"] + h["panelRadiation"] + src,
             glass=-(h["glassConv"] + h["glassRad"]), bar=-(h["fanBarConv"] + h["fanBarRad"]),
             room=h["massT"] / h["mass"] - 273.15, U=h["Uroom"], mass=h["mass"])
    for k in ["fanOutPlus", "fanOutMinus", "convInPlus", "convOutPlus", "glassT", "glassLowerT", "glassUpperT",
              "lineLowT", "lineDeskT", "lineHighT", "farT", "coldestT", "hottestT"] + [w + "Stored" for w in WALLS]:
        r[k] = np.interp(t, g["time"], g[k])
    r["stored"] = sum(r[w + "Stored"] for w in WALLS)
    if earlier:
        c = restart(trees[-1])
        k = int(np.searchsorted(t, c, side="right"))
        r["join"] = (c, t[k - 1], t[k], r["room"][k - 1], r["room"][k], r["out"][k - 1], r["out"][k],
                     r["fins"][k - 1], r["fins"][k])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs")
    ap.add_argument("results")
    ap.add_argument("--earlier", nargs=2, action="append", default=[], metavar=("RUN", "DIR"))
    a = ap.parse_args()
    earlier = dict(a.earlier)
    runs, res = Path(a.runs), Path(a.results)
    d = {r: load(r, runs / r, earlier.get(r)) for r in RUNS}
    for r in RUNS:
        assert d[r]["t"][-1] >= 300 - 1e-6, f"{r} has not reached 300 s"

    # ---- histories, 2.5 s windows ---------------------------------------------------------
    for r in RUNS:
        q = d[r]
        t = q["t"]
        (res / r).mkdir(parents=True, exist_ok=True)
        lines = ["start_s,end_s,panel_convection_W,panel_radiation_W,fins_W,output_W,fins_energy_balance_W,"
                 "output_since_0_kJ,glass_W,glass_since_0_kJ,glass_C,glass_lower_C,glass_upper_C,"
                 "line010_C,line110_C,line260_C,beyond0424_C,room_C,fan_out_Ls,fins_in_Ls,fins_out_Ls"]
        for k in range(120):
            lo, hi = 2.5 * k, 2.5 * (k + 1)
            m = lambda key: wmean(t, q[key], lo, hi)
            lines.append(",".join(f"{v:.3f}" for v in [
                lo, hi, m("panelC"), m("panelR"), m("fins"), m("out"), m("balance"),
                integral(t, q["out"], 0, hi) / 1e3, m("glass"), integral(t, q["glass"], 0, hi) / 1e3,
                at(t, q["glassT"], hi) - 273.15, at(t, q["glassLowerT"], hi) - 273.15, at(t, q["glassUpperT"], hi) - 273.15,
                at(t, q["lineLowT"], hi) - 273.15, at(t, q["lineDeskT"], hi) - 273.15, at(t, q["lineHighT"], hi) - 273.15,
                at(t, q["farT"], hi) - 273.15, at(t, q["room"], hi),
                1e3 * m("fanOutPlus"), 1e3 * m("convInPlus"), 1e3 * m("convOutPlus")]))
        (res / r / "history.csv").write_text("\n".join(lines) + "\n")

    # ---- minutes -----------------------------------------------------------------------------
    b, f = d["bare"], d["fan"]
    W = [(0, 60), (60, 120), (120, 180), (180, 240), (240, 300), (0, 120), (0, 300)]
    lines = ["start_s,end_s,bare_output_W,fan_output_W,fan_over_bare,bare_glass_W,fan_glass_W,fan_glass_over_bare,"
             "bare_fins_in_Ls,fan_fins_in_Ls,fan_out_Ls"]
    for lo, hi in W:
        ob, of = wmean(b["t"], b["out"], lo, hi), wmean(f["t"], f["out"], lo, hi)
        gb, gf = wmean(b["t"], b["glass"], lo, hi), wmean(f["t"], f["glass"], lo, hi)
        lines.append(f"{lo},{hi},{ob:.2f},{of:.2f},{of / ob:.4f},{gb:.2f},{gf:.2f},{gf / gb:.4f},"
                     f"{1e3 * wmean(b['t'], b['convInPlus'], lo, hi):.3f},{1e3 * wmean(f['t'], f['convInPlus'], lo, hi):.3f},"
                     f"{1e3 * wmean(f['t'], f['fanOutPlus'], lo, hi):.3f}")
    (res / "minutes.csv").write_text("\n".join(lines) + "\n")

    # ---- summary -----------------------------------------------------------------------------
    S = ["radiatorFanBar: figures from the runs' monitors (scripts/extract_results.py)",
         "A 2-D section of a 3.4 x 2.7 m study, a Stelrad Compact K2 600 mm double panel at 55 C under a",
         "tall window, bare and with a fan bar on its top, 0-300 s from switch-on at 16 C, 0 C outside,",
         "W and J per metre of section",
         f"hv {b['hv']:g} W/m3K, fin zone {b['ini']['zoneVolume']:.4f} m3 (constant/convectorSettings, the mesh)", ""]
    for r in RUNS:
        q = d[r]
        pieces = " + ".join(str(p) for p in q["trees"]) if len(q["trees"]) > 1 else "one piece"
        S.append(f"{r}: monitored to t = {q['t'][-1]:g} s, {q['steps']} steps; monitors from {pieces}")
        if "join" in q:
            c, t0, t1, r0, r1, o0, o1, f0, f1 = q["join"]
            S.append(f"  joined at {c:g} s: rows at {t0:.6f} and {t1:.6f} s; room {r0:.4f} -> {r1:.4f} C, "
                     f"radiator {o0:.2f} -> {o1:.2f} W/m, fins {f0:.3f} -> {f1:.3f} W/m")
    S += ["", "The radiator's heat, mean W/m: the panels' convection and radiation and the fins' heat to the",
          "fin zone's air; the fan run against the bare one in the same window",
          "  window s    run                  panel conv  panel rad     fins    total   / bare    glass W/m  / bare"]
    for lo, hi in [(0, 60), (60, 120), (120, 180), (180, 240), (240, 300), (0, 120), (0, 300)]:
        base = wmean(b["t"], b["out"], lo, hi)
        gbase = wmean(b["t"], b["glass"], lo, hi)
        for r in RUNS:
            q, t = d[r], d[r]["t"]
            o, g = wmean(t, q["out"], lo, hi), wmean(t, q["glass"], lo, hi)
            S.append(f"  {lo:3d}-{hi:3d}    {LABEL[r]:20s} {wmean(t, q['panelC'], lo, hi):9.1f} {wmean(t, q['panelR'], lo, hi):10.1f}"
                     f" {wmean(t, q['fins'], lo, hi):8.1f} {o:8.1f} {100 * o / base:7.1f}%  {g:9.1f} {100 * g / gbase:6.1f}%")
    S.append("")
    for lo, hi in [(0, 120), (60, 120), (0, 300), (240, 300)]:
        ob, of = wmean(b["t"], b["out"], lo, hi), wmean(f["t"], f["out"], lo, hi)
        S.append(f"Fan bar's gain in the radiator's heat, {lo}-{hi} s: {100 * (of / ob - 1):+.1f}% ({of:.1f} against {ob:.1f} W/m)")
    for hi in (60, 120, 180, 240, 300):
        gb, gf = integral(b["t"], b["glass"], 0, hi), integral(f["t"], f["glass"], 0, hi)
        S.append(f"Heat out through the glass since switch-on at {hi:3d} s: bare {gb / 1e3:.2f}, fan {gf / 1e3:.2f} kJ/m, fan / bare {100 * gf / gb:.1f}%")
    for r in RUNS:
        q = d[r]
        S.append(f"Radiator's heat since switch-on, {r}: {integral(q['t'], q['out'], 0, 120) / 1e3:.2f} kJ/m at 120 s, "
                 f"{integral(q['t'], q['out'], 0, 300) / 1e3:.2f} at 300 s")
    S += ["", "The fins' air flow, gross upward through the zone's bottom face, mean L/s per metre; the fan's outlet"]
    for lo, hi in [(0, 60), (60, 120), (120, 180), (180, 240), (240, 300)]:
        S.append(f"  {lo:3d}-{hi:3d} s   bare fins {1e3 * wmean(b['t'], b['convInPlus'], lo, hi):6.2f}   fan fins "
                 f"{1e3 * wmean(f['t'], f['convInPlus'], lo, hi):6.2f}   fan outlet {1e3 * wmean(f['t'], f['fanOutPlus'], lo, hi):6.2f}")
    S += ["", "The air, C: the line means across the room (x = 0.5-3.3 m) at 0.1, 1.1 and 2.6 m, the air beyond",
          "x = 0.424 m, the room's air mass-weighted, and the glass's mean surface; instantaneous",
          "     t   run                  0.1 m    1.1 m    2.6 m   beyond    room    glass"]
    for s in (10, 30, 60, 120, 180, 240, 300):
        for r in RUNS:
            q, t = d[r], d[r]["t"]
            S.append(f"  {s:4d}   {LABEL[r]:20s} {at(t, q['lineLowT'], s) - 273.15:6.2f}   {at(t, q['lineDeskT'], s) - 273.15:6.2f}"
                     f"   {at(t, q['lineHighT'], s) - 273.15:6.2f}   {at(t, q['farT'], s) - 273.15:6.2f}  {at(t, q['room'], s):6.2f}"
                     f"   {at(t, q['glassT'], s) - 273.15:6.2f}")
    S += ["", "Checks"]
    for r in RUNS:
        q, t = d[r], d[r]["t"]
        worst = max(abs(wmean(t, q["balance"], lo, lo + 60) / wmean(t, q["fins"], lo, lo + 60) - 1) for lo in range(0, 300, 60))
        k10 = int(np.searchsorted(t, 10))
        inp = integral(t, q["out"], 10, 300)
        air = q["U"][-1] - at(t, q["U"], 10)
        sto = q["stored"][-1] - at(t, q["stored"], 10)
        gl = integral(t, q["glass"], 10, 300)
        bar = integral(t, q["bar"], 10, 300)
        resid = inp - air - sto - gl - bar
        S.append(f"  {r}: the fins' heat against the zone air's own balance, by minute: largest difference {100 * worst:.3f}%")
        S.append(f"  {r}: section's budget 10-300 s, kJ/m: radiator {inp / 1e3:.3f} = air {air / 1e3:.3f} + wall layers "
                 f"{sto / 1e3:.3f} + glass {gl / 1e3:.3f} + fan housing {bar / 1e3:.3f} + residual {resid / 1e3:.3f} "
                 f"({100 * resid / inp:.3f}%)")
        S.append(f"  {r}: the air's mass against the hydrostatic start: largest drift {np.max(np.abs(q['mass'] / q['ini']['mass'] - 1)):.1e}; "
                 f"air {q['coldestT'][k10:].min() - 273.15:.2f}-{q['hottestT'].max() - 273.15:.2f} C outside the fins after 10 s")
    (res / "summary.txt").write_text("\n".join(S) + "\n")
    print("\n".join(S))


if __name__ == "__main__":
    main()
