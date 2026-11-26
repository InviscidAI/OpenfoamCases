/* The monitor: the body of the coded function object `metrics` in system/functions (codeExecute),
   run at every step and written at the first step and every 0.625 s of flow (and at each field
   write) to postProcessing/metrics/metrics.csv, one row of 104 columns in scripts/columns.json's
   order, and the twelve cells of highest Courant number to postProcessing/metrics/courant.csv.
   The solved runs' code, character for character; scripts/make_case.py drops this comment.
   Two hooks of the solved runs' driver are left in and do nothing unless their files exist in the
   run's folder: CAP_END_744 (end the run at 744 s) and TEST_STEPS (end it after that many steps). */
const fvMesh& m=mesh();
const auto& T=m.lookupObject<volScalarField>("T"); const auto& U=m.lookupObject<volVectorField>("U"); const auto& rho=m.lookupObject<volScalarField>("rho"); const auto& p=m.lookupObject<volScalarField>("p"); const auto& phi=m.lookupObject<surfaceScalarField>("phi"); const auto& V=m.V(); const auto& C=m.C();
const scalar dt=m.time().deltaTValue(),t=m.time().value(); DynamicList<scalar> row;row.append(t);row.append(dt);row.append(m.time().elapsedClockTime());
scalar supply=0,ret=0,minflow=0,moutflow=0,mreg=0,Treg=292.04,Tret=292.04;
for(const word name:wordList({"register","return"})) {
 label b=m.boundaryMesh().findPatchID(name);scalar pos=0,neg=0,ts=0,wgt=0,hpos=0,hneg=0,otr=0,otw=0,cellT=0,area=0;
 const auto& ph=phi.boundaryField()[b];const auto& tt=T.boundaryField()[b];const scalarField tc(tt.patchInternalField());
 forAll(ph,i){pos+=max(ph[i],scalar(0));neg+=max(-ph[i],scalar(0));ts+=mag(ph[i])*tt[i];wgt+=mag(ph[i]);hpos+=max(ph[i],scalar(0))*1005*(tt[i]-292.04);hneg+=max(-ph[i],scalar(0))*1005*(tt[i]-292.04);otr+=max(ph[i],scalar(0))*tt[i];otw+=max(ph[i],scalar(0));cellT+=tc[i];area+=1;}
 for(scalar* v:{&pos,&neg,&ts,&wgt,&hpos,&hneg,&otr,&otw,&cellT,&area})reduce(*v,sumOp<scalar>());
 row.append(pos);row.append(neg);row.append(wgt>SMALL?ts/wgt:cellT/area);row.append(hpos);row.append(hneg);
 if(name=="return"){ret=hpos-hneg;Tret=otw>SMALL?otr/otw:cellT/area;}else{supply=hneg-hpos;mreg=neg;Treg=wgt>SMALL?ts/wgt:cellT/area;}
 minflow+=neg;moutflow+=pos;
}
static scalarList integral(5,0);scalar heater=mreg*1005*(Treg-Tret);integral[0]+=heater*dt;integral[1]+=supply*dt;integral[2]+=ret*dt;integral[3]+=minflow*dt;integral[4]+=moutflow*dt;
row.append(Tret);row.append(heater);for(scalar v:integral)row.append(v);
scalar mass=0,enthalpy=0,intp=0,minT=GREAT,maxT=-GREAT,umax=0;vector minP(Zero),maxP(Zero);
forAll(V,i){mass+=rho[i]*V[i];enthalpy+=rho[i]*1005*(T[i]-292.04)*V[i];intp+=p[i]*V[i];umax=max(umax,mag(U[i]));if(T[i]<minT){minT=T[i];minP=C[i];}if(T[i]>maxT){maxT=T[i];maxP=C[i];}}
for(scalar* v:{&mass,&enthalpy,&intp})reduce(*v,sumOp<scalar>());reduce(umax,maxOp<scalar>());
row.append(mass);row.append(enthalpy);row.append(intp);
scalar gmin=minT,gmax=maxT;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
label minrank=(minT==gmin?Pstream::myProcNo():labelMax),maxrank=(maxT==gmax?Pstream::myProcNo():labelMax);reduce(minrank,minOp<label>());reduce(maxrank,minOp<label>());
if(Pstream::myProcNo()!=minrank)minP=vector(Zero);if(Pstream::myProcNo()!=maxrank)maxP=vector(Zero);reduce(minP,sumOp<vector>());reduce(maxP,sumOp<vector>());
row.append(gmin);for(direction k=0;k<3;k++)row.append(minP[k]);row.append(gmax);for(direction k=0;k<3;k++)row.append(maxP[k]);row.append(umax);
scalar sofaAnkle=0,sofaHead=0;
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(true){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=1 && c.x()<=4.2 && c.y()>=0.05 && c.y()<=0.15 && c.z()>=0 && c.z()<=1.8){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=1 && c.x()<=4.2 && c.y()>=1 && c.y()<=1.2 && c.z()>=0 && c.z()<=1.8){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=1 && c.x()<=4.2 && c.y()>=1.6 && c.y()<=1.8 && c.z()>=0 && c.z()<=1.8){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=1 && c.x()<=4.2 && c.y()>=2.2 && c.y()<=2.4 && c.z()>=0 && c.z()<=1.8){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=2.6 && c.x()<=3 && c.y()>=0.05 && c.y()<=0.15 && c.z()>=0 && c.z()<=0.6){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
sofaAnkle=ts/max(vol,SMALL);}
{scalar vol=0,ts=0,us=0,lo=GREAT,hi=-GREAT,um=0;forAll(V,i){const vector& c=C[i];if(c.x()>=3.3 && c.x()<=3.7 && c.y()>=1 && c.y()<=1.2 && c.z()>=0 && c.z()<=0.6){vol+=V[i];ts+=V[i]*T[i];us+=V[i]*mag(U[i]);lo=min(lo,T[i]);hi=max(hi,T[i]);um=max(um,mag(U[i]));}}
 for(scalar* v:{&vol,&ts,&us})reduce(*v,sumOp<scalar>());reduce(lo,minOp<scalar>());reduce(hi,maxOp<scalar>());reduce(um,maxOp<scalar>());row.append(ts/max(vol,SMALL));row.append(lo);row.append(hi);row.append(us/max(vol,SMALL));row.append(um);
sofaHead=ts/max(vol,SMALL);}
row.append(sofaHead-sofaAnkle);
static scalarList wallIntegral(7,0);const auto& wh=m.lookupObject<volScalarField>("wallHeatFlux");const auto& aw=m.lookupObject<volScalarField>("assembledWallHeatFlux");label ih=0;
for(const word name:wordList({"outerWall","innerWall","floor","ceiling","sideWall","sofa","window"})) {label b=m.boundaryMesh().findPatchID(name); scalar q=-gSum(aw.boundaryField()[b]*m.magSf().boundaryField()[b]);wallIntegral[ih]+=q*dt;row.append(q);row.append(wallIntegral[ih++]);row.append(-gSum(wh.boundaryField()[b]*m.magSf().boundaryField()[b]));row.append(gSum(T.boundaryField()[b]*m.magSf().boundaryField()[b])/gSum(m.magSf().boundaryField()[b]));}
{ scalar um=0,tm=-GREAT;forAll(V,i){if(mag(C[i].y()-0.5)<.051){um=max(um,mag(U[i]));tm=max(tm,T[i]);}}reduce(um,maxOp<scalar>());reduce(tm,maxOp<scalar>());row.append(um);row.append(tm);}
{ scalar um=0,tm=-GREAT;forAll(V,i){if(mag(C[i].y()-1)<.051){um=max(um,mag(U[i]));tm=max(tm,T[i]);}}reduce(um,maxOp<scalar>());reduce(tm,maxOp<scalar>());row.append(um);row.append(tm);}
{ scalar um=0,tm=-GREAT;forAll(V,i){if(mag(C[i].y()-1.5)<.051){um=max(um,mag(U[i]));tm=max(tm,T[i]);}}reduce(um,maxOp<scalar>());reduce(tm,maxOp<scalar>());row.append(um);row.append(tm);}
{ scalar um=0,tm=-GREAT;forAll(V,i){if(mag(C[i].y()-2.2)<.051){um=max(um,mag(U[i]));tm=max(tm,T[i]);}}reduce(um,maxOp<scalar>());reduce(tm,maxOp<scalar>());row.append(um);row.append(tm);}
if(isFile(m.time().globalPath()/"CAP_END_744")){if(t>=743.7 && Pstream::master()){std::ofstream stop((m.time().globalPath()/"STOP_AT_NEXT_WRITE").c_str());}if(t>=744-1e-7)const_cast<Time&>(m.time()).writeAndEnd();}
static scalar last=-GREAT;
label testSteps=0;{fileName f=m.time().globalPath()/"TEST_STEPS";if(isFile(f)){std::ifstream in(f.c_str());in>>testSteps;}}
if(testSteps>0&&m.time().timeIndex()>=testSteps)const_cast<Time&>(m.time()).writeAndEnd();
bool sample=testSteps>0||last<0||std::floor((t+1e-8)/.625)>std::floor((last+1e-8)/.625)||m.time().writeTime();
if(!sample)return true;last=t;
auto fs=fvc::surfaceSum(mag(phi));std::vector<std::pair<scalar,label>> ranks;forAll(V,i)ranks.emplace_back(.5*dt*fs()[i]/(rho[i]*V[i]),i);
std::partial_sort(ranks.begin(),ranks.begin()+min(label(12),label(ranks.size())),ranks.end(),[](const auto& a,const auto& b){return a.first>b.first;});
List<scalarList> candidates(Pstream::nProcs());scalarList& mine=candidates[Pstream::myProcNo()];mine.setSize(12*10,0);
for(label j=0;j<min(label(12),label(ranks.size()));j++){label i=ranks[j].second;vector lo(GREAT,GREAT,GREAT),hi(-GREAT,-GREAT,-GREAT);for(label pt:m.cellPoints()[i]){const auto& v=m.points()[pt];lo=Foam::min(lo,v);hi=Foam::max(hi,v);}mine[10*j]=ranks[j].first;mine[10*j+1]=mag(U[i]);for(direction d=0;d<3;d++){mine[10*j+2+d]=C[i][d];mine[10*j+5+d]=hi[d]-lo[d];}mine[10*j+8]=i;mine[10*j+9]=Pstream::myProcNo();}
Pstream::gatherList(candidates);
if(Pstream::master()){fileName dir=m.time().globalPath()/"postProcessing"/"metrics";mkDir(dir);std::ofstream out((dir/"metrics.csv").c_str(),std::ios::app);out<<std::setprecision(14);forAll(row,i){if(i)out<<',';out<<row[i];}out<<'\n';
std::vector<scalarList> tops;for(const auto& part:candidates)for(label j=0;j<12;j++){scalarList rec(10);for(label k=0;k<10;k++)rec[k]=part[10*j+k];tops.push_back(rec);}std::sort(tops.begin(),tops.end(),[](const auto& a,const auto& b){return a[0]>b[0];});std::ofstream co((dir/"courant.csv").c_str(),std::ios::app);co<<std::setprecision(14);for(label j=0;j<12;j++){co<<t<<','<<j+1;for(scalar v:tops[j])co<<','<<v;co<<'\n';}}
