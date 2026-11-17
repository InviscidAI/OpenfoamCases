# An air curtain over an open shop door in winter, off against on

Many shops leave the front door open in winter and run an air curtain over it: a fan unit on the inside wall above
the door that blows a flat sheet of air down across the opening. One camp calls it money blown on people's heads: "in
reality I think it's a large expense for little reward" (DIYnot forum, 2024), "it's surely a ruinously expensive way of
keeping your shoppers inside?" and "satisfying people psychologically, despite the inefficiency!" (PistonHeads forum,
2012). The makers say it works: "a correctly installed air curtain can reduce energy losses at an open door by up to
80%" (Frico), and air curtains "are between 70%-80% effective in minimizing energy loss" (Mars Air Systems). This case
opens the same shop door on a still, freezing day twice, once with the curtain off and once with it on, and asks how
much of the cold outdoor air gets into the shop in the first minute, and how cold the air gets at ankle height just
inside the door. It is about the air through the door, not the heating bill.

    ./Allrun off     # the curtain unit there but not running, 0-60 s from the door opening
    ./Allrun on      # the curtain blowing from the moment the door opens, 0-60 s

**The result.** **With the curtain off, the cold air pours in along the floor and the warm air leaves over the top of
the door; with it on, most of the cold stays in the street.** The ankle air in the first 3 m inside the door (0-0.3 m
up) is at 32.1 °F (0.04 °C) by 10 s with the curtain off, the front of the cold current, and stays there; with it on it
holds at 57.7-61.1 °F (14.3-16.2 °C) from 2 s to 30 s and ends at 53.8 °F (12.12 °C) at 60 s. Counted by the tracer
that marks the outdoor air, the shop holds 21.0 kg of it at 30 s with the curtain off and 4.72 kg with it on, per metre
of door width: **the curtain kept out 78% of the outdoor air that came in without it at 30 s, and 64% at 60 s**, inside
the "up to approximately 80%" that the literature gives for a curtain in still air. The share falls after 30 s because
the off shop is by then full of cold air almost to the ceiling and stops taking more in; a real, wider shop would not
fill, so the 30 s figure is the closer one. Read [What it cannot](#what-it-cannot) before any number here: **the
curtain is a typical one, not a code-compliant one** (its jet reaches the floor at 1.0-1.3 m/s, not the 2.0 m/s the
code asks for), **the shop is as wide as its door**, so it floods far faster than a real one, and **nothing here says
what happens to the bill**.

The section, the curtain and the outdoor-air tracer are new. The buoyant model, buoyantPimpleFoam with k-ω SST and
buoyancy production, is the one our room cases use ([`acLouvreAngle`](../acLouvreAngle),
[`doorwayFanStove`](../doorwayFanStove)), and `template/system/fvSolution` keeps
[`radiatorUnderWindow`](../radiatorUnderWindow)'s notes. [`windowAiring`](../windowAiring) is the other case of cold air
through an opening.

## The doorway

A vertical section through the middle of the door, seen from the side, one cell (1 m) deep: every figure here is per
metre of door width. x runs from the façade's outer face into the shop, y up from the pavement and the floor; metres.

| | where | |
|---|---|---|
| street | x -5.0 to 0, y 0 to 6.0 | still air at 0 °C (32 °F); open at x = -5 (`street`) and y = 6 (`sky`); the pavement a wall |
| façade | x = 0, y 2.2 to 6.0 | a wall above the door |
| door | x 0 to 0.2, y 0 to 2.2 | an opening 2.2 m tall through a 0.2 m front wall; no door leaf, it is simply open at t = 0 |
| shop | x 0.2 to 8.2, y 0 to 3.2 | 8 m deep, 3.2 m to the ceiling, closed at the back, no other opening; air at 20 °C (68 °F) |
| curtain unit | x 0.20 to 0.50, y 2.25 to 2.50 | a box 0.30 m deep and 0.25 m tall on the inside wall above the door, its underside 5 cm above the door head |
| slot | x 0.21 to 0.27, y = 2.25 | the unit's underside, 6 cm wide |
| intake | x = 0.50, y 2.27 to 2.48 | the unit's face to the room, 21 cm tall |

**off**: the unit hangs there with its slot and intake walls like the rest of it. **on**: from t = 0, switched on with
the door, as door-contact units are, the slot blows a fixed 6 m/s, (-2.0521, -5.6382) m/s, aimed 20° from the vertical
out towards the street, 0.33829 m³/s per metre (1,218 m³/h per metre), with k from 5% intensity and ω from a 6 mm
mixing length. The intake draws the same 0.33829 m³/s (`flowRateOutletVelocity`), and the slot's temperature and tracer
are the intake's mean (`outletMappedUniformInlet`), so the jet is the shop's own air, recirculated and unheated. Most UK
and European shop units are heated; this one is not.

**The start.** Both runs start at rest at t = 0, when the door opens: the air at 0 °C and the tracer at 1 for
x < 0.1 m (the street and the outer half of the doorway), at 20 °C and 0 in the shop. Each side is hydrostatic, the
two pressures equal at y = 1.1 m, the door's mid-height, on the cells and on every boundary face, and the face flux is
zero; the first step is 0.1 ms. The open boundaries carry the street's hydrostatic total pressure face by face
(`prghTotalPressure`); air that comes in through them is at 0 °C with tracer 1. Every wall is no-slip and adiabatic.

**The outdoor-air tracer** (`outdoor`, a `scalarTransport` function object) is 1 in the outdoor air and 0 in the
shop's, carried by the mass flux with the same diffusivity as the temperature: alphaD 1/0.71 for the laminar part
and alphaDt 1.0, because the bulk turbulent Prandtl number of SST in v2512 is 1.0 (the wall functions' Prt 0.85 is
theirs only). The shop's outdoor air is the integral of ρ times the tracer over the shop, x > 0.2 m.

**The numbers.** The ankle air is the volume mean of the air temperature over x 0.2-3.2 m, y 0-0.3 m, the first 3 m
inside the door (partial cells weighted by the share of their volume inside). The curtain's share is
E = 1 - M_on / M_off, M the shop's outdoor air at the same time.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71, the sensible enthalpy referenced at 20 °C), k-ω SST with `buoyancyTurbSource` and wall
functions (`kLowReWallFunction`, `omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction` with
Prt 0.85). Euler in time, adaptive steps at Courant 1 (maxDeltaT 0.02 s), limitedLinearV for U and limitedLinear for h,
the tracer, k and ω. Two outer and two pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100
iterations; the tracer by PBiCGStab to 1e-12. No radiation, no heating, no other sources.

**The mesh** (`scripts/make_mesh.py`): a tensor grid written directly as a polyMesh, with no blockMesh, less the
solid cells of the wall and the unit, 430 x 247 lines, **88,890 hexahedral cells**. Six 1 cm cells across the slot,
1 cm cells down the jet's first metres and five across the 5 cm gap under the unit, cells no larger than
1.52 x 1.90 cm in the doorway, 3.4 cm in the shop to x = 3 m and 4.1 cm beyond, coarsening to 9.5 cm far out in the
street and the sky; neighbouring cells differ in size by at most 7.3% in x and 7.8% in y. `checkMesh` OK, no
non-orthogonality. The patches' areas are what the task set (slot 0.06 m², intake 0.21 m²; `results/mesh.json`). Three
face zones of the door's height, at x = 0, 0.1 and 0.2 m, carry the monitor's door sums. One mesh, no mesh study.

**The monitor** (`template/system/monitor`, a coded function object run at every step, into
`postProcessing/monitor/monitor.csv`): the gross flow each way through the three door lines, the street and the sky
(volume, mass, enthalpy and outdoor air); the shop's outdoor air, near the door and in all, its heat, ∫p dV and the
mean temperatures of the ankle layer, the floor layer, the head height and the whole shop; the neutral level in the
door; the slot's and the intake's flows, temperatures and tracer; the jet's largest downward speed on the line 15 cm
above the floor; and the heat budget's terms, the scheme's own face fluxes and the diffusive flux through the door
included. `courant.csv` keeps the twelve cells of highest Courant number. The `planes` are the whole section, T, U and
the tracer, as point values (`section`) and as cell values (`sectionCells`), every 0.125 s, 481 a run.

## Results

`results/off_summary.csv` and `on_summary.csv` (the ankle, floor-layer, head-height and shop means, the outdoor air,
the shop's heat, the neutral level, the extremes and the jet at 15 cm, at 1-60 s), `effectiveness.csv` (the curtain's
share at 2-60 s, by the outdoor air and by four counts of the heat), `off_gross_flows.csv` and `on_gross_flows.csv`
(each way through the door lines, the street and the sky), `off_heat_budget.csv` and `on_heat_budget.csv`,
`on_curtain.csv` (the slot and the intake) and `mesh.json`.

| ankle air by the door, °F (°C) | 2 s | 5 s | 10 s | 30 s | 60 s |
|---|---:|---:|---:|---:|---:|
| curtain off | 57.6 (14.22) | 34.2 (1.25) | 32.1 (0.04) | 32.1 (0.06) | **32.1 (0.04)** |
| curtain on | 57.7 (14.29) | 58.9 (14.94) | 61.1 (16.18) | 57.7 (14.27) | **53.8 (12.12)** |

| | 5 s | 10 s | 20 s | 30 s | 45 s | 60 s |
|---|---:|---:|---:|---:|---:|---:|
| outdoor air in the shop, off, kg | 3.12 | 6.80 | 14.08 | 21.00 | 22.44 | 23.22 |
| outdoor air in the shop, on, kg | 1.06 | 1.85 | 3.42 | 4.72 | 6.46 | 8.25 |
| **kept out by the curtain** | 66% | 73% | 76% | **78%** | 71% | **64%** |
| the shop's whole mean, off / on, °C | 18.07 / 19.31 | 15.79 / 18.79 | 11.26 / 17.77 | 6.99 / 16.93 | 6.12 / 15.82 | 5.66 / 14.69 |
| at head height (1.5-1.8 m), off / on, °C | 20.00 / 19.84 | 19.96 / 18.66 | 15.93 / 17.61 | 3.52 / 17.05 | 1.61 / 16.16 | 1.02 / 15.26 |

**With the curtain off** the cold air runs in along the floor as a gravity current and its front passes the first 3 m
within about 5 s, at nearly the street's temperature, while the warm air leaves over the top of the door, the neutral
level at 1.15-1.50 m in the door through 30 s. About 0.59 m³/s per metre crosses the door line each way on average over
0-30 s, and 0.16 m³/s over 30-60 s, 0.08 m³/s at 60 s, once the shop is full: by 30 s it is cold to about two thirds
of its height, and by 60 s only a thin warm layer is left under the ceiling.

**With it on** the jet stands across the door from the first second, the cold stays in the street, and the shop turns
over in one large roll, cooling slowly. About 0.39 m³/s crosses the door line each way throughout, most of it the
curtain's own air and the street air it turns back: of the 16.1 kg of outdoor air that crossed the line into the shop
over the minute, the curtain carried 12.2 kg back out (the agent's count from the monitor). The jet bends into the shop as it falls: its foot lands at
x = 0.37 m at 30 s and 0.48 m at 60 s, inside the door's inner face at x = 0.2. Because the intake recirculates the
shop's air, the jet cools with the shop, from 293.15 K to 289.8 K at 30 s and 287.6 K at 60 s, its tracer from 0 to
0.17 and 0.28.

The share kept out is the same counted by heat: at 30 s the shop lost 77.6% less heat with the curtain on, and the
total heat carried through the door, diffusion included, was 77.6% less; at 60 s, 64.7% and 64.6%. A count by the
advected enthalpy alone, with T interpolated linearly to the faces, gives 81.8% and 72.4%, but it leaves out the
scheme's own face values and the turbulent diffusion in the jet's mixing layer, which carry a good part of what crosses
the door with the curtain on (below), and is not the heat saved.

**Checks.** Both runs reached 60 s with a clean `End`. The slot's and the intake's flows were within 0.001% of
0.33829 m³/s from the start, and their temperatures agreed within 0.00015 K. Over 5-60 s the shop's heat budget, its
loss against the door's scheme-consistent transport, diffusion, the unit's fluxes and the pressure work, closes to
**0.045% (off) and -0.032% (on)** of the off run's door loss. Against the advected enthalpy alone it closes to 0.33%
(off) and 8.55% (on): with the curtain on, the advective count through the door line keeps only 3.9 kg of the shop's
8.2 kg of outdoor air at 60 s, the rest crossing by turbulent diffusion in the jet's mixing layer and by the scheme's
face reconstruction. That is why the share kept out is taken from the shop's inventory, not from the door sums. Every
final pressure solve met 1e-7 and none reached its 100-iteration cap (at most 34 iterations off, 21 on), and neither
log has a bounding message. From 0.2 s on, the air stayed within the 273.0-293.3 K and the tracer within the 1e-4 of
[0, 1] set as limits for it (below, on the start). In a still-air check (the whole domain at 0 °C, hydrostatic, the door open, the curtain off) the air reached
0.00017 m/s in 51 steps.

## What the clip shows, and what it does not

The clip shows the section twice on every frame, stacked, the curtain off above and on below, each panel the whole
doorway, a metre of street and the whole shop to its back wall, **from the moment the door opens to 1:00 of the solve**
at three times speed in 20 s. It is coloured by air temperature on a 32-68 °F scale, with moving dashes along the flow,
a clock and the question "Shop air curtain: does it keep the cold out?". Each panel carries one rounded number, the
ankle air in the first 3 m inside the door, "ankles by the door": with the curtain off it falls from 68 to 32 °F by 0:06
and stays there; with it on it holds at 58-61 °F and ends at 54.

- **The number is the air at the cashier's ankles by the door, not the shop or the heat lost.** It is a volume mean
  over the first 3 m and the lowest 0.3 m, and with the curtain off it reads the cold current's front.
- The curtain unit, its glowing slot and its arrow are drawn from the mesh's solid cells and the task's box, which
  agree to the pixel; the door is open its full 2.2 m.

## What it cannot

- **It is a typical curtain, not a code-compliant one.** The jet leaves at 6 m/s aimed 20° out, but its largest
  downward speed on the line 15 cm above the floor is 1.0-1.3 m/s from 3 s on (1.31 m/s at most, at 3.0 s; 1.13 m/s at
  30 s and 1.06 m/s at 60 s), against the 2.0 m/s (400 ft/min) that ASHRAE 90.1 asks of an air curtain in place of a
  vestibule, tested to AMCA 220, and the 2.3 m/s the brief's plane-jet estimate gave. It slows faster than a free jet
  because it bends into the shop. The case was not tuned to meet the code: that would mean choosing a stronger unit's
  discharge speed, and no source gives the speed that produces 2.0 m/s at the floor in this doorway; the makers'
  own warning that a curtain set too strong loses more than none makes that a judgement, not a correction. Nothing
  here should be read as a code-compliant curtain's performance.
- **The shop is as wide as its door.** A 2-D section cannot let the cold air spread sideways, so the off shop floods
  far faster and deeper than a real one, almost to the ceiling within the minute, and the on shop's fall to 54 °F at
  the ankles is too fast as well: a real shop ten doors wide would have lost about a tenth as much. **The contrast and
  the share kept out hold; the absolute temperatures at 1:00 are not a real shop's.** The off shop's exchange also
  stops once it is full, which is why the share falls from 78% at 30 s to 64% at 60 s.
- **Nothing here is about the bill.** One minute of one door on a still day is solved. The curtain's own fan power, a
  heated jet, wind, people walking through the door, other openings in the building and a unit set too weak or too
  strong are all outside the model. AMCA's own whole-building study finds that, against a vestibule, an air-curtain
  door "can save 0.3% ~ 2.2% energy" in US climate zones 3-8; the 78% is the outdoor air kept out of this doorway in
  half a minute, not a share of a heating bill.
- **A recirculated, unheated jet.** The intake takes the shop's own air, so the jet cools and carries some outdoor air
  as the shop cools (a tracer of 0.28 at 60 s). Frank and Linden found heating the jet lowers the seal; a heated
  unit is not tried.
- **The slot and the intake are walls on the shared mesh.** Both are mesh type `wall` in both runs, so that the off
  run's wall functions apply there; in the on run they carry inlet and outlet conditions and no wall functions (nut
  and alphat calculated, 0), but as walls they count in SST's wall distance.
- **The start is impulsive.** The jet starts at full speed into air at rest, and the pressure work at the slot heats
  the slot's cell to 294.19 K at 0.12 ms, 1.04 K above the shop's air, falling below 293.3 K by 1.2 ms. The air and the
  tracer were judged from 0.2 s on. No temperature or tracer was clipped.
- **The time step ran a little past its settings.** maxCo 1 and maxDeltaT 0.02 s are set in both runs, but OpenFOAM's
  alignment of steps to the write times enlarged some: the Courant number after the pressure correction reached 1.28
  (off) and 1.25 (on), and the off run's longest step was 0.0239 s.
- **RANS, one mesh, one run each.** k-ω SST on a 2-D tensor grid of 88,890 cells, 1-9.5 cm, with wall functions; the
  turbulence of a real jet and of the cold current's head is three-dimensional and unsteady, and a 2-D URANS averages
  it. No mesh or time-step study, and no uncertainty bar on the 78%.
- **No wind, no people, no radiation, no heat through the walls.** All surfaces are adiabatic, and the shop has no
  furniture, stock, heating or other opening.

## Sources

- DIYnot forum, "Simplex heater above shop doors" (https://www.diynot.com/diy/threads/simplex-heater-above-shop-doors.638801/),
  29 Nov 2024: "in reality I think it's a large expense for little reward".
- PistonHeads forum, "Heaters over open shop doorways" (https://www.pistonheads.com/gassing/topic.asp?h=0&f=219&t=1216874),
  9 Nov 2012: "it's surely a ruinously expensive way of keeping your shoppers inside?" and "satisfying people
  psychologically, despite the inefficiency!".
- Frico, "What You Need to Know before Buying an Air Curtain" (https://www.frico.net/en/explore/insights/choose-right-air-curtain):
  "Independent tests show that a correctly installed air curtain can reduce energy losses at an open door by up to
  80%."
- Mars Air Systems, "Energy Savings and Sustainable Buildings: How Mars Air Curtains Reduce Energy & Save Money"
  (white paper, on BIMobject): air curtains "are between 70%-80% effective in minimizing
  energy loss".
- T. Agrawal, N. K. Jha and V. K. Chalamalla, "Improvement in sealing effectiveness of air curtains using positive
  buoyancy", arXiv:2305.06697, 2023: "The existing literature suggests that AC can inhibit up to approximately 80% of
  the total buoyancy-driven exchange flow across a doorway"; and the same kind of 2-D section for the sealing.
- "Air Curtains Allowed as Vestibule Substitutes in Upcoming ASHRAE Standard 90.1-2019", Healthcare Facilities Today:
  air curtains accepted in place of vestibules if tested to
  ANSI/AMCA Standard 220 to give "a minimum 400-ft/min. airstream velocity at the floor".
- L. Wang (Concordia University) for AMCA International, "Investigation of the Impact of Building Entrance Air Curtain
  on Whole Building Energy Use", 2013: "Compared to the vestibule door, the air curtain door can save 0.3% ~ 2.2%
  energy for zone 3 ~ 8".
- J. Frank and P. F. Linden, "The effectiveness of an air curtain in the doorway of a ventilated building", J. Fluid
  Mech., 2014, for the effectiveness E as the share of the exchange flow kept out, and the deflection modulus.

## How the case got here

**The solve.** The case was set up and solved by an agent on a cloud workspace of four cores and checked by us. The
first tests showed three start-up faults, each fixed before production: the slot and the intake had been generic
patches, which OpenFOAM refuses wall functions on in the off run, and are now walls in both; the intake's initial
velocity pointed into the room, which the outlet condition corrected on the first solve but which left the start-up
flux with the wrong sign; and the first step is now 0.1 ms, with the face flux written as zero at rest. A 0-10 s timing
probe of the on run on all four cores ran at 121.2 wall-seconds per second of flow, a median step of 1.31 ms set by
the 1 cm cells below the slot, with no pressure solve at its limit. Production ran off then on, one after the other on
all four ranks, **each straight through from rest to 60 s in one segment, with no restart**: 8,505 steps and 1,902 s of
solver wall time (off) and 45,610 steps and 6,654 s (on), 3.11 h for everything with the meshing, the tests and the
probe, within the 10 h we allow. A check at 30 s, which would have stopped both runs had the curtain kept out less
than a quarter of the outdoor air, passed at 78%. The finalising script failed on an import error after both solves
had ended; it was fixed and only the finalising was rerun. After the solve, the face zones' flipMap was set so that
their normals point out of the shop; the monitor's sums are oriented by geometry and did not change, and
`make_mesh.py` writes the zones that way.

**A straight run with this case's `Allrun` is the same run**, but it will not repeat the solved runs bit for bit: the
scotch decomposition and the parallel sums need not match on another machine (the solved runs pinned each rank to one
core), and in a turbulent buoyant flow that round-off grows. The means of a rebuilt run should be expected to agree with
these to a few hundredths of a kelvin and the share kept out to about a percentage point, not to the last digit. No
rebuilt run was solved through.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/airCurtain
    ./Allrun off                 # [nProcs], default 4; builds the mesh first
    ./Allrun on                  # default 4; start it once runs/mesh/ is built

The first `Allrun` writes the shared mesh in `runs/mesh/` (`scripts/make_mesh.py`, a few seconds) and checks it. Then
`scripts/make_case.py` writes `runs/<run>/`: the mesh, `0/` and `system/controlDict` and `decomposeParDict`, with
`constant/` and the rest of `system/` from `template/`. `Allrun` writes the t = 0 section, decomposes by scotch and
solves from 0 to 60 s. The two runs differ only in the slot's and the intake's conditions in `0/`.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs. The solved runs took about
0.5 h (off) and 1.8 h (on) on 4 ranks each.

Each run writes 481 times of 2 planes (VTK), the fields every 10 s and monitor files of about 10 MB (off) and 59 MB
(on).
`results/` holds the tables at the report times; no fields, meshes, planes or logs. The files in `results/` are what
the agent's report script wrote from the solved runs' monitors; that script is not included.

Checked from a clean copy of this folder on 17 Nov 2026: `make_mesh.py` writes the solved mesh byte for byte
(`points`, `faces`, `owner`, `neighbour`, `boundary` and `faceZones`), and `checkMesh` gives Mesh OK at 88,890 cells.
`make_case.py` writes both runs' `0/`, `constant/` and `system/` byte for byte, but for the monitor's name and the
unused abort function object, and for the hydrostatic `p` and `p_rgh`, where about one value in twenty differs in its
last digit (at most 1.5e-11 Pa), as the solved runs' own script gives on this machine: the exponential rounds
differently here. Eight steps of the on run from there (to 2 ms), serially, gave the solved run's time steps to the last digit
and its first-step residuals to eight figures or more (Ux 1 then 0.00199895418342 against 0.00199895549941, p_rgh
0.129681444103 against 0.129681444652), as a serial and a parallel solve differ, and the monitor wrote its rows.
