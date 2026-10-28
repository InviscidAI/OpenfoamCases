#!/usr/bin/env python3
"""The sink's resistance by hand, to set beside the solved one.

    python3 scripts/hand_estimate.py                 the no-bypass bound and 1.5 m/s
    python3 scripts/hand_estimate.py runs/base       also at the solved air speed between the fins

1. Heat transfer in the fin channels: the composite model of Teertstra, Yovanovich and
   Culham (2000), "Analytical forced convection modeling of plate fin heat sinks",
   J. Electronics Manufacturing 10(4). It blends developing flat-plate flow with fully
   developed channel flow, and its Nusselt number is referred to the inlet air, so the
   air's own warming along the channel is inside it.
       Re* = (V b / nu) (b / L)
       Nu_b = [ (Re* Pr / 2)^-3 + (0.664 sqrt(Re*) Pr^(1/3) sqrt(1 + 3.65 / sqrt(Re*)))^-3 ]^(-1/3)
       h = Nu_b k / b
2. Fin efficiency of a straight fin with its tip folded into its height:
       eta = tanh(m Hc) / (m Hc),  m = sqrt(2 h / (k_al t)),  Hc = H + t/2
3. Spreading from the 30 x 30 mm contact into the 50 x 50 x 5 mm base: Lee, Song, Au and
   Moran (1995), "Constriction/spreading resistance model for electronics packaging",
   ASME/JSME Thermal Engineering Conference, the average-temperature form, with the square
   areas taken as circles of the same area.

The air speed between the fins is the input the hand method cannot supply: how much of the
2 m/s goes round and over the sink rather than through it. The no-bypass bound sends it all
through.
"""
import json
import math
import os
import sys

# the whole sink
N, t, H, L, W, BASE = 10, 1.0e-3, 25.0e-3, 50.0e-3, 50.0e-3, 5.0e-3
b = 4.0e-3                      # gap between fins
LEDGE = 2.0e-3                  # base left outside each outer fin
SRC = 30.0e-3                   # CPU contact, square
K_AL = 200.0
Q = 15.0
# air, from constant/air/thermophysicalProperties at 25 C and 1 bar
MU, CP, PR = 1.846e-5, 1006.43, 0.7064
RHO = 1e5 / (8314.47 / 28.966 * 298.15)
NU_AIR = MU / RHO
K_AIR = MU * CP / PR
V_APPROACH = 2.0


def sink(v):
    re_b = v * b / NU_AIR
    re_s = re_b * b / L
    nu = ((re_s * PR / 2) ** -3
          + (0.664 * math.sqrt(re_s) * PR ** (1 / 3) * math.sqrt(1 + 3.65 / math.sqrt(re_s))) ** -3) ** (-1 / 3)
    h = nu * K_AIR / b
    hc = H + t / 2
    m = math.sqrt(2 * h / (K_AL * t))
    eta = math.tanh(m * hc) / (m * hc)
    a_fins = N * 2 * hc * L
    a_base = ((N - 1) * b + 2 * LEDGE) * L
    r_conv = 1 / (h * (eta * a_fins + a_base))
    a_s = math.sqrt(SRC ** 2 / math.pi)
    b_p = math.sqrt(W * L / math.pi)
    h_eff = 1 / (r_conv * W * L)
    eps, tau, bi = a_s / b_p, BASE / b_p, h_eff * b_p / K_AL
    lam = math.pi + 1 / (math.sqrt(math.pi) * eps)
    phi = (math.tanh(lam * tau) + lam / bi) / (1 + lam / bi * math.tanh(lam * tau))
    psi_avg = 0.5 * (1 - eps) ** 1.5 * phi
    r_sp = psi_avg / (K_AL * a_s * math.sqrt(math.pi))
    r_1d = BASE / (K_AL * W * L)
    r = r_conv + r_1d + r_sp
    m_dot = RHO * v * (N - 1) * b * H
    return dict(v=v, re_b=re_b, re_star=re_s, nu_b=nu, h=h, eta=eta, r_conv=r_conv, r_1d=r_1d,
                r_sp=r_sp, r_total=r, t_base=25 + Q * r, channel_rise=Q / (m_dot * CP))


def show(label, d):
    print(label)
    print(f"  V between fins {d['v']:.3f} m/s   Re_b {d['re_b']:.0f}   Re* {d['re_star']:.1f}   Nu_b {d['nu_b']:.2f}   h {d['h']:.1f} W/m2K")
    print(f"  fin efficiency {d['eta']:.3f}")
    print(f"  R convection {d['r_conv']:.3f} + base {d['r_1d']:.3f} + spreading {d['r_sp']:.3f} = {d['r_total']:.3f} K/W")
    print(f"  base (contact mean) {d['t_base']:.1f} C;  air through the channels alone would warm {d['channel_rise']:.1f} K")


def main():
    out = {"no_bypass": sink(V_APPROACH * 5 / 4)}
    show(f"No bypass: all of the 2 m/s through the fins ({V_APPROACH * 5 / 4:.2f} m/s between them)", out["no_bypass"])
    if len(sys.argv) > 1:
        res = json.load(open(os.path.join(sys.argv[1], "results.json")))
        v = res["mid_fin_channel_velocity_m_s"]
        d = out["at_solved_speed"] = sink(v)
        show(f"At the solved speed between the fins, {v:.3f} m/s", d)
        print(f"  solved R_th {res['R_th_K_per_W']:.3f} K/W, hand {d['r_total']:.3f} K/W "
              f"({100 * (d['r_total'] / res['R_th_K_per_W'] - 1):+.0f}%)")
        with open(os.path.join(sys.argv[1], "hand_estimate.json"), "w") as f:
            json.dump(out, f, indent=1)
    else:
        show("At 1.5 m/s between the fins", sink(1.5))


if __name__ == "__main__":
    main()
