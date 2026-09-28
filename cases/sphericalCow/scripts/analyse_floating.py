#!/usr/bin/env python3
from pathlib import Path
import glob,json,math,re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import pyvista as pv
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
c=json.load(open(ROOT/'config.json')); g=json.load(open(ROOT/'geometry/geometry.json'))

def forces(mode):
    aa=[np.loadtxt(f,comments='#') for f in glob.glob(str(ROOT/'runs'/mode/'postProcessing/forceCoeffs/*/coefficient.dat'))]
    a=np.vstack(aa); a=a[np.argsort(a[:,0])]
    _,ix=np.unique(a[:,0],return_index=True)
    return a[ix]

def spectrum(t,y):
    ti=np.arange(5,25,.005); yi=np.interp(ti,t,y); yi-=np.polyval(np.polyfit(ti,yi,1),ti)
    f=np.fft.rfftfreq(len(ti),.005); p=abs(np.fft.rfft(yi))**2
    sel=(f>=.1)&(f<=10); return float(f[np.where(sel)[0][np.argmax(p[sel])]])

summary={'window_s':[5,25],'model':'kOmegaSSTSAS','delta':'cubeRootVol, deltaCoeff 1',
 'schemes':{'U':'bounded Gauss LUST grad(U)','k_omega':'bounded Gauss limitedLinear 1'},'maxCo':1,'runs':{}}
arrays={}
for mode in ('cow-floating','sphere-floating'):
    a=forces(mode); arrays[mode]=a; q=a[(a[:,0]>=5)&(a[:,0]<=25)]
    mesh=(ROOT/'runs'/mode/'log.checkMesh.standard').read_text(); cells=int(re.search(r'cells:\s+(\d+)',mesh).group(1))
    A=g['reference_frontal_area_m2'] if mode.startswith('cow') else math.pi*g['equal_volume_sphere_diameter_m']**2/4
    dynA=.5*c['rho']*c['Uinf']**2*A
    d={}; names={1:'Cd',10:'Cs',4:'Cl'}
    for col,name in names.items():
        y=q[:,col]; d[name+'_mean']=float(y.mean()); d[name+'_std']=float(y.std(ddof=1)); d[name+'_force_mean_N']=float(y.mean()*dynA); d[name+'_force_std_N']=float(y.std(ddof=1)*dynA)
    d['cells']=cells; d['samples']=len(q); d['dominant_Cd_frequency_Hz']=spectrum(q[:,0],q[:,1]); d['dominant_Cs_frequency_Hz']=spectrum(q[:,0],q[:,10])
    d['Cd_mean_5_15']=float(q[q[:,0]<=15,1].mean()); d['Cd_mean_15_25']=float(q[q[:,0]>=15,1].mean())
    d['Cd_half_window_change_percent']=100*(d['Cd_mean_15_25']/d['Cd_mean_5_15']-1)
    co=np.polyfit(q[:,0],q[:,1],1); d['Cd_fitted_drift_percent_over_20s']=float(100*co[0]*20/q[:,1].mean())
    d['five_second_blocks']=[]
    for lo in (5,10,15,20):
        b=q[(q[:,0]>=lo)&(q[:,0]<(lo+5) if lo<20 else q[:,0]<=25)]
        d['five_second_blocks'].append({'window':[lo,lo+5],'Cd_mean':float(b[:,1].mean()),'Cd_std':float(b[:,1].std(ddof=1)),'Cs_mean':float(b[:,10].mean()),'Cs_std':float(b[:,10].std(ddof=1))})
    summary['runs'][mode]=d
ref=.13; calc=summary['runs']['sphere-floating']['Cd_mean']
summary['achenbach']={'Re':c['Uinf']*g['equal_volume_sphere_diameter_m']/c['nu'],'reference_Cd_approx':ref,'reference_reading_uncertainty':.01,'computed_Cd':calc,'relative_difference_percent':100*(calc/ref-1),'result':'failed quantitative validation check'}
summary['sampling']={'plane_rate_Hz':24,'times_per_case':481,'planes':['vertical y=0','horizontal z=3 m']}
summary['compute']={'pre_run_estimate_wall_minutes':36,'pre_run_upper_minutes':47,'actual_mesh_to_completed_solve_minutes_approx':79,'actual_useful_rank_hours_approx':17.6,'actual_including_discarded_three_layer_cow_rank_hours_approx':19.0}
(OUT/'floating_summary.json').write_text(json.dumps(summary,indent=2))

fig,axs=plt.subplots(2,1,figsize=(10,6),sharex=True)
for ax,(m,col) in zip(axs,[('cow-floating','#6B4226'),('sphere-floating','#3976AF')]):
 a=arrays[m]; q=a[a[:,0]>=1]; ax.plot(q[:,0],q[:,1],lw=.55,color=col); ax.axvline(5,color='k',ls=':',lw=.8); ax.axhline(summary['runs'][m]['Cd_mean'],color='k',ls='--',lw=.8); ax.set_ylabel(m+' $C_D$'); ax.grid(alpha=.2)
axs[-1].set_xlabel('flow time (s)'); fig.suptitle('Floating SSTSAS drag; statistics use t=5–25 s'); fig.tight_layout(); fig.savefig(OUT/'floating_drag_history.png',dpi=180); plt.close(fig)

def plane(mode,name):
 p=pv.read(ROOT/'runs'/mode/'postProcessing/planes'/'25'/f'{name}.vtp').triangulate(); pts=np.asarray(p.points); faces=np.asarray(p.faces).reshape(-1,4)[:,1:]; U=np.asarray(p.point_data['U']); return pts,faces,np.linalg.norm(U,axis=1),np.asarray(p.point_data['p'])*c['rho']
for orient in ('vertical','horizontal'):
 for var,cmap,label,lim in [('speed','viridis','speed (m/s)',(0,12)),('pressure','coolwarm','gauge pressure (Pa)',(-50,50))]:
  fig,axs=plt.subplots(2,1,figsize=(11,6),sharex=True); pc=None
  for ax,m in zip(axs,('cow-floating','sphere-floating')):
   pts,faces,spd,pres=plane(m,orient); vals=spd if var=='speed' else pres; xx=pts[:,0]; yy=pts[:,2] if orient=='vertical' else pts[:,1]
   pc=ax.tripcolor(mtri.Triangulation(xx,yy,faces),vals,shading='flat',cmap=cmap,vmin=lim[0],vmax=lim[1]); ax.set_title(m); ax.set_ylabel('z (m)' if orient=='vertical' else 'y (m)'); ax.set_aspect('equal'); ax.set_xlim(-2.5,8); ax.set_ylim((1,5) if orient=='vertical' else (-2.5,2.5)); ax.set_facecolor('#e8e5dc')
  axs[-1].set_xlabel('x (m), wind →'); fig.colorbar(pc,ax=axs,label=label,shrink=.85,pad=.02); fig.suptitle(f'Floating runs: {orient} plane at t=25 s'); fig.subplots_adjust(left=.08,right=.88,bottom=.1,top=.9,hspace=.32); fig.savefig(OUT/f'floating_{orient}_{var}.png',dpi=180); plt.close(fig)
print(json.dumps(summary,indent=2))
