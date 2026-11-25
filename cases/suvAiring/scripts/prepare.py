from build import *
WALLS=['ground','dashboard','seats','cabinInterior','bodyExterior']
def field(case,n,dim,internal,bc,cls='volScalarField'):
 def val(a):
  if np.isscalar(a):return 'uniform '+str(a)
  a=np.asarray(a);vec=a.ndim==2
  return 'nonuniform List<'+('vector' if vec else 'scalar')+'>\n'+str(len(a))+'\n(\n'+'\n'.join(('(%s)'%' '.join('%.12g'%x for x in v)) if vec else '%.12g'%v for v in a)+'\n)'
 (case/'0'/n).write_text(header(n,cls)+'dimensions ['+dim+'];\ninternalField '+val(internal)+';\nboundaryField\n{\n'+''.join(p+'\n{'+s+'}\n' for p,s in bc.items())+'}\n')
def initialize(case,kind,still=False):
 from wind import initialize_wind
 initialize_wind(case,kind,still)

def options(case,kind,offset=0,fixed=-1,K=1e6):
 text=header('fvOptions')+'buoyancyTurb {type buoyancyTurbSource; selectionMode all;}\n'
 if kind=='doorFan':
  code=(SCRIPTS/'door.C').read_text()
  text+='doorPenalty {type vectorCodedSource; selectionMode all; fields (U); name doorPenalty;\ncodeContext {K '+str(K)+'; clockOffset '+str(offset)+'; fixedAngle '+str(fixed)+';}\ncodeInclude\n#{\n'+code+'\n#};\ncodeAddSup\n#{\n static bool first=true; if(first){Info<<"doorPenalty: codeAddSup (no rho)"<<endl;first=false;} applyDoor(mesh_,fv::option::dict_.subDict("codeContext"),eqn,nullptr);\n#};\ncodeAddSupRho\n#{\n static bool first=true; if(first){Info<<"doorPenalty: codeAddSupRho (rho momentum)"<<endl;first=false;} applyDoor(mesh_,fv::option::dict_.subDict("codeContext"),eqn,&rho);\n#};\ncodeCorrect #{ #}; codeConstrain #{ #};\n}\n'
 (case/'constant/fvOptions').write_text(text)
def planes(interval,names):
 text='type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval '+str(interval)+'; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor doorKm); interpolate true; surfaces\n{\n'
 for n,p,normal,interp in names:text+=f'{n} {{type cuttingPlane; point ({p}); normal ({normal}); interpolate {interp};}}\n'
 return text+'}\n'
def controls(case,end=60,test=False,planesOn=True):
 base=header('controlDict')+f'application buoyantPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT 8.333333333333333e-5; adjustTimeStep yes; maxCo 1; maxDeltaT .02; writeControl adjustableRunTime; writeInterval 10; purgeWrite 0; writeFormat binary; writePrecision 12; writeCompression on; timeFormat general; timePrecision 12; runTimeModifiable false; libs (atmosphericModels);\nfunctions\n{{\n'
 base+='outdoorTransport {type scalarTransport; libs (solverFunctionObjects); field outdoor; phi phi; rho rho; alphaD 1.40845; alphaDt 1.0; bounded01 false; nCorr 1; tolerance 0; executeControl timeStep; executeInterval 1; writeControl writeTime;}\n'
 base+='wallHeat {type wallHeatFlux; libs (fieldFunctionObjects); patches (dashboard seats cabinInterior); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval .125;}\n'
 base+='extrema {type fieldMinMax; libs (fieldFunctionObjects); fields (T U outdoor); mode magnitude; location true; log false; writeControl adjustableRunTime; writeInterval .125;}\n'
 if planesOn:
  base+='clip { '+planes(.125,[(n,'0 0 '+str(z),'0 0 1',i) for n,z,i in [('head',1.50,'true'),('headCells',1.50,'false'),('sill',1.30,'true'),('low',1.,'true')]])+'}\n'
  base+='sections { '+planes(.25,[(n,'0 '+str(y)+' 0','0 1 0','true') for n,y in [('sideLeft',-.44),('centre',0),('sideRight',.44)]]+[(n,str(x)+' 0 0','1 0 0','true') for n,x in [('row1',2.92),('row2',3.84),('row3',4.64)]])+'}\n'
  base+='warmIso {type surfaces; libs (sampling); executeControl timeStep; executeInterval 1; writeControl adjustableRunTime; writeInterval .25; surfaceFormat vtk; formatOptions {vtk {format binary; compression true;}} fields (T U outdoor doorKm); interpolate true; surfaces {warm {type isoSurface; isoField T; isoValue 315.37; interpolate true;}}}\n'
 if planesOn:
  special=planes(18,[('head','0 0 1.5','0 0 1','true'),('sill','0 0 1.3','0 0 1','true'),('centre','0 0 0','0 1 0','true')])
  base+='doorEndFrames { '+special+'timeEnd 18.00000001; }\n'
  preview=planes(.125,[('centre','0 0 0','0 1 0','true')])
  base+='firstPreview { '+preview+'timeEnd .12500001; }\n'
 diag=(SCRIPTS/'diagnostics.C').read_text().replace('TEST_STOP', 'true' if test else 'false')
 base+='diagnostics83 {type coded; libs (utilityFunctionObjects); name diagnostics83; executeControl timeStep; executeInterval 1; writeControl none; codeInclude #{\n#include "fvCFD.H"\n#include "turbulentFluidThermoModel.H"\n#include <fstream>\n#include <iomanip>\n#include <vector>\n#include <sstream>\n#include <algorithm>\n#}; codeOptions #{\n-I$(LIB_SRC)/TurbulenceModels/turbulenceModels/lnInclude -I$(LIB_SRC)/TurbulenceModels/compressible/lnInclude -I$(LIB_SRC)/transportModels/compressible/lnInclude -I$(LIB_SRC)/thermophysicalModels/basic/lnInclude -I$(LIB_SRC)/thermophysicalModels/specie/lnInclude\n#}; codeLibs #{\n-lfluidThermophysicalModels -lcompressibleTurbulenceModels\n#}; codeRead #{\n const fvMesh& m=mesh();\n if(!m.foundObject<volScalarField>("doorKm")){auto* km=new volScalarField(IOobject("doorKm",m.time().timeName(),m,IOobject::READ_IF_PRESENT,IOobject::AUTO_WRITE,IOobject::REGISTER),m,dimensionedScalar(dimless/dimTime,Zero));km->store();}\n#}; codeExecute #{\n'+diag+'\n#};}\n}\n'
 (case/'system/controlDict').write_text(base)
 # Zero-time plane output deliberately excludes scalar transport / flux diagnostics.
 (case/'system/initialSurfaces').write_text(header('controlDict')+'libs (atmosphericModels); application postProcess; startFrom startTime; startTime 0; stopAt endTime; endTime 0; deltaT 1; writeControl timeStep; writeInterval 1; functions\n{clip {'+planes(.125,[(n,'0 0 '+str(z),'0 0 1',i) for n,z,i in [('head',1.50,'true'),('headCells',1.50,'false'),('sill',1.30,'true'),('low',1.,'true')]])+'} sections {'+planes(.25,[('centre','0 0 0','0 1 0','true')])+'}}\n')
 # Override the zero-time export with every production sampling object, excluding flux-based monitors.
 if planesOn:
  snippets=[]
  for objectName in ['clip','sections','warmIso']:
   start=base.index(objectName+' {');brace=base.index('{',start);depth=1;i=brace+1
   while depth:
    depth += (base[i]=='{')-(base[i]=='}');i+=1
   snippets.append(base[start:i])
  (case/'system/initialSurfaces').write_text(header('controlDict')+'libs (atmosphericModels); application postProcess; startFrom startTime; startTime 0; stopAt endTime; endTime 0; deltaT 1; writeControl timeStep; writeInterval 1; functions\n{\n'+'\n'.join(snippets)+'\n}\n')

def prepare(case,kind,still=False,offset=0,fixed=-1,end=60,test=False,planesOn=True):
 # template/: case72's thermophysical and turbulence properties with Tref at the outside air's
 # 310.93 K, and case77's schemes and solution settings with the tracer named outdoor.
 for f in ['thermophysicalProperties','turbulenceProperties']:shutil.copy(TEMPLATE/'constant'/f,case/'constant'/f)
 (case/'constant/g').write_text(header('g','uniformDimensionedVectorField')+'dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);\n')
 for f in ['fvSchemes','fvSolution']:shutil.copy(TEMPLATE/'system'/f,case/'system'/f)
 (case/'system/decomposeParDict').write_text(header('decomposeParDict')+'numberOfSubdomains 2; method scotch;\n')
 initialize(case,kind,still);options(case,kind,offset,fixed);controls(case,end,test,planesOn)
