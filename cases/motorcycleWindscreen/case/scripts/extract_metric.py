#!/usr/bin/env python3
import re,sys,json
from pathlib import Path
rho=1.225
p=Path(sys.argv[1]) if len(sys.argv)>1 else next(Path('postProcessing/helmetMetric').glob('*/surfaceFieldValue.dat'))
rows=[]
for l in p.read_text().splitlines():
 if l.strip() and not l.lstrip().startswith('#'):
  try: rows.append([float(x) for x in l.split()])
  except: pass
if not rows: raise SystemExit(f'no metric rows in {p}')
kin=rows[-1][-1]; pa=rho*kin
out={'definition':'rho * areaAverage_helmet(sqrt(timeAverage((p-timeAverage(p))^2)))','rho_kg_m3':rho,'pRMS_kinematic_m2_s2':kin,'helmet_pRMS_Pa':pa,'source':str(p)}
Path('results').mkdir(exist_ok=True); Path('results/helmet_metric.json').write_text(json.dumps(out,indent=2)+'\n')
print(f'HELMET_RMS_PA={pa:.6g}')
