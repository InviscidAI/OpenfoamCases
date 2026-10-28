# Airing a heated room: the window wide open, or on tilt

German advice on airing a room in winter is to open the windows wide for a few minutes
(Stoßlüften), not to leave them on tilt (Kipplüften). This case opens the window above
[`radiatorUnderWindow`](../radiatorUnderWindow)'s radiator on a still 0 °C morning and follows
the room for five minutes, once with the window turned wide open and once on tilt. The numbers
it reports are **the share of the room's own air replaced** and **the air coming in through
the window, in room volumes an hour**. It is not about heat loss, heating costs or comfort.

radiatorUnderWindow's room, made 3-D and 3.5 m wide, with its window opened: one OpenFOAM case,
two runs that differ only in the sash:

    ./Allrun open        # the sash turned wide open, 0-300 s
    ./Allrun tilted      # the sash on tilt, its top 140 mm into the room, 0-300 s

**It is a still day and an empty room, from the moment the window opens.** No wind, no
furniture, the room's surfaces held at 20 °C, and only the first five minutes, when the room
is at its warmest and the exchange at its fastest. Read [What it cannot](#what-it-cannot)
before any number here.

Two more runs put a US double-hung window in the same wall, its top sash lowered 10 cm, or the
same 10 cm split between the top sash lowered 5 cm and the bottom sash raised 5 cm, the US tip
for airing a room. They are in [A US double-hung window](#a-us-double-hung-window):

    ./Allrun doubleHungTop     # the top sash lowered 10 cm, 0-300 s
    ./Allrun doubleHungSplit   # the top sash lowered 5 cm and the bottom one raised 5 cm, 0-300 s

The same cold inflow along the floor, through an open front door, is what lifts a dry-ice
cauldron's CO2 off a living-room floor in [`dryIceCauldron`](../dryIceCauldron).

The same room with its window shut, heated with the radiator's 60 W either from the radiator or
through the whole floor, is [`underfloorVsRadiator`](../underfloorVsRadiator).

An attic room of the same floor, aired through a roof window turned wide open, against this
room's wide-open window rebuilt with the barometric outdoor boundary, is
[`roofWindowAiring`](../roofWindowAiring).

The same room aired wide open for five minutes and then shut, its radiator sized for the room and
behind a thermostatic valve that is turned off while the window is open or left on, with walls
that store heat, is [`airingRadiatorValve`](../airingRadiatorValve). It asks what leaving the
valve on costs.

The tilted sash, unchanged, in a small bathroom after a ten-minute shower, against a ceiling
extractor fan at 15 l/s with the window shut, is [`showerFanVsWindow`](../showerFanVsWindow). It
asks what share of the shower's water vapour each takes out in fifteen minutes.

## The room

| | value | from |
|---|---|---|
| room | 4.0 m from the window wall to the inner wall and 2.4 m high, as radiatorUnderWindow's section; 3.5 m wide; 33.6 m³ | radiatorUnderWindow; the width ours |
| window | a clear opening 1.0 m wide and 1.2 m tall, sill 0.90 m above the floor, centred in the room's width, at the inside face of a 24 cm wall | radiatorUnderWindow's glass; the width is the radiator's length |
| radiator | radiatorUnderWindow's box, 0.083 m deep and 0.60 m tall, bottom 0.15 m above the floor, 0.04 m off the wall, 1.0 m long under the window, 60 W in all (radiatorUnderWindow's 60 W/m) | a Stelrad Compact K1 600 x 1000; radiatorUnderWindow says why 60 W/m |
| outside | still air at 0 °C, 1.5 m deep beyond the wall, from 1 m below the floor to 3.4 m up, and 2.5 m either side of the window, open on every face | ours |
| surfaces | the room's floor, ceiling and walls held at 20 °C; the wall's outer face, the reveal and the sash adiabatic | ours |
| start | the room's air at rest at 20 °C, the outside air at 0 °C; at t = 0 the window is open | ours |

The radiator is radiatorUnderWindow's enthalpy source spread over its box, through which the
air passes freely. Its 60 W is about a tenth of a real radiator's, for the reasons that case
gives, and it stays on.

## The window

**Wide open,** the sash is turned on its side hinge to stand at 90° to the wall, a plate in the
plane z = +0.5 m from the frame 1.0 m into the room (a baffle of 1,240 faces). The whole
1.0 × 1.2 m opening is clear.

**On tilt,** the sash turns about its bottom edge. On an ordinary turn-tilt fitting its top
swings 140 mm into the room: that is Roto NT's standard tilt width (Roto's care and
maintenance guide, p. 6) and the Kippöffnungsweite of Winkhaus's activPilot scissor
SC2.20-9.LS, at the top of the usual 10-15 cm. The clear gap is smaller than the swing,
because the sash sits in the frame's rebate and overlaps it. Winkhaus gives a rebate clearance
(Falzluft) of 12 mm and a sash overlap of 20 mm. Maas, Schmidt and Hauser (wksb 42/98,
Tabelle 2) measured a clear opening of 10.4 cm on a 1.21 m sash whose fitting swung it
15.5 cm, about two thirds. Sash profiles are 70-85 mm deep (VEKA Softline 82, aluplast Ideal
4000 70/85).

So the tilted sash is a solid profile 80 mm deep, with 50 mm of it behind the frame's face
when shut, turned until its top has moved 140 mm into the room. Its cells are taken out of
the mesh with the wall's. The top gap is then 90 mm clear, two thirds of the swing, and the
side gaps open only where the sash's outer face has left the frame, above 0.43 m up the sash.
On the mesh the gaps are 0.080 m² at the top and 0.0342 m² down each side, 0.148 m² in all
(`results/summary.txt`). The top gap is 11% short of the drawn 0.090 m² because the 20 mm
cells step the sash's edge, and the sides are within 1.5% of the drawn 0.0347 m². The rebate
clearance is narrower than a cell and is left shut.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's
own Allrun.

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect gas with
  radiatorUnderWindow's properties (c_p 1005 J/kgK, μ 1.82e-5 Pa s, Pr 0.71), k-omega SST
  with the buoyancy source on k (`buoyancyTurbSource`), PIMPLE with 2 outer and 2 pressure
  correctors, Euler in time at Courant 1, limitedLinear for energy and turbulence and
  limitedLinearV for momentum.
- **Mesh:** one graded blockMesh box of 751,488 cells over the outside air, the wall and the
  room, cut down with subsetMesh to the air: 526,848 cells wide open and 522,368 on tilt.
  Cells are 20 mm across the reveal and the first 0.3 m of the room, 30 mm tall over the
  window, 10 mm at the floor and 20 mm at the window's side edges.
- **The outside's open faces** hold the still 0 °C air's own hydrostatic pressure, face by
  face (`prghTotalPressure` with p0(y) = 1e5/(1 + g y/(R T)), written by `hydrostatic_p0.py`
  once the mesh is final), less the dynamic head on inflow. Air coming in is at 0 °C. Why it is
  this boundary and not a uniform one is in [How the case got here](#how-the-case-got-here).
- **The room's own air** is a passive scalar s, 1 in the room at the start and 0 outside and
  in the reveal, carried by the flow with T's diffusivity (`scalarTransport`, α + α_t with
  Pr 0.71 and Pr_t 0.85). The share replaced is 1 − ∫ρs over the room / the room's mass at
  the first step.
- **Monitors, every step:** ∫ρs over the room and over everything inside the frame's plane,
  the room's mass and mass-average temperature, the gross mass flow each way through the
  frame's plane x = 0 and Σφs through it, and on tilt the gross flow each way through the top
  gap and each side gap. Three planes every 0.625 s for the clip: the mid-plane through the
  window (z = 0.005 m), a floor plane 0.1 m up, and a plane beside the window (z = −0.65 m).

## How the case got here

The first build had two faults, and both runs were solved again with them fixed. Those runs
are not kept here; `make_case.py tilted-thin` and `--outdoor fixed` write their setups.

**The tilted sash.** The first build's tilted sash was a plate of no thickness, hinged at the
sill, with its top 0.14 m from the frame and its side triangles open from the hinge up: an
opening of 0.31 m², 0.14 m² at the top and 0.084 m² down each side, twice the solid sash's.
That run took in 0.053 kg/s at 300 s, all of it through the side triangles, and replaced 37%
of the room's air in five minutes, 5.5 air changes an hour as a well-mixed decay: more than
twice the top of the measured range below. A real sash's depth closes the bottom of those
triangles, hence the solid sash.

**The outdoor boundary.** The open faces first held p_rgh at a uniform 1e5. That is right for
still 0 °C air, but a face that warm air leaves through then holds the pressure of a column of
that warm air, not of the outdoor air: where the window's plume reached the top of the domain
at about 13 °C, 1-2 Pa too much, against about 0.5 Pa driving the flow across the window. The
plume pooled under the top boundary and spread down. In the first build's open run the outdoor
air beside the window warmed to about 2 °C by 30-60 s and was still 1.2 °C at 300 s, which cut
the open window's driving temperature difference by a sixth to a seventh, and the warm air
coming down in front of the window carried the room's own air back in: the outdoor air 0-0.2 m
in front of the opening's lower half, where the cold air goes in, was 12% room air at 60 and
120 s and 6% at 300 s. With the hydrostatic boundary the plume leaves through the top at about
1 m/s, the outdoor air beside the window stays at 0.0-0.5 °C, and the air going in is pure
outdoor air at every time. On cold faces the new boundary gives exactly the old values.

The wide-open run with the hydrostatic boundary had the first build's mesh, fields and
decomposition, so the two differed only in the boundary, and agreed to within 1% to 25 s. By
300 s:

| run | sash | outdoor boundary | inflow, room volumes an hour, mean over 0-300 s | as a well-mixed decay | share replaced at 300 s |
|---|---|---|---:|---:|---:|
| first build, wide open | wide open | uniform | 19.05 | 19.7 | 81% |
| first build, tilted | a plate, side triangles open | uniform | 4.7 | 5.5 | 37% |
| tilted, solid sash | solid, 140 mm | uniform | 1.85 | 1.88 | 14.5% |
| **`open`** | wide open | hydrostatic | **19.8** | 29.3 | **91%** |
| **`tilted`** | solid, 140 mm | hydrostatic | **1.93** | 1.97 | **15%** |

At 300 s the open window takes in 6% more than with the uniform boundary and the tilted one
5.5% more. The open room's share replaced rises more than its inflow, from 81% to 91%, because
the uniform boundary had also fed the room's own air back in.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only open`
  and `--setup-only tilted` wrote the solved runs' meshes (points, faces, owner, neighbour,
  boundary, cell and face zones) and every initial field, the hydrostatic p_rgh included, byte
  for byte: 526,848 and 522,368 cells, `checkMesh` OK, one region. Their dictionaries have
  the solved runs' values and differ only in comments, and the open run's
  `decomposeParDict`, which was the first build's manual decomposition so that the boundary
  comparison above shared it; `scotch` on 7 ranks, as here, splits the mesh differently, so a
  re-solve will not match the committed histories to the last digit.
- **The sash on the mesh** (`scripts/geometry_check.py`, `results/geometry_<run>.txt`). Wide
  open, the baffle's faces lie in the plane z = +0.500 m from x = 0.01 to 0.96 m and
  y = 0.915 to 2.085 m. On tilt, the sash's faces lie a median 4.3 mm from the drawn faces,
  40 mm at most where the 20 mm cells step them. `results/frame_60s.png` is both runs'
  mid-plane at 60 s with the solved cells as they are and the drawn wall, opening, sash and
  radiator over them (`scripts/frame_check.py`); on that plane no solved cell's centre lies
  inside the drawn sash.
- **The scalar's budget.** Over everything inside the frame's plane, the change in ∫ρs against
  the time integral of Σφs through the plane closes to 0.28% (wide open) and 0.47% (tilted) of
  what has left at 300 s, and 0.44% and 1.02% at 60 s. In the first seconds it is large as a
  share (23% wide open at 0.625 s in `history.csv`), because s is a step at the opening and the
  monitor's face value, the linear interpolate, undercounts what leaves. The share replaced
  is read from the transported field over the room, not from the monitor.
- **Both runs ended cleanly** at 300 s, in 13,800 steps wide open and 11,014 on tilt.

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors. The inflow is the gross mass flow into the room
through the window, as volume of 0 °C air (1.275 kg/m³) over the room's 33.6 m³. The
well-mixed decay is the share replaced read as −ln(1 − share)/t.

| | `open` | `tilted` |
|---|---:|---:|
| **share of the room's own air replaced, at 60 / 120 / 300 s** | 41.1 / 66.5 / **91.3%** | 3.05 / 6.14 / **15.2%** |
| **inflow, mean over 0-300 s** | **19.8 room volumes an hour** (1.65 room volumes in five minutes) | **1.93 an hour** (0.16) |
| inflow at 60 / 300 s | 23.0 / 17.4 an hour (583 m³/h at 300 s) | 1.90 / 1.92 an hour (65 m³/h) |
| as a well-mixed decay at 300 s | 29.3 an hour | 1.97 an hour |
| the room's mass-average temperature at 300 s | 8.4 °C | 18.6 °C |

**Tilted, the window takes in 9.8% of the air the open one does** over the five minutes.

Wide open, the inflow falls from 23 room volumes an hour at 60 s to 17.4 at 300 s as the room
cools to a mass average of 8.4 °C. On tilt it holds at 1.90-1.93 while the room cools to
18.6 °C. On tilt all of the inflow comes in through the two side gaps, 0.0109 kg/s each at
300 s, and the top gap carries 0.0170 of the 0.0225 kg/s out, with nothing in.

**The two measures part wide open.** On tilt the room stays nearly mixed, and the share
replaced and the inflow give the same rate. Wide open, 1.65 room volumes come in over five
minutes, which would replace 81% of a well-mixed room's air, but the cold air lies on the
floor and pushes the room's own air out through the top of the opening, so 91% of it goes. A
flow measurement and a tracer decay would read this room differently, and the inflow is the
figure to set beside the measured rates below.

### Against the authorities and the measurements

The Umweltbundesamt's advice page, "Wie lüfte ich richtig?", says to air two or three times a
day for about five minutes with the windows wide open, and warns that windows left on tilt for
long periods raise heating costs "drastisch" and cool the wall beside them. It gives no
air-change figures. Its guidance for schools (*Leitfaden für die Innenraumhygiene in
Schulgebäuden*, 2008) gives wide-open windows "etwa 10–20/h" (p. 25) and calls tilted airing
"weitgehend wirkungslos, da durch sie kaum Luft ausgetauscht wird" (p. 26); its 2017
*Anforderungen an Lüftungskonzeptionen in Gebäuden* (p. 18) calls airing through tilted
windows "unzweckmäßig", summer excepted. The Innenraumlufthygiene-Kommission's 2020 statement
(p. 4) says five minutes wide open can be enough in winter. dena's factsheet *Richtig heizen
und lüften* (2022, p. 2) and the economics ministry's Energiewechsel sheet (2022, p. 1) say the
same in words. None of them gives a figure for a tilted window. The figures come from
measurements and the standard:

- A Berlin borough's sheet on airing (Treptow-Köpenick, Tabelle 1, p. 2): 0.8-2.5 air changes
  an hour tilted and 9-15 wide open, both without cross-draught.
- The AnBUS study, quoted in Münzenberg, Weithaas and Thumulla, "Luftwechsel im
  Gebäudebestand": a bedroom at 1.2 an hour tilted (−3 °C, still) and 8.8 wide open (−5 °C,
  still). Neither source gives the room's or the window's size.
- TU Dresden's report for the BBR (p. 8): a tilted window gives about 10% of the air change of
  the same window fully open.
- Maas's dissertation (Kassel 1995, Bild 6.3, p. 46): about 125 m³/h through a tilted window
  1.33 m tall for a 14 cm tilt, a 20 K difference and wind under 0.5 m/s; his 8 and 10 cm
  curves give about 85 and 100 m³/h.
- EN 16798-7's single-sided formula with its tilt-angle factor (as given in Jiang et al. 2025,
  Eq. 9): about 75 m³/h for this window tilted 140 mm at a 20 K difference, 2.2 an hour in this
  room; wide open, about 626 m³/h, 18.6 an hour.

Against them:

- **Tilted,** 1.93 an hour, 65 m³/h: inside Berlin's 0.8-2.5, 1.6 times AnBUS's 1.2, 87% of
  EN 16798-7's 75 m³/h, and below Maas's 85-100 m³/h for 8-10 cm through a window 1.33 m tall.
  The first build's 5.5 an hour was more than twice the top of Berlin's range; the difference
  was the sash.
- **Wide open,** 19.8 an hour on average and 17.4 at 300 s (583 m³/h): at the top of UBA's
  10-20, 6% above EN 16798-7's 18.6 on the average and 7% below it at 300 s, above Berlin's
  9-15, and 2.2 times AnBUS's 8.8.
- **The ratio:** the tilted window takes in 9.8% of what the open one does, TU Dresden's 10%.
  AnBUS's open window takes in 7.3 times its tilted one, Berlin's 3.6-19 times, and this case's
  10.2 times.

**Why the model sits above AnBUS.** Neither run is out of line with UBA, Berlin or the
standard, but both are above AnBUS's one bedroom. None of the following is a wrong input that a
sourced value would correct, so the case was not re-solved:

- **The first five minutes.** The room starts at 20 °C, so the buoyancy driving the exchange is
  at its largest. A measurement over a whole airing averages a falling temperature difference.
- **A stratified room.** The cold air pools on the floor and pushes the room's own air out at
  the top, which replaces air faster than mixing at the same flow would.
- **Warm surfaces.** The floor, ceiling and walls are held at 20 °C, as masonry nearly is over
  five minutes, so they keep reheating the air and hold the buoyancy up.
- **An empty room.** No furniture or curtain slows the cold layer on the floor.
- **Unknown sizes.** AnBUS's room, window and tilt are not given; a smaller window or a
  narrower tilt would account for the difference.

## What the clip shows, and what it does not

**It shows** the mid-plane through the window, wide open above and tilted below, from the
moment the window opens to 300 s, 15× fast, coloured by the air's temperature on one scale,
with parcels of air carried by the solved flow in the plane. The wall, the radiator and, on
tilt, the sash's section are drawn over it. Each panel has one number, the share of the room's
own air replaced, in whole percent: it ends at 91% wide open and 15% on tilt.

**It does not show** the cold air coming in through the tilted window's side gaps, which lie
off the mid-plane, though at 300 s the room's cells on the mid-plane average 18.6 °C on tilt,
as on the plane beside the window and as the room's mass average. It shows no flow rates, heat loss or costs. On screen the shares differ by
a factor of six, not the ten of the inflows, because the open room's share flattens as it nears
all of its air.

## What it cannot

- **A still day at 0 °C.** No wind, which on a real window adds to the exchange, so this is the
  low case for a single window, and one temperature difference, 20 K at the start.
- **A stratified room makes the 91% read high** against a well-mixed decay. Its 91% in five
  minutes is 29.3 air changes an hour as a decay, while the inflow is 19.8 an hour. A tracer
  measurement in a fan-mixed room would find less replaced for the same flow. The inflow is
  the figure to compare with measured air-change rates.
- **Warm surfaces and an empty room.** The floor, ceiling and walls are held at 20 °C and the
  room has no furniture, door gaps or other leaks; the radiator stays at 60 W, about a tenth of
  a real one's, and does not turn up as the room cools.
- **The first five minutes,** from a room uniformly at 20 °C. The exchange slows as the room
  cools, so a longer airing would average a smaller rate.
- **One sash for each.** A 140 mm tilt, at the top of the usual range, with the rebate
  clearance shut and a top gap 11% short on the mesh; one turn sash at 90°.
- **URANS on one mesh,** k-omega SST with wall functions, no mesh or time-step study, one
  realization of each run.
- **Not about heating costs.** The case does not compute the heat lost through the window, so
  it does not test the advice's point about costs, only the air.

## A US double-hung window

The US window is the double-hung: two sashes in two tracks, the upper one outside and the lower
one inside, each sliding up or down. On a cold day it is opened a crack, usually at the top, and
a common tip is to open it a little at the top and a little at the bottom instead. These two runs
put such a window in this room's wall and compare the two ways of opening the same 10 cm.

**It is a still morning: no wind.** The flow is driven by buoyancy alone, the room's air at
20 °C against the outdoor air at 0 °C. Wind, which on most days drives more air through a
window than buoyancy does, would change both numbers and could change their ratio.

### The window

| | value | from |
|---|---|---|
| frame | Andersen 400 Series Tilt-Wash TW3042, 956 × 1343 mm (3'-1 5/8" × 4'-4 7/8") | Andersen's table of sizes |
| clear opening | 0.86 m wide (the table's "window width − 1.852"" × 2", 862 mm) and 1.24 m tall, from a 0.95 m sill | the width Andersen's; the height the frame's 1343 mm less a 47 mm head and sill, ours, like the 47 mm jambs |
| sill | 0.95 m above the floor: the frame on this room's 0.90 m sill, plus the frame's sill | this room's |
| sashes | two, each 0.65 m tall and 40 mm deep, the upper in the outer track (x −0.08 to −0.04 m), the lower in the inner (x −0.04 to 0), at the wall's inside face; shut, they overlap 0.06 m at the meeting rails | the lower sash's height from the table's 557 mm of glass ("Lower Sash = lower sash height − 3.831"", 97 mm of rails); the upper taken as tall; the depth and the tracks ours |
| `doubleHungTop` | the upper sash lowered 10 cm: a slot 0.86 × 0.10 m above it, 0.086 m² | a 10 cm slit at the top, the winter crack |
| `doubleHungSplit` | the upper sash lowered 5 cm and the lower raised 5 cm: slots 0.86 × 0.05 m at the head and at the sill, 0.043 m² each, 1.19 m apart (centre to centre) | the US tip, the same open area |
| radiator, room, outside | as `open` and `tilted`: the 1.0 m radiator at 60 W under the window, the room's surfaces at 20 °C, still outdoor air at 0 °C | |

Both sashes are solid: their cells are taken out of the mesh with the wall's, as the tilted
sash's are. Their faces, the reveal and the wall's outer face are adiabatic. There is no insect
screen, no leakage past the weatherstrips and no detail of the meeting rails or the sash
frames.

**Why this pair.** On a still day a single opening swaps air by buoyancy alone, cold in through
its lower part and warm out through its upper, at Q = (C_d/3) W h √(g h ΔT/T) for an opening of
width W and height h (Linden 1999; BS 5925). Where the slot sits on the wall does not enter, so
the bottom sash raised 10 cm and the top sash lowered 10 cm would show two nearly equal numbers.
Two openings at different heights work as a stack instead, cold in at the bottom and warm out at
the top, at Q = C_d A* √(2 g Δz ΔT/T) with A* = a/√2 for two equal openings of area a (CIBSE
AM10; BS 5925): for these slots about five times as much as the single slot, through the same
open area. Keeping the open area the same makes the arrangement the only difference.

### The double-hung runs' model

`open` and `tilted`'s model, with four differences outside the solver's physics and numerics:

- **The outdoor boundary is barometric.** The open faces hold p0 = 1e5 exp(−g y/(R T)), the
  still 0 °C air's own pressure at each face's height, and every cell starts at that pressure,
  with its own density in p_rgh (`barometric_p.py`, written by `make_case.py`), so the solve
  starts at rest. `open` and `tilted` hold p0 = 1e5/(1 + g y/(R T)) on the faces and start from
  a uniform p_rgh. The two forms differ by about 0.01 Pa at the top of the box, but the second
  is not rest for a compressible gas: in another case's still outdoor box, which nothing drove,
  it moved the air at up to 0.06 m/s ([`dryIceCauldron`](../dryIceCauldron), "How the case got
  here"). For `open` it makes no
  difference that matters here: [`roofWindowAiring`](../roofWindowAiring)'s `wall` run is
  `open` rebuilt with the barometric boundary on a finer mesh across the window, and it takes
  in the same 0.235 kg/s on average over the five minutes and replaces 92.0% of the room's air
  at 300 s against `open`'s 91.3%.
- **The mesh** is `open`'s box with a uniform 10 mm band from 0.90 to 2.24 m up, indoors and
  out, for the slots (a 5 cm slot is five cells tall), and `open`'s cells across the room's
  width split so that a cell face falls on the window's edges at ±0.43 m: 1,422,720 cells in
  the box, 1,079,176 kept, `checkMesh` OK, one region. Both runs have the same mesh but for
  the sashes' cells.
- **The monitors** add the gross flow each way through the two slots, in the sashes' tracks
  (`slotHead` at x = −0.06 m, `slotSill` at x = −0.02 m), and through the frame's plane x = 0
  below and above 1.30 m, and a per-step budget of the room's own air through the frame's plane
  (`fluxBudget`, s's own face flux as the scalar transport discretises it). The frame's plane
  lies in front of the sashes, and the room's air turning in the recess there crosses it twice,
  so the air coming in is read at the slots.
- **The planes** are written every 1.25 s, the mid-plane at z = 0 and the floor plane, and the
  full fields every 60 s.

### Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only
  doubleHungTop` and `doubleHungSplit` wrote the solved runs' meshes (points, faces, owner,
  neighbour, boundary, cell, face and point zones) and every initial field, the barometric p
  and p_rgh included, byte for byte, 1,079,176 cells each. Their `0.orig`, `constant/`,
  `fvSchemes`, `fvSolution` and `setFieldsDict` have the solved runs' values and differ only in
  comments and layout. Their monitors were tidied: the solved runs also logged the cell that set
  the time step and the probes, and named the slots' inflow monitors `slotHeadArea` and
  `slotSillArea`. A few steps of each new setup gave the solved runs' first steps' monitors to
  four or five figures.
- **Three legs, two decompositions.** Each run was solved 0-30 s on 8 ranks (the two side by
  side), then 30-35 s and 35-300 s on 16 ranks, each leg from the last one's field write;
  `extract_results.py` joins the monitors' pieces. A re-solve will not match the committed
  histories to the last digit.
- **The scalar's budget** closes to 0.50% (top) and 0.11% (split) of what has left the room at
  300 s, and within 0.9% and 0.4% at every write from 10 s on.
- **Still air outside.** At 1.25 s the outdoor air in the outer half of the box in front of the
  window (x < −0.99 m) on the mid-plane moved at a median 8.9e-6 m/s in `doubleHungTop`. In
  `doubleHungSplit` the same air moved at 2.7e-3 m/s, and at 4.4e-4 m/s at the box's sides on
  the floor plane: its two slots 1.2 m apart draw air in at the sill and push it out at the
  head, a source and a sink, and the box moves with them. The two runs share the mesh, boundary
  and fields, so the first is the second's control.

### Results

From `results/summary_doubleHung.txt` and `results/<run>/history.csv`. The air in is the gross
flow into the room through the slots, as volume of 0 °C air (1.275 kg/m³).

| | `doubleHungTop` | `doubleHungSplit` |
|---|---:|---:|
| **share of the room's own air replaced, at 60 / 120 / 300 s** | 0.72 / 1.41 / **3.35%** | 5.04 / 10.07 / **25.14%** |
| **air in, mean over 0-300 s** | **13.5 m³/h** (0.40 room volumes an hour) | **97.2 m³/h** (2.89 an hour) |
| air in at 300 s | 12.3 m³/h | 95.4 m³/h |
| the room's mass-average temperature at 300 s | 19.8 °C | 17.6 °C |
| over the last minute | 0.03 K cooler, 0.6 points more replaced | 0.31 K cooler, 5.0 points more replaced |

**With the same open area, the split window takes in 7.2 times as much air** over the five
minutes, and replaces 7.5 times as much of the room's air. With one slot at the head, the cold
air comes in along the slot's lower edge and the warm air goes out along its upper edge, the
two streams sharing 10 cm of height. Split, the sill slot only takes air in and the head slot
only lets it out (the mean flows the other way are below 1e-5 kg/s): cold air pours in at the
sill, falls past the radiator to the floor and spreads across it, and the room's warm air
leaves at the head. The pressure that drives it builds over the 1.2 m between the slots.

**Against the orifice formulas**, with C_d 0.61 and each run's mean room temperature over the
five minutes: the single slot's formula gives 16.5 m³/h and the run 82% of it, an effective
C_d of 0.50; the two slots' formula gives 82.8 m³/h and the run 117% of it, an effective C_d of
0.72. Both are in the usual range for small openings. The formulas put the split at 5.0 times
the single slot, the runs at 7.2: a likely reason, not tested here, is that the single slot's
two streams shear against each other in its 10 cm, where the split gives each stream a slot of
its own.

**Against the turn-tilt window in the same room**: wide open it replaces 91.3% in five minutes,
on tilt 15.2% and takes in 65 m³/h. The slit at the top replaces 22% of the tilted window's
share and takes in 21% of its air. The split replaces 1.66 times the tilted window's share and
takes in 1.50 times its air, but it is nowhere near a window opened wide.

### What the clip shows, and what it does not

**It shows** the mid-plane through the window, the top sash lowered above and the split below,
from the moment the window opens to 300 s, 15× fast, coloured by the air's temperature, with
parcels of air carried by the solved flow in the plane, the wall and both sashes drawn over it.
Each panel has one number, the share of the room's own air replaced, in whole percent: it ends
at 3% and 25%. It shows no flow rates.

### What these two runs cannot

- **A still day at 0 °C.** No wind, one temperature difference, 20 K at the start.
- **One slot size, one split.** 10 cm at the top, or 5 cm at each end; wider openings, the
  bottom sash raised alone, and an insect screen over the lower half, as US windows usually
  have, are not run.
- **A drawn window.** The upper sash's height is taken equal to the lower's, the head and sill
  members as 47 mm, the sashes as plain 40 mm slabs; no weatherstrips, no leakage, no meeting
  rail detail.
- **Warm surfaces, an empty room, a 60 W radiator**, as `open` and `tilted`.
- **The first five minutes.** Neither room has settled at 300 s: the split room still cools
  0.31 K a minute.
- **URANS on one mesh,** k-omega SST with wall functions, no mesh or time-step study.

## Sources

- Umweltbundesamt, "Wie lüfte ich richtig?":
  https://www.umweltbundesamt.de/themen/gesundheit/umwelteinfluesse-auf-den-menschen/schimmel/wie-luefte-ich-richtig-tipps-tricks-zur
- Umweltbundesamt, *Leitfaden für die Innenraumhygiene in Schulgebäuden* (2008), pp. 25-26:
  https://www.umweltbundesamt.de/system/files/medien/515/dokumente/3689.pdf
- Umweltbundesamt, *Anforderungen an Lüftungskonzeptionen in Gebäuden* (2017), p. 18:
  https://www.umweltbundesamt.de/system/files/medien/1410/publikationen/uba_empfehlungspapier_lueftung_unterrichtsgebaeude_final_bf.pdf
- Innenraumlufthygiene-Kommission, statement on airing (2020), p. 4:
  https://www.umweltbundesamt.de/system/files/medien/2546/dokumente/irk_stellungnahme_lueften_sars-cov-2_0.pdf
- dena, *Richtig heizen und lüften* (2022), p. 2:
  https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2022/FS_Richtig_heizen_und_lueften.pdf
- Energiewechsel, *Richtig Energie einsparen: Beim Heizen, Kühlen und Lüften* (2022), p. 1:
  https://www.energiewechsel.de/KAENEF/Redaktion/DE/Downloads/Dialog-Energiewechsel/energiewechsel_energiespartipps-heizen-kuehlen.pdf
- Bezirksamt Treptow-Köpenick von Berlin, sheet on airing, Tabelle 1, p. 2:
  https://www.berlin.de/ba-treptow-koepenick/_assets/aemter-und-se/buergerdienste/pdf/merkblatt___ber_das_l__ftungsverhalten_und_l__ftungsanlagen.pdf
- Münzenberg, Weithaas and Thumulla, "Luftwechsel im Gebäudebestand" (Verband Baubiologie),
  quoting AnBUS:
  https://baubiologie.net/media/vdb_luftwechsel_fensterlueftung_und_die_notwendigkeit_von_lueftungskonzepten.pdf
- TU Dresden, report for the BBR, p. 8: https://www.irbnet.de/daten/kbf/kbf_d_F_2425.pdf
- Maas, dissertation, Kassel 1995, Bild 6.3, p. 46:
  https://www.uni-kassel.de/fb6/bpy/de/forschung/abgeschlprojekte/pdfs/maas_diss.pdf
- Maas, Schmidt and Hauser, wksb 42/98, Tabelle 2:
  https://www.uni-kassel.de/fb6/bpy/de/forschung/abgeschlprojekte/dfg_schmidt/wksb42_98-2.pdf
- EN 16798-7, as given in Jiang et al. (2025), Eq. 9:
  https://www.sciencedirect.com/science/article/pii/S0360132325007334
- Roto, care and maintenance guide, p. 6:
  https://www.distner.de/file/686_Roto_Pflege_und_Wartungsanleitung.pdf
- Winkhaus, activPilot scissor SC2.20-9.LS, technical data sheet:
  https://media.meesenburg.com/image/upload/v1683872240/document/0000098604/technical_data_sheet_0000098604_5062140_technisches_Datenblatt_5062140.pdf
- VEKA Softline 82 and aluplast Ideal 4000, sash profile depths.
- Andersen, *400 Series Product Guide* (2025-26), "Table of Sizes for Tilt-Wash Double-Hung
  Windows", as filed with a planning application in Haddonfield, NJ:
  https://cms5.revize.com/revize/boroughofhaddonfield/HPC/2025/HPC%202025-0223%20-%20334%20Kings%20Hwy%20E%20-%20Windows.pdf
- P. F. Linden, "The fluid mechanics of natural ventilation", Annual Review of Fluid Mechanics 31
  (1999); BS 5925 and CIBSE AM10, the single-opening and two-opening formulas.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy; `scripts/frame_check.py` also needs PyVista and Matplotlib.

    cd cases/windowAiring
    ./Allrun open                    # [nProcs], default 7
    ./Allrun tilted
    python3 scripts/extract_results.py runs results

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there: blockMesh, subsetMesh to the air (and, on tilt, without the sash's
cells), the outer walls and the sash as patches, the wide-open sash as a baffle, the zones,
the initial fields, the outside faces' hydrostatic pressure, checkMesh and decomposePar. It
then writes the t = 0 planes from the initial fields and solves 0-300 s, writing the planes
every 0.625 s and the fields every 25 s (the last two kept). `./Allrun --setup-only <run>`
stops before the t = 0 planes and the solve, in about 15 s. `./Allclean` removes the runs.

To check the sash on the mesh, write the cell and face centres and read them:

    (cd runs/tilted && postProcess -func writeCellCentres -time 0)
    python3 scripts/geometry_check.py runs/tilted > results/geometry_tilted.txt
    python3 scripts/frame_check.py results/frame_60s.png 60 runs/open runs/tilted

The runs took 11,855 s (`open`) and 9,549 s (`tilted`) of wall time on 7 ranks each, side by
side. Each writes about 0.7 GB of planes. `results/` holds the histories, every step's
monitors sampled at the plane writes, the summary, the sash on the mesh and one frame at 60 s;
no fields, meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine, and sent back once to
have the tilted window checked against the German sources and measured rates, which found the
two faults above; both runs were then solved again.

The double-hung runs:

    ./Allrun doubleHungTop           # [nProcs], default 16
    ./Allrun doubleHungSplit
    python3 scripts/extract_results.py runs results

They are written and meshed the same way, without a baffle, with the two sashes' cells taken
out with the wall's, and with each cell's and outdoor face's barometric pressure in place of the
faces' hydrostatic pressure. They write the planes every 1.25 s and the fields every 60 s (the
last one kept). Solved in legs of 0-30 s on 8 ranks, beside each other, then 30-35 s and
35-300 s on 16 ranks alone, they took 3,260 + 256 + 13,764 s (`doubleHungTop`) and
5,841 + 572 + 27,962 s (`doubleHungSplit`) of wall time; the split run's 5 cm slots, at about
1 m/s through 10 mm cells, set its smaller time step. `results/` holds their histories, every
step's monitors sampled at the plane writes, and `summary_doubleHung.txt`, which also reads
`open`'s and `tilted`'s histories for the comparison; no fields, meshes, planes or logs.
`extract_results.py` writes the double-hung results from `runs/doubleHungTop` and
`runs/doubleHungSplit` and the turn-tilt window's from `runs/open` and `runs/tilted`, for
whichever pair is there.

They were built by an agent on our own machine from this case's generator, and checked and
solved there.
