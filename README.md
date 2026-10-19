# OpenFOAM cases

Runnable OpenFOAM cases from [Inviscid AI](https://inviscid.ai). Each directory under
`cases/` is one self-contained case with the setup that produced its results, so a claim
made anywhere else can be checked here.

| case | what it is |
|---|---|
| [`cases/roomFanInOut2D`](cases/roomFanInOut2D) | A fan in a room, blowing in versus blowing out. Two runs differing in one setting. Backs a published clip. |
| [`cases/motorcycleWindscreen`](cases/motorcycleWindscreen) | A windscreen at three heights, and how much the air on the rider's helmet fluctuates. Three runs differing in one thing. Backs a published clip, and its limits say why it names no winner. |
| [`cases/airFryerVsOven`](cases/airFryerVsOven) | An air fryer and a convection oven with the same fan and the same food, and where the air goes. Two runs differing in the appliance. Backs a published clip, and its limits say why it names no winner. |
| [`cases/portableAcHoses`](cases/portableAcHoses) | A portable air conditioner with one hose and with two, in the same room. One case, run two ways. Backs a published clip; the README says what the numbers can and cannot carry. |
| [`cases/sphericalCow`](cases/sphericalCow) | The physics joke taken literally: a cow (Keenan Crane's public-domain Spot) and a sphere of the same volume in the same wind. Floating runs under SST-SAS back a published clip; grounded SST runs and a failed sphere drag check are kept, and the README says what that leaves standing. |
| [`cases/ceilingFanWinter`](cases/ceilingFanWinter) | A ceiling fan in a heated room, off, blowing down and reversed, from switch-on. An axisymmetric wedge with swirl and a check that the wedge carries the swirl's fictitious forces unaided. Backs a published clip; the README says why the fan-off room is the weakest of the three. |
| [`cases/ceilingFanHighCeiling`](cases/ceilingFanHighCeiling) | The reversed fan of `ceilingFanWinter` under a ceiling twice as high, the mesh extended at the same resolution and the heater doubled so each cubic metre gets the same heat; the 1300 W runs are kept. Backs a published clip; the README says why the result belongs to equal heat per volume and not to moving the same heater into a taller room. |
| [`cases/marathonDrafting`](cases/marathonDrafting) | A runner at women's world-record marathon pace alone, behind one pacer and behind two side by side, as static CC0 figures over a moving ground under SST-SAS. Backs a published clip; the README says why it finds less shelter than the literature. |
| [`cases/pcCaseAirflow`](cases/pcCaseAirflow) | A generic mid-tower PC with its case fans in three layouts (more in than out, more out than in, three and three), the card and CPU cooler as fixed-flow heat sources, from switch-on under SST-SAS. Backs a published clip; the README says why the pressure's sign barely matters here and what does. A fourth layout is a viewer's build from that clip's comments, with two bottom intakes, no front fans and the CPU cooler turned round, on its own mesh. Backs a published clip; the README says why its cooler's near-room air is the optimistic end. A fifth is another viewer's build, two low front intakes with rear and rear top exhausts, on the shared mesh. Backs a published clip; the README says why it gains less than the fourth and cannot be told apart from three and three. The first two layouts again with the room's dust carried on the flow as a passive scalar, the front and top behind filter mesh that catches half of it and the slot covers unfiltered. Backs a published clip; the README says why it shows where dusty air goes and not where dust settles, and why positive pressure does not stop the slot leak. Two more layouts are a third viewer's build, the CPU on an all-in-one liquid cooler with a 360 mm radiator on three top exhausts, three front intakes and the rear exhaust, with and without two bottom intakes, on a mesh of their own. Backs a published clip; the README says why most of the air the bottom intakes add leaves the case where the clip's section cannot show it. The last two answer a comment under the first clip, the same liquid cooler in the PC with three and three's fans and its radiator on the three front intakes or on the two top exhausts, the radiator as the heat it adds to its fans' air, on a mesh of their own. Backs a clip; the README says why each position wins on one part, and why the two runs are two realizations of one flow rather than the same air moving. |
| [`cases/radiatorUnderWindow`](cases/radiatorUnderWindow) | A radiator under a cold window against the same radiator on the opposite wall, a 2-D buoyant room section from switch-on to an hour, the radiator's output set to the section's own heat loss. Backs a published clip; the README says why the output is a tenth of a real radiator's, and that its reason for the floor draught opposite running at half the correlation's beyond 1 m is untested. Two more runs put a floor-length curtain over the radiator under the window, hanging in front of it and tucked in at the sill, as an impermeable sheet that conducts heat, over the first 300 s from switch-on. Backs a clip; the README says why, in a 2-D section with no air round the curtain's ends, no radiation and a 60 W/m plume, the shares of heat reaching the room compare the two shapes and do not measure a real curtain, and why the one laboratory measurement, made with no window, does not check them. A third curtain run hangs the same curtain but ends it at the sill, 0.14 m above the radiator, as German advice says to. Backs a clip; the README says why it gains little over the floor-length curtain, the gap behind it becoming a channel for cold air off the glass, and why the curtain holds the heat back by being airtight, not by insulating. |
| [`cases/spinningCat`](cases/spinningCat) | The spinning cat of the "OIIA" meme on a floor in still air, from rest, its zone of the mesh turning with it under SST-SAS; the cat is a remeshed CC BY 4.0 model by Zhuier, credited in the case. Backs a published clip; the README says how the run was restarted and its Courant limit raised, and that the flow has not settled by 10 s. |
| [`cases/cyclistBehindLorry`](cases/cyclistBehindLorry) | A road cyclist at 90 km/h alone, 1.5 m behind a lorry's rear doors and 10 m back, a static MakeHuman CC0 rider on a simplified bike behind a generic box lorry built from published dimensions, from rest under SST-SAS. Backs a published clip; the README says why the close rider is sheltered rather than pulled, and why, on a coarse mesh, the shares of riding alone carry the result and the newtons do not. A fourth run is the same lorry alone in its own frame at 80 km/h, overtaking a rider at 20 km/h with a 1.5 m gap; the rider is a probe read off the solve along his path, and the air's force on him a quasi-steady estimate from published drag areas. Backs a clip; the README says why the rider is not in the solve, why the air pushes him once and pulls him once rather than pulling twice, and why the force is an estimate to read against a 17 N flipping limit, not a measurement. Three more runs put a generic car built from published dimensions behind the same lorry at 90 km/h, alone, tailgating 12.5 m behind its doors and at the two-second gap of 50 m, its drag share turned into fuel saved with the National Research Council's half of a car's fuel going on drag at motorway speed; the lorry's emergency stop that follows is kinematics from sourced reaction and braking figures, not CFD. Backs a clip; the README says why the car's absolute drag is too high but its share is used, and why whether the tailgater hits the lorry turns on the reaction time. |
| [`cases/heatPumpCover`](cases/heatPumpCover) | A heat pump's outdoor unit, built from a Daikin ERGA06EV's published dimensions, switched on in still air at 2 C in the open and inside a louvred cover with a solid lid, a 3-D half model on one snappyHexMesh mesh from the fan's switch-on to 60 s, the coil as a capped cooling of fixed effectiveness and the fan as a fixed flow. Backs a clip; the README says why the run's own coil-inlet monitor reads 0.24 K too cold and how the clip's number corrects it, and why a half model with a fixed fan, no wind and no frost bounds what 0.7 C colder can mean. |
| [`cases/lorryClosePass2D`](cases/lorryClosePass2D) | A lorry overtaking a cyclist at 1.5 m and at 30 cm, in a 2-D horizontal section at his shoulder height, the rider a drag term moving through the fixed mesh, after a precursor of the lorry alone, under k-omega SST. Backs a clip; the README says why, with no air over the roof and an exaggerated wake behind the doors, it reports the 30 cm pass's push and pull only as multiples of the 1.5 m pass's, why the clip stops 2.5 m past the doors, and how its 1.5 m pass compares with `cyclistBehindLorry`'s 3-D estimate, which carries the newtons. |
| [`cases/windowAiring`](cases/windowAiring) | The window above `radiatorUnderWindow`'s radiator opened on a still 0 C morning, turned wide open and on tilt, in that room made 3-D and 3.5 m wide, from the moment it opens to 300 s, the tilted sash a solid profile from published fittings and the room's own air a passive scalar. Backs a clip; the README says why the stratified room makes its 91% replaced read high against a well-mixed decay, why the inflow is the figure to set beside measured air-change rates, and why both runs sit above the one measured bedroom while matching the authorities' ranges and the 10% ratio for a tilted window. |
| [`cases/cylinderRe3900_LES`](cases/cylinderRe3900_LES) | Re = 3900 circular cylinder LES, matched to Parnaudeau et al. (2008). |

## What you should be able to do

Clone, run, and get a different answer if we got it wrong.

```sh
cd cases/roomFanInOut2D
./Allrun in        # or: ./Allrun out
```

Meshes and initial fields are generated by scripts in each case rather than committed, so
a clean clone runs. Nothing under `constant/polyMesh` or in time directories is tracked —
those are outputs.

## What is not here

Results. No fields, no time directories, no renders. A case's job is to let you produce
those yourself; a repository full of somebody else's output is not evidence, it is file
size.

## Reading a case

Every case README states what the case claims and, separately, **what it cannot**. The
limits section is the part worth reading first — the modelling choices that would change
the answer are listed there rather than left for you to find. If a case's results are used
to make a claim publicly and the limits contradict that claim, the limits are correct and
the claim is wrong.

Issues and corrections are welcome. A case that survives being checked is worth more than
one that was never looked at.
