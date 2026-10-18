#include "rampedMeanVelocityForce.H"
#include "addToRunTimeSelectionTable.H"
namespace Foam { namespace fv {
defineTypeNameAndDebug(rampedMeanVelocityForce,0);
addToRunTimeSelectionTable(option,rampedMeanVelocityForce,dictionary);
rampedMeanVelocityForce::rampedMeanVelocityForce(const word& n,const word& t,const dictionary& d,const fvMesh& m)
: meanVelocityForce(n,t,d,m), rampTime_(coeffs_.getOrDefault<scalar>("rampTime",2.0)) {}
void rampedMeanVelocityForce::correct(volVectorField& U)
{
    const vector full=Ubar_;
    const scalar f=min(max(mesh_.time().value()/max(rampTime_,SMALL),scalar(0)),scalar(1));
    Ubar_=f*full;
    meanVelocityForce::correct(U);
    Ubar_=full;
}
}}
