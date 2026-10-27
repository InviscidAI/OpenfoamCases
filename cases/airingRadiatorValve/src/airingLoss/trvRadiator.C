// A radiator behind a thermostatic radiator valve, as an enthalpy source spread over the
// radiator's box. Three lumped states, after Xu, Fu and Di (Building Simulation 2007,
// "Simulation on hydraulic heating system of building under the control of thermostat
// radiator valves", eqs 4-14):
//   sensor   tauSen dTsen/dt = Tsensed - Tsen                          (their eq 10)
//   valve    q = qNom * clamp((Tclose - Tsen)/Xp, 0, fMax)              (eqs 13-14, linear in
//            the valve's proportional band; EN 215 rates the nominal flow at Xp = 2 K)
//   radiator Crad dTrad/dt = cw q eps (Tsupply - Ta) - Q,  Q = Q50 ((Trad - Ta)/50)^n,
//            eps = 1 - exp(-KA/(cw q)),  KA = Q/(Trad - Ta)              (eqs 4-8, EN 442 output)
// Tsensed is the volume-mean air temperature within sensorRadius of the sensor head, Ta the
// room's mass-mean air temperature (EN 442 rates output against the room's air temperature).
// Before offUntil the valve is held shut (the radiator "turned off"); the body still gives
// off its stored heat. The states advance once per time step from the fields at the start of
// the step; the heat Q given to the air over the step is the one the radiator lost, so the
// body's energy, the water's input and the air's gain balance step by step.
// Every step is logged to postProcessing/<name>/trv_<startTime>.csv; at each field write the
// states are written to postProcessing/<name>/state_<time>, which a restart reads.

#include "cellSetOption.H"
#include "addToRunTimeSelectionTable.H"
#include "fvMatrices.H"
#include "volFields.H"
#include "uniformDimensionedFields.H"
#include "OFstream.H"
#include "IFstream.H"
#include <fstream>
#include <iomanip>

namespace Foam { namespace fv {

class trvRadiator : public cellSetOption
{
    scalar Q50_, n_, Crad_, cw_, Tsupply_, qNom_, Tclose_, Xp_, fMax_, tauSen_, offUntil_;
    point sensorPoint_; scalar sensorRadius_;
    scalar Tsen_, Trad_;
    label lastIndex_;
    labelList sensorCells_, roomCells_;
    autoPtr<uniformDimensionedScalarField> power_;
    std::ofstream out_;
    fileName dir_;

    void selectCells()
    {
        const vectorField& C = mesh_.C();
        DynamicList<label> s, r;
        forAll(C, i)
        {
            if (mag(C[i] - sensorPoint_) < sensorRadius_) s.append(i);
            if (C[i].x() > 0) r.append(i);
        }
        if (returnReduce(s.size(), sumOp<label>()) == 0)
        {
            const label c = mesh_.findCell(sensorPoint_);
            if (c >= 0) s.append(c);
        }
        sensorCells_.transfer(s); roomCells_.transfer(r);
        Info<< "trvRadiator " << name_ << ": sensor over "
            << returnReduce(sensorCells_.size(), sumOp<label>()) << " cells, room "
            << returnReduce(roomCells_.size(), sumOp<label>()) << " cells" << endl;
    }

    scalar output(scalar Trad, scalar Ta) const
    {
        const scalar d = max(Trad - Ta, scalar(0));
        return Q50_*pow(d/50, n_);
    }

public:
    TypeName("trvRadiator");

    trvRadiator(const word& name, const word& modelType, const dictionary& dict, const fvMesh& mesh)
    :
        cellSetOption(name, modelType, dict, mesh),
        lastIndex_(-1)
    {
        fieldNames_.resize(1, "h");
        fv::option::resetApplied();
        const dictionary& c = coeffs_;
        Q50_ = c.get<scalar>("Q50"); n_ = c.get<scalar>("n"); Crad_ = c.get<scalar>("Crad");
        cw_ = c.getOrDefault<scalar>("cw", 4186); Tsupply_ = c.get<scalar>("Tsupply");
        qNom_ = c.get<scalar>("qNom"); Tclose_ = c.get<scalar>("Tclose"); Xp_ = c.get<scalar>("Xp");
        fMax_ = c.get<scalar>("fMax"); tauSen_ = c.get<scalar>("tauSen");
        offUntil_ = c.getOrDefault<scalar>("offUntil", -1);
        sensorPoint_ = c.get<point>("sensorPoint"); sensorRadius_ = c.get<scalar>("sensorRadius");
        Tsen_ = c.get<scalar>("TsenInit"); Trad_ = c.get<scalar>("TradInit");

        dir_ = mesh.time().globalPath()/"postProcessing"/name_;
        const word start = mesh.time().timeName();
        const fileName state = dir_/("state_" + start);
        if (isFile(state))
        {
            IFstream is(state); dictionary d(is);
            Tsen_ = d.get<scalar>("Tsen"); Trad_ = d.get<scalar>("Trad");
            Info<< "trvRadiator " << name_ << ": state read from " << state << endl;
        }
        Info<< "trvRadiator " << name_ << ": Tsen " << Tsen_ << " K, Trad " << Trad_ << " K" << endl;

        power_.reset
        (
            new uniformDimensionedScalarField
            (
                IOobject("radiatorPower", mesh.time().timeName(), mesh,
                         IOobject::NO_READ, IOobject::NO_WRITE, IOobject::REGISTER),
                dimensionedScalar(dimPower, output(Trad_, Tsen_))
            )
        );
        selectCells();
        if (Pstream::master())
        {
            mkDir(dir_);
            out_.open((dir_/("trv_" + start + ".csv")).c_str());
            out_<< "t,dt,TsenAir,Ta,Tsen,f,q,Trad,Q,Qwater,TsenNext,TradNext\n" << std::setprecision(14);
        }
    }

    virtual void addSup(const volScalarField& rho, fvMatrix<scalar>& eqn, const label fieldi)
    {
        const Time& time = mesh_.time();
        if (time.timeIndex() != lastIndex_)
        {
            lastIndex_ = time.timeIndex();
            const scalar dt = time.deltaTValue(), ta = time.value() - dt;
            const auto& T = mesh_.lookupObject<volScalarField>("T");
            const auto& rhoC = mesh_.lookupObject<volScalarField>("rho");
            const scalarField& V = mesh_.V();
            scalar sv = 0, stv = 0, rm = 0, rmt = 0;
            for (const label i : sensorCells_) { sv += V[i]; stv += V[i]*T[i]; }
            for (const label i : roomCells_) { const scalar m = rhoC[i]*V[i]; rm += m; rmt += m*T[i]; }
            reduce(sv, sumOp<scalar>()); reduce(stv, sumOp<scalar>());
            reduce(rm, sumOp<scalar>()); reduce(rmt, sumOp<scalar>());
            const scalar Ts = stv/sv, Ta = rmt/rm;

            scalar f = (Tclose_ - Tsen_)/Xp_;
            f = (ta < offUntil_ - 1e-9) ? 0 : min(max(f, scalar(0)), fMax_);
            const scalar q = f*qNom_;
            const scalar Q = output(Trad_, Ta);
            scalar Qw = 0;
            if (q > 0)
            {
                const scalar d = Trad_ - Ta;
                const scalar KA = d > 1e-6 ? Q/d : Q50_/50*pow(1e-6/50, n_ - 1);
                Qw = cw_*q*(1 - exp(-KA/(cw_*q)))*(Tsupply_ - Ta);
            }
            const scalar TsenNext = Ts + (Tsen_ - Ts)*exp(-dt/tauSen_);
            const scalar TradNext = Trad_ + dt*(Qw - Q)/Crad_;
            if (Pstream::master())
            {
                out_<< time.value() << ',' << dt << ',' << Ts << ',' << Ta << ',' << Tsen_ << ',' << f
                    << ',' << q << ',' << Trad_ << ',' << Q << ',' << Qw << ',' << TsenNext << ','
                    << TradNext << '\n';
                out_.flush();
            }
            power_->value() = Q;
            Tsen_ = TsenNext; Trad_ = TradNext;
            if (time.writeTime() && Pstream::master())
            {
                OFstream os(dir_/("state_" + time.timeName()));
                os.precision(17);
                os << "Tsen " << Tsen_ << ";\nTrad " << Trad_ << ";\n";
            }
        }

        DimensionedField<scalar, volMesh> Su
        (
            IOobject(name_ + "Su", mesh_.time().timeName(), mesh_, IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
            mesh_, dimensionedScalar(eqn.dimensions()/dimVolume, Zero)
        );
        const scalar s = power_->value()/V_;
        for (const label i : cells_) Su[i] = s;
        eqn += Su;
    }

    virtual void addSup(fvMatrix<scalar>& eqn, const label fieldi)
    {
        addSup(volScalarField::null(), eqn, fieldi);
    }

    virtual bool read(const dictionary& dict) { return cellSetOption::read(dict); }
};

defineTypeNameAndDebug(trvRadiator, 0);
addToRunTimeSelectionTable(option, trvRadiator, dictionary);

}}
