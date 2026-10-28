#!/usr/bin/env python3
"""Print a solved run's numbers from the monitors its controlDict writes.

    python3 scripts/postprocess.py runs/base

Everything is doubled from the half model to the whole sink. The heat balance compares the
15 W put into the CPU contact with the heat crossing the sink's wetted surface and with what
the air carries out of the domain, cp * sum(phi * (T - T_inlet)) over the inlet and outlet.
The drift over the last 500 iterations is printed so a run that has not settled says so,
and so are the same numbers at the end of stage 1, before the flow was frozen.
"""
import glob
import json
import os
import sys

CP = 1006.43          # constant/air/thermophysicalProperties
Q_CPU = 15.0          # W, the whole CPU
FLUX = 16666.667      # W/m2, 0.orig/heatsink/T
T_IN = 298.15


def series(case, region, fo):
    files = sorted(glob.glob(os.path.join(case, "postProcessing", region, fo, "*", "*.dat")))
    if not files:
        sys.exit(f"no monitor {region}/{fo} in {case}/postProcessing")
    rows = {}
    for f in files:
        for line in open(f):
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            rows[float(p[0])] = float(p[1].strip("()"))
    return sorted(rows.items())


def header_area(case, region, fo):
    f = sorted(glob.glob(os.path.join(case, "postProcessing", region, fo, "*", "*.dat")))[0]
    for line in open(f):
        if line.startswith("# Area"):
            return float(line.split(":")[1])
    sys.exit("no area in the cpuT monitor's header")


def wall_q(case):
    out = []
    for f in sorted(glob.glob(os.path.join(case, "postProcessing", "air", "wallQ", "*", "wallHeatFlux.dat"))):
        for line in open(f):
            p = line.split()
            if len(p) == 5 and p[1] == "air_to_heatsink":
                out.append((float(p[0]), float(p[4])))
    return out


def at(s, t):
    """The last sample at or before t."""
    best = s[0][1]
    for ti, v in s:
        if ti <= t + 1e-9:
            best = v
    return best


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "."
    cpu = series(case, "heatsink", "cpuT")
    cpumax = series(case, "heatsink", "cpuTmax")
    sinkmax = series(case, "heatsink", "sinkT")
    end = cpu[-1][0]
    t500 = end - 500
    q_in = 2 * FLUX * header_area(case, "heatsink", "cpuT")

    phi_in, phiT_in = series(case, "air", "inletPhi"), series(case, "air", "inletPhiT")
    phi_out, phiT_out = series(case, "air", "outletPhi"), series(case, "air", "outletPhiT")

    def q_air(t):
        return 2 * CP * (at(phiT_in, t) + at(phiT_out, t) - T_IN * (at(phi_in, t) + at(phi_out, t)))

    wq = wall_q(case)
    q_wall = 2 * wq[-1][1] if wq else float("nan")
    mdot = 2 * at(phi_out, end)
    t_out_bulk = at(phiT_out, end) / at(phi_out, end)

    def plane(name):
        Q = at(series(case, "air", name + "Q"), end)
        M = at(series(case, "air", name + "M"), end)
        H = at(series(case, "air", name + "H"), end)
        return 2 * Q, 2 * M, H / M
    q_mid, _, _ = plane("midPlane")
    _, m_exit, t_exit = plane("exitPlane")
    open_area = 2 * (0.025 * 0.025 - 5 * 0.001 * 0.025)   # fin envelope less the fins, m2
    v_channel = q_mid / open_area

    t_base = at(cpu, end)
    r = {
        "iterations": end,
        "T_inlet_C": T_IN - 273.15,
        "T_base_mean_C": t_base - 273.15,
        "T_base_max_C": at(cpumax, end) - 273.15,
        "T_sink_max_C": at(sinkmax, end) - 273.15,
        "R_th_K_per_W": (t_base - T_IN) / Q_CPU,
        "Q_cpu_W": q_in,
        "Q_into_air_at_sink_surface_W": q_wall,
        "Q_carried_out_by_air_W": q_air(end),
        "heat_balance_closure_pct": 100 * q_air(end) / q_in,
        "domain_mass_flow_kg_s": mdot,
        "outlet_bulk_rise_K": t_out_bulk - T_IN,
        "fin_exit_bulk_rise_K": t_exit - T_IN,
        "fin_exit_mass_flow_kg_s": m_exit,
        "mid_fin_volume_flow_m3_s": q_mid,
        "mid_fin_channel_velocity_m_s": v_channel,
        "drift_last_500_T_base_K": t_base - at(cpu, t500),
        "drift_last_500_Q_air_W": q_air(end) - q_air(t500),
    }
    print(f"iterations                      {end:.0f}")
    print(f"CPU contact (base) mean         {r['T_base_mean_C']:.2f} C   max {r['T_base_max_C']:.2f} C   sink max {r['T_sink_max_C']:.2f} C")
    print(f"inlet air                       {r['T_inlet_C']:.2f} C")
    print(f"R_th = (T_base - T_inlet)/15 W  {r['R_th_K_per_W']:.3f} K/W")
    print(f"heat in at the CPU contact      {q_in:.3f} W")
    print(f"heat into the air at the sink   {q_wall:.3f} W")
    print(f"heat carried out by the air     {r['Q_carried_out_by_air_W']:.3f} W  ({r['heat_balance_closure_pct']:.1f}% of the heat in)")
    print(f"outlet air, mixed-mean rise     {r['outlet_bulk_rise_K']:.3f} K over {mdot * 1000:.2f} g/s through the whole domain")
    print(f"air leaving the fins, bulk rise {r['fin_exit_bulk_rise_K']:.2f} K over {m_exit * 1000:.3f} g/s")
    print(f"mean air speed between the fins {v_channel:.3f} m/s at mid-length (2 m/s approaching)")
    print(f"drift over the last 500 iters   T_base {r['drift_last_500_T_base_K']:+.4f} K, heat out {r['drift_last_500_Q_air_W']:+.4f} W")
    stages = os.path.join(case, "stages")
    if os.path.exists(stages):
        flow_end = float(open(stages).read().split()[0])
        if flow_end < end:
            r["stage1_iterations"] = flow_end
            r["stage1_T_base_mean_C"] = at(cpu, flow_end) - 273.15
            r["stage1_Q_carried_out_by_air_W"] = q_air(flow_end)
            lo = [q_air(t) for t, _ in cpu if flow_end - 1000 < t <= flow_end]
            r["stage1_Q_air_last_1000_min_max_W"] = [min(lo), max(lo)]
            print(f"end of stage 1 (flow and heat)  iteration {flow_end:.0f}: base {r['stage1_T_base_mean_C']:.2f} C, "
                  f"air carries out {r['stage1_Q_carried_out_by_air_W']:.3f} W "
                  f"({min(lo):.2f} to {max(lo):.2f} W over its last 1000 iterations)")
    with open(os.path.join(case, "results.json"), "w") as f:
        json.dump(r, f, indent=1)


if __name__ == "__main__":
    main()
