# mammos-mumag FEM simulation of a 20 nm iron sphere

This directory documents the `mammos-mumag` finite-element micromagnetic
simulation used for the 20 nm radius iron-sphere hysteresis benchmark.

The setup uses a three-region finite-element mesh:

1. iron sphere, radius 20 nm
2. non-magnetic air region, radius 20 nm to 60 nm
3. outer spherical shell, radius 60 nm to 120 nm

The air and shell regions are required by the `mammos-mumag` magnetostatic
solver. The outer shell is used for the spherical-shell transformation that
approximates the open boundary condition at infinity.

## Directory Structure

```text
mumag/
  README.md
  sphere20_air_shell.fly
  sphere20_mumag.py
  mesh_generation/
    prepare_sphere20_air_shell.py
    sphere20_air_shell.geo
    sphere20_air_shell.unv
    sphere20_air_shell_raw.fly
    sphere20_air_shell_mesh_check.txt
  results/
    sphere20_mumag.log
    iron_sphere_air_shell_loop/
      sphere20.csv
      sphere20.fly
      sphere20.krn
      sphere20.p2
      sphere20_0001.vtu
      ...
      sphere20_0098.vtu
      sphere20_stats.txt
      info.json
```

The top-level `sphere20_air_shell.fly` is the final mesh used by the simulation.
The `mesh_generation/` folder contains the scripts and intermediate files needed
to reproduce that mesh.

## Mesh Generation

The mesh is generated with Gmsh and converted to the `.fly` format required by
`mammos-mumag`.

From the `mumag/` directory:

```bash
python mesh_generation/prepare_sphere20_air_shell.py
```

This script reads:

```text
mesh_generation/sphere20_air_shell.geo
```

and writes:

```text
mesh_generation/sphere20_air_shell.unv
mesh_generation/sphere20_air_shell_raw.fly
mesh_generation/sphere20_air_shell_mesh_check.txt
sphere20_air_shell.fly
```

The final `.fly` file is written to the `mumag/` directory because it is the mesh
directly consumed by `sphere20_mumag.py`.

The mesh-generation script also sanitizes and retags the `.fly` file:

- Fortran-style `D` exponents are converted to `E` exponents for compatibility
  with `esys-escript`.
- Tetrahedra are retagged by centroid radius:
  - tag 1: iron sphere
  - tag 2: non-magnetic air region
  - tag 3: outer shell

The mesh check for the archived mesh is:

```text
nodes: 16970
tets: 98946
tag 1 iron tets: 6298
tag 2 air tets: 36187
tag 3 shell tets: 56461
min volume: 0.9938346883663521
max volume: 392.89753111092733
bad tets: 0
```

The geometry is specified in nanometers in the `.geo` file. The simulation uses
`size = 1.0e-9`, so one mesh unit corresponds to one nanometer.

## Simulation Script

The simulation is defined in:

```text
sphere20_mumag.py
```

It loads:

```python
Mesh("sphere20_air_shell.fly")
```

and writes output to:

```text
results/iron_sphere_air_shell_loop/
```

The simulation can be started from the `mumag/` directory with:

```bash
python sphere20_mumag.py > results/sphere20_mumag.log 2>&1
```

## Material Parameters

The magnetic material is assigned only to tag 1, the iron sphere. Tags 2 and 3
are non-magnetic.

Iron sphere:

```text
Ms = 1.7e6 A/m
A  = 1.0e-11 J/m
K1 = 4.8e4 J/m^3
anisotropy axis = z
```

Air and outer shell:

```text
Ms = 0
A  = 0
K1 = 0
```

## Hysteresis Parameters

The simulation starts from a uniform magnetization along `z`:

```text
m = (0, 0, 1)
```

The external field is applied along `z`:

```text
h_vect = (0, 0, 1)
```

Field sweep:

```text
mu0 H_start = +1.0 T
mu0 H_final = -1.0 T
mu0 H_step  = -0.01 T
```

For a complete run this corresponds to 201 field points for the down-sweep.

The minimizer settings used here are:

```text
tol_fun = 1e-10
tol_h_mag_factor = 1
precond_iter = 10
```

## Results

The main hysteresis output is:

```text
results/iron_sphere_air_shell_loop/sphere20.csv
```

The spatial magnetization states are stored as VTU files:

```text
results/iron_sphere_air_shell_loop/sphere20_0001.vtu
...
results/iron_sphere_air_shell_loop/sphere20_0098.vtu
```

The output also contains the exact input files written by `mammos-mumag` for the
run:

```text
results/iron_sphere_air_shell_loop/sphere20.fly
results/iron_sphere_air_shell_loop/sphere20.krn
results/iron_sphere_air_shell_loop/sphere20.p2
```

These files preserve the mesh, material parameters, and simulation parameters
used for the archived result.

## Notes

The archived run contains 98 saved VTU states. The down-sweep stops before
reaching `mu0 H_final = -1 T` because the stopping criterion
`m_final = -2.0 T` is reached. The last CSV row is at approximately
`mu0 H = -0.47 T` with `Jz = -2.023 T`.

This behavior is relevant for reproducibility because `mammos-mumag` uses
`m_final` as an early stopping condition in the hysteresis loop.
