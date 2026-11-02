#!/usr/bin/env python3
"""Read the two runs' monitors and write results/.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

reads <runsDir>/ceiling and <runsDir>/floor (their postProcessing/ monitors and the tail of
log.buoyantPimpleFoam) and writes:

- <resultsDir>/<run>/history.csv, every 2.5 s from 0 to 1200 s;
- <resultsDir>/minutes.csv, the occupied zone at every minute, both runs;
- <resultsDir>/summary.txt, the figures the README quotes.

Signs and definitions:
- wallHeatFlux's integral over a patch is the heat leaving the surface into the room, W,
  convection plus net radiation; qr's integral is the net radiation the surface absorbs. The
  convection into the air is their sum, and the net radiation the surface gives is -qr.
- The air's internal energy is (cv/R) times the integral of p dV (the room is closed and the
  air a perfect gas); its rise is compared with the sum of every patch's convection, summed
  over the steps as Euler integrates (right end of each step). Radiation does not heat the
  air, which is transparent.
- The heat a layered wall has taken in is minus the sum over the steps of its wallHeatFlux:
  the layer has an adiabatic back, so all of it is stored there. The glass passes its heat on
  to the outside at h (T - 0 C) A, from its mean surface temperature.
- The mean radiant temperature in a band of the occupied zone is (G / 4 sigma)^(1/4) from the
  band's mean incident radiation G, and the operative temperature is the mean of it and the
  band's mean air temperature. This is the band's mean irradiation, not a seated person's own
  view of the room.
Needs NumPy.
"""
import re
import sys
from pathlib import Path

import numpy as np

SIGMA = 5.670374419e-8
R = 8314.46261815324 / 28.96
CV = 1005 - R
T0, TK = 289.15, 273.15
VOLUME = 33.6
H_GLASS, A_GLASS = 4.403, 1.2
Q = 1400.0
RUNS = ("ceiling", "floor")
PATCHES = ("ceiling", "floor", "glass", "windowWall", "innerWall", "sideWalls")
HEIGHTS = (("ankle", 0.1), ("knee", 0.6), ("head", 1.1), ("standing", 1.7))
END = 1200.0


def table(case, fo, pattern="*.dat"):
    """A function object's rows by time, later time directories (restarts) winning."""
    rows = {}
    base = case / "postProcessing" / fo
    for d in sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: float(p.name)):
        for f in sorted(d.glob(pattern)):
            for line in f.read_text().splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                a = line.split()
                try:
                    rows[float(a[0])] = [float(v) for v in a[1:]]
                except ValueError:
                    pass
    t = np.array(sorted(rows))
    return t, np.array([rows[k] for k in t])


def wall_heat(case):
    rows = {p: {} for p in PATCHES}
    base = case / "postProcessing" / "wallHeatFlux"
    for d in sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: float(p.name)):
        for f in d.glob("*.dat"):
            for line in f.read_text().splitlines():
                a = line.split()
                if len(a) == 5 and a[1] in rows:
                    rows[a[1]][float(a[0])] = float(a[4])
    return {p: np.array(sorted(v.items())) for p, v in rows.items()}


def wall_time(case):
    log = case / "log.buoyantPimpleFoam"
    if not log.exists():
        return None
    with open(log, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 20000))
        tail = f.read().decode(errors="replace")
    m = re.findall(r"ExecutionTime = ([\d.]+) s\s+ClockTime = ([\d.]+) s", tail)
    return float(m[-1][1]) if m else None


def crossing(t, y, level):
    """The first time y reaches level and stays at or above it to the end, or None."""
    below = np.nonzero(y < level)[0]
    if len(below) == 0:
        return t[0]
    i = below[-1]
    if i == len(y) - 1:
        return None
    return float(t[i] + (level - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))


def first_crossing(t, y, level):
    i = np.nonzero(y >= level)[0]
    if len(i) == 0:
        return None
    i = i[0]
    if i == 0:
        return float(t[0])
    return float(t[i - 1] + (level - y[i - 1]) * (t[i] - t[i - 1]) / (y[i] - y[i - 1]))


def analyse(case, run):
    te, e = table(case, "energyCheck")
    t = te[te <= END + 1e-9]
    dt = np.diff(np.r_[0.0, t])
    U = e[: len(t), 0] * CV / R
    whf = wall_heat(case)
    total = {p: np.interp(t, whf[p][:, 0], whf[p][:, 1]) for p in PATCHES}
    qr = {}
    for p in PATCHES:
        tq, a = table(case, "qr_" + p)
        qr[p] = np.interp(t, tq, a[:, 0])
    conv = {p: total[p] + qr[p] for p in PATCHES}
    convsum = sum(conv.values())
    E0 = 1e5 * VOLUME * CV / R
    stored = U[-1] - E0
    supplied = float(np.sum(dt * convsum))
    d = dict(run=run, t=t, steps=len(t), end=float(t[-1]), dt=dt, total=total, qr=qr, conv=conv,
             stored_J=stored, conv_J=supplied, gap_W=(stored - supplied) / t[-1],
             qr_sum=sum(qr.values()), U=U, E0=E0)
    d["wall_s"] = wall_time(case)
    # heat into each surface over the run, J (minus the integral of its wallHeatFlux)
    d["into_J"] = {p: float(-np.sum(dt * total[p])) for p in PATCHES}
    d["conv_mean_W"] = {p: float(np.sum(dt * conv[p]) / t[-1]) for p in PATCHES}
    d["rad_out_mean_W"] = {p: float(np.sum(dt * -qr[p]) / t[-1]) for p in PATCHES}
    d["total_mean_W"] = {p: float(np.sum(dt * total[p]) / t[-1]) for p in PATCHES}
    # glass to outside
    tg, g = table(case, "glassIntT")
    gl = H_GLASS * (np.interp(t, tg, g[:, 0]) - TK * A_GLASS)
    d["glass_out_J"] = float(np.sum(dt * gl))
    d["glass_out_W"] = gl
    # every-step monitors
    for fo in ("roomMeanT", "T_ceilingMean", "T_ceilingMax", "T_ceilingMin", "T_floorMean",
               "T_floorMax", "T_floorMin", "surfaceT"):
        tt, a = table(case, fo)
        d[fo] = (tt, a[:, 0])
    for name, _ in HEIGHTS:
        tt, a = table(case, "occ_" + name)
        d["occ_" + name] = (tt, a[:, 0])
        tt, a = table(case, "comfort_" + name)
        d["comfort_" + name] = (tt, a[:, 0], a[:, 1])
    tp, a = table(case, "probes", "T")
    d["probes"] = (tp, a)
    return d


def at(series, time):
    t, y = series[0], series[1]
    return float(np.interp(time, t, y))


def comfort(d, name, time):
    t, T, G = d["comfort_" + name]
    if time <= 0:
        return T0, T0, T0
    i = int(np.argmin(abs(t - time)))
    Tmr = (G[i] / (4 * SIGMA)) ** 0.25
    return T[i], Tmr, (T[i] + Tmr) / 2


def history(d, out):
    times = np.arange(0, END + 1e-9, 2.5)
    cols = {"t_s": times}
    for name, _ in HEIGHTS:
        T, Tmr, Top = zip(*(comfort(d, name, s) for s in times))
        cols[f"T_{name}_C"] = np.array(T) - TK
        cols[f"Tmr_{name}_C"] = np.array(Tmr) - TK
        cols[f"Toperative_{name}_C"] = np.array(Top) - TK
    cols["head_minus_ankle_K"] = cols["T_head_C"] - cols["T_ankle_C"]

    def every(key, label):
        tt, y = d[key]
        cols[label] = np.where(times > 0, np.interp(times, tt, y), T0) - TK

    every("roomMeanT", "T_room_C")
    every("surfaceT", "T_glass_surface_C")
    for p in ("ceiling", "floor"):
        for o in ("Mean", "Max"):
            every(f"T_{p}{o}", f"T_{p}_surface_{o.lower()}_C")
    t = d["t"]

    def at_steps(y):
        return np.where(times > 0, np.interp(times, t, y), np.nan)

    heated = d["run"]
    cols["heated_convection_W"] = at_steps(d["conv"][heated])
    cols["heated_radiation_out_W"] = at_steps(-d["qr"][heated])
    cols["glass_to_outside_W"] = at_steps(d["glass_out_W"])
    cols["air_internal_energy_rise_kJ"] = np.where(times > 0, np.interp(times, t, d["U"] - d["E0"]), 0) / 1e3
    cum = {p: np.r_[0, np.cumsum(d["dt"] * -d["total"][p])] for p in PATCHES}
    tc = np.r_[0, t]
    for p in PATCHES:
        if p in ("glass", heated):
            continue
        cols[f"heat_into_{p}_kJ"] = np.interp(times, tc, cum[p]) / 1e3
    keys = list(cols)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "history.csv", "w") as f:
        f.write(",".join(keys) + "\n")
        for i in range(len(times)):
            f.write(",".join("" if np.isnan(cols[k][i]) else
                             (f"{cols[k][i]:g}" if k == "t_s" else f"{cols[k][i]:.4f}")
                             for k in keys) + "\n")


def main(runs, results):
    runs, results = Path(runs), Path(results)
    D = {r: analyse(runs / r, r) for r in RUNS}
    for r in RUNS:
        history(D[r], results / r)
    with open(results / "minutes.csv", "w") as f:
        f.write("run,t_s,T_ankle_C,T_head_C,Toperative_ankle_C,Toperative_head_C,T_room_C\n")
        for r in RUNS:
            for s in range(0, int(END) + 1, 60):
                a, h = comfort(D[r], "ankle", s), comfort(D[r], "head", s)
                room = at(D[r]["roomMeanT"], s) if s > 0 else T0
                f.write(f"{r},{s},{a[0] - TK:.2f},{h[0] - TK:.2f},{a[2] - TK:.2f},{h[2] - TK:.2f},{room - TK:.2f}\n")

    L = ["ceilingVsUnderfloor: figures from the two runs' monitors (scripts/extract_results.py)",
         "1400 W through the whole ceiling or the whole floor from a 16 C start, 0-1200 s", ""]
    for r in RUNS:
        d = D[r]
        w = d["wall_s"]
        L.append(f"{r}: to t = {d['end']:g} s in {d['steps']} steps, mean step {d['end'] / d['steps']:.4f} s"
                 + (f", {w:.0f} s of wall time ({w / 3600:.2f} h)" if w else ""))
    L += ["", "Occupied zone at 1200 s, C (air; mean radiant (G/4 sigma)^1/4; operative = their mean)",
          "  run       height          air    radiant  operative"]
    for r in RUNS:
        for name, y in HEIGHTS:
            T, Tmr, Top = comfort(D[r], name, END)
            L.append(f"  {r:8s}  {name:8s} {y:3.1f} m  {T - TK:6.2f}   {Tmr - TK:6.2f}   {Top - TK:6.2f}")
    L += ["", "Air in the occupied zone over time, C (every-step band means)",
          "  t s     ceiling ankle  head    floor ankle  head"]
    for s in (60, 120, 300, 410, 600, 900, 1200):
        row = []
        for r in RUNS:
            row += [at(D[r]["occ_ankle"], s) - TK, at(D[r]["occ_head"], s) - TK]
        L.append(f"  {s:5d}   {row[0]:12.2f} {row[1]:5.2f}   {row[2]:11.2f} {row[3]:5.2f}")
    L.append("  head minus ankle at 1200 s: " + ", ".join(
        f"{r} {at(D[r]['occ_head'], END) - at(D[r]['occ_ankle'], END):+.2f} K" for r in RUNS))
    L.append("  room mean at 1200 s: " + ", ".join(f"{r} {at(D[r]['roomMeanT'], END) - TK:.2f} C" for r in RUNS))
    for r in RUNS:
        for name in ("ankle", "head"):
            tt, y = D[r]["occ_" + name]
            c = crossing(tt, y, TK + 20)
            L.append(f"  {r} {name} air reaches 20 C and stays: " + (f"{c:.0f} s" if c is not None else "not by 1200 s")
                     + f" (max {y.max() - TK:.2f} C)")
    for r in RUNS:
        tt = D[r]["occ_ankle"][0]
        both = np.minimum(D[r]["occ_ankle"][1], D[r]["occ_head"][1])
        c = crossing(tt, both, TK + 20)
        L.append(f"  {r} ankle and head both at 20 C or more from: " + (f"{c:.0f} s" if c is not None else "not by 1200 s"))
    for r in RUNS:
        for name in ("ankle", "head"):
            tt, T, G = D[r]["comfort_" + name]
            op = (T + (G / (4 * SIGMA)) ** 0.25) / 2
            c = crossing(tt, op, TK + 20)
            L.append(f"  {r} operative temperature at the {name} reaches 20 C and stays: "
                     + (f"{c:.0f} s" if c is not None else "not by 1200 s"))
    L.append(f"  floor ankle air: {at(D['floor']['occ_ankle'], 30) - TK:.2f} C at 30 s, "
             f"{at(D['floor']['occ_ankle'], 60) - TK:.2f} C at 60 s")
    tp, a = D["ceiling"]["probes"]
    L.append(f"  ceiling run, probe at x 2.0 m, y 2.2 m (0.2 m under the ceiling): {a[-1, 7] - TK:.2f} C at {tp[-1]:g} s")

    L += ["", "Surfaces, C (area means; max the warmest face)"]
    for r in RUNS:
        other = "floor" if r == "ceiling" else "ceiling"
        for s in (60, 300, 600, 1200):
            L.append(f"  {r:8s} {s:5d} s  heated {r} {at(D[r]['T_' + r + 'Mean'], s) - TK:6.2f} (max {at(D[r]['T_' + r + 'Max'], s) - TK:6.2f})"
                     f"   {other} {at(D[r]['T_' + other + 'Mean'], s) - TK:6.2f} (max {at(D[r]['T_' + other + 'Max'], s) - TK:6.2f})"
                     f"   glass {at(D[r]['surfaceT'], s) - TK:6.2f}")
    tt, y = D["floor"]["T_floorMean"]
    c1 = first_crossing(tt, y, TK + 29)
    c2 = crossing(tt, y, TK + 29)
    L.append(f"  floor run: the heated floor's mean first reaches 29 C at {c1:.2f} s and stays at or above it from {c2:.2f} s"
             f" (min after 1 s {y[tt > 1].min() - TK:.2f} C at {tt[tt > 1][np.argmin(y[tt > 1])]:.1f} s)")
    s20 = crossing(*D["floor"]["occ_ankle"], TK + 20)
    L.append(f"  floor run at {s20:.0f} s, when the ankle air reaches 20 C: floor mean {at(D['floor']['T_floorMean'], s20) - TK:.2f} C, "
             f"max {at(D['floor']['T_floorMax'], s20) - TK:.2f} C, room mean air {at(D['floor']['roomMeanT'], s20) - TK:.2f} C")

    L += ["", "The heated surface, W (convection into the air / net radiation given out / the two together)"]
    for r in RUNS:
        d = D[r]
        cm, rm, tm = d["conv_mean_W"][r], d["rad_out_mean_W"][r], d["total_mean_W"][r]
        L.append(f"  {r:8s} run mean {cm:7.1f} / {rm:7.1f} / {tm:7.1f}  ({rm / tm * 100:.1f}% radiation)")
        L.append(f"  {r:8s} at 1200 s {d['conv'][r][-1]:7.1f} / {-d['qr'][r][-1]:7.1f} / {d['total'][r][-1]:7.1f}")
    L += ["", "Where the 1.68 MJ went by 1200 s, MJ (heat each surface took from the room; the air's rise)"]
    for r in RUNS:
        d = D[r]
        parts = [(p, d["into_J"][p]) for p in PATCHES if p not in ("glass", r)]
        layers = sum(v for _, v in parts)
        L.append(f"  {r:8s} " + ", ".join(f"{p} {v / 1e6:.3f}" for p, v in parts)
                 + f"; layers {layers / 1e6:.3f} ({layers / (Q * END) * 100:.0f}%)")
        L.append(f"           air {d['stored_J'] / 1e6:.3f} ({d['stored_J'] / (Q * END) * 100:.1f}%), "
                 f"glass to outside {d['glass_out_J'] / 1e6:.3f} (glass wallHeatFlux {-d['into_J']['glass'] / 1e6:.3f}), "
                 f"heated surface gave {-d['into_J'][r] / 1e6:.4f} of {Q * END / 1e6:.2f}")
        L.append(f"           sum of air, layers and glass {(d['stored_J'] + layers + d['glass_out_J']) / 1e6:.4f}")
    L += ["", "The air's heat budget over 0-1200 s (rise of (cv/R) int p dV against the sum of convection)"]
    for r in RUNS:
        d = D[r]
        L.append(f"  {r:8s} stored {d['stored_J'] / END:7.2f} W, convected in {d['conv_J'] / END:7.2f} W, gap {d['gap_W']:+.3f} W")
        L.append(f"           sum of qr over all walls: run mean {np.sum(d['dt'] * d['qr_sum']) / END:+.3f} W, "
                 f"at 1200 s {d['qr_sum'][-1]:+.3f} W")
    (results / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
