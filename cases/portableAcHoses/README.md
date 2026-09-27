# Portable AC: one hose or two?

One OpenFOAM case, run two ways: the same portable air conditioner in the same room, with
its condenser fed by one hose or by two. `./Allrun single` and `./Allrun dual` differ only
in that argument.

## The question

A portable AC blows the heat it removes outdoors through a hose. A single-hose unit takes
that air from the room, so every cubic metre it blows out has to be replaced, and the
replacement leaks in through the gaps under the door and around the window bracket, at
outdoor temperature. A dual-hose unit brings most of its condenser air in from outdoors
through a second hose, so much less has to leak in.

The question is narrow on purpose: **where does the replacement air come from, and what
does it do to the room?** Not the unit's efficiency rating.

## The evidence the setup rests on

From the US Department of Energy's test procedure for portable air conditioners (10 CFR 430
Subpart B, Appendix CC) and the measurements DOE published while writing it (Notice of Data
Availability, docket EERE-2014-BT-TP-0014, May 2014):

- For a single-duct unit, infiltration equals the condenser exhaust. For a dual-duct unit,
  it is the exhaust minus the outdoor intake.
- Measured condenser flows, NODA Table II.7: single-duct units exhausted 254-286 CFM. The
  dual-duct unit **DD1** exhausted 271.9 CFM and took 170.8 CFM from outdoors, a net
  **101.1 CFM** drawn from the room. Dual-hose units are not zero-infiltration.
- At 95 °F infiltration, two of the four single-duct units DOE tested delivered net
  heating to the room (NODA Table II.4).

This case uses DD1 for both configurations, so it is the same machine: 271.9 CFM exhaust.
The single hose takes all of it from the room; the dual hose takes 170.8 CFM from outdoors.

## What the clip shows, and what it does not

**It shows where the heat goes.** The room is coloured by temperature on one scale centred
on the switch-on 26.7 °C, with streamlines through the solved flow. With one hose, outdoor
air comes in at the door and the window bracket and spreads across the room toward the
unit. With two, far less comes in, and the unit's cooling holds more of the room.

**It prints no number.** Here they are, with the reason they carry no verdict:

| | one hose | two hoses |
|---|---|---|
| Replacement air through the gaps | 271.9 CFM | 101.1 CFM |
| Room mean at 150 s, the end of the clip | 27.8 °C | 25.5 °C |
| Room mean at 900 s, a longer run of the same case | 29.0 °C | 26.5 °C |

Both started at 26.7 °C. At 150 s the one-hose room is warmer than when the unit was
switched on, while the two-hose room has cooled; neither is settled. Past about 7 minutes
the dual unit starts cycling on its thermostat, which is why the longer run's figures sit
closer together: see the thermal-mass limit below.

**The energy balance, which needs none of the model's choices.** At a given indoor
temperature, the heat the replacement air brings in is its flow times the temperature
difference (rho 1.2 kg/m3, cp 1005 J/kg K):

| indoor, 35 °C outdoors | one hose | two hoses |
|---|---|---|
| 26.7 °C (DOE's test condition) | 1,284 W, 46% of a 9,500 Btu/h rating | 478 W, 17% |
| 24 °C | 1,702 W, 61% | 633 W, 23% |

DOE measured larger losses, 71-107% of rated capacity for single-duct units, because its
calorimeter also captures duct heat and case leakage.

## The model

- **A plan view.** The 4.00 x 3.00 m room is solved in 2-D, one cell thick, as the plane
  that represents the full 2.5 m height. A flow Q through an opening of plan width w enters
  at Q / (w x 2.5 m). `buoyantBoussinesqPimpleFoam` with gravity zero, since gravity is
  normal to the plane, so temperature is carried by the flow. Standard k-epsilon.
- **The unit** is a 0.39 x 0.46 m solid body, the footprint of a 10,000 Btu/h unit,
  standing beside the window with its back 0.51 m from the wall. Its cold supply leaves the
  front face; its two rear grilles, the evaporator return and the condenser intake, sit
  side by side on the back.
- **The supply jet** is 0.30 m wide in plan, the width of a real top louvre, with the real
  outlet's momentum flux: 400 CFM at about 6 m/s, 1.36 N. In a plan view that needs 1.23
  m/s over 0.30 m x 2.5 m, which represents **4.9 times** the real volume flow. The unit
  removes exactly 2.0 kW in both configurations, so the supply comes out only 1.8 K below
  the return, not about 9 K. The jet looks pale for that reason.
- **The leaks** are spread across the 0.9 m door gap on the west wall and the 0.9 m
  window-bracket gap on the north wall, with effective areas 0.0135 and 0.0140 m2. The
  exhaust fixes the total inflow; equal pressure across both cracks fixes the split, 49/51.
  Air only flows in.
- **The room** starts at 26.7 °C, with 35 °C outdoors and a 900 W sensible gain spread
  uniformly through the air. A thermostat at 24 °C with a 180 s restart lockout is in the
  case, but neither unit reaches it inside the 150 s clip.

### Choices that shape the picture, stated once

- **The unit stands beside the window, not in front of it.** With the bracket gap directly
  behind the unit, about two-thirds of the single-hose condenser intake was outdoor air
  straight from the gap, sent back outside without reaching the room. Some of that is real,
  but a plan view cannot separate a gap at window height from a grille low on the unit's
  back, so it overstated it.
- **The door is on the wall opposite the window**, as in most rooms. With both gaps on the
  unit's side, the replacement air took a short path to the condenser and never crossed the
  room.
- **The heat gain is uniform.** Over a 150 s window a uniform 900 W can raise a completely
  stagnant cell by only about 4.4 K. Concentrating it along the walls heated cells there past
  the outdoor temperature.

## Verified: the supply jet

The jet decides the room's circulation, so it was checked on its own before going into the
room: the same outlet, turbulence model, schemes and inlet treatment, blowing into a large
quiet domain, against the plane-jet law (centreline Um/U0 = 2.4 sqrt(b/x), half-width 0.10x).
Over the developed 2-3 m, centreline velocity is within 13% and half-width within 10%. A
medium mesh changes the 3 m values by 2-4% from the coarse one used here.
`validation/freejet_generate.py` builds it; `validation/freejet_verification.csv` has the
comparison.

## Limits, which are the part worth reading

- **A plan view has no height.** There is no stratification: hot air cannot rise and cold
  air cannot sink. The grilles cannot be at different heights. Every opening is
  floor-to-ceiling. A real room mixes more than this one, and the sharp boundaries between
  warm and cool regions here are sharper than a real room's.
- **The jet is momentum-matched, not volume-matched.** Its throw and the circulation it
  drives are right; its volume is 4.9 times too high and its temperature drop 5 times too
  small. The unit's own return draws air several kelvin colder than the room mean, because
  that inflated flow recirculates tightly around the unit.
- **The dual-hose jet swings** from side to side on a cycle of about 40 s. Confined 2-D jets
  do this more coherently than real ones, because nothing in the third dimension breaks the
  motion up.
- **The room has only the air's heat capacity.** No walls, floor or furniture store heat. Past
  the first thermostat stop, which the dual unit reaches at about 7.4 minutes in the longer
  run, the room swings several kelvin during each lockout. A furnished room would not. The
  clip ends well before that.
- **One mesh, one turbulence model**, apart from the free-jet check above. No grid
  convergence study of the room.
- **The unit is prescribed flows and a fixed 2 kW**, not a refrigeration cycle. It does not
  lose capacity as its condenser air gets hotter, which a real unit does.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it, and Python 3.

```sh
cd cases/portableAcHoses
./Allrun single      # or: ./Allrun dual
```

`Allrun` writes `run_<mode>/` from `config.py` via `generate_case.py`: blockMesh, fields,
dictionaries. It then checks the mesh and solves from switch-on to 150 s, writing 481
states. Each takes about ten minutes on one core. It is serial on purpose: at about 5,200
cells a parallel run is slower. `./Allclean` removes the runs.

The thermostat lives in a coded boundary condition on the supply and keeps its state in
static variables. **Always run from switch-on:** a restart from a written time resets the
thermostat to cooling-on.

The case was set up by an agent and checked by us, over a first build and a series of
corrections. The layout choices and limits above record what those corrections found.
