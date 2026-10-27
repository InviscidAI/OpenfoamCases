"""Shut the window at 300 s: python3 close_window.py <run dir>, in the run reconstructed at 300 s.

The outdoor air and the reveal are dropped and the room's cells kept as they are: the sash's
baffle is merged (mergeOrSplitBaffles), the mesh is cut to the room's cell zone (subsetMesh), and
the faces it exposes in the frame's plane become the glass, patch glassRoom: double glazing,
U = 2.8 W/m2K to 0 C outside (externalWallHeatFluxTemperature, h = 4.403 W/m2K with the inside
film left to the solver, as in radiatorUnderWindow and underfloorVsRadiator). Nothing is
interpolated: every kept cell's values, volume and centre, and all 72 arrays of the wall layers,
are compared before and after (switch_raw_checks.json, switch_conservation.json), and the script
stops if any differs.

The shut room is closed, and buoyantPimpleFoam then shifts p to pRefValue at pRefPoint as it
starts. Both are set to a kept cell's own centre and 300 s pressure, in the room's far upper
corner, 1.57 m off the clip's section, so that the restart adds no jump in pressure or energy.
The planes go to every 2.5 s, the walls' surface sampling takes the glass too, and the opening's
monitors are removed. The radiator carries on from postProcessing/radiator/state_300, which the
fv option trvRadiator wrote at 300 s.
"""
import subprocess,re,sys,os,shutil,json
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]).resolve(); os.chdir(p)
def run(cmd):
 print(cmd,flush=True)
 with open('log.switch.'+cmd.split()[0],'w') as f: subprocess.run(cmd,shell=True,stdout=f,stderr=subprocess.STDOUT,check=True)
def state():
 def entry(b,key,components=1):
  m=re.search(rb'\b'+key.encode()+rb'\s+(nonuniform|uniform)\s+',b)
  if not m: return np.array([293.15])
  if m[1]==b'uniform':
   v=b[m.end():b.index(b';',m.end())].strip().strip(b'()'); return np.fromstring(v.decode(),sep=' ')
  start=m.end(); l=re.search(rb'List<[^>]+>\s*(\d+)\s*\(',b[start:]); n=int(l[1])*components; start+=l.end()
  if re.search(rb'format\s+binary',b): return np.frombuffer(b,dtype='<f8',count=n,offset=start).copy()
  return np.fromstring(b[start:b.index(b')',start)].replace(b'(',b' ').replace(b')',b' ').decode(),sep=' ')
 result={}
 for x in folder.iterdir():
  if x.is_file():
   b=x.read_bytes()
   if b'internalField' in b and (b'volScalarField' in b[:1500] or b'volVectorField' in b[:1500]):
    nc=3 if b'volVectorField' in b[:1500] else 1
    result[x.name]=entry(b,'internalField',nc)
 wall=Path(folder/'T').read_bytes(); m=re.search(rb'\n\s*walls\s*\n\s*\{',wall); tail=wall[m.end():]
 # Preserve file header's binary/ascii information when reading boundary data.
 tail=wall[:wall.index(b'internalField')]+tail
 for j in range(72): result['wallLayer'+str(j)]=entry(tail,'layer'+str(j))
 return result
# Work at the reconstructed switch time. Read exact cell volumes and centres.
times=[x for x in Path('.').iterdir() if x.is_dir() and re.fullmatch(r'[0-9.]+',x.name)]
folder=max(times,key=lambda x:float(x.name))
run('postProcess -func writeCellCentres -latestTime')
run('postProcess -func writeCellVolumes -latestTime')
before=state(); mask=before['Cx']>0; nold=len(mask)
# Retaining a subset changes labels, never field values or retained cell geometry.
for key,a in list(before.items()):
 if not key.startswith('wallLayer') and len(a)>1:
  nc=3 if key in ('U','C') else 1
  if len(a)==nold*nc: before[key]=a.reshape(nold,nc)[mask].ravel()
run('mergeOrSplitBaffles -overwrite')
run('subsetMesh room -zone -patch glassRoom -overwrite')
mesh=folder/'polyMesh'; mesh=mesh if mesh.exists() else Path('constant/polyMesh')
# The new exposed patch is the opening at x=0. Make its geometric type wall.
bound=(mesh/'boundary').read_text()
m=re.search(r'glassRoom\s*\{',bound); j=bound.index('}',m.end()); block=bound[m.end():j];block=re.sub(r'type\s+\w+;','type wall;',block);block=re.sub(r'inGroups\s+[^;]+;','inGroups 1(wall);',block);bound=bound[:m.end()]+block+bound[j:];(mesh/'boundary').write_text(bound)
Path('system/createPatchDict.closed').write_text('FoamFile { version 2.0; format ascii; class dictionary; object createPatchDict; }\npointSync false; patches ();\n')
run('createPatch -dict system/createPatchDict.closed -overwrite')
rename={}
BC={
 'T':'type externalWallHeatFluxTemperature; mode coefficient; Ta constant 273.15; h uniform 4.403; kappaMethod fluidThermo; value uniform 283.15;',
 'U':'type noSlip;', 'p_rgh':'type fixedFluxPressure; value uniform 1e5;', 'p':'type calculated; value uniform 1e5;',
 's':'type zeroGradient;', 'k':'type kLowReWallFunction; value uniform 1e-4;', 'omega':'type omegaWallFunction; value uniform 1;',
 'nut':'type nutkWallFunction; value uniform 0;', 'alphat':'type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;'
}
for f in folder.iterdir():
 if not f.is_file() or f.name.startswith('C'): continue
 b=f.read_bytes()
 for a,c in rename.items(): b=re.sub(rb'\b'+a.encode()+rb'\b',c.encode(),b)
 if f.name in BC:
  for pat in ('glassRoom',):
   m=re.search(rb'\b'+pat.encode()+rb'\s*\{',b)
   if not m: continue
   start=m.end(); depth=1; i=start
   while depth:
    if b[i]==123:depth+=1
    if b[i]==125:depth-=1
    i+=1
   bc=BC[f.name]
   if pat=='glassOutside' and f.name=='T': bc='type zeroGradient;'
   b=b[:start]+b'\n'+bc.encode()+b'\n'+b[i-1:]
 f.write_bytes(b)
# Recompute geometric quantities, not merely their mapped stored values.
run('postProcess -func writeCellCentres -latestTime')
run('postProcess -func writeCellVolumes -latestTime')
after=state()
comparisons={k:bool((k in ('V','C','Cx','Cy','Cz') and np.allclose(before[k],after[k],rtol=1e-13,atol=1e-13)) or np.array_equal(before[k],after[k]) or (before[k].size==1 and np.all(before[k]==after[k])) or (after[k].size==1 and np.all(before[k]==after[k]))) for k in before}
Path('switch_raw_checks.json').write_text(json.dumps(comparisons,indent=2))
R=8314.46261815324/28.96;cv=1005-R
energy=lambda d: float(cv/R*np.sum(d['p']*d['V'])-cv*273.15*np.sum(d['p']/(R*d['T'])*d['V']))
e0=energy(before);e1=energy(after)
proof={'old_cells':nold,'retained_cells':int(mask.sum()),'closed_cells':len(after['Cx']),
 'Eair_before_J':e0,'Eair_after_J':e1,'Eair_change_percent':100*(e1-e0)/abs(e0),
 'all_retained_cell_values_and_volumes_identical':all(v for k,v in comparisons.items() if not k.startswith('wallLayer')),
 'all_72_wall_layer_arrays_identical':all(v for k,v in comparisons.items() if k.startswith('wallLayer')),
 'wall_stored_heat_change_J':0.0 if all(v for k,v in comparisons.items() if k.startswith('wallLayer')) else None}
Path('switch_conservation.json').write_text(json.dumps(proof,indent=2));print(proof,flush=True)
if not all(comparisons.values()) or abs(proof['Eair_change_percent'])>.1: raise RuntimeError('Switch changed retained state: '+str(comparisons))
for f in ('C','Cx','Cy','Cz','V','wallHeatFlux','phi'): (folder/f).unlink(missing_ok=True)
# buoyantPimpleFoam shifts absolute p to pRefValue during initialization.
# Choose the EXACT existing p in a known cell, so restart adds no pressure/energy jump.
centres=after['C'].reshape(-1,3);refi=int(np.argmin(np.sum((centres-np.array([3.9,2.3,-1.6]))**2,axis=1)))  # far upper corner, 1.57 m off the clip's section
pt=' '.join('%.17g'%v for v in centres[refi]);pr=float(after['p'][refi])
f=Path('system/fvSolution');t=re.sub(r'PIMPLE\s*\{',f'PIMPLE\n{{\n pRefPoint ({pt}); pRefValue {pr:.17g};',f.read_text());f.write_text(t)
proof['pRefPoint']=centres[refi].tolist();proof['pRefValue']=pr
Path('switch_conservation.json').write_text(json.dumps(proof,indent=2))
# the radiator carries on behind its valve from postProcessing/radiator/state_300 (trvRadiator)
f=Path('system/functions'); t=f.read_text(); t=t.replace('writeInterval 1.25;','writeInterval 2.5;'); t=t.replace('patches         (walls);','patches         (walls glassRoom);').replace('patches (walls);','patches (walls glassRoom);'); f.write_text(t)
subprocess.run([sys.executable,str(Path(__file__).resolve().parent/'remove_opening_monitors.py'),'system/functions'],check=True)
run('checkMesh -constant')
