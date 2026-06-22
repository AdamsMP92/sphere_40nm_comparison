import pathlib
import time

import numpy as np
import pandas as pd

import discretisedfield as df
import micromagneticmodel as mm
import oommfc as oc


mu0 = 4 * np.pi * 1e-7

# Geometry
diameter = 40e-9
radius = diameter / 2

cell = 2e-9
n = 32
box_length = n * cell

# Material
Ms = 1700e3
A = 1e-11
Ku = 4.8e4
anis_u = (0, 0, 1)

# Field
Bmax = 1.0
Bmin = -1.0
Bstep = 0.005
field_direction = np.array([0.0, 0.0, 1.0])

mesh = df.Mesh(
    p1=(-box_length / 2, -box_length / 2, -box_length / 2),
    p2=( box_length / 2,  box_length / 2,  box_length / 2),
    cell=(cell, cell, cell),
)


def inside_sphere(point):
    x, y, z = point
    return x**2 + y**2 + z**2 <= radius**2


Ms_field = df.Field(
    mesh,
    nvdim=1,
    value=lambda point: Ms if inside_sphere(point) else 0,
)

m0 = df.Field(
    mesh,
    nvdim=3,
    value=(0, 0, 1),
    norm=Ms_field,
)

system = mm.System(name="IronSphere_UniaxialAni_32x32x32")
system.m = m0

driver = oc.MinDriver()


def set_energy_for_B(B):
    H = B / mu0
    Hvec = tuple(field_direction * H)

    system.energy = (
        mm.Exchange(A=A)
        + mm.UniaxialAnisotropy(K=Ku, u=anis_u)
        + mm.Demag()
        + mm.Zeeman(H=Hvec)
    )

    return Hvec


base_dir = pathlib.Path("IronSphere_UniaxialAni_ubermag_32")
mag_dir = base_dir / "MagData" / "Orientation_1"
hyst_dir = base_dir / "HystData"

mag_upper_dir = mag_dir / "upper"
mag_lower_dir = mag_dir / "lower"

mag_upper_dir.mkdir(parents=True, exist_ok=True)
mag_lower_dir.mkdir(parents=True, exist_ok=True)
hyst_dir.mkdir(parents=True, exist_ok=True)

nsteps = int(round((Bmax - Bmin) / Bstep))

B_upper = [Bmax - i * Bstep for i in range(nsteps + 1)]
B_lower = [Bmin + i * Bstep for i in range(nsteps + 1)]

rows = []
start = time.perf_counter()
global_index = 0

for branch_name, B_values, save_dir in [
    ("upper", B_upper, mag_upper_dir),
    ("lower", B_lower, mag_lower_dir),
]:
    print(f"\nStarting {branch_name} branch")

    for branch_index, B in enumerate(B_values):
        Hvec = set_energy_for_B(B)

        driver.drive(system)

        mx, my, mz = system.m.mean()

        rows.append(
            {
                "global_index": global_index,
                "branch": branch_name,
                "branch_index": branch_index,
                "B_T": B,
                "Hx_Apm": Hvec[0],
                "Hy_Apm": Hvec[1],
                "Hz_Apm": Hvec[2],
                "mx_Apm": mx,
                "my_Apm": my,
                "mz_Apm": mz,
                "mx_norm": mx / Ms,
                "my_norm": my / Ms,
                "mz_norm": mz / Ms,
            }
        )

        system.m.to_file(save_dir / f"m_{branch_index + 1:06d}.ovf")

        print(
            f"{branch_name:5s} "
            f"i={branch_index:04d} "
            f"B={B:+.6f} T "
            f"<mz>/Ms={mz / Ms:+.6f}"
        )

        global_index += 1

end = time.perf_counter()

df_table = pd.DataFrame(rows)
df_table.to_csv(hyst_dir / "Hysteresis_upper_lower.txt", sep="\t", index=False)

with open(base_dir / "timing.txt", "w") as f:
    f.write(f"elapsed_wall_clock_s\t{end - start:.6f}\n")
    f.write(f"grid\t{n} {n} {n}\n")
    f.write(f"cell_m\t{cell}\n")
    f.write(f"diameter_m\t{diameter}\n")
    f.write(f"Ms_Apm\t{Ms}\n")
    f.write(f"A_Jpm\t{A}\n")
    f.write(f"Ku_Jpm3\t{Ku}\n")
    f.write("demag\ton\n")

print(f"\nElapsed wall-clock time: {end - start:.3f} s")
print(f"Saved table to: {hyst_dir / 'Hysteresis_upper_lower.txt'}")
