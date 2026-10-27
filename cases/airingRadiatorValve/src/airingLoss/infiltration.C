// EN 12831's minimum air change as a heat sink on the room's air: every room cell (x > 0)
// loses n/3600 rho cp (T - Tout) W/m3, outdoor air at Tout coming in through the envelope's
// leaks and the room's own air going out (0.5 /h for a living room, EN 12831's minimum air
// change; with 33.6 m3 at 20 C and 0 C, 113 W). The sink is fixed from the fields at the start of each time step, so the power
// registered for the budget (infiltrationPower, W, positive out) is the one applied.

#include "cellSetOption.H"
#include "addToRunTimeSelectionTable.H"
#include "fvMatrices.H"
#include "volFields.H"
#include "uniformDimensionedFields.H"

namespace Foam { namespace fv {

class infiltration : public cellSetOption
{
    scalar n_, cp_, Tout_;
    label lastIndex_;
    scalarField su_;
    labelList room_;
    autoPtr<uniformDimensionedScalarField> power_;

public:
    TypeName("infiltration");

    infiltration(const word& name, const word& modelType, const dictionary& dict, const fvMesh& mesh)
    :
        cellSetOption(name, modelType, dict, mesh),
        lastIndex_(-1)
    {
        fieldNames_.resize(1, "h");
        fv::option::resetApplied();
        n_ = coeffs_.get<scalar>("airChangesPerHour");
        cp_ = coeffs_.get<scalar>("Cp");
        Tout_ = coeffs_.get<scalar>("Tout");
        DynamicList<label> r;
        forAll(mesh_.C(), i) if (mesh_.C()[i].x() > 0) r.append(i);
        room_.transfer(r);
        su_.setSize(room_.size(), 0);
        power_.reset(new uniformDimensionedScalarField(
            IOobject("infiltrationPower", mesh.time().timeName(), mesh,
                     IOobject::NO_READ, IOobject::NO_WRITE, IOobject::REGISTER),
            dimensionedScalar(dimPower, 0)));
        Info<< "infiltration " << name_ << ": " << n_ << " /h over "
            << returnReduce(room_.size(), sumOp<label>()) << " room cells" << endl;
    }

    virtual void addSup(const volScalarField& rho, fvMatrix<scalar>& eqn, const label fieldi)
    {
        const Time& time = mesh_.time();
        if (time.timeIndex() != lastIndex_)
        {
            lastIndex_ = time.timeIndex();
            const auto& T = mesh_.lookupObject<volScalarField>("T");
            const auto& rhoC = mesh_.lookupObject<volScalarField>("rho");
            const scalarField& V = mesh_.V();
            const scalar a = n_/3600*cp_;
            scalar P = 0;
            forAll(room_, k)
            {
                const label i = room_[k];
                su_[k] = -a*rhoC[i]*(T[i] - Tout_);
                P -= su_[k]*V[i];
            }
            power_->value() = returnReduce(P, sumOp<scalar>());
        }
        DimensionedField<scalar, volMesh> Su
        (
            IOobject(name_ + "Su", time.timeName(), mesh_, IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
            mesh_, dimensionedScalar(eqn.dimensions()/dimVolume, Zero)
        );
        forAll(room_, k) Su[room_[k]] = su_[k];
        eqn += Su;
    }

    virtual void addSup(fvMatrix<scalar>& eqn, const label fieldi)
    {
        addSup(volScalarField::null(), eqn, fieldi);
    }

    virtual bool read(const dictionary& dict) { return cellSetOption::read(dict); }
};

defineTypeNameAndDebug(infiltration, 0);
addToRunTimeSelectionTable(option, infiltration, dictionary);

}}
