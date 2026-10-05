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

The published clip shows `positive` against `negative`. `even` is here because equal fan
counts are not equal flows: two 140 mm top fans and a 120 mm rear fan move more air than
three 120 mm front fans, so "3 in, 3 out" is slightly negative. `viewer` is a layout asked
for in the clip's comments, on the same PC with its cooler turned round and two bottom fans
added; it has [its own section](#a-viewers-layout-bottom-intakes-and-the-cooler-turned-round).

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

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3
with NumPy, pandas and PyVista.

    cd cases/pcCaseAirflow
    ./Allmesh                  # about 1-6 minutes
    ./Allrun positive          # negative, even
    ./Allrun viewer            # builds mesh/viewer/ first if it is not there
    python3 scripts/summarize.py
    python3 scripts/plot_results.py

`Allmesh` builds the shared mesh from `geometry/` (`mesh/rebuild_mesh.py`) and checks it.
`Allrun` writes the layout's case into `runs/<layout>/` from `config/model.json`
(`scripts/make_case.py`), which holds every number above, and solves to 8 s on 8 MPI ranks:
36-44 minutes each here. `summarize.py` writes the statistics to `results/summary.csv`, where
the published ones already are, with `comparison.png` and `histories.png`. `./Allclean`
removes the runs and the mesh.

The case was set up by an agent and checked by us, in one build, from geometry we built and
reviewed first.
