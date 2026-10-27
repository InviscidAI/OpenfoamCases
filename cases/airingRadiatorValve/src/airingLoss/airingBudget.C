#include "fvMeshFunctionObject.H"
#include "addToRunTimeSelectionTable.H"
#include "wallLayer.H"
#include "volFields.H"
#include "surfaceFields.H"
#include "surfaceInterpolate.H"
#include "fvcFlux.H"
#include "fvcSnGrad.H"
#include "processorPolyPatch.H"
#include "turbulentFluidThermoModel.H"
#include "uniformDimensionedFields.H"
#include <fstream>
#include <iomanip>
namespace Foam { namespace functionObjects {
class airingBudget : public fvMeshFunctionObject {
 std::ofstream out_; scalar watts_;
public:
 TypeName("airingBudget");
 airingBudget(const word& n,const Time& t,const dictionary& d):fvMeshFunctionObject(n,t,d),watts_(d.get<scalar>("watts")) {
 if(Pstream::master()) { fileName dir=t.globalPath()/"postProcessing"/n; mkDir(dir); out_.open((dir/("history_"+t.timeName()+".csv")).c_str()); out_ << "t,dt,mass,meanT,meanS,intP,Eair,Ekin,Epot,inflow,outflow,Hout,diffOut,Qrad,Ewall,Qback,Qfloor,Qceiling,Qinner,QsideMinus,QsidePlus,QwindowWall,Qglass,Qoutside,Qinf,QwinRad\n"; out_<<std::setprecision(14); }
 }
 virtual bool read(const dictionary& d) { fvMeshFunctionObject::read(d); watts_=d.get<scalar>("watts"); return true; }
 virtual bool execute() {
 const auto& T=mesh_.lookupObject<volScalarField>("T");
 const auto& rho=mesh_.lookupObject<volScalarField>("rho");
 const auto& p=mesh_.lookupObject<volScalarField>("p");
 const auto& s=mesh_.lookupObject<volScalarField>("s");
 const auto& U=mesh_.lookupObject<volVectorField>("U");
 const auto& phi=mesh_.lookupObject<surfaceScalarField>("phi");
 const auto& turb=mesh_.lookupObject<compressible::turbulenceModel>(turbulenceModel::propertiesName);
 const scalar R=8314.46261815324/28.96, cp=1005, cv=cp-R, To=273.15;
 scalar m=0,mt=0,ms=0,ip=0,ek=0,ep=0;
 forAll(mesh_.C(),i) { if(mesh_.C()[i].x()>0) { scalar dm=rho[i]*mesh_.V()[i]; m+=dm; mt+=dm*T[i]; ms+=dm*s[i]; ip+=p[i]*mesh_.V()[i]; ek+=.5*dm*magSqr(U[i]); ep+=dm*9.81*mesh_.C()[i].y(); } }
 reduce(m,sumOp<scalar>()); reduce(mt,sumOp<scalar>()); reduce(ms,sumOp<scalar>()); reduce(ip,sumOp<scalar>()); reduce(ek,sumOp<scalar>()); reduce(ep,sumOp<scalar>());
 scalar inflow=0,outflow=0,hout=0,diff=0;
 auto ft=fvc::flux(phi,T,"div(phi,h)"); auto ta=fvc::interpolate(turb.alphaEff()); auto tg=fvc::snGrad(T);
 const label zi=mesh_.faceZones().findZoneID("opening");
 if(zi>=0) { const auto& z=mesh_.faceZones()[zi];
 forAll(z,j) { label f=z[j];
  scalar flux=0,fluxT=0,sign=0,diffFlux=0;
  if(f<mesh_.nInternalFaces()) {
   sign=mesh_.Sf()[f].x()<0 ? 1 : -1; flux=phi[f]; fluxT=ft()[f];
   label own=mesh_.faceOwner()[f], nei=mesh_.faceNeighbour()[f];
   diffFlux=-ta()[f]*cp*(T[nei]-T[own])*mesh_.deltaCoeffs()[f]*mesh_.magSf()[f];
  } else {
   label pi=mesh_.boundaryMesh().whichPatch(f); const auto& pp=mesh_.boundaryMesh()[pi];
   if(!isA<processorPolyPatch>(pp) || !refCast<const processorPolyPatch>(pp).owner()) continue;
   label k=f-pp.start(); sign=mesh_.Sf().boundaryField()[pi][k].x()<0 ? 1 : -1;
   flux=phi.boundaryField()[pi][k]; fluxT=ft().boundaryField()[pi][k];
   diffFlux=-ta().boundaryField()[pi][k]*cp*tg().boundaryField()[pi][k]*mesh_.magSf().boundaryField()[pi][k];
  }
  scalar fl=flux*sign;
  if(fl<0) inflow-=fl; else outflow+=fl;
  hout+=sign*(cp*fluxT-cv*To*flux); diff+=sign*diffFlux;
 }

 }
 reduce(inflow,sumOp<scalar>()); reduce(outflow,sumOp<scalar>()); reduce(hout,sumOp<scalar>()); reduce(diff,sumOp<scalar>());
 scalar ew=0,qb=0,qo=0; scalar q[6]={0,0,0,0,0,0}; scalar qglass=0;
 forAll(T.boundaryField(),pi) {
 const auto& tp=T.boundaryField()[pi];
 if(isA<wallLayerFvPatchScalarField>(tp)) {
  const auto& w=refCast<const wallLayerFvPatchScalarField>(tp);
  ew+=w.stored(); qb+=w.backHeat(); qo+=w.outsideHeat();
  scalarField flux(w.kappa(w)*w.snGrad()*w.patch().magSf());
  forAll(flux,i) { const auto& c=w.patch().Cf()[i]; label k=5;
   if(mag(c.y())<1e-7) k=0; else if(mag(c.y()-2.4)<1e-7) k=1; else if(mag(c.x()-4)<1e-7) k=2; else if(mag(c.z()+1.75)<1e-7) k=3; else if(mag(c.z()-1.75)<1e-7) k=4;
   q[k]+=flux[i];
  }
 }
 if(tp.patch().name()=="glassRoom") { auto a=turb.alphaEff(pi); qglass-=gSum(a()*cp*tp.snGrad()*tp.patch().magSf()); }
 }
 for(label k=0;k<6;++k) reduce(q[k],sumOp<scalar>());
 // the radiator's heat over this step: the trvRadiator option's, else the fixed watts
 scalar qrad=watts_; if(mesh_.foundObject<uniformDimensionedScalarField>("radiatorPower")) qrad=mesh_.lookupObject<uniformDimensionedScalarField>("radiatorPower").value();
 // the leaks' heat over this step (the infiltration option's), and the window wall's to outdoors
 scalar qinf=0; if(mesh_.foundObject<uniformDimensionedScalarField>("infiltrationPower")) qinf=mesh_.lookupObject<uniformDimensionedScalarField>("infiltrationPower").value();
 scalar qwr=0; if(mesh_.foundObject<uniformDimensionedScalarField>("windowRadiationPower")) qwr=mesh_.lookupObject<uniformDimensionedScalarField>("windowRadiationPower").value();
 if(Pstream::master()) { out_<<mesh_.time().value()<<','<<mesh_.time().deltaTValue()<<','<<m<<','<<mt/m<<','<<ms/m<<','<<ip<<','<<(cv/R*ip-cv*To*m)<<','<<ek<<','<<ep<<','<<inflow<<','<<outflow<<','<<hout<<','<<diff<<','<<qrad<<','<<ew<<','<<qb; for(label k=0;k<6;++k) out_<<','<<q[k]; out_<<','<<qglass<<','<<qo<<','<<qinf<<','<<qwr<<'\n'; out_.flush(); }
 return true;
 }
 virtual bool write() { return true; }
};
defineTypeNameAndDebug(airingBudget,0);
addToRunTimeSelectionTable(functionObject,airingBudget,dictionary);
}}
