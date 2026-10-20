# Ice dams: an attic with its soffit vents open, or buried in insulation

Icicles and a ridge of ice along the eaves mean the snow on a roof is melting higher up, where
the attic warms the deck under it, and the water is freezing again at the cold edge. The usual
advice is a clear air path from vents in the soffits, up under the roof deck, to a vent at the
ridge, so that outdoor air keeps the deck cold. A **soffit vent** is the vent slot in the
underside of the roof's overhang, the board under the eaves, where outside air comes into the
attic. Blown-in insulation often buries those vents.

This case takes one house on one cold, still night with snow on the roof, the US Army Cold
Regions Research and Engineering Laboratory's (CRREL's) own design case for sizing attic
ventilation against ice dams, and solves a vertical section through it from one gable side to
the other: the heated room's ceiling, the insulation on it, the attic air, the overhangs and
the roof. The number it reports is **the share of the roof over the attic whose snow is melting
from below**, its base above 0 °C. One OpenFOAM case, two runs that differ only at the eaves:

    ./Allrun vented     # soffit vents open, a baffle keeping a 2 in airway over the insulation, 0-3600 s
    ./Allrun buried     # the insulation blown over the soffits up to the deck, 0-7200 s

**This is a 2-D section with no air leaking up from the rooms, and its solids hold no heat, so
its time is not the house's.** The number is what the attic's air does on one published design
night with the roof's layers as plain resistances. Read [What it cannot](#what-it-cannot)
before any number here.

## The night and the house

Every input that moves the answer is CRREL's (Tobiasson, Buska and Greatorex 2001), or comes
from the same group's 1998 paper; the rest are from other published guidance, each named.

| | value | from |
|---|---|---|
| the night | still air at 22 °F (−5.6 °C); "all ventilation is by stack effect", since "winds cannot be relied on" | CRREL's outside design temperature for sizing ventilation against icings at the eaves |
| the attic | 30 ft (9.14 m) wide under a 3-in-12 (14°) roof | CRREL's worked example |
| the ceiling | R25 (4.4 m²K/W) at full depth: 10 in (0.254 m) of loose-fill fibreglass at R2.5 an inch; where the roof leaves less room the insulation is thinner and its resistance falls in proportion | CRREL's worked example; "settled R-value per inch is from 2.2 to 2.7" (Building America Solution Center, loose-fill insulation) |
| the room below | 70 °F (21.1 °C), with a still-air film of 0.107 m²K/W on the ceiling | the usual US winter indoor design temperature; with it, an R30 ceiling under a 30 °F attic passes the 3.8 W per m² of roof CRREL quote from TenWolde and Rose (1999) on a 6-in-12 roof |
| soffit vents | a slot 15.2 mm wide along each eave: 7.3 in² per running foot (15.2 mm²/mm) | CRREL's Equation 1 for this house: 14.6 in²/ft of inlets in all, half along each eave |
| ridge vent | one slot 30.4 mm wide: 14.6 in² per running foot | "That same total value would also be needed for outlets along the ridge" |
| overhang | 12 in (0.305 m), the soffit vent in its middle | "A 12 in (305 mm) overhang is a good target" (Buska, Tobiasson and Greatorex 1998) |
| baffle (vented) | keeps the insulation 2 in (51 mm) below the deck, from the wall's outer face to where the insulation reaches its full 0.254 m, 0.813 m in | "a target height of 2 in. (51 mm)" (1998); "at least 2 inches of ventilation space above the insulation" (Building America Solution Center) |
| truss heel | the deck's underside 4 in (0.102 m) above the ceiling at the wall's outer face, rising to 1.245 m at the ridge | "Typical truss heel height is about 4"" (Structural Building Components Association) |
| snow | 9.5 in (0.24 m) at 210 kg/m³ and 6.1 m·K/W: 1.464 m²K/W | CRREL: "the base of the snow would begin to melt at the 22ºF (–5.6ºC) outside 'design' temperature when there are only 9.5 in. (0.24 m) of snow on the roof", the least snow on which they find melting can start that night |
| the roof's other layers | 7/16 in OSB at k = 0.13 W/m K (0.085 m²K/W), asphalt shingles (0.077) and a still-air film on the snow (0.107, heat flowing up): with the snow, 1.733 m²K/W from the deck's underside to the night | ASHRAE Handbook of Fundamentals |
| soffit and fascia | 19 mm boards (0.158 m²K/W) with the outdoor film | ours |

**buried** differs only at the eaves: the insulation has been blown over the soffits and fills
the overhangs and the eaves up to the deck, so the ridge vent is the only opening. The
insulation touches the deck for the 0.65 m nearest each wall (0.670 m along the slope), where
the deck is less than 0.254 m above the ceiling; there is no air there.

**When the snow melts from below.** The snow's base sits between the deck and the night air, at
T_out + (T_deck − T_out) × (1.464 + 0.107)/1.733. It is above 0 °C wherever the deck's
underside is above +0.58 °C.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's
own Allrun; `scripts/roof.py` holds every number in the table and the section's outline. x runs
across the house with the ridge at x = 0, y up from the ceiling (the insulation's underside).

- **A 2-D section,** one cell deep and 1 m thick, so every flux is per metre of house. The air
  region is the attic over the insulation, the overhangs and, as structured blocks of square
  cells, the soffit vents' and the ridge vent's slots. The ridge vent's slot rises from the apex
  to an opening at y = 1.30 m, 59 mm above the deck's underside, standing for the deck, the
  shingles and the vent's body. The soffit is level with the bottom of a 2×6 rafter tail at the
  fascia, y = −0.119 m.
- **The ceiling** is the insulation's upper surface, a wall passing heat from the 21.1 °C room
  through the film and the insulation's local depth, h = 1/(0.107 + 4.4 × depth/0.254) W/m²K,
  face by face (`setup_fields.py`). Under the baffle the depth is the deck's height less 51 mm,
  0.051 m at the wall.
- **The roof** is the deck's underside, a wall passing heat to the −5.6 °C night through
  1.733 m²K/W; over the overhangs too, which carry the same snow. The soffit and fascia boards
  pass heat to the night through 0.158 + 0.107 m²K/W. The wall's outer face in the overhang, and
  in buried the short face where the air wedge over the insulation ends, are adiabatic.
- **Where the buried insulation touches the deck** there is no air. The deck's temperature there
  is the one-dimensional path from the room through the insulation's local depth and up through
  the roof: the snow's base is at +6.05 °C at the wall and +0.94 °C where the air begins, above
  freezing all along it. That strip is 14.2% of the roof over the attic, and it melts in the
  buried run from the start, whatever the air does.
- **The solids carry no heat.** The insulation, the deck and the snow are resistances with no
  heat capacity, so the attic settles as fast as its air can warm. A real roof would take a day
  or more.
- **The openings** hold the still −5.6 °C outdoor air's barometric pressure at each face's
  height, p0 = 1e5 exp(−g y/(R T)), as `prghTotalPressure`; air coming in is at −5.6 °C. Each
  cell starts at the same formula's pressure, so the still air is at rest, as in
  [`dryIceCauldron`](../dryIceCauldron) and [`windowAiring`](../windowAiring).
- **The start:** the attic's air still and at the outdoor −5.6 °C, and the ceiling's heat
  starting to come through at t = 0.
- **Air and numerics** as [`radiatorUnderWindow`](../radiatorUnderWindow)'s curtain runs:
  `buoyantPimpleFoam` (OpenFOAM v2512), air a perfect gas with c_p 1005 J/kgK and μ 1.72e-5 Pa s
  (about −3 °C), k-omega SST with the buoyancy source on k (`buoyancyTurbSource`) and wall
  functions, Euler in time at Courant 1, PIMPLE with two outer and two pressure correctors,
  limitedLinear schemes. p_rgh is solved to 1e-7 with at most 100 iterations, as in
  `windowAiring` and `dryIceCauldron`: at 1e-8 the solves stalled near 5e-6 in this still, open
  domain and ran to their limit every step.
- **Mesh:** gmsh's, quad-dominant and recombined, one cell deep (`scripts/make_mesh.py`, gmsh
  4.15.2 from pip, at its mesh scale 1.5): 4.5 mm at the deck, the insulation and the boards,
  growing to 18 mm in the attic's middle, 6 mm in vented's overhangs and the airway under the
  baffle, and 3.75 mm cells in the vent slots, 4 across a soffit vent and 8 across the ridge.
  vented has 49,477 cells, all hexahedra; buried has 42,228, six of them prisms. `checkMesh`
  passes on both with one region (largest non-orthogonality 33° and 35°, skewness 0.97 and
  0.84).
- **Writes:** the section every 7.5 s (`postProcessing/clip`, the clip's planes), the deck's
  underside and the insulation's surface face by face at every write (`deckT`), the attic's
  mean air temperature and the mass flow through each opening every 20 steps, the heat through
  each thermal boundary every step.

## How the case got here

The case was built without a mesh study, sized from coarse smoke tests at mesh scale 2:

- **Still air stays still.** With the room set to the outdoor temperature, the largest speed
  anywhere was 0.0009 m/s at 1 s and 0.0006 m/s at 2 s, at the ridge slot's corner.
- **The vent slots.** Meshed as part of the unstructured domain, six sliver cells at the slots'
  corners held the time step to 0.0067 s. As structured blocks of square cells the same case ran
  at 0.029 s, the step then set by the ridge slot and the attic's plume.
- **The mesh scale.** From the coarse runs' cost, scale 1 (about 113,000 cells, 3 mm at the
  walls) would have taken about 13 h a run on four cores; scale 1.5 was chosen.

Both runs were solved 0-3600 s, the hour the clip shows. vented had settled long before the
hour was out. buried had not: its share was 31.5%, 32.9% and 34.1% over the last three
five-minute windows, and its attic was still warming at 3.7e-4 K/s. So buried was continued
from its 3600 s fields to 7200 s with nothing changed but `endTime`, and its number is taken
there, once settled. `./Allrun buried` here runs 0-7200 s in one go.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only vented`
  and `--setup-only buried` wrote the solved runs' meshes (points, faces, owner, neighbour,
  boundary, zones and sets) and every initial field, the face-by-face ceiling h, the openings'
  p0 and the cells' barometric p included, byte for byte, as well as `0.orig` and `constant/`:
  `checkMesh` OK at 49,477 and 42,228 cells. The dictionaries in `system/` have the solved
  values and differ only in comments. The decomposition on 4 ranks is scotch's and was not
  compared, and a re-solve will not match the committed histories to the last digit.
- **The geometry.** Every boundary node of each run's section at 3600 s lies on `roof.py`'s
  outline to within 0.001 mm, and the sections' areas equal the outlines' (4.1107 m² vented, 3.9265 m² buried).
- **The heat budgets close.** vented, 3300-3600 s, per metre of house: 50.99 W in through the
  ceiling, 9.69 W out through the deck, 0.001 W through the boards and 0.03 W going into the
  air's warming, so the air through the vents carries 41.27 W away. buried, 6900-7200 s:
  28.82 W in, 28.26 W out through the deck and 0.05 W stored, leaving 0.51 W for the ridge
  vent.
- **The vent path runs one way.** vented's soffits take in 12.14 g/s per metre of house and its
  ridge lets out 12.14 g/s, with nothing going the other way at either opening (3300-3600 s).
  buried's ridge vent exchanges 0.26 g/s each way.
- **The restart joined smoothly.** buried's share and attic air carry on across 3600 s without a
  step: 35.87% and +2.190 °C at 3600 s, 35.78% and +2.192 °C at 3607.5 s.
- **Both runs ended cleanly,** vented at 3600 s and buried at 7200 s.

## Results

`scripts/extract_results.py` on the two runs; `results/summary.txt` has every figure below.

| roof over the attic with its snow melting from below | at the end of the hour (3600 s) | settled (the number) |
|---|---:|---:|
| vented: soffit vents open | 0% | 0%, 3300-3600 s |
| buried: soffit vents buried by insulation | 36% (35.87%) | 44% (44.10%), 6900-7200 s |

**vented.** Cold air comes in at both soffits, runs up under the deck and leaves at the ridge.
The attic's air is within 0.1 K of its final −2.68 °C from about 520 s on. No part of the snow's
base over the attic is above freezing at any write: the warmest face of the deck's underside is
−2.25 °C over the last five minutes and −1.57 °C at any write, against the +0.58 °C needed.

**buried.** The ridge vent is the only opening and the attic keeps its heat. Its air warms
through the hour to +2.19 °C at 3600 s and settles at +2.54 °C, within 0.1 K of that from about
4970 s. From the first write the contact strips at both eaves are melting (14.3% of the roof
over the attic at 7.5 s); the melting spreads up both slopes, and then in patches further up.
The share over five-minute windows:

| window, s | 0-300 | 900-1200 | 1800-2100 | 2700-3000 | 3300-3600 | 4500-4800 | 6000-6300 | 6300-6600 | 6600-6900 | 6900-7200 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| share | 15.0% | 21.1% | 28.4% | 31.5% | 34.1% | 40.8% | 43.4% | 43.7% | 44.2% | 44.1% |

Over the last 20 minutes the share rose 0.8 points in the first ten and not at all in the last
ten, and the attic's air stored 0.05 W against 28.8 W coming through the ceiling, so the
6900-7200 s mean, 44.10%, is taken as settled: 44%. A straight line through the last 20 minutes'
writes still rises 0.55 points per ten minutes, so a longer run might add about a point.

**The two slopes differ.** buried's air turns over in one large slow eddy that settles
off-centre and warms the left slope most (the deck's underside is warmest near x = −1.4 m over
6900-7200 s), so the left slope melts more: 53.5% against 34.7%
over 6900-7200 s, 45.2% against 23.0% over 3300-3600 s. The number is over both slopes. A real
attic has trusses and gable ends that would break such an eddy up, so which side melts more
here means nothing.

## What the clip shows, and what it does not

**It shows** the whole section from gable side to gable side, vented above ("vents under the
eaves open") and buried below ("vents under the eaves buried by insulation"), from rest through
the first hour, 0-3600 s, at 180 times real time: 7.5 s of flow a frame at 24 frames a second,
20 s in all. The colour is the attic's air temperature from −6 to +6 °C, blue below freezing and
red above. The snow is drawn on the roof at its 0.24 m, and its base turns orange wherever the
solved deck puts it above 0 °C. Each panel labels its soffit vent, "soffit vent" with a short
line to the slot under the roof's edge; in the buried panel the line goes through the slot into
the insulation lying on it.

**The number on screen for the buried attic is its settled value, reached after the hour the
clip shows.** Each panel's number is fixed for the whole clip: 0% for vented, and 44% for
buried, the 6900-7200 s mean from the run continued to 7200 s. The clip's planes stop at
3600 s, when buried's share was 35.87%, so the orange along the buried roof in the clip's last
frame covers 36% of the roof over the attic, less than the 44% beside it. vented had settled
long before the hour was out and stays at 0% throughout.

**The moving marks** are parcels of air carried by the solved flow, on their own, slower clock:
each frame carries them 0.75 s through the flow of that moment, a tenth of the 7.5 s the colour
moves on. Carried for the full 7.5 s, the fastest air, 0.40 m/s in vented's ridge vent, would
jump 3 m between frames. They show where the air is going at each moment, not how far it gets.

**It does not show** melting or ice. The icicles are drawn, not simulated: the model has no
melting or refreezing. They grow in the buried panel with the melting so far and never appear in
the vented one. The snow is drawn; the model has it only as a resistance.

## What it cannot

- **Air leaking up from the rooms.** The ceiling here is airtight. Warm air escaping through
  light fittings, hatches and gaps in a real ceiling carries heat into the attic, and air
  sealing is the other half of the usual advice; TenWolde and Rose (1999) argued that sealing
  and insulation alone could prevent ice dams, and CRREL argued for venting against them.
- **A 2-D section.** No gable ends, no trusses across the airway, no air moving along the house.
  buried's single off-centre eddy is a product of that.
- **Solids with no heat capacity.** The model's time is not the house's: a real roof takes a day
  or more to settle, and the order in which the roof starts melting here is the attic's air
  warming, not the roof's.
- **Radiation and sun.** There is no radiation between the insulation and the deck inside the
  attic, no night-sky cooling of the snow and no sun.
- **No melt.** The snow is a fixed resistance at a fixed depth; it neither melts, thins nor
  refreezes, and meltwater never reaches the eaves.
- **The ridge vent is clear of snow.**
- **One design night.** Still air at 22 °F with CRREL's house, vents and least melting snow. A
  colder night, deeper snow or a wind would each move the numbers, and nothing here says what
  they would be on another night.
- **One mesh, unsteady RANS,** k-omega SST with wall functions, one realization of each run, no
  mesh or time-step study.

## Sources

- W. Tobiasson, J. Buska and A. Greatorex, "Guidelines for Ventilating Attics and Cathedral
  Ceilings to Avoid Icings at Their Eaves", Buildings VIII, ORNL, 2001:
  https://web.ornl.gov/sci/buildings/conf-archive/2001%20B8%20papers/017_Tobiasson.pdf
- J. Buska, W. Tobiasson and A. Greatorex, "Roof Ventilation to Prevent Problematic Icings at
  Eaves", ASHRAE Transactions 104(2), 1998; AIVC 11883:
  https://www.aivc.org/sites/default/files/airbase_11883.pdf
- Building America Solution Center (US DOE and PNNL), "Construct Roofs and Attics for Ice Dam
  Prevention": "Ice dams occur if snow is present on a roof and the roof deck under that snow
  reaches above freezing temperatures".
  https://basc.pnnl.gov/resource-guides/construct-roofs-and-attics-ice-dam-prevention
- Building America Solution Center, "Loose-Fill Insulation":
  https://basc.pnnl.gov/redcalc/tool/loose-fill-insulation
- Structural Building Components Association, "Truss Heel Heights and Energy Code
  Requirements".
- ASHRAE Handbook of Fundamentals: surface films and the resistance of asphalt shingles.
- A. TenWolde and W. Rose (1999), on ice dams and attic ventilation, as quoted by Tobiasson,
  Buska and Greatorex (2001).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, Python 3 with NumPy,
and gmsh for Python (`pip install gmsh==4.15.2`; set `PYTHON` to the interpreter that has it if
it is not `python3`). Another gmsh version will mesh the same outline but not to the same cells.

    cd cases/iceDamRoofVents
    ./Allrun vented                  # [nProcs], default 4
    ./Allrun buried
    python3 scripts/extract_results.py runs results

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there: gmsh (`make_mesh.py`), gmshToFoam, changeDictionary for the patch types,
checkMesh, the initial fields with the ceiling's h face by face and the barometric pressure in
the cells and on the openings (`setup_fields.py`), and decomposePar. It then solves, vented
0-3600 s and buried 0-7200 s, writing the section every 7.5 s and keeping the last two full
fields. `./Allrun --setup-only <run>` stops before the solve, in under a minute.
`./Allclean` removes the runs.

The solved runs took 35,217 s (vented) and 11,270 s (buried, 0-3600 s) of wall time on 4 ranks
each, side by side on a machine shared with other solves, and 10,730 s for buried's
continuation to 7200 s. The gzipped sections take about 0.8 GB for vented and 1.4 GB for
buried. `results/` holds each run's history at every write (the share over both slopes and each
slope, the deck's warmest face, the attic's air, the heat through each boundary and the flow at
each opening), the snow base along the roof over the number's window, and the summary; no
fields, meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine, which found buried
unsettled at the end of the hour; it was continued to 7200 s before the clip was made.
