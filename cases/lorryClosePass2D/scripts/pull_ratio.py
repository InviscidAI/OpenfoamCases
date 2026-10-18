#!/usr/bin/env python3
"""The 30 cm pass's peak pull towards the lorry as a multiple of the 1.5 m pass's, and the push.

    python3 scripts/pull_ratio.py results > results/pull_ratio.txt

Reads results/rider_force_gap150.csv and rider_force_gap030.csv (scripts/rider_force.py).
The pull is +Fy (+ y towards the lorry), the push -Fy; each peak is taken inside the clip's
window, t = 4.4167-6.0417 s (his shoulders 8.06 m ahead of the cab's front to 19.0 m
behind it, 2.5 m past the doors). Single steps jitter by about a cell's worth as his edge
crosses cells, so the peak is read after smoothing, and the ratio is given for each of
twelve smoothings:
  - running means over 0.02, 0.05 and 0.10 s of flow, centred and trailing (a centred mean
    near the window's end takes steps up to half its width past it);
  - 2 m bins of his position along the lorry (0.12 s), at four phases;
  - 1 m bins (0.06 s), at two phases; a bin cut by the window's end counts only if it
    holds at least half its steps.
Last, the arrows' own peaks: on the clip's frames, 481 evenly spaced over the window, the
mean over the 0.05 s of flow up to each frame, updated every 6 frames and held between.
(The published clip later played the stretch along the trailer faster; it kept these frames
for the push and the pull, and its arrows' peaks are the same.)
"""
import sys
from pathlib import Path

import numpy as np

T0, T1 = 4.4167, 6.0417
FRAMES = np.linspace(4.4166432199941568, 6.0416432199941568, 481)  # the panels' write times
U_REL = 16.667  # m/s, the rider's speed back along the lorry in its frame


def behind(t):
    """Metres his shoulders are behind the cab's front (x = 16.5 m; the doors at 16.5 behind)."""
    return 16.5 - (41.5 - U_REL * (t - 3.4))


def running(t, y, w, centred):
    c = np.concatenate([[0.0], np.cumsum(y)])
    lo = np.searchsorted(t, t - (w / 2 if centred else w), side="right")
    hi = np.searchsorted(t, t + (w / 2 if centred else 0.0), side="right")
    return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)


def ratios(F, sign, name):
    lines, rs = [f"{name} = {'+' if sign > 0 else '-'}Fy, N per metre; peak inside {T0}-{T1} s; "
                 "'behind' = metres his shoulders are behind the cab's front", ""], []
    for w in (0.02, 0.05, 0.10):
        for centred in (True, False):
            pk = {}
            for r, (t, f) in F.items():
                m = running(t, sign * f[:, 1], w, centred)
                sel = (t >= T0) & (t <= T1)
                k = np.argmax(np.where(sel, m, -np.inf))
                pk[r] = (m[k], behind(t[k]))
            rs.append(pk["gap030"][0] / pk["gap150"][0])
            lines.append(f"{'centred' if centred else 'trailing'} {w:.2f} s mean: 30 cm "
                         f"{pk['gap030'][0]:5.1f} at {pk['gap030'][1]:+6.2f} m behind, 1.5 m "
                         f"{pk['gap150'][0]:5.1f} at {pk['gap150'][1]:+6.2f} m; ratio {rs[-1]:.2f}")
    for width, phases in ((2.0, (0.0, 0.5, 1.0, 1.5)), (1.0, (0.0, 0.5))):
        for ph in phases:
            pk = {}
            for r, (t, f) in F.items():
                sel = (t >= T0) & (t <= T1)
                b, y = behind(t[sel]), sign * f[sel, 1]
                edges = np.arange(-16 + ph, 24, width)
                idx = np.digitize(b, edges)
                full = width / U_REL / np.median(np.diff(t))
                means = [(y[idx == i].mean(), edges[i - 1]) for i in np.unique(idx)
                         if 0 < i < len(edges) and (idx == i).sum() >= 0.5 * full]
                pk[r] = max(means)
            rs.append(pk["gap030"][0] / pk["gap150"][0])
            lines.append(f"{width:.0f} m bins, phase {ph}: 30 cm {pk['gap030'][0]:5.1f} (bin from "
                         f"{pk['gap030'][1]:+.1f} m), 1.5 m {pk['gap150'][0]:5.1f} (bin from "
                         f"{pk['gap150'][1]:+.1f} m); ratio {rs[-1]:.2f}")
    lines += ["", f"{name} ratio over all {len(rs)} smoothings: {min(rs):.2f}-{max(rs):.2f}, "
              f"median {np.median(rs):.2f}", ""]
    return lines


def arrows(t, f, window=0.05, every=6):
    c = np.concatenate([np.zeros((1, 2)), np.cumsum(f[:, :2], axis=0)])
    hi = np.searchsorted(t, FRAMES + 1e-9, side="right")
    lo = np.searchsorted(t, FRAMES - window, side="right")
    fxy = (c[hi] - c[lo]) / (hi - lo)[:, None]
    return fxy[(np.arange(len(FRAMES)) // every) * every]


def main(results):
    F = {}
    for r in ("gap150", "gap030"):
        d = np.loadtxt(Path(results) / f"rider_force_{r}.csv", delimiter=",", skiprows=1)
        F[r] = (d[:, 0], d[:, 1:3])
    lines = ratios(F, +1, "pull") + ratios(F, -1, "push")
    sh = {}
    for r, (t, f) in F.items():
        s = arrows(t, f)
        sh[r] = (s[:, 1].max(), FRAMES[s[:, 1].argmax()], -s[:, 1].min(), FRAMES[s[:, 1].argmin()],
                 np.hypot(s[:, 0], s[:, 1]).max())
    lines.append("the arrows (0.05 s trailing mean, held 6 frames): " + "; ".join(
        f"{r} pull {v[0]:.1f} at {v[1]:.3f} s, push {v[2]:.1f} at {v[3]:.3f} s, largest in-plane {v[4]:.1f}"
        for r, v in sh.items()))
    lines.append(f"arrow pull ratio {sh['gap030'][0] / sh['gap150'][0]:.2f}, push ratio "
                 f"{sh['gap030'][2] / sh['gap150'][2]:.2f}")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n\n")[1])
    main(sys.argv[1])
