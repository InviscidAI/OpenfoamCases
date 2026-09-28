#!/usr/bin/env python3
from pathlib import Path
import json, math, re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import pyvista as pv
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
c=json.load(open(ROOT/'config.json')); g=json.load(open(ROOT/'geometry/geometry.json'))

def read_force(mode):
    rows=[]
    p=ROOT/'runs'/mode/'postProcessing/forceCoeffs/0/coefficient.dat'
    for line in p.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        try: rows.append([float(x) for x in line.split()])
        except ValueError: pass
    return np.asarray(rows)

def spectral(t,y):
    ti=np.arange(5,25,0.005); yi=np.interp(ti,t,y)
    trend=np.polyfit(ti,yi,1); yd=yi-np.polyval(trend,ti)
    f=np.fft.rfftfreq(len(ti),.005); power=abs(np.fft.rfft(yd))**2
    sel=(f>0.1)&(f<20); ix=np.where(sel)[0][np.argmax(power[sel])]
    return float(f[ix]),float(trend[0])

summary={'geometry':g,'air':{'rho_kg_m3':c['rho'],'nu_m2_s':c['nu'],'speed_m_s':c['Uinf']},'runs':{}}
arrays={}
for mode in ('cow','sphere','isolated'):
    a=read_force(mode); arrays[mode]=a; q=a[(a[:,0]>=5)&(a[:,0]<=25)]
    info=json.load(open(ROOT/'runs'/mode/'caseInfo.json'))
    mesh=(ROOT/'runs'/mode/'log.checkMesh.standard').read_text()
    cells=int(re.search(r'cells:\s+(\d+)',mesh).group(1))
    cd=q[:,1]; freq,slope=spectral(q[:,0],cd)
    A=info['Aref_m2']; drag=cd.mean()*0.5*c['rho']*c['Uinf']**2*A
    blocks=[]
    for lo in range(5,25):
        b=cd[(q[:,0]>=lo)&(q[:,0]<lo+1)]; blocks.append(float(b.mean()))
    pre=a[(a[:,0]>=1)&(a[:,0]<=5),1]
    summary['runs'][mode]={'cells':cells,'Re':info['Re'],'Aref_m2':A,
      'Cd_mean_t5_25':float(cd.mean()),'Cd_std_t5_25':float(cd.std(ddof=1)),
      'drag_N_mean_t5_25':float(drag),'Cd_mean_t1_5':float(pre.mean()),
      'settled_mean_change_percent':float(100*(cd.mean()/pre.mean()-1)),
      'linear_drift_percent_over_20s':float(100*slope*20/cd.mean()),
      'one_second_Cd_means':blocks,'dominant_Cd_frequency_Hz':freq,
      'samples_retained':int(len(cd)),'final_Cd':float(a[-1,1])}
# Achenbach 1972 smooth-sphere curve, approximate digitized/interpolated reading.
ref=0.13
iso=summary['runs']['isolated']['Cd_mean_t5_25']
summary['achenbach']={'Re':summary['runs']['isolated']['Re'],
 'reference_Cd_approx':ref,'reference_reading_uncertainty':0.01,
 'source':'Achenbach (1972), J. Fluid Mech. 54, 565-575; approximate interpolation of smooth-sphere supercritical data near Re=7.86e5',
 'computed_Cd':iso,'relative_difference_percent':100*(iso/ref-1)}
summary['sampling']={'settle_interval_s':[0,5],'retained_window_s':[5,25],
 'plane_rate_Hz':24,'plane_times_per_ground_case':481,
 'planes':['vertical y=0','horizontal at run mid-body z']}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))

# Drag history after startup spike.
fig,axs=plt.subplots(3,1,figsize=(9,7),sharex=True)
for ax,(mode,col) in zip(axs,[('cow','#6B4226'),('sphere','#3976AF'),('isolated','#666666')]):
    a=arrays[mode]; q=a[a[:,0]>=0.5]; ax.plot(q[:,0],q[:,1],lw=.65,color=col)
    ax.axvspan(0.5,5,color='#CCCCCC',alpha=.25); ax.axhline(summary['runs'][mode]['Cd_mean_t5_25'],color='k',lw=.8,ls='--')
    ax.set_ylabel(mode+' $C_D$'); ax.grid(alpha=.2)
axs[-1].set_xlabel('flow time (s)'); fig.suptitle('Transient drag; dashed lines are t=5–25 s means')
fig.tight_layout(); fig.savefig(OUT/'drag_history.png',dpi=180); plt.close(fig)

# Final sampled-plane preview. Pressure is kinematic in OpenFOAM and converted to Pa.
def plane_data(mode,plane,time='25'):
    p=pv.read(ROOT/'runs'/mode/'postProcessing/planes'/time/f'{plane}.vtp').triangulate()
    pts=np.asarray(p.points); faces=np.asarray(p.faces).reshape(-1,4)[:,1:]
    U=np.asarray(p.point_data['U']); return pts,faces,np.linalg.norm(U,axis=1),np.asarray(p.point_data['p'])*c['rho']
for plane in ('vertical','horizontal'):
  for var,cmap,label,lims in [('speed','viridis','speed (m/s)',(0,12)),('pressure','coolwarm','gauge pressure (Pa)',(-50,50))]:
    fig,axs=plt.subplots(2,1,figsize=(11,6),sharex=True)
    pc=None
    for ax,mode in zip(axs,('cow','sphere')):
      pts,faces,speed,press=plane_data(mode,plane); vals=speed if var=='speed' else press
      xx=pts[:,0]; yy=pts[:,2] if plane=='vertical' else pts[:,1]
      tri=mtri.Triangulation(xx,yy,faces); pc=ax.tripcolor(tri,vals,shading='flat',cmap=cmap,vmin=lims[0],vmax=lims[1])
      ax.set_title(mode); ax.set_ylabel('z (m)' if plane=='vertical' else 'y (m)'); ax.set_aspect('equal')
      ax.set_xlim(-2.5,8); ax.set_ylim((0,3) if plane=='vertical' else (-2.5,2.5)); ax.set_facecolor('#E8E5DC')
    axs[-1].set_xlabel('x (m), wind →'); fig.colorbar(pc,ax=axs,label=label,shrink=.85,pad=.02)
    fig.suptitle(f'{plane} plane at t=25 s (one frame of 481)')
    fig.subplots_adjust(left=.08,right=.88,bottom=.10,top=.90,hspace=.32)
    fig.savefig(OUT/f'{plane}_{var}.png',dpi=180); plt.close(fig)
print(json.dumps(summary,indent=2))
