const fvMesh& m=mesh();
const auto& T=m.lookupObject<volScalarField>("T");
const auto& U=m.lookupObject<volVectorField>("U");
const auto& rho=m.lookupObject<volScalarField>("rho");
const auto& p=m.lookupObject<volScalarField>("p");
const auto& phi=m.lookupObject<surfaceScalarField>("phi");
const auto& V=m.V();const auto& C=m.C();
const scalar dt=m.time().deltaTValue(),t=m.time().value();
DynamicList<scalar> row;row.append(t);row.append(dt);row.append(m.time().elapsedClockTime());
scalar supply=0,ret=0,minflow=0,moutflow=0;
for(const word name:wordList({"register_livingW","register_livingE","register_kitchen","register_bedroom","register_bath","register_spare","return"}))
{
 label b=m.boundaryMesh().findPatchID(name);scalar pos=0,neg=0,ts=0,wgt=0,hpos=0,hneg=0;
 const auto& ph=phi.boundaryField()[b];const auto& tt=T.boundaryField()[b];
 forAll(ph,i){pos+=max(ph[i],scalar(0));neg+=max(-ph[i],scalar(0));ts+=mag(ph[i])*tt[i];wgt+=mag(ph[i]);hpos+=max(ph[i],scalar(0))*1005*(tt[i]-289.82);hneg+=max(-ph[i],scalar(0))*1005*(tt[i]-289.82);}
 for(scalar* v:{&pos,&neg,&ts,&wgt,&hpos,&hneg})reduce(*v,sumOp<scalar>());
 row.append(pos);row.append(neg);row.append(wgt>SMALL?ts/wgt:289.82);row.append(hpos);row.append(hneg);
 if(name=="return")ret+=hpos-hneg;else supply+=hneg-hpos;
 minflow+=neg;moutflow+=pos;
}
auto tf=fvc::interpolate(T);
for(const word name:wordList({"gap","bedDoor","bathDoor","livingDoor","kitchenDoor"}))
{
 const auto& z=m.faceZones()[m.faceZones().findZoneID(name)];scalar sum=0,sm=0,hpos=0,hneg=0;
 forAll(z,j){label f=z[j];scalar ph,tt,w=1;
 if(f<m.nInternalFaces()){ph=phi[f];tt=tf()[f];}
 else{label b=m.boundaryMesh().whichPatch(f);label k=f-m.boundaryMesh()[b].start();ph=phi.boundaryField()[b][k];tt=tf().boundaryField()[b][k];if(m.boundary()[b].coupled())w=.5;}
 if(z.flipMap()[j])ph=-ph;
 sum+=w*ph;sm+=w*mag(ph);if(ph>0)hpos+=w*ph*1005*(tt-289.82);else hneg-=w*ph*1005*(tt-289.82);}
 for(scalar* v:{&sum,&sm,&hpos,&hneg})reduce(*v,sumOp<scalar>());
 row.append((sm+sum)/2);row.append((sm-sum)/2);row.append(hpos);row.append(hneg);
}
scalar mass=0,enthalpy=0,intp=0,minT=GREAT,maxT=-GREAT;vector minP(Zero),maxP(Zero);
forAll(V,i){mass+=rho[i]*V[i];enthalpy+=rho[i]*1005*(T[i]-289.82)*V[i];intp+=p[i]*V[i];if(T[i]<minT){minT=T[i];minP=C[i];}if(T[i]>maxT){maxT=T[i];maxP=C[i];}}
for(scalar* v:{&mass,&enthalpy,&intp})reduce(*v,sumOp<scalar>());
row.append(mass);row.append(enthalpy);row.append(intp);
scalar gmin=minT,gmax=maxT;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
label minrank=(minT==gmin?Pstream::myProcNo():labelMax),maxrank=(maxT==gmax?Pstream::myProcNo():labelMax);reduce(minrank,minOp<label>());reduce(maxrank,minOp<label>());
if(Pstream::myProcNo()!=minrank)minP=vector(Zero);if(Pstream::myProcNo()!=maxrank)maxP=vector(Zero);reduce(minP,sumOp<vector>());reduce(maxP,sumOp<vector>());
row.append(gmin);for(direction k=0;k<3;k++)row.append(minP[k]);row.append(gmax);for(direction k=0;k<3;k++)row.append(maxP[k]);
for(label r=0;r<7;r++)for(label l=0;l<5;l++){
 scalar vol=0,ts=0;
 forAll(V,i){const vector& c=C[i];bool in=false;
 if(r==0)in=c.x()<5.6&&c.z()<4.4;
 if(r==1)in=c.x()>5.7&&c.z()<4.4;
 if(r==2)in=c.x()>2.1&&c.x()<7.6&&c.z()>4.5&&c.z()<5.4;
 if(r==3)in=c.x()<4&&c.z()>5.5;
 if(r==4)in=c.x()>4.1&&c.x()<6.1&&c.z()>5.5;
 if(r==5)in=c.x()>6.2&&c.z()>5.5;
 if(r==6)in=!(c.x()>6.2&&c.z()>5.5);
 if(l==1)in=in&&c.y()<.2;if(l==2)in=in&&c.y()>.9&&c.y()<1.2;if(l==3)in=in&&c.y()>1.5&&c.y()<1.8;if(l==4)in=in&&c.y()>2.2;
 if(in){vol+=V[i];ts+=V[i]*T[i];}}
 reduce(vol,sumOp<scalar>());reduce(ts,sumOp<scalar>());row.append(ts/max(vol,SMALL));
}
static scalarList integral(8,0);const auto& wh=m.lookupObject<volScalarField>("wallHeatFlux");
const auto& aw=m.lookupObject<volScalarField>("assembledWallHeatFlux");label ih=0;
for(const word name:wordList({"floor","ceiling","walls","windows"})){
 label b=m.boundaryMesh().findPatchID(name);
 scalar q=-gSum(aw.boundaryField()[b]*m.magSf().boundaryField()[b]);
 integral[ih]+=q*dt;row.append(q);row.append(integral[ih++]);row.append(-gSum(wh.boundaryField()[b]*m.magSf().boundaryField()[b]));}
integral[4]+=supply*dt;integral[5]+=ret*dt;integral[6]+=minflow*dt;integral[7]+=moutflow*dt;
for(label j=4;j<8;j++)row.append(integral[j]);
static scalar last=-GREAT;
bool test=isFile(m.time().globalPath()/"TEST_50_STEPS");
bool sample=test||last<0||std::floor((t+1e-8)/.625)>std::floor((last+1e-8)/.625)||m.time().writeTime();
if(test&&m.time().timeIndex()>=50)const_cast<Time&>(m.time()).writeAndEnd();
if(!sample)return true;
last=t;
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
