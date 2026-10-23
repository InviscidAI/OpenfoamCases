#!/usr/bin/env python3
"""The room's own air and the window's flows, from the two solved runs' per-step monitors.

    python3 scripts/extract_results.py runs results

writes results/roof/history.csv, results/wall/history.csv and results/summary.txt.

Each monitor may be in several pieces, one per start time (postProcessing/<name>/<start>/, the
roof run's 0 and 30 s), joined in order, each after the last time of the one before; the
largest .dat in a piece is its data.

share replaced = 1 - (integral of rho s over the room) / (the room's mass at the first step),
as windowAiring.
inflow = the gross mass flow into the room through the opening (opening1In: the frame's plane
x = 0 for the wall window, the roof's inner face for the roof window), also as m3/h of the 0 C
outdoor air and as room volumes an hour over each room's own volume; its mean over 0-t is the
trapezoidal time integral of every step's inflow over t. For the roof window the same through
its two sides of the sash on the roof's inner face, eaves (below) and ridge (above).
budget: the change in the integral of rho s over the room against the Euler sum of the net
flux of s through the opening (fluxBudget's budget.dat, every step after the first); the
difference as a share of what has left.
the air leaving: the mean s of the air the window lets out, the time integral of the net flux
of s out (opening1S) over that of the gross outflow, against the room's mean s over the same
interval (roomMeanS, volume-weighted).

The histories are every step's values sampled at the plane writes, every 1.25 s; the means and
the budget use every step.
"""
import math
import os
import sys

import numpy as np

RHO_OUT = 1e5 / (8314.47 / 28.96 * 273.15)   # the 0 C outdoor air, kg/m3
TIMES = (60, 120, 300)
# the single-opening formula's ratio, Q ~ W H^1.5 (Linden 1999; BS 5925): the roof window's
# 0.887 m width over the 0.947 m of height it spans in a 45-degree roof, against 1.0 x 1.2 m
FORMULA = 0.887 * (1.339 * math.sin(math.pi / 4)) ** 1.5 / (1.0 * 1.2 ** 1.5)


def dat(path):
    rows, head = [], {}
    for line in open(path):
        if line.startswith("#"):
            if ":" in line:
                k, v = line[1:].split(":", 1)
                head[k.strip()] = v.strip()
        elif line.strip():
            rows.append(line.split())
    return np.array(rows, dtype=float), head


def joined(pp, name):
    if not os.path.isdir(f"{pp}/{name}"):
        return None, {}
    parts = sorted((d for d in os.listdir(f"{pp}/{name}") if os.path.isdir(f"{pp}/{name}/{d}")), key=float)
    out, head = None, {}
    for d in parts:
        files = [f"{pp}/{name}/{d}/{f}" for f in os.listdir(f"{pp}/{name}/{d}") if f.endswith(".dat")]
        a, h = dat(max(files, key=os.path.getsize))
        if not len(a):
            continue
        head = head or h
        out = a if out is None else np.r_[out, a[a[:, 0] > out[-1, 0]]]
    return out, head


def cumtrapz(t, y):
    return np.concatenate([[0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t))])


def mean_over(t, v, lo, hi):
    ts = np.r_[lo, t[(t > lo) & (t < hi)], hi]
    y = np.interp(ts, t, v)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(ts)) / (hi - lo))


def read(run):
    pp = f"{run}/postProcessing"
    mons, head = {}, {}
    for name in ("roomAir", "roomMass", "roomMeanT", "roomMeanS", "opening1In", "opening1Out",
                 "opening1S", "eavesIn", "eavesOut", "ridgeIn", "ridgeOut"):
        a, h = joined(pp, name)
        if a is not None:
            mons[name], head[name] = a, h
    t = mons["roomAir"][:, 0]
    if not np.all(np.diff(t) > 0):
        raise SystemExit(f"{run}: the joined monitors' times are not one increasing series")
    for k, a in mons.items():
        assert np.array_equal(a[:, 0], t), k
    col = {k: a[:, 1] for k, a in mons.items()}
    b = dat(f"{pp}/fluxBudget/budget.dat")[0]
    if not (np.all(np.diff(b[:, 0]) > 0) and np.allclose(b[:, 0], t)):
        raise SystemExit(f"{run}: budget.dat's times are not the monitors'")
    dt = np.diff(np.r_[0.0, t])
    left_flux = -np.concatenate([[0], np.cumsum(b[1:, 1:3].sum(1) * dt[1:])])
    gone = col["roomAir"][0] - col["roomAir"]
    with np.errstate(divide="ignore", invalid="ignore"):
        err_pct = np.where(gone > 0, (gone - left_flux) / gone * 100, 0.0)
    m0 = col["roomMass"][0]
    vol = float(head["roomAir"]["Volume"])
    mean_in = np.concatenate([[col["opening1In"][0]], cumtrapz(t, col["opening1In"])[1:] / (t[1:] - t[0])])
    pieces = sorted((d for d in os.listdir(f"{pp}/roomAir") if os.path.isdir(f"{pp}/roomAir/{d}")), key=float)
    return dict(t=t, col=col, head=head, m0=m0, vol=vol, share=1 - col["roomAir"] / m0, err_pct=err_pct,
                mean_in=mean_in, pieces=pieces, radiator=(b[:, 3].min(), b[:, 3].max()))


def at(r, tt):
    i = int(np.searchsorted(r["t"], tt - 1e-9))
    assert abs(r["t"][i] - tt) < 1e-6, (tt, r["t"][i])
    return i


def m3h(kg_s):
    return kg_s / RHO_OUT * 3600


def history(r, path):
    c = r["col"]
    sides = [k for k in ("eavesIn", "eavesOut", "ridgeIn", "ridgeOut") if k in c]
    cols = ["t_s", "share_replaced", "room_mass_kg", "room_mean_T_C", "in_kg_s", "out_kg_s", "in_m3_h",
            "mean_in_0_t_m3_h", "mean_in_0_t_room_volumes_per_h", "room_air_out_kg_s",
            "budget_error_pct_of_left"] + [f"{k[:-2] if k.endswith('In') else k[:-3]}_{'in' if k.endswith('In') else 'out'}_kg_s" for k in sides]
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for w in range(1, 241):
            tt = w * 1.25
            i = at(r, tt)
            row = [f"{tt:g}", f"{r['share'][i]:.5f}", f"{c['roomMass'][i]:.4f}", f"{c['roomMeanT'][i] - 273.15:.3f}",
                   f"{c['opening1In'][i]:.5f}", f"{c['opening1Out'][i]:.5f}", f"{m3h(c['opening1In'][i]):.1f}",
                   f"{m3h(r['mean_in'][i]):.1f}", f"{m3h(r['mean_in'][i]) / r['vol']:.3f}",
                   f"{-c['opening1S'][i]:.5f}", f"{r['err_pct'][i]:.3f}"] + [f"{c[k][i]:.5f}" for k in sides]
            f.write(",".join(row) + "\n")


def summary(runs, out):
    L = []
    p = L.append
    p(f"Outdoor air at 0 C: rho {RHO_OUT:.4f} kg/m3; m3/h and room volumes an hour are volume flows of")
    p("outdoor air, over each room's own volume (its room zone's).")
    for name, r in runs.items():
        h, c, t = r["head"], r["col"], r["t"]
        p("")
        p(f"== {name}: {len(t)} steps to t = {t[-1]:g} s, monitors in pieces from {', '.join(r['pieces'])} s; "
          f"radiator {r['radiator'][0]:g}-{r['radiator'][1]:g} W")
        p(f"   room zone {h['roomAir']['Cells']} cells, {r['vol']:.4f} m3; opening {h['opening1In']['Faces']} faces, "
          f"{float(h['opening1In']['Area']):.4f} m2 of air")
        for k in ("eavesIn", "ridgeIn"):
            if k in h:
                p(f"   {k[:-2]} side: {h[k]['Faces']} faces, {float(h[k]['Area']):.4f} m2")
        p(f"   room mass {r['m0']:.4f} kg at the first step, {c['roomMass'][-1]:.4f} kg at {t[-1]:g} s")
        for tt in TIMES:
            i = at(r, tt)
            sh = r["share"][i]
            p(f"   t {tt:3d} s: share replaced {sh * 100:5.2f}%; inflow {c['opening1In'][i]:.4f} kg/s = "
              f"{m3h(c['opening1In'][i]):4.0f} m3/h, mean over 0-t {r['mean_in'][i]:.4f} kg/s = "
              f"{m3h(r['mean_in'][i]) / r['vol']:5.2f}/h; room {c['roomMeanT'][i] - 273.15:5.2f} C; "
              f"budget error {r['err_pct'][i]:+.2f}% of what left")
        p("   means, kg/s:        0-300 s   240-300 s")
        for k in ("opening1In", "opening1Out", "eavesIn", "eavesOut", "ridgeIn", "ridgeOut"):
            if k in c:
                p(f"     {k:12s} {mean_over(t, c[k], 0, 300):9.5f} {mean_over(t, c[k], 240, 300):9.5f}")
        r["in300"] = mean_over(t, c["opening1In"], 0, 300)
        lm = at(r, 240)
        p(f"   over the last minute the room's mean T fell {c['roomMeanT'][lm] - c['roomMeanT'][-1]:.3f} K "
          f"and the share rose {(r['share'][-1] - r['share'][lm]) * 100:.2f} points")
        for lo, hi in ((0, 60), (60, 300), (0, 300)):
            sel = (t > lo) & (t <= hi)
            ts = t[sel]
            s_out = -np.trapezoid(c["opening1S"][sel], ts) / np.trapezoid(c["opening1Out"][sel], ts)
            room = np.trapezoid(c["roomMeanS"][sel], ts) / (ts[-1] - ts[0])
            p(f"   {lo}-{hi} s: mean s of the air leaving {s_out:.3f}, the room's mean s {room:.3f}, ratio {s_out / room:.2f}")
    if len(runs) == 2:
        rf, wl = runs["roof"], runs["wall"]
        p("")
        p(f"roof / wall: mean inflow over 0-300 s {rf['in300'] / wl['in300']:.3f}; share replaced at 300 s "
          f"{rf['share'][-1] / wl['share'][-1]:.3f}; at 60 s {rf['share'][at(rf, 60)] / wl['share'][at(wl, 60)]:.3f}")
        p(f"the single-opening formula, 0.887 x 0.947^1.5 / (1.0 x 1.2^1.5): {FORMULA:.3f}")
    open(out, "w").write("\n".join(L) + "\n")


def main():
    runs_dir, res = sys.argv[1], sys.argv[2]
    runs = {}
    for name in ("roof", "wall"):
        if os.path.isdir(f"{runs_dir}/{name}"):
            runs[name] = read(f"{runs_dir}/{name}")
            os.makedirs(f"{res}/{name}", exist_ok=True)
            history(runs[name], f"{res}/{name}/history.csv")
    if not runs:
        raise SystemExit(f"no runs in {runs_dir}")
    summary(runs, f"{res}/summary.txt")


if __name__ == "__main__":
    main()
