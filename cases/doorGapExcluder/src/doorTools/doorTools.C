#include "fvCFD.H"
#include "wallLayer.H"
#include "prghTotalPressureFvPatchScalarField.H"
#include <fstream>
#include <iomanip>
using namespace Foam;
int main(int argc,char *argv[]){
 argList::addBoolOption("prepare","Initialize isothermal perfect-gas hydrostatics; no time integration");
 argList::addBoolOption("layerTest","Serial fixed-air 60 s layer test");
 #include "setRootCase.H"
 #include "createTime.H"
 #include "createMesh.H"
 const scalar R=8314.46261815324/28.96,T0=293.15;
 volScalarField T(IOobject("T",runTime.timeName(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
 if(args.found("prepare")){
  volScalarField p(IOobject("p",runTime.timeName(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh),pr(IOobject("p_rgh",runTime.timeName(),mesh,IOobject::MUST_READ,IOobject::AUTO_WRITE),mesh);
  forAll(p,i){scalar y=mesh.C()[i].y(),ti=mesh.C()[i].x()<4 ? 293.15:283.15;T[i]=ti;p[i]=1e5*Foam::exp(-9.81*(y-1.174)/(R*ti));pr[i]=p[i]+p[i]/(R*ti)*9.81*y;}
  forAll(p.boundaryField(),pi){auto& pb=p.boundaryFieldRef()[pi];auto& pp=pr.boundaryFieldRef()[pi];forAll(pb,i){scalar y=mesh.boundary()[pi].Cf()[i].y(),ti=mesh.boundary()[pi].Cf()[i].x()<4 ? 293.15:283.15;pb[i]=1e5*Foam::exp(-9.81*(y-1.174)/(R*ti));pp[i]=pb[i]+pb[i]/(R*ti)*9.81*y;}}
  T.write();p.write();pr.write();
  std::cout<<std::setprecision(16)<<"INITIAL_MASS "<<gSum(p.primitiveField()/(R*T.primitiveField())*mesh.V())<<" INITIAL_INTP "<<gSum(p.primitiveField()*mesh.V())<<std::endl;
  Info<<"Initialization only; no solver run."<<endl;return 0;
 }
 if(args.found("layerTest")){
  if(Pstream::parRun())FatalErrorInFunction<<"Serial only"<<exit(FatalError);
  volScalarField kapp(IOobject("testKappa",runTime.timeName(),mesh,IOobject::NO_READ,IOobject::NO_WRITE),mesh,dimensionedScalar("k",dimPower/dimLength/dimTemperature,1005*1.82e-5/.71));
  const scalar initial=refCast<const wallLayerFvPatchScalarField>(T.boundaryField()[mesh.boundaryMesh().findPatchID("testFloor")]).initialTemperature();
  T.primitiveFieldRef()=initial+20;
  const word names[2]={"testFloor","testCeiling"};scalar Q[2]={0,0};scalar dt=.05;
  for(label step=1;step<=1200;++step){runTime.setDeltaT(dt);runTime.setTime(step*dt,step);
   for(label l=0;l<2;++l){label pi=mesh.boundaryMesh().findPatchID(names[l]);auto& tp=refCast<wallLayerFvPatchScalarField>(T.boundaryFieldRef()[pi]);tp.setUpdated(false);tp.evaluate();scalar q=gSum(-kapp.boundaryField()[pi]*tp.snGrad()*mesh.magSf().boundaryField()[pi]);Q[l]+=q*dt;}
  }
  bool pass=true;Info<<"Fixed air "<<initial+20<<" K; solid initially "<<initial<<" K; adiabatic back; 24 solid cells; dt .05 s; 60 s.\n";
  for(label l=0;l<2;++l){label pi=mesh.boundaryMesh().findPatchID(names[l]);const auto& tp=refCast<const wallLayerFvPatchScalarField>(T.boundaryField()[pi]);scalar A=gSum(mesh.magSf().boundaryField()[pi]),S=tp.stored(),rise=gSum((tp-initial)*mesh.magSf().boundaryField()[pi])/A;scalar k=l?.1587:.1060,rho=l?640.7:656.8,cp=l?1130:1884;scalar analytic=2*(Q[l]/(A*60))*Foam::sqrt(60/constant::mathematical::pi)/Foam::sqrt(k*rho*cp);scalar conservation=mag(S-Q[l])/max(mag(Q[l]),SMALL),err=mag(rise-analytic)/analytic;bool ok=conservation<.01 && err<.15 && mag(A-1)<1e-8;pass=pass&&ok;
   Info<<names[l]<<" area="<<A<<" m2 heat_from_air="<<Q[l]<<" J stored="<<S<<" J relative_energy_error="<<conservation<<" surface_rise="<<rise<<" K semi_infinite_mean_flux_prediction="<<analytic<<" K relative_surface_error="<<err<<" "<<(ok?"PASS":"FAIL")<<nl;
  }
  Info<<(pass?"LAYER_TEST_PASS":"LAYER_TEST_FAIL")<<endl;return pass?0:2;
 }
 return 1;
}
