#!/usr/bin/env python3
"""The curtain runs' report, 0-300 s: heat crossing x = 0.15 into the room, the 7.5 s heat
budgets, the probes, the flows over the curtain's top and under its hem, and the 300 s fields.

    python3 postprocess_curtains.py [runs/start300] [results/curtains]

Reads runs/start300/hanging and runs/start300/tucked. Writes <run>_history.csv,
<run>_heat_budget.csv, <run>_probes.csv, summary.md and final_fields.png, and a t = 0 plane
(T = 293.15 K, U = 0) into each run's postProcessing/clip/0/, which the solver does not write.
"""
from pathlib import Path
import csv, re, sys
from collections import defaultdict
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
HERE=Path(__file__).parent
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'runs/start300'
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else HERE/'results/curtains'; OUT.mkdir(parents=True,exist_ok=True)
CP=1005.; R=8314.462618/28.96; T0=293.15; SOURCE=60.; CV_R=(CP-R)/R; E0=CV_R*1e5*9.6

def rows(path):
 for line in path.read_text().splitlines():
  if line.strip() and not line.startswith('#'): yield line.split()
def wall_data(rd):
 d=defaultdict(dict)
 for r in rows(rd/'postProcessing/wallHeatFlux/0/wallHeatFlux.dat'): d[r[1]][float(r[0])]=float(r[4])
 return d
def interp_dict(d,t,initial=0):
 x=np.array(sorted(d)); y=np.array([d[a] for a in x]); return float(np.interp(t,x,y,left=initial,right=y[-1]))
def section(path):
 m=pv.read(path); cc=m.cell_centers().points
 xs=np.unique(cc[:,0].round(7)); ys=np.unique(cc[:,1].round(7)); ix=np.searchsorted(xs,cc[:,0].round(7));iy=np.searchsorted(ys,cc[:,1].round(7))
 F={}
 for n,v in [('T',np.asarray(m.cell_data['T'])),('u',np.asarray(m.cell_data['U'])[:,0]),('v',np.asarray(m.cell_data['U'])[:,1])]:
  a=np.empty((len(ys),len(xs)));a[iy,ix]=v;F[n]=a
 return m,xs,ys,F
def edges(c,lo,hi): return np.r_[lo,(c[1:]+c[:-1])/2,hi]
def overlap_weights(c,lo,hi,domlo,domhi):
 e=edges(c,domlo,domhi);return np.maximum(0,np.minimum(e[1:],hi)-np.maximum(e[:-1],lo))
def across_col(xs,a,x):
 i=np.searchsorted(xs,x); w=(x-xs[i-1])/(xs[i]-xs[i-1]);return (1-w)*a[:,i-1]+w*a[:,i]
def across_row(ys,a,y):
 j=np.searchsorted(ys,y); w=(y-ys[j-1])/(ys[j]-ys[j-1]);return (1-w)*a[j-1]+w*a[j]
def probes(rd):
 ts=[]; T=[]; U=[]
 for r in rows(rd/'postProcessing/probes/0/T'):ts.append(float(r[0]));T.append([float(x)-273.15 for x in r[1:]])
 for r in rows(rd/'postProcessing/probes/0/U'):
  vals=re.findall(r'\(([^)]*)\)', ' '.join(r[1:]));U.append([np.linalg.norm(list(map(float,x.split()))) for x in vals])
 return np.array(ts),np.array(T),np.array(U)
def budget(rd,walls):
 er={float(r[0]):CV_R*float(r[1]) for r in rows(rd/'postProcessing/energyCheck/0/volFieldValue.dat')}
 te=np.array(sorted(er));ee=np.array([er[t] for t in te]); rec=[]
 for k in range(1,41):
  a,b=7.5*(k-1),7.5*k; row={'t_start_s':a,'t_end_s':b,'radiator_W_per_m':60.}; total=60.
  for patch in ['glass','ceiling','innerWall','floor','outerWall']:
   dd=walls[patch];tw=np.array(sorted(dd));ww=np.array([dd[t] for t in tw]);m=(tw>a)&(tw<=b+1e-9)
   q=np.sum(ww[m]*np.diff(np.r_[a,tw[m]]))/(b-a);row[patch+'_W_per_m']=q;total+=q
  ea=E0 if a==0 else np.interp(a,te,ee);row['stored_W_per_m']=(np.interp(b,te,ee)-ea)/(b-a);row['unaccounted_W_per_m']=total-row['stored_W_per_m'];rec.append(row)
 return rec
def write_csv(path,recs):
 with open(path,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=recs[0].keys(),lineterminator='\n');w.writeheader();w.writerows(recs)
summary={}
for run in ['hanging','tucked']:
 rd=BASE/run; walls=wall_data(rd); dirs=sorted((p for p in (rd/'postProcessing/clip').iterdir() if float(p.name)>0),key=lambda p:float(p.name)); rec=[]  # the t = 0 plane is written below
 # establish grid and create the requested t=0 VTK plane
 m0,xs,ys,F0=section(dirs[0]/'clip.vtp'); z=pv.read(dirs[0]/'clip.vtp');z.cell_data['T'][:]=T0;z.cell_data['U'][:]=0;(rd/'postProcessing/clip/0').mkdir(exist_ok=True);z.save(rd/'postProcessing/clip/0/clip.vtp',binary=True)
 all_dirs=[rd/'postProcessing/clip/0']+dirs
 dx=overlap_weights(xs,0,4,0,4);dy=overlap_weights(ys,0,2.4,0,2.4);A=np.outer(dy,dx);X,Y=np.meshgrid(xs,ys)
 for n,d in enumerate(all_dirs):
  t=float(d.name)
  if t==0: F={'T':np.full_like(F0['T'],T0),'u':np.zeros_like(F0['u']),'v':np.zeros_like(F0['v'])}
  else: _,_,_,F=section(d/'clip.vtp')
  uc=across_col(xs,F['u'],.15);Tc=across_col(xs,F['T'],.15);rho=1e5/(R*Tc)
  wy=dy.copy()
  if run=='hanging': wy[(ys>=0.007608029076)&(ys<=2.196430812)]=0
  adv=float(np.sum(rho*uc*CP*(Tc-T0)*wy)); cond=interp_dict(walls['curtainB'],t,0) if run=='hanging' else 0.; q=adv+cond
  vt=across_row(ys,F['v'],2.20); wx=overlap_weights(xs,0,.15,0,4)
  top_up=float(np.sum(np.maximum(vt,0)*wx));top_down=float(np.sum(np.maximum(-vt,0)*wx))
  if run=='hanging':
   ug=across_col(xs,F['u'],.15);wg=overlap_weights(ys,0,.01,0,2.4);gap_room=float(np.sum(np.maximum(ug,0)*wg));gap_behind=float(np.sum(np.maximum(-ug,0)*wg))
  else: gap_room=gap_behind=np.nan
  room=X>.15
  behind=(X<.15) if run=='hanging' else ((Y>=.9)&(Y<=2.2)&(X < .15*(Y-.9)/1.3))
  avg=lambda mask:float(np.sum(F['T'][mask]*A[mask])/np.sum(A[mask])-273.15)
  rec.append({'time_s':t,'advected_sensible_enthalpy_into_room_W_per_m':adv,'curtain_conduction_into_room_W_per_m':cond,'total_heat_into_room_W_per_m':q,'instantaneous_share_of_60W':q/60.,'cumulative_heat_into_room_J_per_m':0.,'cumulative_radiator_J_per_m':60*t,'cumulative_share':0. if t==0 else np.nan,'glass_heat_loss_W_per_m':-interp_dict(walls['glass'],t,0),'radiator_output_W_per_m':60.,'room_side_mean_C':avg(room),'behind_curtain_mean_C':avg(behind),'top_up_m3_s_per_m':top_up,'top_down_m3_s_per_m':top_down,'hem_gap_into_room_m3_s_per_m':gap_room,'hem_gap_into_behind_m3_s_per_m':gap_behind})
 tt=np.array([r['time_s'] for r in rec]);qq=np.array([r['total_heat_into_room_W_per_m'] for r in rec]);cum=np.r_[0,np.cumsum((qq[1:]+qq[:-1])/2*np.diff(tt))]
 for r,c in zip(rec,cum):r['cumulative_heat_into_room_J_per_m']=c;r['cumulative_share']=0 if r['time_s']==0 else c/(60*r['time_s'])
 write_csv(OUT/f'{run}_history.csv',rec)
 bt=budget(rd,walls);write_csv(OUT/f'{run}_heat_budget.csv',bt)
 pt,pT,pU=probes(rd); prec=[]
 for i,t in enumerate(np.r_[0,pt]):
  valsT=np.full(6,20.) if i==0 else pT[i-1];valsU=np.zeros(6) if i==0 else pU[i-1];row={'time_s':t}
  for j,(x,y) in enumerate([(1,.1),(2,.1),(3,.1),(1,1.1),(2,1.1),(3,1.1)]):row[f'T_C_x{x:g}_y{y:g}']=valsT[j];row[f'speed_m_s_x{x:g}_y{y:g}']=valsU[j]
  prec.append(row)
 write_csv(OUT/f'{run}_probes.csv',prec)
 summary[run]={'final':rec[-1],'budget':bt,'history':rec}
# compact markdown summary
L=['# Curtain comparison, 0–300 s','', '| run | cumulative heat into room | share of 60 W radiator | final instantaneous crossing | final glass loss |','|---|---:|---:|---:|---:|']
for run,s in summary.items():
 r=s['final'];L.append(f"| {run} | {r['cumulative_heat_into_room_J_per_m']/1000:.2f} kJ/m | {100*r['cumulative_share']:.1f}% | {r['total_heat_into_room_W_per_m']:.2f} W/m | {r['glass_heat_loss_W_per_m']:.2f} W/m |")
L+=['','The crossing enthalpy is the solver’s sensible enthalpy reference, `rho*Ux*Cp*(T-293.15 K)`, net into x>0.15. For hanging, curtainB is the room-side mapped-wall patch and its wall heat flux is added.','']
for run,s in summary.items():
 u=np.array([x['unaccounted_W_per_m'] for x in s['budget']]);r=s['final'];L += [f"## {run}",f"At 300 s: room-side mean {r['room_side_mean_C']:.2f} C; behind-curtain mean {r['behind_curtain_mean_C']:.2f} C; top gross up/down {r['top_up_m3_s_per_m']:.4f}/{r['top_down_m3_s_per_m']:.4f} m3/s/m.",f"7.5 s budget unaccounted: mean {u.mean():+.3f}, range {u.min():+.3f} to {u.max():+.3f} W/m.",'']
(OUT/'summary.md').write_text('\n'.join(L))
# final comparison image
fig,ax=plt.subplots(2,2,figsize=(12,6),constrained_layout=True)
for row,run in enumerate(['hanging','tucked']):
 m=pv.read(BASE/run/'postProcessing/clip/300/clip.vtp');cc=m.cell_centers().points;T=np.asarray(m.cell_data['T'])-273.15;S=np.linalg.norm(np.asarray(m.cell_data['U']),axis=1)
 for col,(v,title,cmap,lims) in enumerate([(T,'Temperature (C)','coolwarm',(17,24)),(S,'Speed (m/s)','viridis',(0,.25))]):
  a=ax[row,col];im=a.tripcolor(cc[:,0],cc[:,1],v,shading='flat',cmap=cmap,vmin=lims[0],vmax=lims[1]);a.set_aspect('equal');a.set_xlim(0,4);a.set_ylim(0,2.4);a.set_title(f'{run}: {title}, 300 s');fig.colorbar(im,ax=a)
  if run=='hanging':a.plot([.15,.15],[.007608,2.196431],'k-',lw=2)
  else:a.plot([0,.15],[.9,2.2],'k-',lw=2)
fig.savefig(OUT/'final_fields.png',dpi=160)
print((OUT/'summary.md').read_text())
