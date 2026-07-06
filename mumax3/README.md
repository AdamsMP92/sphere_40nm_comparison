# MuMax3

This folder contains a MuMax3 hysteresis calculation for a 40 nm Fe sphere.

- Script: `IronSphere_UniaxialAni.mx3`
- Grid: `32 x 32 x 32`
- Cell size: `2 nm`
- Geometry: spherical cutout with diameter 40 nm
- Active magnetic cells: 4224
- Material: `Msat = 1.7e6 A/m`, `Aex = 1e-11 J/m`, `Ku1 = 4.8e4 J/m^3`
- Field loop: `+1 T -> -1 T -> +1 T`, `5 mT` steps
- Temperature: `Temp = 0`
- Demag: enabled

Main output used in the comparison:

- `Hysteresis_1.txt`

Run with MuMax3 from this directory:

```bash
mumax3 IronSphere_UniaxialAni.mx3
```
