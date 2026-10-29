
#ifndef wallLayer_H
#define wallLayer_H
#include "mixedFvPatchFields.H"
#include "temperatureCoupledBase.H"
namespace Foam {
class wallLayerFvPatchScalarField : public mixedFvPatchScalarField, public temperatureCoupledBase {
    List<scalarField> layers_, old_;
    label index_;
    void init();
public:
    TypeName("bedroomLayer");
    wallLayerFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    wallLayerFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField&);
    wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
    const List<scalarField>& layers() const { return layers_; }
    scalar stored() const;
    void sync();
};
}
#endif
