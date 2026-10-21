#!/usr/bin/env python3
"""A run's results from its sampled planes and monitors, written every 0.25 s during the solve.

Never reads volume fields. The cut planes of resultPlanes are clipped here to the exact faces
asked for and integrated triangle by triangle into plane_integrals.csv. The face-flux monitors
give summary.csv, one row per write: how much colder than the outside air (2 C) the air
entering the coil reads on the coilInT monitor (uncorrected; see coil_number.py), the coil's
drop against its design value eps (T_in - Ts), the fan's flow, the coldest and warmest air, and
the gross flow each way through the three open faces of the space behind the unit. The scalar
monitor files are copied to <results dir>/monitors/<name>.dat; a run continued from a later
start time writes a file in a folder of that name, and the files are joined in time order.

For the three covers' runs (slatsDown, slatsUp, movedOut), summary.csv gains the air entering the
coil read off the upstream plane, inletUpwindSeries/up1 (cell values one cell upstream of the
inlet face, weighted by positive Ux times the face area). For movedOut the cover's front and side
planes are where its moved cover is, the front at x = 1.063 m, and the low strip is the open band
below 0.29 m. The cover is taken from the run directory's name.

    python3 scripts/extract_results.py runs/open results/open
"""
from pathlib import Path
import csv, re, shutil, sys
import numpy as np
import pyvista as pv
if len(sys.argv) != 3: raise SystemExit('usage: extract_results.py <run dir> <results dir>')
case, out = Path(sys.argv[1]), Path(sys.argv[2])
src = case/'postProcessing'/'resultPlanes'
if not src.is_dir(): raise SystemExit(f'missing {src}')
out.mkdir(parents=True, exist_ok=True)
if case.name == 'movedOut':
    FX, LOW, SX = 1.063, .29, .988
else:
    FX, LOW, SX = .775, .030, .700
# name: exact clip box, outward axis/sign. Coordinates normal to the plane include tolerance.
P={
 'coilIn': ((.2499,.2503,.3125,1.0275,0,.430),0,1),
 'coilOut':((.2897,.2901,.3125,1.0275,0,.430),0,1),
 'fanMid': ((.5495,.5505,.315,.960,0,.3225),0,1),
 # the three open faces of the space behind the unit, x 0-0.250, y 0.300-1.040, z 0-0.442 (17 Oct 2026)
 'unitTop':((0,.250,1.0395,1.0405,0,.442),1,1),
 'unitBottom':((0,.250,.2995,.3005,0,.442),1,-1),
 'unitEnd':((0,.250,.300,1.040,.4415,.4425),2,1),
 'coverFrontLow':((FX-.0005,FX+.0005,0,LOW,0,.550),0,1),
 'coverFrontHigh':((FX-.0005,FX+.0005,LOW,1.12,0,.550),0,1),
 'coverSideLow':((0,SX,0,LOW,.6245,.6255),2,1),
 'coverSideHigh':((0,SX,LOW,1.12,.6245,.6255),2,1),
}
rows=[]
for td in sorted((p for p in src.iterdir() if p.is_dir()),key=lambda p:float(p.name)):
 for name,(bounds,axis,sgn) in P.items():
  f=td/(name+'.vtk')
  if not f.exists() or f.stat().st_size==0: raise SystemExit(f'missing/empty plane {f}')
  m=pv.read(f).clip_box(bounds=bounds,invert=False).triangulate()
  if not m.n_cells: raise SystemExit(f'plane clips to zero cells: {f}')
  # Remove any tiny vertical clipping side facets: retain triangles normal to requested plane.
  ids=np.asarray(m.cells).reshape(-1,4)[:,1:]
  xyz=np.asarray(m.points)[ids]
  cr=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]); amag=np.linalg.norm(cr,axis=1)
  keep=np.abs(cr[:,axis])/np.maximum(amag,1e-300)>0.99
  a=.5*amag[keep]; ids=ids[keep]
  U=np.asarray(m.point_data['U'])[ids].mean(1)
  T=np.asarray(m.point_data['T'])[ids].mean(1)
  q=sgn*U[:,axis]
  qp=np.maximum(q,0); qn=np.maximum(-q,0)
  outward=float(np.sum(qp*a)); inward=float(np.sum(qn*a))
  Tin=float(np.sum(T*qn*a)/np.sum(qn*a)) if np.sum(qn*a)>1e-20 else float('nan')
  # For coil and fan, also report +axis flux and +axis-weighted temperature.
  forward=float(np.sum(np.maximum(U[:,axis],0)*a))
  Tf=float(np.sum(T*np.maximum(U[:,axis],0)*a)/np.sum(np.maximum(U[:,axis],0)*a)) if forward>1e-20 else float('nan')
  rows.append([float(td.name),name,float(a.sum()),outward,inward,Tin,forward,Tf])
with open(out/'plane_integrals.csv','w',newline='') as f:
 w=csv.writer(f);w.writerow(['time_s','plane','area_m2','outward_gross_m3_s','inward_gross_m3_s','inflow_weighted_T_K','positive_axis_flow_m3_s','positive_axis_weighted_T_K']);w.writerows(rows)
MONITORS = ('velocityExtrema', 'temperatureExtrema', 'zoneMeans', 'coilMeans', 'fanFlux', 'coilInFlux', 'coilInT',
            'coilOutT') + tuple(f'{n}_{op}' for n in ('behindTop', 'behindBottom', 'behindEnd') for op in ('sum', 'sumMag'))
fo = out/'monitors'
fo.mkdir(exist_ok=True)
def monitor_file(name):
    # the solver's file in each start-time folder (a t = 0 postProcess leaves a one-row file beside
    # it, so the largest), joined in time order: the rows of a later start replace an earlier one's
    # from its own first row on. A run with one start folder is copied as it is.
    starts = sorted((d for d in (case/'postProcessing'/name).iterdir() if d.is_dir()), key=lambda d: float(d.name))
    files = [max(d.glob('*.dat'), key=lambda q: q.stat().st_size) for d in starts]
    p = fo/f'{name}.dat'
    if len(files) == 1:
        shutil.copyfile(files[0], p)
        return p
    def rows(f):
        return [l for l in open(f).read().splitlines(keepends=True) if l.strip() and not l.startswith('#')]
    lines = open(files[0]).read().splitlines(keepends=True)
    for f in files[1:]:
        later = rows(f)
        t1 = float(later[0].split()[0])
        lines = [l for l in lines if l.startswith('#') or not l.strip() or float(l.split()[0]) < t1 - 1e-9] + later
    p.write_text(''.join(lines))
    return p
for name in MONITORS:
    monitor_file(name)
print(f'wrote {len(rows)} plane-time rows to {out}/plane_integrals.csv')

# Per-write summary from the face-flux monitors (17 Oct 2026): the clip's number (2 C minus the flow-weighted
# temperature of the air entering the coil), the coil's drop against eps (T_in - Ts), the fan's flow, the
# coldest and warmest air, and the gross flow each way through the three open faces of the space behind the
# unit (out = (sumMag + sum)/2, in = (sumMag - sum)/2, phi oriented outward).
def series(name):
    p = monitor_file(name)
    return {round(float(l.split()[0]), 6): l.split()[1:] for l in open(p) if not l.startswith('#') and len(l.split()) > 1}
fan, cin, tin, tout = series('fanFlux'), series('coilInFlux'), series('coilInT'), series('coilOutT')
beh = {f'{n}_{op}': series(f'{n}_{op}') for n in ('behindTop', 'behindBottom', 'behindEnd') for op in ('sum', 'sumMag')}
def extrema(name):
    # fieldMinMax rows: time, field, min, (x y z), [processor], max, (x y z), [processor]
    p = monitor_file(name)
    out = {}
    for l in open(p):
        if l.startswith('#') or not l.strip(): continue
        v = re.sub(r'\([^)]*\)', ' ', l).split()
        out[round(float(v[0]), 6)] = (float(v[2]), float(v[4] if len(v) >= 6 else v[3]))
    return out
tx = extrema('temperatureExtrema')
Ts, eps, Tout_air = 267.15, 0.4125, 275.15
srows = []
for t in sorted(fan):
    if abs(t*4 - round(t*4)) > 1e-6: continue
    Ti, To = float(tin[t][0]), float(tout[t][0])
    row = [t, Tout_air - Ti, Ti - To, eps*(Ti - Ts), float(fan[t][0]), float(cin[t][0]), tx[t][0] - 273.15, tx[t][1] - 273.15]
    for n in ('behindTop', 'behindBottom', 'behindEnd'):
        s_, m_ = float(beh[f'{n}_sum'][t][0]), float(beh[f'{n}_sumMag'][t][0])
        row += [(m_ - s_)/2, (m_ + s_)/2]
    srows.append(row)
upstream = (case/'postProcessing'/'inletUpwindSeries').is_dir()
if upstream:
    # the air entering the coil off the upstream plane, at every write
    up = {}
    for td in (case/'postProcessing'/'inletUpwindSeries').iterdir():
        f = td/'up1.vtk'
        if not f.exists(): continue
        m = pv.read(f).compute_cell_sizes()
        w = np.clip(np.asarray(m.cell_data['U'])[:, 0], 0, None)*np.asarray(m.cell_data['Area'])
        if w.sum() > 0:
            up[round(float(td.name), 6)] = Tout_air - float((w*np.asarray(m.cell_data['T'])).sum()/w.sum())
    for row in srows:
        row.append(up.get(row[0], float('nan')))
with open(out/'summary.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['time_s', 'number_K_below_outside_air', 'coil_drop_K', 'design_drop_K', 'fan_flow_m3_s', 'coil_inflow_m3_s',
                'coldest_air_C', 'warmest_air_C', 'behind_top_in_m3_s', 'behind_top_out_m3_s', 'behind_bottom_in_m3_s',
                'behind_bottom_out_m3_s', 'behind_end_in_m3_s', 'behind_end_out_m3_s']
               + (['upstream_K_below_outside_air'] if upstream else []))
    w.writerows(srows)
S = np.array(srows)
for a, b in ((50, 60), (80, 90)):
    late = S[(S[:, 0] >= a) & (S[:, 0] <= b)]
    if len(late):
        print(f'number over {a}-{b} s: {late[:,1].mean():.3f} K ({len(late)} writes); coil drop {late[:,2].mean():.3f} K '
              f'against {late[:,3].mean():.3f} K; fan {late[:,4].mean():.4f} m3/s; coldest air {S[:,6].min():.3f} C'
              + (f'; upstream plane {np.nanmean(late[:,-1]):.3f} K' if upstream else ''))
print(f'wrote {len(srows)} rows to {out}/summary.csv; last write t = {S[-1,0]:g} s, number {S[-1,1]:.3f} K')
