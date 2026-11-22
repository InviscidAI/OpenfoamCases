/* storedLayerWall73: radiatorCabinetTop's radLayerWall (src/radLayerWall there) with its radiation
   taken out, as the solved runs of ovenDoorOpen compiled it. qr and the linearised radiative film hr
   are zero, so a face's surface balances

       kc (Tc - Tw) + q + h (Ta - Tw) + g0 (T0 - Tw) = 0

   with kc = kappaEff * deltaCoeffs to the first air cell, q = Q/A and h, Ta a film to an outside
   temperature (both zero in this case), and, if nLayers > 0, an implicit 1-D layer behind the surface
   with heat capacity and an adiabatic back (nodes at the cell centres of nLayers equal slices,
   g0 = 2k/dx to the first; T0 is the first node's temperature). The layer is advanced from the step's
   starting state at every evaluation, so outer correctors do not advance it twice.

   Two additions over radLayerWall, both used by scripts/monitor.C:
   commitFinalSurface()  re-solves the layer's nodes from the step's starting state against the
                         surface temperature the step ended with (the nodes are otherwise left at the
                         temperature of the last assembly); the monitor calls it after every step.
   storedEnergyAbove(T)  the heat in the layer above T, J.
   The emissivity entry is read and not used. The class keeps radLayerWall's C++ name; the type name
   in 0/T is storedLayerWall73.                                                                       */
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
    TypeName("storedLayerWall73");
    radLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&);
    radLayerWallFvPatchScalarField(const fvPatch&,const DimensionedField<scalar,volMesh>&,const dictionary&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&,const fvPatch&,const DimensionedField<scalar,volMesh>&,const fvPatchFieldMapper&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&);
    radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField&,const DimensionedField<scalar,volMesh>&);
    virtual tmp<fvPatchField<scalar>> clone() const { return fvPatchField<scalar>::Clone(*this); }
    virtual tmp<fvPatchField<scalar>> clone(const DimensionedField<scalar,volMesh>& f) const { return fvPatchField<scalar>::Clone(*this,f); }
    // Commit implicit layer nodes against the final solved surface temperature.
    // This advances from old_ (not layers_), so repeated calls never double-step.
    void commitFinalSurface();
    scalar storedEnergyAbove(scalar Tref) const { scalar e=0; forAll(layers_,j) e += gSum((layers_[j]-Tref)*patch().magSf())*rhoCp_*thick_/max(N_,label(1)); return e; }
    virtual void autoMap(const fvPatchFieldMapper&);
    virtual void rmap(const fvPatchField<scalar>&,const labelList&);
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
};
}
#endif
