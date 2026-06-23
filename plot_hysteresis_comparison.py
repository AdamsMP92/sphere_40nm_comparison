#!/usr/bin/env python3
"""Plot the R=20 nm sphere hysteresis data from all available solvers."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = Path(__file__).resolve().parent
JS_T = 2.13628
OUTPUT_PATH = BASE_DIR / "hysteresis_comparison.png"
MATRIXFREE2_RUN_DIR = BASE_DIR / "matrixfree2" / "sim_5mT"

STYLES = {
    "Finmag": {"color": "#2a6fbb", "linewidth": 1.8},
    "Ubermag-OOMMF": {"color": "#d1495b", "linewidth": 1.8},
    "MuMax3": {"color": "#ed8b00", "linewidth": 1.8},
    "Matrixfree2": {"color": "#3a923a", "linewidth": 2.0},
    "mammos-mumag": {"color": "#7b4ab5", "linewidth": 2.0},
}


def load_tsv(path: Path, field_column: str, magnetization_column: str):
    """Read two numeric columns from a tab-separated table."""
    field = []
    magnetization = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for row in reader:
            field.append(float(row[field_column]))
            magnetization.append(float(row[magnetization_column]))
    return np.asarray(field), np.asarray(magnetization)


def load_finmag():
    path = BASE_DIR / "finmag" / "sphere_R20_hysteresis_upper_lower.txt"
    field, magnetization = load_tsv(path, "Bz_T", "mz_avg")
    return field, magnetization, path


def load_oommf():
    path = BASE_DIR / "ubermag-oommf" / "Hysteresis_1.txt"
    field, magnetization = load_tsv(path, "B_T", "mz_norm")

    # The exported OOMMF mean includes the nonmagnetic cells of the surrounding
    # box. Remove this constant volume-fraction factor for an M/Ms comparison.
    saturation = np.max(np.abs(magnetization))
    if saturation == 0:
        raise ValueError(f"OOMMF data in {path} have zero magnetization.")
    magnetization = magnetization / saturation
    return field, magnetization, path


def load_mumax3():
    path = BASE_DIR / "mumax3" / "Hysteresis_1.txt"
    data = np.loadtxt(path, comments="#")
    field = data[:, 6]
    magnetization = data[:, 3]
    return field, magnetization, path


def load_mammos_mumag():
    path = (
        BASE_DIR
        / "mumag"
        / "results"
        / "reduced_result_new"
        / "sphere20.csv"
    )
    data = np.loadtxt(path, delimiter=",", skiprows=15)
    field = data[:, 1]
    magnetization = data[:, 5] / JS_T
    return field, magnetization, path


def load_matrixfree2_csv(path: Path):
    field = []
    magnetization = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            field.append(float(row["B_ext_T"]))
            magnetization.append(float(row["J_par_T"]) / JS_T)
    return np.asarray(field), np.asarray(magnetization)


def load_matrixfree2_log(path: Path):
    pattern = re.compile(
        r"^step\s+\d+\s+B=(?P<field>[+-]?\d+\.\d+e[+-]\d+)\s+T\s+"
        r"J_par=(?P<magnetization>[+-]?\d+\.\d+e[+-]\d+)\s+T"
    )
    field = []
    magnetization = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        field.append(float(match.group("field")))
        magnetization.append(float(match.group("magnetization")) / JS_T)

    if not field:
        raise ValueError(f"No Matrixfree2 step data found in {path}.")
    return np.asarray(field), np.asarray(magnetization)


def latest_matrixfree2_csv() -> Path | None:
    selected_csv = MATRIXFREE2_RUN_DIR / "hysteresis.csv"
    if selected_csv.exists():
        return selected_csv

    directory = BASE_DIR / "matrixfree2"
    csv_candidates = sorted(
        directory.rglob("hysteresis.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return csv_candidates[0] if csv_candidates else None


def load_matrixfree2():
    directory = BASE_DIR / "matrixfree2"
    path = latest_matrixfree2_csv()
    if path is not None:
        field, magnetization = load_matrixfree2_csv(path)
        return field, magnetization, path

    log_candidates = sorted(
        directory.rglob("*.txt"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in log_candidates:
        try:
            field, magnetization = load_matrixfree2_log(path)
        except ValueError:
            continue
        return field, magnetization, path

    raise FileNotFoundError(
        "No Matrixfree2 hysteresis.csv or terminal log was found in "
        f"{directory}."
    )


def format_runtime(seconds: float) -> str:
    """Format a runtime in seconds as a compact human-readable string."""
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d} h {minutes:02d} min"
    return f"{minutes:d} min {seconds:02d} s"


def read_runtime_summary() -> dict[str, str]:
    """Read the manually collected runtime comparison."""
    path = BASE_DIR / "times.txt"
    runtimes = {}
    if not path.exists():
        return runtimes

    patterns = {
        "MuMax3": re.compile(r"^mumax3 .*?2 nm .*?\((?P<seconds>[\d.]+) seconds\)"),
        "Ubermag-OOMMF": re.compile(r"^ubermag .*?\((?P<seconds>[\d.]+) s\)"),
        "Finmag": re.compile(r"^finmag .*?\((?P<seconds>[\d.]+) s\)"),
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        for label, pattern in patterns.items():
            match = pattern.search(line)
            if match is not None:
                runtimes[label] = format_runtime(float(match.group("seconds")))
    return runtimes


def read_matrixfree2_summary() -> dict[str, str]:
    """Summarize the currently selected Matrixfree2 run."""
    csv_path = latest_matrixfree2_csv()
    if csv_path is None:
        return {
            "runtime": "n/a",
            "field_step": "n/a",
            "data": "n/a",
        }

    field, _ = load_matrixfree2_csv(csv_path)
    step_t = np.median(np.abs(np.diff(field))) if len(field) > 1 else np.nan
    step_mt = int(round(step_t * 1000)) if np.isfinite(step_t) else None

    runtime = "n/a"
    log_path = csv_path.with_name("run.log")
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        runtime_match = re.search(r"Simulation runtime:\s*(?P<runtime>\d+:\d+:\d+)", text)
        if runtime_match is not None:
            hours, minutes, seconds = (
                int(part) for part in runtime_match.group("runtime").split(":")
            )
            runtime = format_runtime(hours * 3600 + minutes * 60 + seconds)
        else:
            loop_match = re.search(r"Hysteresis loop finished in (?P<seconds>[\d.]+) s", text)
            if loop_match is not None:
                runtime = format_runtime(float(loop_match.group("seconds")))

    step_text = f"{step_mt} mT" if step_mt is not None else "unknown"
    return {
        "runtime": runtime,
        "field_step": step_text,
        "data": f"{len(field)} points",
    }


def read_mammos_mumag_runtime() -> str:
    """Estimate the archived MuMag runtime from output file timestamps."""
    result_dir = (
        BASE_DIR
        / "mumag"
        / "results"
        / "reduced_result_new"
    )
    setup_path = result_dir / "sphere20.p2"
    csv_path = result_dir / "sphere20.csv"
    if not setup_path.exists() or not csv_path.exists():
        return "n/a"

    elapsed = csv_path.stat().st_mtime - setup_path.stat().st_mtime
    if elapsed <= 0:
        return "n/a"
    return f"~{format_runtime(elapsed)}*"


def add_common_axis_style(ax):
    """Apply the common square-axis presentation."""
    ax.axhline(0, color="0.75", linewidth=0.8)
    ax.axvline(0, color="0.75", linewidth=0.8)
    ax.set_xlabel(r"$\mu_0 H_\mathrm{ext}$ (T)")
    ax.set_ylabel(r"$M_\parallel/M_s$")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)


def main():
    loaders = {
        "Finmag": load_finmag,
        "Ubermag-OOMMF": load_oommf,
        "MuMax3": load_mumax3,
        "mammos-mumag": load_mammos_mumag,
        "Matrixfree2": load_matrixfree2,
    }

    datasets = {}
    for label, loader in loaders.items():
        field, magnetization, path = loader()
        datasets[label] = (field, magnetization)
        print(f"{label:15s}: {len(field):4d} points from {path.relative_to(BASE_DIR)}")

    runtimes = read_runtime_summary()
    matrixfree_summary = read_matrixfree2_summary()
    mammos_mumag_runtime = read_mammos_mumag_runtime()

    fig = plt.figure(figsize=(11.5, 18.5))
    grid = fig.add_gridspec(
        nrows=6,
        ncols=2,
        height_ratios=[2.45, 4.8, 0.28, 3.15, 3.15, 3.15],
        hspace=0.28,
        wspace=0.18,
    )

    ax_info = fig.add_subplot(grid[0, :])
    ax_info.axis("off")
    ax_info.text(
        0.5,
        0.98,
        "Benchmark setup",
        ha="center",
        va="top",
        fontsize=13,
        fontweight="bold",
        transform=ax_info.transAxes,
    )
    ax_info.text(
        0.5,
        0.86,
        "Fe sphere: D = 40 nm | Ms = 1.70 MA/m | A = 10 pJ/m | "
        "K1 = 48 kJ/m³ | exchange length = 2.35 nm | T = 0 K",
        ha="center",
        va="top",
        fontsize=10.5,
        transform=ax_info.transAxes,
    )
    ax_info.text(
        0.5,
        0.74,
        "Reference loop: +1 T → -1 T → +1 T",
        ha="center",
        va="top",
        fontsize=10.5,
        transform=ax_info.transAxes,
    )

    table_rows = [
        [
            "MuMax3",
            "FDM",
            "32³ grid; 2 nm",
            "GPU",
            runtimes.get("MuMax3", "n/a"),
            "5 mT",
            "full loop",
            "relax: alpha=1",
            "802 points",
        ],
        [
            "Ubermag-OOMMF",
            "FDM",
            "32³ grid; 2 nm",
            "4 CPU",
            runtimes.get("Ubermag-OOMMF", "n/a"),
            "5 mT",
            "full loop",
            "MinDriver: defaults",
            "802 points",
        ],
        [
            "Finmag",
            "FEM",
            "tetrahedral; maxh=2 nm",
            "4 CPU",
            runtimes.get("Finmag", "n/a"),
            "5 mT",
            "full loop",
            "LLG: alpha=0.5, dt<=1e-10",
            "802 points",
        ],
        [
            "mammos-mumag",
            "FEM",
            "16,970 nodes / 98,946 tets",
            "CPU",
            mammos_mumag_runtime,
            "5 mT",
            "upper",
            "loop: tol_fun=1e-10",
            "401 points",
        ],
        [
            "Matrixfree2",
            "FEM",
            "20,496 nodes / 102,629 tets",
            "GPU",
            matrixfree_summary["runtime"],
            matrixfree_summary["field_step"],
            "upper",
            "AAPG: tau_f=1e-8, eps_a=1e-12",
            matrixfree_summary["data"],
        ],
    ]
    table = ax_info.table(
        cellText=table_rows,
        colLabels=[
            "Solver",
            "Method",
            "Discretization",
            "Hardware",
            "Runtime",
            "Field step",
            "Loop",
            "Dyn. / stop",
            "Data",
        ],
        colWidths=[0.112, 0.052, 0.242, 0.064, 0.085, 0.07, 0.078, 0.2, 0.097],
        cellLoc="left",
        colLoc="left",
        bbox=[0.0, 0.10, 1.0, 0.56],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.8)
    for (row, column), cell in table.get_celld().items():
        cell.set_edgecolor("0.75")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("0.92")
            cell.set_text_props(fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("0.975")

    ax_main = fig.add_subplot(grid[1, :])
    for label, (field, magnetization) in datasets.items():
        ax_main.plot(field, magnetization, label=label, **STYLES[label])

    add_common_axis_style(ax_main)
    ax_main.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=5,
        frameon=False,
    )

    ax_fdm_heading = fig.add_subplot(grid[2, 0])
    ax_fdm_heading.axis("off")
    ax_fdm_heading.text(
        0.5,
        0.5,
        "Finite-difference methods (FDM)",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    ax_fem_heading = fig.add_subplot(grid[2, 1])
    ax_fem_heading.axis("off")
    ax_fem_heading.text(
        0.5,
        0.5,
        "Finite-element methods (FEM)",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    panel_layout = [
        ("Ubermag-OOMMF", fig.add_subplot(grid[3, 0])),
        ("MuMax3", fig.add_subplot(grid[4, 0])),
        ("Finmag", fig.add_subplot(grid[3, 1])),
        ("mammos-mumag", fig.add_subplot(grid[4, 1])),
        ("Matrixfree2", fig.add_subplot(grid[5, 1])),
    ]
    ax_unused = fig.add_subplot(grid[5, 0])
    ax_unused.axis("off")
    for label, ax in panel_layout:
        field, magnetization = datasets[label]
        ax.plot(field, magnetization, **STYLES[label])
        ax.set_title(label)
        add_common_axis_style(ax)

    fig.subplots_adjust(top=0.985, bottom=0.025, left=0.09, right=0.98)
    fig.savefig(OUTPUT_PATH, dpi=250, bbox_inches="tight")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
