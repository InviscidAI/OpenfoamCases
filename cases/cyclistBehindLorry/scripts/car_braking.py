#!/usr/bin/env python3
"""The lorry's emergency stop and the two cars behind it, as kinematics.

No CFD: the braking and the bump follow from sourced figures (README, "The stop"):
  * speed 25 m/s (90 km/h), the EU speed limiter for lorries (Directive 92/6/EEC, as amended)
  * gaps, bumper to bumper: 12.5 m (0.5 s; about 15% of drivers at 60-80 km/h on the M42
    keep 0.5 s or less, Al-Obaedi, IJE 32(5) 2019 661-666) and 50 m (two seconds, the
    Highway Code, Rule 126)
  * the car driver's brake reaction time 1.25 s for an unexpected braking ahead
    (Green, Transportation Human Factors 2 (2000) 195-216, as summarised on visualexpert.com)
  * the car's deceleration 7.4 m/s2, ordinary drivers' emergency stops on dry roads in cars
    with ABS (Greibe, "Braking distance, friction and behaviour", Trafitec 2007, Table 4.6)
  * the lorry's deceleration 7.4 / 1.4 = 5.3 m/s2: HGV stopping distances are typically 40%
    longer than cars' (Dunn & Hoover 2004, as cited by Henderson & Cebon, HVTT13)
The lorry brakes at t = 0 at a constant deceleration; each car holds its speed for the
reaction time, then brakes at a constant deceleration. If a car reaches the lorry's back, the
contact is drawn as a cartoon bump: the car takes the lorry's speed and the two stop together
(the lorry is about 25 times heavier). Positions are of the lorry's rear doors and each car's
front bumper, in metres along the road from where the lorry's doors were at t = 0.

The sensitivity rows vary the reaction time (0.7-1.5 s) and the car's braking: 6.5 m/s2,
what the Highway Code's typical braking distances imply, and Greibe's ordinary and
professional drivers, with the lorry's 40% longer stop each time.

    python3 scripts/car_braking.py results/car_braking.json [--fps 120] [--t-end 6.0]
"""
import argparse
import json

import numpy as np

V = 25.0
GAPS = {"tailgate": 12.5, "safe": 50.0}
T_REACT = 1.25
A_CAR = 7.4
A_LORRY = A_CAR / 1.4


def lorry(t, v=V, a=A_LORRY):
    t = np.minimum(t, v / a)
    return v * t - 0.5 * a * t * t, v - a * t


def car_free(t, gap, v=V, tr=T_REACT, a=A_CAR):
    tb = np.clip(t - tr, 0, v / a)
    x = -gap + v * np.minimum(t, tr) + v * tb - 0.5 * a * tb * tb
    return x, np.where(t < tr, v, v - a * tb)


def contact(gap, v=V, tr=T_REACT, aC=A_CAR, aL=A_LORRY, dt=1e-5):
    """First time the car's front reaches the lorry's doors, or None."""
    t = np.arange(0, v / min(aC, aL) + tr + 1, dt)
    xl, vl = lorry(t, v, aL)
    xc, vc = car_free(t, gap, v, tr, aC)
    s = xl - xc
    hit = np.nonzero(s <= 0)[0]
    if len(hit) == 0:
        return None, dict(closest_m=float(s.min()), closest_t=float(t[np.argmin(s)]), final_m=float(s[-1]))
    i = hit[0]
    return dict(t=float(t[i]), closing_kmh=float((vc[i] - vl[i]) * 3.6), car_kmh=float(vc[i] * 3.6),
                lorry_kmh=float(vl[i] * 3.6), x=float(xl[i])), None


def track(gap, ts):
    xl, vl = lorry(ts)
    xc, vc = car_free(ts, gap)
    c, short = contact(gap)
    if c is not None:
        after = ts >= c["t"]
        xc = np.where(after, xl, xc)        # stuck to the lorry's doors from contact on
        vc = np.where(after, vl, vc)
    return xl, vl, xc, vc, c, short


def threshold(tr, aC, aL, v=V):
    lo, hi = 0.0, 200.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if contact(m, v, tr, aC, aL, 1e-4)[0] is not None else (lo, m)
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=120)
    ap.add_argument("--t-end", type=float, default=6.0)
    a = ap.parse_args()
    ts = np.arange(0, a.t_end + 1e-9, 1 / a.fps)
    res = dict(inputs=dict(speed_ms=V, gaps_m=GAPS, reaction_s=T_REACT, car_decel=A_CAR,
                           lorry_decel=round(A_LORRY, 3)),
               lorry_stops=dict(t=V / A_LORRY, at_m=V * V / (2 * A_LORRY)), runs={})
    for name, gap in GAPS.items():
        xl, vl, xc, vc, c, short = track(gap, ts)
        stop = dict(t=T_REACT + V / A_CAR, at_m=float(xc[-1])) if c is None else None
        res["runs"][name] = dict(gap_m=gap, contact=c, clearance=short, stop=stop,
                                 t=ts.round(6).tolist(), lorry_x=xl.round(4).tolist(),
                                 car_front_x=xc.round(4).tolist(), car_speed=vc.round(4).tolist())
        print(f"{name:9s} gap {gap:5.1f} m: " + (
            f"hits the lorry at t = {c['t']:.2f} s, closing at {c['closing_kmh']:.0f} km/h "
            f"(car {c['car_kmh']:.0f}, lorry {c['lorry_kmh']:.0f} km/h)" if c else
            f"comes within {short['closest_m']:.1f} m of the lorry's doors at t = {short['closest_t']:.2f} s"
            f" and stops {short['final_m']:.1f} m short"))
    # how the outcome depends on the reaction time and the car's braking
    sens = []
    for tr in (0.7, 1.0, 1.25, 1.5):
        for aC, src in ((6.5, "Highway Code braking distances"), (7.4, "Greibe 2007, ordinary drivers"),
                        (8.4, "Greibe 2007, professional drivers")):
            aL = aC / 1.4
            row = dict(reaction_s=tr, car_decel=aC, lorry_decel=round(aL, 2), car_source=src,
                       crash_below_gap_m=round(threshold(tr, aC, aL), 1))
            for name, gap in GAPS.items():
                c, short = contact(gap, V, tr, aC, aL, 1e-4)
                row[name] = (f"hit at {c['closing_kmh']:.0f} km/h" if c else f"closest {short['closest_m']:.1f} m")
            sens.append(row)
            print(f"  reaction {tr:4.2f} s, car {aC} m/s2, lorry {aL:.2f}: crash below {row['crash_below_gap_m']:5.1f} m;"
                  f" 12.5 m {row['tailgate']}; 50 m {row['safe']}")
    res["sensitivity"] = sens
    with open(a.out, "w") as f:
        json.dump(res, f)


if __name__ == "__main__":
    main()
