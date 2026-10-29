#include "fvMeshFunctionObject.H"
#include "addToRunTimeSelectionTable.H"
#include "wallLayer.H"
#include "fvCFD.H"
#include "turbulentFluidThermoModel.H"
#include <fstream>
#include <iomanip>
namespace Foam { namespace functionObjects {
class bedroomMonitor : public fvMeshFunctionObject {
 autoPtr<std::ofstream> history_,zones_;
 scalarField xmin_,xmax_,ymin_,ymax_;
 void open(){
  if(!Pstream::master() || history_.valid()) return;
  fileName dir=mesh_.time().globalPath()/"postProcessing"/name()/mesh_.time().timeName();mkDir(dir);
  bool oldBudget=isFile(dir/"budget.csv"), oldZones=isFile(dir/"zones.csv");
  history_.reset(new std::ofstream((dir/"budget.csv").c_str(),std::ios::app)); zones_.reset(new std::ofstream((dir/"zones.csv").c_str(),std::ios::app));
  *history_<<std::setprecision(14); *zones_<<std::setprecision(14);
  if(!oldBudget) *history_<<"t,dt,clock,cpu,mass,intP,Esensible,KE,gravityPower,glassPower,floorPower,ceilingPower,innerWallPower,floorStored,ceilingStored,innerWallStored,supplyMassIn,supplyMassOut,supplyVolumeIn,supplyVolumeOut,supplyHIn,supplyHOut,supplyKIn,supplyKOut,returnMassIn,returnMassOut,returnVolumeIn,returnVolumeOut,returnHIn,returnHOut,returnKIn,returnKOut,CoMax,CoX,CoY,CoZ,CoUx,CoUy\n";
  if(!oldZones) *zones_<<"t,ankleK,kneeK,seatedK,standingK,roomK,heatBelow1p8,heatTotal,shareBelow1p8,Tmin,minX,minY,Tmax,maxX,maxY\n";
 }
 public:
 TypeName("bedroomMonitor");
 bedroomMonitor(const word& n,const Time& t,const dictionary& d):fvMeshFunctionObject(n,t,d),xmin_(mesh_.nCells(),GREAT),xmax_(mesh_.nCells(),-GREAT),ymin_(mesh_.nCells(),GREAT),ymax_(mesh_.nCells(),-GREAT),dict_(d){
  forAll(mesh_.cells(),i) for(label fi:mesh_.cells()[i]) for(label pi:mesh_.faces()[fi]) {const point& p=mesh_.points()[pi];xmin_[i]=min(xmin_[i],p.x());xmax_[i]=max(xmax_[i],p.x());ymin_[i]=min(ymin_[i],p.y());ymax_[i]=max(ymax_[i],p.y());}
 }
 bool execute() override {
  if(!mesh_.foundObject<volScalarField>("rho") || !mesh_.foundObject<surfaceScalarField>("phi"))return true;
  open();
  const auto& T=mesh_.lookupObject<volScalarField>("T"); const auto& p=mesh_.lookupObject<volScalarField>("p");const auto& rho=mesh_.lookupObject<volScalarField>("rho");const auto& U=mesh_.lookupObject<volVectorField>("U");const auto& phi=mesh_.lookupObject<surfaceScalarField>("phi");
  const auto& turb=mesh_.lookupObject<compressible::turbulenceModel>("turbulenceProperties");const auto ta=turb.alphaEff();const auto& alpha=ta();
  const scalar cp=1005, R=8314.46261815324/28.96,cv=cp-R;
  scalar M=gSum(rho.primitiveField()*mesh_.V()),P=gSum(p.primitiveField()*mesh_.V()),E=gSum(rho.primitiveField()*cv*(T.primitiveField()-293.15)*mesh_.V()),K=gSum(.5*rho.primitiveField()*magSqr(U.primitiveField())*mesh_.V()),G=gSum(-9.81*rho.primitiveField()*U.primitiveField().component(vector::Y)*mesh_.V());
  scalar heat[4]={0,0,0,0},stored[3]={0,0,0};
  // All ranks visit all patches, including empty patches, for matching reductions.
  forAll(T.boundaryField(),pi){
   const word& n=mesh_.boundary()[pi].name();label group=-1;
   if(n=="glass")group=0;
   else if(n=="floor"||n=="floorSlot")group=1;
   else if(n=="ceiling"||n=="ceilingSlot")group=2;
   else if(n=="innerWall")group=3;
   if(group<0)continue;
   const auto& tp=T.boundaryField()[pi];
   if(group==0 || isA<wallLayerFvPatchScalarField>(tp)){
    scalar q=gSum(-cp*alpha.boundaryField()[pi]*tp.snGrad()*mesh_.magSf().boundaryField()[pi]);heat[group]+=q;
    if(group>0)stored[group-1]+=refCast<const wallLayerFvPatchScalarField>(tp).stored();
   }
  }
  scalar flows[16]={0};
  const word supply=getDict().get<word>("supply");
  for(label l=0;l<2;++l){label pi=mesh_.boundaryMesh().findPatchID(l ? word("undercut"):supply);const auto& ph=phi.boundaryField()[pi];const auto& tb=T.boundaryField()[pi];const auto& rb=rho.boundaryField()[pi];const auto& ub=U.boundaryField()[pi];
   forAll(ph,j){bool in=ph[j]<0;label off=l*8+(in?0:1);scalar m=mag(ph[j]);flows[off]+=m;flows[off+2]+=m/rb[j];flows[off+4]+=m*cp*(tb[j]-293.15);flows[off+6]+=m*.5*magSqr(ub[j]);}
  }
  for(auto& f:flows)reduce(f,sumOp<scalar>());
  const auto tsum=fvc::surfaceSum(mag(phi));scalarField co(.5*mesh_.time().deltaTValue()*tsum().primitiveField()/(rho.primitiveField()*mesh_.V()));scalar maxco=gMax(co);vector cx(Zero),cu(Zero);label own=0;
  forAll(co,i)if(co[i]>=maxco-1e-14){cx=mesh_.C()[i];cu=U[i];own=1;break;}
  label rnk=own ? Pstream::myProcNo():labelMax;reduce(rnk,minOp<label>());if(Pstream::myProcNo()!=rnk){cx=Zero;cu=Zero;}reduce(cx,sumOp<vector>());reduce(cu,sumOp<vector>());
  if(Pstream::master()){
   *history_<<mesh_.time().value()<<','<<mesh_.time().deltaTValue()<<','<<mesh_.time().elapsedClockTime()<<','<<mesh_.time().elapsedCpuTime()<<','<<M<<','<<P<<','<<E<<','<<K<<','<<G;
   for(auto h:heat)*history_<<','<<h;for(auto s:stored)*history_<<','<<s;for(auto f:flows)*history_<<','<<f;
   *history_<<','<<maxco<<','<<cx.x()<<','<<cx.y()<<','<<cx.z()<<','<<cu.x()<<','<<cu.y()<<'\n';history_->flush();
  }
  return true;
 }
 bool write() override {
  if(!mesh_.foundObject<volScalarField>("T"))return true;open();
  const auto& T=mesh_.lookupObject<volScalarField>("T");
  const scalar R=8314.46261815324/28.96,cv=1005-R;scalarField rh(mesh_.nCells(),1);
  if(mesh_.foundObject<volScalarField>("rho"))rh=mesh_.lookupObject<volScalarField>("rho").primitiveField();else if(mesh_.foundObject<volScalarField>("p"))rh=mesh_.lookupObject<volScalarField>("p").primitiveField()/(R*T.primitiveField());
  scalar ht=0,hb=0,ts=0,vol=0,tmin=GREAT,tmax=-GREAT;vector pmin(Zero),pmax(Zero);scalar sum[4]={0},len[4]={0};const scalar yy[4]={.1,.6,1.1,1.7};
  forAll(T,i){scalar V=mesh_.V()[i];scalar H=rh[i]*cv*(T[i]-293.15)*V;ht+=H;hb+=H*max(scalar(0),min(ymax_[i],scalar(1.8))-ymin_[i])/(ymax_[i]-ymin_[i]);ts+=T[i]*V;vol+=V;
   if(T[i]<tmin){tmin=T[i];pmin=mesh_.C()[i];}if(T[i]>tmax){tmax=T[i];pmax=mesh_.C()[i];}
   for(label l=0;l<4;++l)if(ymin_[i]<=yy[l]+1e-10 && ymax_[i]>yy[l]+1e-10){scalar w=max(scalar(0),min(xmax_[i],scalar(3.7))-max(xmin_[i],scalar(1.0)));len[l]+=w;sum[l]+=w*T[i];}
  }
  scalar gmin=tmin,gmax=tmax;reduce(gmin,minOp<scalar>());reduce(gmax,maxOp<scalar>());
  label rmin=tmin==gmin?Pstream::myProcNo():labelMax,rmax=tmax==gmax?Pstream::myProcNo():labelMax;reduce(rmin,minOp<label>());reduce(rmax,minOp<label>());if(Pstream::myProcNo()!=rmin)pmin=Zero;if(Pstream::myProcNo()!=rmax)pmax=Zero;reduce(pmin,sumOp<vector>());reduce(pmax,sumOp<vector>());
  reduce(ht,sumOp<scalar>());reduce(hb,sumOp<scalar>());reduce(ts,sumOp<scalar>());reduce(vol,sumOp<scalar>());for(label l=0;l<4;++l){reduce(sum[l],sumOp<scalar>());reduce(len[l],sumOp<scalar>());}
  if(Pstream::master()){*zones_<<mesh_.time().value();for(label l=0;l<4;++l)*zones_<<','<<sum[l]/max(len[l],VSMALL);*zones_<<','<<ts/vol<<','<<hb<<','<<ht<<','<<(mag(ht)>1e-8?hb/ht:0)<<','<<gmin<<','<<pmin.x()<<','<<pmin.y()<<','<<gmax<<','<<pmax.x()<<','<<pmax.y()<<'\n';zones_->flush();}
  return true;
 }
 const dictionary& getDict() const {return dict_;}
 private: dictionary dict_;
 public: bool read(const dictionary& d) override {fvMeshFunctionObject::read(d);dict_=d;return true;}
};
defineTypeNameAndDebug(bedroomMonitor,0);addToRunTimeSelectionTable(functionObject,bedroomMonitor,dictionary);
}}
