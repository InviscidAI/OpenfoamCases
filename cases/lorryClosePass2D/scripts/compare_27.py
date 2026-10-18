#!/usr/bin/env python3
"""The 1.5 m pass's force on the rider against cyclistBehindLorry's 3-D overtaking estimate.

    python3 scripts/compare_27.py results/rider_force_gap150.csv \
        ../cyclistBehindLorry/results/overtaking_force.csv > results/compare_27.txt

The 3-D force (../cyclistBehindLorry, the overtaking run) is a quasi-steady estimate in
newtons from the lorry-alone solve, the rider not in it; this one is the reaction to the
drag term, per metre of height, at one height. Both use + x forwards and + y towards the
lorry, the same lorry, gap (1.5 m), speeds (80 and 20 km/h) and path, so they are compared
by where his shoulders are, in metres behind the cab's front (the doors at 16.5 m).

Part 1 is the test written down before the 2-D run had a force: on 0.05 s centred running
means over t = 4-8 s,
  1. a push away from the lorry comes first and a pull towards it after;
  2. the push's peak lies within 2 m of the 3-D one's;
  3. the push-to-pull sign change lies within 3 m of the 3-D one's;
  4. the pull's peak lies within 4 m of the 3-D one's;
  5. the two curves, each scaled by its own push peak, correlate at r >= 0.7 (on the 3-D
     run's write times).
Failing 1 or 5, or two of 2-4, would have counted as disagreeing badly, and the 30 cm pass
would not have been solved. The 3-D curve is its file's shown (0.05 s mean) column. The
test is run over the window as written, 4-8 s, and again over 4-6.4 s, the stretch the
30 cm pass was solved over: beyond that the 2-D wake behind the doors dominates (README).

Part 2 is both forces in 1 m bins of his position: the 2-D run every step, the 3-D run's
single writes (481 over 4-8 s), each bin [a, a + 1) m.
"""
import sys

import numpy as np

CAB_FRONT, U_REL = 16.5, 16.667


def behind(t):
    return CAB_FRONT - (41.5 - U_REL * (t - 3.4))


def running_mean(t, y, width):
    c = np.concatenate([[0.0], np.cumsum(y)])
    lo = np.searchsorted(t, t - width / 2, side="left")
    hi = np.searchsorted(t, t + width / 2, side="right")
    return (c[hi] - c[lo]) / (hi - lo)


def features(b, fy):
    """Push = most negative Fy, pull = most positive after it, and the sign change between."""
    i_push = int(np.argmin(fy))
    after = np.arange(len(fy)) > i_push
    i_pull = int(np.argmax(np.where(after, fy, -np.inf)))
    seg = np.arange(i_push, i_pull + 1)
    cross = seg[np.where(np.diff(np.sign(fy[seg])) > 0)[0]]
    return {"push": (b[i_push], fy[i_push]), "pull": (b[i_pull], fy[i_pull]),
            "cross": b[cross[0]] if len(cross) else np.nan,
            "push_first": i_push < i_pull and fy[i_push] < 0 < fy[i_pull]}


def main(csv2d, csv3d):
    d = np.loadtxt(csv2d, delimiter=",", skiprows=1)
    t, fx, fy = d[:, 0], d[:, 1], d[:, 2]
    ref = np.genfromtxt(csv3d, delimiter=",", names=True)
    rb = ref["behind_cab_front_m"]

    out = [f"2-D: {csv2d}, {len(t)} steps; 3-D: {csv3d}, {len(rb)} writes", ""]
    for t1 in (8.0, 6.4):
        win = (t >= 4.0 - 1e-9) & (t <= t1 + 1e-9)
        tw = t[win]
        fy05 = running_mean(tw, fy[win], 0.05)
        bw = behind(tw)
        a, b = features(rb, ref["Fy_shown_N"]), features(bw, fy05)
        on = np.interp(rb, bw, fy05)
        ok = (rb >= bw.min()) & (rb <= bw.max())
        r = np.corrcoef(ref["Fy_shown_N"][ok] / abs(a["push"][1]), on[ok] / abs(b["push"][1]))[0, 1]
        tests = {
            "1 push first, then pull": b["push_first"],
            "2 push peak within 2 m": abs(b["push"][0] - a["push"][0]) <= 2.0,
            "3 sign change within 3 m": abs(b["cross"] - a["cross"]) <= 3.0,
            "4 pull peak within 4 m": abs(b["pull"][0] - a["pull"][0]) <= 4.0,
            "5 shapes correlate r >= 0.7": r >= 0.7,
        }
        bad = (not tests["1 push first, then pull"]) or (not tests["5 shapes correlate r >= 0.7"]) \
            or sum(not tests[k] for k in list(tests)[1:4]) >= 2
        out += [
            f"1. The test set before the 2-D force existed, over t = 4-{t1} s (his shoulders "
            f"-15.0 to {bw.max():.1f} m behind the cab's front;",
            f"   0.05 s means; {win.sum()} steps)",
            "",
            "                          3-D (N)                 2-D (N/m)",
            f"push peak                 {a['push'][0]:6.2f} m ({a['push'][1]:6.1f})      {b['push'][0]:6.2f} m ({b['push'][1]:6.1f})",
            f"sign change               {a['cross']:6.2f} m                {b['cross']:6.2f} m",
            f"pull peak                 {a['pull'][0]:6.2f} m ({a['pull'][1]:6.1f})      {b['pull'][0]:6.2f} m ({b['pull'][1]:6.1f})",
            f"curves scaled by their own push peak: r = {r:.3f}",
            "",
        ] + [f"  {'pass' if v else 'FAIL'}  {k}" for k, v in tests.items()] + [
            "", "shapes disagree badly" if bad else "shapes agree", ""]
    out += [
        "2. In 1 m bins of his position, [a, a + 1) m behind the cab's front; the doors at 16.5 m",
        "   (sideways + towards the lorry; fore-aft + forwards, so his drag is negative)",
        "",
        "    a    2-D Fy  3-D Fy   2-D Fx  3-D Fx",
        "         N/m     N        N/m     N",
    ]
    ball = behind(t)
    for lo in np.arange(-5.0, 20.0, 0.5):
        s = (ball >= lo) & (ball < lo + 1)
        q = (rb >= lo) & (rb < lo + 1)
        out.append(f"{lo:5.1f}  {fy[s].mean():7.2f} {ref['Fy_N'][q].mean():7.2f}  "
                   f"{fx[s].mean():7.2f} {ref['Fx_N'][q].mean():7.2f}")
    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__.split("\n\n")[1])
    main(*sys.argv[1:])
