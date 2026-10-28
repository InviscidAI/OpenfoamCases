#!/usr/bin/env python3
"""Write a run's system/flightCondition: the inflow for one angle of attack.

    python3 scripts/flight.py <alpha_deg> <run_dir>

The aircraft stays at zero incidence in the mesh and the air comes at it from below:
U = 45 (cos a, 0, sin a) m/s. Lift is normal to the inflow and drag along it.
"""
import json
import math
import os
import sys

U_INF = 45.0          # m/s, sea level
NU = 1.5e-5           # m2/s
INTENSITY = 0.001     # free-stream turbulence intensity
VISC_RATIO = 1.0      # free-stream nut / nu

alpha = float(sys.argv[1])
run = sys.argv[2]
geo = json.load(open(os.path.join(os.path.dirname(__file__), "..", "geometry", "geometry.json")))
a = math.radians(alpha)
k = 1.5 * (U_INF * INTENSITY) ** 2
omega = k / (VISC_RATIO * NU)
with open(os.path.join(run, "system", "flightCondition"), "w") as f:
    f.write(f"""// alpha = {alpha:g} deg, written by scripts/flight.py
alphaDeg    {alpha:g};
magUInf     {U_INF:g};
Uinf        ({U_INF * math.cos(a):.8f} 0 {U_INF * math.sin(a):.8f});
liftDir     ({-math.sin(a):.8f} 0 {math.cos(a):.8f});
dragDir     ({math.cos(a):.8f} 0 {math.sin(a):.8f});
kInf        {k:.6g};
omegaInf    {omega:.6g};
mac         {geo['mean_aerodynamic_chord_m']:.6f};
AhalfRef    {geo['wing_reference_area_half_m2']:.6f};
""")
