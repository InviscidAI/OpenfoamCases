# A ceiling fan in winter: down, up, or off

"Reverse your ceiling fan in winter" is advice most people have heard: blowing upward, the
fan is supposed to push warm air across the ceiling and down the walls without blowing on
anyone. This case puts one room, one heater and one fan through three configurations from
the moment everything is switched on, and shows where the heater's heat goes.

One OpenFOAM case, one `config.sh`:

    ./Allrun off medium      # heater on, fan off            (the published clip)
    ./Allrun down medium     # heater on, fan blowing down   (the published clip)
    ./Allrun up medium       # heater on, fan reversed       (the published clip)
    ./Allrun down low        # and up low: supported, not run for the clip

## The room, from a measurement

The dimensions come from the one controlled test of fan direction in a heated room we
could find: H. W. Samuelson, *Comparing Modes of Operation for Residential Ceiling Fans to
Achieve Thermal Destratification*, Harvard GSD, 2015
([Harvard DASH](http://nrs.harvard.edu/urn-3:HUL.InstRepos:29312101)). The study was
funded by a fan maker; the numbers used here are its ordinary paddle fan's.

| | Samuelson | this case |
|---|---|---|
| room | 20 x 20 ft square (6.10 m), 10 ft ceiling (3.05 m) | round, radius 3.441 m (the same 37.2 m2 floor), 3.05 m ceiling |
| fan | 60 in (1.52 m) paddle fan, centred, lowest blade 2.67 m up | 1.52 m actuator disk on the axis, z 2.60-2.74 m |
| heater | 1300 W portable heater with a blower | 1300 W ring against the wall, 0.25 m deep, 0.50 m tall |
| start | 40 min fan off to stratify, then fan on | uniform 20 C at rest; heater and fan on together at t = 0 |
| walls | uninsulated plywood inside a heated hall | heat loss to a 20 C hall, see below |

**Why round.** The fan sits on the room's axis, so the flow it drives is nearly
axisymmetric, and an axisymmetric model can be solved on a 5-degree wedge one cell thick:
11,424 cells, at 2 cm where it matters. The same resolution in 3-D would be millions of
cells. A round room of the same floor area loses the square room's corners.

**Why a ring heater.** An axisymmetric room cannot hold a portable heater standing in one
place: anything off the axis becomes a ring. The ring against the wall stands in for a
baseboard heater or a radiator. It is not Samuelson's heater, and where it sits matters
to the result (see the limits).

## The fan

Samuelson reports power, not airflow. DOE's 2023 proposed ceiling fan standards (88 FR
40932, 22 June 2023, Table IV.2) give an example AC-motor fan at 4,500 CFM on 58.7 W (high)
and 1,200 CFM on 12.0 W (low). Samuelson's paddle fan drew 11.5 W on low and 30.1 W on
medium, and the fan laws (flow ~ rpm, power ~ rpm^3) put medium near
4,500 x (30.1 / 58.7)^(1/3) = **3,600 CFM, 1.70 m3/s**. That is a derivation, not a
measurement.

The fan is an annulus of cells from r = 0.15 m (an unforced motor hub) to 0.76 m, 0.14 m
thick. Two `meanVelocityForce` controllers hold its mean axial velocity at 0.975 m/s
(1.70 m3/s over the annulus) and its mean swirl at half that, 0.487 m/s. **The swirl ratio,
0.5, is an estimate**; we found no measured value for a paddle fan. Reversed flips both
components, since a reversed fan turns the other way. The flat paddle is taken to move the
same air in both directions. The fan plane carried 1.65 m3/s down and 1.60 up at the end,
a few per cent under the target because the controller fixes a zone mean, not a plane flux.

## Heat in and heat out

- **In:** 1300 W in the ring, as a volumetric source. The wedge carries 5/360 of it.
- **Out:** the floor, ceiling and outer wall each lose heat to a 20 C hall through a mixed
  boundary condition sized for **h = 3 W/m2/K**, an estimate for thin uninsulated plywood
  with its air films. Samuelson gives no wall data.

Measured from the solved fields, as the room's stored heat against what went in:

| at 180 s | room-average rise | heat kept | wall loss at the end |
|---|---:|---:|---:|
| fan off | 1.40 K | 82% | about 370 W |
| blowing down | 1.22 K | 71% | about 570 W |
| reversed | 1.32 K | 77% | about 430 W |

About 420 W per kelvin leaves through 140 m2 of surface, so this room would settle about
3 K above the hall with a time constant of about 5.5 minutes; at 180 s it is still warming.
The fan-driven rooms lose more because the fan drags warm air along the surfaces.

## The model

- `buoyantBoussinesqPimpleFoam`, realizable k-epsilon URANS, wall functions, bounded
  advection, Courant number at most 0.9, one outer and two pressure corrections.
- **The wedge.** 5 degrees, one cell thick, cells collapsed onto the axis (no inner
  radius). Velocity on the axis: radial and tangential components below 1e-15 m/s.
- **Mesh.** blockMesh, piecewise uniform, `checkMesh -allGeometry -allTopology` OK, zero
  non-orthogonality, skewness at most 0.33:

  | r | spacing | | z | spacing |
  |---|---:|---|---|---:|
  | 0-0.76 m (fan) | 20 mm | | 0-0.50 m (floor, heater) | 20 mm |
  | 0.76-3.19 m | 40 mm | | 0.50-2.54 m | 40 mm |
  | 3.19-3.44 m (heater, wall) | 19 mm | | 2.54-2.80 m (fan) | 20 mm |
  | | | | 2.80-3.05 m (ceiling) | 19 mm |

- **Output.** The wedge's r-z face, axis to wall, all three velocity components and
  temperature, 481 times over 180 s (every 0.375 s), gzipped. The window was chosen from a
  600 s fan-off screening run, before the production runs.

### Fictitious forces, checked

With swirl, the radial momentum equation carries w^2/r and the swirl equation -u w/r. On
an OpenFOAM wedge the equations are solved in Cartesian components on a thin 3-D slice and
the wedge patches rotate vectors, so both terms come from the geometry. **Nothing is added
by hand, and there is no rotating frame**; either would count them twice.
`verification/swirl/` is the check: solid-body rotation at 1 rad/s on a wedge, no
sources, whose pressure should settle to p(r) - p(0) = Omega^2 r^2 / 2. It does, to
**0.06%** RMS over the range (`results.json`, `pressure_balance.png`).

## Results at 180 s

Temperatures averaged over the floor area (weighted by radius) at Samuelson's heights;
draft is the share of that area where the air moves at 0.15 m/s or more (ASHRAE 55's
still-air limit, which Samuelson used).

| | 0.10 m | 1.09 m | 1.70 m | 2.75 m | top minus bottom | draft at 0.10 / 1.09 / 1.70 m |
|---|---:|---:|---:|---:|---:|---:|
| fan off | 21.46 C | 21.43 C | 21.44 C | 21.54 C | +0.08 K | 49 / 78 / 66% |
| blowing down | 21.50 C | 21.18 C | 20.96 C | 21.39 C | -0.11 K | 97 / 100 / 100% |
| reversed | 23.06 C | 20.78 C | 20.63 C | 20.72 C | -2.34 K | 100 / 98 / 100% |

Histories are in `results/*/history.csv` and `results/four_height_histories.png`.

**Blowing down** mixes the heater's output through the whole room: the jet goes down the
middle, out across the floor, and up the walls past the heater, and the room warms evenly.

**Reversed** sends the fan's air across the ceiling and down the walls, where it lands on
the heater and carries its warm air inward along the floor. The feet end up warmest, 1.5 K
above either other room, and the air at head height coolest. That is a thermal inversion
held in place by the circulation, and it depends on the heater being where the reversed
air comes down.

**Fan off** never settles into a calm warm layer. The heater's plume leaves the wall in
rolls; the warm air running inward across the ceiling converges on the axis, collides, and
drives down the middle of the room. The warm-over-cool difference peaks at +0.73 K at 131 s
and reverses more than once. That convergence is what a round room does to a ring of warm
air, and a real room with one heater would not focus it onto a line. **The fan-off room is
the least trustworthy of the three.**

### Against Samuelson

Absolute temperatures do not compare: the start, the heater and its position all differ.
The ordering does, partly. At medium speed he found blowing down left less stratification
than reversed (0.11 K against 1.17 K floor to ceiling), and so does this case, but here
the reversed room's spread is an inversion, warm at the floor, where his was warm at the
ceiling. He found fan off the most stratified; here it is the least, for the reason above.
Draft: his medium runs put 42-53% of sensors at or above 0.15 m/s; this case puts
97-100% of the floor area there. The model overstates the draft.

## What the clip shows, and what it does not

**It shows** the full cross-section through the room, the solved half and its mirror image,
coloured by temperature on one fixed scale for all three rooms, with streamlines of the
in-plane air. The fan and the heater are drawn over the cells where the case applies them.

**It does not show** swirl, which runs out of the section, or any number. The mirror is
exact by construction, not a second solution.

## Limits, which are the part worth reading

- **The heater's position decides the reversed result.** A heater standing in the room, as
  in Samuelson's test, would meet the reversed fan's air somewhere else.
- **Round, axisymmetric.** No corners, no furniture, no off-axis heater, and a fan-off
  room whose plume focuses on the axis in a way a real room's does not.
- **Estimated inputs.** The medium airflow is derived from DOE's example fan and the fan
  laws; the swirl ratio and the wall conductance are estimates.
- **An actuator, not blades.** No tip vortices, hub wake or blade pitch; the paddle is
  taken to move the same air both ways.
- **URANS on one mesh.** No mesh or time-step study. The draft areas are well above
  Samuelson's and should not be read as comfort predictions.
- **Three minutes from a uniform start.** Samuelson stratified for 40 minutes and then ran
  the fan for 40 more. This case shows the first 180 s of heating, not a settled room.
- **The 0.10 m statistics plane passes through the heater**, which lifts the floor-level
  averages, most of all in the reversed room.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy, pandas, Matplotlib and PyVista.

    cd cases/ceilingFanWinter
    ./Allrun up medium

`Allrun` writes the case into `runs/<direction>_<speed>/` (`makeCase.py`, from
`config.sh`), meshes it, checks the mesh, samples t = 0, solves to 180 s on 4 MPI ranks,
and writes `results/` in the run with `postprocess.py`. The three medium runs took 21
(off), 41 (up) and 57 (down) minutes running side by side. `python3 axis_regularity.py`
plots the velocity approaching the axis for each run. `verification/swirl/Allrun` runs the
fictitious-force check. `./Allclean` removes the runs.

The case was set up by an agent and checked by us over a build and three corrections. It
was first built in 3-D as a square room with a prescribed 5 K stratification and a heater
in a corner; the heater first sat on the plane we were drawing, and the question changed
from "what does the fan do to an existing warm layer" to "where does the heater's heat go
from switch-on", which the axisymmetric case answers far more cheaply. The 3-D runs were
deleted. The ring heater
was enlarged from 0.16 x 0.20 m to 0.25 x 0.50 m because the smaller one made a hot spot
that dominated the picture.
