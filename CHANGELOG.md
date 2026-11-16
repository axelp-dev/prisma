# PRISMA Changelogs 

> Describe all the changes and added/deleted/modified features in the project. 

## Roadmap & Active Work

- [x] Write mathematics backend on viscoelastic Hookean damping in `MATHEMATICS.md`.
- [x] Implement unified `TrajectoryConfig` container and decouple trajectory reporting.
- [x] Refactor CLI around two primary subcommands: `prisma trajectory` and `prisma simulation`.
- [x] Implement multi-page PDF generation for trajectories with Mollweide density projection.
- [x] Implement analytical profile presets (`random_walk`, `desynchronized_sine`, `constant_speed_ratio`, `static_1g`, `clinostat_1d`, `centrifuge_sweep`).
- [ ] Implement unified `Simulation` orchestrator class consuming `SimulationConfig`.


---

## Unreleased 

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
- **Reporting Inversion (`src/stats/trajectory_report.py`)**:
  - Refactored `TrajectoryReport` to inherit from `Report(config)`.
  - Inverted execution flow: `Trajectory` now passes its pre-computed `KinematicProfile` directly to `TrajectoryReport`.
  - Removed deprecated `TrajectoryReport.from_csv()` factory method.

- Add bouncing effect on particule on the cell structure. Use simple deviation towards the normal from the impact point. 
- Trajectory generators: 
  - Define different trajectory profiles and their generator functions in `src/trajectory/generators.py` using `PROFILE` dict. 
  - Branch `Trajectory.generate()` method on `cli.py` wrapper using `prisma trajectory generate` command. 
  - Add a `--log-report` flag to the `generate` command which compile the PDF report next to export CSV trajectory. 
- Branching `SimulationReport` on cli wrapper in `cli./py`. 
- Implement simulation report in `SimulationReport.py`. 
- Include metrics and plotting functions for simulation report in `metrics.py` and `plotting.py`. 
- Branching `TrajectoryReport` on cli wrapper in `cli.py`. 
- Stats module wrapper with abstract `Report` class defining `TrajectoryReport` one. Implements generations methods using `metrics.py` and `plotting.py`. 
- `plotting.py` and `metrics.py` helpers for `TrajectoryReport` in new `src.stats` module. 
- Nested CLI subcommands under `prisma trajectory`:
  - `prisma trajectory show`: parses motor CSV, computes apparent gravity $\vec{g}_{\mathcal{R}_2}$, displays diagnostic metrics in console, and provides interactive 4-panel matplotlib plots (`--plot`).
  - `prisma trajectory generate`: synthesizes harmonic and constant angular speed profiles (`--mode`), writes metadata headers, and outputs clean CSV files.
- Linear cytoskeletal elastic restoring force $\vec{F}_{\text{elast}} = -k(\vec{r} - \vec{x}_0)$ in `RK4Overdamped.v_limit`.
- Hookean viscoelastic relaxation timescale $\tau_k = (6\pi\mu R) / k$ computed via `PhysicalSystem.compute_tau_k()`.
- Initial equilibrium anchor vector `x0` stored directly within the frozen `Particle` dataclass.
- Restoring stiffness parameter `k` added to the `Fluid` dataclass (defaults to $0.0\text{ N/m}$).
- CLI entrypoint (`src/cli.py`) exposing the `run` command with custom arguments and predefined presets (`glycerol_bead`, `statolith`).
- Console script hook `prisma = "src.cli:main"` declared in `pyproject.toml`.
- Comprehensive test coverage in `tests/test_physics.py` and `tests/test_solver.py` for viscoelastic relaxation under static gravity.

### Changed
- **CLI Unification (`src/cli.py`)**:
  - Replaced legacy commands (`run`, `result`) with a clean two-level hierarchy: `prisma trajectory {generate,show}` and `prisma simulation {run,show}`.
  - Added `-l` / `--log-report` option to automatically compile side-car PDF reports alongside CSV exports.
  - Cleaned up subparser namespaces to avoid destination collisions (`trajectory_command`, `simulation_command`).
- **Visual & Reporting Enhancements**:
  - Switched Mollweide spherical projection to `PowerNorm` gamma scaling with masked zero-density elements for high visual clarity.
  - Replaced raw LaTeX math text strings (`\mu\mathrm{m}`) with Unicode symbols (`µm`) to prevent font engine rendering errors on standard Matplotlib backends.
- Set auto-zoom on particle's trajectory in `render_particle_3d_confinement` function on `src/stats/plotting.py`. 
- Refactored `cli.py` to remove `--plot` option from `prisma trajectory show` command and disable plot display. 
- Refactored `init_run` and `init_trajectory` parser initialization routines to use independent subparser instances.
- Aligned `solve` signature across `Solver` and `RK4Overdamped` to take initial position directly from `particle.x0`.
- Streamlined `dependencies` in `pyproject.toml` by removing standard library package `argparse`.
- Updated `ARCHITECTURE.md` and `README.md` to document the CLI pipeline and elasticity model.

### Fixed
- Changing `render_mollweide_heatmap` colors in Trajectory report. 
- Resolved unbound reference to `self.r_t[0]` in `RK4Overdamped.v_limit` by explicitly using `self.system.particle.x0`.
- Corrected unit inconsistency in the viscoelastic damping formulation by strictly eliminating $m^*$ from the $\frac{k \tau_v}{m^*}$ velocity term.

## Removed 
- **Legacy Result Command**: Deprecated `prisma result show`; post-processing and diagnostic display are now consolidated under `prisma simulation show`.


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