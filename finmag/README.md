# Finmag

This folder contains a Finmag hysteresis calculation for a 40 nm Fe sphere.

- Script: `sphere_R20_hyst_full.py`
- Geometry: Finmag internal sphere mesh, radius 20 nm, `maxh = 2 nm`
- Material: `Ms = 1.7e6 A/m`, `A = 1e-11 J/m`, `K1 = 4.8e4 J/m^3`
- Field loop: `+1 T -> -1 T -> +1 T`, `5 mT` steps
- Dynamics/minimization: `sim.relax(stopping_dmdt=1.0, dt_limit=1e-10)`, `alpha = 0.5`

Main outputs:

- `sphere_R20_hysteresis_upper_lower.txt`
- `sphere_R20_hysteresis_upper_lower.png`
- `sphere_R20_hysteresis_timing.txt`

Run from this directory in a working Finmag environment:

```bash
python sphere_R20_hyst_full.py
```
