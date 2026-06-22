from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

import meshio
import numpy as np


NAME = "sphere20_air_shell"
MATRIXFREE2_NAME = "sphere_40nm"
R_IRON = 20.0
R_AIR = 60.0


def parse_float(value: str) -> float:
    return float(value.replace("D", "E"))


def tetra_volume(a, b, c, d) -> float:
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    dx, dy, dz = d
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    wx, wy, wz = dx - ax, dy - ay, dz - az
    return abs(
        ux * (vy * wz - vz * wy)
        - uy * (vx * wz - vz * wx)
        + uz * (vx * wy - vy * wx)
    ) / 6.0


def tag_from_centroid_radius(r: float) -> str:
    if r <= R_IRON:
        return "1"
    if r <= R_AIR:
        return "2"
    return "3"


def sanitize_and_retag_fly(raw_fly: Path, out_fly: Path, check_path: Path) -> None:
    lines = raw_fly.read_text().splitlines()
    nodes: dict[str, tuple[float, float, float]] = {}
    out_lines: list[str] = []
    in_nodes = False
    in_tets = False
    remaining = 0
    volumes: list[float] = []
    counts = {"1": 0, "2": 0, "3": 0}

    for line in lines:
        line = line.replace("D+", "E+").replace("D-", "E-")
        if line.startswith("3E-nodes"):
            line = line.replace("3E-nodes", "3D-nodes", 1)

        parts = line.split()
        if len(parts) == 2 and parts[0] == "3D-nodes":
            in_nodes = True
            remaining = int(parts[1])
            out_lines.append(line)
            continue

        if in_nodes and remaining > 0:
            nodes[parts[0]] = (
                parse_float(parts[3]),
                parse_float(parts[4]),
                parse_float(parts[5]),
            )
            remaining -= 1
            if remaining == 0:
                in_nodes = False
            out_lines.append(line)
            continue

        if len(parts) == 2 and parts[0] == "Tet4":
            in_tets = True
            remaining = int(parts[1])
            out_lines.append(line)
            continue

        if in_tets and remaining > 0:
            element_id = parts[0]
            node_ids = parts[2:6]
            xyz = [nodes[node_id] for node_id in node_ids]
            cx = sum(p[0] for p in xyz) / 4.0
            cy = sum(p[1] for p in xyz) / 4.0
            cz = sum(p[2] for p in xyz) / 4.0
            tag = tag_from_centroid_radius(math.sqrt(cx * cx + cy * cy + cz * cz))
            counts[tag] += 1
            volumes.append(tetra_volume(*xyz))
            out_lines.append(" ".join([element_id, tag, *node_ids]))
            remaining -= 1
            if remaining == 0:
                in_tets = False
            continue

        out_lines.append(line)

    out_fly.write_text("\n".join(out_lines) + "\n")
    check_path.write_text(
        "\n".join(
            [
                f"nodes: {len(nodes)}",
                f"tets: {sum(counts.values())}",
                f"tag 1 iron tets: {counts['1']}",
                f"tag 2 air tets: {counts['2']}",
                f"tag 3 shell tets: {counts['3']}",
                f"min volume: {min(volumes)}",
                f"max volume: {max(volumes)}",
                f"bad tets: {sum(v <= 0 for v in volumes)}",
            ]
        )
        + "\n"
    )


def run_gmsh(geo: Path, unv: Path, msh: Path) -> None:
    try:
        subprocess.run(
            ["gmsh", "-3", str(geo), "-format", "unv", "-o", str(unv)],
            check=True,
        )
        subprocess.run(
            ["gmsh", "-3", str(geo), "-format", "msh2", "-o", str(msh)],
            check=True,
        )
    except FileNotFoundError:
        import gmsh

        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 1)
            gmsh.open(str(geo))
            gmsh.write(str(unv))
            gmsh.write(str(msh))
        finally:
            gmsh.finalize()


def export_mumag_mesh(unv: Path, raw_fly: Path, out_fly: Path, check_path: Path) -> None:
    from mammos_mumag.tofly import convert

    convert(unv, raw_fly, exclude_list=[1, 2])
    sanitize_and_retag_fly(raw_fly, out_fly, check_path)
    print(f"wrote {out_fly}")
    print(f"wrote {check_path}")


def export_matrixfree2_core_mesh(msh: Path, out_dir: Path) -> None:
    mesh = meshio.read(msh)
    tetra_blocks = []
    tag_blocks = []

    for cells, physical in zip(
        mesh.cells,
        mesh.cell_data.get("gmsh:physical", []),
        strict=False,
    ):
        if cells.type != "tetra":
            continue
        tetra_blocks.append(cells.data)
        tag_blocks.append(np.asarray(physical))

    if not tetra_blocks:
        raise RuntimeError(f"No tetrahedra found in {msh}.")

    tets = np.vstack(tetra_blocks)
    tags = np.concatenate(tag_blocks)
    core_tets = tets[tags == 1]
    if len(core_tets) == 0:
        raise RuntimeError(f"No Physical Volume 1 core tetrahedra found in {msh}.")

    used_nodes, inverse = np.unique(core_tets.reshape(-1), return_inverse=True)
    core_points = mesh.points[used_nodes]
    core_tets_reindexed = inverse.reshape(core_tets.shape).astype(np.int32)
    matrixfree2_tets = np.column_stack(
        [
            core_tets_reindexed,
            np.ones(len(core_tets_reindexed), dtype=np.int32),
        ]
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / f"{MATRIXFREE2_NAME}.npz"
    vtu_path = out_dir / f"{MATRIXFREE2_NAME}.vtu"
    check_path = out_dir / f"{MATRIXFREE2_NAME}_mesh_check.txt"

    np.savez(npz_path, knt=core_points.astype(np.float64), ijk=matrixfree2_tets)
    meshio.write(
        vtu_path,
        meshio.Mesh(
            points=core_points,
            cells=[("tetra", core_tets_reindexed)],
            cell_data={"mat_id": [np.ones(len(core_tets_reindexed), dtype=np.int32)]},
        ),
    )

    volumes = [
        tetra_volume(*(core_points[node_id] for node_id in tet))
        for tet in core_tets_reindexed
    ]
    check_path.write_text(
        "\n".join(
            [
                f"source mesh: {msh}",
                f"nodes: {len(core_points)}",
                f"tets: {len(core_tets_reindexed)}",
                "tag 1 core tets: " + str(len(core_tets_reindexed)),
                f"min volume: {min(volumes)}",
                f"max volume: {max(volumes)}",
                f"bad tets: {sum(v <= 0 for v in volumes)}",
            ]
        )
        + "\n"
    )
    print(f"wrote {npz_path}")
    print(f"wrote {vtu_path}")
    print(f"wrote {check_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the sphere20 mammos-mumag mesh and optionally export the "
            "same magnetic core for Matrixfree2."
        )
    )
    parser.add_argument(
        "--target",
        choices=["both", "mumag", "matrixfree2"],
        default="both",
        help="Which solver mesh export to write. Default: both.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    dataset_dir = script_dir.parent

    geo = script_dir / f"{NAME}.geo"
    unv = script_dir / f"{NAME}.unv"
    msh = script_dir / f"{NAME}.msh"
    raw_fly = script_dir / f"{NAME}_raw.fly"
    out_fly = dataset_dir / f"{NAME}.fly"
    check_path = script_dir / f"{NAME}_mesh_check.txt"
    matrixfree2_dir = script_dir / "matrixfree2_core_from_mumag_mesh"

    run_gmsh(geo, unv, msh)
    if args.target in {"both", "mumag"}:
        export_mumag_mesh(unv, raw_fly, out_fly, check_path)
    if args.target in {"both", "matrixfree2"}:
        export_matrixfree2_core_mesh(msh, matrixfree2_dir)


if __name__ == "__main__":
    main()
