#!/usr/bin/env python3
"""The room's own air and the window's flows, from the two solved runs' per-step monitors.

    python3 scripts/extract_results.py runs results

writes results/open/history.csv, results/tilted/history.csv and results/summary.txt.

share replaced = 1 - (integral of rho s over the room) / (the room's mass at the first step),
when the room is still all its own air (roomAir over roomMass).
inflow = the gross mass flow into the room through the frame's plane x = 0 (openingIn), as
volume of the 0 C outdoor air over the room's 33.6 m3, in room volumes an hour; its mean over
0-t is the time integral of every step's inflow (trapezoidal) over t.
well-mixed decay = -ln(1 - share)/t: the air-change rate a fully mixed room would need to
lose the same share.
budget: the change in the integral of rho s inside the frame's plane (indoorAir: the room,
and on tilt the wedge between the frame and the sash's outer face) against the time integral
of the net flow of s through that plane (openingS, sum of phi s, + into the room); the
difference as a share of what has left is the budget's error.
On tilt, the gross flows through the top gap and the two side gaps, each way.

The histories are every step's values sampled at the plane writes, every 0.625 s; the means
and the budget use every step.
"""
import math
import os
import sys

import numpy as np

RHO_OUT = 1e5 / (8314.47 / 28.96 * 273.15)   # the 0 C outdoor air, kg/m3
V_ROOM = 4.0 * 2.4 * 3.5                     # m3
TIMES = (60, 120, 300)
GAPS = (("top_in", "topUp"), ("top_out", "topDown"), ("left_in", "leftIn"),
        ("left_out", "leftOut"), ("right_in", "rightIn"), ("right_out", "rightOut"))


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


def per_h(kg_s):
    return kg_s / RHO_OUT / V_ROOM * 3600


def cumtrapz(t, y):
    return np.concatenate([[0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(t))])


def read(run):
    pp = f"{run}/postProcessing"
    mons = {k: dat(f"{pp}/{k}/0/volFieldValue.dat") for k in ("roomAir", "indoorAir", "roomMass", "roomMeanT")}
    for k in ("openingIn", "openingOut", "openingS") + tuple(g for _, g in GAPS):
        p = f"{pp}/{k}/0/surfaceFieldValue.dat"
        if os.path.exists(p):
            mons[k] = dat(p)
    n = min(len(a) for a, _ in mons.values())
    t = mons["roomAir"][0][:n, 0]
    for k, (a, _) in mons.items():
        assert np.array_equal(a[:n, 0], t), k
    col = {k: a[:n, 1] for k, (a, _) in mons.items()}
    head = {k: h for k, (_, h) in mons.items()}
    m0 = col["roomMass"][0]
    share = 1 - col["roomAir"] / m0
    gone = col["indoorAir"][0] - col["indoorAir"]
    err = gone + cumtrapz(t, col["openingS"])
    with np.errstate(divide="ignore", invalid="ignore"):
        err_pct = np.where(gone > 0, err / gone * 100, 0.0)
    mean_in = np.concatenate([[col["openingIn"][0]], cumtrapz(t, col["openingIn"])[1:] / (t[1:] - t[0])])
    return dict(t=t, col=col, head=head, m0=m0, share=share, err_pct=err_pct, mean_in=mean_in)


def at(r, tt):
    i = int(np.searchsorted(r["t"], tt - 1e-9))
    assert abs(r["t"][i] - tt) < 1e-6, (tt, r["t"][i])
    return i


def history(r, path):
    gaps = [(name, k) for name, k in GAPS if k in r["col"]]
    cols = ["t_s", "share_replaced", "room_mass_kg", "room_mean_T_C", "in_kg_s", "out_kg_s",
            "in_room_volumes_per_h", "mean_in_0_t_room_volumes_per_h", "well_mixed_decay_per_h",
            "room_air_out_kg_s", "budget_error_pct_of_left"] + [f"{name}_kg_s" for name, _ in gaps]
    c = r["col"]
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for w in range(1, 481):
            tt = w * 0.625
            i = at(r, tt)
            sh = r["share"][i]
            row = [f"{tt:g}", f"{sh:.5f}", f"{c['roomMass'][i]:.4f}", f"{c['roomMeanT'][i] - 273.15:.3f}",
                   f"{c['openingIn'][i]:.5f}", f"{c['openingOut'][i]:.5f}",
                   f"{per_h(c['openingIn'][i]):.3f}", f"{per_h(r['mean_in'][i]):.3f}",
                   f"{-math.log(1 - sh) / tt * 3600:.3f}", f"{-c['openingS'][i]:.5f}",
                   f"{r['err_pct'][i]:.3f}"] + [f"{c[k][i]:.5f}" for _, k in gaps]
            f.write(",".join(row) + "\n")


def summary(runs, out):
    L = []
    p = L.append
    p(f"Outdoor air at 0 C: rho {RHO_OUT:.4f} kg/m3. Room {V_ROOM:g} m3 as drawn; room volumes an hour")
    p("are volume flows of outdoor air over it.")
    for name, r in runs.items():
        h, c, t = r["head"], r["col"], r["t"]
        p("")
        p(f"== {name}: {len(t)} steps to t = {t[-1]:g} s")
        p(f"   room zone {h['roomAir']['Cells']} cells, {float(h['roomAir']['Volume']):.4f} m3; "
          f"opening {h['openingIn']['Faces']} faces, {float(h['openingIn']['Area']):.4f} m2 of air in x = 0")
        for gap, k in (("top", "topDown"), ("left", "leftIn"), ("right", "rightIn")):
            if k in h:
                p(f"   {gap} gap: {h[k]['Faces']} faces, {float(h[k]['Area']):.4f} m2")
        p(f"   room mass {r['m0']:.3f} kg at the first step, {c['roomMass'][-1]:.3f} kg at {t[-1]:g} s")
        for tt in TIMES:
            i = at(r, tt)
            sh = r["share"][i]
            p(f"   t {tt:3d} s: share replaced {sh * 100:5.2f}%, well-mixed decay {-math.log(1 - sh) / tt * 3600:5.2f}/h; "
              f"inflow {c['openingIn'][i]:.4f} kg/s = {c['openingIn'][i] / RHO_OUT * 3600:4.0f} m3/h = "
              f"{per_h(c['openingIn'][i]):5.2f}/h, mean over 0-t {per_h(r['mean_in'][i]):5.2f}/h; "
              f"room {c['roomMeanT'][i] - 273.15:5.2f} C; budget error {r['err_pct'][i]:+.2f}% of what left")
        i = at(r, 300)
        p(f"   inflow over 0-300 s: {r['mean_in'][i] * 300 / RHO_OUT / V_ROOM:.3f} room volumes")
        for name_, k in GAPS:
            if k in c:
                p(f"   {name_:9s} {c[k][i]:.4f} kg/s at 300 s")
    o, ti = runs["open"], runs["tilted"]
    io, it = at(o, 300), at(ti, 300)
    p("")
    p(f"tilted / open, mean inflow over 0-300 s: {ti['mean_in'][it] / o['mean_in'][io] * 100:.1f}%; "
      f"inflow at 300 s: {ti['col']['openingIn'][it] / o['col']['openingIn'][io] * 100:.1f}%; "
      f"share replaced at 300 s: {ti['share'][it] / o['share'][io] * 100:.1f}%")
    open(out, "w").write("\n".join(L) + "\n")


def main():
    runs_dir, res = sys.argv[1], sys.argv[2]
    runs = {}
    for name in ("open", "tilted"):
        runs[name] = read(f"{runs_dir}/{name}")
        os.makedirs(f"{res}/{name}", exist_ok=True)
        history(runs[name], f"{res}/{name}/history.csv")
    summary(runs, f"{res}/summary.txt")


if __name__ == "__main__":
    main()
