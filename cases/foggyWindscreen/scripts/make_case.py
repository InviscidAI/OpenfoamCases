#!/usr/bin/env python3
"""Write one run of the cabin section as an OpenFOAM v2512 case.

usage: $PYTHON make_case.py <outside|recirc> <case dir> [--end T] [--write DT] [--ranks N] [--mesh-scale S]
                    [--film KG_M2]

$PYTHON needs shapely (geometry.py, run here) and gmsh 4.15.2 (make_mesh.py, run by the case's Allrun).

The air: buoyantPimpleFoam, k-omega SST with the buoyancy source, a perfect gas, as in
radiatorUnderWindow's curtain runs and iceDamRoofVents, with PISO in place of PIMPLE. The water vapour:
a scalarTransport function object `w` (specific humidity), carried by the mass flux with D rho = mu/0.60 + mut/0.85, and fed by the two occupants (70 g/h each: a quarter
at the breath in front of the face, the rest over the cells touching the torso, neck and head, less
those against a seat). The mist: a second scalarTransport `L` (liquid water per kg of air), into which
`walls` condenses any vapour above saturation after each step, and from which it evaporates where the
air is below saturation, the latent heat going to the air in the next step (hiddenHeat, hidElat).
The glass and the fog: the coded function object `walls` keeps, for every face of the screens and the trim, a temperature with the face's heat capacity, and for the
screens a film of water. Each step it takes the heat the air gave the face (kappaEff dT/dn) and the
vapour the face took from the air (D rho dw/dn) from the step just solved, adds the latent heat,
loses heat through the glass to the 3 C morning, and sets the face's temperature, and its vapour at
saturation wherever it is wet or condensing, for the next step. A screen face is misted while its
film holds more than physics.FILM_CLEAR.

outside: the defroster takes air from outside (3 C, 90%) through the heater; the recirculation
intake is a wall. recirc: it takes the cabin's own air from the intake under the dash, through the
same heater (fixed effectiveness against 85 C coolant); its air carries the intake's vapour and the
mist the heater evaporates, set each step by `walls`, and adds no water. In both the A/C is off
and the rear vent at the parcel shelf is open to the outdoor pressure.
"""
import argparse
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import physics as ph

ap = argparse.ArgumentParser()
ap.add_argument("variant", choices=("outside", "recirc"))
ap.add_argument("case")
ap.add_argument("--end", type=float, default=600.0)
ap.add_argument("--write", type=float, default=1.25)
ap.add_argument("--ranks", type=int, default=8)
ap.add_argument("--mesh-scale", type=float, default=1.0)
ap.add_argument("--film", type=float, default=ph.FILM0)
ap.add_argument("--contents-x", type=float, default=ph.CONTENTS_X,
                help="the hidden contents' heat capacity, in times the cabin air's")
ap.add_argument("--contents-zone", choices=("low", "all"), default=ph.CONTENTS_ZONE,
                help="where the contents' capacity sits: below the beltline, or over the whole cabin")
a = ap.parse_args()

V = a.variant
C = os.path.abspath(a.case)
os.makedirs(C, exist_ok=True)
REC = V == "recirc"
G = 9.81

# the geometry, and each occupant's surface for the heat flux
subprocess_geo = f"{sys.executable} {HERE}/geometry.py {C}/geometry.json"
if os.system(subprocess_geo + " > " + C + "/log.geometry") != 0:
    raise SystemExit("geometry.py failed")
geo = json.load(open(f"{C}/geometry.json"))
length = {}
for r in geo["rings"]:
    for i, (x, y, n) in enumerate(r):
        x2, y2, _ = r[(i + 1) % len(r)]
        length[n] = length.get(n, 0) + math.hypot(x2 - x, y2 - y)
Q_DRIVER = ph.HEAT_PER_M_EACH / length["driver"]
Q_PASS = ph.HEAT_PER_M_EACH / length["passenger"]

# wall nodes kept by the `walls` function object: name, heat capacity, resistance to outside
# (0 = adiabatic), wettable, starting temperature
NODES = [("windscreen", ph.C_WIND, ph.R_WIND + 1 / ph.H_OUT, True, ph.TG0_WIND),
         ("rearScreen", ph.C_REAR, ph.R_REAR + 1 / ph.H_OUT, True, ph.TG0_REAR),
         ("roof", ph.C_TRIM, ph.R_ROOF, False, ph.TS0_ROOF),        # headliner on the steel roof
         ("trim", ph.C_TRIM, 0.0, False, ph.T0)]
if not REC:
    NODES.append(("recirc", ph.C_TRIM, 0.0, False, ph.T0))     # the closed intake's flap is trim

HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def write(rel, cls, body):
    path = os.path.join(C, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(HDR.format(cls=cls, obj=os.path.basename(rel)) + body)


WALLS = "(windscreen|rearScreen|roof|trim|driver|passenger" + ("" if REC else "|recirc") + ")"


def field(name, cls, dims, internal, walls, defrost, recirc, vent, extra=""):
    rec = f'    recirc {{ {recirc} }}\n' if REC else ""
    write(f"0.orig/{name}", cls, f"""dimensions      {dims};
internalField   {internal};
boundaryField
{{
    "{WALLS}" {{ {walls} }}
    defrost {{ {defrost} }}
{rec}    rearVent {{ {vent} }}{extra}
    frontAndBack {{ type empty; }}
}}
""")


ramp = f"table ((0 0) (0.5 {ph.MDOT:.6g}))"     # the blower spins up over half a second
field("U", "volVectorField", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", "type noSlip;",
      f"type flowRateInletVelocity; massFlowRate {ramp}; rho rho; value uniform (0 0 0);",
      f"type flowRateOutletVelocity; massFlowRate {ramp}; rho rho; value uniform (0 0 0);",
      "type pressureInletOutletVelocity; value uniform (0 0 0);")
p0_vent = ph.P_ATM * math.exp(-G * 0.90 / (ph.R_GAS * ph.T_OUT))
field("p_rgh", "volScalarField", "[1 -1 -2 0 0 0 0]", "uniform 1e5",
      "type fixedFluxPressure; value uniform 1e5;", "type fixedFluxPressure; value uniform 1e5;",
      "type fixedFluxPressure; value uniform 1e5;",
      # the boot's vents: the 3 C outdoor air's barometric pressure at the shelf's height, 0.90 m
      f"type prghTotalPressure; rho rho; p0 uniform {p0_vent:.10g}; value uniform 1e5;")
field("p", "volScalarField", "[1 -1 -2 0 0 0 0]", "uniform 1e5", "type calculated; value uniform 1e5;",
      "type calculated; value uniform 1e5;", "type calculated; value uniform 1e5;",
      "type calculated; value uniform 1e5;")
I_IN, L_IN = 0.05, 0.1 * ph.DUCT_W
field("k", "volScalarField", "[0 2 -2 0 0 0 0]", "uniform 1e-5", "type kLowReWallFunction; value uniform 1e-5;",
      f"type turbulentIntensityKineticEnergyInlet; intensity {I_IN}; value uniform 1e-5;",
      "type zeroGradient;", "type inletOutlet; inletValue uniform 1e-5; value uniform 1e-5;")
field("omega", "volScalarField", "[0 0 -1 0 0 0 0]", "uniform 1.0", "type omegaWallFunction; value uniform 1.0;",
      f"type turbulentMixingLengthFrequencyInlet; mixingLength {L_IN:.6g}; value uniform 1.0;",
      "type zeroGradient;", "type inletOutlet; inletValue uniform 1.0; value uniform 1.0;")
field("nut", "volScalarField", "[0 2 -1 0 0 0 0]", "uniform 0", "type nutUSpaldingWallFunction; value uniform 0;",
      "type calculated; value uniform 0;", "type calculated; value uniform 0;", "type calculated; value uniform 0;")
field("alphat", "volScalarField", "[1 -1 -1 0 0 0 0]", "uniform 0",
      "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;",
      "type calculated; value uniform 0;", "type calculated; value uniform 0;", "type calculated; value uniform 0;")

eps, Tc = ph.EPS_HEATER, ph.T_COOLANT
if REC:
    t_def = f"""type outletMappedUniformInlet; outlets {{ recirc {{ fraction constant {1 - eps:.6g}; offset constant {eps * Tc:.6g}; }} }}
        value uniform {ph.T_SUP_OUT:.6g};"""
    # the intake's vapour and the mist the heater evaporates: set every step by `walls`
    w_def = f"type fixedValue; value uniform {ph.W0:.8g};"
else:
    t_def = f"type fixedValue; value uniform {ph.T_SUP_OUT:.6g};"
    w_def = f"type fixedValue; value uniform {ph.W_OUT:.8g};"
node_T = "\n".join(f"    {n} {{ type fixedValue; value uniform {t0:.6g}; }}" for n, _, _, _, t0 in NODES)
write("0.orig/T", "volScalarField", f"""dimensions      [0 0 0 1 0 0 0];
internalField   uniform {ph.T0:.6g};
boundaryField
{{
    // screens and trim: each face's temperature is set every step by the `walls` function object
{node_T}
    // the occupants' sensible heat, {ph.OCC_HEAT:g} W each over a cabin {ph.WIDTH} m wide
    driver    {{ type externalWallHeatFluxTemperature; mode flux; q uniform {Q_DRIVER:.6g}; kappaMethod fluidThermo; value uniform {ph.T0:.6g}; }}
    passenger {{ type externalWallHeatFluxTemperature; mode flux; q uniform {Q_PASS:.6g}; kappaMethod fluidThermo; value uniform {ph.T0:.6g}; }}
    // the heater: T_in + {eps:g} ({Tc - ph.C2K:g} C - T_in)
    defrost {{ {t_def} }}
{"    recirc { type zeroGradient; }" if REC else ""}
    rearVent {{ type inletOutlet; inletValue uniform {ph.T_OUT:.6g}; value uniform {ph.T0:.6g}; }}
    frontAndBack {{ type empty; }}
}}
""")
wet = "\n".join(f"    {n} {{ type mixed; refValue uniform {ph.W0:.8g}; refGradient uniform 0; valueFraction uniform 1; value uniform {ph.W0:.8g}; }}"
                for n in ("windscreen", "rearScreen"))
write("0.orig/w", "volScalarField", f"""dimensions      [0 0 0 0 0 0 0];
internalField   uniform {ph.W0:.8g};
boundaryField
{{
    // wet or condensing screen faces: saturated at the glass (valueFraction 1); dry faces: no flux.
    // Set every step by the `walls` function object.
{wet}
    "(roof|trim|driver|passenger{'' if REC else '|recirc'})" {{ type zeroGradient; }}
    defrost {{ {w_def} }}
{"    recirc { type zeroGradient; }" if REC else ""}
    rearVent {{ type inletOutlet; inletValue uniform {ph.W_OUT:.8g}; value uniform {ph.W0:.8g}; }}
    frontAndBack {{ type empty; }}
}}
""")

# the mist: liquid water carried in the air, kg per kg of air (physics.py, "mist"); none comes in, none is
# deposited on a wall, and it leaves with the air at the rear vent and, on recirculation, at the intake
write("0.orig/L", "volScalarField", f"""dimensions      [0 0 0 0 0 0 0];
internalField   uniform 0;
boundaryField
{{
    "(windscreen|rearScreen|roof|trim|driver|passenger{'' if REC else '|recirc'})" {{ type zeroGradient; }}
    defrost {{ type fixedValue; value uniform 0; }}
{"    recirc { type zeroGradient; }" if REC else ""}
    rearVent {{ type inletOutlet; inletValue uniform 0; value uniform 0; }}
    frontAndBack {{ type empty; }}
}}
""")

# ---------------------------------------------------------------- what the section does not hold
# Per cell of air: the side glass (above the beltline, between the pillars) or the door and pillar trim
# beside it, each 2/W m2 per m3 with ISO 6946's inside coefficient, and below the beltline the contents'
# heat capacity, in step with the air within TAU_CONTENTS. setup_fields.py writes where each is (hidASg,
# hidADr m2/m3, hidCCt J/m3K); `walls` keeps their temperatures (hidTsg, hidTdr, hidTct) and the side
# glass's film (hidFilm). These two sources take the heat and the vapour from the air, and leave what they
# took in hidQsg, hidQdr, hidQct (W/m3) and hidMsg (kg/m3s) for `walls` to give the same amounts to the
# surfaces. `eqn += Su` adds +Su in v2512 (source() holds minus the source).
HIDDEN_HEAT = f"""
hiddenHeat
{{
    type            scalarCodedSource;
    selectionMode   all;
    fields          (h);
    name            hiddenHeat;
    codeCorrect     #{{ #}};
    codeConstrain   #{{ #}};
    codeAddSupRho
    #{{
        if (!mesh_.foundObject<volScalarField>("hidQsg")) return;
        const scalarField& T = mesh_.lookupObject<volScalarField>("T").primitiveField();
        const scalarField& Tsg = mesh_.lookupObject<volScalarField>("hidTsg").primitiveField();
        const scalarField& Tdr = mesh_.lookupObject<volScalarField>("hidTdr").primitiveField();
        const scalarField& Tct = mesh_.lookupObject<volScalarField>("hidTct").primitiveField();
        const scalarField& aSg = mesh_.lookupObject<volScalarField>("hidASg").primitiveField();
        const scalarField& aDr = mesh_.lookupObject<volScalarField>("hidADr").primitiveField();
        const scalarField& cCt = mesh_.lookupObject<volScalarField>("hidCCt").primitiveField();
        scalarField& Qsg = mesh_.lookupObjectRef<volScalarField>("hidQsg").primitiveFieldRef();
        scalarField& Qdr = mesh_.lookupObjectRef<volScalarField>("hidQdr").primitiveFieldRef();
        scalarField& Qct = mesh_.lookupObjectRef<volScalarField>("hidQct").primitiveFieldRef();
        Qsg = {ph.H_SI:.8g}*aSg*(T - Tsg);
        Qdr = {ph.H_SI:.8g}*aDr*(T - Tdr);
        Qct = cCt/{ph.TAU_CONTENTS:.8g}*(T - Tct);
        volScalarField::Internal Su
        (
            IOobject("hiddenHeatSu", mesh_.time().timeName(), mesh_,
                     IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
            mesh_,
            dimensionedScalar(dimPower/dimVolume, Zero)
        );
        Su.field() = -(Qsg + Qdr + Qct);
        // the latent heat of the mist `walls` condensed (or evaporated) after the last step, J/m3
        if (mesh_.foundObject<volScalarField>("hidElat"))
        {{
            Su.field() += mesh_.lookupObject<volScalarField>("hidElat").primitiveField()/mesh_.time().deltaTValue();
        }}
        eqn += Su;
    #}};
}}
"""
SIDE_VAPOUR = f"""
            sideGlass
            {{
                // the side glass condenses where it is below the air's dew point, and its film evaporates,
                // at h_c/cp = {ph.H_CI:g}/1005 kg/m2s per unit of specific humidity
                type            scalarCodedSource;
                selectionMode   all;
                fields          (w);
                name            sideGlassVapour;
                codeCorrect     #{{ #}};
                codeConstrain   #{{ #}};
                codeAddSupRho
                #{{
                    if (!mesh_.foundObject<volScalarField>("hidMsg")) return;
                    const scalarField& w = mesh_.lookupObject<volScalarField>("w").primitiveField();
                    const scalarField& p = mesh_.lookupObject<volScalarField>("p").primitiveField();
                    const scalarField& Tsg = mesh_.lookupObject<volScalarField>("hidTsg").primitiveField();
                    const scalarField& film = mesh_.lookupObject<volScalarField>("hidFilm").primitiveField();
                    const scalarField& aSg = mesh_.lookupObject<volScalarField>("hidASg").primitiveField();
                    scalarField& M = mesh_.lookupObjectRef<volScalarField>("hidMsg").primitiveFieldRef();
                    const scalar dt = mesh_.time().deltaTValue();
                    forAll(M, i)
                    {{
                        if (aSg[i] <= 0) {{ M[i] = 0; continue; }}
                        const scalar t = Tsg[i] - 273.15;
                        const scalar e = 611.21*::exp((18.678 - t/234.5)*(t/(257.14 + t)));
                        const scalar ws = 0.622*e/(p[i] - 0.378*e);
                        scalar m = {ph.H_CI / 1005.0:.8g}*aSg[i]*(w[i] - ws);
                        if (m < 0) m = max(m, -film[i]*aSg[i]/dt);
                        M[i] = m;
                    }}
                    volScalarField::Internal Su
                    (
                        IOobject("sideGlassSu", mesh_.time().timeName(), mesh_,
                                 IOobject::NO_READ, IOobject::NO_WRITE, IOobject::NO_REGISTER),
                        mesh_,
                        dimensionedScalar(dimDensity/dimTime, Zero)
                    );
                    Su.field() = -M;
                    eqn += Su;
                #}};
            }}"""

# the occupants' water: 70 g/h each over a cabin {WIDTH} m wide, a share BREATH_SHARE at the breath in front
# of the face and the rest through the skin of the upper body (physics.py; topoSet's <who>Breath, <who>Skin)
OCC_SOURCES = "".join(f"""
            {who}{part}
            {{
                type            scalarSemiImplicitSource;
                volumeMode      absolute;
                selectionMode   cellSet;
                cellSet         {who}{part};
                sources {{ w {{ explicit constant {rate:.8g}; implicit constant 0; }} }}
            }}""" for who in ("driver", "passenger")
    for part, rate in (("Breath", ph.BREATH_PER_M_EACH), ("Skin", ph.SKIN_PER_M_EACH)))

# ---------------------------------------------------------------- constant
write("constant/g", "uniformDimensionedVectorField", "dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n")
write("constant/thermophysicalProperties", "dictionary", f"""thermoType
{{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}}
pRef            100000;
mixture
{{
    specie          {{ molWeight 28.96; }}
    thermodynamics  {{ Cp 1005; Hf 0; Tref {ph.T_OUT:.6g}; Href 0; }}
    transport       {{ mu {ph.MU:g}; Pr 0.71; }}
}}
""")
write("constant/turbulenceProperties", "dictionary", """simulationType  RAS;
RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
""")
write("constant/fvOptions", "dictionary", """buoyancyTurb
{
    type            buoyancyTurbSource;
    selectionMode   all;
}
""" + HIDDEN_HEAT)

# ---------------------------------------------------------------- system
write("system/fvSchemes", "dictionary", """ddtSchemes      { default Euler; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default         none;
    div(phi,U)      Gauss limitedLinearV 1;
    energy          Gauss limitedLinear 1;
    div(phi,h)      $energy;
    div(phi,e)      $energy;
    div(phi,K)      Gauss linear;
    div(phi,Ekp)    Gauss linear;
    div(phi,w)      Gauss limitedLinear 1;   // the same scheme as T
    div(phi,L)      Gauss limitedLinear 1;
    turbulence      Gauss limitedLinear 1;
    div(phi,k)      $turbulence;
    div(phi,omega)  $turbulence;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes    { default Gauss linear limited corrected 0.5; }   // 16 faces above 70 degrees, at the screens' lips
interpolationSchemes{ default linear; }
snGradSchemes       { default limited corrected 0.5; }
wallDist            { method meshWave; }
""")
write("system/fvSolution", "dictionary", """solvers
{
    "rho.*"
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       0;
        relTol          0;
    }
    p_rgh
    {
        solver          GAMG;
        smoother        DICGaussSeidel;
        tolerance       1e-7;
        relTol          0.01;
        maxIter         100;
    }
    p_rghFinal
    {
        $p_rgh;
        relTol          0.001;      // a pilot: relTol 0 took 33-40 GAMG sweeps per final solve
    }
    "(U|h|e|k|omega|w|L)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-9;
        relTol          0.1;
    }
    "(U|h|e|k|omega)Final"
    {
        $U;
        relTol          0;
    }
}
PIMPLE
{
    momentumPredictor           yes;
    nOuterCorrectors            1;      // PISO: a pilot took 0.088 s a step with 2 outer correctors
    nCorrectors                 2;
    nNonOrthogonalCorrectors    0;
}
relaxationFactors { equations { ".*" 1; } }
""")
def upper_actions(who):
    """The cells touching `who`'s torso, neck and head: patchToCell, kept where within the primitives + margin."""
    acts = []
    for k, (a0, a1, r) in enumerate(ph.UPPER[who]):
        act = "new" if k == 0 else "add"
        R = r + ph.UPPER_MARGIN
        if a1 is None:
            acts.append(f"{{ name {who}Upper; type cellSet; action {act}; source sphereToCell; origin ({a0[0]} {a0[1]} 0.5); radius {R:g}; }}")
        else:
            acts.append(f"{{ name {who}Upper; type cellSet; action {act}; source cylinderToCell; "
                        f"p1 ({a0[0]} {a0[1]} 0.5); p2 ({a1[0]} {a1[1]} 0.5); radius {R:g}; }}")
            # the cylinder has flat ends: round them off as the capsule is
            for c in (a0, a1):
                acts.append(f"{{ name {who}Upper; type cellSet; action add; source sphereToCell; origin ({c[0]} {c[1]} 0.5); radius {R:g}; }}")
    acts.append(f"{{ name {who}Skin; type cellSet; action new; source patchToCell; patches ({who}); }}")
    acts.append(f"{{ name {who}Skin; type cellSet; action subset; source cellToCell; sets ({who}Upper); }}")
    for a0, a1, r in ph.SEATS:
        R = r + ph.SEAT_GAP
        acts.append(f"{{ name {who}Skin; type cellSet; action subtract; source cylinderToCell; "
                    f"p1 ({a0[0]} {a0[1]} 0.5); p2 ({a1[0]} {a1[1]} 0.5); radius {R:g}; }}")
        for c in (a0, a1):
            acts.append(f"{{ name {who}Skin; type cellSet; action subtract; source sphereToCell; origin ({c[0]} {c[1]} 0.5); radius {R:g}; }}")
    bx, by = ph.BREATH[who]
    acts.append(f"{{ name {who}Breath; type cellSet; action new; source sphereToCell; origin ({bx:.4f} {by:.4f} 0.5); radius {ph.BREATH_R:g}; }}")
    return acts


write("system/topoSetDict", "dictionary", "actions\n(\n    { name occupantCells; type cellSet; action new; source patchToCell; patches (driver passenger); }\n"
      + "".join(f"    {s}\n" for who in ("driver", "passenger") for s in upper_actions(who)) + ");\n")
write("system/decomposeParDict", "dictionary", f"numberOfSubdomains {a.ranks};\nmethod scotch;\n")

# the `walls` function object's C++: the parameters are written in as constants
names = " ".join(f'"{n}"' for n, *_ in NODES)
caps = ", ".join(f"{c:.6g}" for _, c, _, _, _ in NODES)
routs = ", ".join(f"{r:.6g}" for _, _, r, _, _ in NODES)
wets = ", ".join("true" if w else "false" for _, _, _, w, _ in NODES)
t0s = ", ".join(f"{t:.6g}" for *_, t in NODES)
walls_fo = f"""
    // each screen and trim face's temperature, and the screens' film of water (see make_case.py)
    walls
    {{
        type            coded;
        libs            (utilityFunctionObjects);
        name            wallNodes;
        writeControl    writeTime;
        codeInclude
        #{{
            #include "turbulentFluidThermoModel.H"
            #include "mixedFvPatchFields.H"
            #include "OFstream.H"
            #include "IFstream.H"
            #include "OSspecific.H"
        #}};
        codeOptions
        #{{
            -I$(LIB_SRC)/finiteVolume/lnInclude \\
            -I$(LIB_SRC)/meshTools/lnInclude \\
            -I$(LIB_SRC)/TurbulenceModels/turbulenceModels/lnInclude \\
            -I$(LIB_SRC)/TurbulenceModels/compressible/lnInclude \\
            -I$(LIB_SRC)/thermophysicalModels/basic/lnInclude \\
            -I$(LIB_SRC)/transportModels/compressible/lnInclude
        #}};
        codeLibs
        #{{
            -lfiniteVolume -lmeshTools -lturbulenceModels -lcompressibleTurbulenceModels \\
            -lfluidThermophysicalModels
        #}};
        codeData
        #{{
            wordList names_;
            labelList ids_;
            scalarList C_, Rout_;
            boolList wet_;
            List<scalarField> Tg_, mf_;
            label nCall_ = 0;
            autoPtr<OFstream> log_;
            // the surfaces the section does not hold: hidTsg hidTdr hidTct hidFilm (state, written),
            // hidQsg hidQdr hidQct hidMsg (what the sources took this step), hidASg hidADr hidCCt (where)
            PtrList<volScalarField> hid_;
            // the latent heat of this step's saturation adjustment, J/m3, for hiddenHeat's next h equation
            autoPtr<volScalarField> Elat_;
            scalar mistCond_ = 0, supMax_ = 0, supExcess_ = 0;

            static scalar wSat(const scalar T, const scalar p)
            {{
                const scalar t = T - 273.15;
                const scalar e = 611.21*::exp((18.678 - t/234.5)*(t/(257.14 + t)));
                return 0.622*e/(p - 0.378*e);
            }}
        #}};
        codeRead
        #{{
            if (ids_.size()) return true;
            const fvMesh& m = mesh();
            names_ = wordList({{{names.replace('" "', '", "')}}});
            C_ = scalarList({{{caps}}});
            Rout_ = scalarList({{{routs}}});
            wet_ = boolList({{{wets}}});
            const scalarList T0({{{t0s}}});
            ids_.setSize(names_.size());
            Tg_.setSize(names_.size());
            mf_.setSize(names_.size());
            forAll(names_, i)
            {{
                ids_[i] = m.boundaryMesh().findPatchID(names_[i]);
                if (ids_[i] < 0) FatalErrorInFunction << "no patch " << names_[i] << exit(FatalError);
                const label n = m.boundaryMesh()[ids_[i]].size();
                Tg_[i] = scalarField(n, T0[i]);
                mf_[i] = scalarField(n, wet_[i] ? {a.film:.8g} : 0.0);
            }}
            const fileName f(m.time().timePath()/"wallState");
            if (isFile(f))
            {{
                IFstream is(f);
                forAll(names_, i) {{ is >> Tg_[i] >> mf_[i]; }}
                Info<< "walls: state read from " << f << endl;
            }}
            else
            {{
                Info<< "walls: starting state, film {a.film:.6g} kg/m2" << endl;
            }}
            const wordList hn({{"hidTsg", "hidTdr", "hidTct", "hidFilm", "hidQsg", "hidQdr", "hidQct", "hidMsg",
                                "hidASg", "hidADr", "hidCCt"}});
            const scalarList h0({{{ph.TS0_GLASS:.8g}, {ph.TS0_DOOR:.8g}, {ph.T0:.8g}, {a.film:.8g}, 0, 0, 0, 0}});
            const dimensionSet hd[8] = {{dimTemperature, dimTemperature, dimTemperature, dimMass/dimArea,
                                        dimPower/dimVolume, dimPower/dimVolume, dimPower/dimVolume, dimDensity/dimTime}};
            hid_.setSize(hn.size());
            bool restarted = false;
            forAll(hn, k)
            {{
                if (k >= 8)
                {{
                    // where each surface is, from setup_fields.py: always read from 0/
                    hid_.set(k, new volScalarField(IOobject(hn[k], "0", m, IOobject::MUST_READ, IOobject::NO_WRITE), m));
                    continue;
                }}
                IOobject io(hn[k], m.time().timeName(), m, IOobject::MUST_READ, k < 4 ? IOobject::AUTO_WRITE : IOobject::NO_WRITE);
                if (k < 4 && io.typeHeaderOk<volScalarField>(true))
                {{
                    hid_.set(k, new volScalarField(io, m));
                    restarted = true;
                }}
                else
                {{
                    io.readOpt(IOobject::NO_READ);
                    hid_.set(k, new volScalarField(io, m, dimensionedScalar(hd[k], h0[k])));
                }}
            }}
            if (!restarted)
            {{
                hid_[3].primitiveFieldRef() *= pos(hid_[8].primitiveField() - SMALL);   // film on side glass only
            }}
            Elat_.reset(new volScalarField(IOobject("hidElat", m.time().timeName(), m, IOobject::NO_READ, IOobject::NO_WRITE),
                                           m, dimensionedScalar(dimEnergy/dimVolume, Zero)));
            Info<< "walls: hidden surfaces " << (restarted ? "read" : "started") << ", side glass "
                << gSum(hid_[8].primitiveField()*m.V()) << " m2, doors " << gSum(hid_[9].primitiveField()*m.V())
                << " m2, contents " << gSum(hid_[10].primitiveField()*m.V()) << " J/K" << endl;
        #}};
        codeExecute
        #{{
            const fvMesh& m = mesh();
            if (!m.foundObject<volScalarField>("w")) return true;
            const Time& rt = m.time();
            const scalar dt = rt.deltaTValue();
            const volScalarField& T = m.lookupObject<volScalarField>("T");
            const volScalarField& w = m.lookupObject<volScalarField>("w");
            const volScalarField& p = m.lookupObject<volScalarField>("p");
            const auto& turb = m.lookupObject<compressible::turbulenceModel>(turbulenceModel::propertiesName);
            volScalarField& Tw = const_cast<volScalarField&>(T);
            volScalarField& ww = const_cast<volScalarField&>(w);
            const bool first = (nCall_++ == 0);

            // the surfaces the section does not hold get what hiddenHeat and sideGlass took from the air
            scalarField& Tsg = hid_[0].primitiveFieldRef();
            scalarField& Tdr = hid_[1].primitiveFieldRef();
            scalarField& Tct = hid_[2].primitiveFieldRef();
            scalarField& film = hid_[3].primitiveFieldRef();
            const scalarField& Qsg = hid_[4].primitiveField();
            const scalarField& Qdr = hid_[5].primitiveField();
            const scalarField& Qct = hid_[6].primitiveField();
            const scalarField& Msg = hid_[7].primitiveField();
            const scalarField& aSg = hid_[8].primitiveField();
            const scalarField& aDr = hid_[9].primitiveField();
            const scalarField& cCt = hid_[10].primitiveField();
            if (!first)
            {{
                forAll(Tsg, c)
                {{
                    if (aSg[c] > 0)
                    {{
                        film[c] = max(film[c] + dt*Msg[c]/aSg[c], 0.0);
                        const scalar Lv = 2.501e6 - 2370.0*(Tsg[c] - 273.15);
                        Tsg[c] += dt*((Qsg[c] + Lv*Msg[c])/aSg[c] - (Tsg[c] - {ph.T_OUT:.6g})/{ph.R_SIDEGLASS:.8g})/{ph.C_SIDEGLASS:.8g};
                    }}
                    if (aDr[c] > 0)
                    {{
                        Tdr[c] += dt*(Qdr[c]/aDr[c] - (Tdr[c] - {ph.T_OUT:.6g})/{ph.R_DOOR:.8g})/{ph.C_DOOR:.8g};
                    }}
                    if (cCt[c] > 0)
                    {{
                        Tct[c] += dt*Qct[c]/cCt[c];
                    }}
                }}
            }}

            // per node patch: area, misted area, film mass, heat in from the air, vapour taken
            scalarList A(ids_.size(), 0), Am(ids_.size(), 0), M(ids_.size(), 0), Qa(ids_.size(), 0),
                       Mc(ids_.size(), 0), TA(ids_.size(), 0);
            forAll(ids_, i)
            {{
                const label pi = ids_[i];
                const fvPatch& fp = m.boundary()[pi];
                const scalarField& dc = fp.deltaCoeffs();
                const scalarField& mag = fp.magSf();
                const scalarField kEff(turb.kappaEff(pi));
                const scalarField qAir(kEff*(T.boundaryField()[pi].patchInternalField() - T.boundaryField()[pi])*dc);
                scalarField mCond(fp.size(), 0.0);
                if (wet_[i])
                {{
                    const scalarField Deff({ph.ALPHA_D:.8g}*turb.mu(pi) + {ph.ALPHA_DT:.8g}*turb.mut(pi));
                    mCond = Deff*(w.boundaryField()[pi].patchInternalField() - w.boundaryField()[pi])*dc;
                }}
                if (!first)
                {{
                    forAll(Tg_[i], f)
                    {{
                        scalar mc = mCond[f];
                        if (wet_[i])
                        {{
                            scalar mn = mf_[i][f] + mc*dt;
                            if (mn < 0) {{ mc = -mf_[i][f]/dt; mn = 0; }}
                            mf_[i][f] = mn;
                        }}
                        const scalar Lv = 2.501e6 - 2370.0*(Tg_[i][f] - 273.15);
                        const scalar qOut = Rout_[i] > 0 ? (Tg_[i][f] - {ph.T_OUT:.6g})/Rout_[i] : 0;
                        Tg_[i][f] += dt*(qAir[f] + Lv*mc - qOut)/C_[i];
                    }}
                }}
                Tw.boundaryFieldRef()[pi] == Tg_[i];
                if (wet_[i])
                {{
                    auto& wp = refCast<mixedFvPatchScalarField>(ww.boundaryFieldRef()[pi]);
                    const scalarField pp(p.boundaryField()[pi]);
                    const scalarField wc(w.boundaryField()[pi].patchInternalField());
                    forAll(Tg_[i], f)
                    {{
                        const scalar ws = wSat(Tg_[i][f], pp[f]);
                        wp.refValue()[f] = ws;
                        wp.refGrad()[f] = 0;
                        wp.valueFraction()[f] = (mf_[i][f] > 0 || wc[f] > ws) ? 1 : 0;
                    }}
                    wp.evaluate();
                }}
                A[i] = sum(mag);
                Am[i] = sum(mag*pos(mf_[i] - {ph.FILM_CLEAR:g}));
                M[i] = sum(mag*mf_[i]);
                Qa[i] = sum(mag*qAir);
                Mc[i] = sum(mag*mCond);
                TA[i] = sum(mag*Tg_[i]);
            }}
            // mist: vapour above saturation after this step's transport condenses at once, and mist evaporates
            // where the air is below saturation, each limited by the latent heat it gives or takes
            // (dq = excess/(1 + Lv/cp dws/dT)). The heat goes to the air in the next h equation (hidElat).
            volScalarField& LL = const_cast<volScalarField&>(m.lookupObject<volScalarField>("L"));
            {{
                const scalarField& Tc = T.primitiveField();
                const scalarField& pc = p.primitiveField();
                const scalarField& rc = m.lookupObject<volScalarField>("rho").primitiveField();
                const scalarField& Vc = m.V();
                scalarField& wc = ww.primitiveFieldRef();
                scalarField& Lc = LL.primitiveFieldRef();
                scalarField& E = Elat_->primitiveFieldRef();
                mistCond_ = 0; supMax_ = -GREAT; supExcess_ = 0;
                forAll(wc, c)
                {{
                    const scalar ws = wSat(Tc[c], pc[c]);
                    const scalar Lv = 2.501e6 - 2370.0*(Tc[c] - 273.15);
                    const scalar gam = Lv/{ph.CP_AIR:g}*ws*Lv/({ph.R_VAP:g}*sqr(Tc[c]));
                    supMax_ = max(supMax_, wc[c]/ws - 1);
                    supExcess_ += rc[c]*Vc[c]*max(wc[c] - ws, 0.0);
                    scalar dq = (wc[c] - ws)/(1 + gam);
                    if (dq < 0) dq = max(dq, -Lc[c]);
                    wc[c] -= dq;
                    Lc[c] = max(Lc[c] + dq, 0.0);
                    E[c] = rc[c]*Lv*dq;
                    mistCond_ += rc[c]*Vc[c]*dq;
                }}
                mistCond_ /= dt;
            }}
            // recirculation: the heater evaporates the mist it draws in, so its air carries the intake's water
            {{
                const label ri = m.boundaryMesh().findPatchID("recirc");
                const label di = m.boundaryMesh().findPatchID("defrost");
                if (ri >= 0 && di >= 0 && m.boundaryMesh()[ri].type() != "wall")
                {{
                    const surfaceScalarField& phi0 = m.lookupObject<surfaceScalarField>("phi");
                    const scalarField& pr = phi0.boundaryField()[ri];
                    const scalar F0 = gSum(pr);
                    const scalar Fq = gSum(pr*(w.boundaryField()[ri].patchInternalField() + LL.boundaryField()[ri].patchInternalField()));
                    if (F0 > SMALL) ww.boundaryFieldRef()[di] == Fq/F0;
                }}
            }}
            ww.correctBoundaryConditions();
            LL.correctBoundaryConditions();

            if (nCall_ % 20 != 1) return true;
            forAll(A, i)
            {{
                reduce(A[i], sumOp<scalar>()); reduce(Am[i], sumOp<scalar>()); reduce(M[i], sumOp<scalar>());
                reduce(Qa[i], sumOp<scalar>()); reduce(Mc[i], sumOp<scalar>()); reduce(TA[i], sumOp<scalar>());
            }}
            // the cabin's vapour and heat, and what crosses the openings
            const volScalarField& rho = m.lookupObject<volScalarField>("rho");
            const surfaceScalarField& phi = m.lookupObject<surfaceScalarField>("phi");
            scalar Mv = gSum(rho.primitiveField()*w.primitiveField()*m.V());
            const scalar Ml = gSum(rho.primitiveField()*LL.primitiveField()*m.V());
            const scalar mistCond = returnReduce(mistCond_, sumOp<scalar>());
            const scalar supMax = returnReduce(supMax_, maxOp<scalar>());
            const scalar supExcess = returnReduce(supExcess_, sumOp<scalar>());
            const scalar Lmax = gMax(LL.primitiveField());
            scalar Tm = gSum(rho.primitiveField()*T.primitiveField()*m.V())/gSum(rho.primitiveField()*m.V());
            // the air within 0.15 m of the two heads (Brusey et al.'s sensors were at head-rest height)
            const vectorField& cc = m.C().primitiveField();
            const scalarField head
            (
                pos(0.255 - mag(cc - vector(1.405, 1.005, 0.5)))
              + pos(0.25 - mag(cc - vector(2.185, 1.02, 0.5)))
            );
            const scalar Th = gSum(head*T.primitiveField()*m.V())/max(gSum(head*m.V()), SMALL);
            // the surfaces the section does not hold: heat taken (W), mean temperature, the side glass's film
            const scalarField& V = m.V();
            const scalar Asg = gSum(aSg*V), Adr = gSum(aDr*V), Cct = gSum(cCt*V);
            const scalar hq[3] = {{gSum(Qsg*V), gSum(Qdr*V), gSum(Qct*V)}};
            const scalar hT[3] = {{gSum(aSg*V*Tsg)/max(Asg, SMALL), gSum(aDr*V*Tdr)/max(Adr, SMALL),
                                  gSum(cCt*V*Tct)/max(Cct, SMALL)}};
            const scalar sgFilm = gSum(aSg*V*film), sgCond = gSum(Msg*V);
            const scalar sgMisted = gSum(aSg*V*pos(film - {ph.FILM_CLEAR:g}))/max(Asg, SMALL);
            const wordList op({{"defrost", "recirc", "rearVent"}});
            scalarList F(3, 0), FW(3, 0), FT(3, 0), FL(3, 0);
            forAll(op, k)
            {{
                const label pi = m.boundaryMesh().findPatchID(op[k]);
                if (pi < 0) continue;
                F[k] = gSum(phi.boundaryField()[pi]);
                FW[k] = gSum(phi.boundaryField()[pi]*w.boundaryField()[pi]);
                FL[k] = gSum(phi.boundaryField()[pi]*LL.boundaryField()[pi]);
                FT[k] = gSum(phi.boundaryField()[pi]*T.boundaryField()[pi])/(mag(F[k]) > SMALL ? F[k] : SMALL);
            }}
            if (Pstream::master())
            {{
                if (!log_)
                {{
                    const fileName dir(rt.globalPath()/"postProcessing"/"walls"/rt.timeName());
                    mkDir(dir);
                    log_.reset(new OFstream(dir/"walls.dat"));
                    log_() << "# t";
                    forAll(names_, i)
                    {{
                        log_() << " " << names_[i] << "_misted " << names_[i] << "_film_kg "
                               << names_[i] << "_Tmean " << names_[i] << "_Qair_W " << names_[i] << "_cond_kg_s";
                    }}
                    log_() << " cabin_vapour_kg cabin_Tmean defrost_kg_s defrost_vap_kg_s defrost_T recirc_kg_s"
                           << " recirc_vap_kg_s recirc_T vent_kg_s vent_vap_kg_s vent_T head_T"
                           << " sideglass_Qair_W door_Qair_W contents_Qair_W sideglass_Tmean door_Tmean contents_Tmean"
                           << " sideglass_misted sideglass_film_kg sideglass_cond_kg_s"
                           << " cabin_mist_kg mist_cond_kg_s defrost_mist_kg_s recirc_mist_kg_s vent_mist_kg_s"
                           << " supersat_max_before supersat_excess_kg_before mist_max" << nl;
                }}
                log_() << rt.timeOutputValue();
                forAll(names_, i)
                {{
                    log_() << " " << Am[i]/A[i] << " " << M[i] << " " << TA[i]/A[i] - 273.15 << " " << Qa[i] << " " << Mc[i];
                }}
                log_() << " " << Mv << " " << Tm - 273.15;
                forAll(op, k) {{ log_() << " " << F[k] << " " << FW[k] << " " << FT[k] - 273.15; }}
                log_() << " " << Th - 273.15;
                for (label k = 0; k < 3; ++k) {{ log_() << " " << hq[k]; }}
                for (label k = 0; k < 3; ++k) {{ log_() << " " << hT[k] - 273.15; }}
                log_() << " " << sgMisted << " " << sgFilm << " " << sgCond;
                log_() << " " << Ml << " " << mistCond << " " << FL[0] << " " << FL[1] << " " << FL[2]
                       << " " << supMax << " " << supExcess << " " << Lmax;
                log_() << nl;
                log_().flush();
            }}
        #}};
        codeWrite
        #{{
            const fvMesh& m = mesh();
            const Time& rt = m.time();
            {{
                mkDir(rt.timePath());
                OFstream os(rt.timePath()/"wallState");
                forAll(names_, i) {{ os << Tg_[i] << nl << mf_[i] << nl; }}
            }}
            // the screens face by face, for the clip: centre x y, temperature C, film kg/m2
            forAll(names_, i)
            {{
                if (!wet_[i]) continue;
                const fvPatch& fp = m.boundary()[ids_[i]];
                List<scalarField> X(Pstream::nProcs()), Y(Pstream::nProcs()), Tl(Pstream::nProcs()), Ml(Pstream::nProcs());
                X[Pstream::myProcNo()] = fp.Cf().component(0);
                Y[Pstream::myProcNo()] = fp.Cf().component(1);
                Tl[Pstream::myProcNo()] = Tg_[i];
                Ml[Pstream::myProcNo()] = mf_[i];
                Pstream::gatherList(X); Pstream::gatherList(Y); Pstream::gatherList(Tl); Pstream::gatherList(Ml);
                if (Pstream::master())
                {{
                    const fileName dir(rt.globalPath()/"postProcessing"/"glass"/rt.timeName());
                    mkDir(dir);
                    OFstream os(dir/(names_[i] + ".dat"));
                    os << "# x y T_C film_kg_m2" << nl;
                    forAll(X, pr) forAll(X[pr], f)
                    {{
                        os << X[pr][f] << " " << Y[pr][f] << " " << Tl[pr][f] - 273.15 << " " << Ml[pr][f] << nl;
                    }}
                }}
            }}
        #}};
    }}"""

write("system/controlDict", "dictionary", f"""application     buoyantPimpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {a.end:g};
deltaT          1e-4;
adjustTimeStep  yes;
maxCo           2;
maxDeltaT       0.01;
writeControl    adjustableRunTime;
writeInterval   {a.write:g};
purgeWrite      2;              // full fields: the last two only; the clip is the planes
writeFormat     binary;
writePrecision  10;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable false;        // re-reading a running controlDict has killed such runs
DebugSwitches   {{ lduMatrix 0; }}  // no residual lines: about 500,000 steps would fill the log
functions
{{
    // the water vapour, solved after each step with the step's mass flux
    w
    {{
        type            scalarTransport;
        libs            (solverFunctionObjects);
        field           w;
        phi             phi;
        rho             rho;
        alphaD          {ph.ALPHA_D:.8g};      // D rho = mu/Sc, Sc = 0.60 (vapour in air)
        alphaDt         {ph.ALPHA_DT:.8g};     // + mut/0.85
        schemesField    w;
        nCorr           0;
        resetOnStartUp  false;
        writeControl    writeTime;
        log             false;
        fvOptions
        {{
{OCC_SOURCES}{SIDE_VAPOUR}
        }}
    }}
    // the mist, carried by the same mass flux; droplets have no molecular diffusion to speak of
    mist
    {{
        type            scalarTransport;
        libs            (solverFunctionObjects);
        field           L;
        phi             phi;
        rho             rho;
        alphaD          0;
        alphaDt         {ph.ALPHA_DT:.8g};
        schemesField    L;
        nCorr           0;
        resetOnStartUp  false;
        writeControl    writeTime;
        log             false;
    }}{walls_fo}
    // the clip: the whole section, cell values, every write
    clip
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    writeTime;
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U w L);
        surfaces
        {{
            section {{ type cuttingPlane; point (0 0 0.5); normal (0 0 1); interpolate false; }}
        }}
    }}
    minMax
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        fields          (T U w L);
        log             false;
    }}
}}
""")

wall_list = " ".join(f"{n} {{ type wall; }}" for n in ("windscreen", "rearScreen", "roof", "trim", "driver", "passenger"))
write("system/changeDictionaryDict", "dictionary", f"""boundary
{{
    {wall_list}
    recirc {{ type {'patch' if REC else 'wall'}; }}
    defrost {{ type patch; }}
    rearVent {{ type patch; }}
    frontAndBack {{ type empty; }}
}}
""")

for fn in ("geometry.py", "make_mesh.py", "physics.py", "setup_fields.py"):
    shutil.copy(os.path.join(HERE, fn), C)
# The run's Allrun: mesh, fields and decomposition; given `solve`, the solve. It expects the
# OpenFOAM environment and a Python with gmsh in $PYTHON (default python3). Planes are gzipped
# as they come (all but the newest), and the rest when the solver ends.
allrun = f"""#!/bin/bash
# {V}: written by scripts/make_case.py
#   ./Allrun                 mesh, fields, checkMesh, decomposePar
#   ./Allrun solve [cpu-set] the same, then buoyantPimpleFoam on {a.ranks} ranks (from the latest time)
. $WM_PROJECT_DIR/bin/tools/RunFunctions
set -e
cd "${{0%/*}}"
PYTHON=${{PYTHON:-python3}}
if [ ! -f constant/polyMesh/owner ]; then
    $PYTHON make_mesh.py geometry.json mesh.msh {a.mesh_scale:g} > log.gmsh 2>&1
    runApplication gmshToFoam mesh.msh
    rm -f mesh.msh
    runApplication changeDictionary -constant
    runApplication checkMesh
fi
if [ ! -d processor0 ]; then
    rm -rf 0 && cp -r 0.orig 0
    runApplication topoSet
    runApplication postProcess -funcs "(writeCellCentres writeCellVolumes)" -time 0
    python3 setup_fields.py > log.setupFields 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz 0/V
    runApplication decomposePar
fi
[ "${{1:-}}" = solve ] || exit 0
CPUS=${{2:-}}
gzip_planes() {{
    for d in postProcessing/clip/*/; do
        [ -d "$d" ] || continue
        newest=$(ls -d postProcessing/clip/*/ | sort -t/ -k3 -g | tail -1)
        if [ "$d" != "$newest" ] && [ -f "$d/section.vtp" ]; then gzip -f "$d/section.vtp"; fi
    done || true
}}
( while sleep 30; do gzip_planes; done ) &
LOOP=$!
if [ -n "$CPUS" ]; then
    mpirun -np {a.ranks} --cpu-set "$CPUS" --bind-to core buoyantPimpleFoam -parallel > log.buoyantPimpleFoam 2>&1 || status=$?
else
    mpirun -np {a.ranks} buoyantPimpleFoam -parallel > log.buoyantPimpleFoam 2>&1 || status=$?
fi
kill $LOOP 2>/dev/null || true
for f in postProcessing/clip/*/section.vtp; do [ -f "$f" ] && gzip -f "$f"; done || true
exit ${{status:-0}}
"""
with open(os.path.join(C, "Allrun"), "w") as f:
    f.write(allrun)
os.chmod(os.path.join(C, "Allrun"), 0o755)
with open(os.path.join(C, "caseInfo"), "w") as f:
    f.write(f"variant {V}\nmesh_scale {a.mesh_scale}\nfilm {a.film}\ncontents_x {a.contents_x}\ncontents_zone {a.contents_zone}\n")
print(f"{V}: {C}, end {a.end:g} s, write {a.write:g} s, {a.ranks} ranks, film {a.film * 1e3:g} g/m2, "
      f"supply {ph.T_SUP_OUT - ph.C2K:.1f} C (outside air), {ph.MDOT:.5f} kg/s per m, "
      f"occupants {Q_DRIVER:.2f}/{Q_PASS:.2f} W/m2")
