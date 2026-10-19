# Curtain comparison, 0–300 s

| run | cumulative heat into room | share of 60 W radiator | final instantaneous crossing | final glass loss |
|---|---:|---:|---:|---:|
| hanging | 2.51 kJ/m | 13.9% | 7.69 W/m | 47.97 W/m |
| tucked | 10.03 kJ/m | 55.7% | 34.30 W/m | 24.56 W/m |
| sill | 3.39 kJ/m | 18.8% | 10.34 W/m | 47.27 W/m |

The crossing enthalpy is the solver’s sensible enthalpy reference, `rho*Ux*Cp*(T-293.15 K)`, net into x>0.15. For hanging and sill, curtainB is the room-side mapped-wall patch and its wall heat flux is added.

## hanging
At 300 s: room-side mean 20.24 C; behind-curtain mean 21.66 C; top gross up/down 0.0027/0.0000 m3/s/m.
7.5 s budget unaccounted: mean -0.134, range -0.277 to +0.196 W/m.

## tucked
At 300 s: room-side mean 21.01 C; behind-curtain mean 12.89 C; top gross up/down 0.0021/0.0020 m3/s/m.
7.5 s budget unaccounted: mean +0.049, range -0.040 to +0.207 W/m.

## sill
At 300 s: room-side mean 20.42 C; behind-curtain mean 19.96 C; top gross up/down 0.0009/0.0209 m3/s/m.
7.5 s budget unaccounted: mean +0.060, range -0.207 to +0.441 W/m.
