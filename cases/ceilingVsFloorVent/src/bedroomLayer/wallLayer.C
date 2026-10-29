#include "wallLayer.H"
#include "fvPatchFieldMapper.H"
#include "addToRunTimeSelectionTable.H"
#include "volFields.H"
namespace Foam {
static const label N=24;
static const scalar Tin=293.15;
static bool isFloor(const vector& c) {return mag(c.y())<1e-7;}
static scalar dx(bool fl) {return (fl ? .019 : .0127)/N;}
static scalar cap(bool fl) {return fl ? 656.8*1884 : 640.7*1130;}
static scalar cond(bool fl) {return fl ? .1060 : .1587;}
void wallLayerFvPatchScalarField::init() {layers_.setSize(N);forAll(layers_,j) layers_[j].setSize(patch().size(),Tin);old_=layers_;index_=-1;refValue()=Tin;refGrad()=0;valueFraction()=1;}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f):mixedFvPatchScalarField(p,f),temperatureCoupledBase(patch()) {init();}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const dictionary& d):mixedFvPatchScalarField(p,f),temperatureCoupledBase(patch(),d) {init();this->readValueEntry(d,IOobjectOption::MUST_READ);forAll(layers_,j){word key("layer"+Foam::name(j));if(d.found(key)) layers_[j]=scalarField(key,d,p.size());}old_=layers_;}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s,const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const fvPatchFieldMapper& m):mixedFvPatchScalarField(s,p,f,m),temperatureCoupledBase(patch(),s),layers_(N),index_(-1) {forAll(layers_,j) layers_[j]=scalarField(s.layers_[j],m);old_=layers_;}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s):mixedFvPatchScalarField(s),temperatureCoupledBase(s),layers_(s.layers_),old_(s.old_),index_(s.index_) {}
wallLayerFvPatchScalarField::wallLayerFvPatchScalarField(const wallLayerFvPatchScalarField& s,const DimensionedField<scalar,volMesh>& f):mixedFvPatchScalarField(s,f),temperatureCoupledBase(patch(),s),layers_(s.layers_),old_(s.old_),index_(s.index_) {}
void wallLayerFvPatchScalarField::autoMap(const fvPatchFieldMapper& m){mixedFvPatchScalarField::autoMap(m);temperatureCoupledBase::autoMap(m);forAll(layers_,j) layers_[j].autoMap(m);old_=layers_;index_=-1;}
void wallLayerFvPatchScalarField::rmap(const fvPatchField<scalar>& p,const labelList& a){mixedFvPatchScalarField::rmap(p,a);const auto& s=refCast<const wallLayerFvPatchScalarField>(p);forAll(layers_,j) layers_[j].rmap(s.layers_[j],a);old_=layers_;index_=-1;}
void wallLayerFvPatchScalarField::updateCoeffs(){
 if(updated()) return;
 if(index_!=db().time().timeIndex()){old_=layers_;index_=db().time().timeIndex();}
 const scalar dt=db().time().deltaTValue();
 const scalarField kc(kappa(*this)*patch().deltaCoeffs()),tc(patchInternalField());
 forAll(*this,i){
  const bool fl=isFloor(patch().Cf()[i]);const scalar d=dx(fl),k=cond(fl),C=cap(fl)*d/dt,g=k/d;
  const scalar h=1/(d/(2*k)+1/max(kc[i],VSMALL));
  scalar a[N],b[N],c[N],r[N],v[N];
  for(label j=0;j<N;++j){a[j]=j ? -g:0;c[j]=j<N-1 ? -g:0;b[j]=C-a[j]-c[j];r[j]=C*old_[j][i];v[j]=0;}
  b[0]+=h;v[0]=h; // back is adiabatic, no conductance added there
  for(label j=1;j<N;++j){scalar m=a[j]/b[j-1];b[j]-=m*c[j-1];r[j]-=m*r[j-1];v[j]-=m*v[j-1];}
  r[N-1]/=b[N-1];v[N-1]/=b[N-1];
  for(label j=N-2;j>=0;--j){r[j]=(r[j]-c[j]*r[j+1])/b[j];v[j]=(v[j]-c[j]*v[j+1])/b[j];}
  for(label j=0;j<N;++j) layers_[j][i]=r[j]+v[j]*tc[i];
  const scalar H=h*(1-v[0]);refValue()[i]=r[0]/max(1-v[0],VSMALL);refGrad()[i]=0;valueFraction()[i]=H/max(kc[i],VSMALL);
 }
 mixedFvPatchScalarField::updateCoeffs();
}
// Re-evaluate the solid with the final fluid state, still using this step's starting state.
// This never advances a second time. It eliminates the lag from the last energy correction.
void wallLayerFvPatchScalarField::sync(){setUpdated(false);evaluate();}
scalar wallLayerFvPatchScalarField::stored() const {scalar e=0;forAll(*this,i){bool fl=isFloor(patch().Cf()[i]);for(label j=0;j<N;++j)e+=patch().magSf()[i]*cap(fl)*dx(fl)*(layers_[j][i]-Tin);}return returnReduce(e,sumOp<scalar>());}
void wallLayerFvPatchScalarField::write(Ostream& os) const {mixedFvPatchScalarField::write(os);temperatureCoupledBase::write(os);forAll(layers_,j)layers_[j].writeEntry("layer"+Foam::name(j),os);}
makePatchTypeField(fvPatchScalarField,wallLayerFvPatchScalarField);
}
