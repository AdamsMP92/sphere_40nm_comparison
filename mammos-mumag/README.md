# mammos-mumag

This folder contains an archived mammos-mumag hysteresis result for a 40 nm Fe sphere.

- Mesh file: `sphere20.fly`
- Mesh regions: magnetic core, air shell, outer boundary shell
- Mesh size: 16970 nodes / 98946 tetrahedra
- Region tetrahedra: core 6298 / air 36187 / shell 56461
- Material core: `Ms = 1.7e6 A/m`, `A = 1e-11 J/m`, `K1 = 4.8e4 J/m^3`
- Air and boundary shell are non-magnetic
- Field branch: upper branch, `+1 T -> -1 T`, `5 mT` steps
- Minimization: mammos-mumag energy minimizer, `tol_fun = 1e-10`

Main outputs:

- `sphere20.csv`
- `sphere20.fly`
- `sphere20.p2`
- `sphere20.krn`
- `sphere20_stats.txt`
- `info.json`

The mesh can be regenerated from `../mesh_generation/prepare_sphere20_air_shell.py`.
