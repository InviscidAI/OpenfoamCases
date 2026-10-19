#!/usr/bin/env python3
"""The drag curve, his terminal speed and the fall over the 10 m/s fan.

    python3 scripts/analyse_curve_motion.py              # from runs/curve/U*/
    python3 scripts/analyse_curve_motion.py results      # from results/curve/U*/force.dat

Reads the vertical force on him in each steady run (8, 20, 40, 55 m/s), averages it over
the run's second half (the last 4 m of air past him, chosen before the runs), and writes
to runs/:
  drag_curve.csv        mean drag, CdA, the window's CV and the drift between its halves
  motion_summary.json   terminal speed u* (drag = m g), fall time and impact speed
  motion_table.csv      the fall from rest over a 10 m/s updraft, 481 rows to 7.62 m
  inlet_fan_table.txt   10 + v(t) as an OpenFOAM table, for runs/fan's inlet
  inlet_float_table.txt u*, constant, for runs/float's inlet
CdA is interpolated linearly in speed between the four runs; the fall is RK4 at 0.1 ms.
"""
from pathlib import Path
import numpy as np, json, math, sys
case=Path(__file__).resolve().parents[1]
root=case/'runs'; root.mkdir(exist_ok=True)
src=(case/sys.argv[1]/'curve') if len(sys.argv)>1 else root/'curve'
rho=1.204; A=0.5014062288640014; m=62.14978595506412; g=9.80665
speeds=[8.,20.,40.,55.]; rows=[]
for u in speeds:
 p=src/f'U{int(u)}/postProcessing/forces/0/force.dat'
 if not p.exists(): p=src/f'U{int(u)}/force.dat'
 a=np.loadtxt(p,comments='#'); t=a[:,0]; d=a[:,3]
 end=8/u; sel=t>=end/2; x=d[sel]
 # settling: first and second half of predeclared averaging window; variability and drift
 mid=3*end/4; m1=d[(t>=end/2)&(t<mid)].mean(); m2=d[t>=mid].mean()
 mean=x.mean(); sd=x.std(ddof=1); cda=2*mean/(rho*u*u)
 rows.append([u,mean,cda,sd/mean,100*(m2-m1)/mean,len(x),end/2,end,1.75*u/1.516e-5])
# csv
hdr='speed_m_s,mean_D_N,CdA_m2,window_CV,second_minus_first_half_percent,n_samples,window_start_s,window_end_s,Re_length_1p75m'
np.savetxt(root/'drag_curve.csv',np.array(rows),delimiter=',',header=hdr,comments='',fmt='%.10g')
cdas=np.array(rows)[:,2]
def cda(u): return float(np.interp(u,speeds,cdas))
def drag(u): return .5*rho*cda(abs(u))*u*abs(u)
# bisection terminal
lo,hi=0.,80.
for _ in range(80):
 q=(lo+hi)/2
 if drag(q)<m*g: lo=q
 else: hi=q
ustar=(lo+hi)/2
# RK4 coupled v,s; fixed tiny integration then interpolate exact hit
h=1e-4; t=0.; v=0.; z=0.; dat=[(t,z,v,10+v)]
def f(v): return g-drag(10+v)/m
while z<7.62:
 k1v=f(v); k1z=v
 k2v=f(v+.5*h*k1v); k2z=v+.5*h*k1v
 k3v=f(v+.5*h*k2v); k3z=v+.5*h*k2v
 k4v=f(v+h*k3v); k4z=v+h*k3v
 v2=v+h*(k1v+2*k2v+2*k3v+k4v)/6
 z2=z+h*(k1z+2*k2z+2*k3z+k4z)/6
 t2=t+h
 if int(t2*1000)!=int(t*1000): dat.append((t2,z2,v2,10+v2))
 t,v,z=t2,v2,z2
# the hit, interpolated back linearly from the first step past 7.62 m
T=t-(z-7.62)/v; vhit=v-f(v)*(t-T)
# 481 rows from t = 0 to the hit, interpolated in the stored (1 ms) integration
ar=np.array(dat); tq=np.linspace(0,T,481); zq=np.interp(tq,ar[:,0],ar[:,1]); vq=np.interp(tq,ar[:,0],ar[:,2]); zq[-1]=7.62; vq[-1]=vhit
out=np.c_[tq,zq,vq,10+vq]
np.savetxt(root/'motion_table.csv',out,delimiter=',',header='time_s,distance_fallen_m,v_down_m_s,Uin_fan_m_s',comments='',fmt='%.10g')
# OpenFOAM vector table fragment
with open(root/'inlet_fan_table.txt','w') as f:
 f.write('(\n'); [f.write(f'({tt:.10g} (0 0 {uu:.10g}))\n') for tt,uu in zip(tq,10+vq)]; f.write(')\n')
with open(root/'inlet_float_table.txt','w') as f: f.write(f'((0 (0 0 {ustar:.10g})) ({T:.10g} (0 0 {ustar:.10g})))\n')
summary=dict(mass_kg=m,g_m_s2=g,weight_N=m*g,rho_kg_m3=rho,reference_area_m2=A,terminal_speed_m_s=ustar,T_hit_s=T,impact_speed_m_s=vhit,float_updraft_m_s=ustar,fan_initial_quasisteady_weight_share=drag(10)/(m*g),fan_final_quasisteady_weight_share=drag(10+vhit)/(m*g),motion_integration_dt_s=h)
(root/'motion_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2)); print(np.array(rows))
