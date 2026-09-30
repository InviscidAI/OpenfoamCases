#!/usr/bin/env python3
import sys, re, subprocess, shutil
from pathlib import Path
import numpy as np, pandas as pd
import pyvista as pv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
case=Path(sys.argv[1]); root=case/'postProcessing/rzFace'
heights=[0.10,1.09,1.70,2.75]; labels=['010','109','170','275']; R=3.441282078
files=[]
for p in root.glob('*/rz.vtp'):
 try: files.append((float(p.parent.name),p))
 except: pass
files.sort(); rows=[]
for t,p in files:
 m=pv.read(p)
 row={'time_s':t}
 for h,lbl in zip(heights,labels):
  line=pv.Line((0,0,h),(R-0.004,0,h),resolution=700)
  s=line.sample(m)
  valid=np.asarray(s['vtkValidPointMask']).astype(bool); r=s.points[:,0][valid]
  T=np.asarray(s['T'])[valid]; U=np.asarray(s['U'])[valid]; order=np.argsort(r); r,T,U=r[order],T[order],U[order]
  den=np.trapezoid(r,r)
  row['T'+lbl+'_K']=np.trapezoid(T*r,r)/den
  if h<2:
   row['draft'+lbl]=np.trapezoid((np.linalg.norm(U,axis=1)>=0.15)*r,r)/den
 rows.append(row)
out=case/'results'; out.mkdir(exist_ok=True)
df=pd.DataFrame(rows); df.to_csv(out/'history.csv',index=False)
# Endpoint and exact-axis regularity metrics.
m=pv.read(files[-1][1]); pts=m.points; U=np.asarray(m['U']); T=np.asarray(m['T'])
ax=np.abs(pts[:,0])<1e-10; near=(pts[:,0]>0)&(pts[:,0]<0.021)
metrics={'axis_max_abs_Ur_mps':float(np.max(np.abs(U[ax,0]))),'axis_max_abs_Utheta_mps':float(np.max(np.abs(U[ax,1]))),'near_axis_max_abs_Ur_mps':float(np.max(np.abs(U[near,0]))),'near_axis_max_abs_Utheta_mps':float(np.max(np.abs(U[near,1])))}
# Endpoint cell maxima in and outside the actual enlarged heater zone.
# foamToVTK preserves cell-centred T; the temporary export is removed afterward.
subprocess.run(['foamToVTK','-case',str(case),'-latestTime','-ascii','-no-boundary'], check=True, stdout=subprocess.DEVNULL)
vtu=next((case/'VTK').glob('*/internal.vtu'))
vm=pv.read(vtu); cc=vm.cell_centers().points; Tc=np.asarray(vm.cell_data['T']).reshape(-1)
rr=np.sqrt(cc[:,0]**2+cc[:,1]**2)
heater=(rr >= 3.191282078-1e-8) & (rr <= R+1e-8) & (cc[:,2] >= -1e-8) & (cc[:,2] <= 0.50+1e-8)
metrics['heater_cell_count']=int(np.count_nonzero(heater))
metrics['heater_zone_Tmax_K']=float(np.max(Tc[heater]))
metrics['room_outside_heater_Tmax_K']=float(np.max(Tc[~heater]))
shutil.rmtree(case/'VTK')
# Full-circle fan-plane integrals reconstructed from the solved half-face.
line=pv.Line((0,0,2.67),(0.76,0,2.67),resolution=500); fs=line.sample(m); ok=np.asarray(fs['vtkValidPointMask']).astype(bool); fr=fs.points[:,0][ok]; fu=np.asarray(fs['U'])[ok]; o=np.argsort(fr); fr,fu=fr[o],fu[o]
metrics['fan_axial_Q_m3s']=float(2*np.pi*np.trapezoid(fu[:,2]*fr,fr))
metrics['fan_area_mean_Utheta_mps']=float(2*np.trapezoid(fu[:,1]*fr,fr)/(0.76**2))
end=df.iloc[-1]
with open(out/'summary.txt','w') as f:
 f.write(f'case={case.name}\nend_time_s={end.time_s}\n')
 for l in labels: f.write(f'T{l}_K={end["T"+l+"_K"]:.6f}\n')
 f.write(f'deltaT_275_minus_010_K={end.T275_K-end.T010_K:.6f}\n')
 for l in labels[:3]: f.write(f'draft{l}={end["draft"+l]:.8f}\n')
 for k,v in metrics.items(): f.write(f'{k}={v:.9g}\n')
# histories
fig,axp=plt.subplots(2,1,figsize=(8,7),sharex=True)
for l,h in zip(labels,heights): axp[0].plot(df.time_s,(df['T'+l+'_K']-273.15),label=f'{h:.2f} m')
for l,h in zip(labels[:3],heights[:3]): axp[1].plot(df.time_s,100*df['draft'+l],label=f'{h:.2f} m')
axp[0].set_ylabel('Area-weighted T (°C)'); axp[1].set_ylabel('Draft area ≥0.15 m/s (%)'); axp[1].set_xlabel('Time (s)')
for a in axp: a.grid(True,alpha=.3); a.legend(ncol=4)
fig.tight_layout(); fig.savefig(out/'history.png',dpi=160); plt.close(fig)
# final solved half face, four scalar panels
tri=m.triangulate(); r=tri.points[:,0]; z=tri.points[:,2]; vals=[T-273.15,U[:,0],U[:,1],U[:,2]]; titles=['T (°C)','Ur (m/s)','Utheta (m/s)','Uz (m/s)']
fig,axs=plt.subplots(2,2,figsize=(10,7),sharex=True,sharey=True)
for a,v,title in zip(axs.flat,vals,titles):
 c=a.tripcolor(r,z,tri.faces.reshape(-1,4)[:,1:],v,shading='gouraud',cmap='coolwarm'); fig.colorbar(c,ax=a); a.set_title(title); a.set_aspect('equal'); a.set_xlabel('r (m)'); a.set_ylabel('z (m)')
fig.tight_layout(); fig.savefig(out/'final_rz.png',dpi=170); plt.close(fig)
print(out/'summary.txt')
