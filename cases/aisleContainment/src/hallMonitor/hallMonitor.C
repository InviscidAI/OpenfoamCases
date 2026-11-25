#include <dlfcn.h>
#include "processorPolyPatch.H"
#include "fvCFD.H"
#include "fvMeshFunctionObject.H"
#include "addToRunTimeSelectionTable.H"
#include "PstreamReduceOps.H"
#include <fstream>
#include <chrono>
#include <vector>
#include <iomanip>
#include "upwind.H"
#include "planeExporter.H"
namespace Foam { namespace functionObjects {
class hallMonitor: public fvMeshFunctionObject {
 struct Cut { std::string name; int axis; double pos,lo0,hi0,lo1,hi1,sign; std::vector<label> faces; }; std::vector<Cut> cuts_; PlaneExporter planes_;
 bool contained_; double coldInitialMass_; std::vector<label> coldCells_; std::vector<std::vector<label>> hotCells_;
 scalar next_,interval_,last_; fileName out_; wordList names_; labelList patchIDs_; std::vector<std::string> regions_; std::vector<std::vector<label>> cells_; std::chrono::steady_clock::time_point start_;
public:
 TypeName("hallMonitor");
 hallMonitor(const word& name,const Time& t,const dictionary& dict):fvMeshFunctionObject(name,t,dict),planes_(mesh_,dict.getOrDefault<bool>("planes",false)),contained_(dict.getOrDefault<bool>("contained",false)),coldInitialMass_(dict.getOrDefault<scalar>("coldInitialMass",0)),hotCells_(3),next_(t.value()>0 ? t.value()+dict.getOrDefault<scalar>("interval",.25) : t.value()),interval_(dict.getOrDefault<scalar>("interval",.25)),last_(-GREAT),out_(t.globalPath()/"monitors"),start_(std::chrono::steady_clock::now()) {
  auto& bm=mesh_.boundaryMesh(); DynamicList<word> ns;
  forAll(bm,i) if(!isA<processorPolyPatch>(bm[i]) && bm[i].name()!="walls" && !bm[i].name().starts_with("panel_") && !bm[i].name().starts_with("gap_end_") && !bm[i].name().starts_with("end_")) ns.append(bm[i].name());
  names_=wordList(ns); patchIDs_.setSize(names_.size());forAll(names_,i) patchIDs_[i]=bm.findPatchID(names_[i]);
  for(int k=0;k<4;k++){regions_.push_back("cold_"+std::to_string(k));regions_.push_back("cold_upper_"+std::to_string(k));}
  for(int k=0;k<3;k++)regions_.push_back("hot_"+std::to_string(k));
  regions_.push_back("end_south");regions_.push_back("end_south_upper");regions_.push_back("end_north");regions_.push_back("end_north_upper");regions_.push_back("overhead");regions_.push_back("hall");
  cells_.resize(regions_.size());auto& C=mesh_.C();
  forAll(C,i){const auto& c=C[i];for(int k=0;k<4;k++)if(c.x()>4.8*k&&c.x()<4.8*k+1.2&&c.z()<2.2){cells_[2*k].push_back(i);if(c.z()>1.7)cells_[2*k+1].push_back(i);}
   for(int k=0;k<3;k++)if(c.x()>4.8*k+2.4&&c.x()<4.8*k+3.6&&c.y()>2.1&&c.y()<14.1&&c.z()<2.2)cells_[8+k].push_back(i);
   if(c.y()>.9&&c.y()<2.1&&c.z()<2.2){cells_[11].push_back(i);if(c.z()>1.7)cells_[12].push_back(i);}
   if(c.y()>14.1&&c.y()<15.3&&c.z()<2.2){cells_[13].push_back(i);if(c.z()>1.7)cells_[14].push_back(i);}
   if(c.z()>2.2)cells_[15].push_back(i);cells_[16].push_back(i);
  }
  forAll(C,i){const auto& c=C[i];int hot=-1;for(int k=0;k<3;k++)if(c.x()>4.8*k+2.4&&c.x()<4.8*k+3.6&&c.y()>2.1&&c.y()<14.1)hot=k;if(hot>=0)hotCells_[hot].push_back(i);else coldCells_.push_back(i);}
  for(int k=0;k<3;k++){
   for(int r=0;r<2;r++){
    double back=4.8*k+(r?3.6:2.4),front=4.8*k+(r?4.8:1.2),sign=r?-1:1;std::string row=std::string(r?"R":"L")+"0"+std::to_string(k);
    cuts_.push_back({row+"_top",0,back,2.1,14.1,2.2,3.2,sign,{}});
   }
   for(int e=0;e<2;e++)for(int z=0;z<2;z++)cuts_.push_back({"hot_"+std::to_string(k)+(e?"_north":"_south")+(z?"_upper":"_lower"),1,e?14.1:2.1,4.8*k+2.4,4.8*k+3.6,z?2.2:0,z?3.2:2.2,e?1.:-1.,{}});
  }
  const auto& fc=mesh_.faceCentres();const auto& fa=mesh_.faceAreas();
  for(auto& cut:cuts_)forAll(fc,f){int a=cut.axis==0?1:0,b=2;const auto& c=fc[f];if(mag(c[cut.axis]-cut.pos)<1e-7&&c[a]>cut.lo0&&c[a]<cut.hi0&&c[b]>cut.lo1&&c[b]<cut.hi1&&fa[f][cut.axis]>0)cut.faces.push_back(f);}
  if(Pstream::master()){mkDir(out_);std::ofstream p((out_/"ports.csv").c_str(),std::ios::app);if(p.tellp()==0){p<<"time_s,wall_s";forAll(names_,i)for(const auto& v:{"net_kg_s","out_kg_s","in_kg_s","T_K","Hout_W","Hin_W","out_m3_s","in_m3_s","p_Pa"})p<<","<<names_[i]<<":"<<v;p<<"\n";}
   std::ofstream r((out_/"regions.csv").c_str(),std::ios::app);if(r.tellp()==0){r<<"time_s,wall_s,mass_kg,internalEnergy_J,Tmin_K,Tmin_x,Tmin_y,Tmin_z,Tmax_K,Tmax_x,Tmax_y,Tmax_z,maxCo,maxCo_x,maxCo_y,maxCo_z";for(const auto& n:regions_)r<<","<<n<<":T_K,"<<n<<":p_Pa";r<<",cold_side:mass_kg,cold_side:p_rgh_Pa,hot_0:p_rgh_Pa,hot_1:p_rgh_Pa,hot_2:p_rgh_Pa,cold_side:mass_drift_fraction\n";}
   std::ofstream c((out_/"cuts.csv").c_str(),std::ios::app);if(c.tellp()==0){c<<"time_s";for(const auto& cut:cuts_)for(const auto& v:{"plus_kg_s","minus_kg_s","Hplus_W","Hminus_W","plus_m3_s","minus_m3_s","p_Pa"})c<<","<<cut.name<<":"<<v;c<<"\n";}
  }
 }
 bool write() override{return true;}
 bool execute() override {
  planes_.execute();
  {using Marker=void(*)(double);static Marker mark=reinterpret_cast<Marker>(dlsym(RTLD_DEFAULT,"port_profile_step"));if(mark)mark(mesh_.time().value());}
  if(mesh_.time().value()>=1 && mesh_.foundObject<volScalarField>("T")){scalar allMin=gMin(mesh_.lookupObject<volScalarField>("T").primitiveField());if(allMin<293.0)Info<<"HALL_TEMPERATURE_VIOLATION t="<<mesh_.time().value()<<" Tmin="<<allMin<<endl;}
  scalar t=mesh_.time().value(); if(t+SMALL<next_||t<=last_+SMALL)return true;last_=t;while(next_<=t+SMALL)next_+=interval_;
  const auto& T=mesh_.lookupObject<volScalarField>("T");const auto& p=mesh_.lookupObject<volScalarField>("p");const auto& rho=mesh_.lookupObject<volScalarField>("rho");const auto& phi=mesh_.lookupObject<surfaceScalarField>("phi");auto& C=mesh_.C();auto& V=mesh_.V();
  const auto& prgh=mesh_.lookupObject<volScalarField>("p_rgh");
  scalarField cm(9,Zero);for(label i:coldCells_){cm[0]+=rho[i]*V[i];cm[1]+=prgh[i]*V[i];cm[2]+=V[i];}
  for(int k=0;k<3;k++)for(label i:hotCells_[k]){cm[3+2*k]+=prgh[i]*V[i];cm[4+2*k]+=V[i];}reduce(cm,sumOp<scalarField>());
  scalar drift=cm[0]/(coldInitialMass_+VSMALL)-1;
  if(contained_ && mag(drift)>.01){FatalErrorInFunction<<"SEALED_COLD_MASS_STOP t="<<t<<" drift="<<drift<<exit(FatalError);}
  scalarField data(names_.size()*10,Zero);
  forAll(names_,a){label b=patchIDs_[a];auto& fl=phi.boundaryField()[b];auto& tp=T.boundaryField()[b];auto& rp=rho.boundaryField()[b];auto& pp=p.boundaryField()[b];auto& ar=mesh_.magSf().boundaryField()[b];
   forAll(fl,f){scalar po=max(fl[f],scalar(0)),ni=max(-fl[f],scalar(0)),ab=po+ni;data[10*a]+=fl[f];data[10*a+1]+=po;data[10*a+2]+=ni;data[10*a+3]+=ab*tp[f];data[10*a+4]+=po*1005*(tp[f]-293.15);data[10*a+5]+=ni*1005*(tp[f]-293.15);data[10*a+6]+=po/rp[f];data[10*a+7]+=ni/rp[f];data[10*a+8]+=pp[f]*ar[f];data[10*a+9]+=ar[f];}
  }
  reduce(data,sumOp<scalarField>());
  const auto tf=upwind<scalar>(mesh_,phi).interpolate(T);const auto rhof=fvc::interpolate(rho);const auto pf=fvc::interpolate(p);
  auto val=[&](const surfaceScalarField& f,label i)->scalar{if(i<mesh_.nInternalFaces())return f[i];label patch=mesh_.boundaryMesh().whichPatch(i);return f.boundaryField()[patch][i-mesh_.boundaryMesh()[patch].start()];};
  scalarField cd(cuts_.size()*8,Zero);
  for(label a=0;a<label(cuts_.size());a++)for(label f:cuts_[a].faces){scalar fl=val(phi,f)*cuts_[a].sign,po=max(fl,scalar(0)),ni=max(-fl,scalar(0)),temp=val(tf(),f),dens=val(rhof(),f),area=mag(mesh_.faceAreas()[f]);cd[8*a]+=po;cd[8*a+1]+=ni;cd[8*a+2]+=po*1005*(temp-293.15);cd[8*a+3]+=ni*1005*(temp-293.15);cd[8*a+4]+=po/dens;cd[8*a+5]+=ni/dens;cd[8*a+6]+=val(pf(),f)*area;cd[8*a+7]+=area;}
  reduce(cd,sumOp<scalarField>());

  scalarField reg(regions_.size()*3+2,Zero);
  for(label a=0;a<label(cells_.size());a++)for(label i:cells_[a]){reg[3*a]+=T[i]*V[i];reg[3*a+1]+=p[i]*V[i];reg[3*a+2]+=V[i];}
  forAll(V,i){reg[reg.size()-2]+=rho[i]*V[i];reg[reg.size()-1]+=(1005/287.05-1)*p[i]*V[i];}
  reduce(reg,sumOp<scalarField>());
  scalar mn=GREAT,mx=-GREAT,comax=-GREAT;label imin=-1,imax=-1,ico=-1;auto sumPhi=fvc::surfaceSum(mag(phi));
  forAll(T,i){if(T[i]<mn){mn=T[i];imin=i;}if(T[i]>mx){mx=T[i];imax=i;}scalar co=.5*mesh_.time().deltaTValue()*sumPhi()[i]/(rho[i]*V[i]);if(co>comax){comax=co;ico=i;}}
  scalar gmn=mn,gmx=mx,gco=comax;reduce(gmn,minOp<scalar>());reduce(gmx,maxOp<scalar>());reduce(gco,maxOp<scalar>());
  scalarField loc(12,Zero);if(mn==gmn&&imin>=0){for(int k=0;k<3;k++)loc[k]=C[imin][k];loc[3]=1;}if(mx==gmx&&imax>=0){for(int k=0;k<3;k++)loc[4+k]=C[imax][k];loc[7]=1;}if(comax==gco&&ico>=0){for(int k=0;k<3;k++)loc[8+k]=C[ico][k];loc[11]=1;}reduce(loc,sumOp<scalarField>());
  if(Pstream::master()){
   scalar wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-start_).count();std::ofstream pf((out_/"ports.csv").c_str(),std::ios::app);pf<<std::setprecision(12)<<t<<","<<wall;
   forAll(names_,a){for(int k=0;k<9;k++){scalar v=data[10*a+k];if(k==3)v/=(data[10*a+1]+data[10*a+2]+VSMALL);if(k==8)v/=(data[10*a+9]+VSMALL);pf<<","<<v;}}pf<<"\n";
   std::ofstream rf((out_/"regions.csv").c_str(),std::ios::app);rf<<std::setprecision(12)<<t<<","<<wall<<","<<reg[reg.size()-2]<<","<<reg[reg.size()-1]<<","<<gmn;
   for(int k=0;k<3;k++)rf<<","<<loc[k]/(loc[3]+VSMALL);rf<<","<<gmx;for(int k=0;k<3;k++)rf<<","<<loc[4+k]/(loc[7]+VSMALL);rf<<","<<gco;for(int k=0;k<3;k++)rf<<","<<loc[8+k]/(loc[11]+VSMALL);
   for(label a=0;a<label(regions_.size());a++)rf<<","<<reg[3*a]/(reg[3*a+2]+VSMALL)<<","<<reg[3*a+1]/(reg[3*a+2]+VSMALL);rf<<","<<cm[0]<<","<<cm[1]/cm[2];for(int k=0;k<3;k++)rf<<","<<cm[3+2*k]/cm[4+2*k];rf<<","<<drift;rf<<"\n";
   std::ofstream cf((out_/"cuts.csv").c_str(),std::ios::app);cf<<std::setprecision(12)<<t;for(label a=0;a<label(cuts_.size());a++)for(int k=0;k<7;k++)cf<<","<<(k==6?cd[8*a+k]/(cd[8*a+7]+VSMALL):cd[8*a+k]);cf<<"\n";
   scalar heat=0,rise=0;label nserver=0;forAll(names_,a)if(names_[a].ends_with("_exhaust")){word in=names_[a].substr(0,names_[a].size()-8)+"_intake";label j=findIndex(names_,in);if(j>=0){scalar rt=data[10*a+3]/(data[10*a+1]+data[10*a+2]+VSMALL)-data[10*j+3]/(data[10*j+1]+data[10*j+2]+VSMALL);rise+=rt;heat+=1005*data[10*a+2]*rt;nserver++;}}
   Info<<"HALL_MONITOR t="<<t<<" heat_W="<<heat<<" meanRise_K="<<rise/max(nserver,label(1))<<" Tmin="<<gmn<<" Tmax="<<gmx<<" Co="<<gco<<endl;
  }
  return true;
 }
};
defineTypeNameAndDebug(hallMonitor,0);
addToRunTimeSelectionTable(functionObject,hallMonitor,dictionary);
}}
