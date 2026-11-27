#include "fvMeshFunctionObject.H"
#include "fvCFD.H"
#include "addToRunTimeSelectionTable.H"
namespace Foam { namespace functionObjects {
class boundedWriteTimeStep86 : public fvMeshFunctionObject
{
 bool clip_,cough_;
public:
 TypeName("boundedWriteTimeStep86");
 boundedWriteTimeStep86(const word& name,const Time& t,const dictionary& d):fvMeshFunctionObject(name,t,d),clip_(d.getOrDefault("clipWindow",false)),cough_(d.getOrDefault("coughWindow",false)){}
 virtual bool execute(){return true;}
 virtual bool write(){return true;}
 virtual bool adjustTimeStep()
 {
  Time& t=const_cast<Time&>(mesh_.time());const scalar now=t.value();
  scalar dt=min(t.deltaTValue(),t.controlDict().getOrDefault<scalar>("maxDeltaT",.02));
  if(mesh_.foundObject<surfaceScalarField>("phi")&&mesh_.foundObject<volScalarField>("rho")){
   const auto& phi=mesh_.lookupObject<surfaceScalarField>("phi");const auto& rho=mesh_.lookupObject<volScalarField>("rho");auto fs=fvc::surfaceSum(mag(phi));
   scalar rate=0;forAll(mesh_.V(),i)rate=max(rate,.5*fs()[i]/(rho[i]*mesh_.V()[i]));reduce(rate,maxOp<scalar>());
   if(rate>SMALL)dt=min(dt,t.controlDict().getOrDefault<scalar>("maxCo",1)/rate);
  }
  if(cough_&&now<.4){
   #include "coughFlow86.H"
   auto qvalue=[&](scalar at){if(at<0||at>=.4)return scalar(0);for(label i=1;i<81;i++)if(at<=qt[i][0])return qt[i-1][1]+(qt[i][1]-qt[i-1][1])*(at-qt[i-1][0])/(qt[i][0]-qt[i-1][0]);return scalar(0);};
   for(label iter=0;iter<6;iter++){scalar q=max(qvalue(now),qvalue(now+dt));for(label i=0;i<81;i++)if(qt[i][0]>=now&&qt[i][0]<=now+dt)q=max(q,qt[i][1]);if(q>SMALL)dt=min(dt,.01*.0004/(1.5206*q));}
  }
  scalar interval=clip_?(now<3-1e-8?.025:.125):t.controlDict().getOrDefault<scalar>("writeInterval",20);
  scalar next=(floor((now-t.startTime().value()+1e-9)/interval)+1)*interval+t.startTime().value();
  scalar remain=next-now;if(remain<1e-8)remain=interval;
  const scalar n=max(scalar(1),ceil(remain/dt-1e-9));dt=min(dt,remain/n);
  scalar end=t.endTime().value()-now;if(end>1e-9)dt=min(dt,end);
  t.setDeltaT(dt,false);return true;
 }
};
defineTypeNameAndDebug(boundedWriteTimeStep86,0);
addToRunTimeSelectionTable(functionObject,boundedWriteTimeStep86,dictionary);
}}
