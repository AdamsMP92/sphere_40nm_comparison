# Ubermag/OOMMF

This folder contains an Ubermag/OOMMF hysteresis calculation for a 40 nm Fe sphere.

- Script: `iron_sphere_ubermag_32.py`
- Mesh: `32 x 32 x 32`
- Cell size: `2 nm`
- Geometry: spherical `Ms` mask with diameter 40 nm
- Active magnetic cells: 4224
- Material: `Ms = 1.7e6 A/m`, `A = 1e-11 J/m`, `Ku = 4.8e4 J/m^3`
- Driver: `oommfc.MinDriver`
- Field loop: `+1 T -> -1 T -> +1 T`, `5 mT` steps
- Demag: enabled

Main output used in the comparison:

- `Hysteresis_1.txt`

Run from this directory in an Ubermag/OOMMF environment:

```bash
python iron_sphere_ubermag_32.py
```
