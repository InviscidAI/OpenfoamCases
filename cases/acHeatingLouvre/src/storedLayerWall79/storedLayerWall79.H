/* radiatorCabinetTop's radLayerWall (src/radLayerWall there) with its radiation taken out, as
   closedRegister's storedLayerWall: qr and hr are zero, so a face's surface balances

       kc (Tc - Tw) + q + h (Ta - Tw) + g0 (T0 - Tw) = 0

   with kc = kappaEff * deltaCoeffs to the first air cell, q = Q/A, h and Ta a film to an outside
   temperature (h = 0 here: none), and, if nLayers > 0, an implicit 1-D layer behind the surface with heat
   capacity and an adiabatic back (nodes at the cell centres of nLayers equal slices, g0 = 2k/dx to
   the first; T0 is the first node's temperature). The layer is advanced from the step's starting
   state at every evaluation, so outer correctors do not advance it twice. The layers are written
   into T, so a run restarts with them. The emissivity entry is read and not used.
   storedEnergyPerArea() is a read-only accessor for the monitor (scripts/monitor.C): the heat each
   face's layer holds above Tinit, J/m2. It changes nothing in the condition.                   */
#ifndef storedLayerWall79_H
#define storedLayerWall79_H
#include "mixedFvPatchFields.H"
#include "temperatureCoupledBase.H"
namespace Foam {
class storedLayerWall79FvPatchScalarField : public mixedFvPatchScalarField, public temperatureCoupledBase {
    scalar Q_, h_, Ta_, eps_;
    label N_;
    scalar thick_, k_, rhoCp_, Tinit_;
    List<scalarField> layers_, old_;
    label index_;
    scalarField Tr_, qrSeen_;
    bool haveTr_;
public:
    TypeName("storedLayerWall79");
    storedLayerWall79FvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    storedLayerWall79FvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    storedLayerWall79FvPatchScalarField(const storedLayerWall79FvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    storedLayerWall79FvPatchScalarField(const storedLayerWall79FvPatchScalarField&);
    storedLayerWall79FvPatchScalarField(const storedLayerWall79FvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    scalarField storedEnergyPerArea() const {
        scalarField e(patch().size(),0);
        forAll(layers_,j) e += (rhoCp_*thick_/max(N_,label(1)))*(layers_[j]-Tinit_);
        return e;
    }
    virtual void write(Ostream&) const;
};
}
#endif
