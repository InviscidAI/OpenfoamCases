#!/usr/bin/env python3
"""Write the clip runs, fan and float, from the drag curve's answer.

    python3 scripts/make_clips.py fan|float [...]

Needs runs/motion_summary.json and runs/inlet_<run>_table.txt from
scripts/analyse_curve_motion.py. Each run is scripts/make_case.py's case with:
  * the inlet a uniformFixedValue table: fan, 10 m/s plus his fall speed v(t) from the
    motion table (481 rows, t = 0 to the moment he has fallen 7.62 m); float, his terminal
    speed, constant, still written as a table;
  * the side (y = 0) and front (x = 0) planes every T/480 s, 481 writes with t = 0;
  * 8 subdomains, as solved.
"""
from pathlib import Path
import json,re,subprocess,sys
case=Path(__file__).resolve().parents[1]
root=case/'runs'
s=json.load(open(root/'motion_summary.json')); T=s['T_hit_s']; ustar=s['terminal_speed_m_s']
want=sys.argv[1:] or ['fan','float']
for run,speed in [('fan',10.),('float',ustar)]:
 if run not in want: continue
 subprocess.run([sys.executable,str(case/'scripts/make_case.py'),run,str(speed),str(T),'clip'],check=True)
 c=root/run
 # Replace inlet U with tabulated uniform fixed value. Float table is constant but still tabulated.
 table=(root/f'inlet_{run}_table.txt').read_text().strip()
 p=c/'0/U'; txt=p.read_text()
 txt=re.sub(r'inlet \{ type fixedValue; value uniform \(0 0 [^;]+; \}',f'inlet {{ type uniformFixedValue; uniformValue table {table}; value uniform (0 0 {speed:.10g}); }}',txt)
 p.write_text(txt)
 # 480 intervals after t=0. Full cuts generated here, then postprocess_clip.py limits z to [-3,6].
 surfaces=f'''surfaces
{{
 type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval {T/480:.12g};
 surfaceFormat vtk; interpolationScheme cellPoint; fields (U p);
 surfaces
 (
  side {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (0 1 0); }} interpolate true; }}
  front {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point (0 0 0); normal (1 0 0); }} interpolate true; }}
 );
}}
'''
 ctrl=c/'system/controlDict'; x=ctrl.read_text().replace('functions {','functions { '+surfaces)
 x=x.replace(f'writeInterval {T:.12g};',f'writeInterval {T/480:.12g};')
 ctrl.write_text(x)
 dec=c/'system/decomposeParDict'
 dec.write_text(dec.read_text().replace('numberOfSubdomains 4;','numberOfSubdomains 8;'))
 # The curve's answer, copied into each run
 for f in ['drag_curve.csv','motion_table.csv','motion_summary.json',f'inlet_{run}_table.txt']:
  q=root/f
  if q.exists(): (c/f).write_bytes(q.read_bytes())
 cfg=json.load(open(c/'config.json')); cfg.update(dict(clip_writes_including_zero=481,plane_crop_z_m=[-3,6],inlet_table=f'inlet_{run}_table.txt',T_hit_s=T))
 (c/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
 print(c)
