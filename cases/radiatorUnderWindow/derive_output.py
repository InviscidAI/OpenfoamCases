#!/usr/bin/env python3
"""Derive the radiator output this section loses at a 20-21 C room mean: 60 W/m.

The inputs are settled heat flows measured in the case's first two solves (see README.md):

- first solve: floor held at 20 C, a sink relaxing the room towards 20 C, 620 W/m; means
  over the last 120 s of 0-480 s. Only the glass's loss is used from it.
- second solve: this case's dictionaries with radPowerPerM 620, tEnd 1440, writeInt 1.5
  and maxCoNum 5 (no pressure-iteration cap, no energyCheck monitor); means of the
  wallHeatFlux and roomMeanT monitors over 1140-1440 s.

Heat flows are W per metre of section, positive out of the room air.

    python3 derive_output.py        # prints and writes results/output_derivation.json
"""
import json
from pathlib import Path

TOUT = 0.0     # C, outside air beyond the glass
TWALL = 20.0   # C, ceiling and inner wall (fixed)

MEASURED = {
    "window": {
        "first_solve": {"room_mean_C": 21.8643, "glass_W_per_m": 82.8347},
        "second_solve": {"room_mean_C": 40.0663, "glass_W_per_m": 114.3377,
                         "ceiling_W_per_m": 315.1838, "innerWall_W_per_m": 183.0899},
    },
    "opposite": {
        "first_solve": {"room_mean_C": 21.7414, "glass_W_per_m": 56.8197},
        "second_solve": {"room_mean_C": 38.9933, "glass_W_per_m": 103.9472,
                         "ceiling_W_per_m": 292.0195, "innerWall_W_per_m": 214.0952},
    },
}


def conductances(m):
    f, s = m["first_solve"], m["second_solve"]
    walls = s["ceiling_W_per_m"] + s["innerWall_W_per_m"]
    return {
        # glass: heat flow per kelvin of room-to-outside difference
        "glass_W_per_mK": {"first": f["glass_W_per_m"] / (f["room_mean_C"] - TOUT),
                           "second": s["glass_W_per_m"] / (s["room_mean_C"] - TOUT)},
        # 20 C ceiling + inner wall: per kelvin of room excess, at that excess
        "walls_W_per_mK_at_dT": [walls / (s["room_mean_C"] - TWALL), s["room_mean_C"] - TWALL],
    }


def loss(T, k):
    """Steady loss at room mean T: glass K_g (T - T_out), plus the 20 C surfaces by natural
    convection, whose coefficient grows as dT^(1/3). K_g is the second solve's for each run;
    the first solve's plume was ten times stronger and washed the window run's pane."""
    kg = k["glass_W_per_mK"]["second"]
    kw, dref = k["walls_W_per_mK_at_dT"]
    dT = max(T - TWALL, 0.0)
    return kg * (T - TOUT) + kw * (dT / dref) ** (1 / 3) * dT


def solve(f, lo, hi):
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return 0.5 * (lo + hi)


def main():
    out = {"measured": MEASURED, "runs": {}}
    k = {run: conductances(m) for run, m in MEASURED.items()}
    out["runs"] = k
    out["loss_W_per_m_at_room_mean"] = {
        run: {f"{T:.2f}": round(loss(T, k[run]), 1) for T in (20.0, 20.25, 20.5, 20.75, 21.0)}
        for run in k}
    target = 20.5
    q = 0.5 * (loss(target, k["window"]) + loss(target, k["opposite"]))
    Q = round(q / 5) * 5
    out["target_room_mean_C"] = target
    out["output_at_target_W_per_m"] = q
    out["chosen_output_W_per_m"] = Q
    out["predicted_settled_room_mean_C"] = {
        run: solve(lambda T: loss(T, k[run]) - Q, 19.0, 30.0) for run in k}
    text = json.dumps(out, indent=1)
    print(text)
    Path(__file__).with_name("results").mkdir(exist_ok=True)
    Path(__file__).with_name("results").joinpath("output_derivation.json").write_text(text + "\n")


if __name__ == "__main__":
    main()
