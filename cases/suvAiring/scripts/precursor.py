from prepare import *
from wind import map_start,profile,USTAR

def probe_object():
 pts=[(2.88,-1.30,1.44)]+[(2.88,y,z) for y in [-5.,-9.59] for z in [.3,.75,1.5,3.]]
 return 'windProbes {type probes; libs (sampling); fields (U k omega p); interpolationScheme cellPoint; writeControl timeStep; writeInterval 1; probeLocations (\n'+''.join('(%s %s %s)\n'%p for p in pts)+');}\n'
# The solved precursor's steady stage was stopped by the agent's monitor when the probe at
# (2.88, -1.30, 1.44) and the U residuals had settled (the spread of the probe's last 100 values
# under 0.5% of its mean, every U initial residual of the last 50 iterations under 3e-3), which it
# found at iteration 640. Here it runs those 640 iterations and reports the same two measures.
STEADY_ITERATIONS=640
RANKS=int(os.environ.get('NPROCS','4'))
def ctrl(case,steady):
 text=header('controlDict')+'libs (atmosphericModels); application '+('buoyantSimpleFoam' if steady else 'buoyantPimpleFoam')+'; startFrom startTime; startTime 0; stopAt endTime; endTime '+(str(STEADY_ITERATIONS) if steady else '6')+'; deltaT '+('1' if steady else '1e-4')+'; adjustTimeStep '+('no' if steady else 'yes')+'; maxCo 1; maxDeltaT .02; writeControl '+('timeStep; writeInterval '+str(STEADY_ITERATIONS)+';' if steady else 'adjustableRunTime; writeInterval 1;')+' purgeWrite 0; writeFormat binary; writePrecision 12; writeCompression on; timePrecision 12; runTimeModifiable false; functions {\n'+probe_object()+'}\n'
 (case/'system/controlDict').write_text(text)
 (case/'constant/fvOptions').write_text(header('fvOptions')+'buoyancyTurb {type buoyancyTurbSource; selectionMode all;} isothermal {type fixedTemperatureConstraint; selectionMode all; mode uniform; temperature constant 310.93;}\n')
def launch(case,solver):
 cmd=f'mpirun -np {RANKS} {solver} -parallel -fileHandler collated'
 log=case/('log.'+solver);f=open(log,'w');p=subprocess.Popen(cmd,shell=True,cwd=case,stdout=f,stderr=subprocess.STDOUT);return p,f,log,time.monotonic()
def probeU(case):
 paths=list((case/'postProcessing/windProbes').glob('*/U'))
 if not paths:return []
 rows=[]
 for l in paths[0].read_text().splitlines():
  if l.startswith('#'):continue
  v=np.fromstring(l.replace('(',' ').replace(')',' '),sep=' ')
  if len(v)>=4:rows.append(v)
 return np.array(rows)
def precursor():
 steady=ROOT/'precursor/steady';shutil.copytree(ROOT/'mesh/precursor',steady);prepare(steady,'precursor',still=True,planesOn=False);ctrl(steady,True)
 fs=(steady/'system/fvSchemes').read_text().replace('default Euler;','default steadyState;');(steady/'system/fvSchemes').write_text(fs)
 sol=(steady/'system/fvSolution').read_text();sol=sol[:sol.index('PIMPLE')]+'''SIMPLE {nNonOrthogonalCorrectors 0; momentumPredictor yes; pRefPoint (6 0 2); pRefValue 100000;} relaxationFactors {fields {p_rgh .3;} equations {U .7; h .7; k .7; omega .7;}}\n''';(steady/'system/fvSolution').write_text(sol)
 (steady/'system/decomposeParDict').write_text(header('decomposeParDict')+f'numberOfSubdomains {RANKS}; method scotch;\n');run('decomposePar -force -fileHandler collated',steady)
 p,f,log,t=launch(steady,'buoyantSimpleFoam')
 while p.poll() is None:
  time.sleep(20);text=log.read_text();times=re.findall(r'^Time = (.*)',text,re.M);print('steady precursor iteration',times[-1] if times else 'startup',flush=True)
 p.wait();f.close();wall=time.monotonic()-t
 with open(ROOT/'timing.jsonl','a') as f:f.write(json.dumps(dict(stage='steady_precursor',case=str(steady),wall_s=wall,exit=p.returncode,ranks=RANKS))+'\n')
 if p.returncode:raise RuntimeError(log.read_text()[-4000:])
 run('reconstructPar -latestTime -fileHandler collated',steady);last=max(float(d.name) for d in steady.iterdir() if d.is_dir() and re.fullmatch(r'[\d.e+-]+',d.name))
 rows=probeU(steady);text=log.read_text();residuals=re.findall(r'Solving for U[xyz], Initial residual = ([\d.e+-]+)',text)
 q=rows[-100:,1:4];mean=q.mean(axis=0);spread=np.linalg.norm(q-mean,axis=1).max()/max(np.linalg.norm(mean),.01)
 settled={'iterations':int(last),'probe_relative_spread_last100':float(spread),'max_U_initial_residual_last50_iterations':max(map(float,residuals[-150:])),'settled_by_the_solved_criterion':bool(spread<.005 and max(map(float,residuals[-150:]))<.003)}
 transient=ROOT/'precursor/transient';shutil.copytree(ROOT/'mesh/precursor',transient);prepare(transient,'precursor',still=True,planesOn=False)
 # Copy every reconstructed physical field to zero time; the steady clock is not a door clock.
 for path in (steady/f'{last:g}').iterdir():
  if path.is_file():
   target=transient/'0'/path.name
   if target.exists():target.unlink()
   if path.suffix=='.gz' and target.with_suffix('').exists():target.with_suffix('').unlink()
   if path.suffix!='.gz' and target.with_suffix(target.suffix+'.gz').exists():target.with_suffix(target.suffix+'.gz').unlink()
   shutil.copy(path,target)
 ctrl(transient,False);(transient/'system/decomposeParDict').write_text(header('decomposeParDict')+f'numberOfSubdomains {RANKS}; method scotch;\n');run('decomposePar -force -fileHandler collated',transient)
 p,f,log,t=launch(transient,'buoyantPimpleFoam')
 while p.poll() is None:
  time.sleep(30);s=log.read_text();times=re.findall(r'^Time = (.*)',s,re.M);print('transient precursor',times[-1] if times else 'startup',flush=True)
 p.wait();f.close();wall=time.monotonic()-t
 with open(ROOT/'timing.jsonl','a') as f:f.write(json.dumps(dict(stage='transient_precursor',case=str(transient),wall_s=wall,exit=p.returncode,ranks=RANKS))+'\n')
 if p.returncode:raise RuntimeError(log.read_text()[-4000:])
 run('reconstructPar -latestTime -fileHandler collated',transient)
 report={'steady_iterations':last,'steady_assessment':settled,'transient_duration_s':6,'transient_wall_s':wall,'transient_wall_s_per_flow_s':wall/6,'u_star_ms':USTAR,'mapping':map_start(transient,6)}
 (ROOT/'precursor/precursor.json').write_text(json.dumps(report,indent=2));print('PRECURSOR COMPLETE',json.dumps(report),flush=True)
if __name__=='__main__':precursor()
