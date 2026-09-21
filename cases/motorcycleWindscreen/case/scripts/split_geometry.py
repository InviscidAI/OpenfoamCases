#!/usr/bin/env python3
"""Split supplied bike OBJ into a fixed coordinate-defined helmet metric patch."""
import sys, numpy as np
src,out_h,out_b=sys.argv[1:4]
lines=open(src,errors='replace').readlines()
V=np.array([list(map(float,l.split()[1:4])) for l in lines if l.startswith('v ')])
header=['# generated from geometry input; units m\n']+[l for l in lines if l.startswith(('v ','vt ','vn '))]
with open(out_h,'w') as fh, open(out_b,'w') as fb:
 fh.writelines(header); fb.writelines(header); fh.write('g helmet\n'); fb.write('g bike\n')
 nh=nb=0
 for l in lines:
  if not l.startswith('f '): continue
  ids=[int(t.split('/')[0])-1 for t in l.split()[1:]]
  c=V[ids].mean(axis=0)
  # Fixed in all runs: top/front head shell; excludes shoulders behind x=0.64.
  if c[0] < 0.64 and c[2] > 1.13: fh.write(l); nh+=1
  else: fb.write(l); nb+=1
print(f'helmet faces={nh}, rest faces={nb}')
if nh < 100 or nb < 1000: raise SystemExit('implausible split: check geometry coordinates/units')
