"""Write, decompose and solve one production run in runs/<kind>/.

    python3 scripts/run_case.py <kind> [--ranks 4] [--end 10] [--setup-only]
    python3 scripts/run_case.py <kind> --resume --end 45 [--write-interval 5]

The first call copies runs/mesh/<kind>/ (the mesh and its windy start from the precursor), writes
0/, constant/ and system/ with prepare.py, writes the t = 0 planes, decomposes by scotch and
solves from 0 to --end. --resume carries on from the latest write with the same decomposition.
The finished planes are gzipped as the solve goes (OpenFOAM v2512's VTK writer ignores its own
compression option). Each segment ends by reconstructing its last write.
"""
from prepare import *
import argparse,gzip

def compress_planes(case,force=False):
 for path in (case/'postProcessing').rglob('*.vtp'):
  if force or time.time()-path.stat().st_mtime>5:
   target=path.with_suffix(path.suffix+'.gz');target.write_bytes(gzip.compress(path.read_bytes(),compresslevel=1));path.unlink()

p=argparse.ArgumentParser();p.add_argument('kind',choices=['fourWindows','doorFan']);p.add_argument('--ranks',type=int,default=4);p.add_argument('--end',type=float,default=10);p.add_argument('--write-interval',type=float,default=None);p.add_argument('--resume',action='store_true');p.add_argument('--setup-only',action='store_true');a=p.parse_args()
case=ROOT/a.kind
if not a.resume:
 if case.exists():raise RuntimeError('Refusing to overwrite '+str(case)+'; ./Allclean first')
 shutil.copytree(ROOT/'mesh'/a.kind,case)
 shutil.copy(ROOT/'mesh'/a.kind/'wind_start.npz',case/'initial_state.npz')
 prepare(case,a.kind,end=a.end)
 (case/'system/decomposeParDict').write_text(header('decomposeParDict')+f'numberOfSubdomains {a.ranks}; method scotch;\n')
 run("postProcess -dict system/initialSurfaces -fields '(T U outdoor doorKm)' -time 0",case)
 run('decomposePar -force -fileHandler collated',case)
 if a.setup_only:print('set up, not solved:',case);sys.exit(0)
else:
 if not case.exists():raise RuntimeError('Cannot resume a missing case')
 if not (case/f'processors{a.ranks}').exists():raise RuntimeError('Resume needs the original collated decomposition and the same rank count')
 ctrl=case/'system/controlDict';ct=ctrl.read_text().replace('startFrom startTime;','startFrom latestTime;')
 ct=re.sub(r'endTime [^;]*;',f'endTime {a.end:g};',ct,count=1)
 if a.write_interval:ct=re.sub(r'(writeControl adjustableRunTime; )writeInterval [^;]*;',rf'\g<1>writeInterval {a.write_interval:g};',ct,count=1)
 ctrl.write_text(ct)
cmd=f'mpirun -np {a.ranks} buoyantPimpleFoam -parallel -fileHandler collated'
t=time.monotonic();log=case/'log.buoyantPimpleFoam'
print('launch',cmd,'case',case,'resume',a.resume,flush=True)
with open(log,'a' if a.resume else 'w') as f:
 proc=subprocess.Popen(cmd,shell=True,cwd=case,stdout=f,stderr=subprocess.STDOUT)
 while True:
  try:proc.wait(timeout=30);break
  except subprocess.TimeoutExpired:
   compress_planes(case);text=log.read_text();times=re.findall(r'^Time = (.*)$',text,re.M);print('progress',a.kind,'flow_s',times[-1] if times else 'startup',flush=True)
compress_planes(case,True);wall=time.monotonic()-t
with open(ROOT/'timing.jsonl','a') as f:f.write(json.dumps(dict(stage='solve',case=str(case),wall_s=wall,exit=proc.returncode,ranks=a.ranks,resume=a.resume))+'\n')
print('solver ended',proc.returncode,'wall_s',round(wall),'case',case,flush=True)
if proc.returncode:raise RuntimeError('solver error, see '+str(log))
run('reconstructPar -latestTime -fileHandler collated',case)
