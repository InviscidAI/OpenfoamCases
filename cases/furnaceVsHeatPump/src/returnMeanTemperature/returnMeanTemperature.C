#include "fvCFD.H"
#include "inletOutletFvPatchFields.H"
#include "addToRunTimeSelectionTable.H"

namespace Foam
{
class returnMeanTemperatureFvPatchScalarField : public inletOutletFvPatchScalarField
{
    scalar held_;
    static scalar readHeld(const dictionary& d)
    {
        ITstream& is=d.lookup("inletValue");
        word kind; is >> kind;
        if (kind == "uniform") { scalar v; is >> v; return v; }
        FatalIOErrorInFunction(d) << "inletValue must be uniform" << exit(FatalIOError);
        return 292.04;
    }
public:
    TypeName("returnMeanTemperature");
    returnMeanTemperatureFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& i)
    : inletOutletFvPatchScalarField(p,i),held_(292.04) { refValue()=held_; }
    returnMeanTemperatureFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& i,const dictionary& d)
    : inletOutletFvPatchScalarField(p,i,d),held_(readHeld(d)) {}
    returnMeanTemperatureFvPatchScalarField(const returnMeanTemperatureFvPatchScalarField& f,const fvPatch& p,const DimensionedField<scalar,volMesh>& i,const fvPatchFieldMapper& m)
    : inletOutletFvPatchScalarField(f,p,i,m),held_(f.held_) {}
    returnMeanTemperatureFvPatchScalarField(const returnMeanTemperatureFvPatchScalarField& f)
    : inletOutletFvPatchScalarField(f),held_(f.held_) {}
    returnMeanTemperatureFvPatchScalarField(const returnMeanTemperatureFvPatchScalarField& f,const DimensionedField<scalar,volMesh>& i)
    : inletOutletFvPatchScalarField(f,i),held_(f.held_) {}
    virtual tmp<fvPatchScalarField> clone() const { return tmp<fvPatchScalarField>(new returnMeanTemperatureFvPatchScalarField(*this)); }
    virtual tmp<fvPatchScalarField> clone(const DimensionedField<scalar,volMesh>& i) const { return tmp<fvPatchScalarField>(new returnMeanTemperatureFvPatchScalarField(*this,i)); }
    virtual void updateCoeffs()
    {
        if (updated()) return;
        // Every rank owns this patch field, including zero-face partitions.
        // Utilities without phi must neither look it up nor call the phi-reading base.
        if (!db().foundObject<surfaceScalarField>(phiName_))
        {
            refValue()=held_;
            mixedFvPatchField<scalar>::updateCoeffs();
            return;
        }
        const auto& ph=patch().lookupPatchField<surfaceScalarField>(phiName_);
        scalar sumFlux=0, sumFluxT=0;
        forAll(ph,i) { const scalar w=max(ph[i],scalar(0)); sumFlux+=w; sumFluxT+=w*(*this)[i]; }
        reduce(sumFlux,sumOp<scalar>());
        reduce(sumFluxT,sumOp<scalar>());
        if (sumFlux>SMALL) held_=sumFluxT/sumFlux;
        refValue()=held_;
        inletOutletFvPatchScalarField::updateCoeffs();
    }
    virtual void write(Ostream& os) const
    {
        fvPatchScalarField::write(os);
        os.writeEntryIfDifferent<word>("phi","phi",phiName_);
        os.writeKeyword("inletValue") << "uniform " << held_ << token::END_STATEMENT << nl;
        fvPatchScalarField::writeValueEntry(os);
    }
};
makePatchTypeField(fvPatchScalarField,returnMeanTemperatureFvPatchScalarField);
}
