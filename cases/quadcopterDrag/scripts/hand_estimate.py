#!/usr/bin/env python3
"""The airframe's drag added up by hand from textbook coefficients, to set beside the CFD.

    python3 scripts/hand_estimate.py

Each part is treated as an isolated textbook shape in the 15 m/s wind at 10 degrees
nose-down, with no part shielding or washing another:
  body   a rounded box, Cd 0.90 on its silhouette along the wind (from geometry.json)
  arms   yawed cylinders, Cd 1.20 on the velocity normal to the axis: 1.2 D L sin^3(theta),
         theta the angle between the arm and the wind
  cans   vertical cylinders, the same rule, theta = 80 degrees
  hubs   a disc at 10 degrees incidence (1.17 A sin^3 10) plus its rim (1.2 D t cos 10)
  legs   vertical rods, as the cans, over their 60 mm below the body
Writes geometry/hand_estimate.json.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
g = json.load(open(ROOT / "geometry" / "geometry.json"))
U, RHO, NU, PITCH = 15.0, 1.225, 1.5e-5, math.radians(10.0)
Q = 0.5 * RHO * U ** 2
wind = (math.cos(PITCH), 0.0, -math.sin(PITCH))
arm_axis = (math.sqrt(0.5), math.sqrt(0.5), 0.0)
sin_arm = math.sqrt(1 - sum(a * b for a, b in zip(arm_axis, wind)) ** 2)
sin_vert = math.cos(PITCH)

cda = {
    "body": 0.90 * g["silhouette_along_wind_m2"]["body"],
    "arms": 4 * 1.20 * 0.020 * 0.180 * sin_arm ** 3,
    "cans": 4 * 1.20 * 0.028 * 0.030 * sin_vert ** 3,
    "hubs": 4 * (1.17 * math.pi * 0.030 ** 2 * math.sin(PITCH) ** 3 + 1.20 * 0.060 * 0.004 * math.cos(PITCH)),
    "legs": 4 * 1.20 * 0.008 * 0.060 * sin_vert ** 3,
}
print(f"hand estimate, isolated parts, q = {Q:.2f} Pa")
for k, v in cda.items():
    print(f"  {k:5s} CdA {v*1e4:6.1f} cm2   {v*Q:5.2f} N")
total = sum(cda.values())
print(f"  total CdA {total*1e4:6.1f} cm2   {total*Q:5.2f} N")
print(f"Reynolds numbers: body length {U*0.16/NU:.2g}, arm {U*0.020/NU:.2g}, can {U*0.028/NU:.2g}, "
      f"leg {U*0.008/NU:.2g}")
json.dump({"q_Pa": Q, "CdA_m2": cda, "total_CdA_m2": total, "total_drag_N": total * Q},
          open(ROOT / "geometry" / "hand_estimate.json", "w"), indent=2)
