# A misted windscreen: the heater on outside air or on recirculation

Two people get into a car on a cold, damp morning and the windscreen mists over. The heater goes
on full with the air on the screen. Should the intake take outside air, or recirculate the
cabin's own air, which is warmer? Car manuals warn that recirculation fogs the windows; forum
advice argues for it because the cabin's air is warmer.

This case takes one generic compact hatchback on one 3 °C, 90 % morning, the driver and a rear
passenger inside, both screens misted at the start and the A/C off, and solves a vertical section
lengthwise through the cabin at the driver's centreline for the first ten minutes after the blower
starts. The air carries its water vapour; the glass condenses and evaporates a film of water; air
above saturation turns into mist. The number it reports is **the share of the windscreen still
misted**. One OpenFOAM case, two runs that differ only in the heater's intake:

    ./Allrun outside    # the heater takes outside air, 3 C and 90 %, and blows it at the windscreen at 52 C
    ./Allrun recirc     # the same heater takes the cabin's own air from the intake under the dash

**This is a 2-D section of one car on one morning, with a warm engine and the A/C off.** The
section has no sides to its windscreen, so its clearing edge is level across the glass where a real
screen's corners clear last, and a working A/C, a cold engine or a thicker mist would each move
both runs. Read [What it cannot](#what-it-cannot) before any number here.

## The car and the morning

| | value | from |
|---|---|---|
| the morning | 3 °C, 90 % relative humidity, 4.25 g of water per kg of air; still | 3 °C: the Met Office's 1991-2020 mean daily minimum at Heathrow, 3.1 °C in December and 2.7 °C in January and February. 90 % is assumed; no climate figure for the morning was found |
| the cabin at the start | still air at 5 °C and 90 % (4.92 g/kg), saturated at the windscreen's 3.55 °C: a car the two people have just fogged | the glass's steady temperature between 5 °C still air inside (ISO 6946's Rsi 0.13 m²K/W) and 3 °C outside |
| the starting mist | 10 g/m² of water, 10 µm, on every face of both screens and the side glass | the EU demisting test's steam: 70 g/h a seat for six minutes is about 35 g in a five-seat car, over roughly 2.9 m² of glazing (our estimate) at most 12 g/m² even if all of it condensed on glass. Two CFD studies assumed 0.12 mm (Mutlu, Sevilgen and Kılıç, IJVD 71, 2016) and 0.18 mm (Mehdipour et al., IJE 30(7), 2017), about ten times what the test can put there |
| clear | a face counts as clear once less than 1e-5 kg/m², 0.1 % of the starting film, is left | EU 672/2010 counts as demisted only "the area of the windscreen having a dry inside surface, without any drops or traces of water" |
| the occupants | 70 g of water an hour each, and 72 W of sensible heat | EU 672/2010, Annex II: each observer counts as "70 ± 5 g/h" of steam; ASHRAE's "seated, very light work", 72 W sensible and 45 W latent (66 g/h) |
| where their water goes | 25 % in the breath, into a disc of air 30 mm in radius 40 mm in front of the face at mouth height; 75 % into the cells touching the torso, neck and head, less those within 25 mm of a seat back or headrest | the respiration share of ISO 7730's latent terms (Fanger 1970), as Berkeley CBE's pythermalcomfort implements them: 25.3 % in the starting cabin, 24.8 % at 2.2 kPa of vapour (`physics.breath_share`) |
| the defroster | 100 l/s of air, leaving a 25 mm slot at the foot of the windscreen at 3.2 m/s | a Volvo V40 in the SAE J902A defrost test: "approximately 100 l/s" (Sadananda, Chalmers MSc thesis with Volvo Cars, 2016) |
| the heater | a warm engine's 85 °C coolant through a heater of effectiveness 0.6: outside air leaves it at 52 °C; on recirculation the supply is 0.4 T_intake + 51 °C | ours; coolant at 80-95 °C in normal running and 46-60 °C at the vents on full heat are usually quoted. The weakest number in the case, and the same heater in both runs |
| the A/C | off in both runs | at 3 °C most compressors will not run: "The air conditioner may not function when the outside temperature approaches 0 °C (32 °F)" (Mazda CX-5 owner's manual) |
| the windscreen | 2.1 mm glass, 0.76 mm PVB, 2.6 mm glass: 10,317 J/m²K and 0.0097 m²K/W | the Volvo windscreen of the same thesis, its tables 3.2 and 3.3 |
| the rear screen | one 3.2 mm toughened pane of the same glass | thickness assumed |
| outside the glass | 0.04 m²K/W, h = 25 W/m²K: a light wind or a car pulling away | ISO 6946's external surface resistance |

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's own
Allrun; `scripts/physics.py` holds every number above and `scripts/geometry.py` the section. x runs
rearward from the foot of the windscreen's inner surface, y up from the floor.

- **The section.** One cell deep and 1 m thick, standing for a cabin 1.45 m wide (VW Golf 8:
  1,471 mm front and 1,440 mm rear interior width), so every whole-car rate is divided by 1.45.
  The windscreen runs 1.062 m along its slope at 27° from the dash at y = 0.80 m to the header at
  1.27 m; the headliner runs back to the rear screen, which falls 0.405 m at 46° to a lip on the
  parcel shelf. The air is 1.539 m² of section, 2.2 m³ in the car. The driver sits on the front
  seat with hands near a 370 mm steering wheel, the passenger directly behind; both are drawn
  from rounded primitives (limbs, torso, neck and head) in `geometry.py`, with no outside model.
  The defroster's slot is fed through a 60 mm duct and leaves the dash at 63°. The recirculation
  intake is 120 mm of the dash's underside: a wall on outside air, an outlet on recirculation.
  The cabin's air leaves through a 120 mm gap at the parcel shelf into the boot's pressure-relief
  vents, held at the 3 °C outdoor air's barometric pressure at its height.
- **Air and numerics.** `buoyantPimpleFoam` (OpenFOAM v2512), a perfect gas with c_p 1005 J/kgK
  and μ 1.8e-5 Pa s, k-omega SST with the buoyancy source on k, Euler in time at Courant 2, PISO
  with two pressure correctors, limitedLinear schemes, as in
  [`radiatorUnderWindow`](../radiatorUnderWindow)'s curtain runs and
  [`iceDamRoofVents`](../iceDamRoofVents) but for the PISO loop. The blower spins up over the
  first half second. The cells start at the 5 °C air's barometric pressure, so still air stays
  still (`setup_fields.py`).
- **The vapour.** The specific humidity `w` is a `scalarTransport` function object on the step's
  mass flux, with D ρ = μ/0.60 + μt/0.85: water vapour in air has D = 2.5e-5 m²/s, a Schmidt
  number of 0.60, and the turbulent Schmidt number is the turbulent Prandtl number of T. Each
  occupant's water is two `scalarSemiImplicitSource`s, the breath over 22 and 27 cells and the
  upper body over 181 and 240.
- **The glass.** The coded function object `walls` keeps every face of the two screens and the
  trim at its own temperature, with the heat capacity behind it. Each step a face takes the heat
  the air gives it and the latent heat of what condenses on it or evaporates from it, and a
  screen face loses heat through the glass and the outside resistance to the 3 °C air. There is no
  conduction along the glass. A screen face condenses whenever the air in the cell next to it
  holds more vapour than saturation at the face's temperature; the vapour at a wet or condensing
  face is held at saturation, and the flux into it is the resolved gradient. The screens and the
  headliner carry a structured layer 8.7 mm deep whose first cell is 0.1 mm, y+ about 1 under the
  3 m/s wall jet, so no wall function sets the heat or the vapour reaching the glass.
- **The mist in the air.** After every step any vapour above saturation in a cell condenses into
  droplets carried with the air, a second `scalarTransport`, `L`, and where the air is below
  saturation the mist evaporates back. Its latent heat goes to the air in the next step's energy
  equation. This is the saturation adjustment of cloud models: liquid clouds lose their
  supersaturation in "τp ∼ 1–10 s" (Korolev and Mazin, J. Atmos. Sci. 60, 2003, section 8), short
  against the cabin's flow. The mist moves with the air (a 5 µm droplet settles at 0.8 mm/s by
  Stokes' law), is laid on no wall and does not wet the screens. Condensing the excess onto the
  trim and floor at once instead would take it out faster than any surface could: at ISO 6946's
  convective coefficient the side walls beside a cell would need about 370 s to draw an excess out
  of it. On recirculation the heater evaporates the mist it draws in, so its air carries the
  intake's vapour and mist together.
- **What the section cannot hold.** A section has no side windows, doors or pillars, and none of
  the seats, carpet and console across the cabin's width. Taken alone, its walls let the heater
  warm the cabin far faster than a car's. So the section is taken as the cabin averaged across its
  width, and every cell of air carries what lies beside it (`setup_fields.py`, and the
  `hiddenHeat` and `sideGlass` sources in `make_case.py`):
  - side walls, 2/1.45 = 1.38 m² per m³ of air, at ISO 6946's inside resistance 0.13 m²K/W. Above a
    beltline from the windscreen's foot (0.80 m) to the rear screen's (0.94 m), between the A- and
    C-pillars and off the B-pillar, the wall is side glass, 0.90 m² of it in the car: a 3.1 mm
    toughened pane (US 9,950,945 B2 gives air-quenched side glass as 2.5-3.1 mm), losing heat to
    the 3 °C air, starting with 10 g/m² of mist and condensing and evaporating at ISO 6946's
    convective 2.5 W/m²K over c_p. Elsewhere it is door and pillar trim, a 3 mm plastic skin over a
    cavity (0.18 m²K/W) and the steel skin;
  - the cabin's contents, a heat capacity of 10 times the air's spread over the cabin and kept
    within 10 s of the air's temperature, the one number set to make the cabin warm as a measured
    car does (below).
- **The trim.** The dash, seats and wheel are a 3 mm plastic skin with heat capacity and no loss
  outward; the headliner is the same skin over a cavity and the steel roof, and loses heat upward.
  The occupants give their 72 W through the skin of their bodies as a fixed flux.
- **Mesh:** gmsh's, quad-dominant and recombined, one cell deep (`scripts/make_mesh.py`, gmsh
  4.15.2 from pip): 6 mm along the glass, 8 mm near the walls and 20 mm in the open cabin, the
  slot and duct a structured block of 4 mm cells, and the screens' and headliner's layer as three
  transfinite strips. 24,299 cells, 22,162 hexahedra and 2,137 prisms; `checkMesh` passes
  (largest non-orthogonality 58°, skewness 3.3). Both runs have the same mesh.
- **Writes:** the section every 1.25 s (`postProcessing/clip`, T, U, w and L), both screens face
  by face at every write (`postProcessing/glass`: x, y, temperature and film), and every 20 steps
  the screens' misted shares and films, the cabin's vapour, mist and mean temperature, the flows of
  air, vapour and mist through each opening, the air at the two heads and the side glass
  (`postProcessing/walls`).

## How fast the cabin warms

No defrost or demisting test found publishes the cabin's air temperature over time. The reference
is a cabin model fitted to measurement: Brusey, Hintea, Gaura and Beloe, "Reinforcement
learning-based thermal comfort control for vehicle cabins" (Mechatronics 50, 2018;
arXiv 1704.07899), fitted to a Jaguar XJ warmed and cooled in MIRA's climatic wind tunnel and read
at head-rest height. Its cabin node holds 8 times its air's heat capacity. Scaled to this cabin's
2.23 m³ and driven by this defroster (`scripts/warmup_reference.py`), it takes the cabin from 5 °C
to 17.7 °C in the first minute and 24.7 °C in two on outside air; on recirculation its supply rises
from 53.0 °C to 58.5 °C in a minute and 62.0 °C in two.

Short pilots on outside air, run before the mist and the breath placement were added and not repeated after, set the contents' heat capacity. At 10 s the reference is at 7.7 °C;
with contents of 4, 7 and 10 times the air's capacity the section's mean air was at 10.0, 8.6 and
7.8 °C. The runs use 10 times: less leaves the cabin too warm in the first seconds and would let
recirculation's supply run further ahead of the reference, favouring recirculation for a reason no
car has. Over the solved runs' first two minutes (`results/summary.txt`):

- **Outside air at the heads,** where the measurement was read, follows the reference within about
  2 K: 2.1 K above it at 20 s and 0.4 K below it at 120 s.
- **Recirculation's supply** decides how much warmer its jet is than outside air's. It follows the
  reference within 0.5 K for the first 40 s, then runs ahead, by 0.9 K at a minute and 1.7 K at
  two. At two minutes recirculation's jet is 11.5 K warmer than outside air's; 9.8 K of that is
  what the well-mixed reference gives with this heater, and 1.7 K is the section's.
- **The volume mean** runs below the reference in both, by 5.3 K at a minute and 9.1 K (outside)
  and 9.9 K (recirc) at two, because the cold floor and rear count in it; the footwell vents are
  shut in defrost mode.

**Recirculation takes a short path.** Its jet runs up the windscreen, turns down in front of the
driver and returns to the intake under the dash; outside air's runs along the headliner to the
shelf vent. So recirculation's rear cabin stays cold. At two minutes its heads are 9.1 K colder
than outside air's though its mean is 2.0 K warmer, and its intake draws air at 31.7 °C against
the cabin's mean 17.6 °C, which is why its supply runs ahead.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only outside`
  and `--setup-only recirc` wrote the solved runs' meshes (points, faces, owner, neighbour,
  boundary, zones and the occupants' cell sets), every initial field including the cells'
  barometric p and the side glass, door trim and contents fields, `0.orig`, `constant/` and the
  section's `geometry.json`, byte for byte, `checkMesh` OK at 24,299 cells. In `system/`,
  `fvSchemes`, `topoSetDict`, `changeDictionaryDict` and `decomposeParDict` are byte for byte the
  same; `controlDict` and `fvSolution` differ only in four comments. The decomposition on 8 ranks
  is scotch's, and a re-solve will not match the committed histories to the last digit.
- **The water budget closes.** Per metre of section, the change in the cabin's vapour and mist
  and the films on the screens and side glass against what comes in and goes out and the
  occupants' 140 g/h: on outside air within 0.33 % in every window, within 0.08 % from 2 s on; on
  recirculation within 1.33 % from 2 s on (2.6 % in the first second), the steady small shortfall
  falling to 0.46 % over 540-600 s.
- **No air stays above saturation** (`scripts/check_planes.py`, `results/planes_check.txt`). On the
  120, 300 and 600 s sections no cell of outside air's is above 100.5 % relative humidity. On
  recirculation 0.004-0.008 % of the section is, at most 103.0 %, all in the first cells, under
  1.5 mm², of the wall layers under the headliner and on the rear screen, where the latent heat of mist just
  formed has not yet reached the air.
- **The heater draws no mist.** On recirculation the intake's mist is exactly zero at every logged
  step to 600 s; its vapour rises from 5.4 g/kg at 30 s to 14.8 g/kg at 600 s, a dew point of
  about 20 °C.
- **Both runs ended cleanly** at 600 s, with 480 sections each.

## Results

`scripts/extract_results.py` on the two runs; `results/summary.txt` has every figure below.

| windscreen still misted | 1 min | 2 min | 3 min | 4 min | 5 min | 6 min | 7 min | 8 min | 9 min | 10 min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outside air | 100% | 93% | 83% | 60% | 31% | 12% | 1% | 1% | 1% | **0%** |
| recirculated air | 100% | 95% | 92% | 87% | 81% | 74% | 67% | 60% | 52% | **46%** |

The share is by length along the section's windscreen, face by face at the write; in a section
the length share is the area share.

**Outside air.** The jet lands on the foot of the windscreen and the clear edge climbs the glass;
the first face clears at 70 s. The film thins across most of the screen at once: at two minutes
86 % of the glass's length holds between half and nine-tenths of its starting film, and the
stretch over which the film tapers from 90 % of the start to clear is 960 mm of the 1,062 mm
screen. From seven minutes only the top 12 mm, then 6 mm, are left, and **the screen is clear
from 541 s**, just after nine minutes. The rear screen has no defroster: it starts to clear at
431 s, just after seven minutes, and is 88 % misted at ten. The occupants' water and the evaporated mist leave
through the rear vent, and the cabin's vapour stays between 9.3 and 9.6 g per metre of section throughout.

**Recirculation.** The occupants' water stays in the car. The heater's air is warm, 63.7 °C at
two minutes and 72.1 °C at ten, but it carries their water with it, 7.0 g/kg at two minutes and
14.8 g/kg at ten. The edge climbs more slowly, and at ten minutes **the top 46 % of the screen is
still misted**, clearing by about 6 points a minute (6.8 over 480-600 s, 5.6 over 540-600 s).
The top of the screen keeps its film and gains: at ten minutes it rises to 20 g/m² just below the
header, and to 26 and 35 g/m² on the last two faces at the header itself. Below it the film tapers over
150-310 mm of the glass from three minutes on. The rear screen stays misted. The cabin's vapour
doubles, from 9.5 to 19.0 g per metre, and 6.4 g of mist forms: half of it, 3.1 g, in the
headliner's first wall-layer cells, which is in effect water condensed on the cold headliner, and
the rest a fog of more than 1 g/kg over a third of the section, in the cold lower and rear
cabin, its mist-weighted mean at 0.72 m and 8.8 °C. The intake under the dash draws none of it.

**How each strip clears.** On both runs a face takes a median 65-70 s from half its starting film
to clear, but its last tenth goes quickly: a median of 7.5 s, 10 s at the 90th percentile and at
most 12.5 s, at the 1.25 s the glass is written.

The side glass the section stands for stays misted throughout in both runs.

## What the clip shows, and what it does not

**It shows** the section twice, outside air above and recirculation below, for the ten minutes
from the moment the blower starts, at 30 times real time: 1.25 s of flow a frame at 24 frames a
second, 20 s in all. The air is coloured by its relative humidity, capped at 100 %, navy where it
is dry and near white where it is saturated; the windscreen and rear screen are drawn pale where
they are still misted and dark where they have cleared; each panel's number is its windscreen's
misted share at that moment, rounded. The moving marks are parcels of air carried by the solved
flow on their own, slower clock: each frame carries them 0.1 s through the flow of that moment, a
twelfth of the 1.25 s the colour moves on. They show where the air is going at each moment, not
how far it gets. The side glass is counted in the model but not drawn.

**The windscreen above each section is a drawing.** It is the same glass as the driver would see
it, a trapezoid with a road behind it. The run gives the glass's state along its length only,
from the foot to the header in 6 mm faces, and the drawing lays that length up the glass's height
and fogs each strip by the film the run has left on it. The fog's opacity is
(film / 10 g/m²)^(2/3): full at the starting 10 g/m² and above, fading as the strip dries, and none
once the run has cleared it. A fixed number of drops that each lose water cover less and less of
the glass, the area they cover going as their volume to the 2/3; **this is a drawing choice that
follows the film, not a calculation of the light the mist scatters.** The water beads shrink as
evaporating drops do, by the d² law, the smallest vanishing first, and none is left on cleared
glass; the fog's grain and the beads' places are random texture, placed once.

**Because the section is 2-D, the clearing edge is drawn level across the whole width.** The run
says nothing about how the mist varies from side to side. In a real car the vents leave the
corners clearing last and the edge would be curved; the drawing does not guess at that.

**The number and the drawing are not the same measure.** The number counts every part of the
glass still carrying film, however thin, while the drawing fades with the film: on outside air at
five minutes the number is 31 %, of which only the top 14 % is drawn more than half fogged. The
number is a share of the screen's height; the drawn screen narrows toward the top, so by area the
top 46 % of its height is about 45 % of the drawn glass.

## What it cannot

- **The warm-up is matched to one fitted model, not to a defrost test.** It is matched where the
  measurement was read and where the two runs differ: outside air's heads within about 2 K, and
  recirculation's supply within 1.7 K over the first two minutes, running ahead by enough to give
  recirculation about a seventh of its jet's 11.5 K lead at two minutes. The section's mean air
  runs below the reference because its floor stays cold, and over ten minutes the reference's slow
  interior mass and the section's walls and contents need not agree.
- **Recirculation's air takes a short path.** It returns from the windscreen to the intake under
  the dash and leaves the rear of the cabin cold, colder than a real cabin's. A car's jet also
  spreads sideways, and its rear would warm more evenly. The windscreen's number depends on the
  jet, and the jet is checked above.
- **The mist is a simple model.** It forms at once, moves with the air, and evaporates where the
  air can take it. It does not settle or deposit on the trim, and it does not wet the screens. The
  heater evaporates recirculation's mist without cooling its air for that, though the intake never
  draws any. The fog in recirculation's cold rear, more than 1 g/kg over a third of the section,
  would be droplets large enough to settle onto the rear seat and floor within minutes; either way
  it does not reach the intake. Vapour diffusing into the first, 0.1 mm cells of the cold headliner
  condenses there as mist that cannot leave, since the droplets have no molecular diffusion: on
  recirculation that is half its mist, in effect water condensed on the headliner, and no figure
  should be read from the mist's maximum.
- **A section has no sides to its windscreen.** The defroster's jet is a sheet across the whole
  width. In a car the screen's corners, away from the nozzles, clear last: a demisting test of a
  Fiat found regions with no air speed that "did not demist at the end of the 10 minutes test"
  (Zolet et al., COBEM 2011). The share here is along the driver's line of sight.
- **One car on one morning.** The heater's warm engine and effectiveness, the 90 % morning and the
  starting film are assumptions, stated above. A cold engine gives no heat for the first minutes,
  and then neither intake clears anything; a thicker mist clears later in both runs and stretches
  the comparison out in time.
- **The A/C is off.** With a compressor that runs, recirculation's air would be dried at the
  evaporator, and the two runs could come out the other way round.
- **The side windows** are carried cell by cell as glass beside the air, not drawn or solved as
  surfaces.
- No air leaks into or out of the cabin other than at the rear vent. The occupants do not move or
  breathe as jets. No sun or radiation between the glass and the cabin is modelled, beyond what
  ISO 6946's inside resistance holds.
- **One mesh, unsteady RANS,** k-omega SST, one realization of each run, no mesh or time-step
  study.

## How the case got here

The first build had no mist in the air: the occupants' water went into every cell touching their
bodies by volume, 46 % of it below 0.5 m around the shins and feet (0.6 % here), and with nothing
to condense it the cold lower cabin held vapour far above saturation. That set recirculation's
number (42 % at ten minutes). Both runs were solved again with the mist and with the water given
off at the breath and the upper body, which is the case here; outside air's number was unchanged
to the printed digit until five minutes, and recirculation's became 46 %. Pilots of the reworked model found two still
pockets of mist, between the back of the driver's head and the headrest and between the rear
passenger's back and the seat, fed by skin pressed against a seat; skin within 25 mm of a seat
gives its water to the seat, and those cells were taken out of the source with each occupant's
total unchanged.

## Sources

- Commission Regulation (EU) No 672/2010, Annex II: the demisting test, at −3 °C, with "70 ± 5 g/h"
  of steam for each seating position, "Vision area A ... shall be 90 % demisted in 10 minutes".
- T. Sadananda, "Improving the Accuracy of CFD Method for Windscreen Deicing", MSc thesis, Chalmers
  University of Technology with Volvo Cars, 2016:
  https://publications.lib.chalmers.se/records/fulltext/244746/244746.pdf
- J. Brusey, D. Hintea, E. Gaura and N. Beloe, "Reinforcement learning-based thermal comfort control
  for vehicle cabins", Mechatronics 50, 2018; arXiv 1704.07899.
- A. Korolev and I. Mazin, "Supersaturation of water vapor in clouds", J. Atmos. Sci. 60, 2003.
- ASHRAE Handbook of Fundamentals, heat gain from occupants ("seated, very light work").
- ISO 7730 and P. O. Fanger (1970), the latent heat of respiration and the skin, as implemented in
  Berkeley CBE's pythermalcomfort.
- ISO 6946: internal and external surface resistances and unventilated air layers.
- Mazda CX-5 owner's manual (EU English): the air conditioner and low outside temperatures.
- Met Office, Heathrow climate data 1991-2020.
- US 9,950,945 B2: the thickness of air-quenched side glass.
- L. Zolet et al., COBEM 2011, a windscreen demisting test and its CFD.
- M. Mutlu, G. Sevilgen and M. Kılıç, International Journal of Vehicle Design 71, 2016; and
  R. Mehdipour et al., International Journal of Engineering 30(7), 2017: their assumed starting
  films.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy,
shapely and gmsh (`pip install gmsh==4.15.2 shapely numpy`; set `PYTHON` to the interpreter that
has them if it is not `python3`). Another gmsh version will mesh the same outline but not to the
same cells. `scripts/check_planes.py` also needs VTK for Python.

    cd cases/foggyWindscreen
    ./Allrun outside                 # [nProcs], default 8
    ./Allrun recirc
    python3 scripts/extract_results.py runs results
    $PYTHON scripts/check_planes.py runs/recirc 120 300 600

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the Allrun
written there: gmsh (`make_mesh.py`), gmshToFoam, changeDictionary for the patch types, checkMesh,
topoSet for the occupants' water, the cells' barometric pressure and the fields for the side
glass, door trim and contents (`setup_fields.py`), and decomposePar. It then solves 0-600 s,
writing the section every 1.25 s and keeping the last two full fields. The coded source and
function object compile on first use. `./Allrun --setup-only <run>` stops before the solve, in
under a minute. `./Allclean` removes the runs.

The solved runs took 9,136 s (outside) and 14,001 s (recirc) of wall time on 8 ranks each, side by
side on a machine shared with other solves: 516,000 and 744,820 time steps. The gzipped sections
take about 0.4 GB a run. `results/` holds each run's history at every write (both screens' misted
share, film and temperature, the cabin's air, the air at the heads, the supply, the intake's water,
the cabin's vapour and mist), the film along the windscreen face by face every 30 s, the plane
checks and the summary; no fields, meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine; the first build's water
held above saturation was found in its checks, and both runs were solved again with the mist
before the clip was made.
