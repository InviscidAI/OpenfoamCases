# Results of the `start300` runs

Made by `postprocess.py`. Temperatures are area-weighted means over the section: the
floor layer is y < 0.1 m and head height y 1.0-1.2 m, both over x 0.3-2.0 m from the
glass. Fluxes are gross, one way, in m3/s per metre of section: the sill line is
y = 0.90 m for x < 0.30 m, the floor line x = 1.0 m for y < 0.30 m.


## The floor layer against the room mean, 30 s windows (first 600 s)

| window (s) | window: floor below room mean (K) | opposite: floor below room mean (K) |
|---|---:|---:|
| 0-30 | 0.01 | 0.57 |
| 30-60 | 0.05 | 1.72 |
| 60-90 | 0.08 | 1.45 |
| 90-120 | 0.11 | 1.81 |
| 120-150 | 0.21 | 1.76 |
| 150-180 | 0.58 | 1.70 |
| 180-210 | 0.77 | 1.89 |
| 210-240 | 0.66 | 1.95 |
| 240-270 | 0.55 | 2.07 |
| 270-300 | 0.58 | 2.10 |

## Heat budget

Heat unaccounted for over each 7.5 s interval, W/m: the radiator plus the wall heat flux
less the rise in internal energy, (cv/R) times the integral of p (energyCheck).

| | mean | min | max |
|---|---:|---:|---:|
| window | +0.038 | -0.20 | +0.18 |
| opposite | +0.015 | -0.04 | +0.11 |
