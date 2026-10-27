#include "wallLayer.H"
#include "fvPatchFieldMapper.H"
#include "addToRunTimeSelectionTable.H"
#include "volFields.H"
namespace Foam {
// 1 mm cells through first 30 mm, then 5 mm. Interface exactly 13 mm. Every face but the
// window wall's: 54 cells to 150 mm, the back held at 20 C (the rooms next door). The window
// wall's opaque part (the faces at x = 0 above the floor and below the ceiling): 72 cells through
// its whole 24 cm (13 mm plaster, 227 mm concrete), the back through EN ISO 6946's
// Rse = 0.04 m2K/W to the 0 C outdoor air, starting from its steady profile at 20 C inside
// with Rsi = 0.13 (U = 2.54 W/m2K, 50.8 W/m2). The room side is the CFD's own wall
// coupling throughout, as for the glass.
static const label N=72, NI=54;
static const scalar Tin=293.15, Tout=273.15, Rsi=0.13, Rse=0.04;
// EN ISO 6946's Rsi = 0.13 for horizontal heat flow (Table 1) is convection and radiation
// together. The CFD gives the convection (2.6 W/m2K on this wall in a shut-room pilot, the standard's
// 2.5); the radiation onto the window wall's cold inner face from the room's warmer surfaces is
// added here, linearised at 20 C with the usual emissivity of 0.9 (most building materials are
// above 0.8, ISO 6946 5.3.1): hr = 0.9 x 4 sigma (293.15 K)^3 = 5.14 W/m2K. The model has no
// radiation from the radiator either, which gives all its heat to the air, so the heat for this
// exchange is taken from the room's air (fv option windowRadiation).
static const scalar Hr=0.9*4*5.670374419e-8*293.15*293.15*293.15;
static scalar dx(label j) { return j<30 ? .001 : .005; }
static scalar cap(label j,bool floor) { return floor ? 2000000 : (j<13 ? 1300000 : 1800000); }
static scalar cond(label j,bool floor) { return floor ? 1.35 : (j<13 ? .57 : 1.13); }
static scalar edge(label j,bool floor) { return 1/(dx(j)/2/cond(j,floor)+dx(j+1)/2/cond(j+1,floor)); }
static bool isFloor(const vector& c) { return mag(c.y())<1e-7; }
static bool isWin(const vector& c) { return mag(c.x())<1e-7 && c.y()>1e-7 && c.y()<2.4-1e-7; }
static label nOf(bool w) { return w ? N : NI; }
// the steady profile, node centres, and its heat flux
static scalar Rwin() { scalar r=0; for(label j=0;j<N;++j) r+=dx(j)/cond(j,false); return r; }
static scalar qSteady() { return (Tin-Tout)/(Rsi+Rwin()+Rse); }
static scalar Tsteady(label j) { scalar r=Rsi; for(label k=0;k<j;++k) r+=dx(k)/cond(k,false); r+=dx(j)/2/cond(j,false); return Tin-qSteady()*r; }
static scalar Tstart(label j,bool w) { return (w && j<N) ? Tsteady(j) : Tin; }
void wallLayerFvPatchScalarField::init() { layers_.setSize(N); forAll(layers_,j) { layers_[j].setSize(patch().size(),Tin); forAll(layers_[j],i) layers_[j][i]=Tstart(j,isWin(patch().Cf()[i])); } old_=layers_; index_=-1; refValue()=Tin; refGrad()=0; valueFraction()=1; }
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f):mixedFvPatchScalarField(p,f),temperatureCoupledBase(patch()) { init(); }
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const dictionary& d):mixedFvPatchScalarField(p,f),temperatureCoupledBase(patch(),d) { init(); this->readValueEntry(d,IOobjectOption::MUST_READ); forAll(layers_,j) { word key("layer"+Foam::name(j)); if(d.found(key)) layers_[j]=scalarField(key,d,p.size()); } old_=layers_; }
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s,const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const fvPatchFieldMapper& m):mixedFvPatchScalarField(s,p,f,m),temperatureCoupledBase(patch(),s),layers_(N),index_(-1) { forAll(layers_,j) layers_[j]=scalarField(s.layers_[j],m); old_=layers_; }
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s):mixedFvPatchScalarField(s),temperatureCoupledBase(s),layers_(s.layers_),old_(s.old_),index_(s.index_) {}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s,const DimensionedField<scalar,volMesh>& f):mixedFvPatchScalarField(s,f),temperatureCoupledBase(patch(),s),layers_(s.layers_),old_(s.old_),index_(s.index_) {}
void wallLayerFvPatchScalarField::autoMap(const fvPatchFieldMapper& m) { mixedFvPatchScalarField::autoMap(m); temperatureCoupledBase::autoMap(m); forAll(layers_,j) layers_[j].autoMap(m); old_=layers_; index_=-1; }
void wallLayerFvPatchScalarField::rmap(const fvPatchField<scalar>& p,const labelList& a) { mixedFvPatchScalarField::rmap(p,a); const auto& s=refCast<const wallLayerFvPatchScalarField>(p); forAll(layers_,j) layers_[j].rmap(s.layers_[j],a); old_=layers_; index_=-1; }
void wallLayerFvPatchScalarField::updateCoeffs() {
 if(updated()) return;
 if(index_!=db().time().timeIndex()) { old_=layers_; index_=db().time().timeIndex(); }
 const scalar dt=db().time().deltaTValue();
 scalarField kc(kappa(*this)*patch().deltaCoeffs());
 scalarField tc(patchInternalField());
 scalar Tmrt; scalarField qr; radiation(Tmrt,qr);
 forAll(*this,i) {
  const bool fl=isFloor(patch().Cf()[i]), w=isWin(patch().Cf()[i]);
  const label n=nOf(w);
  scalar a[N],b[N],c[N],r[N],v[N];
  // Eliminate the solid: T0 = v0 + response0 * T_fluid.
  const scalar gs=2*cond(0,fl)/dx(0);
  const scalar h=1/(1/gs+1/max(kc[i],VSMALL));
  for(label j=0;j<n;++j) {
   a[j]=j ? -edge(j-1,fl):0; c[j]=j<n-1 ? -edge(j,fl):0;
   b[j]=cap(j,fl)*dx(j)/dt-a[j]-c[j]; r[j]=cap(j,fl)*dx(j)/dt*old_[j][i]; v[j]=0;
  }
  b[0]+=h; v[0]=h;
  if(w) r[0]+=qr[i];   // the radiation, explicit from the step's start
  // the back: to the rooms next door at 20 C, or for the window wall through Rse to 0 C
  const scalar gb=w ? 1/(dx(n-1)/2/cond(n-1,fl)+Rse) : 2*cond(n-1,fl)/dx(n-1);
  b[n-1]+=gb; r[n-1]+=gb*(w ? Tout : Tin);
  for(label j=1;j<n;++j) { scalar m=a[j]/b[j-1]; b[j]-=m*c[j-1]; r[j]-=m*r[j-1]; v[j]-=m*v[j-1]; }
  r[n-1]/=b[n-1]; v[n-1]/=b[n-1];
  for(label j=n-2;j>=0;--j) { r[j]=(r[j]-c[j]*r[j+1])/b[j]; v[j]=(v[j]-c[j]*v[j+1])/b[j]; }
  for(label j=0;j<n;++j) layers_[j][i]=r[j]+v[j]*tc[i];
  // q_to_air=h*(r0-(1-v0)*Tc) = H*(Teq-Tc).
  const scalar H=h*(1-v[0]);
  refValue()[i]=r[0]/max(1-v[0],VSMALL);
  refGrad()[i]=0; valueFraction()[i]=H/max(kc[i],VSMALL);
 }
 mixedFvPatchScalarField::updateCoeffs();
}
// heat stored since the start (each face's start profile)
scalar wallLayerFvPatchScalarField::stored() const { scalar e=0; forAll(*this,i) { const vector& f=patch().Cf()[i]; bool fl=isFloor(f), w=isWin(f); for(label j=0;j<nOf(w);++j) e+=patch().magSf()[i]*cap(j,fl)*dx(j)*(layers_[j][i]-Tstart(j,w)); } return returnReduce(e,sumOp<scalar>()); }
// heat into the layers from the rooms next door (every face but the window wall's)
scalar wallLayerFvPatchScalarField::backHeat() const { scalar q=0; forAll(*this,i) { const vector& f=patch().Cf()[i]; bool fl=isFloor(f); if(isWin(f)) continue; q+=patch().magSf()[i]*2*cond(NI-1,fl)/dx(NI-1)*(Tin-layers_[NI-1][i]); } return returnReduce(q,sumOp<scalar>()); }
// heat out of the window wall's back to the outdoor air at 0 C (positive out)
scalar wallLayerFvPatchScalarField::outsideHeat() const { scalar q=0; forAll(*this,i) { const vector& f=patch().Cf()[i]; if(!isWin(f)) continue; q+=patch().magSf()[i]*(layers_[N-1][i]-Tout)/(dx(N-1)/2/cond(N-1,false)+Rse); } return returnReduce(q,sumOp<scalar>()); }
// the step's starting state: old_ once this step's update has begun, layers_ before
void wallLayerFvPatchScalarField::radiation(scalar& Tmrt, scalarField& q) const {
 const List<scalarField>& s = index_==db().time().timeIndex() ? old_ : layers_;
 scalar a=0, at=0;
 forAll(*this,i) { const vector& f=patch().Cf()[i]; if(isWin(f) || f.x()<-1e-7) continue; a+=patch().magSf()[i]; at+=patch().magSf()[i]*s[0][i]; }
 reduce(a,sumOp<scalar>()); reduce(at,sumOp<scalar>());
 Tmrt = a>0 ? at/a : Tin;
 q.setSize(patch().size(),0);
 forAll(*this,i) if(isWin(patch().Cf()[i])) q[i]=Hr*(Tmrt-s[0][i]);
}
scalar wallLayerFvPatchScalarField::radiationPower() const { scalar Tmrt; scalarField q; radiation(Tmrt,q); return gSum(q*patch().magSf()); }
void wallLayerFvPatchScalarField::write(Ostream& os) const { mixedFvPatchScalarField::write(os); temperatureCoupledBase::write(os); forAll(layers_,j) layers_[j].writeEntry("layer"+Foam::name(j),os); }
makePatchTypeField(fvPatchScalarField,wallLayerFvPatchScalarField);
}
