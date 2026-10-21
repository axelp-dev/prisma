# PRISMA Changelogs 

> Describe all the changes and added/deleted/modified features in the project. 

## TODO : 

- [x] Write Mathematics backend on elasticity in `MATHEMATICS.md`. 
- [ ] Implements `trajectory` command. 
- [ ] Implements logs module with PDF reports on trajectory and simulation. 

---

## Unreleased 

### Added
- Linear cytoskeletal elastic restoring force $\vec{F}_{\text{elast}} = -k(\vec{r} - \vec{x}_0)$ in `RK4Overdamped.v_limit`.
- Hookean viscoelastic relaxation timescale $\tau_k = (6\pi\mu R) / k$ computed via `PhysicalSystem.compute_tau_k()`.
- Initial equilibrium anchor vector `x0` stored directly within the frozen `Particle` dataclass.
- Restoring stiffness parameter `k` added to the `Fluid` dataclass (defaults to $0.0\text{ N/m}$).
- CLI entrypoint (`src/cli.py`) exposing the `run` command with custom arguments and predefined presets (`glycerol_bead`, `statolith`).
- Console script hook `prisma = "src.cli:main"` declared in `pyproject.toml`.
- Comprehensive test coverage in `tests/test_physics.py` and `tests/test_solver.py` for viscoelastic relaxation under static gravity.

### Changed
- Aligned `solve` signature across `Solver` and `RK4Overdamped` to take initial position directly from `particle.x0`.
- Streamlined `dependencies` in `pyproject.toml` by removing standard library package `argparse`.
- Updated `ARCHITECTURE.md` and `README.md` to document the CLI pipeline and elasticity model.

### Fixed
- Resolved unbound reference to `self.r_t[0]` in `RK4Overdamped.v_limit` by explicitly using `self.system.particle.x0`.
- Corrected unit inconsistency in the viscoelastic damping formulation by strictly eliminating $m^*$ from the $\frac{k \tau_v}{m^*}$ velocity term.

---

## [v0.1.0] - 2026-10-02

### Added
- Update `ARCHITECTURE.md` and `MATHEMATICS.md` with implemented features. 
- Implements RK4 solver in `solver` module using Python inheritance. Write associated tests. 
- Move `KinematicProfile` into `src/core/physics`. 
- Implements basic simulation elements with Python `@dataclass` (`Particle`, `Fluid`, etc...) and add test file for them. 
- `dev/RK4_solver.ipynb` : Runge-Kunta 4 order solver for movements equations depending on rotation angles and fluids properties. 
- `dev/trajectory.ipynb` : Basic scripts for trajectory generation using Numpy arrays `[timestamp, theta1, theta2]`. Display trajectories plots. 
- `src/core` : import `rpm-stats` core kinematics and backend for gravoty orientation calculus. 
- `test` : import `core` associated tests to prevent from code regression. 