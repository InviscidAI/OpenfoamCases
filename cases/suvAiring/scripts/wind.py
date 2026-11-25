from build import *
USTAR=2.5*.41/np.log(151.)
EXT=['inlet','outlet','sides','top']
def profile(z):
 z=np.asarray(z);u=USTAR/.41*np.log((z+.01)/.01);k=np.full_like(z,USTAR**2/.3);om=USTAR/(.3*.41*(z+.01))
 return np.column_stack([np.zeros_like(z),u,np.zeros_like(z)]),k,om
def listval(a):
 a=np.asarray(a);vec=a.ndim==2
 return 'nonuniform List<'+('vector' if vec else 'scalar')+'>\n'+str(len(a))+'\n(\n'+'\n'.join(('(%s)'%' '.join('%.12g'%x for x in v)) if vec else '%.12g'%v for v in a)+'\n)'
def patchinfo(case):
 s=(case/'constant/polyMesh/boundary').read_text()
 return {n:(int(st),int(nf)) for n,nf,st in re.findall(r'(\w+)\s*\{[^}]*nFaces\s+(\d+);[^}]*startFace\s+(\d+);',s,re.S)}
def initialize_wind(case,kind,still=False):
 from prepare import field,WALLS
 arr=np.load(case/'mesh_arrays.npz');C=arr['C'];fc=arr['fc'];pi=patchinfo(case)
 U,k,omega=profile(C[:,2]);hot=box(C,(1.76,-.94,.44),(5.56,.94,1.84)) & (not still)
 T=np.where(hot,319.82,310.93);U[hot]=0;k[hot]=1e-4;omega[hot]=np.sqrt(1e-4)/(.09**.25*.1)
 p=1e5*np.exp(-9.81*C[:,2]/(287.1*310.93));rho=p/((8314.46261815324/28.96)*T)
 data={'U':U,'k':k,'omega':omega,'T':T,'p':p,'p_rgh':p+rho*9.81*C[:,2],'outdoor':np.where(hot,0,1)}
 start=ROOT/'mesh'/kind/'wind_start.npz'
 if start.exists() and not still:
  q=np.load(start);data.update({n:q[n] for n in q.files if n in data});rho=data['p']/((8314.46261815324/28.96)*data['T'])
 dims={'U':'0 1 -1 0 0 0 0','k':'0 2 -2 0 0 0 0','omega':'0 0 -1 0 0 0 0','T':'0 0 0 1 0 0 0','p':'1 -1 -2 0 0 0 0','p_rgh':'1 -1 -2 0 0 0 0','outdoor':'0 0 0 0 0 0 0','nut':'0 2 -1 0 0 0 0','alphat':'1 -1 -1 0 0 0 0','doorKm':'0 0 -1 0 0 0 0'}
 data.update(nut=np.zeros(len(C)),alphat=np.zeros(len(C)),doorKm=np.where(box(C,(2.16,.84,.44),(3.20,1.04,1.72)),1e6,0) if kind=='doorFan' else np.zeros(len(C)))
 abl='flowDir (0 1 0); zDir (0 0 1); Uref 2.5; Zref 1.5; z0 uniform .01; d uniform 0; kappa .41; Cmu .09; C1 0; C2 1; initABL true; '
 for n,a in data.items():
  bc={}
  for w in WALLS:
   if w not in pi:continue
   if n=='U':bc[w]='type noSlip;'
   elif n=='T':bc[w]='type fixedValue; value uniform '+str({'dashboard':342.59,'seats':323.71,'cabinInterior':319.82}[w])+';' if w in ['dashboard','seats','cabinInterior'] and not still else 'type zeroGradient;'
   elif n=='p_rgh':bc[w]='type fixedFluxPressure; value uniform 100000;'
   elif n=='p':bc[w]='type calculated; value uniform 100000;'
   elif n in ['k','omega','nut','alphat']:
    wt={'k':'kLowReWallFunction','omega':'omegaWallFunction','nut':'nutkWallFunction','alphat':'compressible::alphatJayatillekeWallFunction'}[n]
    extra='Prt .85; ' if n=='alphat' else ''
    if n=='nut' and w=='ground':wt='atmNutkWallFunction';extra='z0 uniform .01; kappa .41; Cmu .09; '
    v=1e-4 if n=='k' else np.sqrt(1e-4)/(.09**.25*.1) if n=='omega' else 0
    bc[w]='type '+wt+'; '+extra+'value uniform '+str(v)+';'
   else:bc[w]='type zeroGradient;'
  bc.update(sides='type symmetry;',top='type symmetry;')
  st,nf=pi['outlet'];pu,pk,po=profile(fc[st:st+nf,2]);p0=1e5*np.exp(-9.81*fc[st:st+nf,2]/(287.1*310.93))
  if n in ['U','k','omega']:
   typ={'U':'Velocity','k':'K','omega':'Omega'}[n];v='(0 2.5 0)' if n=='U' else '.138' if n=='k' else '1.1'
   bc['inlet']='type atmBoundaryLayerInlet'+typ+'; '+abl+'value uniform '+v+';'
   bc['outlet']='type pressureInletOutletVelocity; value '+listval(pu)+';' if n=='U' else 'type inletOutlet; inletValue '+listval(pk if n=='k' else po)+'; value '+listval(pk if n=='k' else po)+';'
  elif n in ['T','outdoor']:
   v=310.93 if n=='T' else 1;bc['inlet']='type fixedValue; value uniform '+str(v)+';';bc['outlet']='type inletOutlet; inletValue uniform '+str(v)+'; value uniform '+str(v)+';'
  elif n=='p_rgh':bc['inlet']='type fixedFluxPressure; value uniform 100000;';bc['outlet']='type prghPressure; p '+listval(p0)+'; value uniform 100000;'
  elif n=='p':bc.update(inlet='type calculated; value uniform 100000;',outlet='type calculated; value uniform 100000;')
  elif n in ['nut','alphat']:bc.update(inlet='type calculated; value uniform 0;',outlet='type calculated; value uniform 0;')
  else:bc.update(inlet='type zeroGradient;',outlet='type zeroGradient;')
  field(case,n,dims[n],a,bc,'volVectorField' if n=='U' else 'volScalarField')
 owner=arr['owner'];nei=arr['neighbour'];sf=arr['sf'];un=(data['U'][owner[:len(nei)]]+data['U'][nei])/2;rn=(rho[owner[:len(nei)]]+rho[nei])/2
 flux=np.einsum('ij,ij->i',un,sf[:len(nei)])*rn;bc={}
 for w,(st,nf) in pi.items():
  f=np.zeros(nf)
  if w=='inlet':uv,_,_=profile(fc[st:st+nf,2]);rp=1e5*np.exp(-9.81*fc[st:st+nf,2]/(287.1*310.93))/((8314.46261815324/28.96)*310.93);f=np.einsum('ij,ij->i',uv,sf[st:st+nf])*rp
  elif w=='outlet':f=np.einsum('ij,ij->i',data['U'][owner[st:st+nf]],sf[st:st+nf])*rho[owner[st:st+nf]]
  bc[w]='type symmetry; value uniform 0;' if w in ['sides','top'] else 'type calculated; value '+listval(f)+';'
 (case/'0/phi').write_text(header('phi','surfaceScalarField')+'dimensions [1 0 -1 0 0 0 0]; internalField '+listval(flux)+'; boundaryField\n{\n'+''.join(w+' {'+s+'}\n' for w,s in bc.items())+'}\n')
 for n in ['C','Cx','Cy','Cz']:
  if (case/'0'/n).exists():(case/'0'/n).unlink()

def read_internal(case,t,n):
 import gzip
 path=case/f'{t:g}'/n;raw=path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.gz').read_bytes())
 tail=raw[raw.index(b'internalField'):];m=re.search(rb'nonuniform\s+List<(scalar|vector)>\s+(\d+)\s*\(',tail)
 if not m:raise RuntimeError('Nonuniform physical field required: '+str(path))
 count=int(m[2]);components=3 if m[1]==b'vector' else 1
 if b'format      binary' in raw[:raw.index(b'internalField')] or re.search(rb'format\s+binary',raw[:raw.index(b'internalField')]):
  arr=np.frombuffer(tail,dtype='<f8',count=count*components,offset=m.end()).copy()
 else:
  vals=tail[m.end():tail.rfind(b')')].decode();arr=np.fromstring(vals.replace('(',' ').replace(')',' '),sep=' ')[:count*components]
 return arr.reshape(-1,3) if components==3 else arr

def map_start(precursor,t):
 (precursor/'case.foam').touch();a=np.load(precursor/'mesh_arrays.npz');PC=a['C'];lookup={tuple(c):i for i,c in enumerate(np.round(PC,8))};fields={n:read_internal(precursor,t,n) for n in ['U','k','omega','p']}
 np.savez_compressed(ROOT/'precursor/last_state.npz',C=PC,**fields)
 reports={}
 for kind in ['fourWindows','doorFan']:
  case=ROOT/'mesh'/kind;C=np.load(case/'mesh_arrays.npz')['C'];idx=np.array([lookup.get(tuple(c),-1) for c in np.round(C,8)]);exterior=~geometry(C,'precursor');missing=exterior&(idx<0)
  if missing.any():raise RuntimeError('Unmatched exterior cells '+str(missing.sum()))
  # Reveals become fluid only now. Fill these formerly solid cells from nearest exterior cell at the same x,z, outward along y.
  extra=idx<0;hot=box(C,(1.76,-.94,.44),(5.56,.94,1.84));idx[extra&hot]=0
  for i in np.flatnonzero(extra&~hot):
   c=C[i].copy();found=None
   for d in np.arange(.04,.401,.04):
    c[1]=C[i,1]+np.sign(C[i,1])*d;found=lookup.get(tuple(np.round(c,8)))
    if found is not None:break
   if found is None:
    # Cabin cells are overwritten below; nearest wind state is only a temporary fill.
    found=int(np.argmin(np.sum((PC-C[i])**2,axis=1)))
   idx[i]=found
  out={n:fields[n][idx].copy() for n in fields};hot=box(C,(1.76,-.94,.44),(5.56,.94,1.84));out.update(T=np.where(hot,319.82,310.93),outdoor=np.where(hot,0,1))
  out['U'][hot]=0;out['k'][hot]=1e-4;out['omega'][hot]=np.sqrt(1e-4)/(.09**.25*.1)
  pi=patchinfo(precursor);st,nf=pi['bodyExterior'];fc=a['fc'][st:st+nf];sf=a['sf'][st:st+nf];owner=a['owner'][st:st+nf]
  select=np.zeros(nf,bool)
  for x,sgn in ([(2.28,-1),(3.36,-1),(2.28,1),(3.36,1)] if kind=='fourWindows' else [(3.36,-1)]):
   select|=box(fc,(x,sgn*1.04-1e-6,1.20),(x+.76,sgn*1.04+1e-6,1.68))
  area=np.linalg.norm(sf[select],axis=1);pm=float(np.average(fields['p'][owner[select]],weights=area))
  out['p'][hot]=pm*np.exp(-9.81*(C[hot,2]-1.44)/(287.1*319.82));rho=out['p']/((8314.46261815324/28.96)*out['T']);out['p_rgh']=out['p']+rho*9.81*C[:,2]
  np.savez_compressed(case/'wind_start.npz',**out)
  reports[kind]={'outside_cells':int(exterior.sum()),'outside_unmatched':int(missing.sum()),'new_cabin_and_reveal_cells':int(extra.sum()),'new_nonhot_reveal_cells_adjacent_mapped':int((extra&~hot).sum()),'cabin_reference_p_Pa':pm,'reference_face_area_m2':float(area.sum()),'precursor_time_s':t}
 (ROOT/'precursor/mapping.json').write_text(json.dumps(reports,indent=2));return reports
