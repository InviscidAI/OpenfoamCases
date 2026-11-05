#!/usr/bin/env python3
"""Write results/ from the two solved runs' monitors and the radiator's log.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

reads <runsDir>/fan and <runsDir>/oilHot (each a solved run as ./Allrun leaves it) and writes

- <resultsDir>/fan/history.csv and <resultsDir>/oilHot/history.csv, every 2.5 s from 0 to 300 s:
  the heat going into the room, the room's mean air, the occupied zone's four bands (ankle 0.1 m,
  knee 0.6 m, seated head 1.1 m, standing head 1.7 m, more than 1.0 m from the window wall and
  0.3 m from the others), the glass's mean surface temperature and the coldest and hottest air.
  The fan heater's heat is what its air carries away from the element, mass flow x cp x (outlet
  - intake), from the flow_outlet, flowT_outlet and flowT_intake monitors. The radiator's is
  radiatorLumped's own record at every step in log.buoyantPimpleFoam, Qconv (the fins' face flux
  kappaEff dT/dn) + Qrad (minus the integral of qr over the fins), interpolated to the time; its
  first line comes before the first radiation solve (Qrad -0) and is left out.
- <resultsDir>/minutes.csv: the table in the README, at 5, 60, 120, 180, 240 and 300 s.
- <resultsDir>/summary.txt: steps, the heat over the five minutes, the radiator's split and the
  bounds on the radiator run's air, from its every-step monitors.
"""
import sys
from pathlib import Path

import numpy as np

trapezoid = getattr(np, "trapezoid", None) or np.trapz

CP = 1005.0             # constant/thermophysicalProperties
K = 273.15
T_END = 300.0
EVERY = 2.5
MINUTES = (5, 60, 120, 180, 240, 300)


def dat(run, name):
    """A monitor's columns as floats (the time first), from postProcessing/<name>/0/."""
    f = next((run / "postProcessing" / name / "0").glob("*.dat"))
    rows = [l.split() for l in open(f) if l.strip() and not l.startswith("#")]
    return np.array(rows, dtype=float)


def minmax_T(run):
    rows = [l.split() for l in open(run / "postProcessing/minMax/0/fieldMinMax.dat")
            if l.strip() and not l.startswith("#") and l.split()[1] == "T"]
    return np.array([[float(r[0]), float(r[2]), float(r[7])] for r in rows])  # location(min) is three words


def at(t, ts, v):
    if ts[-1] < t[-1] - 1e-6:
        raise SystemExit(f"a record ends at {ts[-1]} s, before {t[-1]} s")
    return np.interp(t, ts, v)


def log_info(run):
    """Steps, the last time and the wall time, from log.buoyantPimpleFoam, read line by line."""
    steps, last, wall, radiator = 0, None, None, []
    with open(run / "log.buoyantPimpleFoam") as f:
        for l in f:
            if l.startswith("Time = "):
                steps += 1
                last = float(l.split()[2])
            elif l.startswith("ExecutionTime"):
                wall = float(l.split()[6])
            elif l.startswith("radiatorLumped:"):
                w = l.split()
                radiator.append((float(w[2]), float(w[4]), float(w[6]), float(w[8])))
    return steps, last, wall, np.array(radiator) if radiator else None


def common(run, t):
    cols = {}
    for name, key in (("roomMeanT", "T_room_C"), ("occ_ankle", "T_ankle_C"), ("occ_knee", "T_knee_C"),
                      ("occ_head", "T_head_C"), ("occ_standing", "T_standing_C"), ("T_glass", "T_glass_surface_C")):
        d = dat(run, name)
        cols[key] = np.r_[289.15, at(t[1:], d[:, 0], d[:, 1])] - K
    mm = minmax_T(run)
    cols["T_air_min_C"] = np.r_[289.15, at(t[1:], mm[:, 0], mm[:, 1])] - K
    cols["T_air_max_C"] = np.r_[289.15, at(t[1:], mm[:, 0], mm[:, 2])] - K
    return cols


def write_csv(path, t, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(cols)
    with open(path, "w") as f:
        f.write("t_s," + ",".join(keys) + "\n")
        for i, ti in enumerate(t):
            vals = []
            for k in keys:
                v = cols[k][i]
                vals.append("" if np.isnan(v) else f"{v:.4f}")
            f.write(f"{ti:g}," + ",".join(vals) + "\n")


def main(runs, out):
    runs, out = Path(runs), Path(out)
    t = np.arange(0, T_END + 1e-9, EVERY)
    fan, oil = runs / "fan", runs / "oilHot"
    lines = ["fanHeaterVsOilRadiator: figures from the two runs' monitors and the radiator's log "
             "(scripts/extract_results.py)",
             "ceilingVsUnderfloor's room from a 16 C setback on a still 0 C morning, 0-300 s", ""]

    # the fan heater: what its air carries off the element
    m, To, Ti = dat(fan, "flow_outlet"), dat(fan, "flowT_outlet"), dat(fan, "flowT_intake")
    n = min(len(m), len(To), len(Ti))
    if not (np.allclose(m[:n, 0], To[:n, 0]) and np.allclose(m[:n, 0], Ti[:n, 0])):
        raise SystemExit("the fan's monitors are not on one time base")
    tf, Qf = m[:n, 0], np.abs(m[:n, 1]) * CP * (To[:n, 1] - Ti[:n, 1])
    fc = {"heat_into_room_W": np.r_[np.nan, at(t[1:], tf, Qf)],
          "mass_flow_kg_s": np.r_[np.nan, at(t[1:], tf, np.abs(m[:n, 1]))],
          "T_intake_C": np.r_[np.nan, at(t[1:], tf, Ti[:n, 1] - K)],
          "T_outlet_C": np.r_[np.nan, at(t[1:], tf, To[:n, 1] - K)]}
    fc.update(common(fan, t))
    write_csv(out / "fan" / "history.csv", t, fc)
    # the element is on from the first step: the first 0.625 s at the first monitor's value
    Ef = (trapezoid(Qf[tf <= T_END], tf[tf <= T_END]) + Qf[0] * tf[0]) / 1e3

    # the radiator: its own record at every step
    steps_o, last_o, wall_o, r = log_info(oil)
    r = r[r[:, 3] != 0]                     # the first line precedes the first radiation solve
    to, Qc, Qr = r[:, 0], r[:, 2], r[:, 3]
    oc = {"heat_into_room_W": at(t, to, Qc + Qr), "convection_W": at(t, to, Qc), "radiation_W": at(t, to, Qr),
          "T_fins_C": at(t, to, r[:, 1]) - K}
    oc.update(common(oil, t))
    write_csv(out / "oilHot" / "history.csv", t, oc)
    Eo = (trapezoid(Qc + Qr, to) + (Qc[0] + Qr[0]) * to[0]) / 1e3

    # the table in the README
    tm = np.array(MINUTES, float)
    with open(out / "minutes.csv", "w") as f:
        f.write("t_s,fan_heat_W,oil_heat_W,oil_radiation_W,fan_T_room_C,oil_T_room_C,fan_T_ankle_C,oil_T_ankle_C\n")
        for ti in tm:
            vals = [np.interp(ti, tf, Qf), np.interp(ti, to, Qc + Qr), np.interp(ti, to, Qr)]
            vals += [np.interp(ti, d[:, 0], d[:, 1]) - K for d in
                     (dat(fan, "roomMeanT"), dat(oil, "roomMeanT"), dat(fan, "occ_ankle"), dat(oil, "occ_ankle"))]
            f.write(f"{ti:g}," + ",".join(f"{v:.2f}" for v in vals) + "\n")

    steps_f, last_f, wall_f, _ = log_info(fan)
    for name, steps, last, wall in (("fan", steps_f, last_f, wall_f), ("oilHot", steps_o, last_o, wall_o)):
        lines.append(f"{name}: to t = {last:g} s in {steps} steps, mean step {last / steps:.4f} s, "
                     f"{wall:.0f} s of wall time ({wall / 3600:.2f} h)")
    lines.append("")
    lines.append("Heat into the room, W (fan: mass flow x cp x (outlet - intake); radiator: Qconv + Qrad)")
    lines.append("  t s      fan   radiator  of which radiation")
    for ti in tm:
        lines.append(f"  {ti:5g} {np.interp(ti, tf, Qf):8.1f} {np.interp(ti, to, Qc + Qr):10.1f} "
                     f"{np.interp(ti, to, Qr):19.1f}")
    lines.append(f"  radiator's first logged step, t = {to[0]:.4g} s: {Qc[0] + Qr[0]:.1f} W "
                 f"({Qc[0]:.1f} convection, {Qr[0]:.1f} radiation)")
    k = np.searchsorted(to, T_END) - 1
    lines.append(f"  radiator at 300 s: {Qc[k]:.1f} W convection + {Qr[k]:.1f} W radiation, "
                 f"{100 * Qr[k] / (Qc[k] + Qr[k]):.1f}% radiant")
    late = tf >= 10
    lines.append(f"  fan heater over 10-300 s: {Qf[late].mean():.1f} W mean, {Qf[late].min():.1f}-{Qf[late].max():.1f}")
    lines.append(f"  heat over 0-300 s: fan heater {Ef:.1f} kJ, radiator {Eo:.1f} kJ")
    lines.append("")
    lines.append("Air, C (room: mean of every cell; bands as in the README)")
    lines.append("  t s     room fan  room rad  ankle fan  ankle rad  head fan  head rad")
    for ti in tm:
        v = [np.interp(ti, d[:, 0], d[:, 1]) - K for d in
             (dat(fan, "roomMeanT"), dat(oil, "roomMeanT"), dat(fan, "occ_ankle"), dat(oil, "occ_ankle"),
              dat(fan, "occ_head"), dat(oil, "occ_head"))]
        lines.append(f"  {ti:5g} " + " ".join(f"{x:9.2f}" for x in v))
    lines.append("")

    # the radiator run's every-step bounds (the regrade's checks)
    lo, hi = dat(oil, "Tair_min"), dat(oil, "Tair_max")
    g, rad, front = dat(oil, "Tmin_glass"), dat(oil, "Tmax_radiator"), dat(oil, "front_min")
    n = min(len(lo), len(hi), len(g), len(rad), len(front))
    below = int(np.sum(lo[:n, 1] < g[:n, 1] - 1e-9))
    above = int(np.sum(hi[:n, 1] > rad[:n, 1] + 1e-9))
    lines.append(f"oilHot, every step ({n} monitor rows):")
    lines.append(f"  air {lo[:n, 1].min() - K:.2f} to {hi[:n, 1].max() - K:.2f} C; glass's coldest face at least "
                 f"{g[:n, 1].min() - K:.2f} C; fins {rad[:n, 1].min() - K:.3f} to {rad[:n, 1].max() - K:.3f} C")
    lines.append(f"  steps with air colder than the glass's coldest face: {below}; hotter than the fins: {above}")
    lines.append(f"  air in front of the heater (frontOfHeater zone) never below {front[:n, 1].min() - K:.2f} C")
    mm = minmax_T(fan)
    lines.append(f"fan, every 0.625 s: air {mm[:, 1].min() - K:.2f} to {mm[:, 2].max() - K:.2f} C")
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
