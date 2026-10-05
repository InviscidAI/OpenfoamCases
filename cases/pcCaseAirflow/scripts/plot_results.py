#!/usr/bin/env python3
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; out=R/'results'; colors={'positive':'#2b6cb0','negative':'#c53030','even':'#2f855a','viewer':'#b7791f'}
# Only the layouts solved here (with a results/<layout>_history.csv) are drawn.
colors={k:v for k,v in colors.items() if (out/f'{k}_history.csv').exists()}
fig,ax=plt.subplots(3,1,figsize=(10,9),sharex=True)
for name,c in colors.items():
 d=pd.read_csv(out/f'{name}_history.csv'); ax[0].plot(d.time,d.gpuRise_C,label=name,color=c,lw=1.2); ax[1].plot(d.time,d.cpuRise_C,color=c,lw=1.2); ax[2].plot(d.time,d.casePressure_Pa,color=c,lw=1.2)
for a in ax: a.axvspan(6,8,color='0.8',alpha=.3); a.grid(alpha=.25)
ax[0].set_ylabel('GPU intake rise (°C)'); ax[1].set_ylabel('CPU intake rise (°C)'); ax[2].set_ylabel('Mean gauge p (Pa)'); ax[2].set_xlabel('Time after switch-on (s)'); ax[0].legend(ncol=len(colors))
fig.tight_layout(); fig.savefig(out/'histories.png',dpi=180); plt.close(fig)
s=pd.read_csv(out/'summary.csv').set_index('layout').loc[list(colors)]
fig,ax=plt.subplots(1,3,figsize=(11,4)); cs=[colors[x] for x in s.index]
ax[0].bar(s.index,s.gpu_rise_C,color=cs); ax[0].set_ylabel('GPU intake above room (°C)')
ax[1].bar(s.index,s.case_pressure_Pa,color=cs); ax[1].axhline(0,color='k',lw=.8); ax[1].set_ylabel('Mean gauge pressure (Pa)')
ax[2].bar(s.index,s.dust_unfiltered_percent,color=cs); ax[2].set_ylabel('Unfiltered share of entering air (%)')
for a in ax: a.grid(axis='y',alpha=.25); a.tick_params(axis='x',rotation=20)
fig.tight_layout(); fig.savefig(out/'comparison.png',dpi=180); plt.close(fig)
