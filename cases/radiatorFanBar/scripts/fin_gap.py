"""radiatorFanBar (10 Nov 2026): the fins' upward resistance for a chosen fin gap s.

radiatorCover's fin-gap formulas (../radiatorCover, its finsBare and finsFans runs), unchanged apart from s:
laminar flow between parallel vertical plates s apart, sheet t = 0.5 mm, height L = 0.6 m,
porosity phi = s/(s+t), in OpenFOAM's DarcyForchheimer form dp/dy = mu d U + f rho |U| U / 2:
  d = 12 / (phi s^2)      (plane Poiseuille, fRe = 24)
  f = 0.674 / (L phi^2)   (Shah and London's K_inf for plates)
The gap is CHOSEN to bring the bare K2 to its rating; it is not Stelrad's figure or any
published one. hv_laminar is the fully developed laminar value (Nu 7.54 on Dh = 2s, both
faces wetted, fin efficiency 1), printed for comparison only: hv itself is held at 4000.
Usage: python3 fin_gap.py <gap_mm> [<gap_mm> ...]   -> one JSON object per gap
"""
import json, sys
t, L, k_air = 0.5e-3, 0.60, 0.0265
def fin(s_mm):
    s = s_mm * 1e-3
    phi = s / (s + t)
    return {'gap_mm': s_mm, 'porosity': phi, 'dy': 12 / (phi * s * s), 'fy': 0.674 / (L * phi * phi),
            'hv_laminar_W_m3K': 7.54 * k_air / (2 * s) * 2 / (s + t)}
if __name__ == '__main__':
    for a in sys.argv[1:]:
        print(json.dumps(fin(float(a))))
