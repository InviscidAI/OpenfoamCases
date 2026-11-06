"""The results of the wet towel case from the solved runs' monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

Reads, in <runsDir>/bare and <runsDir>/clothes, postProcessing/heatAccounting/heat.csv (every step),
postProcessing/diagnostics60/diagnostics.csv (every second), postProcessing/wetWalls/wet_0.dat
(every 20 steps) and postProcessing/wetWalls/faces_0.dat (each glass face's film and temperature,
each towel node's temperature and water, every 1.25 s), and writes

  <resultsDir>/<run>/history.csv  every 2.5 s: the radiator's heat, the heat that has reached the
                                  room, the room's air, the water, the window, the plume
  <resultsDir>/minutes.csv        both runs minute by minute and the towel's shares
  <resultsDir>/summary.txt        the numbers the README quotes

All per metre of section (the section is 1 m deep). Definitions:

- The radiator's heat is the panel's convection and radiation plus what the convector zone gives
  its air (the enthalpy and diffusion leaving the zone and the change in the zone's own energy), as
  radiatorCover measured it, from heat.csv; the first step's change in the zone's energy is taken
  from the hydrostatic rest state.
- The heat that has reached the room is the radiator's heat less what the towel has kept warming
  itself (the heat it took from the air and from radiation less the latent heat it paid) and less
  the latent heat still held in vapour and not given back where it condensed on the glass. In the
  bare run it is the radiator's heat.
- wetWalls wrote the glass's cumulative latent heat on the master rank only, which holds no glass
  faces, so its column is zero. It is recovered here, as the solved runs' accounting did, from the
  film on each glass face at each 1.25 s write, times the face's area and the latent heat at the
  mean of the face's temperatures at the two writes. At the 60 s field writes this agrees with
  the sum of the ranks' own saved totals to 0.00025 J/m.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_case  # noqa: E402  (the grid: x, y)

RUNS = ("bare", "clothes")
T0 = 289.15
WET = ("t clothTm clothTmin clothTmax water evap qLat qAir qRad evapCum latCum airCum radCum glassT "
       "glassFilm glassWet condRate condCum glassLatCum qGlassOut qGlassAir vap airMass meanT").split()
SHEET = 1.0473  # m2 of towel per metre: half its faces' area


def read_csv(p):
    d = np.atleast_1d(np.genfromtxt(p, delimiter=",", names=True))
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def cumul(t, q):
    return np.cumsum(np.diff(np.r_[0, t]) * q)


def hs0():
    """The starting mixture's sensible enthalpy at 16 C, J/kg (JANAF, from 298.15 K)."""
    co = [(31.9988, .2315 * (1 - .00695), [3.21294, .00112749, -5.75615e-7, 1.31388e-9, -8.76855e-13]),
          (28.0134, .7685 * (1 - .00695), [3.29868, .00140824, -3.96322e-6, 5.64152e-9, -2.44486e-12]),
          (18.0153, .00695, [3.38684, .00347498, -6.3547e-6, 6.96858e-9, -2.50659e-12])]
    return sum(fr * make_case.RU / mw * sum(a * (T0 ** (j + 1) - 298.15 ** (j + 1)) / (j + 1) for j, a in enumerate(c))
               for mw, fr, c in co)


def zone_rest():
    """The convector zone's internal energy and mass at rest: sum (rho hs - p) V and sum rho V."""
    x, y = make_case.x, make_case.y
    xc, yc = (x[1:] + x[:-1]) / 2, (y[1:] + y[:-1]) / 2
    i = np.where((xc > .04) & (xc < .103))[0]
    j = np.where((yc > .15) & (yc < .75))[0]
    I, J = np.meshgrid(i, j)
    v = (np.diff(x)[I] * np.diff(y)[J]).ravel()
    p = 1e5 * np.exp(-9.81 * (yc[J].ravel() - 1.174) / (make_case.R * T0))
    rho = p / (make_case.R * T0)
    return float(sum((rho * hs0() - p) * v)), float(sum(rho * v))


def radiator(d):
    """The radiator's heat, W/m every step and J/m so far."""
    t = d["time"]
    dt = np.diff(np.r_[0, t])
    ez = d["Uzone"] - 1005 * T0 * d["zoneMass"]
    qz = d["zoneEnthalpy"] + d["zoneDiffusion"] + np.r_[0, np.diff(ez)] / dt + np.r_[0, np.diff(d["KEzone"])] / dt
    q = qz + d["panelConvection"] + d["panelRadiation"]
    e0, m0 = zone_rest()
    first = d["Uzone"][0] - 1005 * T0 * d["zoneMass"][0] - (e0 - 1005 * T0 * m0) + d["KEzone"][0]
    return q, cumul(t, q) + first


def wet(case):
    a = np.atleast_2d(np.loadtxt(case / "postProcessing/wetWalls/wet_0.dat"))
    return {k: a[:, i] for i, k in enumerate(WET)}


def glass(case):
    """The glass's film by face at each 1.25 s write, and the latent heat given back so far, J/m."""
    rows = np.array([list(map(float, line.split()[1:])) for line in
                     (case / "postProcessing/wetWalls/faces_0.dat").read_text().splitlines() if line.startswith("glass ")])
    times = np.unique(rows[:, 0])
    frames = []
    for t in times:
        f = rows[rows[:, 0] == t]
        frames.append(f[np.argsort(f[:, 1])])
    heights = frames[0][:, 1]
    assert all(len(f) == len(heights) and np.allclose(f[:, 1], heights) for f in frames), "glass rows are not whole writes"
    y = make_case.y
    area = np.diff(y)[np.searchsorted(y, heights) - 1]
    assert np.isclose(area.sum(), 1.2), area.sum()
    film = np.array([f[:, 2] for f in frames])
    T = np.array([f[:, 3] for f in frames])
    L = 2.501e6 - 2370 * (T - 273.15)
    q = np.r_[0, np.cumsum(np.sum(np.diff(film, axis=0) * (.5 * (L[1:] + L[:-1])) * area, axis=1))]
    return times, heights, area, film, q


def load(case):
    d = read_csv(case / "postProcessing/heatAccounting/heat.csv")
    g = read_csv(case / "postProcessing/diagnostics60/diagnostics.csv")
    w = wet(case)
    tg, heights, area, film, glat = glass(case)
    w["glassLatCum"] = np.interp(w["t"], tg, glat)
    q, E = radiator(d)
    keep = w["airCum"] + w["radCum"] - w["latCum"]   # what the towel kept warming itself
    held = w["latCum"] - w["glassLatCum"]            # latent heat still in the vapour
    room = E - np.interp(d["time"], w["t"], keep + held)
    return dict(d=d, g=g, w=w, t=d["time"], q=q, E=E, room=room, keep=keep, held=held,
                tg=tg, heights=heights, area=area, film=film)


def at(r, s):
    """Everything at time s, by linear interpolation in each monitor's own times."""
    t, g, w = r["t"], r["g"], r["w"]

    def it(ts, a):
        return float(np.interp(s, ts, a))

    t0 = np.r_[0.0, t]  # nothing given before the first step
    k = int(np.argmin(abs(r["tg"] - s)))
    return dict(
        t_s=s, radiator_W=it(t, r["q"]), radiator_kJ=it(t0, np.r_[0.0, r["E"]]) / 1e3,
        room_kJ=it(t0, np.r_[0.0, r["room"]]) / 1e3,
        towelKept_kJ=it(w["t"], r["keep"]) / 1e3, latentHeld_kJ=it(w["t"], r["held"]) / 1e3,
        room_C=it(g["time"], g["roomT_K"]) - 273.15, roomRH_pct=100 * it(g["time"], g["roomRH"]),
        airMin_C=it(g["time"], g["airMin_K"]) - 273.15, airMax_C=it(g["time"], g["airMax_K"]) - 273.15,
        evaporated_g=1e3 * it(w["t"], w["evapCum"]), condensed_g=1e3 * it(w["t"], w["condCum"]),
        airWater_g=1e3 * (it(w["t"], w["vap"]) - w["vap"][0]), glassWater_g=1e3 * it(w["t"], w["glassFilm"]),
        misted_pct=100 * float(np.sum(r["area"][r["film"][k] > 1e-4]) / r["area"].sum()),
        glass_C=it(w["t"], w["glassT"]) - 273.15,
        towel_C=it(w["t"], w["clothTm"]) - 273.15, towelWater_kgm2=it(w["t"], w["water"]),
        drying_g_m2h=it(w["t"], w["evap"]) / SHEET * 3.6e6,
        plumeUp_lps=1e3 * it(g["time"], g["up_m3s"]), plumeUp_W=it(g["time"], g["up_W"]),
    )


COLUMNS = [("t_s", "{:.2f}"), ("radiator_W", "{:.2f}"), ("radiator_kJ", "{:.3f}"), ("room_kJ", "{:.3f}"),
           ("towelKept_kJ", "{:.3f}"), ("latentHeld_kJ", "{:.3f}"), ("room_C", "{:.3f}"), ("roomRH_pct", "{:.2f}"),
           ("airMin_C", "{:.2f}"), ("airMax_C", "{:.2f}"), ("evaporated_g", "{:.3f}"), ("condensed_g", "{:.3f}"),
           ("airWater_g", "{:.3f}"), ("glassWater_g", "{:.3f}"), ("misted_pct", "{:.1f}"), ("glass_C", "{:.3f}"),
           ("towel_C", "{:.3f}"), ("towelWater_kgm2", "{:.5f}"), ("drying_g_m2h", "{:.1f}"),
           ("plumeUp_lps", "{:.2f}"), ("plumeUp_W", "{:.2f}")]


def write_csv(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(",".join(c for c, _ in cols) + "\n")
        for row in rows:
            f.write(",".join("" if not np.isfinite(row[c]) else fmt.format(row[c] + 0.0).replace("-0.000", "0.000") for c, fmt in cols) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", type=Path)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    R = {run: load(a.runs / run) for run in RUNS}
    end = min(float(min(r["t"][-1], r["g"]["time"][-1], r["w"]["t"][-1], r["tg"][-1])) for r in R.values())
    end = 2.5 * round(end / 2.5)  # the monitors stop within a step of 600 s
    for run, r in R.items():
        rows = [at(r, s) for s in np.arange(0, end + 1e-9, 2.5)]
        for c in ("radiator_W", "plumeUp_lps", "plumeUp_W"):  # the first step's start-up spike, not a rate
            rows[0][c] = float("nan")
        for row in rows:
            row["airWater_g"] += 0.0
            if run == "bare":  # no towel
                for c in ("towel_C", "towelWater_kgm2", "drying_g_m2h"):
                    row[c] = float("nan")
        write_csv(a.out / run / "history.csv", rows, COLUMNS)
    b, c = R["bare"], R["clothes"]
    minutes = []
    prev = {run: at(R[run], 0) for run in RUNS}
    for s in range(60, int(end) + 1, 60):
        B, C = at(b, s), at(c, s)
        minutes.append(dict(
            t_s=s, bareRadiator_kJ=B["radiator_kJ"], towelRadiator_kJ=C["radiator_kJ"],
            radiatorShare_pct=100 * C["radiator_kJ"] / B["radiator_kJ"],
            bareRoom_kJ=B["room_kJ"], towelRoom_kJ=C["room_kJ"], roomShare_pct=100 * C["room_kJ"] / B["room_kJ"],
            bareRoomThisMinute_W=(B["room_kJ"] - prev["bare"]["room_kJ"]) * 1e3 / 60,
            towelRoomThisMinute_W=(C["room_kJ"] - prev["clothes"]["room_kJ"]) * 1e3 / 60,
            towelRadiatorThisMinute_W=(C["radiator_kJ"] - prev["clothes"]["radiator_kJ"]) * 1e3 / 60,
            bareRoom_C=B["room_C"], towelRoom_C=C["room_C"], bareRH_pct=B["roomRH_pct"], towelRH_pct=C["roomRH_pct"],
            evaporated_g=C["evaporated_g"], airWater_g=C["airWater_g"], glassWater_g=C["glassWater_g"],
            towelMisted_pct=C["misted_pct"], bareMisted_pct=B["misted_pct"]))
        minutes[-1]["roomShareThisMinute_pct"] = 100 * minutes[-1]["towelRoomThisMinute_W"] / minutes[-1]["bareRoomThisMinute_W"]
        prev = dict(bare=B, clothes=C)
    mcols = [(k, "{:.3f}" if k.endswith(("kJ", "_g")) else "{:.2f}") for k in minutes[0] if k != "t_s"]
    write_csv(a.out / "minutes.csv", minutes, [("t_s", "{:.0f}")] + mcols)

    B, C = at(b, end), at(c, end)
    # the first time the glass holds 0.1 g/m2 of water over half its height, and over all of it
    def mist(r, share):
        for k, t in enumerate(r["tg"]):
            if np.sum(r["area"][r["film"][k] > 1e-4]) >= share * r["area"].sum() - 1e-12:
                return float(t)
        return float("nan")
    early = [(s, at(b, s), at(c, s)) for s in (60, 120, 180, 240, 300, 360, 420, 480, 540, 600) if s <= end]
    late = (C["room_kJ"] - at(c, end - 60)["room_kJ"]) / (B["room_kJ"] - at(b, end - 60)["room_kJ"])
    dry = [at(c, s)["drying_g_m2h"] for s in np.arange(180, end + 1e-9, 2.5)]
    L = []
    L.append("wetTowelRadiator: a wet towel over a radiator held at 55 C against the same radiator bare, in a")
    L.append("closed 2-D bedroom section on a 0 C day, from switch-on; per metre of section.")
    L.append("From scripts/extract_results.py on runs/bare and runs/clothes.")
    L.append("")
    L.append(f"Over 0-{end:g} s                                        bare      towel   towel/bare")
    L.append(f"  the radiator's heat (kJ/m)                     {B['radiator_kJ']:8.1f}   {C['radiator_kJ']:8.1f}   {100 * C['radiator_kJ'] / B['radiator_kJ']:6.1f}%")
    L.append(f"  the heat that reached the room (kJ/m)          {B['room_kJ']:8.1f}   {C['room_kJ']:8.1f}   {100 * C['room_kJ'] / B['room_kJ']:6.1f}%")
    L.append(f"  kept warming the towel (kJ/m)                                {C['towelKept_kJ']:8.1f}")
    L.append(f"  latent heat still in the vapour (kJ/m)                       {C['latentHeld_kJ']:8.1f}")
    L.append(f"  of the towelled radiator's heat, reached the room            {100 * C['room_kJ'] / C['radiator_kJ']:6.1f}%")
    L.append("")
    L.append(f"At {end:g} s                                            bare      towel")
    L.append(f"  the room's air, volume mean (C)                {B['room_C']:8.2f}   {C['room_C']:8.2f}   (16.00 at the start)")
    L.append(f"  the room's relative humidity, mean (%)         {B['roomRH_pct']:8.1f}   {C['roomRH_pct']:8.1f}   (61 at the start, at the cells' pressure)")
    L.append(f"  air rising past y = 0.9 m, x < 0.6 m (l/s)     {B['plumeUp_lps']:8.1f}   {C['plumeUp_lps']:8.1f}")
    L.append(f"  heat it carries above 16 C (W)                 {B['plumeUp_W']:8.1f}   {C['plumeUp_W']:8.1f}")
    L.append(f"  the radiator's output (W)                      {B['radiator_W']:8.1f}   {C['radiator_W']:8.1f}")
    L.append(f"  the glass, mean (C)                            {B['glass_C']:8.2f}   {C['glass_C']:8.2f}")
    L.append("")
    L.append(f"Water (g/m), towel run, 0-{end:g} s: {C['evaporated_g']:.2f} left the towel, {C['airWater_g']:.2f} still in the air, "
             f"{C['glassWater_g']:.2f} on the glass")
    L.append(f"  ({C['condensed_g']:.2f} condensed in all); the towel holds {C['towelWater_kgm2']:.4f} kg/m2 of its 0.25 on average, "
             f"at {C['towel_C']:.2f} C mean.")
    L.append(f"  Drying {min(dry):.0f}-{max(dry):.0f} g/m2 h of sheet over 180-{end:g} s ({SHEET} m2 of sheet per metre).")
    L.append(f"  The glass holds 0.1 g/m2 over half its height from {mist(c, .5):.2f} s and over all of it from {mist(c, 1):.2f} s;"
             f" bare: {'never' if not np.isfinite(mist(b, 1e-9)) else f'{mist(b, 1e-9):.2f} s'}.")
    L.append("")
    L.append("Minute by minute (cumulative from 0 s): share of the bare run's, heat reached the room / radiator's heat")
    L.append("  t (s)  " + "".join(f"{s:7d}" for s, _, _ in early))
    L.append("  room % " + "".join(f"{100 * cc['room_kJ'] / bb['room_kJ']:7.1f}" for s, bb, cc in early))
    L.append("  rad. % " + "".join(f"{100 * cc['radiator_kJ'] / bb['radiator_kJ']:7.1f}" for s, bb, cc in early))
    L.append(f"  over the last minute alone the towel room had {100 * late:.1f}% of the bare room's heat; the bare radiator gave")
    L.append(f"  {minutes[0]['bareRoomThisMinute_W']:.0f} W in the first minute and {minutes[-1]['bareRoomThisMinute_W']:.0f} W in the last, "
             f"the towelled one {minutes[0]['towelRadiatorThisMinute_W']:.0f} and {minutes[-1]['towelRadiatorThisMinute_W']:.0f} W.")
    L.append("")
    for run, r in R.items():
        d, g = r["d"], r["g"]
        L.append(f"{run}: {len(d)} steps to {d['time'][-1]:.2f} s, {g['wall_s'][-1] / 3600:.2f} h of wall time on 8 ranks; air "
                 f"{g['airMin_K'].min() - 273.15:.2f} to {g['airMax_K'].max() - 273.15:.2f} C throughout;")
        L.append(f"  air mass within {np.max(np.abs(d['mass'] / d['mass'][0] - 1)):.1e} of its first step's.")
    (a.out / "summary.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
