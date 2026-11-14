const fvMesh& m=mesh();
const auto& T=m.lookupObject<volScalarField>("T");
const auto& U=m.lookupObject<volVectorField>("U");
const auto& rho=m.lookupObject<volScalarField>("rho");
const auto& p=m.lookupObject<volScalarField>("p");
const auto& phi=m.lookupObject<surfaceScalarField>("phi");
const auto& V=m.V();const auto& C=m.C();
auto rf=fvc::interpolate(rho);auto tf=fvc::interpolate(T);
DynamicList<scalar> row;
row.append(m.time().value());row.append(m.time().deltaTValue());row.append(m.time().elapsedClockTime());
for(const word name:wordList({"fanHighLeft","fanHighRight","fanLowLeft","fanLowRight","doorway","doorUpper","doorLower"}))
{
 const auto& z=m.faceZones()[m.faceZones().findZoneID(name)];
 scalar sum=0,sm=0,qsum=0,qsm=0,hpos=0,hneg=0;
 forAll(z,j)
 {
  label f=z[j];scalar ph,rr,tt,w=1;
  if(f<m.nInternalFaces()){ph=phi[f];rr=rf()[f];tt=tf()[f];}
  else {label b=m.boundaryMesh().whichPatch(f);label k=f-m.boundaryMesh()[b].start();ph=phi.boundaryField()[b][k];rr=rf().boundaryField()[b][k];tt=tf().boundaryField()[b][k];if(m.boundary()[b].coupled())w=.5;}
  if(z.flipMap()[j])ph=-ph;
  sum+=w*ph;sm+=w*mag(ph);qsum+=w*ph/rr;qsm+=w*mag(ph)/rr;
  if(ph>0)hpos+=w*ph*1005*(tt-287.15);else hneg-=w*ph*1005*(tt-287.15);
 }
 for(scalar* v:{&sum,&sm,&qsum,&qsm,&hpos,&hneg})reduce(*v,sumOp<scalar>());
 row.append((sm+sum)/2);row.append((sm-sum)/2);row.append((qsm+qsum)/2);row.append((qsm-qsum)/2);row.append(hpos);row.append(hneg);
}
scalar mass=0,energy=0,minT=GREAT,maxT=-GREAT;vector minP(Zero),maxP(Zero);
forAll(V,i){mass+=rho[i]*V[i];energy+=p[i]*V[i];if(T[i]<minT){minT=T[i];minP=C[i];}if(T[i]>maxT){maxT=T[i];maxP=C[i];}}
reduce(mass,sumOp<scalar>());reduce(energy,sumOp<scalar>());row.append(mass);row.append((1005.0/(8314.46261815324/28.96)-1)*energy);
scalar gmin=minT,gmax=maxT;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
label minrank=(minT==gmin?Pstream::myProcNo():labelMax),maxrank=(maxT==gmax?Pstream::myProcNo():labelMax);reduce(minrank,minOp<label>());reduce(maxrank,minOp<label>());
if(Pstream::myProcNo()!=minrank)minP=vector(Zero);if(Pstream::myProcNo()!=maxrank)maxP=vector(Zero);reduce(minP,sumOp<vector>());reduce(maxP,sumOp<vector>());
row.append(gmin);for(direction k=0;k<3;k++)row.append(minP[k]);row.append(gmax);for(direction k=0;k<3;k++)row.append(maxP[k]);
for(label zone=0;zone<10;zone++)
{
 scalar vol=0,ts=0,us=0,ep=0,ma=0;
 forAll(V,i){const vector& c=C[i];bool in=false;
 if(zone<8){label r=zone/4,l=zone%4;in=(r==0?c.x()<4:c.x()>4.08);if(l==1)in=in&&c.y()>.10&&c.y()<1.10;if(l==2)in=in&&c.y()<.10;if(l==3)in=in&&c.y()>2.20;}
 if(zone==8)in=c.x()>6.4&&c.x()<6.8&&c.y()>1&&c.y()<1.2&&c.z()<.32;
 if(zone==9)in=c.x()>6.4&&c.x()<6.8&&c.y()>.04&&c.y()<.16&&c.z()<.32;
 if(in){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);ep+=V[i]*p[i];ma+=V[i]*rho[i];}}
 for(scalar* v:{&vol,&ts,&us,&ep,&ma})reduce(*v,sumOp<scalar>());
 row.append(ts/max(vol,SMALL));row.append(us/max(vol,SMALL));row.append((1005.0/(8314.46261815324/28.96)-1)*ep);row.append(ma);
}
const auto& wh=m.lookupObject<volScalarField>("wallHeatFlux");
for(const word name:wordList({"stoveRoomWalls","coldRoomWalls","doorwayReveal","stove","flue"})){
 label b=m.boundaryMesh().findPatchID(name);row.append(gSum(wh.boundaryField()[b]*m.magSf().boundaryField()[b]));}
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
