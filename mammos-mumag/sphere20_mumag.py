from pathlib import Path

import mammos_entity as me
import mammos_units as u

from mammos_mumag.materials import Materials
from mammos_mumag.mesh import Mesh
from mammos_mumag.parameters import Parameters
from mammos_mumag.simulation import Simulation


eq = u.magnetic_flux_field()

mesh = Mesh("sphere20_air_shell.fly")

materials = Materials(
    domains=[
        {  # iron sphere, tag 1
            "theta": 0.0,
            "phi": 0.0,
            "K1": me.Ku(4.8e4, unit=u.J / u.m**3),
            "Ms": me.Ms(1.7e6, unit=u.A / u.m),
            "A": me.A(1.0e-11, unit=u.J / u.m),
        },
        {  # non-magnetic air region, tag 2
            "theta": 0.0,
            "phi": 0.0,
            "K1": me.Ku(0.0, unit=u.J / u.m**3),
            "Ms": me.Ms(0.0, unit=u.A / u.m),
            "A": me.A(0.0, unit=u.J / u.m),
        },
        {  # outer spherical shell for open-boundary magnetostatics, tag 3
            "theta": 0.0,
            "phi": 0.0,
            "K1": me.Ku(0.0, unit=u.J / u.m**3),
            "Ms": me.Ms(0.0, unit=u.A / u.m),
            "A": me.A(0.0, unit=u.J / u.m),
        },
    ],
)

parameters = Parameters(
    size=1.0e-9,
    scale=0,
    m_vect=[0.0, 0.0, 1.0],
    h_start=(1.0 * u.T).to(u.A / u.m, equivalencies=eq),
    h_final=(-1.0 * u.T).to(u.A / u.m, equivalencies=eq),
    h_step=(-0.005 * u.T).to(u.A / u.m, equivalencies=eq),
    h_vect=[0.0, 0.0, 1.0],
    m_step=(0.01 * u.T).to(u.A / u.m, equivalencies=eq),
    m_final=(-3.0 * u.T).to(u.A / u.m, equivalencies=eq),
    tol_fun=1e-10,
    tol_h_mag_factor=1,
    precond_iter=10,
)

sim = Simulation(mesh=mesh, materials=materials, parameters=parameters)
sim.run_loop(outdir=Path("out/iron_sphere_air_shell_loop_new"), name="sphere20")
