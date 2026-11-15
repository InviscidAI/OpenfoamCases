/* radiatorCabinetTop's radLayerWall (src/radLayerWall there) with its radiation taken out: qr and
   hr are zero, so a face's surface balances

       kc (Tc - Tw) + q + h (Ta - Tw) + g0 (T0 - Tw) = 0

   with kc = kappaEff * deltaCoeffs to the first air cell, q = Q/A, h and Ta a film to an outside
   temperature (the glass), and, if nLayers > 0, an implicit 1-D layer behind the surface with heat
   capacity and an adiabatic back (nodes at the cell centres of nLayers equal slices, g0 = 2k/dx to
   the first; T0 is the first node's temperature). The layer is advanced from the step's starting
   state at every evaluation, so outer correctors do not advance it twice. The layers are written
   into T, so a run restarts with them. The emissivity entry is read and not used.               */
#ifndef storedLayerWall_H
#define storedLayerWall_H
#include "mixedFvPatchFields.H"
#include "temperatureCoupledBase.H"
namespace Foam {
class storedLayerWallFvPatchScalarField : public mixedFvPatchScalarField, public temperatureCoupledBase {
    scalar Q_, h_, Ta_, eps_;
    label N_;
    scalar thick_, k_, rhoCp_, Tinit_;
    List<scalarField> layers_, old_;
    label index_;
    scalarField Tr_, qrSeen_;
    bool haveTr_;
public:
    TypeName("storedLayerWall");
    storedLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    storedLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    storedLayerWallFvPatchScalarField(const storedLayerWallFvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    storedLayerWallFvPatchScalarField(const storedLayerWallFvPatchScalarField&);
    storedLayerWallFvPatchScalarField(const storedLayerWallFvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
};
}
#endif
