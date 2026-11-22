const fvMesh& m=mesh();
const auto& T=m.lookupObject<volScalarField>("T");
const auto& U=m.lookupObject<volVectorField>("U");
const auto& rho=m.lookupObject<volScalarField>("rho");
const auto& p=m.lookupObject<volScalarField>("p");
const auto& phi=m.lookupObject<surfaceScalarField>("phi");
const auto& V=m.V();const auto& C=m.C();
auto rf=fvc::interpolate(rho);auto tf=fvc::interpolate(T);
for(const word name:wordList({"liner","walls","ceiling","floor"})){
 label bi=m.boundaryMesh().findPatchID(name);
 if(bi>=0)const_cast<radLayerWallFvPatchScalarField&>(refCast<const radLayerWallFvPatchScalarField>(T.boundaryField()[bi])).commitFinalSurface();
}
// Discrete end-of-step heat integrals, computed before down-sampling rows.
static scalarList integral(8,0);static label previousIndex=-1;static scalar nextSample=0;
const wordList heatNames({"liner","door","rangeFront","cooktop","walls","ceiling","floor","cabinets"});
const auto& wh=m.lookupObject<volScalarField>("assembledWallHeatFlux");
scalarList heat(8,0);
forAll(heatNames,j){label b=m.boundaryMesh().findPatchID(heatNames[j]);if(b>=0)heat[j]=gSum(wh.boundaryField()[b]*m.magSf().boundaryField()[b]);}
if(previousIndex!=m.time().timeIndex()){forAll(heat,j)integral[j]+=heat[j]*m.time().deltaTValue();previousIndex=m.time().timeIndex();}
bool test=isFile(m.time().globalPath()/"TEST_50_STEPS");

bool output=test || m.time().value()+1e-8>=nextSample;
if(output){nextSample=(std::floor(m.time().value()/.625+1e-7)+1)*.625;
DynamicList<scalar> row;
row.append(m.time().value());row.append(m.time().deltaTValue());row.append(m.time().elapsedClockTime());
for(const word name:wordList({"mouth","mouthUpper","mouthLower"}))
{
 label zi=m.faceZones().findZoneID(name);
 if(zi<0){for(label j=0;j<6;j++)row.append(0);continue;}
 const auto& z=m.faceZones()[zi];
 scalar sum=0,sm=0,qsum=0,qsm=0,hpos=0,hneg=0;
 forAll(z,j)
 {
  label f=z[j];scalar ph,rr,tt,w=1;
  if(f<m.nInternalFaces()){ph=phi[f];rr=rf()[f];tt=tf()[f];}
  else {label b=m.boundaryMesh().whichPatch(f);label k=f-m.boundaryMesh()[b].start();ph=phi.boundaryField()[b][k];rr=rf().boundaryField()[b][k];tt=tf().boundaryField()[b][k];if(m.boundary()[b].coupled())w=.5;}
  if(z.flipMap()[j])ph=-ph;
  sum+=w*ph;sm+=w*mag(ph);qsum+=w*ph/rr;qsm+=w*mag(ph)/rr;
  if(ph>0)hpos+=w*ph*1005*(tt-293.15);else hneg-=w*ph*1005*(tt-293.15);
 }
 for(scalar* v:{&sum,&sm,&qsum,&qsm,&hpos,&hneg})reduce(*v,sumOp<scalar>());
 row.append((sm+sum)/2);row.append((sm-sum)/2);row.append((qsm+qsum)/2);row.append((qsm-qsum)/2);row.append(hpos);row.append(hneg);
}
scalar mass=0,energy=0,minT=GREAT,maxT=-GREAT;vector minP(Zero),maxP(Zero);
forAll(V,i){mass+=rho[i]*V[i];energy+=p[i]*V[i];if(T[i]<minT){minT=T[i];minP=C[i];}if(!(C[i].x()<.30&&C[i].y()>.24&&C[i].y()<.72&&C[i].z()<.64)&&T[i]>maxT){maxT=T[i];maxP=C[i];}}
reduce(mass,sumOp<scalar>());reduce(energy,sumOp<scalar>());row.append(mass);row.append((1005.0/(8314.46261815324/28.96)-1)*energy);
scalar gmin=minT,gmax=maxT;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
label minrank=(minT==gmin?Pstream::myProcNo():labelMax),maxrank=(maxT==gmax?Pstream::myProcNo():labelMax);reduce(minrank,minOp<label>());reduce(maxrank,minOp<label>());
if(Pstream::myProcNo()!=minrank)minP=vector(Zero);if(Pstream::myProcNo()!=maxrank)maxP=vector(Zero);reduce(minP,sumOp<vector>());reduce(maxP,sumOp<vector>());
row.append(gmin);for(direction k=0;k<3;k++)row.append(minP[k]);row.append(gmax);for(direction k=0;k<3;k++)row.append(maxP[k]);
for(label zone=0;zone<8;zone++)
{
 scalar vol=0,ts=0,us=0,ep=0,ma=0,eex=0;
 forAll(V,i){const vector& c=C[i];bool cavity=c.x()<.30&&c.y()>.24&&c.y()<.72&&c.z()<.64;bool in=!cavity;
 if(zone==1)in=in&&c.y()<.10;
 if(zone==2)in=in&&c.y()>.10&&c.y()<1.10;
 if(zone==3)in=in&&c.y()>1.50&&c.y()<1.80;
 if(zone==4)in=in&&c.y()>2.20;
 if(zone==5)in=in&&c.x()<.30&&c.y()>1.50&&c.y()<1.80&&c.z()>2&&c.z()<2.40;
 if(zone==6)in=in&&c.x()<.30&&c.y()>1.50&&c.y()<1.80&&c.z()>1&&c.z()<1.40;
 if(zone==7)in=cavity;
 if(in){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);ep+=V[i]*p[i];ma+=V[i]*rho[i];eex+=V[i]*rho[i]*(1005.0-8314.46261815324/28.96)*(T[i]-293.15);}}
 for(scalar* v:{&vol,&ts,&us,&ep,&ma,&eex})reduce(*v,sumOp<scalar>());
 row.append(ts/max(vol,SMALL));row.append(us/max(vol,SMALL));row.append((1005.0/(8314.46261815324/28.96)-1)*ep);row.append(ma);row.append(eex);
}
for(scalar x:heat)row.append(x);
for(scalar x:integral)row.append(x);
for(const word name:wordList({"liner","walls","ceiling","floor"})){
 label b=m.boundaryMesh().findPatchID(name);scalar e=0;
 if(b>=0)e=refCast<const radLayerWallFvPatchScalarField>(T.boundaryField()[b]).storedEnergyAbove(293.15);
 row.append(e);
}
const auto& raw=m.lookupObject<volScalarField>("wallHeatFlux");
for(const word name:heatNames){label bi=m.boundaryMesh().findPatchID(name);row.append(bi>=0?gSum(raw.boundaryField()[bi]*m.magSf().boundaryField()[bi]):scalar(0));}
scalar tm=gMax(T.primitiveField());row.append(tm);
vector tpos(Zero);scalar pp=0;label tr=labelMax;
forAll(T,i)if(T[i]==tm){tr=Pstream::myProcNo();tpos=C[i];pp=p[i];break;}
label gr=tr;reduce(gr,minOp<label>());if(Pstream::myProcNo()!=gr){tpos=vector(Zero);pp=0;}
reduce(tpos,sumOp<vector>());reduce(pp,sumOp<scalar>());for(direction di=0;di<3;di++)row.append(tpos[di]);row.append(pp);
label li=m.boundaryMesh().findPatchID("liner");scalar lmax=li>=0 ? gMax(T.boundaryField()[li]) : 0;row.append(lmax);
// Flux-based Courant number, exact axis-aligned cell bounds and speed, top 12 across ranks.
auto fs=fvc::surfaceSum(mag(phi));
std::vector<std::pair<scalar,label>> ranks;
forAll(V,i)ranks.emplace_back(.5*m.time().deltaTValue()*fs()[i]/(rho[i]*V[i]),i);
std::partial_sort(ranks.begin(),ranks.begin()+min(label(12),label(ranks.size())),ranks.end(),[](const auto& a,const auto& b){return a.first>b.first;});
List<scalarList> candidates(Pstream::nProcs());scalarList& mine=candidates[Pstream::myProcNo()];mine.setSize(12*10,0);
for(label j=0;j<min(label(12),label(ranks.size()));j++){
 label i=ranks[j].second;vector lo(GREAT,GREAT,GREAT),hi(-GREAT,-GREAT,-GREAT);
 for(label pt:m.cellPoints()[i]){const auto& v=m.points()[pt];lo=Foam::min(lo,v);hi=Foam::max(hi,v);}
 mine[10*j]=ranks[j].first;mine[10*j+1]=mag(U[i]);for(direction d=0;d<3;d++){mine[10*j+2+d]=C[i][d];mine[10*j+5+d]=hi[d]-lo[d];}mine[10*j+8]=i;mine[10*j+9]=Pstream::myProcNo();
}
Pstream::gatherList(candidates);
if(Pstream::master()){
 fileName dir=m.time().globalPath()/"postProcessing"/"metrics";mkDir(dir);
 std::ofstream out((dir/"metrics.csv").c_str(),std::ios::app);out<<std::setprecision(14);forAll(row,i){if(i)out<<',';out<<row[i];}out<<'\n';
 std::vector<scalarList> tops;for(const auto& part:candidates)for(label j=0;j<12;j++){scalarList rec(10);for(label k=0;k<10;k++)rec[k]=part[10*j+k];tops.push_back(rec);}
 std::sort(tops.begin(),tops.end(),[](const auto& a,const auto& b){return a[0]>b[0];});
 std::ofstream co((dir/"courant.csv").c_str(),std::ios::app);co<<std::setprecision(14);for(label j=0;j<12;j++){co<<m.time().value()<<','<<j+1;for(scalar v:tops[j])co<<','<<v;co<<'\n';}
}

}
if(test && m.time().timeIndex()>=50)const_cast<Time&>(m.time()).writeAndEnd();
