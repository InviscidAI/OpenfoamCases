#!/usr/bin/env python3
"""Combine OpenFOAM function-object histories and summarize the configured settled window."""
from pathlib import Path
import json, numpy as np, pandas as pd
R=Path(__file__).resolve().parents[1]; C=json.loads((R/'config/model.json').read_text())
Troom=C['roomTemperature_K']; rho=C['rhoReference_kg_m3']; a,b=C['settledWindow_s']
# Layouts without a run here keep their published row in results/summary.csv.
layouts=[x for x in C['layouts'] if (R/'runs'/x/'postProcessing').is_dir()]; quantities=['gpuIntake','cpuIntake','casePressure']
vents=['vent_front','vent_top','vent_slots']
def read_dat(p):
    rows=[]
    for line in p.read_text().splitlines():
        if line.lstrip().startswith('#') or not line.strip(): continue
        z=line.split(); rows.append((float(z[0]),float(z[1])))
    return pd.DataFrame(rows,columns=['time','value']).drop_duplicates('time',keep='last').set_index('time')
summary=[]
(R/'results').mkdir(exist_ok=True)
for layout in layouts:
    base=R/'runs'/layout/'postProcessing'; series={}
    for q in quantities:
        series[q]=read_dat(base/q/'0/surfaceFieldValue.dat' if q!='casePressure' else base/q/'0/volFieldValue.dat')['value']
    for v in vents:
        net=read_dat(base/(v+'_net')/'0/surfaceFieldValue.dat')['value']; ab=read_dat(base/(v+'_absolute')/'0/surfaceFieldValue.dat')['value']
        series[v+'_out']=0.5*(ab+net); series[v+'_in']=0.5*(ab-net); series[v+'_net']=net
    df=pd.DataFrame(series).sort_index(); df['gpuRise_C']=df.gpuIntake-Troom; df['cpuRise_C']=df.cpuIntake-Troom; df['casePressure_Pa']=rho*df.casePressure
    # unused-fan net flow from instantaneous external continuity; sign is outward.
    la=C['layouts'][layout]; Qin=sum(C['fan140Flow_m3_s'] if x.startswith('top_') else C['fan120Flow_m3_s'] for x in la['intake']); Qout=sum(C['fan140Flow_m3_s'] if x.startswith('top_') else C['fan120Flow_m3_s'] for x in la['exhaust'])
    df['unusedFans_net']=-(Qout-Qin)-sum(df[v+'_net'] for v in vents)
    df['totalExternalIn']=Qin+sum(df[v+'_in'] for v in vents)+np.maximum(-df.unusedFans_net,0)
    df['dustUnfilteredFraction']=df['vent_slots_in']/df.totalExternalIn
    df.to_csv(R/'results'/f'{layout}_history.csv')
    w=df.loc[a:b]; h1=w.loc[a:(a+b)/2]; h2=w.loc[(a+b)/2:b]
    row={'layout':layout,'window_s':f'{a:g}-{b:g}','samples':len(w),
         'gpu_rise_C':w.gpuRise_C.mean(),'gpu_rise_std_C':w.gpuRise_C.std(),'gpu_half_change_C':h2.gpuRise_C.mean()-h1.gpuRise_C.mean(),
         'cpu_rise_C':w.cpuRise_C.mean(),'cpu_rise_std_C':w.cpuRise_C.std(),'cpu_half_change_C':h2.cpuRise_C.mean()-h1.cpuRise_C.mean(),
         'case_pressure_Pa':w.casePressure_Pa.mean(),'pressure_std_Pa':w.casePressure_Pa.std(),'pressure_half_change_Pa':h2.casePressure_Pa.mean()-h1.casePressure_Pa.mean(),
         'dust_unfiltered_percent':100*w.dustUnfilteredFraction.mean(), 'total_external_in_L_s':1000*w.totalExternalIn.mean()}
    for v in vents:
        row[v+'_in_L_s']=1000*w[v+'_in'].mean(); row[v+'_out_L_s']=1000*w[v+'_out'].mean()
    summary.append(row)
(R/'results').mkdir(exist_ok=True)
old=pd.read_csv(R/'results/summary.csv') if (R/'results/summary.csv').exists() else pd.DataFrame(columns=['layout'])
kept=[r for r in old.to_dict('records') if r['layout'] not in layouts]
order={x:i for i,x in enumerate(C['layouts'])}
summary=sorted(kept+summary,key=lambda r:order.get(r['layout'],len(order)))
pd.DataFrame(summary).to_csv(R/'results/summary.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False,float_format=lambda x:f'{x:.4g}'))
