#!/usr/bin/env python3
"""After a clip run: the force on him every step, with the inflow and his weight's share.

    python3 scripts/postprocess_clip.py fan|float

Writes runs/<run>/forces_with_inlet_and_weight_share.csv (every step, the t = 0 evaluation
first) and runs/<run>/clip_summary.json: the time-weighted mean share, the first and last,
and for fan the fall integrated again from the run's own force history instead of the drag
curve, against the curve's fall time and impact speed. It then crops the sampled planes to
z = -3 to +6 m in place (needs pyvista; skipped with a note in the summary without it).
"""
from pathlib import Path
import numpy as np, json, sys
root=Path(__file__).resolve().parents[1]/'runs'; run=sys.argv[1]; c=root/run
m=62.14978595506412; g=9.80665; W=m*g
p=c/'postProcessing/forces/0/force.dat'
# OpenFOAM starts force_0.dat when the solver follows a t=0 postProcess invocation.
parts=[np.loadtxt(p,comments='#')]
q=p.with_name('force_0.dat')
if q.exists(): parts.append(np.loadtxt(q,comments='#'))
a=np.vstack([x[None,:] if x.ndim==1 else x for x in parts]); a=a[np.argsort(a[:,0])]; a=a[np.r_[True,np.diff(a[:,0])>1e-14]]
# Add explicit t=0 row if function output omitted it (normally postProcess generated it).
if a.ndim==1: a=a[None,:]
if a[0,0]>1e-14: a=np.vstack(([0]+[0]*(a.shape[1]-1),a))
motion=np.loadtxt(root/'motion_table.csv',delimiter=',',skiprows=1); U=np.interp(a[:,0],motion[:,0],motion[:,3]) if run=='fan' else np.full(len(a),json.load(open(root/'motion_summary.json'))['terminal_speed_m_s'])
Cd=a[:,3]/(0.5*1.204*0.5014062288640014*U**2)
out=np.c_[a,U,Cd,a[:,3]/W]
h='time_s,total_x_N,total_y_N,total_z_N,pressure_x_N,pressure_y_N,pressure_z_N,viscous_x_N,viscous_y_N,viscous_z_N,Uin_m_s,Cd_on_0p501406m2,weight_share'
np.savetxt(c/'forces_with_inlet_and_weight_share.csv',out,delimiter=',',header=h,comments='',fmt='%.10g')
# Time-weighted summary and fan force-history re-integration
T=float(a[-1,0]); mean=np.trapezoid(a[:,3]/W,a[:,0])/T
res={'time_weighted_mean_weight_share':float(mean),'start_weight_share':float(a[0,3]/W),'end_weight_share':float(a[-1,3]/W),'T_history_s':T}
if run=='fan':
 t=a[:,0]; D=a[:,3]; acc=g-D/m; v=np.zeros(len(t)); z=np.zeros(len(t))
 for i in range(1,len(t)):
  dt=t[i]-t[i-1]; v[i]=v[i-1]+.5*(acc[i-1]+acc[i])*dt; z[i]=z[i-1]+.5*(v[i-1]+v[i])*dt
 target=7.62
 if z[-1]>=target:
  j=np.argmax(z>=target); q=(target-z[j-1])/(z[j]-z[j-1]); th=t[j-1]+q*(t[j]-t[j-1]); vh=v[j-1]+q*(v[j]-v[j-1])
  support='within solved force window'
 else:
  # Constant final force extrapolation, explicitly marked. Usually not needed.
  aa=acc[-1]; dz=target-z[-1]; dt=(-v[-1]+np.sqrt(max(0,v[-1]**2+2*aa*dz)))/aa if abs(aa)>1e-12 else dz/v[-1]
  th=t[-1]+dt; vh=v[-1]+aa*dt; support='constant-final-force extrapolation beyond solved window'
 tab=json.load(open(root/'motion_summary.json')); res.update(force_history_T_hit_s=float(th),force_history_impact_speed_m_s=float(vh),delta_T_hit_s=float(th-tab['T_hit_s']),delta_impact_speed_m_s=float(vh-tab['impact_speed_m_s']),motion_check_support=support,distance_at_table_T_m=float(z[-1]))
# Crop function-object planes in place to requested common region.
try:
 import pyvista as pv
 for f in (c/'postProcessing/surfaces').glob('*/*.vtp'):
  mesh=pv.read(f)
  if mesh.bounds.z_min >= -3.000001 and mesh.bounds.z_max <= 6.000001: continue
  clipped=mesh.clip_box(bounds=(-1.500001,1.500001,-1.500001,1.500001,-3.0,6.0),invert=False)
  clipped.extract_surface().save(f,binary=True)
 res['planes_cropped_z_m']=[-3,6]
except Exception as e: res['plane_crop_error']=repr(e)
(c/'clip_summary.json').write_text(json.dumps(res,indent=2)+'\n')
print(run,json.dumps(res))
