"""Write one run's 0/, constant/ and system/ on its mesh.

configure(name, case, ...) is called by run_case.py. name is fourWindows or doorFan; the mesh is
runs/mesh/<name>/. The start is still air everywhere: the cabin (and the inner half of its side
walls) at 321.85 K, outside at 310.93 K, each hydrostatic and equal in pressure at z = 1.14 m,
with no outside air in the cabin. The inside surfaces are held at their temperatures; the body's
outside and the ground are adiabatic; the domain's other faces are open at hydrostatic pressure.
The door (doorFan only) is a drag term in constant/fvOptions, swung from t = 0 to swing_end.
"""
from common import *
patches=['ground','open','dashboard','seats','cabinInterior','bodyExterior']
def nonuniform(a,typ='scalar'):
 if typ=='vector':s='\n'.join('('+' '.join(f'{x:.12g}' for x in r)+')' for r in a)
 else:s='\n'.join(f'{x:.12g}' for x in a)
 return f'nonuniform List<{typ}>\n{len(a)}\n(\n{s}\n)'
def field(case,name,dim,values,bcs,vector=False):
 typ='vector' if vector else 'scalar';val=values if isinstance(values,str) else nonuniform(values,typ)
 write(case/'0'/name,header(name,'volVectorField' if vector else 'volScalarField')+'dimensions ['+dim+'];\ninternalField '+val+';\nboundaryField\n{\n'+''.join(p+'\n{'+bcs[p]+'}\n' for p in patches)+'}\n')
def doorcode(rho=True,swing_end=60.0):
 # The door: a slab 1.00 x 0.20 x 1.08 m hinged on a vertical axis at its front outer corner
 # (1.96, 0.92), turned outwards by theta(t) = (65/2)(1 - cos(2 pi t / 1.2)) degrees while
 # t <= swing_end, else shut. Its edge is spread over one cell by the mask clamp(1/2 - d/h, 0, 1)
 # of the signed distance d to the slab and the cell size h, and the air in it is held at the
 # door's velocity by the implicit drag -K mask rho (U - U_door), K = 1e6 1/s.
 return '''
 const fvMesh& m=mesh_;
 const auto& d=fv::option::dict_.subDict("codeContext");
 scalar t=m.time().value()+d.get<scalar>("offset");
 const scalar pi=constant::mathematical::pi;
 scalar theta=0,w=0;
 if(!d.get<bool>("hold") && t<=SWINGEND){theta=65*pi/360*(1-cos(2*pi*t/1.2));w=65*pi/360*2*pi/1.2*sin(2*pi*t/1.2);}
 static bool first=true;if(first){Info<<"doorPenalty: CODEFORM K=1e6 rho form=RHOVALUE"<<endl;first=false;}
 volScalarField* ptr=m.getObjectPtr<volScalarField>("doorKm");
 if(!ptr){ptr=new volScalarField(IOobject("doorKm",m.time().timeName(),m,IOobject::NO_READ,IOobject::AUTO_WRITE,IOobject::REGISTER),m,dimensionedScalar(dimless/dimTime,Zero));ptr->store();}
 ptr->writeOpt()=IOobject::AUTO_WRITE;
 auto& km=ptr->primitiveFieldRef();km=0;
 forAll(km,i){
 const vector c=m.C()[i];
 if(c.x()<1.90 || c.x()>3.06 || c.y()<.66 || c.y()>2.02 || c.z()<.18 || c.z()>1.38)continue;
 scalar dx=c.x()-1.96,dy=c.y()-.92;
 vector q(mag(dx*cos(theta)+dy*sin(theta)-.5)-.5,mag(dx*sin(theta)-dy*cos(theta)-.1)-.1,mag(c.z()-.78)-.54);
 vector qp(max(q.x(),scalar(0)),max(q.y(),scalar(0)),max(q.z(),scalar(0)));
 scalar sd=mag(qp)+min(max(q.x(),max(q.y(),q.z())),scalar(0));
 scalar frac=min(max(.5-sd/cbrt(m.V()[i]),scalar(0)),scalar(1));
 if(frac>1-1e-10)frac=1;if(frac<1e-10)frac=0;
 km[i]=1e6*frac;
 vector ub=w*vector(-dy,dx,0);
 scalar a=km[i]*RHOFIELD*m.V()[i];
 eqn.diag()[i]-=a;eqn.source()[i]-=a*ub;
 }
 '''.replace('SWINGEND',str(swing_end)).replace('CODEFORM','codeAddSupRho' if rho else 'codeAddSup').replace('RHOVALUE','true' if rho else 'false').replace('RHOFIELD','rho[i]' if rho else '1.0')
def planes():
 """Plans at head height (z 1.14 m, interpolated and as cell values), at 0.90 m and 1.30 m every
 0.125 s; lengthwise sections at y -0.42, 0.02 and 0.42 m and cross sections through the rows
 every 0.25 s; three of them again every 7.2 s; the 316.48 K isosurface round the cabin."""
 out=''
 groups=[('horizontal',.125,[('head',(0,0,1.14),(0,0,1),True),('headCells',(0,0,1.14),(0,0,1),False),('low',(0,0,.9),(0,0,1),True),('high',(0,0,1.30),(0,0,1),True)]),('vertical',.25,[('sideLeft',(0,-.42,0),(0,1,0),True),('centre',(0,.02,0),(0,1,0),True),('sideRight',(0,.42,0),(0,1,0),True),('row1',(2.62,0,0),(1,0,0),True),('row2',(3.50,0,0),(1,0,0),True)])]
 for n,dt,planes in groups:
  out+=n+''' {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval '''+str(dt)+'''; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor doorKm); interpolate true; surfaces\n{\n'''
  for name,pt,normal,interp in planes:
   vec=lambda p:'('+' '.join(map(str,p))+')'
   out+=f'{name} {{type cuttingPlane; point {vec(pt)}; normal {vec(normal)}; interpolate {str(interp).lower()};}}\n'
  out+='}}\n'
 out+='''milestones {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval 7.2; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor doorKm); interpolate true; surfaces {
head {type cuttingPlane; point (0 0 1.14); normal (0 0 1); interpolate true;}
low {type cuttingPlane; point (0 0 .90); normal (0 0 1); interpolate true;}
centre {type cuttingPlane; point (0 .02 0); normal (0 1 0); interpolate true;}
}}\n'''
 out+='''isotherm {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval .25; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor doorKm); interpolate true; surfaces {warm {type isoSurface; isoField T; isoValue 316.48; interpolate true; bounds (1.3 -1.2 .2) (4.4 2.1 1.5);}}}\n'''
 return out

def configure(name,case,end=60.0,ranks=8,steps=0,swing_end=60.0,offset=0,hold=False):
 """steps > 0 stops the solve, with a write, after that many time steps (the monitor does it);
 offset shifts the door's clock; hold keeps the door shut. The solved runs used the defaults."""
 case=Path(case);source=ROOT/'mesh'/name
 if not (case/'constant/polyMesh').exists():
  shutil.copytree(source/'constant',case/'constant',dirs_exist_ok=True)
  for f in source.glob('log.*'):shutil.copy2(f,case/f.name)
 arr=np.load(source/'mesh_arrays.npz');C,V,cf,sf,own=[arr[k] for k in ['C','V','cf','sf','owner']]
 text=(case/'constant/polyMesh/boundary').read_text();slices={}
 for p,b in re.findall(r'(\w+)\s*\{([^{}]+)\}',text):
  if 'nFaces' in b:slices[p]=slice(int(re.search(r'startFace\s+(\d+)',b)[1]),int(re.search(r'startFace\s+(\d+)',b)[1])+int(re.search(r'nFaces\s+(\d+)',b)[1]))
 hot=cabin(C,.82)
 T=np.where(hot,321.85,310.93);z=C[:,2]
 p=np.where(hot,1e5*np.exp(-9.81*1.14/(287.1*310.93))*np.exp(-9.81*(z-1.14)/(287.1*321.85)),1e5*np.exp(-9.81*z/(287.1*310.93)))
 rho=p/((8314.46261815324/28.96)*T);prgh=p+rho*9.81*z
 bc={p:'type zeroGradient;' for p in patches};bc['open']='type inletOutlet; inletValue uniform 310.93; value uniform 310.93;'
 for pa,temp in [('dashboard',346.95),('seats',327.05),('cabinInterior',321.85)]:bc[pa]=f'type fixedValue; value uniform {temp};'
 field(case,'T','0 0 0 1 0 0 0',T,bc)
 bc={p:'type noSlip;' for p in patches};bc['open']='type pressureInletOutletVelocity; value uniform (0 0 0);'
 field(case,'U','0 1 -1 0 0 0 0','uniform (0 0 0)',bc,True)
 bc={p:'type calculated; value uniform 1e5;' for p in patches};field(case,'p','1 -1 -2 0 0 0 0',p,bc)
 bc={p:'type fixedFluxPressure; value uniform 1e5;' for p in patches}
 op=cf[slices['open'],2];p0=1e5*np.exp(-9.81*op/(287.1*310.93))
 bc['open']='type prghPressure; p '+nonuniform(p0)+'; value '+nonuniform(p0+p0/((8314.46261815324/28.96)*310.93)*9.81*op)+';'
 field(case,'p_rgh','1 -1 -2 0 0 0 0',prgh,bc)
 for f,dim,val,wall in [('k','0 2 -2 0 0 0 0',1e-4,'kLowReWallFunction'),('omega','0 0 -1 0 0 0 0',np.sqrt(1e-4)/(.09**.25*.1),'omegaWallFunction'),('nut','0 2 -1 0 0 0 0',0,'nutkWallFunction'),('alphat','1 -1 -1 0 0 0 0',0,'compressible::alphatJayatillekeWallFunction')]:
  bc={p:f'type {wall}; value uniform {val};'+('Prt .85;' if f=='alphat' else '') for p in patches}
  bc['open']=(f'type inletOutlet; inletValue uniform {val}; value uniform {val};' if f in ['k','omega'] else 'type calculated; value uniform 0;')
  field(case,f,dim,f'uniform {val}',bc)
 bc={p:'type zeroGradient;' for p in patches};bc['open']='type inletOutlet; inletValue uniform 1; value uniform 1;'
 field(case,'outdoor','0 0 0 0 0 0 0',np.where(hot,0.,1.),bc)
 bc={p:'type zeroGradient;' for p in patches};field(case,'doorKm','0 0 -1 0 0 0 0',1e6*box(C,(1.96,.72,.24),(2.96,.92,1.32)).astype(float) if name=='doorFan' else 'uniform 0',bc)
 write(case/'constant/g',header('g','uniformDimensionedVectorField')+'dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);\n')
 # template/: case72's thermophysical and turbulence properties with Tref at the outside air's
 # 310.93 K, and case77's schemes and solution settings with the tracer named outdoor
 for f in ['thermophysicalProperties','turbulenceProperties']:write(case/'constant'/f,(TEMPLATE/'constant'/f).read_text())
 fv=header('fvOptions')+'buoyancyTurb {type buoyancyTurbSource; selectionMode all;}\n'
 if name=='doorFan':
  fv+='doorPenalty {type vectorCodedSource; selectionMode all; fields (U); name doorPenalty;\ncodeContext {offset '+str(offset)+'; hold '+str(hold).lower()+';}\n'
  fv+='codeAddSup #{'+doorcode(False,swing_end)+'#};\ncodeAddSupRho #{'+doorcode(True,swing_end)+'#};\ncodeCorrect #{ #}; codeConstrain #{ #};\n}\n'
 write(case/'constant/fvOptions',fv)
 for f in ['fvSchemes','fvSolution']:write(case/'system'/f,(TEMPLATE/'system'/f).read_text())
 write(case/'system/decomposeParDict',header('decomposeParDict')+f'numberOfSubdomains {ranks}; method scotch;\n')
 funcs='''outdoorTransport {type scalarTransport; libs (solverFunctionObjects); field outdoor; phi phi; rho rho; alphaD 1.40845; alphaDt 1; nCorr 1; tolerance 0; executeControl timeStep; executeInterval 1; writeControl writeTime;}\n'''
 funcs+='''readKm {type readFields; libs (fieldFunctionObjects); fields (doorKm);}\n'''
 funcs+=planes()
 funcs+='wallHeat {type wallHeatFlux; libs (fieldFunctionObjects); patches (dashboard seats cabinInterior); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval .125;}\n'
 diag=(SCRIPTS/'diagnostics.template').read_text().replace('STEPSTOP',str(steps)).replace('DOOROFFSET',str(offset)).replace('DOORHOLD',str(hold).lower()).replace('ISDOOR',str(name=='doorFan').lower()).replace('SWINGEND',str(swing_end))
 funcs+=diag
 control=header('controlDict')+f'''application buoyantPimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT .0001;
adjustTimeStep yes; maxCo 1; maxDeltaT .02;
writeControl adjustableRunTime; writeInterval 10; purgeWrite 0;
writeFormat binary; writePrecision 12; writeCompression on; timeFormat general; timePrecision 10; runTimeModifiable false;
functions\n{{\n{funcs}\n}}\n'''
 write(case/'system/controlDict',control)
 write(case/'system/initialSurfaces',header('initialSurfaces')+'functions { readKm {type readFields; libs (fieldFunctionObjects); fields (T U doorKm outdoor);}\n'+planes()+'}\n')
 return case
