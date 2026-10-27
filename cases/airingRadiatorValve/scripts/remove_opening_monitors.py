"""Remove the opening's monitors (openingIn, openingOut, openingS) from a functions file: once the
window is shut there is no opening. python3 remove_opening_monitors.py <run>/system/functions"""
from pathlib import Path
import re,sys
p=Path(sys.argv[1]);t=p.read_text()
for name in ('openingIn','openingOut','openingS'):
 m=re.search(r'\b'+name+r'\s*\{',t)
 if not m:continue
 i=m.end();depth=1
 while depth:
  if t[i]=='{':depth+=1
  if t[i]=='}':depth-=1
  i+=1
 t=t[:m.start()]+t[i:]
p.write_text(t)
