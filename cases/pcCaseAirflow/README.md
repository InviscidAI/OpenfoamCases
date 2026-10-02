# PC case fans: more in, or more out

PC builders argue over whether a case's fans should push more air in than they pull out
("positive pressure") or the other way round ("negative"). Positive is said to keep dust
out, because every gap blows outward, and to cool worse; negative is said to cool better
and to pull dust in through every unfiltered gap. This case puts the same PC through three
fan layouts and measures the air each part breathes:

    ./Allrun positive    # 3 front fans in, rear fan out
    ./Allrun negative    # 1 front fan in, rear and 2 top fans out
    ./Allrun even        # 3 in, 3 out

The published clip shows `positive` against `negative`. `even` is here because equal fan
counts are not equal flows: two 140 mm top fans and a 120 mm rear fan move more air than
three 120 mm front fans, so "3 in, 3 out" is slightly negative.

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

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3
with NumPy, pandas and PyVista.

    cd cases/pcCaseAirflow
    ./Allmesh                  # about 1-6 minutes
    ./Allrun positive          # negative, even
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
