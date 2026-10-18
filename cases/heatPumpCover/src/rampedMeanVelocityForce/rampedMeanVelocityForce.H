#ifndef rampedMeanVelocityForce_H
#define rampedMeanVelocityForce_H
#include "meanVelocityForce.H"
namespace Foam { namespace fv {
class rampedMeanVelocityForce : public meanVelocityForce
{
    scalar rampTime_;
public:
    TypeName("rampedMeanVelocityForce");
    rampedMeanVelocityForce(const word& sourceName,const word& modelType,const dictionary& dict,const fvMesh& mesh);
    virtual ~rampedMeanVelocityForce() = default;
    virtual void correct(volVectorField& U);
};
}}
#endif
