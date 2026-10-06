# PC case fans: more in, or more out

PC builders argue over whether a case's fans should push more air in than they pull out
("positive pressure") or the other way round ("negative"). Positive is said to keep dust
out, because every gap blows outward, and to cool worse; negative is said to cool better
and to pull dust in through every unfiltered gap. This case puts the same PC through three
fan layouts and measures the air each part breathes:

    ./Allrun positive    # 3 front fans in, rear fan out
    ./Allrun negative    # 1 front fan in, rear and 2 top fans out
    ./Allrun even        # 3 in, 3 out
    ./Allrun viewer      # a viewer's build: 2 bottom fans, rear and rear top fan in,
                         # front top fan out, no front fans, the CPU cooler turned round
    ./Allrun twoInTwoOut # another viewer's build: 2 low front fans in, rear and
                         # rear top fan out
    ./Allrun positive dust  # either layout again, with the room's dust carried on its flow
    ./Allrun negative dust
    ./Allrun aioFrontIn  # a third viewer's build, the CPU on an all-in-one liquid cooler:
                         # 3 front fans in, rear and 3 top fans out, a 360 mm radiator on top
    ./Allrun aioFrontBottomIn  # the same with two bottom fans in as well

The published clip shows `positive` against `negative`. `even` is here because equal fan
counts are not equal flows: two 140 mm top fans and a 120 mm rear fan move more air than
three 120 mm front fans, so "3 in, 3 out" is slightly negative. `viewer` is the first layout
asked for in the clip's comments, on the same PC with its cooler turned round and two bottom
fans added; it has [its own section](#a-viewers-layout-bottom-intakes-and-the-cooler-turned-round).
`twoInTwoOut` is a second, from another comment, using only the fan positions the PC already
has; it has [its own section too](#a-second-viewers-layout-two-in-two-out). The clip's
comments also said the choice is about dust, not temperature, so `positive` and `negative`
were run again with the room's dust carried on the flow; that has
[a section of its own as well](#dust-where-the-rooms-dust-goes). `aioFrontIn` and
`aioFrontBottomIn` are a third viewer's build, asked for under the `viewer` layout's clip,
with the tower cooler replaced by an all-in-one liquid cooler and three top fans; they are in
[the last section](#a-third-viewers-layouts-a-liquid-cooled-cpu-with-and-without-bottom-intakes).

## The PC

A generic mid-tower, built by us from public form-factor sizes rather than downloaded:
`scripts/build_geometry.py` writes every part, and `geometry/dimensions_mm.json` lists every
size. The case interior is 440 x 460 x 210 mm, with:

| part | size | in the solve |
|---|---|---|
| PSU shroud | closed box over the whole floor, 100 mm tall | a solid |
| motherboard | ATX, 305 x 244 mm, on 6 mm standoffs | a solid |
| RAM | four DIMMs, 133 mm, as one block | a solid |
| graphics card | 300 mm long, 140 mm tall, 55 mm thick (2.75 slots), fans facing down | a black box, below |
| CPU cooler | tower: 120 mm fan in front of a 52 mm fin stack, 165 mm tall | a black box, below |
| case fans | 3 x 120 mm front, 1 x 120 mm rear, 2 x 140 mm top | fixed flows |
| filter mesh | the whole front and top panels, behind and around the fans | open, with a loss |
| slot covers | perforated, below the card at the rear, no filter | open, with a loss |

Every part is a box at the level of detail electronics-cooling CFD uses: the air sees a
part's outside, not its capacitors or fins.

## The model, and why it is this one

**The card and the cooler are black boxes.** The pressures this argument is about are a
few pascals; a card or cooler fan works against 20-40 Pa. So each moves about the same air
in any layout, and what the layout changes is *which* air reaches it. The card draws
0.040 m3/s through its three fan openings and returns it through the open edges of its fin
stack (both long sides, the front end and a flow-through window on top), 300 W warmer:
6.23 K above the flow-weighted mean of what went in. The cooler does the same with
0.020 m3/s through its fan face to the back of its fin stack, 150 W.

**Case fans are fixed flows,** for the same reason: 0.0165 m3/s per 120 mm fan and
0.021 m3/s per 140 mm fan, about 70% of typical free-air ratings, for filters and the case.
Intake fans bring in air at the room's 22 C.

**The leaks are a result, not a setting.** Filter mesh (with any fan position not in use)
and slot covers are open to a room at 0 Pa gauge and 22 C, with a quadratic loss,
p = K/2 Un|Un|: K = 3 for filter mesh, K = 6 for the slot covers. Air may cross any of
them either way. Whatever the fans do not balance goes through them.

**Air:** `pimpleFoam`, incompressible, rho 1.196 kg/m3, nu 1.52e-5 m2/s, cp 1007 J/(kg K);
temperature a passive scalar (laminar Pr 0.71, turbulent 0.85) advanced every step.
k-omega SST-SAS, because plain SST holds free jets unnaturally steady. Second-order
backward in time, bounded convection, adaptive time step with a local Courant number up to
10 (the mean was 0.42-0.63). Walls and parts are no-slip and adiabatic.

**No buoyancy, checked.** Temperature does not feed back on the flow. On the card-middle
section, over 6-8 s, the Richardson number g beta dT L / U^2 is 0.07-0.11 for the whole case
(L 0.36 m, the largest rise 17-19 K, section rms speed 1.5-1.7 m/s) and 0.05-0.07 in the hot
pool above the card (mean rise 15-17 K over about 0.2 m, rms speed 1.3-1.45 m/s). Buoyancy
alone would move that pool at about 0.33 m/s; the fans move it at four times that.

**Mesh:** snappyHexMesh, 8 mm background, 4 mm near the parts, the openings and the card,
382,688 cells. `checkMesh` reports "Mesh OK" (non-orthogonality up to 39.9 degrees, skewness
up to 2.90). The stricter `-allGeometry -allTopology` flags 74 concave faces, 4,461
low-determinant cells and 2,176 concave cells, typical of snappyHexMesh's cut cells. A clean
copy rebuilt the same 382,688 cells.

**Start and length:** still air at 22 C, everything switched on at t = 0. The case's air
turns over in 0.50-0.59 s; the run is 8 s, 14-16 turnovers, fixed before solving. Two
planes are written every 0.02 s: vertical through the card's middle, parallel to the glass
(z = 0.082 m), and horizontal between the shroud and the card (y = 0.145 m).

## Results

Means over the settled window, 6-8 s:

| layout | air into the card | air into the CPU cooler | case pressure | entering air through unfiltered slots |
|---|---:|---:|---:|---:|
| positive | 29.9 C (+7.94) | 34.8 C (+12.78) | +0.39 Pa | 6.1% |
| negative | 29.6 C (+7.57) | 33.7 C (+11.73) | -1.29 Pa | 8.3% |
| even | 27.4 C (+5.44) | 32.5 C (+10.46) | -0.54 Pa | 6.9% |

The two halves of the window agree within 0.24 C on the card and 0.10 C on the cooler.
"Settled" means statistically steady: SAS keeps the jets moving.

**Positive against negative is a 0.4 C difference at the card,** inside how much the card's
air moves about from moment to moment (one standard deviation 0.30-0.44 C). The sign of the
case pressure barely matters here.

**What matters is how air is delivered to the card.** The exhaust fans in `negative` and
`even` are the same and move the same 58.5 L/s, yet `even` feeds the card air 2.1 C
cooler. In `even` most of it comes in as three fan jets aimed at the card; in `negative`
most seeps in through the filter mesh around one fan.

**Positive pressure does not seal the case.** Air still comes in through the slot covers in
`positive`, 3.3 L/s against 2.8 out, because the pressure inside is not the same
everywhere. Negative raises the unfiltered share of entering air from 6% to 8%.

Vent flows, L/s in / out, 6-8 s (unused fan positions are counted separately in the
histories):

| layout | front mesh | top mesh | slot covers |
|---|---:|---:|---:|
| positive | 1.77 / 12.62 | 0.03 / 8.46 | 3.34 / 2.83 |
| negative | 21.86 / 0.00 | 9.38 / 1.94 | 5.21 / 2.28 |
| even | 8.09 / 3.41 | 5.76 / 3.49 | 4.67 / 2.61 |

With the unused fan positions included, the air through the openings matches each
layout's fan imbalance exactly: 33, -42 and -9 L/s.

## What the clip shows, and what it does not

**It shows** the vertical section through the middle of the card, through the glass, front
on the left, temperature on one scale from 22 to 42 C, for `positive` and `negative`, from
switch-on, at 2.5x slow motion. The card, the cooler and the fans are drawn over the holes
they leave in the section, at the solver's sizes, with detail the solver never had: fins,
heat pipes, fan frames and blades. The motherboard and RAM are behind the section, so the
field never shows them; they are drawn as dashed outlines. The number on the card and on the
cooler is the temperature of the air going into each, as the solve computed it, averaged
over the last 0.5 s of flow and updated four times a second. The card's and cooler's fins
take the colour of that temperature. The moving dashes follow the section's in-plane
velocity, at a tenth of the air's speed so they do not strobe.

**It does not show** the third layout, the flow across the section, or anything inside the
card or cooler.

## Limits, which are the part worth reading

- **Black boxes.** No resolved fans, fins or heat sinks; fan flows are fixed, not read off
  fan curves, and leave the fan face uniform, without swirl. A layout that starved a fan of
  air would not show it here.
- **Air temperatures, not part temperatures.** No conduction in the parts, no radiation, no
  junction temperatures. The numbers are the air each part breathes.
- **One PC.** One case, one card, one cooler, one set of fan flows and vent losses. The
  K values are prescribed, not calibrated; the leak flows, and the dust share with them,
  depend on them most.
- **Dust is an airflow proxy.** The unfiltered share of entering air is not particle
  capture or deposition.
- **No leaks other than the openings listed.** Real cases leak at panel seams and cable
  cut-outs.
- **One mesh, one model, one time step.** No mesh, time-step or turbulence-model study, and
  a local Courant number up to 10 rules out fine-scale turbulence claims.
- **Eight seconds of flow,** two of them averaged.

## A viewer's layout: bottom intakes and the cooler turned round

A viewer asked, under the published clip: "Make one w 2 bottom intake, 1 intake next to the
processor, CPU tower cooler facing front, and two in top, behind cpu tower is intake, one
closer to front blowing out. No front cooler." This layout is that build, in this PC:

| the comment | here |
|---|---|
| "2 bottom intake" | two 120 mm fans blowing up through the top of the PSU shroud (100 mm up), centred 75 and 205 mm from the front, leaving the shroud's rear 175 mm for a power supply. They take in room air at 22 C, as through a filtered floor; the shroud's inside is not modelled. |
| "1 intake next to the processor" | the rear 120 mm fan, as an intake. It is the fan next to the CPU in an ATX case, 375 mm up, with the socket 330 mm up. |
| "CPU tower cooler facing front" | the cooler turned round to blow toward the front (below). |
| "two in top, behind cpu tower is intake, one closer to front blowing out" | the two 140 mm top fans: the rear one (centre 360 mm from the front, above the turned cooler's fan) in, the front one (220 mm) out. |
| "No front cooler" | no front fans. The three front mounts stay filter mesh, open to the room with the same loss as the rest of the front panel. |

"Next to the processor" could also mean a fan in the glass side panel. The rear fan is the
reading the rest of the comment supports, so it is the one used. The fan flows are the
other layouts': 33 L/s from the bottom, 16.5 from the rear and 21 from the top in, 21 out.
That leaves 49.5 L/s to leave through the openings, against 33 in `positive`.

**The cooler, turned.** In the other layouts the cooler's 120 mm fan is on the front face of
its fin stack and blows toward the rear. Turned, the fin stack stays where it was (52 mm
deep, centred on the socket) and the fan moves to its rear face, so the cooler draws air
in 369 mm from the front, facing the rear fan, and returns it out of the stack's front face
292 mm from the front, toward the front. It is the same black box, with the same 0.020 m3/s and 150 W.
The RAM stays where it was. `scripts/build_geometry.py --viewer` makes the changed parts
(the cooler, its two faces and the two bottom fan faces), into `geometry/viewer/`; every
other part is the shared `geometry/`.

**Its own mesh.** A turned cooler is a different solid, so this layout cannot run on the
mesh of the other three. `./Allmesh viewer` builds `mesh/viewer/` the same way, with the
same settings: 382,688 cells, the same count as the shared mesh, and `checkMesh` reports
"Mesh OK". The other three layouts' geometry, mesh and cases are unchanged, so `positive`
and `viewer` compare two meshes built alike, not one.

**Result.** Solved on 8 ranks in 1,775 s of wall clock, 8 s from still air. Means over
6-8 s, in `results/summary.csv` with the others:

| layout | air into the card | air into the CPU cooler | case pressure | entering air through unfiltered slots |
|---|---:|---:|---:|---:|
| positive | 29.9 C (+7.94) | 34.8 C (+12.78) | +0.39 Pa | 6.1% |
| viewer | 26.3 C (+4.29) | 22.3 C (+0.33) | +0.63 Pa | 3.9% |

The two halves of the window agree within 0.09 K on the card and 0.06 K on the cooler, and
both intakes level off by about 2 s.

**Both parts get cooler air.** The card's is 3.7 K cooler than in `positive`: the bottom
fans blow room air up under its front half, where its fans draw. The cooler's is almost room
air: turned round, its fan faces the rear and the rear top intakes, where in `positive` it
breathed the card's exhaust.

**The front panel becomes the way out.** With no front fans and more air pushed in than
pulled out, the front filter mesh lets out 30.3 L/s and the three empty front mounts about
17 more, about 47 L/s in all. Vent flows, L/s in / out, 6-8 s:

| layout | front mesh | top mesh | slot covers |
|---|---:|---:|---:|
| positive | 1.77 / 12.62 | 0.03 / 8.46 | 3.34 / 2.83 |
| viewer | 0.46 / 30.26 | 1.69 / 5.24 | 2.94 / 2.08 |

Some air still comes in through every opening, as in `positive`: the card's fans pull hard
near the slot covers.

**What it cannot say,** on top of everything in the limits above:

- **Fans are fixed flows.** This layout pushes more air into the case than `positive`, and a
  real fan blowing in against that pressure, or a bottom fan behind the shroud's floor and
  filter, would move somewhat less air than its fixed flow here. The cooler's inlet sits
  right in the rear and top intake jets, so its near-room air is the optimistic end.
- **Air into the parts, not part temperatures.** The 0.33 K is the air the cooler breathes,
  not a CPU temperature; the 4.29 K is the card's air, not its core.
- **One reading of one comment.** A side-panel fan, a different bottom-fan position or a
  shroud with a real power supply in it are different builds.

## A second viewer's layout: two in, two out

Another viewer wrote, under the published clip: "With four fans, I imagine it would be best
to have two at the front-bottom for intake, and two for exhaust, split between one at the
rear and another at the top, positioned towards the back." Every fan in it is one of this
PC's positions, so this layout is `positive` with a different set of fans switched on:

| the comment | here |
|---|---|
| "two at the front-bottom for intake" | the lower two of the three front 120 mm fans, as intakes: `front_low` (centre 160 mm above the floor, just above the PSU shroud) and `front_mid` (280 mm). The top front mount, `front_high` (400 mm), is not used. |
| "one at the rear" | the rear 120 mm fan (centre 375 mm up), as an exhaust, as in every layout here. |
| "another at the top, positioned towards the back" | the rear 140 mm top fan, `top_rear` (centre 360 mm from the front, over the cooler), as an exhaust. The front top mount, `top_front` (220 mm), is not used. |

The unused mounts are filter mesh open to the room with its loss, as in the other layouts.
The fan flows are the others': 33 L/s in, 16.5 + 21 = 37.5 L/s out, so 4.5 L/s has to come
in through the openings, a nearly balanced, slightly negative layout against `positive`'s
33 L/s pushed out. The cooler is as in `positive`, on the front face of its fin stack and
blowing toward the rear.

**The shared mesh.** No part moves and no fan position is added, so this layout runs on the
mesh of `positive`, `negative` and `even` (`checkMesh`: the same 382,688 cells, 1,178,265
faces and 412,994 points), and `positive` and `twoInTwoOut` compare on one mesh. The only
changes are the layout in `config/model.json` and its name in `Allrun`.

**Result.** Solved on 8 ranks in 2,710 s of wall clock, 8 s from still air. Means over
6-8 s, in `results/summary.csv` with the others:

| layout | air into the card | air into the CPU cooler | case pressure |
|---|---:|---:|---:|
| positive | 29.9 C (+7.94) | 34.8 C (+12.78) | +0.39 Pa |
| twoInTwoOut | 27.5 C (+5.47) | 32.6 C (+10.61) | -0.32 Pa |

The two halves of the window agree within 0.01 K on the card and 0.11 K on the cooler, and
the card's and the cooler's intakes level off by about 1.5-2 s in both layouts.

**Both parts get somewhat cooler air:** 2.5 K at the card and 2.2 K at the cooler, with one
intake fewer than `positive`. That is close to `even` (+5.44 and +10.46), which has the same
rear and rear top exhausts and the front top one as well: 0.03 K apart at the card, inside
the card's moment-to-moment spread (one standard deviation 0.16-0.19 K), and 0.15 K at the
cooler, about one standard deviation (0.11-0.12 K). This model does not tell the two apart.

**No opening carries much either way.** The openings take in 13.9 L/s and let out 11.2, and
the two unused mounts let in 1.74 L/s net, which with the fans' 4.5 L/s shortfall balances.
`positive` lets 21 L/s out through the front and top mesh alone. Vent flows, L/s in / out,
6-8 s:

| layout | front mesh | top mesh | slot covers |
|---|---:|---:|---:|
| positive | 1.77 / 12.62 | 0.03 / 8.46 | 3.34 / 2.83 |
| twoInTwoOut | 4.79 / 5.95 | 4.55 / 2.86 | 4.58 / 2.35 |

**Why the gain is smaller than `viewer`'s** (3.7 K at the card, 12.4 K at the cooler):

- **The cooler is not turned.** In `viewer` the cooler faced the rear and the rear top
  intake and breathed almost room air. Here it faces the front, as in `positive`, and draws
  from the upper front of the case: on the card-middle section the card's exhaust still
  reaches the cooler's intake, as it does in `positive`. The top exhaust sits over the cooler's
  outlet, downstream of it, so it can carry the cooler's warm air out but cannot change what
  the cooler draws in.
- **The card's air comes in from the front wall.** In `viewer` two bottom fans blew room air
  straight up under the card's front half, where its fans draw. Here both intakes blow
  horizontally through the front panel toward the rear, not up into the card's fans, which
  face down.

**What it cannot say,** on top of everything in the limits above:

- **No buoyancy.** In a real case warm air rising toward the top fan would help a top
  exhaust slightly; this model leaves that out, as for every layout here.
- **Small differences are not rankings.** The 2.5 and 2.2 K against `positive` are larger
  than the spread; the gap to `even` is not, and nothing here says which of the two is
  better.
- **Air into the parts, not part temperatures.** The 5.47 K is the card's air, not its core;
  the 10.61 K is the air the cooler breathes, not a CPU temperature.
- **One reading of one comment.** "Front-bottom" is read as the lower two of this case's
  three front mounts, and the unused mounts are open filter mesh. A case with lower front
  mounts, bottom fans or blanked-off unused mounts is a different build.

## Dust: where the room's dust goes

Most comments under the published clip said the choice is about dust, not temperature.
`./Allrun positive dust` and `./Allrun negative dust` solve those two layouts again from
switch-on, as they are, with the dust in the air carried on the flow as a passive scalar:
an advection-diffusion equation with no source, advanced every time step beside the
temperature. They write `runs/positive_dust` and `runs/negative_dust`. Nothing that sets the
flow changes, and without `dust` every layout's case is generated exactly as before.

**The room and the openings.** The room's air carries a uniform, fixed dust concentration,
called 100%, and the case starts clean at switch-on. Air coming in through an unfiltered
opening carries the room's 100%; through a filter, what the filter lets past:

| opening | filtered |
|---|---|
| front panel, filter mesh, with the three front fan positions behind it | yes |
| top panel, filter mesh, with the two top fan positions | yes |
| expansion-slot covers, perforated, below the card at the rear | no |
| rear fan position | no, but it exhausts in both layouts, so nothing comes in there |

The PSU is inside the closed shroud and draws no case air, and the case has no seams or
cut-outs that leak, so the slot covers are the only unfiltered way in, in either layout.
That is how a current airflow case is filtered: Corsair's 4000D Airflow ships magnetic dust
filters for the front, the top and the PSU intake and sells them as spares, with none for
the rear fan or the slot covers
([spare parts](https://help.corsair.com/hc/en-us/articles/4423638037773-4000-Series-Cases-Spare-Parts),
[top filter](https://www.corsair.com/us/en/p/pc-components-accessories/cc-8900447/icue-4000x-4000d-4000d-airflow-top-magnetic-dust-filter-gray-cc-8900447)).

**The filter catches 50%.** A stock case filter is one layer of woven nylon or polyester
mesh. DustEND, which makes PC case filter material, gives a capture for each grade
([dustend.com](https://www.dustend.com/)): 50% for its woven polyester G1, 80% for its
non-woven G2, 90% for its 60 ppi foam G3. The grade names are EN 779's coarse classes, whose
average arrestance of the standard synthetic test dust is 50-65% for G1, 65-80% for G2 and
80-90% for G3 (EN 779:2012, since replaced by ISO 16890). DEMCiflex
([why DEMCiflex](https://www.demcifilter.com/why-demciflex)) and Silverstone describe their
mesh but give no fraction. So 50% is the maker's own figure for the kind of filter a case
ships with, a test-dust average over a mix of particle sizes.

**Two fields, so the 50% is not built in.** The dust is passive, so its concentration is
linear in what comes in. The solve carries two fields: `dustF`, the dust that came in
through filter mesh or a filtered fan position, counted at the room's full concentration,
and `dustU`, the dust that came in through an unfiltered opening. A filter catching a
fraction eta gives (1 - eta) dustF + dustU, so one solve answers for any filter, and 0.8 and
0.9 are given below to show what a better filter changes. The card and the CPU cooler return
the flow-weighted mean of what they draw in and catch nothing. The dust is carried with
bounded first-order upwind, so both fields stay between 0 and 1 without clipping, and a
diffusivity of 1e-6 nu (Brownian diffusion, negligible) plus nu_t/0.85 (a turbulent Schmidt
number of 0.85). Its linear solves converge to an absolute 1e-8, so the budget closes.
`scripts/make_case.py --dust` writes it; `scripts/summarize_dust.py` reads the runs.

**Result.** Solved on 8 ranks each, the two at the same time, in 4,431 s (`positive`) and
4,132 s (`negative`) of wall clock, 8 s from still air. The dust in the air the card breathes, flow-weighted over its fan
openings, as a share of the room's, means over 6-8 s (`results/dust_summary.csv`):

| filter capture | positive | negative |
|---|---:|---:|
| 0.5, woven mesh, the clip's | 59.0% | 65.0% |
| 0.8 | 34.4% | 44.0% |
| 0.9 | 26.2% | 37.0% |

The two halves of the window agree within 0.2 points, and the every-step record agrees with
the 0.02 s one within 0.01. The card's dust reaches half its settled value by 0.4 s and
levels off by about 2 s (`results/dust_card.png`). Over the whole case, the mean at 8 s is
53.5% (`positive`) and 56.4% (`negative`) of the room's dust at a capture of 0.5.

**The slot leak is the difference.** The slot covers take in 3.5 L/s of room air in
`positive` and 5.8 L/s in `negative`, 6.4% and 9.3% of all the air coming in. Positive
pressure does not stop it: 3.5 L/s comes in through the covers while 2.9 L/s goes out through
other parts of them, because the card's fans face down just above them and pull hard there.
The card breathes dustier air than the case's mean in both layouts. `negative` brings it more
dust at every capture, and the gap widens as the filter gets better (6.0, 9.6 and 10.8
points), because the slot leak is then a larger part of what the card breathes. One-way
flows, L/s in / out, 6-8 s:

| layout | front mesh | top mesh | slot covers (unfiltered) |
|---|---:|---:|---:|
| positive | 1.9 / 12.7 | 0.0 / 8.5 | 3.5 / 2.9 |
| negative | 21.4 / 0.0 | 9.2 / 2.0 | 5.8 / 1.9 |

**The flow is the one above.** The dust does not act on the flow. The card's intake rise is
7.85 K (`positive`) and 7.37 K (`negative`), against 7.94 and 7.57 K in the runs above, and
the vent flows of `positive` are within 0.2 L/s of the table in the results. In `negative`
the front takes in 0.5 L/s less and the slot covers 0.6 L/s more (5.8 against 5.2): with
nothing that sets the flow changed, that is the scatter of a 2 s mean of this unsteady flow
from one solve to the next.

**The budget closes.** Over 0-8 s, the dust each field holds at 8 s equals what came in less
what left, through every boundary by advection and diffusion, to within 0.007% of what came
in, for both fields in both layouts (`results/dust_budget.csv`). The numerics neither lose
nor make dust.

**The dust's numerics against the temperature's.** Upwind and the nu_t/0.85 diffusivity
both smear the dust more than the temperature in the same runs, which is carried with
`limitedLinear 1` and, through the `nut nut` entry of its function object, a diffusivity of
nu_t exactly. `scripts/dust_scheme_check.sh <layout>` tests that directly: it restarts the
layout's dust run from its 8 s flow with the dust set to zero and carries it to 9.5 s twice,
as solved ("upwind") and with the temperature's scheme and diffusivity ("as T"). The flow
equations are the same in both, so they differ only in the dust's numerics. Filling a clean
case on a developed flow gives the steepest fronts the dust ever has, a harder test than the
start from still air. At a capture of 0.5 (`results/dust_scheme_check.csv`):

| | card's dust, 8.5-9.0 s | card's dust, 9.0-9.5 s | section, mean / 95th percentile difference, 8.5 s | the same at 9.5 s |
|---|---:|---:|---:|---:|
| positive, upwind / as T | 46.6 / 46.6% | 54.1 / 54.2% | 1.3 / 4.5 points | 0.3 / 1.0 points |
| negative, upwind / as T | 52.2 / 52.1% | 60.7 / 60.4% | 1.5 / 5.6 points | 0.6 / 2.1 points |

The card's number moves by 0.3 points at most, and the gap between the layouts stays at
6 points either way. On the card-middle section the upwind dust is softer, as expected: its
mean gradient is 16-31% lower than with the temperature's scheme. The structures are the
same, in the same places, so the runs stand as solved.

**What the clip shows.** The card-middle section of `positive` and `negative` from
switch-on, with the case's front on the right, as a standard ATX build looks through its
left-side glass (the first clip drew it the other way round). Dust is grey, lighter is
cleaner, on 40-80% of the room's: on 0-100% the filled case sits at 50-65% and both halves
come out the same grey. Air above 80%, the core of the slot-leak plume at the rear, is drawn
black, about 1% of the section and 4.1% in the worst frame. Air below 40% is drawn white, and
only in the first 1.3 s, while the fans replace the clean air the case starts with. The
number on the card is the dust it breathes at a capture of 0.5, averaged over the last 0.5 s
of flow: 59% and 66% at the end, against 59.0 and 65.0% over 6-8 s.

**What it cannot say,** on top of everything in the limits above:

- **Dusty air, not dust.** The dust has no weight and no inertia, and it does not settle,
  stick, bounce or come loose again; the filter does not load or clog, and the flow does not
  feel it. So this is where dusty air goes, not where dust ends up: the air carries dust into
  the card's and the cooler's fins, but how much stays there is not modelled.
- **One filter figure.** 50% is a maker's test-dust average for woven mesh, not an
  efficiency by particle size; a filter that catches more changes the numbers, which is why
  0.8 and 0.9 are given.
- **One leak.** The slot covers are the only unfiltered opening, and how much comes in
  through them rests on their prescribed loss (K = 6). Real cases also leak at panel seams
  and cable cut-outs.
- **The room's dust is fixed and uniform,** and the case starts clean. Nothing here says how
  fast a real case gets dusty over weeks.

## A third viewer's layouts: a liquid-cooled CPU, with and without bottom intakes

A viewer asked, under the `viewer` layout's clip: "Can you do three top fans as exhaust, one
back fan as exhaust and three front/lateral fans as intake? And comoare it to the same setup
but with two bottom intakes below the GPU. In this case the CPU is being cooled via liquid
cooling so there's no heatsink producing air in the middle". These two layouts are that
build, in this PC:

| the comment | here |
|---|---|
| "three front/lateral fans as intake" | the three front 120 mm fans, as in `positive`. |
| "three top fans as exhaust" | three 120 mm top fans (below). |
| "one back fan as exhaust" | the rear 120 mm fan, as in every layout here. |
| "two bottom intakes below the GPU" | `viewer`'s two 120 mm bottom fans, in the top of the PSU shroud, centred 75 and 205 mm from the front, under the card's front half. Only `aioFrontBottomIn` has them; in `aioFrontIn` they are closed shroud. |
| "the CPU is being cooled via liquid cooling" | the tower cooler is gone; an all-in-one cooler's pump block sits on the socket and its radiator on the top fans (below). |

**The PC, changed.** `scripts/build_geometry.py --aio` writes the parts that differ into
`geometry/aio/`; every other part is the shared `geometry/`.

- **The top holds three fans.** This PC's top has two 140 mm positions. A 360 mm radiator
  takes three 120 mm fans, so the top becomes a 360 mm mount: three 120 mm fans at 120 mm
  pitch, centred 100, 220 and 340 mm from the front, the middle one where the front top fan
  was. The top filter mesh is widened to cover the new mount (40-400 mm from the front, the
  span of the three fan frames), as it covered the two 140 mm frames.
- **The pump block.** In place of the tower cooler, a closed 70 x 70 mm box on the socket,
  standing 42.4 mm off the board, with no flow and no heat of its own (the pump's few watts
  are left out). The cooler's black box, with its 20 L/s and 150 W, is gone. The RAM stays
  where it was.
- **The radiator is not in the air volume.** Where the radiator goes is not in the comment.
  It is put on the three top exhaust fans, which is our reading. It is not meshed: the air
  leaving through the top fans is the air reaching the radiator, and the CPU's 150 W goes
  into that air after it has left. So the case air carries only the card's 300 W, and "the
  air entering the radiator" is the flow-weighted temperature over the three top fans' faces.
- **Every fan is 120 mm,** at the same 16.5 L/s. `aioFrontIn` takes in 49.5 L/s and blows out
  66, so 16.5 L/s has to come in through the openings; `aioFrontBottomIn` takes in 82.5, so
  16.5 L/s has to leave through them. The bottom fans bring in room air at 22 C, as through
  a filtered floor; the shroud's inside is not modelled.

**Its own mesh.** `./Allmesh aio` builds `mesh/aio/` the same way as the others, with the same
settings and the top fans' rings cut to 120 mm: 400,745 cells, and `checkMesh` reports
"Mesh OK" (non-orthogonality up to 41.2 degrees, skewness up to 2.90). The stricter
`-allGeometry -allTopology` flags 101 concave faces, 4,461 low-determinant cells and 2,337
concave cells, snappyHexMesh's cut cells as in the shared mesh. Both layouts run on this one mesh; in `aioFrontIn` the
run's `createPatch` merges the two bottom fan positions into the walls. A clean copy rebuilt
the solved mesh exactly, and `scripts/make_case.py` writes the solved runs' dictionaries and
initial fields, apart from the order in which the radiator monitor lists its three fans.
The other layouts' geometry, meshes and generated cases are unchanged.

**Result.** Both solved together on 8 ranks each, in 4,359 s (`aioFrontIn`) and 3,599 s
(`aioFrontBottomIn`) of wall clock, 8 s from still air. Means over 6-8 s, in
`results/aio_summary.csv` (`scripts/summarize_aio.py`):

| layout | air into the card | air into the radiator | case pressure |
|---|---:|---:|---:|
| aioFrontIn, 3 in / 4 out | 27.3 C (+5.26) | 23.9 C (+1.91) | -0.67 Pa |
| aioFrontBottomIn, 5 in / 4 out | 24.2 C (+2.15) | 24.2 C (+2.23) | +0.05 Pa |

Each half of the window agrees with the whole within 0.05 K. The card's air moves about from
moment to moment by one standard deviation of 0.17 and 0.10 K, the radiator's by 0.12 and
0.10 K.

**The bottom intakes cool the card's air by 3.1 K,** about thirty times either run's standard
deviation. **The radiator's air barely moves:** it is 0.3 K warmer with them, both within
about 2 K of the room.

**The heat budget closes.** The heat carried out through every fan and opening,
rho cp sum(phi (T - T_room)) over 6-8 s, comes to 300.04 W in `aioFrontIn` and 300.22 W in
`aioFrontBottomIn`, against the card's 300 W.

**The front panel turns from a way in to the way out.** Vent flows, L/s in / out, 6-8 s:

| layout | front mesh | top mesh | slot covers |
|---|---:|---:|---:|
| aioFrontIn | 10.55 / 2.87 | 9.97 / 3.78 | 5.07 / 2.44 |
| aioFrontBottomIn | 3.02 / 14.21 | 4.94 / 8.61 | 1.92 / 3.57 |

Without the bottom intakes the four exhausts draw room air in through the front mesh, about
10.6 L/s. With them the front mesh lets out about 14.2 L/s, which is where most of the extra
air leaves.

**Most of that air leaves beside the fans, off the clip's section.** At the 8 s write
(`results/aio_vent_depth.csv`), the front mesh of `aioFrontBottomIn` lets out 15.3 L/s, and
12.3 L/s of it leaves through the two strips of mesh either side of the fan column: 6.35 L/s
within 30 mm of the motherboard tray and 5.99 L/s within 30 mm of the glass (the fans span
45-165 mm across the width). In the 30 mm band that holds the card-middle section
(z = 0.082 m), 0.31 L/s goes out and 0.28 L/s comes in. On that section the front wall is
almost all fan.

**What the clip shows, and what it does not.** It shows the card-middle section of both
layouts from switch-on, `aioFrontIn` above `aioFrontBottomIn`, front on the right, on one
temperature scale from 22 to 36 C, at 2.5x slow motion, with the air entering the card and
the radiator as the solve computed them. On the section the air is seen leaving only through
the rear and top fans, in both. It does not show the front mesh letting air out in
`aioFrontBottomIn`, because that happens beside the fans, off the section; the numbers above
are where that is.

**What it cannot say,** on top of everything in the limits above:

- **The radiator is a reading, not the comment's,** and it is not modelled: no radiator
  pressure loss, so the top fans move their full 16.5 L/s; no coolant, fins or pump heat. The
  radiator's number is the air reaching it, not a coolant or CPU temperature, and a radiator
  in the front, as an intake, would change the card's air and is not run here.
- **Fans are fixed flows.** `aioFrontBottomIn` pushes more air in than it pulls out, and a
  real fan blowing against that, or a bottom fan behind a shroud floor and filter, would move
  somewhat less than its fixed flow here.
- **Air into the parts, not part temperatures.** The 2.15 and 5.26 K are the card's air, not
  its core.
- **One reading of one comment.** "Front/lateral" is read as the three front positions, and
  the third top fan as a 360 mm mount on this PC's top. A side-panel intake, bottom fans
  elsewhere, or a case with a real 360 mm top mount are different builds.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3
with NumPy, pandas and PyVista.

    cd cases/pcCaseAirflow
    ./Allmesh                  # about 1-6 minutes
    ./Allrun positive          # negative, even, twoInTwoOut
    ./Allrun viewer            # builds mesh/viewer/ first if it is not there
    ./Allrun aioFrontIn        # and aioFrontBottomIn; builds mesh/aio/ first
    python3 scripts/summarize.py
    python3 scripts/plot_results.py
    ./Allrun positive dust     # and negative: runs/<layout>_dust
    scripts/dust_scheme_check.sh positive    # optional, after the dust run
    python3 scripts/summarize_dust.py
    python3 scripts/summarize_aio.py          # after the aio runs

`Allmesh` builds the shared mesh from `geometry/` (`mesh/rebuild_mesh.py`) and checks it.
`Allrun` writes the layout's case into `runs/<layout>/` from `config/model.json`
(`scripts/make_case.py`), which holds every number above, and solves to 8 s on 8 MPI ranks:
36-44 minutes each here. `summarize.py` writes the statistics to `results/summary.csv`, where
the published ones already are, with `comparison.png` and `histories.png`. `./Allclean`
removes the runs and the mesh. The two dust runs took 69-74 minutes here, run at the same time; `summarize_dust.py`
writes `results/dust_summary.csv`, `dust_budget.csv`, `dust_card.png` and, with the check's
runs, `dust_scheme_check.csv`, and needs NumPy 2 and matplotlib. The two aio runs took 60-73
minutes here, run at the same time; `summarize_aio.py` writes `results/aio_summary.csv` and
`aio_vent_depth.csv`.

The case was set up by an agent and checked by us, in one build, from geometry we built and
reviewed first.
