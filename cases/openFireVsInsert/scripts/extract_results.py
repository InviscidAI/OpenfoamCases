#!/usr/bin/env python3
"""results/ from the two runs' monitors: each run's history every 0.625 s and a summary.

    python3 scripts/extract_results.py RUNS RESULTS

RUNS holds open/ and insert/, each with postProcessing/metrics/metrics.csv as the monitor in
system/functions writes it (no header: the columns are scripts/columns_<run>.json). Temperatures
are written in C (the monitor's are K). "Other rooms" is the hall, the study and the kitchen-diner,
volume-weighted from y = 0.10 to 1.80 m: the number each panel of the clip shows, in whole F.
"""
from pathlib import Path
import json, sys
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
F = lambda c: c * 9 / 5 + 32
GAPS = ['gapFrontDoor', 'gapBackDoor', 'gapWinLF', 'gapWinLB', 'gapWinS', 'gapWinK']
TIMES = [5, 15, 30, 60, 150, 240, 300]


def load(runs, run):
    cols = json.loads((HERE / f'scripts/columns_{run}.json').read_text())
    d = pd.read_csv(Path(runs) / run / 'postProcessing/metrics/metrics.csv', header=None, names=cols)
    return d.drop_duplicates('time', keep='last').reset_index(drop=True)


def history(d, run):
    h = pd.DataFrame({'time_s': d.time.round(6)})
    for room in ['other', 'living', 'kitchen', 'hall', 'study', 'whole']:
        h[f'{room}_occupied_C'] = d[f'{room}_occupied_T'] - 273.15
    for room in ['other', 'living', 'whole']:
        h[f'{room}_mean_C'] = d[f'{room}_mean_T'] - 273.15
    for room in ['living', 'other']:
        h[f'{room}_ankle_C'] = d[f'{room}_ankle_T'] - 273.15     # y < 0.10 m
        h[f'{room}_ceiling_C'] = d[f'{room}_ceiling_T'] - 273.15  # y > 2.20 m
    h['sofa_front_air_C'] = d.sofa_front_air_T - 273.15
    h['outdoor_air_in_kg_s'] = sum(d[g + '_min'] for g in GAPS)
    h['house_air_out_kg_s'] = sum(d[g + '_mout'] for g in GAPS)
    h['under_doors_in_kg_s'] = d.gapFrontDoor_min + d.gapBackDoor_min
    if run == 'open':
        h['chimney_kg_s'] = d.throat_mout
        h['fire_radiation_into_room_W'] = -(d.Qrad_firePanel + d.Qrad_recess + d.Qrad_throat)
    else:
        h['chimney_kg_s'] = d.combustionAir_mout
        h['jacket_out_C'] = d.jacketOut_T - 273.15
        h['fire_radiation_into_room_W'] = -d.Qrad_glass
    for p in ['ceiling', 'walls', 'floor']:
        h[f'{p}_convection_W'] = d[f'Qconv_{p}']                  # air to surface, positive
        h[f'{p}_radiation_absorbed_W'] = d[f'Qrad_{p}']
    h['hearth_surface_max_C'] = d.hearth_surface_max_T - 273.15
    h['Tmin_air_C'] = d.Tmin - 273.15
    h['Tmax_air_C'] = d.Tmax - 273.15
    h['dt_s'] = d.dt
    return h


def at(h, t):
    return h.iloc[(h.time_s - t).abs().argmin()]


def main(runs, out):
    out = Path(out); hs = {}
    for run in ['open', 'insert']:
        hs[run] = history(load(runs, run), run)
        (out / run).mkdir(parents=True, exist_ok=True)
        hs[run].to_csv(out / run / 'history.csv', index=False, float_format='%.6g')
    L = ['Open fire against stove insert: the same ground floor from lighting, 0-300 s.',
         'From the monitors of the runs (system/functions), by scripts/extract_results.py. C and F.', '',
         'The other rooms (hall, study, kitchen-diner) from y = 0.10 to 1.80 m, volume-weighted air temperature:']
    for t in TIMES:
        o, i = at(hs['open'], t), at(hs['insert'], t)
        L.append(f'  {t:4d} s   open {o.other_occupied_C:8.4f} C ({F(o.other_occupied_C):5.2f} F)   insert {i.other_occupied_C:8.4f} C ({F(i.other_occupied_C):5.2f} F)'
                 f'   insert - open {i.other_occupied_C - o.other_occupied_C:+.4f} K')
    L += ['', 'The living room and the whole floor, every height, volume-weighted:']
    for t in TIMES:
        o, i = at(hs['open'], t), at(hs['insert'], t)
        L.append(f'  {t:4d} s   living open {o.living_mean_C:7.3f} insert {i.living_mean_C:7.3f} C;   whole open {o.whole_mean_C:7.3f} insert {i.whole_mean_C:7.3f} C;'
                 f'   living ceiling (y > 2.2 m) open {o.living_ceiling_C:6.2f} insert {i.living_ceiling_C:6.2f} C')
    L += ['', 'Air (kg/s) and heat (W):']
    for run in ['open', 'insert']:
        for t in [15, 60, 150, 300]:
            r = at(hs[run], t)
            ach = r.outdoor_air_in_kg_s * 3600 / 1.22 / 150.6
            L.append(f'  {run:6s} {t:3d} s   outdoor air in {r.outdoor_air_in_kg_s:.4f} ({ach:.2f} air changes an hour), {r.under_doors_in_kg_s:.4f} of it under the doors;'
                     f' house air out through the gaps {r.house_air_out_kg_s:.4f}; up the chimney {r.chimney_kg_s:.4f};'
                     f' radiation into the room {r.fire_radiation_into_room_W:.0f} W; air to the ceiling {r.ceiling_convection_W:.0f} W, to the walls {r.walls_convection_W:.0f} W, to the floor {r.floor_convection_W:.0f} W')
    L += ['', 'Checks:']
    for run in ['open', 'insert']:
        h = hs[run]; late = h[h.time_s >= 5]
        L.append(f'  {run:6s} {len(h)} monitor rows, 0-{h.time_s.iloc[-1]:g} s; coldest air after 5 s {late.Tmin_air_C.min():.3f} C, warmest {late.Tmax_air_C.max():.2f} C;'
                 f' last time step {h.dt_s.iloc[-1]:.5f} s')
    (out / 'summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: extract_results.py RUNS RESULTS')
    main(*sys.argv[1:])
