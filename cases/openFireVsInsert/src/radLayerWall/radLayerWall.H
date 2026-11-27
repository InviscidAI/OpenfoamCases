/* ceilingVsUnderfloor's wall (written for the solved runs, 29 Oct 2026). A wall whose surface
   balances, per face,

       kc (Tc - Tw) + q + h (Ta - Tw) + qr + hr (Tr - Tw) + g0 (T0 - Tw) = 0,   hr = 4 eps sigma Tr^3

   with kc = kappaEff * deltaCoeffs to the first air cell, qr (absorbed, positive) from the last radiation
   solve, Tr the wall temperature that solve saw (the wall's own emission linearised about it, so the
   surface temperature is implicit in its own radiative loss between fvDOM solves), q = Q/A, h and Ta a
   film to an outside temperature (the glass), and, if nLayers > 0, an implicit 1-D layer behind the
   surface with heat capacity and an adiabatic back (as ceilingVsFloorVent's bedroomLayer: nodes at the
   cell centres of nLayers equal slices, g0 = 2k/dx to the first). T0 is the first node's temperature.
   The layer is advanced from the step's starting state at every evaluation, so outer correctors do not
   advance it twice. The layers, Tr and the qr last seen are written into T, so a run restarts with them. */
#ifndef radLayerWall_H
#define radLayerWall_H
#include "mixedFvPatchFields.H"
#include "temperatureCoupledBase.H"
namespace Foam {
class radLayerWallFvPatchScalarField : public mixedFvPatchScalarField, public temperatureCoupledBase {
    scalar Q_, h_, Ta_, eps_;
    label N_;
    scalar thick_, k_, rhoCp_, Tinit_;
    List<scalarField> layers_, old_;
    label index_;
    scalarField Tr_, qrSeen_;
    bool haveTr_;
public:
    TypeName("radLayerWall");
    radLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    radLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
};
}
#endif
