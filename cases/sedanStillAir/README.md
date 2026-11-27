# A hot sedan aired out in still air: all four windows down, against one window and fanning the door

A mid-size sedan has stood an hour in a sunny parking lot on a 100 °F afternoon with no wind at all, and before
getting in the owner wants the hot air out. [`suvAiring`](../suvAiring) put the same two camps side by side in a
light crosswind, and four windows won from 1.2 s on; the question it left open is the one the trick's defenders
raise, that the trick is for still air. One camp opens a rear window and then, on the opposite side, "rapidly open
and close the front door" (Motor1); Thrillist found fanning the door "about a half dozen times" the fastest of the
four ways it tried (as reported by KDWB). The other says "you can simply open all your windows" (SlashGear). Without
wind, four windows exchange air only by buoyancy, cool air in low and hot air out high; the door pumps air as long
as it is swung. This case airs the same two-row cabin twice in dead-still air, once with all four door windows down
and once with the rear window behind the driver down and the front passenger door swung open and shut **for the
whole minute**, and asks how hot the air is where five seated heads will be, second by second for 60 s. It is about
airing only, not the A/C, driving off, or children or pets left in a car.

    ./Allrun fourWindows    # all four door windows down, 0-60 s
    ./Allrun doorFan        # the rear-left window down, the front passenger door swung every 1.2 s, 0-60 s

**The result.** **Fanning the door keeps the heads cooler than four open windows at every monitored time, by about
10 °F from 3 to 10 s and 3.8 °F at 60 s; the two never cross.** Both cabins start at 119.7 °F (321.85 K) with the
air outside at 100 °F (310.93 K) and still. Through four windows the outside air comes in low over the sills and
sinks, about 60 L/s in all, 1.3 cabin volumes a minute, falling to 52 L/s over the last 30 s as the cabin cools, and
the heads stay at 119-120 °F until about 7 s, then fall to **110.9 °F at 60 s**. The swung door moves about 600 L/s
in and out, 13 cabin volumes a minute, in at the window and out at the door on balance; its heads are at 109.6 °F by
3 s and level off near 107 °F from about 30 s: **107.1 °F at 60 s**, though by then 99% of its cabin's air came from
outside. The hot dashboard and seats keep heating that air, so neither cabin gets near the outside's 100 °F in a
minute, and four windows keep closing the gap. Read [What it cannot](#what-it-cannot) before any number here: **the
door is fanned for the whole minute, fifty swings, where the articles describe five or six**, and with six swings the
door lost (below); **the door run's energy budget closes only to 12.6% of the net change in the cabin's heat** (0.9%
of the heat that passed through); **the door is a drag term that conducts heat**; and there is **no mesh or time-step
study**.

The car and the two layouts are this case's. The buoyant model, the fixed hot surfaces, the moving-door drag term
and its K are those of `suvAiring`'s; the schemes and solution settings are
[`weldingFumeExtraction`](../weldingFumeExtraction)'s, and the air and the turbulence model those of an earlier
buoyant case of ours that is not in this repository, with the enthalpy referred to the outside air's 310.93 K.

**An earlier solve** of the same pair, with the door swung six times and left shut from 7.2 s, was reviewed and
replaced by this one; its files are not here. Up to 7.2 s it is the same solve as this case's `doorFan`. Once its
door was shut, one window traded 10-15 L/s, the cabin warmed back, and its heads were at 118.0 °F at 60 s: four
windows were cooler from 26.5 s on, by 7.2 °F at 60 s.

## The car

x runs rearward from the front bumper, y towards the passenger side (the right in a US car, so the driver sits at
-y) and z up from the ground; metres. Every edge lies on the 4 cm grid of the car's mesh. The outside sizes are
rounded from the published ones of a 2025 mid-size sedan; **the windows, the door and the inside are our estimates
from those overall sizes, not measurements**.

| | value | from |
|---|---|---|
| the body | x 0-4.92, y -0.92 to 0.92, z 0.16-1.44 m: the hood at z 0.92 over x 0-1.40, the windscreen raked from (x 1.40, z 0.92) to (x 2.28, z 1.44), the roof at z 1.44 to x 3.56, the rear glass falling to (x 4.28, z 1.00) and the trunk deck at z 1.00 to the tail, the rakes stepped on the grid; no wheels or mirrors | 4.92 m long, 1.84 m wide without mirrors, 1.445 m tall (CarExpert) |
| the cabin | x 1.48-4.12, y -0.72 to 0.72, z 0.24-1.36 m, behind the windscreen's inner face through (1.48, 0.92) and (2.36, 1.44) and in front of the rear glass's through (3.48, 1.44) and (4.20, 1.00); side walls and doors 0.20 m thick; **2.7645 m³ of air** with the seats, the dashboard and the trunk's bulkhead out | ours; the headliner 22 cm above the heads' centres, from the 38.3 in front headroom (Edmunds) |
| the dashboard | x 1.48-1.92, z 0.68-0.92, the cabin's full width; the footwell under it is air | ours |
| the seats | solid boxes: two front buckets (cushions x 2.24-2.72, y ±0.12-0.64, z 0.24-0.48; backs x 2.72-2.88 to z 1.04; headrests x 2.76-2.84, y ±0.28-0.52, to z 1.24) and a three-seat rear bench (cushion x 3.16-3.60, z 0.24-0.48; back x 3.60-3.80 to z 1.00; three headrests x 3.64-3.72 to z 1.16), with the trunk's bulkhead x 3.80-4.12 up to the parcel shelf at z 1.00 behind it | ours |
| the windows that open | the four door windows, lowered fully, z 0.96-1.32: front x 2.16-2.84 (0.2448 m² each), rear x 2.96-3.60 (0.2304 m²), each side. The windscreen, the rear glass and the quarter glass stay shut | ours |
| the front passenger door | x 1.96-2.96 (1.00 m), z 0.24-1.32, the wall's 0.20 m thick, hinged on a vertical axis at its front outer corner (1.96, 0.92) and swinging outwards; its aperture is 1.08 m², 1.072 m² of it open to the cabin past the stepped A-pillar | ours |
| the surfaces | inside, held at their measured temperatures for the whole run: the dashboard at 346.95 K (164.8 °F), the seats at 327.05 K (129.0 °F), everything else inside (headliner, floor, trim, the glass) at the cabin's 321.85 K (119.7 °F). The body's outside and the ground are adiabatic | the means of the mid-size sedan's twelve trials in the sun in Vanos et al. (2018), Table 1: cabin air 48.7 °C, dashboard 73.8 °C, seat 53.9 °C (our arithmetic) |
| outside | 310.93 K (100 °F), dry air at 1e5 Pa at the ground, at rest; the domain x -2.56 to 7.52, y -2.88 to 3.84, z 0-3.52 m (10.08 x 6.72 x 3.52 m), open on every face but the ground | ours; 100 °F for days "in the 100s" in Tempe, Arizona, where the cars were measured |

**fourWindows**: all four door windows open from t = 0; every door shut. **doorFan**: the rear-left window, behind
the driver, open from t = 0, and the front passenger door swung open to 65° and shut again every 1.2 s for the whole
run, θ(t) = (65°/2)(1 - cos(2πt/1.2)) for 0 ≤ t ≤ 60 s, fifty swings, shut at 60 s. 65° is the bottom of a door
check's "soft open" range, 65-72° (US patent 6,105,208), a brisk swing to the door's first full stop; no source gives
the period, and 1.2 s is our estimate of "rapidly", putting the door's edge at up to 2.97 m/s. Fanning it for the
whole minute is our choice for this case: the articles describe "a few" swings to "about a half dozen".

**There are no people.** The heads are five boxes of air, 20 cm along x, 24 cm across and 20 cm high (z 1.04-1.24 m),
150 cells and 0.0096 m³ each, in front of each headrest: the front row at x 2.52-2.72 (head 1 driver, head 2
passenger), the rear row at x 3.40-3.60 (head 3 on the driver's side, 4 in the middle, 5 on the passenger's). "The
heads" is the volume mean of all five.

**At t = 0** (`scripts/prepare.py`) all the air is at rest. The cabin, and the inner half of its side walls' openings
(|y| ≤ 0.82 m), is at 321.85 K with no outside air in it; everything else is at 310.93 K. Each side is hydrostatic,
the two equal in pressure at the windows' mid-height, z = 1.14 m. The face fluxes start at zero.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96, μ 1.82e-5 Pa s, Pr 0.71,
its enthalpy referred to 310.93 K), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `compressible::alphatJayatillekeWallFunction` with Prt 0.85). Euler in time,
adaptive steps at Courant 1 with maxDeltaT 0.02 s, the first step 1e-4 s; fourWindows runs at 0.016-0.025 s (the
step lands on the writes, so it can pass 0.02 s slightly), doorFan at 2.6-8.7 ms while its door swings. limitedLinearV
1 for U and limitedLinear 1 for h, k, ω and the tracer; two outer and two pressure correctors; p_rgh by GAMG to 1e-8
(relTol 0.01) and the final solve to 1e-7 (relTol 0, at most 100 iterations). **No radiation.** The domain's open
faces are `prghPressure` at the outside's hydrostatic p0(z) = 1e5 exp(-9.81 z / (287.1 x 310.93)) with
`pressureInletOutletVelocity`, and T, k, ω and the tracer `inletOutlet`. The outside air is a passive tracer
(`scalarTransport`, `outdoor`, diffusivity 1.408 μ plus the turbulent viscosity), 1 for outside air and 0 for the
cabin's at t = 0.

**The door** (in `constant/fvOptions` as a `vectorCodedSource`, written by `scripts/prepare.py`) is `suvAiring`'s drag
term on the fixed mesh: a slab 1.00 x 0.20 x 1.08 m turned about the hinge by θ(t), its edge spread over one cell by
a mask m = clamp(1/2 - d/h, 0, 1) of the signed distance d to the slab and the cell size h, and a momentum source
-K m ρ (U - U_b) with K = 1e6 s⁻¹ that holds the air in it at the door's velocity U_b = θ'(t) ẑ x (r - r_hinge). It
stops the air, not heat: the masked cells stay gas. Shut, it covers 0.2160 m³, every aperture cell fully; while it
swings the mask holds 0.2151-0.2170 m³. fourWindows has no door term.

**The meshes** (`scripts/build.py`): a background of 0.16 m cubes over the whole domain (blockMesh, 63 x 42 x 22),
refined by snappyHexMesh, castellated only, without snapping or layers: 0.08 m over x -0.56 to 5.52, y -1.64 to 2.60,
z 0-2.24 m, and 0.04 m over the car (x -0.08 to 5.00, y -1.16 to 1.16, z 0.08-1.52 m) and the door's swing (x
1.88-3.04, y 0.92-2.04, z 0.16-1.40 m), two cells between levels, the same in both runs. The car's solid cells (the
body round the cabin, the seats, the dashboard and the bulkhead, less each run's openings) are chosen by cell centre
and cut out with topoSet and subsetMesh, so the solids are stepped on the 4 cm cells. The cut faces are sorted into
`bodyExterior`, `dashboard`, `seats` and `cabinInterior` (every step of both raked glasses that faces cabin air is
`cabinInterior`); the openings are face zones on the side walls' inner planes (y = ±0.72 m), and the heads, the rows
and the cabin cell zones. **320,445 cells (fourWindows) and 321,560 (doorFan)**, 4 cm over the car, 308,722 and
309,837 of them hexahedra and 11,723 the split-face cells at the refinement steps. `checkMesh` OK, non-orthogonality
at most 25.24°, skewness at most 0.33. `checkMesh -allGeometry` fails two of its extra checks: 72 cells with a small
determinant in the shallow wedge of air above the dashboard, and 10,602 concave cells, the split-face cells at the
refinement steps. Both logs are written; `results/mesh_*.json` have the patch, opening and head-box sizes. One mesh
each, no mesh study.

**The monitor** (`scripts/diagnostics.template`, a coded function object run every step, one row every 0.125 s into
`postProcessing/diagnostics89/diagnostics.csv`): the volume, mass, volume- and mass-mean temperature, outside-air mass
and excess enthalpy above 310.93 K of the cabin, of each row and of each head box; the gross flow each way through each
opening, in m³/s and kg/s, with the enthalpy and tracer it carries and its diffusive heat; the heat into the air from
each hot patch; the door's angle, its masked volume, the power it gives the air and how well the masked air follows
it; the hottest and coldest cabin air, the fastest air, and the twelve cells of highest Courant number on each rank;
and, summed every step, the surfaces' heat and the enthalpy advected and diffused through the openings. The planes:
plans at head height (z 1.14 m, interpolated and as cell values), at 0.90 m and at 1.30 m every 0.125 s, three
lengthwise and two cross sections every 0.25 s, three of them again every 7.2 s, and the 316.48 K isosurface every
0.25 s, with T, U, the tracer and the door's drag, from t = 0.

## Results

`results/summary.txt` and `results/<run>/history.csv` (every 0.25 s), from `scripts/extract_results.py`; the tests
before production are `results/tests.json`.

| heads, °F | 0.5 s | 3 s | 7.25 s | 10 s | 30 s | 50 s | 60 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| fourWindows | 119.66 | 119.38 | 119.77 | 118.45 | 113.62 | 110.90 | **110.89** |
| doorFan | 113.27 | 109.56 | 110.83 | 108.66 | 107.37 | 107.19 | **107.08** |
| fourWindows, front/rear row | 119.7/119.7 | 119.5/119.3 | 119.9/119.7 | 119.8/117.6 | 113.6/113.7 | 111.5/110.5 | 111.7/110.4 |
| doorFan, front/rear row | 118.9/109.5 | 115.8/105.4 | 114.9/108.1 | 114.7/104.6 | 110.0/105.6 | 110.3/105.1 | 109.4/105.6 |

| | 3 s | 10 s | 30 s | 60 s |
|---|---:|---:|---:|---:|
| the cabin's mean air, fourWindows, °F | 119.08 | 116.29 | 111.51 | 108.98 |
| the cabin's mean air, doorFan, °F | 114.05 | 110.90 | 108.77 | 108.52 |
| outside air at the heads, fourWindows, % | 1.6 | 7.6 | 44.6 | 75.8 |
| outside air at the heads, doorFan, % | 54.7 | 69.2 | 93.2 | 99.3 |
| the cabin's starting excess heat gone, fourWindows, % | 3.0 | 16.9 | 40.8 | 53.6 |
| the cabin's starting excess heat gone, doorFan, % | 28.1 | 43.9 | 54.6 | 55.9 |

The heads' means do not cross: from the first monitor row after the start, at 0.125 s, to 60 s doorFan is the
cooler at every row, by 0.17 to 11.5 °F. The cabin starts with 32.83 kJ above the outside air in both runs. **Not
every head is cooler with the door**: at 60 s the front driver's box (head 1) is at 112.1 °F against 111.4 °F with
four windows, and at 30 s the two are within 0.5 °F; the other four are 1.4-7.3 °F cooler with the door.

**Where the air goes.** With four windows the cool outside air comes in through the lower part of each window and
the hot air leaves through the upper part, 14-16 L/s each way at each window over the first 30 s and 60.1 L/s in all
over 0-7.25 s, 61.3 L/s over 0-30 s and 51.9 L/s over 30-60 s, about 1.2 cabin volumes a minute. The incoming air
sinks round the seats into the footwells, so the head boxes see it late: their outside air is 1.6% at 3 s and 7.6% at
10 s against 21% of the whole cabin. With the door swinging the rear-left window takes in 363 L/s and lets out 182, and
the door's aperture lets in 235 and out 420, averaged over 0-60 s and the same in each half: 598 L/s in all, 13 cabin
volumes a minute. That air reaches the rear row first, which is at 105.4 °F at 3 s while the front row is at 115.8 °F.

**Why both cabins stay warm.** The hot surfaces keep heating the air that passes them. At 60 s the dashboard, the
seats and the trim give the air 178, 726 and 534 W in doorFan, where the air moves fast over them, against 84, 137 and
72 W in fourWindows. Carried off by 0.60 m³/s of air, 1.44 kW warms it by about 2.1 K (3.8 °F) on average, and the
door-fan heads, in front of the hot headrests, stay 3.9 K (7.1 °F) above the outside air although 99% of their air
came from outside. The four-window cabin is still emptying at 60 s, with 76% outside air at the heads, so the gap
narrows from about 10 °F at 3-10 s to 3.7 °F at 50 s and 3.8 °F at 60 s.

**Is it believable?** Two checks against something outside the solve. **Four windows in still air**: the textbook
buoyant exchange through a vertical opening, Q = (Cd/3) w (g ΔT/T h³)^½ with Cd 0.6, gives 66 L/s for these four
0.36 m tall windows (2.64 m wide in all) with the cabin 11 K above the outside, and 45 L/s at 5 K; the solve carries
60-61 L/s over the first 30 s and 52 L/s over the last 30, as its cabin cools. At about 60 L/s the 2.76 m³ cabin
turns over in 46 s, and 82% of it is outside air at 60 s. **The door**: a 1.00 m door swung to 65° over its 1.08 m of
height sweeps ½ L² θ h = 0.61 m³ each way a swing; the door's aperture passes 0.28 m³ in and 0.50 m³ out a swing and
the window 0.44 m³ in and 0.22 m³ out, so the pumped volume is the size the door can move.

**Checks.** The cabin's simplified energy budget over 1-60 s, the change in its air's enthalpy against the hot
surfaces' heat and the enthalpy advected and diffused through the openings, each summed at every step, closes to
**-5.5 J (-0.031%) of the net change in fourWindows and -1,548 J (-12.6%) in doorFan**, -0.91% of the heat that passed
through; it grows while the door swings (-4.5% of the net change over 1-7.25 s, -9.5% over 1-50 s), and the pressure
work and kinetic energy that the door's work goes into are not separated from it. No final pressure solve reached
its cap in either run. SST's k needed bounding 319 times in fourWindows and 252 times in doorFan; ω never. The runs
took 2,909 and 22,316 steps.

## What the clip shows, and what it does not

The clip shows the plan at head height, z 1.14 m, as cell values, of the whole car seen from above with the nose up,
"All 4 windows down" beside "1 window + fan the door", **from the moment the windows open to 60 s of the solve** at
three times speed, one solved write a frame, 481 frames at 24 fps, with the door swinging to the last flow frame. It
is coloured by air temperature on a 100-120 °F scale, with the body, the seats, the open windows and, on the right,
the door at its solved angle drawn on the solved outlines, a clock, a line saying "a mid-size sedan after an hour in a
sunny parking lot, no wind", and the question "Hot car, no wind:
windows down or fan the door?". Each panel carries one number: the heads' mean, rounded to the nearest °F.

- **The air by the dashboard, the seat backs and the headrests is hotter than the scale's 120 °F** and shows as its
  top colour. The cap changes no
  number.
- **The drawn door follows the solved one** within 1.55° at every write.
- **The moving streaks are drawn, not solved.** They are parcels moved through the plane's horizontal velocity after
  the solve, at 0.06 s of flow a frame in both panels; the plane's vertical motion is not shown, and about one in eight
  of the door-fan cabin's parcels stands against a seat or wall until it fades.

## What it cannot

- **Fifty swings, not six.** The door is fanned for the whole minute, where the articles describe "a few" to "about a
  half dozen" swings. With six (the earlier solve above) the door was ahead for the first 26.5 s and four windows won
  the minute. The answer here holds for someone who keeps fanning, and it says nothing about the effort of fanning
  or the person standing in the door's opening, who is not modelled.
- **Still air only.** No wind at all. With a light crosswind ([`suvAiring`](../suvAiring)) four windows won from 1.2 s.
- **Airing only.** There is no A/C, no driving off, no sun on the car during the minute, no body vents and no leaks
  through the seals, and no people. The surfaces are held at their measured temperatures and do not cool as the air
  flows over them, which overstates the heat they give back, more so in the door-fan cabin, whose air moves faster
  over them; the means measured were for silver sedans on three days, and a dark car would be hotter. Neither cabin
  has settled at 60 s.
- **The door's energy budget.** In doorFan the simplified budget leaves 1.55 kJ unaccounted over 1-60 s, 12.6% of the
  net change in the cabin's heat; the earlier six-swing solve, identical to 7.2 s, closed to 11.2%. If all of it were
  spurious cooling it would be about 0.5 K (0.9 °F) of the cabin's mean, against a gap of 3.8 °F at 60 s and 10 °F at
  3-10 s. It was not separated into pressure work, kinetic energy and numerical error.
- **The door is a drag term on a fixed mesh, and it conducts heat.** The masked cells stop the air but stay gas, so
  heat and the tracer diffuse through the door's slab, swinging or shut. In the six-swing solve, whose door stayed shut
  from 7.2 s, the heat diffusing out through the shut door's plane was 76 W at 10 s, 19 W at 30 s and 10 W at 60 s; a
  real door would keep most of that in. In the tests below the shut door also leaked, 0.9% of the window's outflow on
  average over 1-2 s. While it swings the slab's inner corner sweeps 20 mm past the aperture's rear edge, smoothed over
  by the one-cell mask, and the fastest air in the domain, 9-10 m/s, is in the narrowing gap at the door's lower rear
  corner as it opens and closes, outside the cabin.
- **No mesh or time-step independence.** One castellated mesh per run, 4 cm over the car with wall functions on
  stepped solids, at Courant 1, and no other mesh or step was tried. No uncertainty bar is put on the 3.8 °F.
- **A restart at 50 s.** doorFan was solved from 0 to 50 s in one go and continued from its 50 s write to 60 s with
  nothing changed (below). The first step after the restart moved head box 3 by +0.017 K and box 5 by +0.007 K, the
  others and the cabin by less than 0.004 K, at most 0.03 °F; we accepted that step.
- **The sizes are estimates.** The windows, the door, the seats and the inside are ours, from the car's overall sizes,
  not measured. The cabin starts uniform at its mean temperature, not stratified.
- **RANS, one run each.** k-ω SST with wall functions; the door's jets and the buoyant plumes are unsteady and these
  are single realisations of them.

## Sources

- Vanos et al., 2018, "Evaluating the impact of solar radiation on pediatric heat balance within enclosed, hot
  vehicles", *Temperature* 5(3):276-292, doi 10.1080/23328940.2018.1468205
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC6204985): three pairs of vehicles, among them silver mid-size sedans, one
  of each pair parked in the sun for about an hour on summer days in Tempe, Arizona. Table 1's final values for the
  mid-size sedan in the sun, twelve trials, average a cabin of 48.7 °C (trials 40.2 to 51.8 °C), a dashboard of 73.8 °C
  and a seat of 53.9 °C (our means of the table's values).
- US patent 6,105,208, a vehicle door check (https://patents.google.com/patent/US6105208): "the soft open position is
  normally about 65-72°", as summarised by a search.
- The car's outside sizes: CarExpert, a 2025 mid-size sedan, 4,920 mm long, 1,840 mm wide, 1,445 mm tall, 2,825 mm
  wheelbase; Edmunds, the same model's front headroom, 38.3 in. Read from search summaries on 27 Nov 2026.
- Motor1, 27 Jun 2025 (https://www.motor1.com/news/764069/scientific-trick-instantly-cool-car/): "Open one of your
  car's rear windows. Then, on the opposite side, rapidly open and close the front door".
- KDWB, 8 Jun 2018
  (https://kdwb.iheart.com/featured/the-dave-ryan-show/content/2018-06-08-lifehack-the-quickest-way-to-cool-down-a-hot-car/),
  citing a Thrillist test of four methods, the fastest being to "fan the car with the driver's side door about a half
  dozen times".
- SlashGear, 8 Jul 2025
  (https://www.slashgear.com/1906301/how-cool-down-car-without-air-conditioning-hot-summer-window-door-fan-trick-science-based-explained):
  "you can simply open all your windows."
- The buoyant exchange through an opening, Q = (Cd/3) w (g ΔT/T h³)^½, is the standard textbook result for a vertical
  opening between two still air masses at different temperatures.
- The schemes and solution settings: [`weldingFumeExtraction`](../weldingFumeExtraction); the door term and the hot
  surfaces: [`suvAiring`](../suvAiring).

## How the case got here

**The solve.** The case was set up and solved by an agent on one of our own machines, 16 physical cores, and checked by
us, on 27 Nov 2026. Before production the agent ran 50-step tests from the start (`results/tests.json`): in still
air, with the cabin at the outside's temperature, the fastest air stayed at 3.5e-4 m/s; the door starting to swing
held its air to 0.026% of the door's speed on average and 0.26% in the worst cell; the door held shut, from 1 to 2 s,
leaked 0.94% of the window's outflow on average and 1.7% at worst, and nothing inwards; and the hot surfaces heating
the air closed the cabin's budget to 0.26% of their heat. The dashboard gave 54 W and the seats 39 W, while the rest
of the inside took 0.24 W back, since it starts at the air's own temperature and the air warmed by the dashboard gives
a little heat to it. No physics, mesh, scheme, step or corrector setting was changed after a test.

fourWindows and the earlier six-swing door run were solved from rest side by side, eight ranks each on separate
cores, each from 0 to 60 s in one go: fourWindows took 1,413 s of wall time. The first study, with the meshes,
the tests, timing probes and both runs, used 1.59 h of the 10 h we allow a solve. The six-swing run was then replaced:
`doorFan` is a copy of it with the door's swing extended from 7.2 s to 60 s, in both forms of the drag term and in the
monitor, and nothing else changed, on the same mesh and the same eight-way decomposition; to 0.40 s its pressure
residuals were the first run's digit for digit. It ran 0-50 s in 5,342 s and stopped at its 50 s write on a rule that
protects the machine's disk. A first continuation stopped itself at 50.40 s, because a screening check flagged the
restart's first step on heads 3 and 5 as five to twelve times the largest change over the same step at the same
phase of earlier swings; we judged the
step too small to matter (above), accepted it, and the continuation was run again from the same 50 s write to 60 s
(1,102 s), the stopped attempt's output after 50 s discarded. The re-solve used 1.80 h of its own 10 h. Its monitor
here is the 0-50 s file joined to the 50-60 s one, the running sums carried across the joint; the planes every
0.125 and 0.25 s are complete, but the every-7.2 s sampler restarted its interval at 50 s and wrote at 57.2 s, not
57.6 s.

**A straight run with this case's `Allrun` solves each run from 0 to 60 s in one segment**, with the solved runs'
settings. **It will not repeat the solved runs bit for bit**: scotch's decomposition can differ from machine to
machine (the solved door run kept its first decomposition), the solved door run was restarted at 50 s, and in a
turbulent buoyant flow the round-off grows. No rebuilt production run was solved.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/sedanStillAir
    ./Allrun fourWindows        # [nProcs], default 8; builds both meshes first
    ./Allrun doorFan            # default 8
    python3 scripts/extract_results.py runs results

The first `Allrun` builds the two meshes in `runs/mesh/` with `scripts/build.py` (blockMesh, one serial castellated
snappyHexMesh of the whole domain, then for each run topoSet, subsetMesh, createPatch, the face and cell zones and
both checkMesh runs; a few minutes, most of it Python reading the meshes). Each run is then written into
`runs/<run>/` by `scripts/run_case.py` and `scripts/prepare.py` (`0/` from the still start, `constant/` and `system/`
from `template/` and the scripts, the door's code and the monitor's), its t = 0 planes are written, it is decomposed
by scotch into collated `processors<n>/` and solved from 0 to 60 s. The door's term and the monitor are coded and
compiled when the solve starts. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `python3
scripts/run_case.py <run> --steps N` (from `scripts/`) solves only N steps; `--resume --end <t>` continues from the
latest write, keeping the monitor's earlier file, which `extract_results.py` joins on. Extra `mpirun` arguments go in
`MPIRUN_ARGS`. `./Allclean` removes the runs and the meshes. The solved runs took about 0.4 h (fourWindows) and 1.8 h
(doorFan) on eight ranks.

Each run writes 481 times of four plans and 241 of five sections and an isosurface over the whole domain (gzipped as
they are finished, about 1 GB a run), the fields every 10 s, and its monitor. `results/` holds the summary, each run's
history every 0.25 s, the mesh audits and the tests' report; no fields, meshes, planes or logs.

The files in `results/` are what `scripts/extract_results.py` wrote from the solved runs' monitors (`--door-name
doorFanContinuous`, the solved door run's folder); `results/tests.json` and `results/mesh_*.json` are the solve's own
reports.

Checked from a clean clone of this case on 27 Nov 2026: `build.py` rebuilt both solved run meshes byte for byte
(`points`, `faces`, `owner`, `neighbour`, `boundary`, `cellZones` and `faceZones`) in about four minutes, with
checkMesh OK at 320,445 and 321,560 cells. `run_case.py --setup-only` wrote both runs' `0/` fields, `constant/g`,
`turbulenceProperties`, `system/fvSchemes`, `fvSolution`, `decomposeParDict` and `initialSurfaces` byte for byte
as the solved runs had them, fourWindows' `fvOptions` too; `thermophysicalProperties` differs only in a comment we
corrected; `controlDict` differs in the abort function object the solved runs carried, left out here, in the
swing's end in the monitor's door clock, which fourWindows never reads, and in one line, as in the door's
`fvOptions`, that writes the door's drag field into the volume writes, which the solved runs did not do and which
was rebuilt for them afterwards; neither touches the flow. Thirty steps of fourWindows and sixty of doorFan, the
door opening to 21° by 0.23 s, on eight ranks, took the solved runs' steps exactly (30 and 35 to 0.125 s) and gave
the solved monitors' head and cabin temperatures at 0.125 s to within 3e-4 K and the window's flow to within 0.02%,
the difference a different decomposition makes, and the door's masked volume and angle to every digit.
