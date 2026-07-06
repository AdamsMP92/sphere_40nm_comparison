# Matrixfree2

This folder contains an archived Matrixfree2 hysteresis result for a 40 nm Fe sphere.

- Mesh files: `sphere_40nm.npz`, `sphere_40nm.vtu`
- Mesh source: Gmsh core exported from the mammos-mumag mesh-generation pipeline
- Mesh size: 1301 nodes / 6228 tetrahedra
- Material tag: all tetrahedra have tag 1
- Sidecar files: `sphere_40nm.p2`, `sphere_40nm.krn`
- Field loop: `+1 T -> -1 T -> +1 T`, `5 mT` steps
- Data points: 801
- Runtime log: `run.log`

Main outputs:

- `hysteresis.csv`
- `run.log`
- `params.log`
- `sphere_40nm.mh`

Reproduction note:

`run_sphere.sh` uses `pixi run -e cuda` and runs `../src/loop.py`. Check that the mesh basename in the script matches the available files. The archived files in this folder use the basename `sphere_40nm`.

Expected basename set:

```text
sphere_40nm.npz
sphere_40nm.vtu
sphere_40nm.p2
sphere_40nm.krn
```
