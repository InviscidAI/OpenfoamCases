"""The warm-up a real car's cabin would follow with this case's defroster, from a measured model.

usage: python3 warmup_reference.py [out.csv]

Brusey, Hintea, Gaura and Beloe, "Reinforcement learning-based thermal comfort control for vehicle
cabins" (Mechatronics 50, 2018; arXiv 1704.07899v2, section 3.1-3.2 and Table 1) fitted a lumped
cabin model to warm-up and cool-down runs of a Jaguar XJ in MIRA's climatic wind tunnel
(head-rest height sensors; their Figures 3 and 4). Their equations (3)-(5):

    Q_h + I_in (T_amb - T_c) = I_fan (T_x - T_c)
    I_fan (T_x - T_c) + Q_sol + Q_occ + (T_m - T_c)/R_m = (T_c - T_amb)/R_c + C_c k dT_c/dt
    (T_c - T_m)/R_m = C_m dT_m/dt

with V_c = 2.5 m3, k = 8, R_c = 1/(5.741626794 x 4.0) K/W, R_m = 1/(75 x 1.08) K/W,
C_m = 450 x 0.02 x 7850 J/K. Here their cabin is scaled to this case's, 1.54 m2 of section x 1.45 m
= 2.23 m3: every capacity and conductance in proportion to the volume. The supply is this case's:
100 l/s of 3 C air (0.127 kg/s), through a heater of effectiveness 0.6 against 85 C coolant, from
outside (T_x = 52.2 C) or from the cabin (T_x = T_c + 0.6 (85 - T_c)); two occupants at 72 W; no sun.
Cabin and interior mass start at 5 C. Prints both, per 10 s, and writes a CSV.
"""
import math
import sys

V_OURS = 1.5394 * 1.45
S = V_OURS / 2.5                     # scale from the Jaguar's cabin to ours
RHO, CP = 1.27, 1005.0
C_C = 2.5 * 1.2 * CP * S             # Brusey's C_c = V_c rho c_p (rho 1.2 assumed), scaled
K = 8.0
G_C = 5.741626794 * 4.0 * S          # 1/R_c, W/K
G_M = 75 * 1.08 * S                  # 1/R_m, W/K
C_M = 450 * 0.02 * 7850 * S          # J/K
T_AMB, T0 = 3.0, 5.0
MCP = 0.100 * (1e5 / (287.1 * 276.15)) * CP   # 100 l/s of outside air, W/K
Q_OCC = 2 * 72.0
EPS, T_COOL = 0.6, 85.0


def run(mode, t_end=600.0, dt=0.05):
    tc, tm, t, out = T0, T0, 0.0, []
    while t <= t_end + 1e-9:
        t_in = T_AMB if mode == "outside" else tc
        tx = t_in + EPS * (T_COOL - t_in)
        if abs(t / 10 - round(t / 10)) < 1e-6:
            out.append((round(t), tc, tm, tx))
        dtc = (MCP * (tx - tc) + Q_OCC + G_M * (tm - tc) - G_C * (tc - T_AMB)) / (C_C * K)
        dtm = G_M * (tc - tm) / C_M
        tc += dt * dtc
        tm += dt * dtm
        t += dt
    return out


if __name__ == "__main__":
    a, b = run("outside"), run("recirc")
    print(f"scale {S:.3f}: C_c k {C_C * K / 1e3:.1f} kJ/K, C_m {C_M / 1e3:.1f} kJ/K, G_m {G_M:.1f} W/K, "
          f"G_c {G_C:.1f} W/K, supply {MCP:.1f} W/K")
    print("   t   outside: cabin  mass  supply | recirc: cabin  mass  supply")
    for (t, c1, m1, x1), (_, c2, m2, x2) in zip(a, b):
        if t % 30 == 0 or t <= 120 and t % 10 == 0:
            print(f"{t:4d}   {c1:13.2f} {m1:5.2f} {x1:7.2f} | {c2:13.2f} {m2:5.2f} {x2:7.2f}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            f.write("t,outside_cabin,outside_mass,outside_supply,recirc_cabin,recirc_mass,recirc_supply\n")
            for (t, c1, m1, x1), (_, c2, m2, x2) in zip(a, b):
                f.write(f"{t},{c1:.4f},{m1:.4f},{x1:.4f},{c2:.4f},{m2:.4f},{x2:.4f}\n")
