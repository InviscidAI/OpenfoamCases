# An air curtain over an open store door in summer, off against on

[`airCurtain`](../airCurtain) opened a shop door on a freezing day and ran an air curtain over it. Asked for the
reverse, a hot day outside and an air-conditioned store inside, the comments under that case's clip split two ways.
One camp says nothing changes: "it works exactly the same", "we install these in tropical countries but in reverse (to
keep cold air inside)", and "un-heated air curtains are pretty much all you see in hotter areas like texas". The
makers agree: "Ambient air curtains without heat are recommended for use in cold storage openings and air conditioned
premises in warm climates" (Frico), and curtains "reduce the ingress of cold air (or hot air in summertime) from the
outside" (Engineering ToolBox). The other camp says the physics turns against it: "cold air sinks and hot air rises.
This will not work for hot air. This is basic Thermodynamics", and "hot air rises. you would need an completely
different setup. Common sense." (all from comments of 17-18 Nov 2026). This case opens a US convenience store's glass
door on a still 95 °F afternoon twice, the store air-conditioned to 70 °F, once with the curtain off and once with it
on, and asks how much of the hot outdoor air gets into the store in the first minute, and how warm the air gets at
head height. It is about the air through the door, not the cooling bill.

    ./Allrun off     # the curtain unit there but not running, 0-60 s from the door opening
    ./Allrun on      # the curtain blowing from the moment the door opens, 0-60 s

**The result.** **With the curtain off, the hot street air comes in over the top of the door and the store's cool air
spills out along the floor onto the sidewalk; with it on, about two thirds of the hot air stays in the street.** The
air at head height (1.5-1.8 m) through the whole store is, off against on, 70.6 against 70.2 °F (21.44 against
21.22 °C) at 2 s, 73.6 against 71.2 °F at 10 s, 80.6 against 72.7 °F at 30 s and **90.2 against 75.1 °F (32.36 against
23.92 °C) at 60 s**; the clip's whole-degree numbers are 71/70, 74/71, 81/73 and 90/75. Counted by the tracer that
marks the outdoor air, the store holds 13.59 kg of it at 30 s with the curtain off and 4.20 kg with it on, per metre
of door width: **the curtain kept out 69% of the outdoor air that came in without it, at 30 s (69.1%) and at 60 s
(69.0%)**, inside the 60 to 80% ASHRAE gives for a curtain's effectiveness and below the makers' "up to 80%". In
winter ([`airCurtain`](../airCurtain)) the same unit at the same setting kept out 78% at 30 s and 64% at 60 s. **So
"hot air rises, this won't work" is wrong for this unit and this doorway**: the hot air does come in over the top of
the door, where the curtain's slot is, and the curtain turns most of it back. Read [What it cannot](#what-it-cannot)
before any number here: **the store is as wide as its door**, so with the curtain off it fills with hot air to near
the floor in a minute, and **90 °F at head height after a minute is not what a real store reaches**; **the curtain is
a typical one, not a code-compliant one** (its jet reaches 15 cm above the floor at 1.0-1.2 m/s, not 2.0 m/s); **with
it on, the ankle air just inside the door is warmer than with it off**; and **the air is dry**, where a field study of
a hot, humid shop found conventional curtains hardly helped.

The section, the curtain, its setting and the outdoor-air tracer are [`airCurtain`](../airCurtain)'s; the scene is
new. The store is 10 m deep under a 2.9 m suspended ceiling behind a 7 ft (2.13 m) door in a 0.15 m storefront, where
airCurtain's shop was 8 m deep and 3.2 m tall behind a 2.2 m door in a 0.2 m wall, and the temperatures differ by 14 K
instead of 20 K. The buoyant model is the one our room cases use, and `template/system/fvSolution` keeps
[`radiatorUnderWindow`](../radiatorUnderWindow)'s notes.

## The doorway

A vertical section through the middle of the door, seen from the side, one cell (1 m) deep: every figure here is per
metre of door width. x runs from the storefront's outer face into the store, y up from the sidewalk and the floor;
metres.

| | where | |
|---|---|---|
| street | x -5.0 to 0, y 0 to 6.0 | still, dry air at 35 °C (95 °F); open at x = -5 (`street`) and y = 6 (`sky`); the sidewalk a wall |
| storefront | x 0 to 0.15, y 2.13 to 6.0 | solid above the door, an aluminium-and-glass front 0.15 m deep |
| door | x 0 to 0.15, y 0 to 2.13 | a standard 7 ft door; no door leaf, it is simply open at t = 0 |
| store | x 0.15 to 10.15, y 0 to 2.9 | 10 m deep, 2.9 m to a suspended ceiling, closed at the back, no other opening, no air conditioning running; air at 21.1 °C (70 °F, 294.261 K) |
| curtain unit | x 0.15 to 0.45, y 2.18 to 2.43 | airCurtain's box, 0.30 m deep and 0.25 m tall, on the storefront's inside face, its underside 5 cm above the door head |
| slot | x 0.16 to 0.22, y = 2.18 | the unit's underside, 6 cm wide |
| intake | x = 0.45, y 2.20 to 2.41 | the unit's face to the store, 21 cm tall |

**off**: the unit hangs there with its slot and intake walls like the rest of it. **on**: from t = 0, switched on with
the door, the slot blows a fixed 6 m/s, (-2.0521, -5.6382) m/s, aimed 20° from the vertical out towards the street,
0.33829 m³/s per metre, with k from 5% intensity and ω from a 6 mm mixing length. The intake draws the same
0.33829 m³/s (`flowRateOutletVelocity`), and the slot's temperature and tracer are the intake's mean
(`outletMappedUniformInlet`), so the jet is the store's own air, recirculated and unheated: in summer it blows the
store's cool air. This is airCurtain's unit at airCurtain's setting, on purpose, since the question is whether the
same unit still works. At 14 K its deflection modulus is about 1.0 against airCurtain's 0.6, further above the
laboratory optimum of 0.2-0.4 (the brief's estimate), and the brief left the answer to the solve.

**The start.** Both runs start at rest at t = 0, when the door opens: the air at 35 °C and the tracer at 1 for
x < 0.075 m (the street and the outer half of the doorway), at 21.1 °C and 0 in the store. Each side is hydrostatic,
the two pressures equal at y = 1.065 m, the door's mid-height, on the cells and on every boundary face, and the face
flux is zero; the first step is 0.1 ms. The open boundaries carry the street's hydrostatic total pressure face by face
(`prghTotalPressure`); air that comes in through them is at 35 °C with tracer 1. Every wall is no-slip and adiabatic.

**The outdoor-air tracer** (`outdoor`, a `scalarTransport` function object) is 1 in the outdoor air and 0 in the
store's, carried by the mass flux with the same diffusivity as the temperature: alphaD 1/0.71 for the laminar part and
alphaDt 1.0, because the bulk turbulent Prandtl number of SST in v2512 is 1.0. The store's outdoor air is the integral
of ρ times the tracer over the store, x 0.15-10.15 m.

**The numbers.** The head-height air is the volume mean of the air temperature over x 0.15-10.15 m, y 1.5-1.8 m, the
whole store (partial cells weighted by the share of their volume inside); the same mean over x 1.15-4.15 m is the
near-door head height, and over x 0.15-3.15 m, y 0-0.3 m the ankle air by the door. The curtain's share is
E = 1 - M_on / M_off, M the store's outdoor air at the same time.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71, the sensible enthalpy referenced at 294.261 K, the store's start; the file's comment still
says 20 C, from airCurtain), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction` with Prt 0.85). Euler in time, adaptive steps
at Courant 1 (maxDeltaT 0.02 s), limitedLinearV for U and limitedLinear for h, the tracer, k and ω. Two outer and two
pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100 iterations; the tracer by PBiCGStab to
1e-12. No radiation, no air conditioning, no other sources.

**The mesh** (`scripts/make_mesh.py`): a tensor grid written directly as a polyMesh, with no blockMesh, less the solid
cells of the storefront, the unit and everything above the ceiling, 430 x 221 lines, **79,256 hexahedral cells**. Six
cells of 0.91-1.07 cm across the slot, 1 cm cells over y 2.13-2.43 m round the door head and the unit, cells no larger
than 1.34 x 2.0 cm in the doorway and 1.5 cm tall in the lowest 0.3 m, 0.9-1.2 cm wide under the unit, 1.2-2.0 cm in
the store to x = 1.5 m, 2.0-3.4 cm to 4.15 m and 3.6-5.0 cm beyond, growing to 9.8 cm far out in the street and the
sky; neighbouring cells differ in size by at most 10.0% in x and 6.4% in y. `checkMesh` OK, no non-orthogonality. The
patches' areas are what the task set (slot 0.06 m², intake 0.21 m², each door zone 2.13 m²; `results/mesh.json`).
Three face zones of the door's height, at x = 0, 0.075 and 0.15 m, carry the monitor's door sums, their normals +x,
into the store. One mesh, no mesh study.

**The monitor** (`template/system/monitor`, a coded function object run at every step, into
`postProcessing/monitor/monitor.csv`): the gross flow each way through the three door lines, the street and the sky
(volume, mass, enthalpy relative to 294.261 K and outdoor air); the store's outdoor air, near the door (x 0.15-4.15 m)
and in all, its heat, ∫p dV and the mean temperatures of the ankle layer, the head height through the store and near
the door, the ceiling layer (y 2.6-2.9 m), the sidewalk just outside (x -1.5-0, y 0-0.15 m) and the whole store; the
neutral level in the door; the slot's and the intake's flows, temperatures and tracer; the jet's largest downward
speed on the line 15 cm above the floor between x = -1.5 and 0.45 m; and the heat budget's terms, the scheme's own
face fluxes, the diffusive flux through the door, the kinetic energy and the work of gravity included. `courant.csv`
keeps the twelve cells of highest Courant number. The `planes` are the whole section, T, U and the tracer, as point
values (`section`) and as cell values (`sectionCells`), every 0.125 s, 481 a run.

## Results

`results/off_report.csv` and `on_report.csv` (every monitor column at 1, 2, 3, 5, 10, 15, 20, 30, 45 and 60 s, with
the region means in °C and °F, the curtain's slot and intake and the heat budget), `effectiveness.csv` (the curtain's
share at 2-60 s, by the outdoor air, by the heat carried through the door and by three other counts), `mesh.json`,
`jet_all_frames_summary.json` (the jet's path from the slot in all 481 planes) and `door_flux.txt` (our own count of
the gross flow through the door line from the monitor's every step).

| head height through the store, °F (°C) | 2 s | 10 s | 30 s | 60 s |
|---|---:|---:|---:|---:|
| curtain off | 70.6 (21.44) | 73.6 (23.12) | 80.6 (26.99) | **90.2 (32.36)** |
| curtain on | 70.2 (21.22) | 71.2 (21.78) | 72.7 (22.64) | **75.1 (23.92)** |

| | 5 s | 10 s | 20 s | 30 s | 45 s | 60 s |
|---|---:|---:|---:|---:|---:|---:|
| outdoor air in the store, off, kg | 1.93 | 4.45 | 9.05 | 13.59 | 20.07 | 23.74 |
| outdoor air in the store, on, kg | 1.01 | 1.71 | 3.04 | 4.20 | 5.82 | 7.35 |
| **kept out by the curtain** | 47% | 61% | 66% | **69%** | 71% | **69%** |
| the store's whole mean, off / on, °C | 21.93 / 21.53 | 22.98 / 21.81 | 24.92 / 22.36 | 26.82 / 22.83 | 29.55 / 23.50 | 31.12 / 24.14 |
| under the ceiling (2.6-2.9 m), off / on, °C | 22.30 / 21.11 | 26.23 / 21.31 | 32.48 / 22.51 | 33.83 / 23.22 | 34.02 / 23.92 | 34.05 / 24.25 |
| head height near the door (1-4 m in), off / on, °C | 21.78 / 22.31 | 24.47 / 22.40 | 23.31 / 22.63 | 23.35 / 23.08 | 26.74 / 23.94 | 30.99 / 24.70 |
| ankles by the door, off / on, °C | 21.11 / 23.40 | 21.11 / 24.48 | 21.11 / 25.71 | 21.12 / 26.34 | 21.17 / 26.92 | 23.35 / 27.32 |
| sidewalk just outside, off / on, °C | 21.11 / 26.90 | 21.11 / 30.30 | 21.11 / 30.84 | 21.12 / 31.13 | 21.12 / 31.37 | 24.52 / 31.53 |

**With the curtain off** the hot air comes in over the top of the door and runs along the ceiling to the back wall,
while the store's cool air pours out over the threshold: the neutral level in the door stays at 1.02-1.11 m, about the
door's mid-height, but for 0.90 m at 10 s, and from 5 s to 45 s the strip of sidewalk just outside the door is at the
store's own 70 °F. The layer under the ceiling is at 90.5 °F (32.48 °C) by 20 s, and the hot layer thickens downwards
from the back wall forward, so the first metres inside the door stay cool longest: at 30 s head height 1-4 m inside
the door is 74.0 °F, while through the whole store it is 80.6 °F. About 0.42 m³/s per metre crosses the door line each
way on average over 0-30 s and 0.37 m³/s over 30-60 s, 0.29 m³/s at 60 s; the textbook two-way exchange through a
2.13 m door at 14 K, (Cd/3)·√(g′H³) with Cd 0.6, is 0.42 m³/s. By 60 s outdoor air is 23.74 kg of the store's 33.11 kg
of air, the store is hot to near the floor, and the ankle air by the door has begun to warm.

**With it on** the jet stands across the door from the first second and the store turns over in one large roll,
warming slowly. About 0.38 m³/s crosses the door line each way throughout, most of it the curtain's own air and the
street air it turns back: of the 22.3 kg of outdoor air that crossed the line into the store over the minute, 18.0 kg
went back out (our count from the monitor). The flow through the door line changes direction at 0.34-0.39 m from 3 s
on. The jet bends into the store as it falls: the streamline from the slot's centre first crosses 15 cm above the
floor at 2.25 s, 0.98 m inside the façade, and in all 463 of the 481 planes where it reaches that height it does so in
the store, 0.41-1.01 m inside, never in the door or on the street. Because the intake recirculates the store's air,
the jet warms with the store, from 294.26 K to 297.41 K at 30 s and 298.59 K at 60 s, its tracer from 0 to 0.23 and
0.31.

The share kept out is the same counted by heat: at 30 s the store gained 69.1% less heat through the door with the
curtain on, counted with the scheme's own face values and the diffusion, and 69.0% less at 60 s; by the store's own
heat, 69.1% and 69.0%. A count by the advected enthalpy alone, with T interpolated linearly to the faces, gives 84.1%
and 84.8%, but it leaves out the turbulent diffusion in the jet's mixing layer and the scheme's face reconstruction,
which carry a good part of what crosses the door with the curtain on (below), and is not the heat kept out.

**Checks.** Both runs reached 60 s with a clean `End` at the end of each of their two segments (below). The slot's and
the intake's flows were 0.338292 and 0.338290 m³/s throughout, and their temperatures agreed within 0.0004 K in the
tests and to 0.0001 K at 60 s. Over 5-60 s the store's heat budget, its gain against the door's full discrete
transport, the unit's fluxes, the pressure work, the kinetic energy and gravity, closes to **-0.039% (off) and -0.083%
(on)** of the off run's door gain. Against the advected enthalpy alone it closes to 0.27% (off) and 16.0% (on): with
the curtain on, the advective count through the door line keeps only 4.3 kg of the store's 7.35 kg of outdoor air at
60 s, the rest crossing by turbulent diffusion in the jet's mixing layer and by the scheme's face reconstruction. That
is why the share kept out is taken from the store's inventory, not from the door sums. Every final pressure solve met
1e-7 and none reached its 100-iteration cap (at most 22 iterations off, 23 on), and neither log has a bounding
message. From 0.2 s on, the air stayed within 294.259-308.189 K (off) and 294.248-308.195 K (on), inside the
294.1-308.3 K set as limits, and the tracer within 1e-6 of [0, 1]. ∫p dV over the store varied by 2e-6 (off) and 9e-5
(on) of itself. In a still-air check (the whole domain at 35 °C, hydrostatic, the door open, the curtain off) the air
reached 0.000106 m/s in 50 steps; 82 of its final pressure solves stopped at the 100-iteration cap with residuals of
1.3-5.5e-7, at the hydrostatic round-off floor, as on airCurtain, and the tolerance was not relaxed.

## What the clip shows, and what it does not

The clip shows the section twice on every frame, stacked, the curtain off above and on below, each panel the whole
store to its back wall and 1 m of sidewalk, **from the moment the door opens to 1:00 of the solve** at three times
speed, 481 frames and the last held for half a second, 20.5 s. It is coloured by air temperature on a 70-95 °F scale,
the two starting temperatures, with air parcels moving through the planes' velocity, a clock, the question "Does an
air curtain keep summer heat out?" and under it "a follow-up: you asked for the summer version". Each panel carries
one rounded number, "head height", the air at 1.5-1.8 m through the whole store: 71/70 °F at 0:02, 74/71 at 0:10,
81/73 at 0:30 and 90/75 at 1:00.

- **The number is the whole store at head height, not the air by the door.** The brief proposed head height 1-4 m
  inside the door, but that mean barely parts the panels until late (74.0 against 73.5 °F at 30 s), because the off
  store fills from the ceiling and the back wall down.
- **The 90 °F is the section's, not a real store's** (below). The panels' contrast and the share kept out are what the
  clip carries.
- The curtain unit, its glowing slot and its arrow are drawn from the mesh's solid cells and the task's box, which
  agree to the pixel; the door is open its full 2.13 m. The parcels are moved through the planes' velocity after the
  solve; they are not solved particles.

## What it cannot

- **The store is as wide as its door.** A 2-D section cannot let the hot air spread sideways, so the off store fills
  far faster and deeper than a real one: by 60 s outdoor air is 23.74 kg of its 33.11 kg of air, it is hot to near the
  floor, and its head height reads 90 °F. A real store several doors wide would warm far less in a minute, and so
  would the on store, whose 75 °F is too warm as well. **The contrast and the share kept out hold; the absolute
  temperatures at 1:00 are not a real store's.**
- **It is a typical curtain, not a code-compliant one.** The jet leaves at 6 m/s aimed 20° out, but it bends into the
  store and its largest downward speed on the line 15 cm above the floor is about 1.0-1.2 m/s from 5 s on
  (0.93-1.22 m/s at every step, 1.22 m/s at 10.4 s; 1.06 m/s at 30 s and 1.10 m/s at 60 s), against the 2.0 m/s (400
  ft/min) that ASHRAE 90.1 asks of an air curtain in place of a vestibule, tested to AMCA 220. The monitor's line ends
  at x = 0.45 m and the strongest downflow at that height sits just past it, at x 0.47-0.57 m; read from the saved
  cell planes over the whole store it is hardly faster, 1.07-1.23 m/s from 5 s on. The case was not tuned to meet the
  code: that would mean choosing a stronger unit's discharge speed, and no source gives the speed that produces
  2.0 m/s at the floor in this doorway. Nothing here should be read as a code-compliant curtain's performance.
- **With the curtain on, the ankle air just inside the door is warmer than with it off**: 26.3 against 21.1 °C (79.4
  against 70.0 °F) at 30 s and 27.3 against 23.4 °C (81.2 against 74.0 °F) at 60 s, over the first 3 m and the lowest
  0.3 m. The off store keeps a pool of its own cool air on the floor while the heat collects above; the jet stirs the
  store and brings street air down to the floor by the door. The head-height number is not affected, but a curtain
  that keeps two thirds of the hot air out still makes a cashier's feet by the door warmer in the first minute.
- **The air is dry.** There is no humidity in the model, so nothing here speaks to the latent half of a cooling load
  or to a humid street. UPM's field study of a shop in Jávea, in hot and humid weather, found that "the usage of
  conventional air curtains hardly has advantages, but the usage of high efficient air curtains provides significant
  improvements" (as ScienceDaily reports it; the paper was not retrieved). This curtain is a conventional one.
- **Nothing here is about the bill.** One minute of one door on a still day is solved, and the store's air
  conditioning is not running in either run: no supply, no return, no thermostat. The curtain's fan power, wind,
  people walking through the door, other openings, sun on the sidewalk and a unit set too weak or too strong are all
  outside the model. AMCA's whole-building study, which has a summer mode, finds that against a vestibule an
  air-curtain door "can save 0.3% ~ 2.2% energy" in US climate zones 3-8; the 69% is the outdoor air kept out of this
  doorway in a minute, not a share of a cooling bill.
- **It is not a clean summer-against-winter comparison.** The door, the storefront, the store and the temperature
  contrast all differ from airCurtain's, so 69% against 78% and 64% does not isolate the season.
- **A recirculated, unheated jet.** The intake takes the store's own air, so the jet warms and carries some outdoor
  air as the store warms (298.59 K and a tracer of 0.31 at 60 s). The slot takes the intake's mean once a time step,
  not after every correction; the two differ by 0.0001 K at 60 s.
- **The slot and the intake are walls on the shared mesh.** Both are mesh type `wall` in both runs, so that the off
  run's wall functions apply there; in the on run they carry inlet and outlet conditions and no wall functions (nut
  and alphat calculated, 0), but as walls they count in SST's wall distance.
- **The start is impulsive.** The jet starts at full speed into air at rest, and in the on run the hottest air reaches
  308.33 K at 0.74 ms, 0.18 K above the street's, and the coldest 293.77 K at 0.22 ms, 0.49 K below the store's. The
  air and the tracer were judged from 0.2 s on. No temperature or tracer was clipped.
- **The time step ran a little past its settings.** maxCo 1 and maxDeltaT 0.02 s are set in both runs, but OpenFOAM's
  alignment of steps to the write times enlarged some: the Courant number after the pressure correction reached 1.26
  (off) and 1.25 (on), and the off run's longest step was 0.0239 s.
- **RANS, one mesh, one run each.** k-ω SST on a 2-D tensor grid of 79,256 cells, 0.9-9.8 cm, with wall functions; the
  turbulence of a real jet and of the hot current's head is three-dimensional and unsteady, and a 2-D URANS averages
  it. No mesh or time-step study, and no uncertainty bar on the 69%.
- **No wind, no people, no radiation, no heat through the walls.** All surfaces are adiabatic, and the store has no
  shelving, stock, cooling or other opening.

## Sources

- Comments under the clip of [`airCurtain`](../airCurtain), 17-18 Nov 2026: "Now try the opposite, 40°C outside and
  about 20°C inside." (the request); "it works exactly the same", "we install these in tropical countries but in
  reverse (to keep cold air inside)" and "un-heated air curtains are pretty much all you see in hotter areas like
  texas"; against, "cold air sinks and hot air rises. This will not work for hot air. This is basic Thermodynamics"
  and "hot air rises. you would need an completely different setup. Common sense."
- Frico, "What You Need to Know before Buying an Air Curtain"
  (https://www.frico.net/en/explore/insights/choose-right-air-curtain): "Ambient air curtains without heat are
  recommended for use in cold storage openings and air conditioned premises in warm climates", and "Independent tests
  show that a correctly installed air curtain can reduce energy losses at an open door by up to 80%."
- Engineering ToolBox, "Air Curtains" (https://www.engineeringtoolbox.com/air-curtains-d_129.html): curtains "reduce
  the ingress of cold air (or hot air in summertime) from the outside".
- Wikipedia, "Air door" (https://en.wikipedia.org/wiki/Air_door), quoting ASHRAE: "Air curtain effectiveness in
  preventing infiltration through an entrance generally ranges from 60 to 80%".
- Mars Air Systems, "Energy Savings and Sustainable Buildings: How Mars Air Curtains Reduce Energy & Save Money"
  (white paper, on BIMobject): air curtains "are between 70%-80% effective in minimizing energy loss".
- T. Agrawal, N. K. Jha and V. K. Chalamalla, "Improvement in sealing effectiveness of air curtains using positive
  buoyancy", arXiv:2305.06697, 2023: a 2-D numerical study of the doorway of an air-conditioned building "during the
  summer season in an Indian subcontinental situation", and "AC can inhibit up to approximately 80% of the total
  buoyancy-driven exchange flow across a doorway".
- "Air Curtains Allowed as Vestibule Substitutes in Upcoming ASHRAE Standard 90.1-2019", Healthcare Facilities Today:
  air curtains accepted in place of vestibules if tested to ANSI/AMCA Standard 220 to give "a minimum 400-ft/min.
  airstream velocity at the floor".
- L. Wang (Concordia University) for AMCA International, "Investigation of the Impact of Building Entrance Air Curtain
  on Whole Building Energy Use", 2013, with winter and summer modes: "Compared to the vestibule door, the air curtain
  door can save 0.3% ~ 2.2% energy for zone 3 ~ 8".
- ScienceDaily, "Businesses: Air curtains for energy saving", 19 May 2014
  (https://www.sciencedaily.com/releases/2014/05/140519091925.htm), on Universidad Politécnica de Madrid's study of a
  shop in Jávea "with hot and humid weather": "the usage of conventional air curtains hardly has advantages, but the
  usage of high efficient air curtains provides significant improvements".
- J. Frank and P. F. Linden, "The effectiveness of an air curtain in the doorway of a ventilated building", J. Fluid
  Mech., 2014, for the effectiveness E as the share of the exchange flow kept out, and the deflection modulus.

## How the case got here

**The solve.** The case was set up and solved by an agent on a cloud workspace of four cores and checked by us, from
airCurtain's solved set-up with this scene's geometry, temperatures and regions and airCurtain's corrections written
in from the start. Two things were fixed before production: `decomposePar` refused the first mapped-inlet dictionary,
since v2512 wants `outlets { curtainIntake { offset 0; fraction 1; timeDelay 0; } }` and not `outletPatch`; and
OpenFOAM enlarged the first step to 1.2e-4 s, so `deltaT` was set to 8.33e-5 s, which OpenFOAM's adjustment makes the
1e-4 s asked for, and the tests and the probe were repeated. A 0-10 s timing probe of the on run on all four cores ran
at 143.4 wall-seconds per second of flow over 5-10 s, a median step of 1.27 ms set by the cells just under the slot,
with no pressure solve at its limit. Production ran off then on, one after the other on all four ranks, **each from
rest to 30 s, then, after a check of both at 30 s, on from its own 30 s fields to 60 s**, with only the end time
changed: 5,321 steps and 1,102 s of solver wall time (off) and 47,131 steps and 7,576 s (on), 3.34 h for everything
with the meshing, the tests and the probe, within the 10 h we allow. The check at 30 s, which would have stopped both
runs had the curtain kept out less than a quarter of the outdoor air, passed at 69.1%. The solved runs' planes,
monitors, logs and `system/` came back in the study's archives; its `0/`, `constant/` and mesh were fetched from the
workspace for this case. The agent's own scripts, its mesh writer among them, were not among the files fetched.

**What this folder rebuilds.** `scripts/make_mesh.py` carries the solved mesh's grid lines as numbers, since the
agent's grading rule is not here, and writes the mesh from them. `scripts/make_case.py` writes each run's `0/` and
`system/` from the same rules the solved files follow. `Allrun` solves 0-30 s and then 30-60 s, as the solved runs
were, without the check between. A straight run with this case's `Allrun` is the same run, but it will not repeat the
solved runs bit for bit: the scotch decomposition and the parallel sums need not match on another machine, and in a
turbulent buoyant flow that round-off grows. The means of a rebuilt run should be expected to agree with these to a
few hundredths of a kelvin and the share kept out to about a percentage point, not to the last digit. No rebuilt run
was solved through.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/summerStoreCurtain
    ./Allrun off                 # [nProcs], default 4; builds the mesh first
    ./Allrun on                  # default 4; start it once runs/mesh/ is built

The first `Allrun` writes the shared mesh in `runs/mesh/` (`scripts/make_mesh.py`, a few seconds) and checks it. Then
`scripts/make_case.py` writes `runs/<run>/`: the mesh, `0/` and `system/controlDict` and `decomposeParDict`, with
`constant/` and the rest of `system/` from `template/`. `Allrun` writes the t = 0 section, decomposes by scotch and
solves from 0 to 30 s and on to 60 s. The two runs differ only in the slot's and the intake's conditions in `0/`.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs. The solved runs took
about 0.3 h (off) and 2.1 h (on) on 4 ranks each.

Each run writes 481 times of 2 planes (VTK), the fields every 10 s and monitor files of about 8 MB (off) and 66 MB
(on). OpenFOAM v2512 ignores the planes' compression option; the solved runs gzipped each finished plane with a
wrapper of the agent's, which is not here, so a rebuilt run's planes are uncompressed, about 11 MB a write. `results/`
holds the tables at the report times; no fields, meshes, planes or logs. `off_report.csv`, `on_report.csv`,
`mesh.json` and `jet_all_frames_summary.json` are what the agent's report scripts wrote from the solved runs;
`effectiveness.csv` is the same agent's table taken from its results file; `door_flux.txt` is ours, from the monitor's
every step.

Checked from a clean copy of this folder on 20 Nov 2026: `make_mesh.py` writes the solved mesh byte for byte
(`points`, `faces`, `owner`, `neighbour`, `boundary`, `faceZones`, `cellZones` and `pointZones`), and `checkMesh`
gives Mesh OK at 79,256 cells, its report the solved one's line for line after the header. `make_case.py` writes both
runs' `0/`, `constant/` and `system/` byte for byte, but for the monitor's name, the unused abort function object and
`endTime`, which `Allrun` sets to 30 s and then 60 s, and for the hydrostatic `p`, where 553 of its 80,819 lines
differ in their last digit (at most 1.0e-10 Pa): the exponential rounds differently here. `p_rgh` is the same byte for
byte. The t = 0 planes of both runs, `section` and `sectionCells`, are the solved runs' byte for byte once theirs are
unzipped. Six steps of the on run from there (to 1 ms) on four ranks gave the solved run's time steps to the last
printed digit and its first pressure residual to eleven figures (p_rgh 0.172179203136 against 0.172179203138); from
the second pressure solve on the residuals differ from the second or third figure, as scotch split the mesh
differently here (19,869 cells on the first rank against 19,953).
