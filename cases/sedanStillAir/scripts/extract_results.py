"""Write results/ from the two runs' monitors.

    python3 scripts/extract_results.py <runs dir> <results dir> [--door-name doorFan]

Reads <runs>/<run>/postProcessing/diagnostics89/diagnostics.csv (scripts/diagnostics.template,
a row every 0.125 s of flow, at the first step and at the first step after a restart). Files
an earlier segment left in diagnostics89.before_<t>/ (run_case.py --resume) are joined in front,
their running sums carried on. --door-name is the door run's folder under <runs> (the solved
one was called doorFanContinuous). Writes <results>/<run>/history.csv every 0.25 s and
<results>/summary.txt. NumPy only.
"""
import sys,csv,argparse
from pathlib import Path
import numpy as np

OPENINGS={'fourWindows':['frontLeft','rearLeft','frontRight','rearRight'],'doorFan':['rearLeft','doorAperture']}
REPORT=[0.5,1,2,3,5,7.25,10,15,20,30,45,50,60]
RUNNING=['cumulative_surfaces_J','cumulative_adv_J','cumulative_diff_J','wall_s']
F=lambda K:(K-273.15)*1.8+32

def read(path):
    with open(path) as f:
        rows=[r for r in csv.reader(f) if r]
    return {n:np.array([float(r[i]) for r in rows[1:]]) for i,n in enumerate(rows[0])}

def load(run):
    pp=run/'postProcessing'
    parts=sorted(pp.glob('diagnostics89.before_*'),key=lambda p:float(p.name.split('_',1)[1]))+[pp/'diagnostics89']
    d=None
    for part in parts:
        s=read(part/'diagnostics.csv')
        if d is not None:
            keep=s['time']>d['time'][-1]+1e-9
            for k in RUNNING:s[k]=s[k]+d[k][-1]
            d={k:np.concatenate([d[k],s[k][keep]]) for k in d}
        else:d=s
    return d

def on_grid(d):
    t=d['time'];keep=np.abs(t*8-np.round(t*8))<1e-6;keep[0]=True
    return {k:v[keep] for k,v in d.items()}

def at(d,c,t):return float(np.interp(t,d['time'],d[c]))
def mean(d,reg,q='T',t=None):
    if q=='T':return F(d[reg+'_TV']/d[reg+'_V']) if t is None else F(at(d,reg+'_TV',t)/at(d,reg+'_V',t))
    return 100*(d[reg+'_outdoorMass']/d[reg+'_mass'] if t is None else at(d,reg+'_outdoorMass',t)/at(d,reg+'_mass',t))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('runs');ap.add_argument('results');ap.add_argument('--door-name',default='doorFan');a=ap.parse_args()
    runs=Path(a.runs);res=Path(a.results);folder={'fourWindows':'fourWindows','doorFan':a.door_name}
    raw={k:load(runs/v) for k,v in folder.items()};D={k:on_grid(v) for k,v in raw.items()}
    out=[]
    for k,d in D.items():
        t=d['time'];H0=d['cabin_H'][0]
        cols={'time_s':t,'heads_F':mean(d,'heads'),'row1_F':mean(d,'row1'),'row2_F':mean(d,'row2')}
        for h in range(1,6):cols['head%d_F'%h]=mean(d,'head%d'%h)
        cols.update({'cabin_F':mean(d,'cabin'),'heads_outdoor_pct':mean(d,'heads','o'),'cabin_outdoor_pct':mean(d,'cabin','o'),
                     'excess_heat_J':d['cabin_H'],'excess_removed_pct':100*(1-d['cabin_H']/H0),
                     'dashboard_W':d['dashboard_W'],'seats_W':d['seats_W'],'cabinInterior_W':d['cabinInterior_W']})
        for o in OPENINGS[k]:cols[o+'_in_Ls']=1000*d[o+'_Qin'];cols[o+'_out_Ls']=1000*d[o+'_Qout']
        if k=='doorFan':
            cols['door_angle_deg']=np.degrees(d['theta_rad']);cols['door_maskVolume_m3']=d['door_maskVolume']
            cols['door_diffusion_into_cabin_W']=d['doorAperture_diffusionInto_W']
        sel=np.isclose((t*4)%1,0,atol=1e-6)|(np.arange(len(t))==0)
        (res/k).mkdir(parents=True,exist_ok=True)
        with open(res/k/'history.csv','w',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(list(cols))
            for i in np.where(sel)[0]:w.writerow(['%.6g'%cols[c][i] for c in cols])
        out.append(f'{k} (solved as {folder[k]}): {len(t)} monitor rows, {t[0]:g} to {t[-1]:g} s, {int(d["step"][-1])} time steps, '
                   f'{d["wall_s"][-1]:.0f} s of wall time; the cabin starts with {H0:.1f} J above 310.93 K')
    out.append('')
    out.append('Head-height air, the mean of the five head boxes (20 x 24 x 20 cm at z 1.04-1.24 m), F; rows 1/2; the cabin\'s volume mean, F')
    out.append('  t, s | '+' | '.join(f'{k:34s}' for k in D))
    for t in REPORT:
        out.append(f'{t:6g} | '+' | '.join(f'{mean(d,"heads",t=t):6.2f}  {mean(d,"row1",t=t):6.2f}/{mean(d,"row2",t=t):6.2f}  cabin {mean(d,"cabin",t=t):6.2f}' for d in D.values()))
    a4,ad=D['fourWindows'],D['doorFan'];tt=a4['time'][a4['time']>=.125]
    diff=np.interp(tt,a4['time'],mean(a4,'heads'))-np.interp(tt,ad['time'],mean(ad,'heads'))
    cross=[tt[i]-diff[i]*(tt[i+1]-tt[i])/(diff[i+1]-diff[i]) for i in range(len(tt)-1) if diff[i]*diff[i+1]<0]
    out.append('the heads\' means cross from 0.125 s on at: '+(', '.join('%.3f s'%c for c in cross) if cross else 'never')+
               f'; doorFan is the cooler at every row from 0.125 to 60 s: {bool((diff>0).all())}; the gap is {diff.min():.2f} to {diff.max():.2f} F')
    out.append('')
    out.append('Each head box, F (1 front driver, 2 front passenger, 3 rear driver side, 4 rear middle, 5 rear passenger side)')
    for t in [3,10,30,60]:
        out.append(f'{t:6g} | '+' | '.join(k+' '+'/'.join('%.1f'%mean(d,'head%d'%h,t=t) for h in range(1,6)) for k,d in D.items()))
    out.append('')
    out.append('Outside air (the tracer) at the heads and in the cabin, % of the mass; the starting excess heat gone, %')
    for t in [0.5,3,10,30,60]:
        out.append(f'{t:6g} | '+' | '.join(f'{k:12s} heads {mean(d,"heads","o",t):5.1f}  cabin {mean(d,"cabin","o",t):5.1f}  gone {100*(1-at(d,"cabin_H",t)/d["cabin_H"][0]):5.1f}' for k,d in D.items()))
    out.append('')
    out.append('Gross flow each way through the openings, L/s (in / out), the mean over each period (trapezoidal over the monitor rows)')
    for k,d in D.items():
        for t0,t1 in [(0,7.25),(0,30),(0,60),(30,60)]:
            m=(d['time']>=t0-1e-9)&(d['time']<=t1+1e-9);tm=d['time'][m];V=d['cabin_V'][0]
            q=lambda c:np.trapezoid(d[c][m],tm)/(tm[-1]-tm[0]) if hasattr(np,'trapezoid') else np.trapz(d[c][m],tm)/(tm[-1]-tm[0])
            qin=sum(q(o+'_Qin') for o in OPENINGS[k])
            out.append(f'  {k:12s} {t0:4g}-{t1:<5g} s  '+', '.join(f'{o} {1000*q(o+"_Qin"):.0f}/{1000*q(o+"_Qout"):.0f}' for o in OPENINGS[k])+
                       f'; in all {1000*qin:.1f} L/s, {60*qin/V:.2f} cabin volumes a minute')
    out.append('')
    out.append('The cabin\'s energy budget from the monitor\'s running sums: the change in the cabin air\'s enthalpy above 310.93 K against the hot surfaces\' heat,')
    out.append('the enthalpy advected through the openings and the heat diffused through their planes, kJ (pressure work and kinetic energy are not in it)')
    for k,d in D.items():
        for t0,t1 in [(1,60),(1,7.25),(1,50)]:
            i0=np.argmin(abs(d['time']-t0));i1=np.argmin(abs(d['time']-t1))
            c={n:d[n][i1]-d[n][i0] for n in RUNNING[:3]};dH=d['cabin_H'][i1]-d['cabin_H'][i0];pred=sum(c.values());thr=sum(abs(v) for v in c.values())
            out.append(f'  {k:12s} {t0:g}-{t1:g} s: surfaces {c[RUNNING[0]]/1e3:+.2f}, advected {c[RUNNING[1]]/1e3:+.2f}, diffused {c[RUNNING[2]]/1e3:+.2f}; '
                       f'change in the air {dH/1e3:+.2f}; residual {dH-pred:+.1f} J, {100*(dH-pred)/abs(pred):+.2f}% of the net change, {100*(dH-pred)/thr:+.3f}% of the throughput')
    d=ad;sw=(d['time']>1)&(d['time']<59.9)
    out.append('')
    out.append(f'doorFan, the door\'s masked volume from 1 s: {d["door_maskVolume"][sw].min():.4f} to {d["door_maskVolume"][sw].max():.4f} m3 (0.2160 shut); '
               f'its largest angle {np.degrees(d["theta_rad"]).max():.2f} degrees; at 60 s {np.degrees(d["theta_rad"][-1]):.2f} degrees')
    out.append(f'doorFan, diffusion into the cabin through the door\'s plane, W: '+', '.join(f'{at(d,"doorAperture_diffusionInto_W",t):.1f} at {t:g} s' for t in [10,30,60]))
    for k,d in raw.items():
        t=d['time'];off=np.where(np.abs(t*8-np.round(t*8))>1e-6)[0];off=off[off>0]
        for i in off:
            out.append(f'{k}: a restart at {t[i-1]:g} s; its first step, to {t[i]:.8f} s, moved the head boxes by '+', '.join('%+.5f'%(d['head%d_TV'%h][i]/d['head%d_V'%h][i]-d['head%d_TV'%h][i-1]/d['head%d_V'%h][i-1]) for h in range(1,6))+
                       f' K and the cabin by {d["cabin_TV"][i]/d["cabin_V"][i]-d["cabin_TV"][i-1]/d["cabin_V"][i-1]:+.5f} K')
    for k,d in D.items():
        out.append(f'{k}: hottest cabin air {d["Tmax"].max():.2f} K, coolest {d["Tmin"].min():.2f} K; the dashboard, seats and trim give '
                   f'{d["dashboard_W"][-1]:.1f}, {d["seats_W"][-1]:.1f} and {d["cabinInterior_W"][-1]:.1f} W at 60 s')
    (res/'summary.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out))

main()
