# Mesh Generation

This folder contains the mesh-generation files used for mammos-mumag and the shared Matrixfree2 core export.

Main script:

- `prepare_sphere20_air_shell.py`

Geometry:

- Core radius: 20 nm
- Air shell radius: 60 nm
- Outer boundary shell radius: 120 nm
- Source geometry: `sphere20_air_shell.geo`

Outputs for mammos-mumag:

- `sphere20_air_shell.unv`
- `sphere20_air_shell_raw.fly`
- `sphere20_air_shell_mesh_check.txt`
- `../mammos-mumag/sphere20.fly`

Archived mammos-mumag mesh check:

```text
nodes: 16970
tets: 98946
core/air/shell tets: 6298 / 36187 / 56461
bad tets: 0
```

Outputs for Matrixfree2 core export:

- `matrixfree2_core_from_mumag_mesh/sphere_40nm_new.npz`
- `matrixfree2_core_from_mumag_mesh/sphere_40nm_new.vtu`
- `matrixfree2_core_from_mumag_mesh/sphere_40nm_mesh_check.txt`

Matrixfree2 core check:

```text
nodes: 1301
tets: 6228
tag 1 core tets: 6228
bad tets: 0
```

Run examples:

```bash
python prepare_sphere20_air_shell.py --target mumag
python prepare_sphere20_air_shell.py --target matrixfree2
python prepare_sphere20_air_shell.py --target both
```
