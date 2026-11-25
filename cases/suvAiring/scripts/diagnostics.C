const fvMesh& m=mesh();
if(!m.foundObject<volScalarField>("outdoor") || !m.foundObject<volScalarField>("rho"))return true;
const auto& T=m.lookupObject<volScalarField>("T");const auto& U=m.lookupObject<volVectorField>("U");const auto& rho=m.lookupObject<volScalarField>("rho");const auto& h=m.lookupObject<volScalarField>("h");const auto& s=m.lookupObject<volScalarField>("outdoor");const auto& phi=m.lookupObject<surfaceScalarField>("phi");
const auto& turb=m.lookupObject<compressible::turbulenceModel>("turbulenceProperties");auto alpha=turb.alphaEff();auto tf=fvc::interpolate(T);auto rf=fvc::interpolate(rho);auto sf=fvc::interpolate(s);surfaceScalarField hf(fvc::flux(phi,h,"div(phi,h)"));surfaceScalarField conductive(fvc::interpolate(alpha())*fvc::snGrad(h)*m.magSf());surfaceScalarField sflux(fvc::flux(phi,s,"div(phi,outdoor)"));auto scalarDiffusion=1.40845*turb.mu()+turb.mut();surfaceScalarField sdiff(fvc::interpolate(scalarDiffusion())*fvc::snGrad(s)*m.magSf());surfaceScalarField kflux(fvc::flux(phi,m.lookupObject<volScalarField>("K"),"div(phi,K)"));
scalar theta=0,rate=0,doorK=1e6;
IOdictionary opts(IOobject("fvOptions",m.time().constant(),m,IOobject::MUST_READ,IOobject::NO_WRITE,false));
if(opts.found("doorPenalty")){const auto& dc=opts.subDict("doorPenalty").subDict("codeContext");doorK=dc.get<scalar>("K");scalar clock=m.time().value()+dc.get<scalar>("clockOffset"),fixed=dc.get<scalar>("fixedAngle");if(fixed>=0)theta=fixed*constant::mathematical::pi/180;else if(clock<=18){theta=constant::mathematical::pi/6*(1-cos(2*constant::mathematical::pi*clock/1.2));rate=constant::mathematical::pi/6*2*constant::mathematical::pi/1.2*sin(2*constant::mathematical::pi*clock/1.2);}}
// Per region: volume, mass, TV, Tmass, outdoorMass, excessEnthalpy.
scalarList v(150,0);scalar tmax=-GREAT,tmin=GREAT,umax=0,errmax=0;vector hot(Zero),cold(Zero),fast(Zero),errat(Zero);
forAll(T,i){const vector c=m.C()[i];scalar vol=m.V()[i],mass=rho[i]*vol;
 auto region=[&](label offset){v[offset]+=vol;v[offset+1]+=mass;v[offset+2]+=T[i]*vol;v[offset+3]+=T[i]*mass;v[offset+4]+=s[i]*mass;v[offset+5]+=mass*1005*(T[i]-310.93);};
 bool cabin=c.x()>1.76&&c.x()<5.56&&mag(c.y())<.84&&c.z()>.44&&c.z()<1.84&&(c.z()<=1.12||c.x()>=1.80+(c.z()-1.12)*.60/.72-1e-8);
 if(cabin){region(0);if(T[i]>tmax){tmax=T[i];hot=c;}if(T[i]<tmin){tmin=T[i];cold=c;}}
 label head=0;
 if(c.z()>1.4&&c.z()<1.6){
 if(c.x()>2.80&&c.x()<3.00){if(c.y()>.32&&c.y()<.56)head=1;else if(c.y()>-.56&&c.y()<-.32)head=2;}
 if(c.x()>3.72&&c.x()<3.92){if(c.y()>-.64&&c.y()<-.40)head=3;else if(c.y()>-.12&&c.y()<.12)head=4;else if(c.y()>.40&&c.y()<.64)head=5;}
 if(c.x()>4.52&&c.x()<4.72){if(c.y()>-.64&&c.y()<-.40)head=6;else if(c.y()>-.12&&c.y()<.12)head=7;else if(c.y()>.40&&c.y()<.64)head=8;}}
 if(head)region(6*head);
 if(mag(U[i])>umax){umax=mag(U[i]);fast=c;}
 if(m.foundObject<volScalarField>("doorKm")){scalar km=m.lookupObject<volScalarField>("doorKm")[i],mask=km/doorK;vector ub=rate*vector(-(c.y()-1.04),c.x()-2.16,0);v[130]+=mask*vol;v[131]+=km*rho[i]*((ub-U[i])&ub)*vol;
 if(mask>1-1e-7&&mag(ub)>1e-8){scalar er=mag(U[i]-ub)/mag(ub);v[132]+=er;v[133]+=1;if(er>errmax){errmax=er;errat=c;}}
 }
 if(cabin){v[143]+=mag(U[i])*vol;v[134]+=.5*mass*magSqr(U[i]);v[136]+=mass*(-9.81*U[i].z());if(m.foundObject<volScalarField>("dpdt"))v[135]+=m.lookupObject<volScalarField>("dpdt")[i]*vol;}
}
// Opening groups at 60,70,80,90,100: Qin,Qout,Min,Mout,Hin,Hout,tracerIn,tracerOut,numericalHnet,conductiveIn.
auto opening=[&](const vector& c,const vector& a,scalar mass,scalar den,scalar temp,scalar tracer,scalar heat,scalar diff,scalar tracerFlux,scalar tracerDiff,scalar keFlux,scalar weight){label off=-1;scalar sign=0;
 if(mag(c.y()+.84)<1e-6&&c.z()>1.20&&c.z()<1.68){sign=1;if(c.x()>2.28&&c.x()<3.04)off=60;if(c.x()>3.36&&c.x()<4.12)off=70;}
 if(mag(c.y()-.84)<1e-6){sign=-1;if(opts.found("doorPenalty")){if(c.x()>2.16&&c.x()<3.20&&c.z()>.44&&c.z()<1.72)off=100;}else if(c.z()>1.20&&c.z()<1.68){if(c.x()>2.28&&c.x()<3.04)off=80;if(c.x()>3.36&&c.x()<4.12)off=90;}}
 if(off<0||mag(a.y())<.9*mag(a))return;scalar orientation=(a.y()>0?1:-1)*sign;scalar f=mass*weight*orientation;label j=f>=0?0:1;v[off+j]+=mag(f)/den;v[off+2+j]+=mag(f);v[off+4+j]+=heat*weight*orientation*(j==0?1:-1);v[off+6+j]+=tracerFlux*weight*orientation*(j==0?1:-1);v[138+(off-60)/10]+=tracerDiff*weight*orientation;v[137]+=keFlux*weight*orientation;v[off+8]+=heat*weight*orientation;v[off+9]+=diff*weight*orientation;
};
forAll(m.neighbour(),f)opening(m.Cf()[f],m.Sf()[f],phi[f],rf()[f],tf()[f],sf()[f],hf[f],conductive[f],sflux[f],sdiff[f],kflux[f],1);
forAll(m.boundary(),b){const auto& p=m.boundary()[b];if(p.coupled()){forAll(p,j)opening(m.Cf().boundaryField()[b][j],m.Sf().boundaryField()[b][j],phi.boundaryField()[b][j],rf().boundaryField()[b][j],tf().boundaryField()[b][j],sf().boundaryField()[b][j],hf.boundaryField()[b][j],conductive.boundaryField()[b][j],sflux.boundaryField()[b][j],sdiff.boundaryField()[b][j],kflux.boundaryField()[b][j],.5);}else{label slot=-1;if(p.name()=="dashboard")slot=120;if(p.name()=="seats")slot=121;if(p.name()=="cabinInterior")slot=122;if(slot>=0){scalarField heatFaces(alpha().boundaryField()[b]*h.boundaryField()[b].snGrad()*m.magSf().boundaryField()[b]);v[slot]=sum(heatFaces);forAll(p,j){vector c=m.C()[p.faceCells()[j]];if(c.x()>1.76&&c.x()<5.56&&mag(c.y())<.84&&c.z()>.44&&c.z()<1.84&&(c.z()<=1.12||c.x()>=1.80+(c.z()-1.12)*.60/.72-1e-8))v[slot+4]+=heatFaces[j];}}}}
v[123]=v[124]+v[125]+v[126];
forAll(v,i)reduce(v[i],sumOp<scalar>());
auto extremum=[&](scalar& value,vector& at,bool maximum){scalar global=value;if(maximum)reduce(global,maxOp<scalar>());else reduce(global,minOp<scalar>());label rank=value==global?Pstream::myProcNo():labelMax;reduce(rank,minOp<label>());if(Pstream::myProcNo()!=rank)at=Zero;reduce(at,sumOp<vector>());value=global;};extremum(tmax,hot,true);extremum(tmin,cold,false);extremum(umax,fast,true);extremum(errmax,errat,true);
static scalar next=0,heatInt=0,advInt=0,diffInt=0,wallOffset=0;
static scalarList openingCumulative(40,0),tracerDiffCumulative(5,0);static scalar CVheatInt=0,pressureInt=0,gravityInt=0,keAdvInt=0;
static bool resumeLoaded=false;
if(!resumeLoaded){
 fileName old=m.time().globalPath()/"postProcessing/diagnostics83/diagnostics.csv";
 std::ifstream in(old.c_str());std::string line,last;while(std::getline(in,line)){if(!line.empty())last=line;}
 if(!last.empty() && last[0]!='t'){std::stringstream ss(last);std::string token;std::vector<double> vals;while(std::getline(ss,token,','))vals.push_back(std::stod(token));if(vals.size()>=173){heatInt=vals[170];advInt=vals[171];diffInt=vals[172];wallOffset=vals[169];if(vals.size()>=213){for(label j=0;j<40;j++)openingCumulative[j]=vals[173+j];}if(vals.size()>=214)CVheatInt=vals[213];if(vals.size()>=219)for(label j=0;j<5;j++)tracerDiffCumulative[j]=vals[214+j];if(vals.size()>=222){pressureInt=vals[219];gravityInt=vals[220];keAdvInt=vals[221];}}}
 resumeLoaded=true;
}
scalar dt=m.time().deltaTValue();heatInt+=dt*(v[120]+v[121]+v[122]);for(label off=60;off<=100;off+=10){advInt+=dt*v[off+8];diffInt+=dt*v[off+9];}
CVheatInt+=dt*v[123];pressureInt+=dt*v[135];gravityInt+=dt*v[136];keAdvInt+=dt*v[137];for(label g=0;g<5;g++)tracerDiffCumulative[g]+=dt*v[138+g];
for(label group=0;group<5;group++)for(label j=0;j<8;j++)openingCumulative[8*group+j]+=dt*v[60+10*group+j];
// Per-cycle Euler-in-time gross transport, splitting a step at an exact swing boundary.
if(opts.found("doorPenalty")){
 static List<scalarList> cycle(15,scalarList(40,0));
 static bool cycleLoaded=false;
 if(!cycleLoaded){std::ifstream in((m.time().globalPath()/"postProcessing/diagnostics83/door_cycle_state.csv").c_str());std::string line;label k=0;while(k<15&&std::getline(in,line)){std::stringstream ss(line);std::string tok;label j=0;while(j<40&&std::getline(ss,tok,','))cycle[k][j++]=std::stod(tok);k++;}cycleLoaded=true;}
 scalar current=m.time().value(),previous=current-dt;
 for(label k=0;k<15;k++){
  scalar lo=1.2*k,hi=1.2*(k+1),w=max(scalar(0),min(current,hi)-max(previous,lo));
  if(w>0)for(label group=0;group<5;group++)for(label j=0;j<8;j++)cycle[k][8*group+j]+=w*v[60+10*group+j];
  if(previous<hi && current>=hi && previous<18){
   if(Pstream::master()){
    fileName dir=m.time().globalPath()/"postProcessing/diagnostics83";mkDir(dir);fileName path=dir/"door_swing_integrals.csv";bool first=!isFile(path);
    std::ofstream out(path.c_str(),first?std::ios::out:std::ios::app);out<<std::setprecision(14);
    if(first){out<<"swing,from_s,to_s";for(label group=0;group<5;group++)for(label j=0;j<8;j++)out<<",g"<<group<<"_integral"<<j;out<<'\n';}
    out<<k+1<<','<<lo<<','<<hi;forAll(cycle[k],j)out<<','<<cycle[k][j];out<<'\n';
   }
  }
 }
 if(m.time().writeTime()&&Pstream::master()){fileName dir=m.time().globalPath()/"postProcessing/diagnostics83";mkDir(dir);std::ofstream out((dir/"door_cycle_state.csv").c_str());out<<std::setprecision(14);forAll(cycle,k){forAll(cycle[k],j){if(j)out<<',';out<<cycle[k][j];}out<<'\n';}}
}
bool emit=TEST_STOP || m.time().value()+1e-9>=next || m.time().writeTime() || mag(m.time().value()-18)<1e-8;
if(emit){next=floor((m.time().value()+1e-9)*8+1)/8;fileName dir=m.time().globalPath()/"postProcessing/diagnostics83";mkDir(dir);
 auto sumflux=fvc::surfaceSum(mag(phi));std::vector<std::pair<scalar,label>> co;forAll(T,i)co.push_back({.5*dt*sumflux()[i]/(rho[i]*m.V()[i]),i});std::partial_sort(co.begin(),co.begin()+min(label(12),T.size()),co.end(),[](auto a,auto b){return a.first>b.first;});
 static bool cf=!isFile(dir/("courant_rank"+Foam::name(Pstream::myProcNo())+".csv"));std::ofstream cr((dir/("courant_rank"+Foam::name(Pstream::myProcNo())+".csv")).c_str(),cf?std::ios::out:std::ios::app);cr<<std::setprecision(14);if(cf)cr<<"time,rank,cell,Co,size_m,speed_ms,x,y,z,doorKm\n";for(label k=0;k<min(label(12),T.size());k++){label i=co[k].second;cr<<m.time().value()<<','<<Pstream::myProcNo()<<','<<i<<','<<co[k].first<<','<<cbrt(m.V()[i])<<','<<mag(U[i])<<','<<m.C()[i].x()<<','<<m.C()[i].y()<<','<<m.C()[i].z()<<','<<(m.foundObject<volScalarField>("doorKm")?m.lookupObject<volScalarField>("doorKm")[i]:0)<<'\n';}cf=false;
 if(Pstream::master()){static bool first=!isFile(dir/"diagnostics.csv");std::ofstream out((dir/"diagnostics.csv").c_str(),first?std::ios::out:std::ios::app);out<<std::setprecision(14);if(first){out<<"time";forAll(v,i)out<<",v"<<i;out<<",theta_rad,door_error_max,err_x,err_y,err_z,Tmax_K,hot_x,hot_y,hot_z,Tmin_K,cold_x,cold_y,cold_z,Umax_ms,fast_x,fast_y,fast_z,deltaT_s,wall_s,heat_integral_J,adv_integral_J,diff_integral_J";for(label j=0;j<40;j++)out<<",opening_cumulative"<<j;out<<",CV_heat_integral_J";for(label g=0;g<5;g++)out<<",tracer_diff_out_integral"<<g;out<<",pressure_integral_J,gravity_integral_J,KE_adv_in_integral_J\n";}out<<m.time().value();forAll(v,i)out<<','<<v[i];out<<','<<theta<<','<<errmax<<','<<errat.x()<<','<<errat.y()<<','<<errat.z()<<','<<tmax<<','<<hot.x()<<','<<hot.y()<<','<<hot.z()<<','<<tmin<<','<<cold.x()<<','<<cold.y()<<','<<cold.z()<<','<<umax<<','<<fast.x()<<','<<fast.y()<<','<<fast.z()<<','<<dt<<','<<(m.time().elapsedClockTime()+wallOffset)<<','<<heatInt<<','<<advInt<<','<<diffInt;forAll(openingCumulative,j)out<<','<<openingCumulative[j];out<<','<<CVheatInt;forAll(tracerDiffCumulative,g)out<<','<<tracerDiffCumulative[g];out<<','<<pressureInt<<','<<gravityInt<<','<<keAdvInt<<'\n';first=false;}
}
if(TEST_STOP && m.time().timeIndex()>=49)const_cast<Time&>(m.time()).stopAt(Time::saWriteNow);
