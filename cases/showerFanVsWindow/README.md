# After a shower: the extractor fan, or the window on tilt

After a winter shower some people tilt the bathroom window open, and others keep it shut and
run the extractor fan, and the advice in print goes both ways. This case takes a small bathroom
with the door shut on a still 0 °C morning, runs one ten-minute shower in it, and then follows
the fifteen minutes after the shower twice: once with a ceiling extractor at the UK Building
Regulations bathroom rate and the window shut, and once with the window on tilt and the fan
off. It asks **what share of the shower's water vapour has left the room**, where the moist air
goes, and how humid the air the two rooms leave behind is. It does not model condensation or
mould, and its number is the vapour removed, not the water.

    ./Allrun shower    # 0-600 s from rest: the shower on, everything shut
    ./Allrun fan       # 600-1500 s: the fan at 15 l/s, the window shut
    ./Allrun window    # 600-1500 s: the window on tilt, the fan off

**The result.** Of the vapour in the room when the shower stops, **the fan has taken out 76%
fifteen minutes later and the tilted window 86%**. The two move about the same air, 4.8 room
volumes an hour, but the window takes more of the moist air out with it, and it also cools the
room by 9 K. On these assumptions, a still morning, an undercut door to a hall at 20 °C,
walls held at 20 °C and no condensation, the window does better on vapour removed, and the
room it leaves is the drier of the two at the end, 56% against 67% relative humidity on
average on the section, though for some minutes in the middle it keeps a thin saturated layer
under its ceiling that the fan room has lost. [What it cannot](#what-it-cannot) says which of
those assumptions favour which.

The window is [`windowAiring`](../windowAiring)'s tilted sash, unchanged, and the gas model is
[`dryIceCauldron`](../dryIceCauldron)'s with its CO2 replaced by water vapour, but this is a case
of its own and not a third run of either: the room is a 2.5 × 2.0 m bathroom with a bath, a
shower, a ceiling fan grille and a door with an undercut, both branches start from one solved
shower, and the question is about vapour, not the room's own air. None of `windowAiring`'s or
`dryIceCauldron`'s runs changes, and none of their scripts is used.

## The bathroom

Coordinates as `windowAiring`: x into the room from the inside face of the window wall, y up from
the floor, z across the room.

- **The room:** 2.50 m from the window wall to the door wall (x = 0 to 2.50), 2.00 m wide
  (z = -1.00 to 1.00), 2.40 m high: 12.0 m³, **11.35 m³ of air** less the bath.
- **The bath:** a solid block 0.70 m deep, 1.70 m long and 0.55 m high against the window wall
  and the end wall z = 1.00 (x = 0 to 0.70, z = -0.70 to 1.00, y = 0 to 0.55), adiabatic.
- **The fan:** a 0.10 × 0.10 m grille in the ceiling above the shower (x = 0.30 to 0.40, z = 0.40
  to 0.50). Shut, it is part of the ceiling. Running, it takes out **15 l/s**, the minimum
  intermittent extract rate for a bathroom in Approved Document F, Volume 1 (2026), Table 1.1,
  fixed by its boundary condition. It is in the ceiling, as ADF's paragraph 1.16 asks ("as high
  as is practicable", within 400 mm of the ceiling), and across the room from the door.
  Paragraph 1.51 has a fan in a room without an openable window run on for at least 15 minutes
  after the room is vacated, which is where the fifteen minutes come from.
- **The door:** 0.76 m wide in the wall x = 2.50 (z = 0.07 to 0.83), shut, with a **10 mm
  undercut**, the 7,600 mm² of ADF's paragraph 1.21. Beyond it the hall is air at 20 °C held at
  its barometric pressure, with none of the shower's vapour.
- **The window:** `windowAiring`'s opening (1.0 m wide, 1.2 m tall, sill 0.90 m up) and its
  tilted sash, an 80 mm solid profile seated 50 mm in the frame with its top swung 140 mm into
  the room, moved along the wall to z = -0.30 to 0.70, so that one section passes through the
  window, the shower, the fan and the door. On this mesh its gaps are 0.0800 m² at the top and
  0.0342 m² down each side, the same as `windowAiring`'s tilted run. Shut, it is the wall's face.
- **Outside:** `windowAiring`'s still 0 °C box, 1.5 m deep beyond the 0.24 m wall, y = -1.0 to
  3.4, z = -2.30 to 2.70, its open faces and every cell at the start at the barometric pressure
  1e5 exp(-g y/(R T)).
- **The house's pressure:** with the window on tilt the room has two openings, the window and the
  undercut, and what passes under the door depends on the house's neutral pressure plane. It is
  put at the window's mid-height: the hall's pressure equals the still outdoor air's at y =
  1.5 m. In the fan run the hall's pressure only sets the room's pressure level, since the fan's
  flow is fixed.
- **Surfaces:** the floor, walls, ceiling, the shut window, the shut grille and the door held at
  20 °C; the bath, the reveal, the sash and the wall's outer face adiabatic.

## The shower

A shower head on a rail on the end wall over the bath. Its spray is a box 0.40 × 0.40 m from the
bath's rim to the head (x = 0.15 to 0.55, z = 0.25 to 0.65, y = 0.55 to 1.95; 19,740 cells, 0.224
m³), and from t = 0 to 600 s it releases **0.17 kg of water vapour** (0.2833 g/s) and **300 W of
sensible heat**, both spread evenly over the box (`constant/fvOptions`). The spray's drag on the
air is left out, and there is no shower curtain and no person.

- **The vapour.** TenWolde and Pilon (2007) review the measurements: Hite and Bray (1949) found
  that an average shower adds 0.11-0.23 kg of water vapour to the air, not counting what
  condenses on walls, mirrors and windows. 0.17 kg is the middle of that range. In 11.35 m³ it is
  a mean excess of 15 g/m³, between the 6 g/m³ of Bailes's logged shower and the "up to 20 g/m³
  ... for brief periods only" of the field study by Hafnor et al. (2022). Larger figures, such
  as IEA Annex 14's 0.2 kg for three minutes, include what condenses, which this model cannot.
- **The heat.** No measurement of the sensible heat a shower gives the air was found. 300 W is
  our estimate, chosen so that, against 20 °C walls, the air ends the shower at about 24 °C,
  where Bailes's logged shower put it (dew point 14.5 to 21 °C at a peak of 85%). The run gives
  **24.0 °C**, the room's mass-weighted mean at 600 s.

The stages share one shower. **shower** runs 0-600 s from rest with the door, the window and the
fan shut. **fan** and **window** both start from its 600 s state and run to 1500 s: fifteen
minutes after the shower stops.

## The model

- `rhoReactingBuoyantFoam` (OpenFOAM v2512) with O2, N2 and H2O as perfect gases, JANAF
  thermodynamics and no reactions, as `dryIceCauldron`, so moist air is lighter than dry air at
  the same temperature. Sutherland viscosity, with air's coefficients given to H2O too, which at
  a few grams per kilogram does not matter. k-omega SST with buoyancy's production of
  turbulence (`buoyancyTurbSource`), wall functions, species diffusing with mu_eff (Schmidt
  number 1), Euler in time, two outer and two pressure correctors, H2O and the other species
  bounded to 0-1 by `limitedLinear01`.
- **H2O is the shower's vapour only.** The room's, the hall's and the outdoor air's own humidity
  is not carried; it is added afterwards for the relative humidity (below). The vapour source
  acts on the H2O equation alone and not on the mixture's mass, so the vapour takes the place of
  nitrogen; the 0.17 kg is 1.3% of the room's air.
- **No condensation anywhere.** In the air the vapour stays vapour, however far above saturation,
  and none deposits on or evaporates from a surface.
- **The mesh.** One graded blockMesh box of 1,027,200 cells over the outdoor air, the wall and
  the room, cut down with `subsetMesh` as in `windowAiring`, every edge of the bath, the spray,
  the grille, the undercut, the window and the sash on a grid line. Cells are 20 mm across the
  window's width (z = -0.3 to 0.7) and 32-40 mm beyond it; 17-21 mm in x over the first 0.55 m from
  the window wall and 40 mm beyond 0.7 m; 30 mm in y over the window's height, one 10 mm cell up
  the undercut, finer towards the floor. The shower and fan runs share the room's mesh, **445,744
  cells**; the window run's mesh adds the reveal and the outdoor box and takes out the tilted
  sash, **634,768 cells**, 437,892 of them at x ≥ 0. Its room cells are the room mesh's, cell for
  cell, but for the 7,852 the sash takes; its room holds 11.2589 m³ of air against 11.3455.
  `checkMesh`: Mesh OK for both.
- **The time step:** Courant number 1 in the shower and window runs and **2 in the fan run**. The
  fan's grille draws air at 1.5 m/s on average through 20 × 30 mm cells, and at Courant 1 those
  cells held the step to about 0.007 s; the fan run was projected at 14 h alone on 16 ranks. A
  15 s run at Courant 2 from the same 600 s fields, set against `fanCo1` (Courant 1) over 600-615 s,
  took the same vapour out to 0.006% and the same fan mass flow to 0.002% (Checks), and the fan
  run is that run continued.
- **Output:** a coded function object, `scripts/moistureBudget`, writes at every step the room's
  vapour, mass and temperature, the shower's source as the solver applies it, and for the grille,
  the undercut, the window's opening at x = 0 and each of the sash's three gaps the gross mass
  flow each way and the vapour carried out by convection (with the solver's own convection scheme)
  and by diffusion. The sections z = 0.455 m (the clip's) and z = 0.205 m are written every 1.25 s
  in the branches and every 5 s in the shower; the fields every 60 s, the last two kept.

### The tracer of the outdoor air

The window run carries one more scalar, `outdoorAir`, the share of each cell's air that came in
from outdoors: 1 in the outdoor box and the reveal at 600 s and on inflow through the outdoor
box's faces, 0 in the room at 600 s and under the door. A `scalarTransport` function object carries
it with the solver's phi and rho and diffusivity mu + mu_t, the mu_eff the species equation gives
H2O, with H2O's scheme. It changes nothing the solver solves. It is there for the relative
humidity: outdoor air at 0 °C brings far less water in than the room's air holds. Its
`writeControl writeTime` is needed: without it the function object writes the field at every time
step, a directory a step.

## The share

The number is **1 − W(t)/W(600 s)**, W the room's integral of the shower's vapour from the monitor,
each branch over its own 600 s inventory. For the fan that is the shower's 169.995 g. The window
run's room starts with 168.403 g: mapping the shower onto the window mesh drops the 1.593 g that sat
in the cells the tilted sash takes. Over the 169.980 g the shower released instead, the window's
share at 1500 s is 86.62% rather than 86.49%, and the fan's 76.45% either way; the rounded numbers
do not change. The undercut let out 0.0025 g of vapour during the shower.

## Results

`scripts/extract_results.py` writes, from the three runs' monitors and sections,
`results/summary.txt`, each run's history every 5 s (`results/<run>/history.csv`) and the
relative humidity on the section every 15 s (`results/section_rh.csv`).

| | fan on, window shut | window on tilt, fan off |
|---|---:|---:|
| **share of the vapour in the room when the shower stops that has left it**, 1 min later | 9.9% | 15.7% |
| 3 min | 28.8% | 42.4% |
| 5 min | 45.5% | 59.2% |
| 10 min | 65.9% | 77.7% |
| **15 min** | **76.4%** | **86.5%** |
| air in, mean over the 15 min | 54 m³/h (0.0179 kg/s) of 20 °C hall air under the door | 54 m³/h (0.0190 kg/s) of 0 °C air through the sash, and 7.6 m³/h (0.0025 kg/s) under the door |
| the room's mean air temperature at 600 / 900 / 1500 s | 24.0 / 20.8 / 20.1 °C | 24.0 / 16.3 / 15.0 °C |
| vapour out by 1500 s | 130.0 g through the grille, none under the door | 145.3 g through the sash, 0.42 g under the door into the hall |

The fan takes out 15.00 l/s, 54 m³/h, 4.76 room volumes an hour. The window takes in 53.9 m³/h of
0 °C air through the sash, 4.79 room volumes an hour. It reaches the room through the two side
gaps (0.0182 kg/s in, 0.0043 out), none through the top gap, which carries most of the room's air
out (0.0155 kg/s); the rest of the sash's inflow turns back within the wedge behind it. Fully
mixed air at 4.76 volumes an hour would lose 70% of its vapour in fifteen minutes; the fan does a
little better than that, and the window clearly better.

**Why the window takes more out with about as much air.** Both draw on the warm moist layer the shower
leaves under the ceiling, the grille from right above the shower and the top gap from the top of
the window. The vapour fraction of the air leaving, over the room's mean, was 1.31 for the fan and
1.64 for the window over the fifteen minutes. In the last five minutes the fan's air was no moister
than the room's average (0.93), and the window's still 1.25 times it. The cold air from the side
gaps falls over the bath and spreads across the floor under the warm moist air, which stays under
the ceiling, where the top gap takes it: at 3 min the window room's saturated air on the section
lies above 1.85 m, the fan room's reaches down to 0.8 m. The fan room stays warm and mixes, and by
its last five minutes its exhaust is no moister than its average. The rest is the door: hall air
came in under it (below), which added 11.8% to the dry air coming into the window room.

**The undercut helped the window for its first ten minutes.** The neutral plane was put at the
window's mid-height to leave the undercut nearly idle in the window run. It did not. Hall
air came in under the door at 9.0 g/s on average over the first minute, against the sash's 22 g/s,
falling minute by minute to 0.4 g/s in the tenth (`results/summary.txt`), although the room's mean
temperature was below the hall's 20 °C from 91 s after the shower. The window's exchange held the
room's pressure at the floor below the hall's. From the eleventh minute the flow reversed, and by
1500 s it had carried 0.42 g of vapour into the hall, 0.25% of what the room held at 600 s, which
the share counts as gone. A house whose neutral plane sits lower would push more hall air in and
help the window more; one where it sits higher would push the bathroom's moist air out into the
house.

**The window cools the room by 9 K**, to 15.0 °C at 1500 s against the fan room's 20.1 °C, with
the walls held at 20 °C throughout. By 1500 s 77% of the window room's air by mass came from
outdoors (the tracer).

### Relative humidity

Colder air holds less water, so the vapour left in the window room sits nearer saturation than its
amount alone says, and the outdoor air that replaces the room's own brings less water in. The runs
carry only the shower's vapour, so the humidity is built afterwards, face by face on the section
z = 0.455 m (the clip's), with the shower's vapour s, the temperature and, in the window run, the
outdoor air's share f from the tracer:

- the background: the room's and the hall's air at **7 g of water per kg of dry air** (20 °C at about
  50%), and the outdoor air at **0 °C and 95%**, 3.65 g per kg of dry air, the external condition
  BS 5250:2011 (Annex D, D.3.4) uses for its humidity classes;
- the water's mass fraction q = s + f q_out + (1 − s − f) q_in, its partial pressure p r/(r + M_w/M_air)
  with r = q/(1 − q) at p = 1e5 Pa (the sections carry no pressure; the window run's spans
  99,959-100,011 Pa, which moves the humidity by less than 0.05%), over the saturation pressure
  610.94 exp(17.625 t/(t + 243.04)) Pa (Alduchov and Eskridge's form of Magnus's), t in °C.

The fan run has f = 0: its air all came from the room or the hall, which share the 7 g/kg. The
shares below are by area over the room's part of the section (x > 0):

| on the section, minutes after the shower | 0 | 1 | 2 | 3 | 5 | 6 | 8 | 10 | 15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fan: share at or above saturation | 78% | 64% | 50% | 39% | 18% | 4.3% | 0.04% | 0 | 0 |
| window | 78% | 55% | 51% | 22% | 12% | 9.0% | 5.3% | 0.5% | 0 |
| fan: mean relative humidity | 101% | 103% | 102% | 99% | 89% | 85% | 79% | 75% | **67%** |
| window | 101% | 105% | 104% | 100% | 89% | 86% | 77% | 70% | **56%** |

At the end of the shower 78% of either room's section is at or above saturation, the mean 101%
and the highest 130%: with no condensation the air holds what a real bathroom would put on the
mirror, the window and the walls, or as mist. The window room has less saturated air than the fan
room, or about as much, for the first two minutes (55% against 64% at 1 min, 51% against 50% at
2 min), and clearly less from then until five and a half minutes (22% against 39% at 3 min). After
that the fan room's last saturated air goes, by just after 8 min, while the window room keeps a thin
saturated layer under its cooling ceiling, the top 0.4 m at 6 min narrowing to under 0.1 m, until
about 10 min (9.0% against 4.3% of the section at 6 min). By 15 min neither has saturated air,
and the window room is the drier, 56% against 67% on average. Air at 100% here is air in which
water would condense on a cool surface or as mist, not air that has.

The monitor's own saturated volume (`satVolume`, `satWater`) adds 7 g/kg to every cell, outdoor air
included. That holds for the fan run and not for the window run, whose incoming 0 °C air cannot hold
7 g/kg, so it is not used.

## Checks

- **The vapour budgets close**: the room's vapour at the end, less at the start, less the source,
  plus what left through the grille, the undercut and the window's opening, is within 0.0105% of
  the release over the shower, 0.033% of the 600 s inventory for the fan and 0.0275% for the window.
- **The shower's source** gave 169.980 g over 600 s, 0.2833 g/s, as set.
- **The fan's flow:** 15.00 l/s at the grille, 0.0176 kg/s; the make-up air under the door 0.0179
  kg/s in and none out over the fifteen minutes (the room's air contracts as it cools).
- **The fan's Courant number** (`fanCo1`, 600-615 s): the vapour out 4.29031 g at Courant 1 against
  4.29008 g at Courant 2 (-0.006%), the fan's mass flow 0.0172063 against 0.0172065 kg/s, the
  undercut's inflow 0.0184760 against 0.0184747 kg/s, the vapour left in the room 165.7054 against
  165.7047 g; 2,071 steps against 1,094.
- **The window's exchange against `windowAiring`.** The same sash in `windowAiring`'s bigger room
  took in 0.0229 kg/s on average over its five minutes, with that room at 19.2 °C on average
  (its `results/tilted/history.csv`). Buoyant exchange through a fixed opening goes as the square root
  of the temperature difference, which scales that to 0.0213 kg/s at this room's mean 16.5 °C over
  the fifteen minutes; the run's 0.0190 kg/s is 89% of it, and 89% over the first minute too. The
  top gap carries the outflow and the two side gaps the inflow, as there.
- **The tracer** stayed within -4.2e-11 and 1.0000157 over the run (every tenth step).
- **The still outdoor air:** at 601.25 s, on the plane y = 1.5 m beyond the wall and clear of the
  window (x < -0.24 m, z < -1.3 or > 1.7 m), median 1.6e-4 m/s and largest 5.7e-4 m/s.
- **The shower's heat:** the room's mean air temperature is 24.0 °C at 600 s, the estimate's target.
- All the solves end in `End`. `k` is held at its 1e-15 floor in some steps (`bounding k`), as in
  the other buoyant room cases.

## How the case got here

The case was set up by an agent from a brief, `windowAiring`'s generator and `dryIceCauldron`'s
species model, and checked by us; the runs were solved on our own machine on 16 ranks.

- **The shower** ran 0-30 s as a pilot, then 30-600 s, restarted from the 30 s fields. That run
  ended at 600 s but had written its last fields at 570 s (field writes counted from 30 s), so
  570-600 s was run again from the 570 s fields to write 600 s. The monitor's history keeps the
  rerun's rows for 570-600 s. 21,811 steps, 2.7 h in all.
- **The fan** at Courant 1 projected 14.3 h alone on 16 ranks. The fan run here is the Courant 2
  pilot, 600-615 s, continued from its 615 s fields to 1500 s: 66,872 steps, 12.2 h. `fanCo1`,
  the Courant 1 check, ran 600-630 s on 8 ranks (and on to 645 s on 16); only its 600-615 s is
  used.
- **The fan runs' hall.** `make_case.py branch fan` writes the undercut's total pressure p0 as the
  uniform 1e5 Pa of the field template, as the solved fan runs had it; the shower's barometric value
  there, 99,998.67 Pa, was not carried over. With the fan's volume flow fixed, this sets the room's
  pressure 1.3 Pa higher and gives a small step at 600 s, nothing more.
- **The window** was first solved without the tracer (600-630 s on 8 ranks, then 630-645 s and
  645-1500 s on 16, each restart from the saved fields). It removed 86.52% of its 600 s vapour by
  1500 s. Its saturated share could not be read: the runs carry only the shower's vapour, and in the
  window room up to three quarters of the air came from outdoors, with a background unknown cell by
  cell. The window run was then solved again from the same 600 s fields with the tracer, in one run
  600-1500 s on 16 ranks (37,961 steps, 6.0 h): that is the window run here and the only one the
  results use. It removed 86.49%, and its vapour removed by 630 s was within 0.04% of the first
  run's. Its first launch stopped within half an hour because the tracer's function object had no
  `writeControl` and wrote the field at every step until the disk was full; `writeControl
  writeTime` fixed that, and it is in `make_case.py`.
- **The tracer's starting field.** The 600 s post-processing that writes the first sections and
  the monitor's first row runs the tracer's transport once and writes it back over
  `600/outdoorAir`, moving it by at most 1e-5 (to -9.4e-6 in the room next to the sash). The
  solved run started from that field, and `Allrun` does the same.

## What the clip shows, and what it does not

The clip shows the section z = 0.455 m through the window, the shower, the grille and the door,
fan on above and window on tilt below, from the moment the shower stops to fifteen minutes later,
at 45 times real time over 20 s. The colour is the relative humidity above, from white at 50% to
the deepest blue at 100%, clipped there, so that saturated air, and the model's supersaturated air,
is the deepest blue; air below 50% is white: about 5% of the section, the dry floor layer, in the
first frames, and 1.6% of the window room's at the end.
The fan panel's mesh has no outdoor air, and its strip beyond the shut window is drawn as still 0 °C
air at 95%. Moving parcels follow the solved velocity in the plane. The number in each panel is the
share above, ending at 76% and 86%. The clip's humidity was interpolated from the section to a pixel
grid, so its shares differ from the area-weighted ones here by up to a point (for instance 0.3%
against 0.5% saturated in the window room at 10 min).

## What it cannot

- **Condensation and mould.** Vapour that would condense on the window, the mirror and the walls
  stays in the air, and nothing evaporates afterwards from wet surfaces, towels or the bath. The
  share is the vapour removed, not the water. A real bathroom loses part of its vapour to its
  surfaces, and a colder room more of it, which these runs leave out.
- **The background humidity is assumed.** 7 g/kg indoors and 0 °C at 95% outdoors are not
  measured; 95% is on the moist side of a winter morning, and drier outdoor air would only lower
  the window room's humidity. They enter the humidity, not the share.
- **Still air outside.** Wind drives a tilted window far harder than buoyancy on most days, and
  would change the window's number most.
- **The door and the hall.** The neutral plane at the window's mid-height gave the window run 11.8%
  of its air from the hall; another house would give it more or less. The hall is endless 20 °C air.
- **Walls held at 20 °C.** They keep warming the window room as it cools, and the shut window is not
  cold glass. A real window room would cool more and its surfaces would be colder.
- **A fixed 15 l/s.** The guidance's minimum; a real fan against a duct and a 10 mm undercut often
  moves less.
- **One shower, nothing during it.** A fan wired to the light also runs during the shower, and some
  people open the window then; both panels share one shower with everything shut. The fan and the
  window together were not run.
- **The shower** is a box of vapour and heat: no spray drag, no person, no curtain. Its 300 W is
  our estimate, checked only by the 24 °C it gives.
- **The vapour displaces nitrogen** instead of adding to the air's mass (1.3% of it).
- **The window run's room** is 1.6 g of vapour short at 600 s, the vapour in the sash's cells.
- **One section, one mesh.** The humidity is read on one vertical section, not over the room's
  volume. No mesh study; k-omega SST URANS with wall functions; the fan at Courant 2, checked over
  15 s; one realization each.

## Sources

- HM Government, The Building Regulations 2010, Approved Document F, Volume 1: Dwellings, 2026
  edition (assets.publishing.service.gov.uk/media/69c12224d588c92c483e4b6a/ADF1_2026.pdf): Table 1.1
  (15 l/s), paragraphs 1.16 (the fan's height), 1.21 (the 10 mm undercut, 7,600 mm²) and 1.51
  (15 minutes' run-on).
- TenWolde and Pilon, "The Effect of Indoor Humidity on Water Vapor Release in Homes",
  Buildings X, ORNL 2007 (web.ornl.gov/sci/buildings/conf-archive/2007%20B10%20papers/071_TenWolde.pdf),
  for Hite and Bray (1949), 0.11-0.23 kg a shower, and IEA Annex 14.
- Hafnor, Holøs, Aurlien and Thunshelle, CLIMA 2022
  (proceedings.open.tudelft.nl/clima2022/article/view/65): bathroom moisture excesses up to 20 g/m³.
- Bailes, GreenBuildingAdvisor, 26 Dec 2024
  (greenbuildingadvisor.com/article/running-bath-fans-to-control-humidity): a logged shower with
  no fan.
- BS 5250:2011, Code of practice for control of condensation in buildings, Annex D, D.3.4, p. 29: 0 °C
  and 95% outside.
- O. A. Alduchov and R. E. Eskridge, "Improved Magnus form approximation of saturation vapor
  pressure", Journal of Applied Meteorology 35 (1996) 601-609.
- The sash: [`windowAiring`](../windowAiring), "The window" (Roto NT's 140 mm tilt, Winkhaus).

No third-party files are in the case.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/showerFanVsWindow
    ./Allrun shower          # [nProcs], default 16; reconstructs its 600 s at the end
    ./Allrun fan             # needs runs/shower/600
    ./Allrun window          # needs runs/shower/600
    ./Allrun fanCo1          # optional: the fan's Courant check, 600-615 s
    python3 scripts/extract_results.py runs results

`Allrun` writes the run into `runs/<run>/` with `scripts/make_case.py`: for shower and window it
meshes the box with blockMesh, topoSet, subsetMesh and createPatch, writes the barometric starting
pressure, and (window) maps the shower's 600 s onto the window mesh with mapFields and puts the
outdoor air back to rest; fan copies the shower's mesh and 600 s fields. It then checks the mesh,
writes the first sections, decomposes and solves; once shower, fan and window have solved it writes
`results/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the
runs. The coded function object is compiled by OpenFOAM the first time it runs.

On 16 ranks the shower took 2.7 h, the fan 12.2 h and the window 6.0 h of wall time. The sections
are about 0.8 MB (fan) and 1.2 MB (window) a write, 721 writes in each branch; gzip takes them to
about a quarter.

Checked from a clean clone: `./Allrun --setup-only shower` writes the solved run's mesh (points,
faces, owner, neighbour, boundary and the cell, face and point zones) and every 0/ field byte for
byte, and its t = 0 sections byte for byte. Given the solved shower's 600 s fields,
`--setup-only fan`, `fanCo1` and `window` write the solved runs' meshes and every 600 s field byte
for byte, but for the window's tracer, which equals the field the solved run started from (its
decomposed 600 s, reconstructed) but for 21,413 cells below 1e-300 that it holds as 0; the 600 s
sections byte for byte, but for the window's tracer on them (the solved run's 600 s sections came
from a second post-processing); and the monitor's first row exactly. Expanded, every dictionary
holds the solved runs' values but for the interval between field writes, 60 s here, which the
solved runs changed between restarts (30, 15 and 45 s at the end), and `fanCo1`'s end, 615 s here
against the 645 s its run went on to. The scotch decomposition is not compared.
`scripts/extract_results.py` on the solved runs writes `results/` byte for byte.
