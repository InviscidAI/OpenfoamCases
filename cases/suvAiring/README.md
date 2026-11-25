# A hot SUV aired out: all four windows down, against one window and fanning the door

A full-size SUV has stood an hour in a sunny parking lot, and before getting in the owner wants the hot air out. One
camp has a trick that has been shared millions of times: "Open one of your car's rear windows. Then, on the opposite
side, rapidly open and close the front door" (Motor1), and Thrillist found fanning the door "about a half dozen times"
the fastest of the four ways it tried (as reported by KDWB). The other camp says "you can simply open all your
windows" (SlashGear), and Jalopnik doubts the trick: "it might take more than three or four pumps of the driver's door
to cool the cabin." Each camp has a reason to expect to win: the door pushes air hard while it swings and then stops,
while four windows exchange air the whole time. This case airs the same three-row cabin twice in the same light
crosswind, once with all four door windows down and once with the rear window behind the driver down and the front
passenger door swung fifteen times and then shut, and asks how hot the air is where eight seated heads will be, second
by second for the first 45 s. It is about airing only, not the A/C, driving off, or children or pets left in a car.

    ./Allrun fourWindows    # all four door windows down, 0-45 s
    ./Allrun doorFan        # the rear-left window down, the front passenger door swung 15 times, then shut, 0-45 s

**The result.** **Four windows are cooler at the heads from 1.17 s to the end, and the gap opens once the door is
shut.** Both cabins start at 116 °F (319.82 K) with the air outside at 100 °F (310.93 K) and a breeze of 2.5 m/s at
1.5 m blowing across the car from the driver's side, the side of the door-fan car's open window. Through four windows
the breeze goes straight through, about 1,380 L/s in by the driver's two windows and out by the passenger's, 12 cabin
volumes a minute from 3 s on, and the mean of the eight heads falls to 107.3 °F at 2 s and stays near 106 °F:
**105.9 °F at 45 s**. Fanning the door moves about 850 L/s while it swings (7.5 volumes a minute), in at the window
and out at the door on balance, and is ahead only for the first second (111.0 against 112.4 °F at 1 s); its heads are
at 108.0 °F when the door stops at 18 s, against 106.2 °F. Once it is shut one window trades about 10 L/s, the
dashboard and seats, held hot, warm the cabin back, and the heads are at **112.5 °F at 45 s**, 6.6 °F above four
windows. Read [What it cannot](#what-it-cannot) before any number here: **the 105.9 °F is a mean that hides a hot
third row** (102.2, 100.6 and 113.5 °F by row at 45 s against the door-fan car's even 111.9, 112.3 and 113.1 °F);
**only this wind was solved**, straight across the car, which suits four windows best; **the shut door is a drag term
that conducts heat**, which flatters the door-fan car by a few tenths of a degree F; and there is **no mesh or
time-step study**.

The car and the two layouts are this case's. The buoyant model, the fixed hot surfaces and the moving-door drag term
are those of the earlier still-air solve of this pair (below); the schemes and solution settings are
[`weldingFumeExtraction`](../weldingFumeExtraction)'s, and the air and the turbulence model those of an earlier
buoyant case of ours that is not in this repository, with the enthalpy referred to the outside air's 310.93 K.

**An earlier still-air solve** of the same two cabins, with six swings ending at 7.2 s and no wind, on a 10.88 x
7.04 x 4 m domain of 339,088 and 339,828 cells, was reviewed and replaced by this one; its files are not here. In
still air four windows exchanged about 106 L/s and the door-fan car was ahead for the first 17 s.

## The car

x runs rearward from the front bumper, y towards the passenger side (the right in a US car, so the driver sits at
-y) and z up from the ground; metres. Every edge lies on the 4 cm grid of the cabin's mesh. The sizes are rounded
from the 2025 Chevrolet Suburban's published ones (the GMC Yukon XL is the same body); **the windows, the door and
the inside are our estimates from those overall sizes, not measurements**.

| | value | from |
|---|---|---|
| the body | x 0-5.76, y -1.04 to 1.04, z 0.24-1.92 m: the hood line at z 1.12 over x 0-1.68, the windscreen raked from (x 1.68, z 1.12) to (x 2.36, z 1.92) and stepped on the grid, the roof at z 1.92 to the tail; no wheels or mirrors | 5.75 m long, 2.06 m wide without mirrors, 1.94 m tall (Edmunds) |
| the cabin | x 1.76-5.56, y -0.84 to 0.84, z 0.44-1.84 m behind the inner face of the windscreen through (1.80, 1.12) and (2.40, 1.84); side walls and doors 0.20 m thick; **6.870 m³ of air** with the seats and the dashboard out | ours, from the 1.67 m front shoulder room (Edmunds) |
| the dashboard | x 1.76-2.24, z 0.88-1.12, the cabin's full width; the footwell under it is air | ours |
| the seats | eight, solid boxes: two front buckets (cushions x 2.56-3.04, y ±0.12-0.72, z 0.44-0.80; backs x 3.04-3.20 to z 1.40; headrests to z 1.60), a three-seat second-row bench (cushion x 3.44-3.96, back x 3.96-4.12 to z 1.36, three headrests to z 1.56) and a three-seat third row (x 4.36-4.76, back x 4.76-4.92 to z 1.32, headrests to z 1.52) | ours |
| the windows that open | the four door windows, lowered fully, z 1.20-1.68: front x 2.28-3.04, rear x 3.36-4.12, each side; 0.3648 m² each, of which 0.3392 m² of each rear one meets the cabin past the second-row seat back. The third-row glass, the windscreen and the tailgate stay shut | ours |
| the front passenger door | x 2.16-3.20 (1.04 m), z 0.44-1.72, the wall's 0.20 m thick, hinged on a vertical axis at its front outer corner (2.16, 1.04) and swinging outwards; its aperture is 1.3312 m², 1.3008 m² of it open to the cabin past the dashboard's end | ours |
| the surfaces | inside, held at their measured temperatures for the whole run: the dashboard at 342.59 K (157 °F), the seats at 323.71 K (123 °F), everything else inside (headliner, floor, trim, the glass) at the cabin's 319.82 K (116 °F). The body's outside and the ground are adiabatic | the means ASU and UC San Diego measured for cars parked an hour in the sun on days "in the 100s" in Tempe (Vanos et al. 2018) |
| outside | 310.93 K (100 °F), dry air at 1e5 Pa at the ground, the domain x -7.68 to 13.44, y -9.60 to 19.20, z 0-9.60 m (21.1 x 28.8 x 9.6 m) | ours |

**fourWindows**: all four door windows open from t = 0; every door shut. **doorFan**: the rear-left window, behind the
driver, open from t = 0, and the front passenger door swung open to 60° and shut again fifteen times, 1.2 s a swing,
θ(t) = (π/6)(1 - cos(2πt/1.2)) for 0 ≤ t ≤ 18 s, then shut and at rest to the end. 60° is about a front door's first
detent; the swing is brisk, the door's edge reaching 2.85 m/s. Fifteen swings over 18 s are ours, more than Thrillist's
half dozen.

**There are no people.** The heads are eight boxes of air, 20 cm along x, 24 cm across and 20 cm high (z 1.40-1.60 m),
150 cells and 0.0096 m³ each, in front of each headrest: row 1 at x 2.80-3.00 (head 1 passenger, head 2 driver), row 2
at x 3.72-3.92 and row 3 at x 4.52-4.72 (heads 3/6 on the driver's side, 4/7 in the middle, 5/8 on the passenger's).
"The heads" is the volume mean of all eight.

## The wind and the start

**The breeze** is a neutral atmospheric surface layer blowing along +y, from the driver's side: U(z) = (u*/0.41)
ln((z + z0)/z0) with z0 = 0.01 m (asphalt) and U(1.5 m) = 2.5 m/s, so u* = 0.2043 m/s, with k = u*²/√Cμ = 0.139 m²/s²
and ω = u*/(√Cμ 0.41 (z + z0)) (`scripts/wind.py`). v2512's `atmBoundaryLayerInletVelocity`, `atmBoundaryLayerInletK`
and `atmBoundaryLayerInletOmega` (Cμ 0.09, κ 0.41, C1 0, C2 1) give it on the inlet at y = -9.60 m, with T 310.93 K and
the outside-air tracer at 1. The outlet at y = 19.20 m is `prghPressure` with the hydrostatic p0(z) = 1e5 exp(-9.81 z
/ (287.1 x 310.93)) and `pressureInletOutletVelocity`, with T, k, ω and the tracer `inletOutlet`. The two x sides and
the top are symmetry planes. The ground is a rough wall with `atmNutkWallFunction` at the same z0.

**The precursor** (`scripts/precursor.py`): the wind round the shut car, on the run mesh with the cabin and every
window's and the door's reveal left solid (439,110 cells), isothermal at 310.93 K by a `fixedTemperatureConstraint`:
640 iterations of `buoyantSimpleFoam` with k-ω SST, then 6 s of `buoyantPimpleFoam` with the production settings so
that the wake is in its unsteady state. By 640 iterations the solved precursor's probe just outside the rear-left
window, at (2.88, -1.30, 1.44) m, had moved by 0.24% of its mean over the last 100 and the U residuals were below
4.6e-4. Upwind of the car at x 2.88, y -5.00 m the wind is 2.34 m/s at 1.5 m (2.5 at the inlet) with a turbulence
intensity of 13.2% (12.2%), and 1.36 m/s at 0.3 m (1.71, and 1.61 just inside the inlet): the profile slows near the
ground on the 0.32 m cells there and over the 4.6 m of fetch and the car's blockage, which `results/precursor.json`
gives at four heights. The left windows' outer faces are 4.61
(front) and 4.49 Pa (rear) above the right ones' at z 1.44 m: that is the push the breeze has through the cabin.

**At t = 0** (`scripts/wind.py`) the precursor's 6 s write is copied onto each run's mesh by matching cell centres
(every one of the 439,110 outside cells found its match). The cabin box, x 1.76-5.56, |y| ≤ 0.94, z 0.44-1.84 m,
which takes in the inner half of each open opening's wall, is set to 319.82 K, at rest, with no outside air and the
still-air solve's small k and ω; the outer half of the open openings takes the precursor's air next to it. The cabin's
pressure is hydrostatic at 319.82 K about z = 1.44 m, equal there to the area mean of the mapped outside pressure over
that run's open windows' outer faces (99,985.29 Pa in fourWindows, 99,987.65 in doorFan). The face fluxes start from the
mapped velocity outside and zero inside. The box is rectangular, so it also heats a 0.28 m³ wedge of air just outside
the raked windscreen at t = 0; the cabin's figures leave it out.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96, μ 1.82e-5 Pa s, Pr 0.71,
its enthalpy referred to 310.93 K), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `compressible::alphatJayatillekeWallFunction` with Prt 0.85). Euler in time,
adaptive steps at Courant 1 with maxDeltaT 0.02 s, the first step 1e-4 s; the Courant number holds the step at about
7-9 ms, set by the air through the windows' 4 cm cells, and at 2-8 ms while doorFan's door swings. limitedLinearV 1
for U and limitedLinear 1 for h, k, ω and the tracer; two outer and two pressure correctors; p_rgh by GAMG to 1e-8
(relTol 0.01) and the final solve to 1e-7 (relTol 0, at most 100 iterations). **No radiation.** The outside air is a passive tracer (`scalarTransport`, `outdoor`,
diffusivity 1.408 μ plus the turbulent viscosity), 1 for outside air and 0 for the cabin's at t = 0.

**The door** (`scripts/door.C`, in `constant/fvOptions` as a `vectorCodedSource`) is a drag term on the fixed mesh: a
slab 1.04 x 0.20 x 1.28 m turned about the hinge by θ(t), its edge spread over one cell by a mask m = clamp(1/2 - d/h, 0,
1) of the signed distance d to the slab and the cell size h, and a momentum source -K m ρ (U - U_b) with K = 1e6 s⁻¹
that holds the air in it at the door's velocity U_b = θ'(t) ẑ x (r - r_hinge). It stops the air, not heat: the masked
cells stay gas. Shut, it covers 0.26624 m³, every aperture cell fully; at 30° and 60° the mask is within 0.18% and 0.13%
of the slab's volume. fourWindows has no door term.

**The meshes** (`scripts/build.py`): a background of 0.32 m cubes over the whole domain (blockMesh, 66 x 90 x 30),
refined by snappyHexMesh, castellated only, without snapping or layers: 0.16 m over x -2.56 to 8.32, y -3.20 to 8.00, z
0-4.16 m (round the car and its wake downwind), 0.08 m over x -0.48 to 6.24, y -1.68 to 2.56, z 0-2.40 m, and 0.04 m
in the cabin box (x 1.68-5.68, y -1.28 to 1.28, z 0.40-1.92 m) and the door's swing (x 2.08-3.28, y 1.04-2.08, z
0.40-1.80 m), two cells between levels, the same in both runs. The car's solid cells (the body round the cabin, the seats
and the dashboard, less each run's openings) are chosen by cell centre and cut out with topoSet and subsetMesh, so the
solids are stepped on the 4 cm cells. The cut faces are sorted into `bodyExterior`, `dashboard`, `seats` and
`cabinInterior`; the openings are face zones on the side walls' inner planes (y = ±0.84 m) and the heads and the cabin
cell zones. **551,016 hexahedral cells (fourWindows) and 551,756 (doorFan)**, 4 cm in the cabin and the openings;
`checkMesh` OK, non-orthogonality at most 25.24°. One mesh each, no mesh study.

**The monitor** (`scripts/diagnostics.C`, a coded function object run every step, one row every 0.125 s into
`postProcessing/diagnostics83/diagnostics.csv`): the volume, mass, volume- and mass-mean temperature, outside-air mass
and excess enthalpy above 310.93 K of the cabin and of each head box; the gross flow each way through each opening, in
m³/s and kg/s, with the enthalpy and tracer it carries and its diffusive heat; the heat into the air from each hot
patch, for all its faces and for the cabin's; the door's angle, its masked volume, the power it gives the air and how
well the masked air follows it; the hottest and coldest cabin air, the fastest air, and the twelve cells of highest
Courant number on each rank; and, summed every step, the heat, the advected and diffused enthalpy, the pressure,
gravity and kinetic terms that close the cabin's energy budget, and in doorFan the air each swing moves, split at the
swings' exact ends. It carries its running sums across a restart. The planes are those of the still-air solve: plans at
head height (z 1.50 m, interpolated and as cell values), at the sills (1.30 m) and at 1.0 m every 0.125 s, three
lengthwise and three cross sections and the 315.37 K isosurface every 0.25 s, with T, U, the tracer and the door's
drag, from t = 0.

## Results

`results/summary.txt` and `results/<run>/history.csv` (every 0.25 s), from `scripts/extract_results.py`; the
precursor's report is `results/precursor.json`.

| heads, °F | 0.5 s | 1 s | 2 s | 3 s | 10 s | 18 s | 30 s | 45 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fourWindows | 115.99 | 112.37 | 107.32 | 106.88 | 106.88 | 106.24 | 106.24 | **105.87** |
| doorFan | 112.35 | 111.04 | 109.44 | 110.32 | 109.64 | 107.95 | 111.06 | **112.50** |
| fourWindows, rows 1/2/3 | 116.0/116.0/116.0 | 109.4/110.7/116.0 | 104.2/100.7/116.0 | 102.6/101.0/115.6 | 102.6/100.5/116.1 | 102.2/100.7/114.5 | 102.3/100.6/114.5 | 102.2/100.6/113.5 |
| doorFan, rows 1/2/3 | 115.9/106.3/116.0 | 114.9/103.4/116.1 | 113.0/102.6/113.9 | 112.9/104.3/114.6 | 110.7/105.8/112.8 | 109.0/103.7/111.5 | 111.0/110.4/111.8 | 111.9/112.3/113.1 |

| | 3 s | 10 s | 18 s | 30 s | 45 s |
|---|---:|---:|---:|---:|---:|
| the cabin's mean air, fourWindows, °F | 111.11 | 109.98 | 109.29 | 108.78 | 108.47 |
| the cabin's mean air, doorFan, °F | 113.11 | 110.78 | 109.47 | 111.16 | 111.93 |
| outside air at the heads, fourWindows, % | 58.2 | 59.7 | 67.6 | 71.4 | 77.3 |
| outside air at the heads, doorFan, % | 37.6 | 48.1 | 64.9 | 61.1 | 59.9 |
| the cabin's starting excess heat gone, fourWindows, % | 30.4 | 37.3 | 41.6 | 44.7 | 46.6 |
| the cabin's starting excess heat gone, doorFan, % | 17.9 | 32.2 | 40.3 | 29.7 | 25.0 |

The heads' curves cross once after 0.5 s, at 1.172 s, and fourWindows is the cooler from then to 45 s. The cabin
starts with 66.84 kJ above the outside air in both runs.

**Where the breeze goes.** In fourWindows it comes in through the driver's two windows and leaves through the
passenger's, 686 and 692 L/s in and 701 and 678 L/s out over 3-18 s, with 2 L/s or less the other way, and the same to
45 s: 1,377 L/s, 12.0 cabin volumes a minute, against 106 L/s (0.9 a minute) through the same windows in still air.
It reaches the head plane at once: over 3 s the share of the head plane's cabin part cooled by more than 1 K goes from
0.1% at 0.25 s to 23% at 1 s and 66% at 3 s, and the two runs' head planes differ by more than 1 K over 42% of it at 1 s
and 65% at 3 s (the study's own figures from its planes, which `extract_results.py` does not repeat). It runs
straight across rows 1 and 2, whose five heads are at 100.0-103.0 °F with 98.8-100% outside air at 45 s, and passes in
front of the third row, which no open window faces: its heads are at 113.1-114.0 °F with 38-41% outside air at 45 s.
In doorFan the door does the work while it swings: each swing takes about 0.77 m³ in and 0.21 m³ out through the
window and 0.26 m³ in and 0.83 m³ out through the door, the same from the first swing to the fifteenth; over 3-18 s
that is 629/176 L/s at the window and 224/678 L/s at the door, about 850 L/s in, 7.5 cabin volumes a minute, the
breeze keeping the window mostly an inlet. Once the door is shut nothing lets the air out on the other side, and the
one window trades 11 L/s each way over 18.5-30 s and 8 L/s over 30-45 s, 0.1 of the cabin a minute, less than the
20-23 L/s it traded in still air.

**Why the door-fan cabin warms back.** From 18 to 45 s the hot surfaces give the door-fan cabin's air 13.44 kJ; 1.09 kJ
leaves with the air at the window and 2.31 kJ by diffusion through the openings' planes, 1.46 kJ of it through the
shut door's, and the cabin keeps 10.22 kJ. Over the same time the same surfaces give the four-window cabin 37.65 kJ,
because its air is cooler and moves faster over them, and the breeze carries 40.89 kJ out. At 45 s the dashboard, the
seats and the trim give the air 288, 534 and 610 W in fourWindows and 89, 159 and 57 W in doorFan. From 18 to 45 s
the door-fan heads warm by 4.6 °F and the cabin's mean by 2.5 °F, most likely because the cool outside air is denser
and stays low and by the window while the head layer reheats, as in the still-air solve.

**Checks.** The cabin's energy budget over 1-45 s, the change of its enthalpy and kinetic energy against the hot
surfaces' heat, the enthalpy advected and diffused through the openings and the pressure and gravity work, each summed
at every step, closes to **+22.99 J (+0.040%) in fourWindows and -495.88 J (-1.378%) in doorFan** of the surfaces' heat;
over 18-45 s, with the door shut, doorFan's closes to +0.026%, so its error is the door's swings'. No final pressure
solve reached its cap in either run; the largest final residual was 9.9997e-8. SST's k needed bounding 114 times in
fourWindows, all before 2.3 s, and 24 times in doorFan, before 0.9 s; ω never. The runs took 5,755 and 6,848 steps.

## What the clip shows, and what it does not

The clip shows the plan at head height, z 1.50 m, as cell values, of the whole car seen from above with the nose up,
"All 4 windows down" beside "1 window + fan the door", **from the moment the windows open to 45 s of the solve** at
three times speed, one solved write a frame, 361 frames at 24 fps. It is coloured by air temperature on a 100-116 °F
scale, with the body, the seats, the open windows and, on the right, the door at its solved angle drawn on the solved
outlines, a clock, "light breeze" with three arrows for its direction, and the question "Hot SUV: 4 windows down or fan
the door?". Each panel carries one number: the heads' mean, rounded to the nearest °F.

- **The air by the dashboard and the seats is hotter than the scale's 116 °F** and shows as its top colour. The cap
  changes no number.
- **The shut door shows as a thin cooler band inside it.** That is the modelled door conducting heat (below), not
  something a real door does.
- **The moving streaks are drawn, not solved.** They are parcels moved through the plane's horizontal velocity after
  the solve, at 0.04 s of flow a frame, a third of the clip's own rate, in both panels; the plane's vertical motion is
  not shown.

## What it cannot

- **One wind, from one side.** The breeze blows straight across the car from the driver's side, at 2.5 m/s, steady and
  neutral, the same in both runs. That is the direction four windows like best, and it is the side of the door-fan
  car's open window. Wind from ahead, from behind, from the passenger's side or gusting was not solved, nor still air
  here (the earlier still-air solve gave the door the first 17 s).
- **Airing only.** There is no A/C, no driving off, no sun on the car during the 45 s, no body vents and no leaks
  through the seals, and no people. The surfaces are held at their measured temperatures and do not cool as the air
  flows over them, so the heat they give back is if anything too much in the cooler four-window cabin; the means
  measured were for six smaller silver cars, and a dark SUV would be hotter. Neither cabin has settled at 45 s.
- **The shut door is a drag term on a fixed mesh, and it conducts heat.** The masked cells stop the air but stay gas,
  so heat diffuses through the shut door's plane: 102 W just after it shuts at 18 s, **46 W at 30 s and 61 W at 45 s**,
  1.46 kJ over 18-45 s. A real door would keep most of that in, so this flatters the door-fan cabin, by roughly
  0.2 K, a few tenths of a degree F. The tracer diffuses through it too, so doorFan's outside-air shares are not purely
  air that came in through the window. **The shut door also leaks**: in the 50-step test with the door held shut in the
  wind, its aperture passed 1.43e-4 m³/s out, **4.8% of the window's outflow, against the 2% we asked for**; K = 1e6 was
  kept, as in the still-air solve, where a stiffer K crashed when the door first opened. While it swings, the slab's
  inner corner sweeps 19 mm past the aperture's rear edge, smoothed over by the one-cell mask, and at 0.125 s air in the
  hinge's mask outside the cabin is down to 307.8 K, gas standing in for the door, not cabin air.
- **No mesh or time-step independence.** One castellated mesh per run, 4 cm in the cabin with wall functions on
  stepped solids, at Courant 1. A copy of doorFan at Courant 2 over 0-2.4 s **differed by up to 0.42 K at a head box**
  (against the 0.1 K we would have accepted) and its energy budget closed only to -20.6%, so it was not used, and that
  is the only measure of the step's effect. No uncertainty bar is put on the 6.6 °F.
- **The sizes are estimates.** The windows, the door, the seats and the inside are ours, from the SUV's overall sizes,
  not measured. The cabin starts uniform at its mean temperature, not stratified. The second-row seat back covers the
  lower rear corner of each rear window from inside, and the rectangular start heats a small wedge outside the
  windscreen.
- **The 105.9 °F is a mean of eight heads.** At 45 s four windows' rows are at 102.2, 100.6 and 113.5 °F (102, 101 and
  114) against the door-fan car's 111.9, 112.3 and 113.1 °F: the third row, behind the through-flow, is no better off
  with four windows down, and three of the eight heads sit there. No sentence should say the whole car is cooler.
- **One window in a breeze may trade too little.** About 10 L/s through one open window in a 2.5 m/s breeze is on the
  low side of a rule of thumb for one-sided ventilation (about 20 L/s, quoted from memory, not checked); doubling it
  would cool the door-fan cabin by about 0.5 °F, not change which is cooler.
- **RANS, one run each.** k-ω SST with wall functions; the window jets and the wake behind the car are unsteady and
  these are single realisations of them.

## Sources

- Vanos et al., 2018, *Temperature* (Arizona State University and UC San Diego), as summarised by ASU News, 24 May 2018
  (https://news.asu.edu/20180516-discoveries-asu-study-hot-cars-can-hit-deadly-temperatures-within-one-hour): on hot
  days "in the 100s" in Tempe, Arizona, cars parked in the sun for an hour averaged a cabin of 116 °F, "Dashboards
  averaged 157 degrees, steering wheels 127 degrees, and seats 123 degrees in one hour."
- Edmunds, 2025 Chevrolet Suburban features and specs (https://www.edmunds.com/chevrolet/suburban/2025/features-specs):
  226.3 in long, 81.1 in wide without mirrors, 76.2 in tall, 65.6 in front shoulder room; Kelley Blue Book
  (https://www.kbb.com/chevrolet/suburban/2025/specs): 134.1 in wheelbase. Read from search summaries on 20 Nov 2026.
- Motor1, Alexandra Samuels, 27 Jun 2025 (https://www.motor1.com/news/764069/scientific-trick-instantly-cool-car/):
  "Open one of your car's rear windows. Then, on the opposite side, rapidly open and close the front door", "multiple
  times", the Reel describing it at "over 6.5 million views".
- KDWB, 8 Jun 2018
  (https://kdwb.iheart.com/featured/the-dave-ryan-show/content/2018-06-08-lifehack-the-quickest-way-to-cool-down-a-hot-car/),
  citing a Thrillist test of four methods, the fastest being to "fan the car with the driver's side door about a half
  dozen times".
- SlashGear, Shane O'Neill, 8 Jul 2025
  (https://www.slashgear.com/1906301/how-cool-down-car-without-air-conditioning-hot-summer-window-door-fan-trick-science-based-explained):
  "Alternatively, if you're in a hurry and can't go through the open window, door-as-a-fan method, you can simply open
  all your windows."
- Jalopnik, Alvin Reyes, 5 Apr 2026 (https://jalopnik.com/2136792/science-trick-to-cool-down-hot-car-in-seconds/): "In
  some cases, though, it might take more than three or four pumps of the driver's door to cool the cabin."
- The schemes and solution settings: [`weldingFumeExtraction`](../weldingFumeExtraction).

## How the case got here

**The solve.** The case was set up and solved by an agent on a cloud workspace of four cores and checked by us, on
24 Nov 2026, as a re-solve of the still-air pair with the breeze, the larger domain and fifteen swings in place of six;
the car, the openings, the surfaces, the door term and its K, the model and the monitor are the still-air solve's.
Before production the agent ran the precursor and then 50-step tests from the windy start, two cores each: the hot
surfaces heating fourWindows' air closed the cabin's budget to 1.0% of their heat; the door starting to swing, 2.0%; the
door held shut, 0.21%, with the 4.8% leak above; and the door on a clock advanced by 0.3 s, which its air followed to
0.24% at worst. The first decomposition of the precursor stopped on a symmetry patch's face flux written with the
wrong type, before any solve, and was corrected; a first steady precursor without the temperature constraint was
stopped after about 100 s, because the compressible energy equation let the isothermal outside drift, and was
replaced. No physics, mesh, scheme, step or corrector setting was changed by either.

Both runs were launched at maxCo 1 from rest, one after the other on all four cores, for 60 s. From doorFan's first
2.4 s the agent's projection of the whole study passed the 10 h we allow a solve, the Courant 2 copy that would have
shortened it failed its checks (above), and both runs stopped at their 10 s writes; recounted there, 60 s still came to
11.0 h. We then set 45 s in place of 60 s under the same
10 h, and both runs were continued from their 10 s fields, with the same decomposition and the door on the same clock:
**0-10 s, then 10-20, 20-30, 30-40 and 40-45 s**, each segment ending at a write and in `End`, with no restart from
zero and no swing repeated. At 30 s the two runs' heads differed by 2.68 K, so the stop for runs too alike to tell apart
did not apply. The heads' curves show no step at any restart. The runs took 9,571 s (fourWindows) and 13,242 s
(doorFan) of wall time on four ranks, and everything, with the meshing, the precursor, the tests and the Courant 2 copy,
7.65 h of the 10 h. The volume fields were written every 10 s to 10 s and every 5 s after; the solved runs carried an
abort function object, which stopped them at 10 s and paused them at 20, 30 and 40 s, and it is left out here.

**A straight run with this case's `Allrun` is the same run**, in two segments, 0-10 s and 10-45 s, written as the
solved runs were, so that the steps land on the same write times. **It will not repeat the solved runs bit for bit**:
scotch's decomposition can differ from machine to machine, the solved runs were also restarted at 20, 30 and 40 s, and
in a turbulent buoyant flow the round-off grows. The precursor's steady stage runs a fixed 640 iterations here, where
the solved one was stopped at 640 by the agent's monitor once the probe and residuals had settled; `precursor.py`
reports both measures. A rebuilt precursor (below) gives a start within a few mm/s of the solved one's. No rebuilt
production run was solved.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI (the atmospheric boundary conditions are
v2512's `atmosphericModels` library), and Python 3 with NumPy.

    cd cases/suvAiring
    ./Allrun fourWindows        # [nProcs], default 4; builds the meshes and solves the precursor first
    ./Allrun doorFan            # default 4
    python3 scripts/extract_results.py runs results

The first `Allrun` builds the three meshes in `runs/mesh/` with `scripts/build.py` (blockMesh, one serial
castellated snappyHexMesh of the whole domain, then for each run topoSet, subsetMesh, createPatch, the face and cell
zones and checkMesh; about 8 minutes, most of it Python reading the meshes), then solves the precursor in
`runs/precursor/` with `scripts/precursor.py` (about 0.3 h on four ranks) and maps it onto both run meshes. Each run
is then written into `runs/<run>/` by `scripts/run_case.py` and `scripts/prepare.py` (`0/` from the mapped start,
`constant/` and `system/` from `template/` and the scripts, the door's code and the monitor's), its t = 0 planes are
written, it is decomposed by scotch and solved from 0 to 10 s and on to 45 s. The door's term and the monitor are
coded and compiled when the solve starts. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean`
removes the runs, the meshes and the precursor. The solved runs took about 2.7 h (fourWindows) and 3.7 h (doorFan) on
four ranks.

Each run writes 361 times of four plans and 181 of six sections and an isosurface over the whole domain (gzipped as
they are finished, about 1 GB a run), the fields every 10 s and then 5 s, and its monitor. `results/` holds the summary
and each run's history every 0.25 s; no fields, meshes, planes or logs.

The files in `results/` are what `scripts/extract_results.py` wrote from the solved runs' monitors and mapped starts;
`results/precursor.json` is the solved precursor's own report.

Checked from a clean copy of this folder on 25 Nov 2026: `build.py` rebuilds both solved run meshes byte for byte
(`points`, `faces`, `owner`, `neighbour`, `boundary`, `faceZones`, `cellZones`, `pointZones` and snappyHexMesh's level
and index files, and the blockMesh and snappyHexMesh dictionaries), with checkMesh OK at 551,016 and 551,756 cells and
non-orthogonality 25.2394° at most, and the precursor's mesh at its solved 439,110 cells. From the solved runs' mapped
starts, `run_case.py --setup-only` writes both runs' `0/` fields, `constant/fvOptions`, `g`, `turbulenceProperties`,
`system/fvSchemes`, `fvSolution`, `decomposeParDict` and `initialSurfaces` byte for byte, and `controlDict` but for its
end time and the abort function object, and, edited as `run_case.py --resume` edits it, the solved runs' final
`controlDict` but for the abort function object; `thermophysicalProperties` differs only in a comment we corrected; the
t = 0 planes are the solved runs' byte for byte once theirs are unzipped. The precursor, solved again from the clean
copy on four ranks (280 s steady, 900 s transient), mapped every outside cell of both meshes and gave a start that
differs from the solved runs' by 0.004 m/s rms in U (0.17 m/s at most), 0.0018 Pa rms in p (0.06 Pa at
most) and not at all in T and the tracer, with the cabins' reference pressures within 0.0005 Pa; its steady stage's
probe had moved by 0.57% over its last 100 iterations, against the solved run's 0.24%, the difference a different
decomposition makes. No production run was solved from the clean copy. `extract_results.py` on the solved runs' monitors gives the study's own
figures: the heads at every report time, the 1.172 s crossing, the per-swing volumes and the +0.040% and -1.378%
budgets.
