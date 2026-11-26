/* closedRegister's storedLayerWall (radiatorCabinetTop's radLayerWall with its radiation taken
   out: qr and hr are zero) with a film on the layer's back, registered under the type name the
   solved runs' dictionaries use, radLayerWall. A face's surface balances

       kc (Tc - Tw) + q + h (Ta - Tw) + g0 (T0 - Tw) = 0

   with kc = kappaEff * deltaCoeffs to the first air cell, q = Q/A, h and Ta a film to an outside
   temperature on the room side (the window), and, if nLayers > 0, an implicit 1-D layer behind the
   surface with heat capacity (nodes at the cell centres of nLayers equal slices, g0 = 2k/dx to the
   first; T0 is the first node's temperature). Its back is adiabatic unless h_back > 0: then the
   last node loses gb (Tback - TN) with gb = 1/(dx/(2k) + 1/h_back), half a slice of the layer in
   series with the outer film, so that the steady flux is (T - Tback)/(thickness/k + 1/h_back).
   The layer is advanced from the step's starting state at every evaluation, so outer correctors
   do not advance it twice. The layers are written into T, so a run restarts with them. The
   emissivity entry is read and not used.                                                     */
#ifndef radLayerWall85_H
#define radLayerWall85_H
#include "mixedFvPatchFields.H"
#include "temperatureCoupledBase.H"
namespace Foam {
class radLayerWall85FvPatchScalarField : public mixedFvPatchScalarField, public temperatureCoupledBase {
    scalar Q_, h_, Ta_, eps_;
    label N_;
    scalar thick_, k_, rhoCp_, Tinit_, hBack_, Tback_;
    List<scalarField> layers_, old_;
    label index_;
    scalarField Tr_, qrSeen_;
    bool haveTr_;
public:
    TypeName("radLayerWall");
    radLayerWall85FvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    radLayerWall85FvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    radLayerWall85FvPatchScalarField(const radLayerWall85FvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    radLayerWall85FvPatchScalarField(const radLayerWall85FvPatchScalarField&);
    radLayerWall85FvPatchScalarField(const radLayerWall85FvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
};
}
#endif
