"""Write, decompose and solve one run in runs/<run>/.

    python3 scripts/run_case.py <run> [--ranks 8] [--end 60] [--steps N] [--setup-only]
    python3 scripts/run_case.py <run> --resume --end 60

The first call writes runs/<run>/ on runs/mesh/<run>/ with prepare.py, writes its t = 0 planes,
decomposes it by scotch into collated processors<ranks>/ and solves from 0 to --end. --steps N
stops the solve with a write after N time steps (for a quick test). --resume carries on from
the latest write with the same decomposition, keeping the monitor's earlier file as
postProcessing/diagnostics89.before_<t>/. Extra arguments for mpirun, such as
"--cpu-set 0-7 --bind-to core", can be given in the environment variable MPIRUN_ARGS. The
finished planes are gzipped as the solve goes (OpenFOAM v2512's VTK writer ignores its own
compression option).
"""
from prepare import *
import argparse,gzip

def compress_planes(case,force=False):
 for path in (case/'postProcessing').rglob('*.vtp'):
  if force or time.time()-path.stat().st_mtime>5:
   target=path.with_suffix(path.suffix+'.gz');target.write_bytes(gzip.compress(path.read_bytes(),compresslevel=1));path.unlink()

p=argparse.ArgumentParser();p.add_argument('run',choices=['fourWindows','doorFan']);p.add_argument('--ranks',type=int,default=8);p.add_argument('--end',type=float,default=60.0);p.add_argument('--steps',type=int,default=0);p.add_argument('--resume',action='store_true');p.add_argument('--setup-only',action='store_true');a=p.parse_args()
case=ROOT/a.run
if not a.resume:
 if case.exists():raise RuntimeError('Refusing to overwrite '+str(case)+'; ./Allclean first')
 configure(a.run,case,end=a.end,ranks=a.ranks,steps=a.steps)
 run('postProcess -dict system/initialSurfaces -time 0',case,'log.postProcess.initial')
 run('decomposePar -fileHandler collated',case)
 if a.setup_only:print('set up, not solved:',case);sys.exit(0)
else:
 if not case.exists():raise RuntimeError('Cannot resume a missing case')
 if not (case/f'processors{a.ranks}').exists():raise RuntimeError('Resume needs the original collated decomposition and the same rank count')
 ctrl=case/'system/controlDict';ct=ctrl.read_text().replace('startFrom startTime;','startFrom latestTime;')
 ct=re.sub(r'endTime [^;]*;',f'endTime {a.end};',ct,count=1)
 ctrl.write_text(ct)
 # the monitor starts a new file and new running sums at a restart: keep the earlier segment's
 # file beside it, which extract_results.py joins to the new one
 d=case/'postProcessing/diagnostics89'
 if (d/'diagnostics.csv').exists():
  last=float((d/'diagnostics.csv').read_text().strip().splitlines()[-1].split(',')[0])
  d.rename(d.with_name(f'diagnostics89.before_{last:g}'))
cmd=f'mpirun -np {a.ranks} {os.environ.get("MPIRUN_ARGS","")} buoyantPimpleFoam -parallel -fileHandler collated'
t=time.monotonic();log=case/'log.buoyantPimpleFoam'
print('launch',cmd,'case',case,'resume',a.resume,flush=True)
with open(log,'a' if a.resume else 'w') as f:
 proc=subprocess.Popen(cmd,shell=True,cwd=case,stdout=f,stderr=subprocess.STDOUT)
 while True:
  try:proc.wait(timeout=30);break
  except subprocess.TimeoutExpired:
   compress_planes(case);text=log.read_text();times=re.findall(r'^Time = (.*)$',text,re.M);print('progress',a.run,'flow_s',times[-1] if times else 'startup',flush=True)
compress_planes(case,True);wall=time.monotonic()-t
with open(ROOT/'timing.jsonl','a') as f:f.write(json.dumps(dict(stage='solve',case=str(case),wall_s=wall,exit=proc.returncode,ranks=a.ranks,resume=a.resume))+'\n')
print('solver ended',proc.returncode,'wall_s',round(wall),'case',case,flush=True)
if proc.returncode:raise RuntimeError('solver error, see '+str(log))
