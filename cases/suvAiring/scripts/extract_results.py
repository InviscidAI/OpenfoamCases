"""Write results/ from the solved runs' monitors.

    python3 scripts/extract_results.py <runs dir> <results dir>

Reads <runs>/<run>/postProcessing/diagnostics83/diagnostics.csv (scripts/diagnostics.C, a row every
0.125 s of flow, at the first step and at the first step after each restart), and for the door's
swings door_swing_integrals.csv. The cabin's starting excess heat above the outside air's
310.93 K is taken from the run's mapped start (initial_state.npz and mesh_arrays.npz, as
scripts/run_case.py leaves them), or else from the first monitor row. Writes
<results>/<run>/history.csv every 0.25 s and <results>/summary.txt. NumPy only.
"""
import sys,csv
from pathlib import Path
import numpy as np

KINDS=['fourWindows','doorFan']
OPENINGS={'fourWindows':[('frontLeft',60),('rearLeft',70),('frontRight',80),('rearRight',90)],'doorFan':[('rearLeft',70),('doorAperture',100)]}
REPORT=[0.5,1,2,3,5,10,15,18,20,30,45]
TOUT=310.93
F=lambda K:(K-273.15)*1.8+32

def load(path):
    with open(path) as f:
        rows=list(csv.reader(f))
    names=rows[0];data=np.array([[float(x) for x in r] for r in rows[1:] if r])
    t=data[:,0];keep=np.ones(len(t),bool)
    # a restart writes a row at its first step just after the write it started from; the grid
    # rows (every 0.125 s) are kept and the off-grid rows dropped, but for the very first step
    off=np.abs(t*8-np.round(t*8))>1e-6;keep[off]=False;keep[0]=True
    d={n:data[keep,i] for i,n in enumerate(names)}
    return d

def at(d,c,t):return float(np.interp(t,d['time'],d[c]))

def region(d,heads,t=None):
    v=lambda k:d['v%d'%k] if t is None else at(d,'v%d'%k,t)
    vol=sum(v(6*h) for h in heads);mass=sum(v(6*h+1) for h in heads)
    return sum(v(6*h+2) for h in heads)/vol,sum(v(6*h+4) for h in heads)/mass

def initialH(run,d):
    q=run/'initial_state.npz';m=run/'mesh_arrays.npz'
    if q.exists() and m.exists():
        q=np.load(q);C=np.load(m)['C']
        sel=np.all((C>=np.array([1.76,-.84,.44])-1e-8)&(C<=np.array([5.56,.84,1.84])+1e-8),axis=1)&((C[:,2]<=1.12+1e-8)|(C[:,0]>=1.80+(C[:,2]-1.12)*.60/.72-1e-8))
        rho=q['p']/((8314.46261815324/28.96)*q['T'])
        return float(np.sum(rho[sel]*1005*(q['T'][sel]-TOUT)*.04**3)),'the mapped start'
    return float(d['v5'][0]),'the first monitor row (t = %g s)'%d['time'][0]

def budget(d,t0,t1):
    D=lambda c:at(d,c,t1)-at(d,c,t0)
    H=D('v5');KE=D('v134');cv=D('CV_heat_integral_J');adv=D('adv_integral_J');diff=D('diff_integral_J')
    full=H+KE-cv-adv+diff-D('pressure_integral_J')-D('gravity_integral_J')-D('KE_adv_in_integral_J')
    return {'H':H,'cv':cv,'adv':adv,'diff':diff,'full':full,'frac':full/cv}

def main(runs,results):
    runs=Path(runs);results=Path(results);out=[];D={};H0={}
    for k in KINDS:
        d=load(runs/k/'postProcessing/diagnostics83/diagnostics.csv');D[k]=d;H0[k],src=initialH(runs/k,d)
        out.append(f'{k}: {len(d["time"])} monitor rows, {d["time"][0]:g} to {d["time"][-1]:g} s; the cabin starts with {H0[k]:.1f} J above {TOUT} K (from {src})')
        grid=np.round(np.arange(0,d['time'][-1]+1e-9,.25),6);grid[0]=d['time'][0]
        cols=['time_s','heads_F','row1_F','row2_F','row3_F']+['head%d_F'%h for h in range(1,9)]+['cabin_F','heads_outdoor_pct','cabin_outdoor_pct','cabin_mean_speed_ms','excess_heat_J','excess_removed_pct','dashboard_W','seats_W','cabinInterior_W']
        for n,_ in OPENINGS[k]:cols+=[n+'_in_Ls',n+'_out_Ls']
        if k=='doorFan':cols+=['door_angle_deg','shut_door_diffusion_W']
        (results/k).mkdir(parents=True,exist_ok=True)
        with open(results/k/'history.csv','w',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(cols)
            for t in grid:
                row=[t,F(region(d,range(1,9),t)[0])]+[F(region(d,ids,t)[0]) for ids in [(1,2),(3,4,5),(6,7,8)]]+[F(region(d,[h],t)[0]) for h in range(1,9)]
                Tc,sc=region(d,[0],t);row+=[F(Tc),100*region(d,range(1,9),t)[1],100*sc,at(d,'v143',t)/at(d,'v0',t),at(d,'v5',t),100*(1-at(d,'v5',t)/H0[k]),at(d,'v120',t),at(d,'v121',t),at(d,'v122',t)]
                for n,o in OPENINGS[k]:row+=[1000*at(d,'v%d'%o,t),1000*at(d,'v%d'%(o+1),t)]
                if k=='doorFan':row+=[np.degrees(np.pi/6*(1-np.cos(2*np.pi*t/1.2))) if t<=18 else 0.,at(d,'v109',t)]
                w.writerow(['%.6g'%x for x in row])
    out.append('')
    out.append('Head-height air, the mean of the eight head boxes (20 x 24 x 20 cm at z 1.40-1.60 m), F; rows 1/2/3; the cabin\'s volume mean, F')
    out.append('%6s | %-36s | %-36s'%('t, s','fourWindows','doorFan'))
    for t in [0.0001]+REPORT:
        cells=[]
        for k in KINDS:
            d=D[k];cells.append('%6.2f  %6.2f/%6.2f/%6.2f  cabin %6.2f'%(F(region(d,range(1,9),t)[0]),*[F(region(d,ids,t)[0]) for ids in [(1,2),(3,4,5),(6,7,8)]],F(region(d,[0],t)[0])))
        out.append('%6g | %s | %s'%(t,cells[0],cells[1]))
    a=D['fourWindows'];b=D['doorFan'];tt=a['time'][a['time']>=.5]
    diff=np.array([region(a,range(1,9),t)[0]-region(b,range(1,9),t)[0] for t in tt]);s=np.flatnonzero(np.sign(diff[1:])!=np.sign(diff[:-1]))
    cross=[float(tt[i]-diff[i]*(tt[i+1]-tt[i])/(diff[i+1]-diff[i])) for i in s]
    out.append('the heads\' means cross after 0.5 s at: '+', '.join('%.3f s'%c for c in cross)+' (linear between monitor rows); fourWindows is the cooler from then to 45 s' if len(cross)==1 else 'crossings: %s'%cross)
    out.append('')
    out.append('Outside air (the tracer) at the heads and in the cabin, % of the mass; the starting excess heat gone, %')
    for t in REPORT:
        out.append('%6g | '%t+' | '.join('%-12s heads %5.1f  cabin %5.1f  gone %5.1f'%(k,100*region(D[k],range(1,9),t)[1],100*region(D[k],[0],t)[1],100*(1-at(D[k],'v5',t)/H0[k])) for k in KINDS))
    out.append('')
    out.append('Gross flow each way through the openings, L/s (in / out), the mean over each period')
    for k in KINDS:
        d=D[k]
        for t0,t1 in [(.5,1),(1,3),(3,18),(18.5,30),(30,45)]:
            sel=(d['time']>=t0-1e-9)&(d['time']<=t1+1e-9);parts=[];tot=0
            for n,o in OPENINGS[k]:
                i,o_=1000*d['v%d'%o][sel].mean(),1000*d['v%d'%(o+1)][sel].mean();parts.append('%s %.0f/%.0f'%(n,i,o_));tot+=i
            out.append('  %-12s %5g-%-4g s  %s; in all %.0f L/s, %.2f cabin volumes a minute'%(k,t0,t1,', '.join(parts),tot,tot/1000*60/at(d,'v0',t1)))
    out.append('')
    out.append('Heat into the cabin\'s air and where it went, kJ: from the cabin\'s hot surfaces, carried out by the air through the openings (net), diffused out through the openings\' planes, and the change in the cabin\'s air')
    for k in KINDS:
        for t0,t1 in [(1,45),(18,45)]:
            q=budget(D[k],t0,t1)
            out.append('  %-12s %g-%g s: surfaces %.2f, out with the air %.2f, diffused out %.2f, change in the air %+.2f; the full energy budget closes to %+.2f J, %+.3f%% of the surfaces\' heat'%(k,t0,t1,q['cv']/1e3,-q['adv']/1e3,q['diff']/1e3,q['H']/1e3,q['full'],100*q['frac']))
    for t in [10,18,30,45]:out.append('  doorFan diffusion through the plane of the door (shut from 18 s) at %g s: %.2f W'%(t,at(b,'v109',t)))
    sw=Path(runs/'doorFan/postProcessing/diagnostics83/door_swing_integrals.csv')
    if sw.exists():
        out.append('');out.append('doorFan, air moved each swing, m3: the rear-left window in / out, the door\'s aperture in / out')
        with open(sw) as f:
            for r in csv.DictReader(f):out.append('  swing %2s, %5.1f-%4.1f s: window %.4f / %.4f, door %.4f / %.4f'%(r['swing'],float(r['from_s']),float(r['to_s']),float(r['g1_integral0']),float(r['g1_integral1']),float(r['g4_integral0']),float(r['g4_integral1'])))
    out.append('')
    for k in KINDS:
        d=D[k];i=int(np.argmax(d['Tmax_K']))
        out.append('%s: hottest cabin air %.3f K, coolest %.3f K over the run; the dashboard, seats and trim give %.1f, %.1f and %.1f W at 45 s'%(k,d['Tmax_K'].max(),d['Tmin_K'].min(),at(d,'v120',45),at(d,'v121',45),at(d,'v122',45)))
    (results/'summary.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out))

if __name__=='__main__':main(*sys.argv[1:3])
