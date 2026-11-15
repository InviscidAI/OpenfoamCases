#!/usr/bin/env python3
"""The duct calculation that sets the registers' flows and the supply temperature: a simple duct
network for a small US house, every register open against the spare room's closed.

    python3 scripts/ducts.py > config/ducts.txt

Needs NumPy and SciPy. Nothing here is solved by OpenFOAM: the ducts are not in the mesh, and each
register in the solve is an inlet with the flow and temperature this script prints
(config/case.json, "runs": its L/s times 1.204 kg/m3, and its supply temperature).

The furnace is an American Standard S8X1B040M2PSC (40,000 Btu/h input, 32,500 Btu/h output, 80% AFUE), its
constant-torque blower on tap 3: 820, 662, 504 CFM at 0.1, 0.3, 0.5 in w.c. external static, a straight line
Q = 899 - 790 ESP (the furnace's product submittal, S8X1B040M2-SUB-2D-EN, airflow table). Only the line's slope
is used: the line is shifted to pass through the design point below (fan_off), so the blower here moves
612 CFM at 0.50 in w.c., not tap 3's 504.

The network (ours, set so the open house sits at 0.50 in w.c., the usual rated maximum; Energy Vanguard notes typical
measured systems run near 0.8):
  blower -> return side, filter and coil, a square-law resistance taking 0.25 in at the design flow
         -> supply plenum and trunk node P_t (0.25 in at design), with a plenum leak to the crawlspace
         -> six branches, each a square-law duct from P_t to its boot P_b, then a square-law register from P_b to
            the room (0.04 in = 10 Pa at the boot at design), with a boot leak to the crawlspace at P_b.
Leaks are power laws with exponent 0.6, as LBNL-54005's calibrated leaks (0.61); sized as that report's
"supply plenum and registers" case, 10% of the air handler flow at the plenum and 5% over the boots at design.
A closed register passes nothing; its boot then sits at nearly the trunk pressure and its leak grows.
The furnace's heat goes into the whole air stream (Q_out over the air handler's flow), and the leaked air's heat
is lost to the house.
"""
import numpy as np
from scipy.optimize import brentq

IN = 249.089          # Pa per in w.c.
CFM = 4.71947e-4      # m3/s per CFM
rho, cp = 1.204, 1006.0
Q_out = 32500 * 0.293071  # W into the air stream

rooms = ["living_W", "living_E", "kitchen", "bedroom", "bath", "spare"]
design = np.array([95, 95, 95, 100, 45, 90.0])   # CFM delivered at design, by room load (ours)

def fan(esp_pa):  # CFM
    return 899 - 790 * esp_pa / IN

Pt0, Pb0 = 0.25 * IN, 10.0
Q_reg0 = design.sum()
Q_bootleak0 = 0.05 / 0.85 * Q_reg0  # placeholders, solved below for 10% + 5% of the AH flow
# design air handler flow: registers + leaks = AH, leaks = 15% of AH
Q_ah0 = Q_reg0 / 0.85
c_pl = 0.10 * Q_ah0 / Pt0 ** 0.6
c_bl = (0.05 * Q_ah0 / 6) / Pb0 ** 0.6
k_reg = design / np.sqrt(Pb0)                 # register: Q = k sqrt(P_b)
branch_flow0 = design + c_bl * Pb0 ** 0.6
k_duct = branch_flow0 / np.sqrt(Pt0 - Pb0)    # duct: Q = k sqrt(P_t - P_b)
esp0 = 0.50 * IN
R_ret = (esp0 - Pt0) / Q_ah0 ** 2
# put the design on the fan line by choosing the fan's offset (tap 3's slope, shifted so it passes the design)
fan_off = Q_ah0 + 790 * esp0 / IN

def fan_q(esp):
    return fan_off - 790 * esp / IN

def solve(open_mask):
    def boot(Pt, i):
        if not open_mask[i]:
            # closed: only the boot leak flows through the duct: k_d sqrt(Pt-Pb) = c_bl Pb^0.6
            return brentq(lambda Pb: k_duct[i] * np.sqrt(max(Pt - Pb, 0)) - c_bl * Pb ** 0.6, 1e-9, Pt)
        return brentq(lambda Pb: k_duct[i] * np.sqrt(max(Pt - Pb, 0)) - k_reg[i] * np.sqrt(Pb) - c_bl * Pb ** 0.6, 1e-9, Pt)
    def supply_total(Pt):
        Pb = np.array([boot(Pt, i) for i in range(6)])
        reg = np.where(open_mask, k_reg * np.sqrt(Pb), 0.0)
        bl = c_bl * Pb ** 0.6
        return reg, bl, Pb, reg.sum() + bl.sum() + c_pl * Pt ** 0.6
    def mismatch(Pt):
        q = supply_total(Pt)[3]
        return fan_q(Pt + R_ret * q ** 2) - q
    Pt = brentq(mismatch, 1.0, 600.0)
    reg, bl, Pb, q = supply_total(Pt)
    return dict(Pt=Pt, esp=Pt + R_ret * q ** 2, ah=q, reg=reg, bootleak=bl, plenumleak=c_pl * Pt ** 0.6, Pb=Pb)

T0F = 62.0
out = []
for name, mask in [("open", np.ones(6, bool)), ("closed", np.array([1, 1, 1, 1, 1, 0], bool))]:
    s = solve(mask)
    rise_F = Q_out / (rho * cp * s["ah"] * CFM) * 1.8
    leak = s["bootleak"].sum() + s["plenumleak"]
    heat_rooms = s["reg"].sum() / s["ah"] * Q_out
    out.append((name, s, rise_F, leak, heat_rooms))
    print(f"== {name}: air handler {s['ah']:.1f} CFM, external static {s['esp']/IN:.3f} in w.c., trunk {s['Pt']:.1f} Pa")
    for r, q, b, pb in zip(rooms, s["reg"], s["bootleak"], s["Pb"]):
        print(f"   {r:9s} register {q:6.1f} CFM ({q*CFM*1000:5.2f} L/s)  boot {pb:5.1f} Pa  boot leak {b:5.2f} CFM")
    print(f"   plenum leak {s['plenumleak']:.1f} CFM; all leaks {leak:.1f} CFM = {leak/s['ah']*100:.1f}% of the air handler")
    print(f"   rise {rise_F:.1f} F -> supply {T0F+rise_F:.1f} F = {(T0F+rise_F-32)/1.8:.2f} C from a {T0F} F return")
    print(f"   heat out of the registers {heat_rooms:.0f} W of the furnace's {Q_out:.0f} W; lost in leaks {Q_out-heat_rooms:.0f} W")

(_, so, ro, lo, ho), (_, sc, rc, lc, hc) = out
others = slice(0, 5)
print("\n== closing the spare room's register")
print(f"   the spare room's register carried {so['reg'][5]:.1f} CFM and {so['reg'][5]/so['ah']*Q_out:.0f} W")
d_air = sc['reg'][others].sum() - so['reg'][others].sum()
print(f"   the other five rooms' air: {so['reg'][others].sum():.1f} -> {sc['reg'][others].sum():.1f} CFM (+{d_air:.1f}, +{d_air/so['reg'][others].sum()*100:.1f}%)")
h_o = so['reg'][others].sum() / so['ah'] * Q_out
h_c = sc['reg'][others].sum() / sc['ah'] * Q_out
print(f"   the other five rooms' heat: {h_o:.0f} -> {h_c:.0f} W (+{h_c-h_o:.0f} W, +{(h_c-h_o)/h_o*100:.1f}%)")
print(f"   of the spare room's {so['reg'][5]/so['ah']*Q_out:.0f} W, {h_c-h_o:.0f} W ({(h_c-h_o)/(so['reg'][5]/so['ah']*Q_out)*100:.0f}%) reaches the other rooms and {(lc/sc['ah'] - lo/so['ah'])*Q_out:.0f} W more leaks")
print(f"   air handler flow {so['ah']:.0f} -> {sc['ah']:.0f} CFM ({(sc['ah']/so['ah']-1)*100:.1f}%); leaks {lo:.0f} -> {lc:.0f} CFM")
