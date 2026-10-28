# Finned heat sink on a 15 W CPU

A conjugate heat transfer case: an extruded aluminium heat sink on a 15 W CPU, with air at
25 C coming at it at 2 m/s along its fins. The air and the aluminium are solved together,
so the heat conducts through the base and up the fins and the air carries it away. The
case reports the temperature of the sink where it touches the CPU and the sink's overall
thermal resistance.

`./Allrun` solves it. It prints the numbers below and a hand estimate to set beside them.

## The sink and the air

- **Base** 50 x 50 mm, 5 mm thick.
- **Fins** ten, 1 mm thick and 25 mm tall, at a 5 mm pitch, so the gaps between them are
  4 mm. They run the full 50 mm in the direction of the air. The outer fins sit 2 mm in
  from the base's edges.
- **Aluminium** 200 W/m K, the conductivity of 6063, a common extrusion alloy.
- **The CPU** is 15 W spread evenly over a 30 x 30 mm square centred under the base. The
  rest of the base's underside is insulated.
- **The air** arrives at 2 m/s and 25 C, uniform across the inlet 50 mm upstream of the
  sink. The sink stands on a flat board, a no-slip wall that carries no heat. The domain is
  200 mm wide and 120 mm tall, so the sink blocks 6% of it and most of the air can go round
  and over the sink as it would in open air. The outlet is 100 mm downstream.
- **Laminar** flow. Between the fins the Reynolds number on the 4 mm gap is about 400.
- **Gravity** is on, but at 2 m/s natural convection changes nothing measurable.

## What it finds

The run of record is `runs/base`, 3000 iterations on 4 cores.

| | |
|---|---:|
| CPU contact, mean | 46.36 C |
| CPU contact, hottest point | 46.78 C |
| sink, hottest point | 46.76 C |
| inlet air | 25.00 C |
| thermal resistance, (T_base - T_inlet) / 15 W | 1.424 K/W |
| mean air speed between the fins, at mid-length | 1.522 m/s |

**The sink's thermal resistance is 1.424 K/W.** With 25 C air the CPU contact averages
46.36 C, 21.36 K above the air. Its hottest point is 46.78 C, 0.42 K above its mean, so
the aluminium spreads the 15 W almost evenly.

**Most of the air goes through the fins, but not all of it.** Between the fins it moves at
1.522 m/s at mid-length. If all of the 2 m/s arriving in front of the sink went through
the 4 mm gaps, it would move at 2.50 m/s there. About 61% of it does. The rest goes round
the sides and over the top. The air leaving the fins has warmed by 6.84 K.

## The heat balance closes

The CPU puts 15.000 W into the sink. 15.000 W crosses the sink's wetted surface into the
air, and the air carries 15.003 W out of the domain: 100.0% of the heat in. Over the last
500 iterations the CPU contact moved by 0.0001 K and the heat carried out by 0.0063 W.

The solve runs in two stages, and the balance needs the second. Stage 1 solves the flow
and the heat together for 1500 iterations. The wake behind the sink is unsteady, and the
steady solver does not settle on one flow. Over stage 1's last 1000 iterations the heat
carried out swings between 13.16 and 14.90 W, and it ends at 13.827 W. Stage 2 freezes the
flow at iteration 1500 and solves the heat alone, which has one answer. The CPU contact
moves from 46.33 C at the end of stage 1 to 46.36 C, and is steady to 0.001 K from
iteration 1800.

## A hand estimate agrees once it is told how much air goes through the fins

`scripts/hand_estimate.py` works the resistance out by hand: Teertstra, Yovanovich and
Culham's model for the heat transfer in the fin channels, the fin efficiency, conduction
through the base and the spreading from the 30 mm contact into it. Its one unknown is the
air speed between the fins. It is run twice: with all the air through the fins, and at the
speed the solve found.

| | speed between the fins | h | fin efficiency | resistance | CPU contact |
|---|---:|---:|---:|---:|---:|
| hand, no bypass | 2.500 m/s | 33.8 W/m2K | 0.933 | 1.192 K/W | 42.9 C |
| hand, at the solved speed | 1.522 m/s | 27.3 W/m2K | 0.945 | 1.449 K/W | 46.7 C |
| solve | 1.522 m/s | | | 1.424 K/W | 46.36 C |

At the solved speed the hand estimate is 1.449 K/W, 2% above the solve's 1.424 K/W. Of
that, convection from the fins is 1.405 K/W, the base 0.010 K/W and the spreading 0.034
K/W. With all the air forced through the fins the hand estimate falls to 1.192 K/W, the
bound a shroud or a fan blowing straight into the fins would approach.

## Checks

**Domain size.** `./Allrun tight` solves the same sink in the first study's domain, 15 mm
beside and 20 mm over the sink, which blocks 37% of the air. It has 158,432 air cells.
More air is pushed through the fins there, 1.826 m/s between them, and the resistance comes
out 1.360 K/W, 4.5% below the run of record. Its balance closes too: the air carries out
14.995 W of the 15.000 W. The hand estimate at its speed is 1.348 K/W, 1% below the solve.
The domain moves the answer through the air speed between the fins, and the hand estimate
follows it.

**The enthalpy scheme.** In the study the case came from, a single-stage run on the tight
domain, 1500 iterations with flow and heat together, closed its balance at 97.0%. The same
run with the bounded, limited scheme for enthalpy replaced by an unbounded one closed at
97.2%. The scheme was not what held the balance short. The frozen-flow second stage is
what closes it.

## The model

- `chtMultiRegionSimpleFoam`, steady, from OpenFOAM v2512. The air is one region and the
  sink another, coupled by `turbulentTemperatureCoupledBaffleMixed` on their shared surface.
  The CPU is `externalWallHeatFluxTemperature` with a fixed flux of 16,667 W/m2.
- **Half model.** The plane through the sink's centre, along the air's direction, is a
  symmetry plane. Every number in this README is for the whole sink: the scripts double the
  half model's flows and heats.
- **The mesh** is one blockMesh box of hexahedra, graded away from the sink. topoSet marks
  the base and fins, splitMeshRegions cuts them into their own region, and a second topoSet
  carves the CPU's square out of the sink's underside as a patch. Inside the sink's
  footprint the cells are 1 mm along the flow and 0.5 mm across it, so each fin is two cells
  thick and each gap eight cells wide; 0.5 mm in the base and 1 mm up the fins.
  The run of record has 368,964 cells in the air and 37,500 in the sink.
- **The sides and top of the domain** are symmetry planes, so the air slips along them.
- 3000 SIMPLE iterations in two stages: 1500 with the flow and the heat solved together,
  then 1500 with the flow frozen and the heat alone. The monitors are written every 10.

## Limits

- **The CPU is a uniform heat flux on the sink.** There is no die, no lid, no thermal
  paste. The temperature reported is the sink's base where it meets the CPU, averaged over
  the contact. A real CPU's junction is hotter by the resistance of the paste and the
  package, often as much again for a small sink like this. The result is the sink's
  resistance, not the CPU's.
- **The 2 m/s is the speed of the air approaching the sink, in open space.** About
  61% of it goes through the fins and the rest goes round and over. A fan blowing
  straight into the fins, or a duct that shrouds them, would force more air through and
  lower the resistance toward the no-bypass bound above. The answer belongs to this
  arrangement.
- **Steady and laminar.** The wake behind a blunt body at this speed is unsteady. The steady
  solver does not settle on one flow, so the run freezes the flow at iteration 1500 and
  solves the heat on that one state of the wake. Over stage 1's last 1000 iterations the
  CPU contact moved between 46.13 and 46.39 C. Turbulence arriving with
  the air, from a fan for instance, would raise the heat transfer.
- **No radiation.** A bare aluminium sink radiates little. An anodised black one at 45 C
  would shed perhaps 0.5 to 1 W of the 15 W by radiation and run slightly cooler.
- **Constant properties.** The air's viscosity and conductivity are fixed at their 25 C
  values. Over a 20 K rise this shifts the answer by a few per cent.
- **The board takes no heat.** A real motherboard carries a share of the CPU's heat away
  through its socket and copper. Here all 15 W goes through the sink.
- **One mesh.** The `fine` variant, 1.5 times the cells each way, is set up and was not
  solved for the run of record. The answer is not shown to be independent of the mesh.
- **One sink.** Fin count, thickness and height are fixed in `scripts/make_case.py`, and the
  hand estimate in `scripts/hand_estimate.py` uses the same numbers. Change both together.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it, and Python 3.

```sh
cd cases/finnedHeatSink
./Allrun            # the run of record, runs/base
./Allrun tight      # the first study's small domain, runs/tight
./Allrun fine       # 1.5 times the cells each way, runs/fine
NP=8 ./Allrun       # on 8 cores instead of 4
```

`Allrun` calls `Allmesh`, which writes `runs/<variant>/` from `case/` with
`scripts/make_case.py`, builds and splits the mesh and checks both regions. `Allrun` then
decomposes, solves, reconstructs the last iteration, and runs `scripts/postprocess.py` and
`scripts/hand_estimate.py`. They write `results.txt`, `results.json`,
`hand_estimate.txt` and `wallclock.txt` in the run's directory. `./Allclean` removes
`runs/`.

On a Reynolds instance with 4 cores the run of record's solver took 650 s: 481 s for the
flow and heat together and 169 s for the heat alone. The whole `./Allrun` took 656 s. The
tight run's solver took 586 s.

The case was set up by an agent from a staff study whose solve ran but was never checked,
and rebuilt and checked by us. The rebuild widened the domain, which had blocked 37% of the
air, and added the outlet's heat balance, the planes through the fins that the hand estimate
needs, and the frozen-flow second stage that closes the balance.
