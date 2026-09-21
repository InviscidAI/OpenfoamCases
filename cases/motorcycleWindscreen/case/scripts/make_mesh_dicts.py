#!/usr/bin/env python3
import os,re
from pathlib import Path
c={}
for line in Path('config/run.conf').read_text().splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1); c[k.strip()]=v.split('#')[0].strip()
p=Path('system/snappyHexMeshDict.template').read_text()
p=re.sub(r'bike \{ level \([^)]*\);',f'bike {{ level ({c["BIKE_LEVEL"]} {c["BIKE_LEVEL"]});',p)
p=re.sub(r'helmet \{ level \([^)]*\);',f'helmet {{ level ({c["HELMET_LEVEL"]} {c["HELMET_LEVEL"]});',p)
p=re.sub(r'screen \{ level \([^)]*\);',f'screen {{ level ({c["SCREEN_LEVEL"]} {c["SCREEN_LEVEL"]});',p)
p=re.sub(r'file "screen\.eMesh"; level \d+;',f'file "screen.eMesh"; level {c["SCREEN_LEVEL"]};',p)
p=re.sub(r'(wake \{ mode inside; levels \(\(1e15 )\d+(\)\);)',rf'\g<1>{c["WAKE_LEVEL"]}\2',p)
p=re.sub(r'(nearWake \{ mode inside; levels \(\(1e15 )\d+(\)\);)',rf'\g<1>{c["NEAR_WAKE_LEVEL"]}\2',p)
Path('system/snappyHexMeshDict').write_text(p)
b=Path('system/blockMeshDict').read_text()
nx=int(c['BASE_CELLS_X']); b=re.sub(r'\(96 48 32\)',f'({nx} {nx//2} {nx//3})',b)
Path('system/blockMeshDict.active').write_text(b)
