#!/usr/bin/env python3
"""The room's own air and the windows' flows, from the solved runs' per-step monitors.

    python3 scripts/extract_results.py runs results

writes results/<run>/history.csv for each of one, two, stillOne and stillTwo found in runs/,
and results/summary.txt.

share replaced = 1 - (integral of rho s over the room) / (the room's mass at the first step),
windowAiring's definition; also 1 - the room's mass-mean s, which reads a little higher because
the room gains mass as it cools.
in, out = the gross mass flow into and out of the room through each opening, in its frame's
plane (opening1 in the window wall, x = 0; opening2 opposite, x = 4 m); net = in - out. The
air in is the sum over the openings of each one's gross inflow; its mean over an interval is
the trapezoidal time integral of every step's value.
through-flow (two windows) = half the difference of the two openings' net flows into the room,
(net1 - net2)/2: the air that crosses the room from the window wall's window to the other, the
room's own mass change split evenly between them.
budget: the change in the integral of rho s over the room against the Euler sum of the net
flux of s through the openings (fluxBudget's budget.dat, every step after the first); the
difference as a share of what has left.

The histories are every step's values sampled at the plane writes, every 1.25 s; the means and
the budget use every step.
"""
import math
import os
import sys

import numpy as np

RHO_OUT = 1e5 / (8314.47 / 28.96 * 273.15)   # the 0 C outdoor air at 1e5 Pa, kg/m3
RUNS = {"one": 1, "two": 2, "stillOne": 1, "stillTwo": 2}
DP = 2.41 + 1.45                              # the breeze's pressure across the room, Pa


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


def monitor(pp, name):
    d = f"{pp}/{name}/0"
    files = [f"{d}/{f}" for f in os.listdir(d) if f.endswith(".dat")]
    return dat(max(files, key=os.path.getsize))


def mean_over(t, v, lo, hi):
    ts = np.r_[lo, t[(t > lo) & (t < hi)], hi]
    y = np.interp(ts, t, v)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(ts)) / (hi - lo))


def read(path, n):
    pp = f"{path}/postProcessing"
    for d in ("roomAir", "opening1In"):
        pieces = [p for p in os.listdir(f"{pp}/{d}") if os.path.isdir(f"{pp}/{d}/{p}")]
        if pieces != ["0"]:
            raise SystemExit(f"{path}: {d} in pieces {pieces}; this reads one solve from t = 0")
    names = ["roomAir", "roomMass", "roomMeanT", "roomMeanS"]
    for k in range(1, n + 1):
        names += [f"opening{k}In", f"opening{k}Out", f"opening{k}Net", f"opening{k}S"]
    col, head = {}, {}
    for name in names:
        a, h = monitor(pp, name)
        col[name], head[name] = a, h
    t = col["roomAir"][:, 0]
    if not np.all(np.diff(t) > 0):
        raise SystemExit(f"{path}: the monitors' times are not one increasing series")
    for k, a in col.items():
        assert np.array_equal(a[:, 0], t), k
    col = {k: a[:, 1] for k, a in col.items()}
    b = dat(f"{pp}/fluxBudget/budget.dat")[0]
    if not (np.all(np.diff(b[:, 0]) > 0) and np.allclose(b[:, 0], t)):
        raise SystemExit(f"{path}: budget.dat's times are not the monitors'")
    dt = np.diff(np.r_[0.0, t])
    left_flux = -np.concatenate([[0], np.cumsum(b[1:, 1:3].sum(1) * dt[1:])])
    gone = col["roomAir"][0] - col["roomAir"]
    with np.errstate(divide="ignore", invalid="ignore"):
        err_pct = np.where(gone > 0, (gone - left_flux) / gone * 100, 0.0)
    m0 = col["roomMass"][0]
    inflow = sum(col[f"opening{k}In"] for k in range(1, n + 1))
    cum = np.concatenate([[0], np.cumsum(0.5 * (inflow[1:] + inflow[:-1]) * np.diff(t))])
    mean_in = np.concatenate([[inflow[0]], cum[1:] / (t[1:] - t[0])])
    through = 0.5 * (col["opening1Net"] - col["opening2Net"]) if n == 2 else None
    return dict(t=t, col=col, head=head, n=n, m0=m0, vol=float(head["roomAir"]["Volume"]),
                share=1 - col["roomAir"] / m0, share_s=1 - col["roomMeanS"], err_pct=err_pct,
                inflow=inflow, mean_in=mean_in, through=through, err_total=(gone[-1] - left_flux[-1], gone[-1]),
                radiator=(b[:, 3].min(), b[:, 3].max()))


def at(r, tt):
    i = int(np.searchsorted(r["t"], tt - 1e-9))
    assert abs(r["t"][i] - tt) < 1e-6, (tt, r["t"][i])
    return i


def history(r, path):
    c, n = r["col"], r["n"]
    cols = ["t_s", "share_replaced", "share_replaced_1_minus_mean_s", "room_mass_kg", "room_mean_T_C",
            "in_kg_s", "mean_in_0_t_kg_s", "in1_kg_s", "out1_kg_s"]
    if n == 2:
        cols += ["in2_kg_s", "out2_kg_s", "through_kg_s"]
    cols += ["room_air_out_kg_s", "budget_error_pct_of_left"]
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for w in range(1, int(round(r["t"][-1] / 1.25)) + 1):
            tt = w * 1.25
            i = at(r, tt)
            row = [f"{tt:g}", f"{r['share'][i]:.5f}", f"{r['share_s'][i]:.5f}", f"{c['roomMass'][i]:.4f}",
                   f"{c['roomMeanT'][i] - 273.15:.3f}", f"{r['inflow'][i]:.5f}", f"{r['mean_in'][i]:.5f}",
                   f"{c['opening1In'][i]:.5f}", f"{c['opening1Out'][i]:.5f}"]
            if n == 2:
                row += [f"{c['opening2In'][i]:.5f}", f"{c['opening2Out'][i]:.5f}", f"{r['through'][i]:.5f}"]
            room_out = -sum(c[f"opening{k}S"][i] for k in range(1, n + 1))
            row += [f"{room_out:.5f}", f"{r['err_pct'][i]:.3f}"]
            f.write(",".join(row) + "\n")


def summary(runs, out):
    L = []
    p = L.append
    p(f"Outdoor air at 0 C and 1e5 Pa: rho {RHO_OUT:.4f} kg/m3; room volumes an hour are volume flows of")
    p("that air over the room zone's volume. Shares in percent of the room's own air; in and out are")
    p("gross mass flows, kg/s, net = in - out, all into the room positive.")
    for name, r in runs.items():
        h, c, t, n = r["head"], r["col"], r["t"], r["n"]
        T = t[-1]
        p("")
        p(f"== {name}: {len(t)} steps to t = {T:g} s; radiator {r['radiator'][0]:g}-{r['radiator'][1]:g} W")
        areas = ", ".join(f"opening{k} {h[f'opening{k}In']['Faces']} faces {float(h[f'opening{k}In']['Area']):.4f} m2"
                          for k in range(1, n + 1))
        p(f"   room zone {h['roomAir']['Cells']} cells, {r['vol']:.4f} m3; {areas}")
        p(f"   room mass {r['m0']:.4f} kg at the first step, {c['roomMass'][-1]:.4f} kg at {T:g} s")
        for tt in (30, 60, 120, 180, 240, 300):
            if tt > T + 1e-6:
                continue
            i = at(r, tt)
            p(f"   t {tt:3d} s: share replaced {r['share'][i] * 100:5.2f}% (1 - mean s {r['share_s'][i] * 100:5.2f}%); "
              f"air in {r['inflow'][i]:.4f}, mean over 0-t {r['mean_in'][i]:.4f} kg/s = "
              f"{r['mean_in'][i] / RHO_OUT * 3600 / r['vol']:5.2f}/h; room {c['roomMeanT'][i] - 273.15:5.2f} C; "
              f"budget error {r['err_pct'][i]:+.2f}% of what left")
        wins = [(0, 60), (0, 180), (120, 180)] + ([(0, 300), (240, 300)] if T >= 300 - 1e-6 else [])
        p("   means, kg/s:  " + "".join(f"{f'{lo}-{hi} s':>11s}" for lo, hi in wins))
        series = [("air in", r["inflow"])]
        for k in range(1, n + 1):
            series += [(f"in{k}", c[f"opening{k}In"]), (f"out{k}", c[f"opening{k}Out"]), (f"net{k}", c[f"opening{k}Net"])]
        if n == 2:
            series.append(("through", r["through"]))
        for lab, v in series:
            p(f"     {lab:10s}" + "".join(f"{mean_over(t, v, lo, hi):11.5f}" for lo, hi in wins))
        gone_err, gone = r["err_total"]
        p(f"   scalar budget at {T:g} s: {gone:.4f} kg of the room's air gone, error {gone_err:+.4f} kg, "
          f"{gone_err / gone * 100:+.2f}%; within {np.abs(r['err_pct'][t >= 30]).max():.2f}% at every step from 30 s")
        if n == 2:
            ten = [mean_over(t, r["through"], lo, lo + 10) / mean_over(t, r["inflow"], lo, lo + 10)
                   for lo in range(0, int(T) - 9, 10)]
            p(f"   through-flow over the air in, 10 s windows: {min(ten) * 100:+.2f}% to {max(ten) * 100:+.2f}%; "
              f"{T - 90:g}-{T:g} s {mean_over(t, r['through'], T - 90, T) / mean_over(t, r['inflow'], T - 90, T) * 100:+.3f}%")
    if "two" in runs:
        r = runs["two"]
        a = float(r["head"]["opening1In"]["Area"])
        q_cd06 = 0.6 * a / math.sqrt(2) * math.sqrt(2 * DP / RHO_OUT) * RHO_OUT
        q = mean_over(r["t"], r["inflow"], 120, 180)
        cd = 0.6 * q / q_cd06
        tau = r["vol"] / (q / RHO_OUT)
        p("")
        p(f"two against the orifice formula for its two {a:.2f} m2 openings in series, {DP:.2f} Pa across both:")
        p(f"   Cd 0.6 gives {q_cd06:.4f} kg/s; the run takes in {q:.4f} kg/s over 120-180 s, "
          f"{(q / q_cd06 - 1) * 100:+.1f}%, an effective Cd of {cd:.2f}")
        p(f"   a well-mixed room fed that inflow, time constant {tau:.1f} s: "
          + ", ".join(f"{(1 - math.exp(-tt / tau)) * 100:.1f}% at {tt} s" for tt in (60, 120, 180))
          + "; the run: " + ", ".join(f"{r['share'][at(r, tt)] * 100:.1f}% ({r['share_s'][at(r, tt)] * 100:.1f}% as 1 - mean s)"
                                      for tt in (60, 120, 180)))
    for a, b in (("one", "stillOne"), ("two", "stillTwo"), ("stillTwo", "stillOne"), ("two", "one")):
        if a in runs and b in runs:
            ra, rb = runs[a], runs[b]
            T = min(ra["t"][-1], rb["t"][-1])
            p("")
            p(f"{a} against {b}: share at 60 s {ra['share'][at(ra, 60)] * 100:.2f}% against {rb['share'][at(rb, 60)] * 100:.2f}%, "
              f"at {T:g} s {ra['share'][at(ra, T)] * 100:.2f}% against {rb['share'][at(rb, T)] * 100:.2f}%; "
              f"air in over 0-{T:g} s {mean_over(ra['t'], ra['inflow'], 0, T):.4f} against "
              f"{mean_over(rb['t'], rb['inflow'], 0, T):.4f} kg/s, ratio "
              f"{mean_over(ra['t'], ra['inflow'], 0, T) / mean_over(rb['t'], rb['inflow'], 0, T):.3f}")
    open(out, "w").write("\n".join(L) + "\n")


def main():
    runs_dir, res = sys.argv[1], sys.argv[2]
    runs = {}
    for name, n in RUNS.items():
        if os.path.isdir(f"{runs_dir}/{name}/postProcessing"):
            runs[name] = read(f"{runs_dir}/{name}", n)
            os.makedirs(f"{res}/{name}", exist_ok=True)
            history(runs[name], f"{res}/{name}/history.csv")
    if not runs:
        raise SystemExit(f"no solved runs in {runs_dir}")
    summary(runs, f"{res}/summary.txt")


if __name__ == "__main__":
    main()
