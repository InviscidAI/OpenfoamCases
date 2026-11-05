#include "fvMeshFunctionObject.H"
#include "addToRunTimeSelectionTable.H"
#include "wallLayer.H"
#include "fvCFD.H"
#include "turbulentFluidThermoModel.H"
#include <fstream>
#include <iomanip>
namespace Foam { namespace functionObjects {
class doorMonitor : public fvMeshFunctionObject {
 autoPtr<std::ofstream> out_; scalarField loY_,hiY_; labelList gapFaces_; labelList gapWhich_;
 public:
 TypeName("doorMonitor");
 doorMonitor(const word& n,const Time& t,const dictionary& d):fvMeshFunctionObject(n,t,d),loY_(mesh_.nCells(),GREAT),hiY_(mesh_.nCells(),-GREAT){
  DynamicList<label> faces,which;
  forAll(mesh_.cells(),i) for(label fi:mesh_.cells()[i])for(label pi:mesh_.faces()[fi]) {loY_[i]=min(loY_[i],mesh_.points()[pi].y());hiY_[i]=max(hiY_[i],mesh_.points()[pi].y());}
  forAll(mesh_.faceCentres(),i){const vector c=mesh_.faceCentres()[i];if(mag(c.x()-4.0175)<1e-8 && mag(mesh_.faceAreas()[i].x())>SMALL){label g=c.y()<.010 ? 0 : (c.y()>1.991 && c.y()<1.994 ? 1:-1);if(g>=0){faces.append(i);which.append(g);}}}
  gapFaces_.transfer(faces);gapWhich_.transfer(which);
 }
 bool execute() override {
  if(!mesh_.foundObject<surfaceScalarField>("phi"))return true;
  if(Pstream::master()&&!out_.valid()) {fileName dir=mesh_.time().globalPath()/"postProcessing"/name()/"0";mkDir(dir);out_.reset(new std::ofstream((dir/"history.csv").c_str()));*out_<<std::setprecision(15)<<"t,dt,clock,mass,intP,internalEnergy,KE,gravityPower,roomK,hallK,refK,Tmin,Tmax,layerStored,wallOut,leafRoomOut,leafHallOut,underToHall_m3s,underToRoom_m3s,underToHall_W,underToRoom_W,headToHall_m3s,headToRoom_m3s,headToHall_W,headToRoom_W,underMaxNutNu,headMaxNutNu,reach20_m,reach50_m,CoMax,CoX,CoY,CoUx,CoUy\n";}
  const auto& T=mesh_.lookupObject<volScalarField>("T");const auto& p=mesh_.lookupObject<volScalarField>("p");const auto& rho=mesh_.lookupObject<volScalarField>("rho");const auto& U=mesh_.lookupObject<volVectorField>("U");const auto& phi=mesh_.lookupObject<surfaceScalarField>("phi");const auto& turb=mesh_.lookupObject<compressible::turbulenceModel>("turbulenceProperties");const auto alpha=turb.alphaEff();const auto nut=turb.nut();const auto mu=turb.mu();
  const scalar cp=1005,R=8314.46261815324/28.96,cv=cp-R;
  scalar mass=gSum(rho.primitiveField()*mesh_.V()),intp=gSum(p.primitiveField()*mesh_.V()),ke=gSum(.5*rho.primitiveField()*magSqr(U.primitiveField())*mesh_.V()),gp=gSum(-9.81*rho.primitiveField()*U.primitiveField().component(vector::Y)*mesh_.V());
  scalar ts[2]={0,0},vs[2]={0,0},maxnu[2]={0,0},reach[2]={0,0},ref=0,refdist=GREAT;const volScalarField* h=mesh_.findObject<volScalarField>("hallAir");
  forAll(T,i){const vector c=mesh_.C()[i];label r=c.x()<4?0:1;ts[r]+=T[i]*mesh_.V()[i];vs[r]+=mesh_.V()[i];scalar dist=mag(c-vector(1.503,1.174,.5));refdist=min(refdist,dist);
   if(c.x()>=4&&c.x()<=4.035){label g=c.y()<.010?0:(c.y()>1.991&&c.y()<1.994?1:-1);if(g>=0)maxnu[g]=max(maxnu[g],nut()[i]*rho[i]/mu()[i]);}
   if(c.x()<4&&h&&(*h)[i]>=.10){for(label l=0;l<2;++l){scalar y=l?.05:.02;if(loY_[i]<=y&&hiY_[i]>y)reach[l]=max(reach[l],4-c.x());}}
  }
  scalar gd=refdist;reduce(gd,minOp<scalar>());forAll(T,i)if(mag(mag(mesh_.C()[i]-vector(1.503,1.174,.5))-gd)<1e-12){ref=T[i];break;}reduce(ref,maxOp<scalar>());
  for(label l=0;l<2;++l){reduce(ts[l],sumOp<scalar>());reduce(vs[l],sumOp<scalar>());reduce(maxnu[l],maxOp<scalar>());reduce(reach[l],maxOp<scalar>());}
  scalar stored=0,wall=0,leaf[2]={0,0};
  forAll(T.boundaryField(),pi){if(mesh_.boundary()[pi].type()!="wall")continue;const auto& tp=T.boundaryField()[pi];if(isA<wallLayerFvPatchScalarField>(tp)){auto& w=refCast<wallLayerFvPatchScalarField>(const_cast<fvPatchScalarField&>(tp));w.sync();stored+=w.stored();}
   scalar q=gSum(-cp*alpha().boundaryField()[pi]*tp.snGrad()*mesh_.magSf().boundaryField()[pi]);const word n=mesh_.boundary()[pi].name();if(!isA<wallLayerFvPatchScalarField>(tp))wall+=q;if(n=="leafRoom")leaf[0]=q;if(n=="leafHall")leaf[1]=q;
  }
  const auto rf=fvc::interpolate(rho);const auto tf=fvc::interpolate(T);scalar flow[8]={0,0,0,0,0,0,0,0};
  forAll(gapFaces_,j){label f=gapFaces_[j],g=gapWhich_[j];scalar ph,rr,tt;
   if(f<mesh_.nInternalFaces()){ph=phi[f];rr=rf()[f];tt=tf()[f];}else{label pi=mesh_.boundaryMesh().whichPatch(f),k=f-mesh_.boundary()[pi].start();ph=phi.boundaryField()[pi][k];rr=rf().boundaryField()[pi][k];tt=tf().boundaryField()[pi][k];if(mesh_.boundary()[pi].type()!="processor" || mesh_.faceAreas()[f].x()<0)continue;}
   ph*=mesh_.faceAreas()[f].x()>0?1:-1;label dir=ph>=0?0:1;flow[4*g+dir]+=mag(ph)/rr;flow[4*g+2+dir]+=mag(ph)*cp*(tt-293.15);
  }
  for(auto& f:flow)reduce(f,sumOp<scalar>());
  const auto ss=fvc::surfaceSum(mag(phi));scalarField co(.5*mesh_.time().deltaTValue()*ss().primitiveField()/(rho.primitiveField()*mesh_.V()));scalar cm=gMax(co);vector cc(Zero),cu(Zero);label rank=labelMax;forAll(co,i)if(co[i]>=cm-1e-14){cc=mesh_.C()[i];cu=U[i];rank=Pstream::myProcNo();break;}reduce(rank,minOp<label>());if(Pstream::myProcNo()!=rank){cc=Zero;cu=Zero;}reduce(cc,sumOp<vector>());reduce(cu,sumOp<vector>());
  if(Pstream::master()){*out_<<mesh_.time().value()<<','<<mesh_.time().deltaTValue()<<','<<mesh_.time().elapsedClockTime()<<','<<mass<<','<<intp<<','<<(cv/R)*intp<<','<<ke<<','<<gp<<','<<ts[0]/vs[0]<<','<<ts[1]/vs[1]<<','<<ref<<','<<gMin(T.primitiveField())<<','<<gMax(T.primitiveField())<<','<<stored<<','<<wall<<','<<leaf[0]<<','<<leaf[1];for(auto f:flow)*out_<<','<<f;for(auto f:maxnu)*out_<<','<<f;for(auto f:reach)*out_<<','<<f;*out_<<','<<cm<<','<<cc.x()<<','<<cc.y()<<','<<cu.x()<<','<<cu.y()<<'\n';out_->flush();}
  else{gMin(T.primitiveField());gMax(T.primitiveField());}
  return true;
 }
 bool write() override {return true;}
};
defineTypeNameAndDebug(doorMonitor,0);addToRunTimeSelectionTable(functionObject,doorMonitor,dictionary);
}}
