#!/usr/bin/env python3
import pyvista as pv,numpy as np,pandas as pd,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from pathlib import Path
for cname in ['down_medium','up_medium','off_medium']:
 p=Path('runs')/cname/'postProcessing/rzFace/180/rz.vtp';m=pv.read(p); rows=[]
 fig,ax=plt.subplots(1,2,figsize=(9,4),sharex=True)
 for z in [0.5,1.5,2.67]:
  s=pv.Line((0,0,z),(.20,0,z),resolution=200).sample(m);ok=np.asarray(s['vtkValidPointMask']).astype(bool);r=s.points[:,0][ok];u=np.asarray(s['U'])[ok]
  rows.extend(dict(z_m=z,r_m=x,Ur_mps=a,Utheta_mps=b) for x,a,b in zip(r,u[:,0],u[:,1]))
  ax[0].plot(r,u[:,0],label=f'z={z:g} m');ax[1].plot(r,u[:,1],label=f'z={z:g} m')
 for a,y in zip(ax,['Ur (m/s)','Utheta, sampled-face sign (m/s)']): a.axhline(0,color='k',lw=.5);a.set_xlabel('r (m)');a.set_ylabel(y);a.grid(alpha=.3);a.legend()
 fig.suptitle(cname+': regular approach to degenerate axis');fig.tight_layout();out=Path('runs')/cname/'results';fig.savefig(out/'axis_regularity.png',dpi=160);plt.close(fig);pd.DataFrame(rows).to_csv(out/'axis_regularity.csv',index=False)
