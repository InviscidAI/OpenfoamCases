#include "radLayerWall.H"
#include "fvPatchFieldMapper.H"
#include "addToRunTimeSelectionTable.H"
#include "volFields.H"
#include "physicoChemicalConstants.H"
namespace Foam {

radLayerWallFvPatchScalarField::radLayerWallFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f)
: mixedFvPatchScalarField(p,f), temperatureCoupledBase(patch()),
  Q_(0), h_(0), Ta_(0), eps_(1), N_(0), thick_(0), k_(1), rhoCp_(0), Tinit_(293.15), index_(-1), haveTr_(false)
{ refValue()=0; refGrad()=0; valueFraction()=1; }

radLayerWallFvPatchScalarField::radLayerWallFvPatchScalarField(const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const dictionary& d)
: mixedFvPatchScalarField(p,f), temperatureCoupledBase(patch(),d),
  Q_(d.getOrDefault<scalar>("Q",0)), h_(d.getOrDefault<scalar>("h",0)), Ta_(d.getOrDefault<scalar>("Ta",0)),
  eps_(d.get<scalar>("emissivity")), N_(d.getOrDefault<label>("nLayers",0)),
  thick_(N_ ? d.get<scalar>("thickness") : 0), k_(N_ ? d.get<scalar>("conductivity") : 1),
  rhoCp_(N_ ? d.get<scalar>("rhoCp") : 0), Tinit_(d.get<scalar>("Tinit")), index_(-1), haveTr_(false)
{
    this->readValueEntry(d,IOobjectOption::MUST_READ);
    layers_.setSize(N_);
    forAll(layers_,j)
    {
        const word key("layer"+Foam::name(j));
        layers_[j] = d.found(key) ? scalarField(key,d,p.size()) : scalarField(p.size(),Tinit_);
    }
    old_=layers_;
    if (d.found("Tr") && d.found("qrSeen"))
    {
        Tr_=scalarField("Tr",d,p.size()); qrSeen_=scalarField("qrSeen",d,p.size()); haveTr_=true;
    }
    refValue()=*this; refGrad()=0; valueFraction()=1;
}

radLayerWallFvPatchScalarField::radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField& s,const fvPatch& p,const DimensionedField<scalar,volMesh>& f,const fvPatchFieldMapper& m)
: mixedFvPatchScalarField(s,p,f,m), temperatureCoupledBase(patch(),s),
  Q_(s.Q_), h_(s.h_), Ta_(s.Ta_), eps_(s.eps_), N_(s.N_), thick_(s.thick_), k_(s.k_), rhoCp_(s.rhoCp_), Tinit_(s.Tinit_),
  layers_(s.N_), index_(-1), haveTr_(s.haveTr_)
{
    forAll(layers_,j) layers_[j]=scalarField(s.layers_[j],m);
    old_=layers_;
    if (haveTr_) { Tr_=scalarField(s.Tr_,m); qrSeen_=scalarField(s.qrSeen_,m); }
}

radLayerWallFvPatchScalarField::radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField& s)
: mixedFvPatchScalarField(s), temperatureCoupledBase(s),
  Q_(s.Q_), h_(s.h_), Ta_(s.Ta_), eps_(s.eps_), N_(s.N_), thick_(s.thick_), k_(s.k_), rhoCp_(s.rhoCp_), Tinit_(s.Tinit_),
  layers_(s.layers_), old_(s.old_), index_(s.index_), Tr_(s.Tr_), qrSeen_(s.qrSeen_), haveTr_(s.haveTr_) {}

radLayerWallFvPatchScalarField::radLayerWallFvPatchScalarField(const radLayerWallFvPatchScalarField& s,const DimensionedField<scalar,volMesh>& f)
: mixedFvPatchScalarField(s,f), temperatureCoupledBase(patch(),s),
  Q_(s.Q_), h_(s.h_), Ta_(s.Ta_), eps_(s.eps_), N_(s.N_), thick_(s.thick_), k_(s.k_), rhoCp_(s.rhoCp_), Tinit_(s.Tinit_),
  layers_(s.layers_), old_(s.old_), index_(s.index_), Tr_(s.Tr_), qrSeen_(s.qrSeen_), haveTr_(s.haveTr_) {}

void radLayerWallFvPatchScalarField::autoMap(const fvPatchFieldMapper& m)
{
    mixedFvPatchScalarField::autoMap(m); temperatureCoupledBase::autoMap(m);
    forAll(layers_,j) layers_[j].autoMap(m);
    old_=layers_; index_=-1;
    if (haveTr_) { Tr_.autoMap(m); qrSeen_.autoMap(m); }
}

void radLayerWallFvPatchScalarField::rmap(const fvPatchField<scalar>& p,const labelList& a)
{
    mixedFvPatchScalarField::rmap(p,a);
    const auto& s=refCast<const radLayerWallFvPatchScalarField>(p);
    temperatureCoupledBase::rmap(s,a);
    forAll(layers_,j) layers_[j].rmap(s.layers_[j],a);
    old_=layers_; index_=-1;
    if (haveTr_ && s.haveTr_) { Tr_.rmap(s.Tr_,a); qrSeen_.rmap(s.qrSeen_,a); }
}

void radLayerWallFvPatchScalarField::updateCoeffs()
{
    if (updated()) return;
    if (index_!=db().time().timeIndex()) { old_=layers_; index_=db().time().timeIndex(); }
    const scalar dt=db().time().deltaTValue();
    const scalarField& Tp=*this;
    const scalarField& qr=patch().lookupPatchField<volScalarField>("qr");

    bool solved=!haveTr_ || Tr_.size()!=Tp.size();
    if (!solved) { forAll(qr,i) { if (qr[i]!=qrSeen_[i]) { solved=true; break; } } }
    if (solved) { Tr_=Tp; qrSeen_=qr; haveTr_=true; }

    const scalarField kc(kappa(Tp)*patch().deltaCoeffs()), Tc(patchInternalField());
    const scalar q=Q_/max(gSum(patch().magSf()),VSMALL);
    const scalar sigma=constant::physicoChemical::sigma.value();
    const label M=N_+1;
    const scalar dx=N_ ? thick_/N_ : 1, g=k_/dx, g0=2*k_/dx, C=N_ ? rhoCp_*dx/dt : 0;
    List<scalar> a(M), b(M), c(M), r(M), v(M);
    forAll(Tp,i)
    {
        const scalar hr=4*eps_*sigma*pow3(Tr_[i]);
        // row 0: the massless surface; rows 1..N: the layer's nodes, adiabatic back
        a[0]=0; c[0]=N_ ? -g0 : 0; b[0]=kc[i]+h_+hr-c[0];
        r[0]=q+h_*Ta_+qr[i]+hr*Tr_[i]; v[0]=kc[i];
        for (label j=1;j<M;++j)
        {
            a[j]=(j==1) ? -g0 : -g; c[j]=(j<M-1) ? -g : 0;
            b[j]=C-a[j]-c[j]; r[j]=C*old_[j-1][i]; v[j]=0;
        }
        for (label j=1;j<M;++j) { const scalar f=a[j]/b[j-1]; b[j]-=f*c[j-1]; r[j]-=f*r[j-1]; v[j]-=f*v[j-1]; }
        r[M-1]/=b[M-1]; v[M-1]/=b[M-1];
        for (label j=M-2;j>=0;--j) { r[j]=(r[j]-c[j]*r[j+1])/b[j]; v[j]=(v[j]-c[j]*v[j+1])/b[j]; }
        for (label j=1;j<M;++j) layers_[j-1][i]=r[j]+v[j]*Tc[i];
        // Tw = r0 + v0 Tc  ->  mixed with valueFraction 1 - v0 and refValue r0/(1 - v0)
        const scalar f=max(1-v[0],VSMALL);
        valueFraction()[i]=f; refValue()[i]=r[0]/f; refGrad()[i]=0;
    }
    mixedFvPatchScalarField::updateCoeffs();
}

void radLayerWallFvPatchScalarField::write(Ostream& os) const
{
    mixedFvPatchScalarField::write(os);
    temperatureCoupledBase::write(os);
    os.writeEntry("Q",Q_); os.writeEntry("h",h_); os.writeEntry("Ta",Ta_); os.writeEntry("emissivity",eps_);
    os.writeEntry("nLayers",N_); os.writeEntry("Tinit",Tinit_);
    if (N_) { os.writeEntry("thickness",thick_); os.writeEntry("conductivity",k_); os.writeEntry("rhoCp",rhoCp_); }
    forAll(layers_,j) layers_[j].writeEntry("layer"+Foam::name(j),os);
    if (haveTr_) { Tr_.writeEntry("Tr",os); qrSeen_.writeEntry("qrSeen",os); }
}

makePatchTypeField(fvPatchScalarField,radLayerWallFvPatchScalarField);
}
