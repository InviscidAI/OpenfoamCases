// The heat the window wall's inner face receives by radiation (wallLayer's radiation(): the
// room's other surfaces at their area-weighted mean temperature, hr = 5.14 W/m2K), taken out of
// the room's air (x > 0) evenly by volume, so the room as a whole loses it to the wall as through
// EN ISO 6946's Rsi = 0.13. The model gives all the radiator's heat to the air, radiant part
// included, so the air is where that radiation's heat is.
// The power is computed from the walls' state at the start of each step, as the wall uses it,
// and registered as windowRadiationPower (W, positive into the wall) for the budget.

#include "cellSetOption.H"
#include "addToRunTimeSelectionTable.H"
#include "fvMatrices.H"
#include "volFields.H"
#include "uniformDimensionedFields.H"
#include "wallLayer.H"

namespace Foam { namespace fv {

class windowRadiation : public cellSetOption
{
    labelList room_;
    scalar Vroom_;
    autoPtr<uniformDimensionedScalarField> power_;

public:
    TypeName("windowRadiation");

    windowRadiation(const word& name, const word& modelType, const dictionary& dict, const fvMesh& mesh)
    :
        cellSetOption(name, modelType, dict, mesh)
    {
        fieldNames_.resize(1, "h");
        fv::option::resetApplied();
        DynamicList<label> r;
        scalar v = 0;
        forAll(mesh_.C(), i) if (mesh_.C()[i].x() > 0) { r.append(i); v += mesh_.V()[i]; }
        room_.transfer(r);
        Vroom_ = returnReduce(v, sumOp<scalar>());
        power_.reset(new uniformDimensionedScalarField(
            IOobject("windowRadiationPower", mesh.time().timeName(), mesh,
                     IOobject::NO_READ, IOobject::NO_WRITE, IOobject::REGISTER),
            dimensionedScalar(dimPower, 0)));
        Info<< "windowRadiation " << name_ << ": room " << Vroom_ << " m3" << endl;
    }

    virtual void addSup(const volScalarField& rho, fvMatrix<scalar>& eqn, const label fieldi)
    {
        const auto& T = mesh_.lookupObject<volScalarField>("T");
        scalar P = 0;
        forAll(T.boundaryField(), pi)
        {
            if (isA<wallLayerFvPatchScalarField>(T.boundaryField()[pi]))
            {
                P += refCast<const wallLayerFvPatchScalarField>(T.boundaryField()[pi]).radiationPower();
            }
        }
        power_->value() = P;
        DimensionedField<scalar, volMesh> Su
        (
            IOobject(name_ + "Su", mesh_.time().timeName(), mesh_, IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
            mesh_, dimensionedScalar(eqn.dimensions()/dimVolume, Zero)
        );
        const scalar s = -P/Vroom_;
        for (const label i : room_) Su[i] = s;
        eqn += Su;
    }

    virtual void addSup(fvMatrix<scalar>& eqn, const label fieldi)
    {
        addSup(volScalarField::null(), eqn, fieldi);
    }

    virtual bool read(const dictionary& dict) { return cellSetOption::read(dict); }
};

defineTypeNameAndDebug(windowRadiation, 0);
addToRunTimeSelectionTable(option, windowRadiation, dictionary);

}}
