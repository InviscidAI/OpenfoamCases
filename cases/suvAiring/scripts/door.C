#include "fvCFD.H"
namespace Foam {
void applyDoor(const fvMesh& mesh,const dictionary& ctx,fvMatrix<vector>& eqn,const volScalarField* rho)
{
 const scalar K=ctx.get<scalar>("K"), clock=mesh.time().value()+ctx.get<scalar>("clockOffset"), fixed=ctx.get<scalar>("fixedAngle");
 scalar theta=0,rate=0;
 if(fixed>=0)theta=fixed*constant::mathematical::pi/180;
 else if(clock>=0 && clock<=18){theta=constant::mathematical::pi/6*(1-cos(2*constant::mathematical::pi*clock/1.2));rate=constant::mathematical::pi/6*(2*constant::mathematical::pi/1.2)*sin(2*constant::mathematical::pi*clock/1.2);}
 auto* km=mesh.getObjectPtr<volScalarField>("doorKm");
 if(!km){km=new volScalarField(IOobject("doorKm",mesh.time().timeName(),mesh,IOobject::NO_READ,IOobject::AUTO_WRITE,IOobject::REGISTER),mesh,dimensionedScalar(dimless/dimTime,Zero));km->store();}
 km->primitiveFieldRef()=0;
 const scalar co=cos(theta),si=sin(theta);
 forAll(mesh.C(),i){const vector c=mesh.C()[i];const scalar h=cbrt(mesh.V()[i]);const scalar dx=c.x()-2.16,dy=c.y()-1.04;
 const vector q(mag(dx*co+dy*si-.52)-.52,mag(dx*si-dy*co-.10)-.10,mag(c.z()-1.08)-.64);
 const vector pos(max(q.x(),scalar(0)),max(q.y(),scalar(0)),max(q.z(),scalar(0)));
 const scalar d=mag(pos)+min(max(q.x(),max(q.y(),q.z())),scalar(0));
 const scalar mask=min(max(.5-d/h,scalar(0)),scalar(1));
 (*km)[i]=K*mask;
 const vector ub=rate*vector(-dy,dx,0);const scalar w=K*mask*mesh.V()[i]*(rho?(*rho)[i]:1);
 eqn.diag()[i]-=w;eqn.source()[i]-=w*ub;
 }
 km->correctBoundaryConditions();
}
}
