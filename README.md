# 🦠 PRISMA

> Particle in Random-positioning Integrator for Simulated Microgravity Analysis

---

## 1. Overview

**PRISMA** models the hydrodynamic transport and trajectory of spherical inclusions (macroscopic test beads, single cells, or intracellular organelles such as statoliths) subjected to the *non-inertial kinematics* of a biaxial **Random Positioning Machine**.

The engine leverages an asymptotic reduction to the **overdamped Stokes regime** ($Re_p \ll 1$), bypassing numerical stiffness associated with small viscous relaxation timescales ($\tau_v \sim 10^{-6}\text{ s}$ to $10^{-3}\text{ s}$) while maintaining physical fidelity via an explicit 4th-order Runge-Kutta scheme (RK4).

---

## 2. Key Features

- **Vectorized Biaxial Kinematics:** Full rotation matrix mappings, apparent gravity transformations, and non-inertial angular velocity/acceleration tracking in the moving frame $\mathcal{R}_2$.
- **Overdamped Stokes Solver:** Unconditionally stable first-order integration ($\dot{\vec{r}} = \vec{v}_{\text{limit}}$) under coupled gravity, centrifugal, and Euler fictitious forces.
- **Microgravity Verification Metrics:** Continuous tracking of the particle Reynolds number ($Re_p$) to systematically validate the creeping-flow assumption.
- **Modular Architecture:** Decoupled layout separating physical models, trajectory import/export, and numerical solvers.

---

## 3. Architecture & Data Pipeline

The package enforces a strict one-way dependency model:

```text
src/core/ (conventions, kinematics, physical models)
    ▲
    │
src/trajectory/ (motor angle profiles, CSV parsing, KinematicProfile generation)
    ▲
    │
src/solver/ (RK4 integration, physical regimes, boundary enforcement)
```

---

## 4. Pipeline Flow

```txt 
CSV Trajectory [timestamp, theta1, theta2]
                │
                ▼ (Trajectory.from_csv)
    Trajectory.compute_kinematics()
                │
                ▼
         KinematicProfile
                │
                ├───► RK4Overdamped.solve(system, kin, x0, v0)
                │         ├── Local evaluation of v_limit(r, g, w, dw)
                │         ├── 4th-order Runge-Kutta step (fixed dt)
                │         └── Instantaneous Re_p computation
                ▼
         SimulationResult
                │
                ▼
  3D Trajectory Visualization & Microgravity Confinement Analysis
```

For in-depth software design and physical derivations, see:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Class hierarchy, module contracts, and data containers.
- [docs/MATHEMATICS.md](docs/MATHEMATICS.md): Derivation of non-inertial equations of motion and Stokes regime scaling.

---

## 5. Project Structure 

```txt 
.
├── CHANGELOG.md             # Project release and modification history
├── data/
│   └── trajectories/        # Biaxial RPM angle trajectories (.csv)
├── dev/                     # Prototyping notebooks (solvers, kinematics)
├── docs/                    # Mathematical formulations and architectural specs
├── pyproject.toml           # Project metadata and dependencies
├── README.md
├── src/
│   ├── core/                # Conventions, 2-axis kinematics, physics dataclasses
│   ├── solver/              # Numerical integration engines (Solver, RK4Overdamped)
│   ├── trajectory/          # Trajectory loading, export, and kinematics pipeline
│   └── utils.py             # CSV header and metadata parsers
└── tests/                   # Pytest test suite
```

--- 

## 6. Getting Started 

Start by cloning the repo: 
```bash
git clone git@github.com:axelp-dev/prisma.git
```
and then create a Python environment to install required packages: 
```bash 
cd prisma                           # Move to project folder
python3 -m venv .venv               # Create empty Python venv
source .venv/bin/activate           # Activate venv 
pip install -r requirements.txt     # Install required packages
```
Finish by importing `pyproject.toml` config to run notebooks in `dev`: 
```bash 
pip install -e .
```
