#!/usr/bin/env python3
"""The room's own air and the window's flows, from the two solved runs' per-step monitors.

    python3 scripts/extract_results.py runs results

writes results/open/history.csv, results/tilted/history.csv and results/summary.txt from
runs/open and runs/tilted, and results/<run>/history.csv and results/summary_doubleHung.txt
from runs/doubleHungTop and runs/doubleHungSplit, for whichever of the two pairs is there.

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

The double-hung runs (read_dh): their monitors may be in several pieces, one per start time
(postProcessing/<name>/<start>/, each piece's largest .dat), joined in order, each after the
last time of the one before. The share replaced is as above. The inflow is the air crossing the
window: the gross flow into the room through the slot above the upper sash (slotHead, x =
-0.06 m) and, in doubleHungSplit, the slot below the lower sash (slotSill, x = -0.02 m), in m3/h
of the 0 C outdoor air and in room volumes an hour. The frame's plane x = 0 (opening1) also
counts the room's air turning in the recess in front of the sashes, so its gross flows are
larger. The budget is fluxBudget's: the change in the integral of rho s over the room against
the Euler sum of the net flux of s through opening1 (budget.dat, every step after the first).
The histories sample every step's values at the plane writes, every 1.25 s. Beside the runs, the
summary sets the orifice formulas with Cd 0.61 (BS 5925, CIBSE AM10; Linden 1999): one opening of
width W and height h, Q = (Cd/3) W h sqrt(g h dT/Tm); two openings of area a, dz apart,
Q = Cd (a/sqrt 2) sqrt(2 g dz dT/Tm); dT the room's mass-mean temperature over 0-300 s less 0 C,
Tm the mean of the two in kelvin. The turn-tilt window's figures are read from
results/open/history.csv and results/tilted/history.csv.
"""
import csv
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


# ---------------------------------------------------------------- the double-hung runs
DH = ("doubleHungTop", "doubleHungSplit")
DH_W, DH_SLOT, DH_DZ, CD, G = 0.86, 0.10, 2.165 - 0.975, 0.61, 9.81


def joined(pp, name):
    """A monitor's every step over all its pieces, or None if the run has no such monitor."""
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


def read_dh(run):
    pp = f"{run}/postProcessing"
    mons, head = {}, {}
    names = {"roomAir": "roomAir", "roomMass": "roomMass", "roomMeanT": "roomMeanT",
             "frameIn": "opening1In", "frameOut": "opening1Out", "headIn": ("slotHeadIn", "slotHeadArea"),
             "headOut": "slotHeadOut", "sillIn": ("slotSillIn", "slotSillArea"), "sillOut": "slotSillOut"}
    for k, ns in names.items():
        for n in (ns if isinstance(ns, tuple) else (ns,)):
            a, h = joined(pp, n)
            if a is not None:
                mons[k], head[k] = a, h
                break
    t = mons["roomAir"][:, 0]
    if not np.all(np.diff(t) > 0):
        raise SystemExit(f"{run}: the joined monitors' times are not one increasing series")
    for k, a in mons.items():
        assert np.array_equal(a[:, 0], t), k
    col = {k: a[:, 1] for k, a in mons.items()}
    zero = np.zeros_like(t)
    col["in"] = col["headIn"] + col.get("sillIn", zero)
    col["out"] = col["headOut"] + col.get("sillOut", zero)
    b = dat(f"{pp}/fluxBudget/budget.dat")[0]
    if not (np.all(np.diff(b[:, 0]) > 0) and np.allclose(b[:, 0], t)):
        raise SystemExit(f"{run}: budget.dat's times are not the monitors'")
    dt = np.diff(np.r_[0.0, t])
    left_flux = -np.concatenate([[0], np.cumsum(b[1:, 1:3].sum(1) * dt[1:])])
    gone = col["roomAir"][0] - col["roomAir"]
    with np.errstate(divide="ignore", invalid="ignore"):
        err_pct = np.where(gone > 0, (gone - left_flux) / gone * 100, 0.0)
    m0 = col["roomMass"][0]
    mean_in = np.concatenate([[col["in"][0]], cumtrapz(t, col["in"])[1:] / (t[1:] - t[0])])
    pieces = sorted((d for d in os.listdir(f"{pp}/roomAir") if os.path.isdir(f"{pp}/roomAir/{d}")), key=float)
    return dict(t=t, col=col, head=head, m0=m0, share=1 - col["roomAir"] / m0, err_pct=err_pct,
                mean_in=mean_in, pieces=pieces, radiator=(b[:, 3].min(), b[:, 3].max()))


def m3h(kg_s):
    return kg_s / RHO_OUT * 3600


def mean_over(t, v, lo, hi):
    ts = np.r_[lo, t[(t > lo) & (t < hi)], hi]
    y = np.interp(ts, t, v)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(ts)) / (hi - lo))


def history_dh(r, path):
    c = r["col"]
    sill = "sillIn" in c
    cols = ["t_s", "share_replaced", "room_mass_kg", "room_mean_T_C", "in_kg_s", "out_kg_s",
            "in_m3_h", "mean_in_0_t_m3_h", "in_room_volumes_per_h", "head_in_kg_s", "head_out_kg_s"] \
        + (["sill_in_kg_s", "sill_out_kg_s"] if sill else []) \
        + ["frame_in_kg_s", "frame_out_kg_s", "budget_error_pct_of_left"]
    with open(path, "w") as f:
        f.write(",".join(cols) + "\n")
        for w in range(1, 241):
            tt = w * 1.25
            i = at(r, tt)
            row = [f"{tt:g}", f"{r['share'][i]:.5f}", f"{c['roomMass'][i]:.4f}",
                   f"{c['roomMeanT'][i] - 273.15:.3f}", f"{c['in'][i]:.6f}", f"{c['out'][i]:.6f}",
                   f"{m3h(c['in'][i]):.2f}", f"{m3h(r['mean_in'][i]):.2f}", f"{per_h(c['in'][i]):.3f}",
                   f"{c['headIn'][i]:.6f}", f"{c['headOut'][i]:.6f}"] \
                + ([f"{c['sillIn'][i]:.6f}", f"{c['sillOut'][i]:.6f}"] if sill else []) \
                + [f"{c['frameIn'][i]:.6f}", f"{c['frameOut'][i]:.6f}", f"{r['err_pct'][i]:.3f}"]
            f.write(",".join(row) + "\n")


def reference(res, name):
    """open's or tilted's share at 300 s and mean inflow over 0-300 s, from their histories."""
    rows = list(csv.DictReader(open(f"{res}/{name}/history.csv")))
    last = rows[-1]
    assert abs(float(last["t_s"]) - 300) < 1e-9
    return float(last["share_replaced"]), float(last["mean_in_0_t_room_volumes_per_h"]) * V_ROOM


def summary_dh(runs, res, out):
    L = []
    p = L.append
    p(f"Outdoor air at 0 C: rho {RHO_OUT:.4f} kg/m3. Room {V_ROOM:g} m3 as drawn; m3/h and room volumes an")
    p("hour are volume flows of outdoor air. in = gross flow into the room through the slots.")
    for name, r in runs.items():
        h, c, t = r["head"], r["col"], r["t"]
        p("")
        p(f"== {name}: {len(t)} steps to t = {t[-1]:g} s, monitors in pieces from {', '.join(r['pieces'])} s; "
          f"radiator {r['radiator'][0]:g}-{r['radiator'][1]:g} W")
        p(f"   room zone {h['roomAir']['Cells']} cells, {float(h['roomAir']['Volume']):.4f} m3; "
          f"frame's plane x = 0: {h['frameIn']['Faces']} faces, {float(h['frameIn']['Area']):.4f} m2 of air")
        for k, label in (("headIn", "head slot"), ("sillIn", "sill slot")):
            if k in h:
                p(f"   {label}: {h[k]['Faces']} faces, {float(h[k]['Area']):.4f} m2")
        p(f"   room mass {r['m0']:.4f} kg at the first step, {c['roomMass'][-1]:.4f} kg at {t[-1]:g} s")
        for tt in (60, 120, 300):
            i = at(r, tt)
            sh = r["share"][i]
            p(f"   t {tt:3d} s: share replaced {sh * 100:5.2f}%; in {c['in'][i]:.5f} kg/s = {m3h(c['in'][i]):5.1f} m3/h, "
              f"mean over 0-t {m3h(r['mean_in'][i]):5.1f} m3/h = {per_h(r['mean_in'][i]):4.2f}/h; "
              f"room {c['roomMeanT'][i] - 273.15:5.2f} C; budget error {r['err_pct'][i]:+.2f}% of what left")
        p("   means over 0-300 s, kg/s:")
        for k in ("headIn", "headOut", "sillIn", "sillOut", "frameIn", "frameOut", "in", "out"):
            if k in c:
                p(f"     {k:8s} {mean_over(t, c[k], 0, 300):.5f}")
        r["Tr"] = mean_over(t, c["roomMeanT"], 0, 300)
        r["in300"] = mean_over(t, c["in"], 0, 300)
        lm = at(r, 240)
        p(f"   room mean T over 0-300 s {r['Tr'] - 273.15:.2f} C; over the last minute it fell "
          f"{c['roomMeanT'][lm] - c['roomMeanT'][-1]:.3f} K and the share rose {(r['share'][-1] - r['share'][lm]) * 100:.2f} points")
    p("")
    p(f"orifice formulas, Cd {CD}, W {DH_W} m, dT and Tm from each run's mean room temperature over 0-300 s:")
    form = {}
    for name, r in runs.items():
        dT, Tm = r["Tr"] - 273.15, (r["Tr"] + 273.15) / 2
        if name == "doubleHungTop":
            q = CD / 3 * DH_W * DH_SLOT * math.sqrt(G * DH_SLOT * dT / Tm)
            what = f"one slot {DH_SLOT} m tall"
        else:
            a = DH_W * DH_SLOT / 2
            q = CD * a / math.sqrt(2) * math.sqrt(2 * G * DH_DZ * dT / Tm)
            what = f"two slots {DH_SLOT / 2} m tall, {DH_DZ:.2f} m apart"
        form[name] = q * 3600
        cfd = m3h(r["in300"])
        p(f"   {name}: {what}: {q * 3600:.1f} m3/h; the run's {cfd:.1f} m3/h is {cfd / (q * 3600) * 100:.0f}% of it, "
          f"an effective Cd {CD * cfd / (q * 3600):.2f}")
    if len(runs) == 2:
        tp, sp = runs["doubleHungTop"], runs["doubleHungSplit"]
        p("")
        p(f"split / top: mean inflow over 0-300 s {sp['in300'] / tp['in300']:.2f}; share replaced at 300 s "
          f"{sp['share'][-1] / tp['share'][-1]:.2f}; the formulas {form['doubleHungSplit'] / form['doubleHungTop']:.2f}")
    if all(os.path.exists(f"{res}/{n}/history.csv") for n in ("open", "tilted")):
        p("")
        for n in ("open", "tilted"):
            sh, q = reference(res, n)
            p(f"{n} (results/{n}/history.csv): share replaced at 300 s {sh * 100:.2f}%, mean inflow over 0-300 s "
              f"{q / 3600 * RHO_OUT:.5f} kg/s = {q:.1f} m3/h")
            for name, r in runs.items():
                p(f"   {name} / {n}: share at 300 s {r['share'][-1] / sh:.3f}, mean inflow {m3h(r['in300']) / q:.3f}")
    open(out, "w").write("\n".join(L) + "\n")


def main():
    runs_dir, res = sys.argv[1], sys.argv[2]
    runs = {}
    if all(os.path.isdir(f"{runs_dir}/{n}") for n in ("open", "tilted")):
        for name in ("open", "tilted"):
            runs[name] = read(f"{runs_dir}/{name}")
            os.makedirs(f"{res}/{name}", exist_ok=True)
            history(runs[name], f"{res}/{name}/history.csv")
        summary(runs, f"{res}/summary.txt")
    dh = {}
    for name in DH:
        if os.path.isdir(f"{runs_dir}/{name}"):
            dh[name] = read_dh(f"{runs_dir}/{name}")
            os.makedirs(f"{res}/{name}", exist_ok=True)
            history_dh(dh[name], f"{res}/{name}/history.csv")
    if dh:
        summary_dh(dh, res, f"{res}/summary_doubleHung.txt")
    if not runs and not dh:
        raise SystemExit(f"no runs in {runs_dir}")


if __name__ == "__main__":
    main()
