# PRISMA Changelogs 

> Describe all the changes and added/deleted/modified features in the project. 

## Roadmap & Active Work

- [x] Write mathematics backend on viscoelastic Hookean damping in `MATHEMATICS.md`.
- [x] Implement unified `TrajectoryConfig` container and decouple trajectory reporting.
- [x] Refactor CLI around two primary subcommands: `prisma trajectory` and `prisma simulation`.
- [x] Implement multi-page PDF generation for trajectories with Mollweide density projection.
- [x] Implement analytical profile presets (`random_walk`, `desynchronized_sine`, `constant_speed_ratio`, `static_1g`, `clinostat_1d`, `centrifuge_sweep`).
- [ ] Implement unified `Simulation` orchestrator lifecycle (`launch` & `show`) consuming `SimulationConfig`.
- [ ] Implement inelastic wall boundary condition (geometric clamping and normal velocity suppression) in RK4 solver.

---

## [Unreleased]

### Added
- **Unified Configuration Layer (`src/config.py`)**:
  - Introduced `Config` base class and specialized `TrajectoryConfig` and `SimulationConfig` dataclasses.
  - Implemented human-readable terminal rendering for `TrajectoryConfig` via a customized `__str__` method.
  - Consolidated physical presets (`statolith`, `glycerol_bead`) directly inside `src/config.py`.
- **Streamlined Trajectory Architecture (`src/trajectory/Trajectory.py`)**:
  - Transferred execution orchestration to `Trajectory.generate()` and `Trajectory.show()`.
  - Added structured metadata serialization (`# profile`, `# description`, `# duration_s`, `# step_s`, `# date`) in trajectory CSV headers.
  - Added robust CSV deserialization in `_from_csv()` synchronizing timing and metadata into the active configuration.
- **Kinematic Presets Suite (`src/trajectory/generators.py`)**:
  - Implemented six standard generation profiles: `random_walk`, `desynchronized_sine`, `constant_speed_ratio`, `static_1g`, `clinostat_1d`, and `centrifuge_sweep`.
  - Integrated discrete cumulative stepping (`np.cumsum(omega) * dt`) and closed-form harmonic solutions.
- **Reporting Inversion (`src/stats/trajectory_report.py`, `src/stats/simulation_report.py`)**:
  - Refactored `TrajectoryReport` and `SimulationReport` to inherit from `Report(config)`.
  - Inverted execution flow: `Trajectory` now passes its pre-computed `KinematicProfile` directly to `TrajectoryReport`.
  - Removed deprecated `TrajectoryReport.from_csv()` factory method.
- **Physics & Solver Foundations**:
  - Linear cytoskeletal elastic restoring force $\vec{F}_{\text{elast}} = -k(\vec{r} - \vec{x}_0)$ in `RK4Overdamped.v_limit`.
  - Hookean viscoelastic relaxation timescale $\tau_k = (6\pi\mu R) / k$ computed via `PhysicalSystem.compute_tau_k()`.
  - Initial equilibrium anchor vector `x0` stored directly within the frozen `Particle` dataclass.
  - Comprehensive test coverage in `tests/test_physics.py`, `tests/test_solver.py`, `tests/test_trajectory.py`, and `tests/test_simulation.py`.

### Changed
- **CLI Unification (`src/cli.py`)**:
  - Replaced legacy commands (`run`, `result`) with a clean two-level hierarchy: `prisma trajectory {generate,show}` and `prisma simulation {launch,show}`.
  - Added `-l` / `--log-report` option to automatically compile side-car PDF reports alongside CSV exports.
  - Cleaned up subparser namespaces to avoid destination collisions (`trajectory_command`, `simulation_command`).
- **Visual & Reporting Enhancements**:
  - Switched Mollweide spherical projection to `PowerNorm` gamma scaling with masked zero-density elements for high visual clarity.
  - Set auto-zoom on particle trajectory in `render_particle_3d_confinement` (`src/stats/plotting.py`).
  - Replaced raw LaTeX math text strings (`\mu\mathrm{m}`) with Unicode symbols (`µm`) to prevent font engine rendering errors on standard Matplotlib backends.
- **Build & Packaging (`pyproject.toml`)**:
  - Streamlined `dependencies` by removing standard library package `argparse`.

### Fixed
- Resolved unbound reference to `self.r_t[0]` in `RK4Overdamped.v_limit` by explicitly using `self.system.particle.x0`.
- Corrected unit inconsistency in the viscoelastic damping formulation by strictly eliminating $m^*$ from the $\frac{k \tau_v}{m^*}$ velocity term.
- Fixed string-to-`Path` conversion in `convert_to_pdf_path` (`src/utils.py`).

### Removed
- **Legacy Result Command**: Deprecated `prisma result show`; post-processing and diagnostic display are now consolidated under `prisma simulation show`.
- **Redundant Report Modules**: Removed obsolete duplicated reporting files (`report_2.py`, `trajectory_report_2.py`).

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