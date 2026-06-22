import time

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd

from finmag import Simulation
from finmag.energies import Exchange, Demag, Zeeman, UniaxialAnisotropy
from finmag.util.mesh_templates import Sphere
from finmag.util.consts import flux_density_to_field_strength


# -----------------------------------------------------------------------------
# Geometry
# -----------------------------------------------------------------------------

R = 20.0          # nm, sphere radius -> D = 40 nm
maxh = 2.0        # nm, target FEM mesh resolution

sphere = Sphere(r=R, center=(0, 0, 0), name="sphere_R20")
mesh = sphere.create_mesh(maxh=maxh, save_result=False)


# -----------------------------------------------------------------------------
# Material parameters
# -----------------------------------------------------------------------------

Ms = 1700e3       # A/m
A = 10e-12        # J/m = 1e-11 J/m
K1 = 4.8e4        # J/m^3
easy_axis = (0, 0, 1)


# -----------------------------------------------------------------------------
# Field range
# -----------------------------------------------------------------------------

Bmax = 1.0        # T
Bmin = -1.0       # T
Bstep = 0.005     # T

B_upper = np.arange(Bmax, Bmin - 0.5 * Bstep, -Bstep)
B_lower = np.arange(Bmin, Bmax + 0.5 * Bstep,  Bstep)

branches = [
    ("upper", B_upper),
    ("lower", B_lower),
]


# -----------------------------------------------------------------------------
# Simulation setup
# -----------------------------------------------------------------------------

sim = Simulation(mesh, Ms, unit_length=1e-9, name="sphere_R20_hysteresis_upper_lower")

sim.alpha = 0.5
sim.do_precession = True

# Start saturated along +z.
sim.set_m((0, 0, 1))

sim.add(Exchange(A))
sim.add(Demag())
sim.add(UniaxialAnisotropy(K1, easy_axis))

# Initial Zeeman term.
H0 = flux_density_to_field_strength(B_upper[0])
zeeman = Zeeman((0, 0, H0))
sim.add(zeeman)


# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------

print("mesh vertices:", mesh.num_vertices())
print("mesh cells:", mesh.num_cells())
print("B upper points:", len(B_upper))
print("B lower points:", len(B_lower))
print("total field points:", len(B_upper) + len(B_lower))


# -----------------------------------------------------------------------------
# Hysteresis loop
# -----------------------------------------------------------------------------

hysteresis_data = []

start_time = time.perf_counter()

global_index = 0

for branch_name, B_values in branches:
    print("\nStarting {} branch".format(branch_name))

    for branch_index, Bz in enumerate(B_values):
        Hz = flux_density_to_field_strength(Bz)
        zeeman.set_value((0, 0, Hz))

        print(
            "Relaxing {} branch_index={} global_index={} Bz={:.6f} T".format(
                branch_name, branch_index, global_index, Bz
            )
        )

        sim.relax(stopping_dmdt=1.0, dt_limit=1e-10)

        mx, my, mz = sim.m_average

        hysteresis_data.append(
            {
                "global_index": global_index,
                "branch": branch_name,
                "branch_index": branch_index,
                "Bz_T": Bz,
                "Hz_Apm": Hz,
                "mx_avg": mx,
                "my_avg": my,
                "mz_avg": mz,
            }
        )

        print("  <m> = ({:.6f}, {:.6f}, {:.6f})".format(mx, my, mz))

        global_index += 1

end_time = time.perf_counter()
elapsed_s = end_time - start_time


# -----------------------------------------------------------------------------
# Save data
# -----------------------------------------------------------------------------

df = pd.DataFrame(hysteresis_data)

df.to_csv(
    "sphere_R20_hysteresis_upper_lower.txt",
    sep="\t",
    index=False,
)

with open("sphere_R20_hysteresis_timing.txt", "w") as f:
    f.write("elapsed_wall_clock_s\t{:.6f}\n".format(elapsed_s))
    f.write("R_nm\t{}\n".format(R))
    f.write("D_nm\t{}\n".format(2 * R))
    f.write("maxh_nm\t{}\n".format(maxh))
    f.write("Ms_Apm\t{}\n".format(Ms))
    f.write("A_Jpm\t{}\n".format(A))
    f.write("K1_Jpm3\t{}\n".format(K1))
    f.write("Bmax_T\t{}\n".format(Bmax))
    f.write("Bmin_T\t{}\n".format(Bmin))
    f.write("Bstep_T\t{}\n".format(Bstep))
    f.write("upper_points\t{}\n".format(len(B_upper)))
    f.write("lower_points\t{}\n".format(len(B_lower)))
    f.write("total_points\t{}\n".format(len(B_upper) + len(B_lower)))
    f.write("demag\ton\n")


# -----------------------------------------------------------------------------
# Plot
# -----------------------------------------------------------------------------

plt.figure(figsize=(5, 4))

for branch_name in ["upper", "lower"]:
    sub = df[df["branch"] == branch_name]
    plt.plot(sub["Bz_T"], sub["mz_avg"], "o-", markersize=2, label=branch_name)

plt.xlabel("Bz [T]")
plt.ylabel("<mz>")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("sphere_R20_hysteresis_upper_lower.png", dpi=200)


print("\nElapsed wall-clock time: {:.3f} s".format(elapsed_s))
print("saved sphere_R20_hysteresis_upper_lower.txt")
print("saved sphere_R20_hysteresis_upper_lower.png")
print("saved sphere_R20_hysteresis_timing.txt")
