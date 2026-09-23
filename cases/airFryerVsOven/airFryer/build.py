#!/usr/bin/env python3
# Generate this clean OpenFOAM case: geometry, mesh, dictionaries and initial fields.
from pathlib import Path
import gmsh, re, shutil, subprocess
HERE=Path(__file__).resolve().parent
NAME='air_fryer'
CFG={'W': 0.32, 'H': 0.34, 'z': 0.01, 'inlets': [(0.0, 0.05), (0.27, 0.32)], 'outlet': (0.11, 0.21), 'obstacles': [(0.04, 0.045, 0.01, 0.295), (0.27, 0.045, 0.01, 0.295), (0.05, 0.335, 0.06, 0.005), (0.21, 0.335, 0.06, 0.005), (0.055, 0.04, 0.02, 0.01), (0.095, 0.04, 0.02, 0.01), (0.135, 0.04, 0.02, 0.01), (0.175, 0.04, 0.02, 0.01), (0.215, 0.04, 0.02, 0.01), (0.255, 0.04, 0.01, 0.01), (0.085, 0.105, 0.05, 0.025), (0.185, 0.105, 0.05, 0.025), (0.085, 0.19, 0.05, 0.025), (0.185, 0.19, 0.05, 0.025)]}

def header(cls,obj):
    return f"FoamFile\n{{\n    format ascii;\n    class {cls};\n    object {obj};\n}}\n"

def mesh():
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal',1); gmsh.option.setNumber('Mesh.RandomFactor',0); gmsh.model.add(NAME)
    c=CFG; W,H,z=c['W'],c['H'],c['z']
    outer=gmsh.model.occ.addRectangle(0,0,0,W,H)
    obs=[gmsh.model.occ.addRectangle(x,y,0,w,h) for x,y,w,h in c['obstacles']]
    cut,_=gmsh.model.occ.cut([(2,outer)],[(2,o) for o in obs],removeObject=True,removeTool=True)
    gmsh.model.occ.synchronize(); ext=[]
    for _,s in cut: ext += gmsh.model.occ.extrude([(2,s)],0,0,z,numElements=[1],recombine=True)
    gmsh.model.occ.synchronize(); vols=[t for d,t in ext if d==3]
    pg=gmsh.model.addPhysicalGroup(3,vols); gmsh.model.setPhysicalName(3,pg,'fluid')
    groups={'inlet':[],'outlet':[],'walls':[],'frontAndBack':[]}; tol=1e-5
    def inside(v,a,b): return a-1e-6 <= v <= b+1e-6
    for _,tag in gmsh.model.getEntities(2):
        xmin,ymin,zmin,xmax,ymax,zmax=gmsh.model.getBoundingBox(2,tag)
        cx,cy,cz=gmsh.model.occ.getCenterOfMass(2,tag)
        if zmax-zmin<tol: groups['frontAndBack'].append(tag); continue
        assigned=False
        if NAME=='air_fryer' and ymax-ymin<tol and cy>H-.006:
            for span in c['inlets']:
                if inside(cx,*span): groups['inlet'].append(tag); assigned=True
            if inside(cx,*c['outlet']): groups['outlet'].append(tag); assigned=True
        if NAME=='convection_oven' and xmax-xmin<tol and cx<.006:
            for span in c['inlets']:
                if inside(cy,*span): groups['inlet'].append(tag); assigned=True
            if inside(cy,*c['outlet']): groups['outlet'].append(tag); assigned=True
        if not assigned: groups['walls'].append(tag)
    for n,tags in groups.items():
        if not tags: raise RuntimeError(f'no surfaces assigned to {n}')
        pg=gmsh.model.addPhysicalGroup(2,tags); gmsh.model.setPhysicalName(2,pg,n)
    gmsh.option.setNumber('Mesh.CharacteristicLengthMin',.005)
    gmsh.option.setNumber('Mesh.CharacteristicLengthMax',.007)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.model.mesh.generate(3); gmsh.write(str(HERE/'mesh.msh')); gmsh.finalize()
    subprocess.run(['gmshToFoam','mesh.msh'],cwd=HERE,check=True)
    bp=HERE/'constant/polyMesh/boundary'; txt=bp.read_text()
    txt=re.sub(r'(frontAndBack\s*\{[^}]*?type\s+)patch(\s*;)',r'\1empty\2',txt,flags=re.S)
    txt=re.sub(r'(walls\s*\{[^}]*?type\s+)patch(\s*;)',r'\1wall\2',txt,flags=re.S)
    bp.write_text(txt)

def dictionaries():
    (HERE/'0').mkdir(parents=True,exist_ok=True); (HERE/'constant').mkdir(exist_ok=True); (HERE/'system').mkdir(exist_ok=True)
    uin='uniform (0 -1.5 0)' if NAME=='air_fryer' else 'uniform (1 0 0)'
    fields={
      'U':('volVectorField','[0 1 -1 0 0 0 0]','uniform (0 0 0)',f'inlet {{ type fixedValue; value {uin}; }}\noutlet {{ type inletOutlet; inletValue uniform (0 0 0); value uniform (0 0 0); }}\nwalls {{ type noSlip; }}\nfrontAndBack {{ type empty; }}'),
      'p':('volScalarField','[0 2 -2 0 0 0 0]','uniform 0','inlet { type zeroGradient; }\noutlet { type fixedValue; value uniform 0; }\nwalls { type zeroGradient; }\nfrontAndBack { type empty; }'),
      'k':('volScalarField','[0 2 -2 0 0 0 0]','uniform 0.00375','inlet { type fixedValue; value uniform 0.00375; }\noutlet { type inletOutlet; inletValue uniform 0.00375; value uniform 0.00375; }\nwalls { type kqRWallFunction; value uniform 0.00375; }\nfrontAndBack { type empty; }'),
      'omega':('volScalarField','[0 0 -1 0 0 0 0]','uniform 120','inlet { type fixedValue; value uniform 120; }\noutlet { type inletOutlet; inletValue uniform 120; value uniform 120; }\nwalls { type omegaWallFunction; value uniform 120; }\nfrontAndBack { type empty; }'),
      'nut':('volScalarField','[0 2 -1 0 0 0 0]','uniform 0','inlet { type calculated; value uniform 0; }\noutlet { type calculated; value uniform 0; }\nwalls { type nutkWallFunction; value uniform 0; }\nfrontAndBack { type empty; }')}
    for obj,(cls,dims,internal,bcs) in fields.items():
        (HERE/'0'/obj).write_text(header(cls,obj)+f'dimensions {dims};\ninternalField {internal};\nboundaryField\n{{\n{bcs}\n}}\n')
    (HERE/'constant/physicalProperties').write_text(header('dictionary','physicalProperties')+'viscosityModel constant;\nnu 1.5e-05;\n')
    (HERE/'constant/momentumTransport').write_text(header('dictionary','momentumTransport')+'simulationType RAS;\nRAS { model kOmegaSST; turbulence on; printCoeffs on; }\n')
    (HERE/'constant/transportProperties').write_text(header('dictionary','transportProperties')+'transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] 1.5e-05;\n')
    (HERE/'constant/turbulenceProperties').write_text(header('dictionary','turbulenceProperties')+'simulationType RAS;\nRAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }\n')
    (HERE/'system/controlDict').write_text(header('dictionary','controlDict')+'''application pimpleFoam;
solver incompressibleFluid;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 25;
deltaT 0.001;
adjustTimeStep yes;
maxCo 0.7;
maxDeltaT 0.004;
writeControl adjustableRunTime;
writeInterval 0.0416666667;
purgeWrite 0;
writeFormat binary;
writePrecision 7;
runTimeModifiable true;
''')
    (HERE/'system/fvSchemes').write_text(header('dictionary','fvSchemes')+'''ddtSchemes { default backward; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''')
    (HERE/'system/fvSolution').write_text(header('dictionary','fvSolution')+'''solvers
{
 p { solver GAMG; tolerance 1e-7; relTol 0.05; smoother GaussSeidel; }
 pFinal { $p; relTol 0; }
 "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
 "(U|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { ".*" 0.8; } }
''')
    (HERE/'system/decomposeParDict').write_text(header('dictionary','decomposeParDict')+'numberOfSubdomains 4;\nmethod scotch;\n')
    (HERE/'system/centreline').write_text('''type surfaces;
libs (sampling);
surfaceFormat vtk;
fields (U p k);
surfaces
{
    midPlane
    {
        type cuttingPlane;
        point (0 0 0.005);
        normal (0 0 1);
        interpolate true;
    }
}
''')

if __name__=='__main__':
    shutil.rmtree(HERE/'constant/polyMesh',ignore_errors=True); shutil.rmtree(HERE/'0',ignore_errors=True)
    dictionaries(); mesh()
