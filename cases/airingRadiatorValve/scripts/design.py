#!/usr/bin/env python3
"""The radiator, its valve and the room's design heat loss on a 0 C day.

    python3 design.py            # prints the design as JSON

make_case.py imports design() and writes its numbers into each run's constant/fvOptions. The
sources are in ../README.md, "The radiator and its valve":

- the radiator: a Stelrad Softline Compact K1 600 x 1000, the box already in windowAiring's
  mesh: 980 W at 75/65/20 C (a 50 K log-mean difference), n = 1.29, 19.70 kg of steel and
  3.25 l of water (Stelrad's EN 442 table);
- the valve: a Danfoss RA 2000 head on an RA-N valve at setting 3, 20 C on the scale at
  Xp = 2 K, so shut at 22 C; kv 0.73 m3/h at Xp = 2 K against kvs 0.90 (RA-N DN 15, setting N);
  the gas-filled head's time constant 10 min (Danfoss);
- the design heat loss, EN 12831 style, 20 C inside and 0 C outside: the window wall's opaque
  part as modelled (13 mm of plaster on concrete, 24 cm, EN ISO 6946's surface resistances
  0.13 and 0.04 m2K/W), the glazing's U = 2.8 W/m2K, and EN 12831's minimum air change for a
  living room, 0.5 an hour. The other walls, the floor and the ceiling face heated rooms.

The radiator is Xu, Fu and Di's lumped model (Building Simulation 2007, eqs 4-8): output
Q50 ((Trad - Ta)/50)^n, heated by its water through an effectiveness 1 - exp(-KA/(cw q)).
"""
import json
import math

ROOM = (4.0, 2.4, 3.5)                       # x, y, z (m), windowAiring's room
V = ROOM[0] * ROOM[1] * ROOM[2]              # 33.6 m3
A_WIN = 1.0 * 1.2
A_WALL = ROOM[2] * ROOM[1] - A_WIN           # the window wall's opaque part, 7.2 m2
R_WALL = 0.13 + 0.013 / 0.57 + (0.24 - 0.013) / 1.13 + 0.04
U_WALL, U_WIN = 1 / R_WALL, 2.8
DT = 20.0                                    # 20 C inside, 0 C outside
Q50, N = 980.0, 1.29
CW = 4186.0
CRAD = 3.25 * CW + 19.70 * 450.0             # water + steel at 450 J/kg K
TA = 293.15


def root(f, a, b):
    """f's root in [a, b] by bisection, to the last bit."""
    fa = f(a)
    for _ in range(200):
        m = 0.5 * (a + b)
        if m in (a, b):
            break
        fm = f(m)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
    return 0.5 * (a + b)


def output(trad, ta):
    return Q50 * max(trad - ta, 0) ** N / 50 ** N


def water(trad, ta, q, ts):
    if q <= 0:
        return 0.0
    ka = output(trad, ta) / (trad - ta)
    return CW * q * (1 - math.exp(-ka / (CW * q))) * (ts - ta)


def design():
    phi_t = (A_WALL * U_WALL + A_WIN * U_WIN) * DT
    phi_v = 0.5 * V / 3600 * 1.2 * 1005 * DT
    phi = phi_t + phi_v
    # the design point: the design loss at the nominal flow with a 10 K water drop, at the log-mean
    # water-to-air difference EN 442's output needs
    dt_lm = 50 * (phi / Q50) ** (1 / N)
    x = root(lambda a: 10 / math.log(a / (a - 10)) - dt_lm, 10.0001, 200)
    tsupply = TA + x
    qnom = phi / (CW * 10)
    # the lumped body's temperature at the design point, where the water's heat equals the output
    trad0 = root(lambda t: water(t, TA, qnom, tsupply) - output(t, TA), TA + 1, tsupply - 1e-6)
    d = dict(
        room_volume_m3=V, window_wall_opaque_m2=A_WALL, U_wall=U_WALL, U_window=U_WIN,
        phi_transmission_W=phi_t, phi_ventilation_W=phi_v, design_heat_loss_W=phi,
        Q50_W=Q50, n=N, Crad_J_per_K=CRAD, Tsupply_K=tsupply, Tsupply_C=tsupply - 273.15,
        Treturn_design_C=tsupply - 10 - 273.15, qNom_kg_s=qnom, qNom_kg_h=qnom * 3600,
        TradInit_K=trad0, TradInit_C=trad0 - 273.15, Q_at_init_W=output(trad0, TA),
        Tclose_K=293.15 + 2, Xp_K=2.0, fMax=0.90 / 0.73, tauSen_s=600.0, TsenInit_K=293.15,
        # the body's time constant with its valve shut, linearised at the design point
        tau_body_valve_shut_s=CRAD / (N * output(trad0, TA) / (trad0 - TA)),
        sensorPoint=[0.10, 0.69, 0.57], sensorRadius=0.04,
    )
    # the most the radiator gives at full flow, in room air at 20, 15 and 8 C
    for tac in (20, 15, 8):
        ta = 273.15 + tac
        t = root(lambda t: water(t, ta, d["fMax"] * qnom, tsupply) - output(t, ta), ta + 0.01, tsupply - 1e-6)
        d[f"Q_full_flow_air_{tac}C_W"] = output(t, ta)
    return d


if __name__ == "__main__":
    print(json.dumps(design(), indent=1))
