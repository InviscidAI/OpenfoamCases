const fvMesh& m=mesh();
const auto& T=m.lookupObject<volScalarField>("T");
const auto& U=m.lookupObject<volVectorField>("U");
const auto& rho=m.lookupObject<volScalarField>("rho");
const auto& p=m.lookupObject<volScalarField>("p");
const auto& phi=m.lookupObject<surfaceScalarField>("phi");
const auto& V=m.V(); const auto& C=m.C();
DynamicList<scalar> row;
row.append(m.time().value()); row.append(m.time().deltaTValue()); row.append(m.time().elapsedClockTime());
const word slotName("SLOT");
for (const word name : wordList({slotName, "intake"}))
{
 label id=m.boundaryMesh().findPatchID(name);
 const auto& f=phi.boundaryField()[id]; const auto& tt=T.boundaryField()[id]; const auto& a=m.magSf().boundaryField()[id];
 scalar pos=0,neg=0,ts=0,as=0,tf=0,fs=0;
 forAll(f,i) {pos+=max(f[i],scalar(0));neg+=min(f[i],scalar(0));ts+=tt[i]*a[i];as+=a[i]; tf+=mag(f[i])*tt[i];fs+=mag(f[i]);}
 reduce(pos,sumOp<scalar>());reduce(neg,sumOp<scalar>());reduce(ts,sumOp<scalar>());reduce(as,sumOp<scalar>());reduce(tf,sumOp<scalar>());reduce(fs,sumOp<scalar>());
 row.append(pos);row.append(neg);row.append(ts/as);row.append(tf/max(fs,SMALL));
}
vector du(Zero);scalar dw=0;
scalar mass=0,energy=0,minT=GREAT,maxT=-GREAT;
vector minP(Zero), maxP(Zero);
forAll(V,i)
{
 const vector& c=C[i]; bool near=NEAR;
 if(near) {scalar w=rho[i]*mag(U[i]&vector(NORMAL))*V[i];du+=w*U[i];dw+=w;}
 mass+=rho[i]*V[i];energy+=p[i]*V[i];
 if(T[i]<minT){minT=T[i];minP=c;}if(T[i]>maxT){maxT=T[i];maxP=c;}
}
reduce(du,sumOp<vector>());reduce(dw,sumOp<scalar>());
row.append(atan2(du.y(),du.x())*180/constant::mathematical::pi);row.append(du.x()/max(dw,SMALL));row.append(du.y()/max(dw,SMALL));row.append(du.z()/max(dw,SMALL));
reduce(mass,sumOp<scalar>());reduce(energy,sumOp<scalar>());row.append(mass);row.append((1005.0/(8314.46261815324/28.96)-1)*energy);
scalar gmin=minT,gmax=maxT;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
if(minT!=gmin)minP=vector(Zero);if(maxT!=gmax)maxP=vector(Zero);
// Select one extremum location deterministically if identical values occur on ranks.
label minrank=(minT==gmin?Pstream::myProcNo():labelMax),maxrank=(maxT==gmax?Pstream::myProcNo():labelMax);reduce(minrank,minOp<label>());reduce(maxrank,minOp<label>());
if(Pstream::myProcNo()!=minrank)minP=vector(Zero);if(Pstream::myProcNo()!=maxrank)maxP=vector(Zero);reduce(minP,sumOp<vector>());reduce(maxP,sumOp<vector>());
row.append(gmin);for(direction k=0;k<3;k++)row.append(minP[k]);row.append(gmax);for(direction k=0;k<3;k++)row.append(maxP[k]);
for(label zone=0;zone<6;zone++)
{
 scalar vol=0,ts=0,us=0;
 forAll(V,i)
 {
  const vector& c=C[i]; bool inside=false;
  if(zone==0)inside=c.x()>=3.96&&c.x()<=4.24&&c.y()>=1&&c.y()<=1.2&&c.z()<=.30;
  if(zone==1)inside=c.x()>=3.40&&c.x()<=3.76&&c.y()>=.04&&c.y()<=.16&&c.z()<=.30;
  if(zone==2)inside=c.x()>=.60&&c.x()<=4&&c.y()>=.10&&c.y()<=1.10&&c.z()<=1.40;
  if(zone==3)inside=c.y()<.10;
  if(zone==4)inside=c.y()>2.20;
  if(zone==5)inside=true;
  if(inside){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);}
 }
 reduce(vol,sumOp<scalar>());reduce(ts,sumOp<scalar>());reduce(us,sumOp<scalar>());row.append(ts/max(vol,SMALL));row.append(us/max(vol,SMALL));
}
const auto& wh=m.lookupObject<volScalarField>("wallHeatFlux");
for (const word name : wordList({"unitSideWall","farWall","sideWall","floor","ceiling"}))
{
 label id=m.boundaryMesh().findPatchID(name); scalar q=gSum(wh.boundaryField()[id]*m.magSf().boundaryField()[id]);row.append(q);
}
if(Pstream::master())
{
 fileName dir=m.time().globalPath()/"postProcessing"/"metrics";mkDir(dir);
 std::ofstream out((dir/"metrics.csv").c_str(),std::ios::app);out<<std::setprecision(14);
 forAll(row,i){if(i)out<<',';out<<row[i];}out<<'\n';
}
