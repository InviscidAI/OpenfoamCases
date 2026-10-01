#!/usr/bin/env python3
from pathlib import Path
import pandas as pd, numpy as np, json
root=Path(__file__).resolve().parents[1]
rho=1.225; U=5.41; A=.384; qA=.5*rho*U**2*A
window=(2.5,4.0)
bodies={'alone':['runner'],'behind':['runner','pacer'],'pair':['runner','pacer','pacer2']}
def stats(path,a,b):
 d=pd.read_csv(path,comment='#',sep=r'\s+',header=None); t=d[0].to_numpy(); x=d[1].to_numpy()
 use=(t>=a)&(t<=b); z=x[use]; tt=t[use]; mid=(a+b)/2
 h1=x[(t>=a)&(t<mid)]; h2=x[(t>=mid)&(t<=b)]
 slope=np.polyfit(tt,z,1)[0]
 return {'samples':int(len(z)),'Cd_mean':float(z.mean()),'Cd_temporal_SD':float(z.std(ddof=1)),
 'drag_N_mean':float(z.mean()*qA),'drag_N_temporal_SD':float(z.std(ddof=1)*qA),
 'drag_N_firstHalf':float(h1.mean()*qA),'drag_N_secondHalf':float(h2.mean()*qA),
 'half_change_pct_of_mean':float(100*(h2.mean()-h1.mean())/z.mean()),'linear_slope_N_per_s':float(slope*qA)}
out={'model':'kOmegaSSTSAS','window_s':list(window),'qA_N':qA,'cases':{}}
for c,bs in bodies.items():
 out['cases'][c]={b:stats(root/f'runs/{c}/postProcessing/forceCoeffs_{b}/0/coefficient.dat',*window) for b in bs}
out['runner_drag_reduction_pct']={'behind':100*(1-out['cases']['behind']['runner']['drag_N_mean']/out['cases']['alone']['runner']['drag_N_mean']),'pair':100*(1-out['cases']['pair']['runner']['drag_N_mean']/out['cases']['alone']['runner']['drag_N_mean'])}
# Side-by-side legacy URANS uses its original predeclared 2-3 s window.
out['URANS_comparison']={}
for c in ['alone','behind']:
 out['URANS_comparison'][c]={'SAS_2.5_4':out['cases'][c]['runner'],'URANS_2_3':stats(root/f'runs_URANS_kOmegaSST/{c}/postProcessing/forceCoeffs_runner/0/coefficient.dat',2,3)}
lit=6.52*(5.41/5.83)**2*(.384/.44)
out['literature_scaled_N']=lit
out['SAS_alone_vs_scaled_literature_pct']=100*(out['cases']['alone']['runner']['drag_N_mean']/lit-1)
(root/'results').mkdir(exist_ok=True)
(root/'results/summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
