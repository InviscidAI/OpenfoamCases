#!/usr/bin/env python3
"""Histories and the summaries from the solved runs: results/<run>/history.csv, summary*.txt.

    python3 scripts/extract_results.py runs results            # shut and open: summary.txt
    python3 scripts/extract_results.py runs results raised     # raised and shut solved again
                                                               # beside it: summary_raised.txt

The second form reads runs/shut and runs/raised, solved side by side, writes their histories to
results/shutAgain/ and results/raised/, and sets the shut run solved again beside the committed
results/shut/history.csv, so it must be run after the first form's results are in place.

Reads each run's per-step monitors (postProcessing/<name>/0/*.dat) and its mid plane
(postProcessing/planes/<t>/mid.vtp, every 1.25 s from 0 to 600 s; the t = 0 plane is written
from the initial fields by ../Allrun). One row per plane write:

- the half room's CO2 budget, g: the room's gain since the start (roomCO2), what the
  cauldron's inflow convected in, the net through the doorway (+ into the room) and through
  the leak, each step's flux held over that step, and the residual, gain - in - door - leak,
  which is the CO2 diffusing in through the cauldron's face on top of what the flow carries
  (README, "Checks");
- the room's CO2 at 0.6 m (the `nose` zone, 0.57-0.63 m over the whole room) as a multiple of
  normal air (425 ppm), its volume average, interpolated in time between steps, and its
  largest cell; mass fraction to mole fraction with O2 and N2 in dry air's ratio;
- the CO2 at the toddler's nose, x 3.20-3.30 m, y 0.56-0.64 m on the mid plane (four cells),
  at that write and as the mean of the last 8 writes (10 s; the writes so far at the start),
  which is the number in the clip; here the plane's own O2 is used for the mole fraction;
- open only: the gross mass flow each way through the whole doorway, kg/s (twice the half
  model's), and the room's mean temperature over the mid plane;
- the outdoor air's speed on the mid plane (x < -0.15 m), median and largest.

Needs NumPy and PyVista.
"""
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

W_CO2, W_O2, W_N2, Y_O2_DRY = 44.01, 31.9988, 28.0134, 0.2314
X_NORMAL = 425e-6
TODDLER = (3.25, 0.05, 0.56, 0.64)      # nose x, half-width across, y range
TRAIL = 8
LIMITS = [("OSHA PEL and NIOSH REL, 8 h", 12), ("UK HSE EH40, 15 min", 35),
          ("NIOSH STEL, 15 min", 71), ("NIOSH IDLH", 94)]


def dat(run, fo, kind):
    a = np.loadtxt(run / f"postProcessing/{fo}/0/{kind}.dat", comments="#")
    return a[:, 0], a[:, 1:]


def held(t, q):
    """Integral of a per-step flux, each step's value held over that step."""
    return np.cumsum(q * np.diff(np.r_[0.0, t]))


def dry_air_multiple(y):
    rest = (1 - y) * (Y_O2_DRY / W_O2 + (1 - Y_O2_DRY) / W_N2)
    return (y / W_CO2) / (y / W_CO2 + rest) / X_NORMAL


def plane_multiple(m):
    y = np.asarray(m.cell_data["CO2"], float)
    yo = np.asarray(m.cell_data["O2"], float)
    n = y / W_CO2
    return n / (n + yo / W_O2 + (1 - y - yo) / W_N2) / X_NORMAL


def history(run, name):
    t, m = dat(run, "roomCO2", "volFieldValue")
    m = m[:, 0]
    _, inf = dat(run, "inflowCO2", "surfaceFieldValue")
    _, door = dat(run, "doorCO2", "surfaceFieldValue")
    _, leak = dat(run, "leakCO2", "surfaceFieldValue")
    tn, nose = dat(run, "noseCO2", "volFieldValue")
    _, nmax = dat(run, "noseCO2max", "volFieldValue")
    cin, cdoor, cleak = held(t, -inf[:, 0]), held(t, door[:, 0]), held(t, -leak[:, 0])
    if name == "open":
        _, qi = dat(run, "doorIn", "surfaceFieldValue")
        _, qo = dat(run, "doorOut", "surfaceFieldValue")

    root = run / "postProcessing/planes"
    dirs = sorted((d for d in root.iterdir() if (d / "mid.vtp").exists()), key=lambda d: float(d.name))
    times = np.array([float(d.name) for d in dirs])
    if times[0] != 0.0 or not np.allclose(np.diff(times), 1.25):
        raise SystemExit(f"{run}: the planes are not every 1.25 s from t = 0")
    # the nose zone at each write: the room is normal air at t = 0 and the first row is after a step
    zone = np.interp(times, np.r_[0.0, tn], np.r_[1.0, dry_air_multiple(nose[:, 0])])
    zmax = np.interp(times, np.r_[0.0, tn], np.r_[1.0, dry_air_multiple(nmax[:, 0])])

    rows, spot = [], []
    x0, half, y0, y1 = TODDLER
    for k, d in enumerate(dirs):
        mp = pv.read(d / "mid.vtp")
        cc = mp.cell_centers().points
        X = plane_multiple(mp)
        sel = (np.abs(cc[:, 0] - x0) < half) & (cc[:, 1] > y0) & (cc[:, 1] < y1)
        if sel.sum() != 4:
            raise SystemExit(f"{d}: {sel.sum()} cells at the toddler's nose, not 4")
        spot.append(X[sel].mean())
        U = np.asarray(mp.cell_data["U"])
        sp = np.hypot(U[:, 0], U[:, 1])
        out = cc[:, 0] < -0.15
        room = (cc[:, 0] > 0) & (cc[:, 1] < 2.4)
        s = times[k]
        i = min(np.searchsorted(t, s - 1e-9), len(t) - 1)
        row = dict(t_s=s, gain_g=(m[i] - m[0]) * 1e3, in_g=cin[i] * 1e3, door_g=cdoor[i] * 1e3,
                   leak_g=cleak[i] * 1e3)
        row["residual_g"] = row["gain_g"] - row["in_g"] - row["door_g"] - row["leak_g"]
        if s == 0:      # the start, before the first step
            row.update(gain_g=0.0, in_g=0.0, door_g=0.0, leak_g=0.0, residual_g=0.0)
        row.update(nose_zone_x=zone[k], nose_zone_max_x=zmax[k])
        if name == "open":
            j = min(np.searchsorted(t, s - 1e-9), len(t) - 1)
            row.update(door_in_kg_s=2 * qi[j, 0] if s else 0.0, door_out_kg_s=2 * qo[j, 0] if s else 0.0,
                       room_T_mid_C=float(np.asarray(mp.cell_data["T"])[room].mean()) - 273.15)
        row.update(outdoor_speed_median_m_s=float(np.median(sp[out])),
                   outdoor_speed_max_m_s=float(sp[out].max()))
        rows.append(row)
    spot = np.array(spot)
    c = np.cumsum(np.r_[0.0, spot])
    n = np.arange(1, len(spot) + 1)
    lo = np.maximum(0, n - TRAIL)
    trail = (c[n] - c[lo]) / (n - lo)
    for row, a, b in zip(rows, spot, trail):
        row["toddler_x"], row["toddler_10s_x"] = a, b
    return rows


def write_csv(path, rows):
    keys = list(rows[0])
    keys = keys[:8] + ["toddler_x", "toddler_10s_x"] + [k for k in keys[8:] if not k.startswith("toddler")]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(",".join(keys) + "\n")
        for r in rows:
            f.write(",".join(f"{r[k]:.6g}" for k in keys) + "\n")


def read_csv(path):
    with open(path) as f:
        keys = f.readline().strip().split(",")
        a = np.loadtxt(f, delimiter=",", ndmin=2)
    return {k: a[:, i] for i, k in enumerate(keys)}


def mmss(s):
    return f"{int(s // 60)} min {s % 60:.2f} s"


def raised(runs, out):
    """The cauldron on the coffee table (shut, solved again) against raised, both door shut."""
    H = {"shutAgain": history(runs / "shut", "shut"), "raised": history(runs / "raised", "raised")}
    for n in H:
        write_csv(out / n / "history.csv", H[n])
    col = {n: {k: np.array([r[k] for r in H[n]]) for k in H[n][0]} for n in H}
    t = col["raised"]["t_s"]
    first = read_csv(out / "shut" / "history.csv")
    L = []
    say = L.append
    say("dryIceCauldron: the cauldron raised against the coffee table, door shut (scripts/extract_results.py)")
    say("shutAgain is ./Allrun shut solved again beside raised; shut is the committed results/shut")
    say("")
    say("CO2 as a multiple of normal air (425 ppm), at each whole minute")
    say("  minute                                   " + "".join(f"{m:7d}" for m in range(1, 11)) + "   ten-minute mean")
    for what, key in (("at the toddler's nose, 10 s", "toddler_10s_x"), ("toddler, one write", "toddler_x"),
                      ("room average at 0.6 m", "nose_zone_x")):
        for n, c in (("shut (committed)", first), ("shutAgain", col["shutAgain"]), ("raised", col["raised"])):
            v = c[key]
            say(f"  {n:16s} {what:27s}" + "".join(f"{v[m * 48]:7.1f}" for m in range(1, 11)) + f"   {v.mean():7.1f}")
    for what, key in (("toddler, 10 s", "toddler_10s_x"), ("toddler, one write", "toddler_x"),
                      ("room average", "nose_zone_x")):
        a, b = col["raised"][key], col["shutAgain"][key]
        d = np.sign(a - b)
        flips = [k for k in range(1, len(t)) if t[k] > 30 and d[k] != d[k - 1] and d[k] != 0]
        say(f"  raised - shutAgain ({what}) changes sign after 30 s between: "
            + ", ".join(f"{t[k - 1]:.2f}-{t[k]:.2f} s ({'raised above' if d[k] > 0 else 'raised below'})"
                        for k in flips))
    for n in ("shutAgain", "raised"):
        for what, key in (("toddler, 10 s", "toddler_10s_x"), ("room average", "nose_zone_x")):
            v = col[n][key]
            say(f"  {n} {what}: " + ", ".join(
                f"{lim}x ({lab}) first at {t[np.argmax(v >= lim)]:.2f} s = {mmss(t[np.argmax(v >= lim)])}"
                if (v >= lim).any() else f"{lim}x ({lab}) never" for lab, lim in LIMITS))
        r = col[n]["toddler_10s_x"][48:] / col[n]["nose_zone_x"][48:]
        say(f"  {n}: toddler (10 s) / room average over 60-600 s, median {np.median(r):.2f}, "
            f"range {r.min():.2f}-{r.max():.2f}")
        say(f"  {n}: largest cell at 0.6 m {col[n]['nose_zone_max_x'][96:].min():.0f}-"
            f"{col[n]['nose_zone_max_x'][96:].max():.0f}x over 120-600 s")
    a, b = col["raised"]["toddler_10s_x"], col["shutAgain"]["toddler_10s_x"]
    say(f"  at 600 s raised/shutAgain (toddler, 10 s) {a[-1] / b[-1]:.3f}; ten-minute means {a.mean():.2f} "
        f"and {b.mean():.2f}")
    say("")
    say("The room's layers on the mid plane: CO2 as a multiple of normal air, area-weighted over the")
    say("room's cells in each height band, leaving out x 2.2-2.8 m round the table and the cauldron")
    bands = ((0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.55, 0.65), (0.7, 0.8), (0.8, 1.0), (1.0, 1.4), (1.4, 2.0), (2.0, 2.4))
    say("  y, m            " + "".join(f"{f'{y0:g}-{y1:g}':>10s}" for y0, y1 in bands))
    for s in (120, 300, 600):
        for n, run in (("shutAgain", "shut"), ("raised", "raised")):
            mp = pv.read(runs / run / f"postProcessing/planes/{s:g}/mid.vtp")
            cc = mp.cell_centers().points
            X = plane_multiple(mp)
            a = np.asarray(mp.compute_cell_sizes().cell_data["Area"])
            room = (cc[:, 0] > 0) & (cc[:, 1] < 2.4) & ((cc[:, 0] < 2.2) | (cc[:, 0] > 2.8))
            v = [np.average(X[k], weights=a[k]) for k in
                 (room & (cc[:, 1] >= y0) & (cc[:, 1] < y1) for y0, y1 in bands)]
            say(f"  t {s:3d} {n:9s}  " + "".join(f"{x:10.1f}" for x in v))
    say("")
    say("The shut run solved again against the committed shut run")
    for what, key in (("toddler, 10 s", "toddler_10s_x"), ("room average at 0.6 m", "nose_zone_x")):
        a, b = col["shutAgain"][key], first[key]
        late = t >= 120
        say(f"  {what}: largest difference {np.abs(a - b).max():.2f}x; from 120 s largest relative "
            f"{100 * (np.abs(a - b)[late] / b[late]).max():.1f}%, at 600 s {a[-1]:.2f} against {b[-1]:.2f}")
    say("")
    say("The whole room's CO2 budget, g, twice the half model's (residual = gain - in - door - leak)")
    for n in ("shutAgain", "raised"):
        for s in (60, 120, 300, 600):
            r = H[n][int(s * 0.8)]
            say(f"  {n:9s} t {s:4d}  gain {2 * r['gain_g']:8.2f}  in {2 * r['in_g']:8.2f}  door {2 * r['door_g']:6.2f}  "
                f"leak {2 * r['leak_g']:6.2f}  residual {2 * r['residual_g']:6.2f} = {r['residual_g'] / s:.4f} g/s "
                f"in the half model")
    say("")
    say("The outdoor air on the mid plane (x < -0.15 m), speed, m/s")
    for n in ("shutAgain", "raised"):
        for s in (30, 120, 300, 600):
            r = H[n][int(s * 0.8)]
            say(f"  {n:9s} t {s:4d}  median {r['outdoor_speed_median_m_s']:.6f}  largest {r['outdoor_speed_max_m_s']:.4f}")
    (out / "summary_raised.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    if sys.argv[3:] == ["raised"]:
        return raised(runs, out)
    H = {}
    for name in ("shut", "open"):
        H[name] = history(runs / name, name)
        write_csv(out / name / "history.csv", H[name])
    t = np.array([r["t_s"] for r in H["shut"]])
    col = {n: {k: np.array([r[k] for r in H[n]]) for k in H[n][0]} for n in H}
    L = []
    say = L.append
    say("dryIceCauldron: figures from the two runs (scripts/extract_results.py)")
    say("")
    say("CO2 as a multiple of normal air (425 ppm)")
    say("  minute                         1      2      3      5     10   ten-minute mean")
    for what, key in (("at the toddler's nose, 10 s", "toddler_10s_x"), ("toddler, one write", "toddler_x"),
                      ("room average at 0.6 m", "nose_zone_x")):
        for n in ("shut", "open"):
            v = col[n][key]
            say(f"  {n} {what:26s}" + "".join(f"{v[int(m * 48)]:7.1f}" for m in (1, 2, 3, 5, 10))
                + f"   {v.mean():7.1f}")
    for what, key in (("toddler, 10 s", "toddler_10s_x"), ("room average", "nose_zone_x")):
        s, o = col["shut"][key], col["open"][key]
        k = np.argmax((s > o) & (t > 60))
        say(f"  shut passes open ({what}) at {t[k]:.2f} s, and stays above: {bool((s[k:] > o[k:]).all())}")
    for n in ("shut", "open"):
        for what, key in (("toddler, 10 s", "toddler_10s_x"), ("room average", "nose_zone_x")):
            v = col[n][key]
            say(f"  {n} {what}: " + ", ".join(
                f"{lim}x ({lab}) first at {t[np.argmax(v >= lim)]:.2f} s" if (v >= lim).any()
                else f"{lim}x ({lab}) never" for lab, lim in LIMITS))
        r = col[n]["toddler_10s_x"][48:] / col[n]["nose_zone_x"][48:]
        say(f"  {n}: toddler (10 s) / room average over 60-600 s, median {np.median(r):.2f}, "
            f"range {r.min():.2f}-{r.max():.2f}")
    v = col["open"]["toddler_10s_x"]
    late = (t >= 340) & (t <= 600)
    say(f"  open: toddler (10 s) above 35x for {100 * (v[late] > 35).mean():.0f}% of the writes from 340 to 600 s")
    say(f"  largest cell at 0.6 m: shut {col['shut']['nose_zone_max_x'][96:].min():.0f}-"
        f"{col['shut']['nose_zone_max_x'][96:].max():.0f}x, open {col['open']['nose_zone_max_x'][96:].min():.0f}-"
        f"{col['open']['nose_zone_max_x'][96:].max():.0f}x over 120-600 s")
    say("")
    say("The half room's CO2 budget, g (residual = gain - in - door - leak)")
    for n in ("shut", "open"):
        for s in (60, 120, 300, 600):
            k = int(s * 0.8)
            r = H[n][k]
            say(f"  {n} t {s:4d}  gain {r['gain_g']:7.2f}  in {r['in_g']:7.2f}  door {r['door_g']:8.2f}  "
                f"leak {r['leak_g']:6.2f}  residual {r['residual_g']:6.2f} = {r['residual_g'] / s:.4f} g/s")
    say("")
    say("The open doorway: gross flow each way through the whole door, against the doorway formula")
    say("Cd/3 W sqrt(g H^3 dT/T), Cd 0.6, W 0.914 m, H 2.032 m, dT from the room's mean on the mid plane")
    for s in (10, 30, 60, 120, 300, 600):
        r = H["open"][int(s * 0.8)]
        tr = r["room_T_mid_C"]
        q = 0.6 / 3 * 0.914 * np.sqrt(9.81 * 2.032 ** 3 * (tr - 10) / (273.15 + (tr + 10) / 2))
        qin = r["door_in_kg_s"] / 1.24
        say(f"  t {s:4d}  in {r['door_in_kg_s']:.3f}  out {r['door_out_kg_s']:.3f} kg/s, about {qin:.3f} m3/s in; "
            f"room {tr:.1f} C; formula {q:.3f} m3/s; {100 * (qin / q - 1):+.0f}%")
    say("")
    say("The outdoor air on the mid plane (x < -0.15 m), speed, m/s")
    for n in ("shut", "open"):
        for s in (30, 120, 300, 600):
            r = H[n][int(s * 0.8)]
            say(f"  {n} t {s:4d}  median {r['outdoor_speed_median_m_s']:.5f}  largest {r['outdoor_speed_max_m_s']:.4f}")
    (out / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
