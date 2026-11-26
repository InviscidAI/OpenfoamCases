/* The register's temperature: the body of the codedFixedValue `supplyTemperature85` in 0/T.
   The return's outward mass-flux-weighted mean temperature plus supplyRise (controlDict), or, while
   nothing flows out through the return, the mean of the cells next to it; while the register's
   scheduled flow is under 1e-6 kg/s, the cells next to the register, so that a shut register neither
   heats nor cools. The schedule here must match the massFlowRate table in 0/U. The solved runs' code,
   character for character; scripts/make_case.py drops this comment.                                */
const fvMesh& m=this->patch().boundaryMesh().mesh();
const auto& T=m.lookupObject<volScalarField>("T");label b=m.boundaryMesh().findPatchID("return");
scalar ts=0,w=0;const auto& tt=T.boundaryField()[b];const scalarField tc(tt.patchInternalField());
if(m.foundObject<surfaceScalarField>("phi")){const auto& ph=m.lookupObject<surfaceScalarField>("phi").boundaryField()[b];forAll(ph,i){scalar v=max(ph[i],scalar(0));ts+=v*tt[i];w+=v;}}
reduce(ts,sumOp<scalar>());reduce(w,sumOp<scalar>());
if(w<SMALL){ts=0;w=0;forAll(tc,i){ts+=tc[i];w+=1;}reduce(ts,sumOp<scalar>());reduce(w,sumOp<scalar>());}
const dictionary& d=m.time().controlDict();
scalar rise=d.get<scalar>("supplyRise"); scalar flow=d.get<scalar>("supplyMassFlow");bool furnace=d.getOrDefault<bool>("furnaceMode",false);scalar t=m.time().value(),f=0;
if(furnace){if(t<438)f=min(t/2,scalar(1));else if(t<440)f=(440-t)/2;else if(t<744)f=0;else if(t<1182)f=min((t-744)/2,scalar(1));else if(t<1184)f=(1184-t)/2;}else f=min(t/2,scalar(1));
if(flow*f<1e-6)this->operator==(this->patchInternalField());else this->operator==(ts/max(w,SMALL)+rise);
