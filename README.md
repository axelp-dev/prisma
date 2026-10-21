# 🦠 PRISMA

> Particle in Random-positioning Integrator for Simulated Microgravity Analysis

---

- [🦠 PRISMA](#-prisma)
  - [1. Overview](#1-overview)
    - [1.1 Summary](#11-summary)
    - [1.2 Key Features](#12-key-features)
  - [2. Architecture \& Data Pipeline](#2-architecture--data-pipeline)
    - [2.1 Classes](#21-classes)
  - [2.2 Pipeline Flow](#22-pipeline-flow)
  - [2.3 Project Structure](#23-project-structure)
  - [3. Getting Started](#3-getting-started)
    - [3.1 Installation](#31-installation)
    - [3.2 CLI Usage](#32-cli-usage)
    - [3.3 Running tests](#33-running-tests)


## 1. Overview

### 1.1 Summary

**PRISMA** models the motions of intracellular organelles such as statoliths motion inside a cell while using a biaxial *Radom Positonning Machine* to simulation altered gravity or micro-gravity. 

The engine leverages a `RK4Stokes` solver on the motion equations using Centrifugal, Coriolis, Euler, Buoyant and Elasticity forces. Calculus and references frames are presented in the related doc file : [docs/MATHEMATICS.md](docs/MATHEMATICS.md). 

### 1.2 Key Features

- **Vectorized Biaxial Kinematics:** Full rotation matrix mappings, apparent gravity transformations, and non-inertial angular velocity/acceleration tracking in the moving frame $\mathcal{R}_2$.
- **Overdamped Stokes Solver:** Unconditionally stable first-order integration ($\dot{\vec{r}} = \vec{v}_{\text{limit}}$) under coupled gravity, centrifugal, and Euler fictitious forces.
- **Cytoskeletal Viscoelasticity:** Restoring Hookean coupling ($\vec{F}_{\text{elast}} = -k(\vec{r} - \vec{x}_0)$) parameterized by the elastic relaxation timescale $\tau_k = (6\pi\mu R)/k$.
- **Microgravity Verification Metrics:** Continuous tracking of the particle Reynolds number ($Re_p$) to systematically validate the creeping-flow assumption.
- **Dedicated CLI Pipeline:** Modular command-line tool `prisma` to configure presets, override physical parameters, and serialize results.
- **Modular Architecture:** Decoupled layout separating physical models, trajectory import/export, and numerical solvers.

---

## 2. Architecture & Data Pipeline

Here are presented the project architecture and a brief introduction on the data pipeline for a simulation run. 

### 2.1 Classes

The package enforces a strict one-way dependency model:

```text
src/core/ (conventions, kinematics, physical models)
    ▲
    │
src/trajectory/ (motor angle profiles, CSV parsing, KinematicProfile generation)
    ▲
    │
src/solver/ (RK4 integration, physical regimes, boundary enforcement)
    ▲
    │
src/cli.py (command-line orchestration, preset management, I/O)
```

## 2.2 Pipeline Flow

A simulation `run` calls all the modules independantly from the CLI wrapper in `src/cli.py` : 
1. `Trajectory` is loaded using CSV filepath or generated.
2. `Trajectory.compute_kinematics()` compute the associated values to the trajectory to pre-compute solver values. 
3. `KinematicProfile` is instanciated from the preious object and the selected `Solver` compute the trajectory from the RPM trajectory stored in `Trajectory`. 
4. A `SimulationResult` can be saved or plotted at the end of the solving process. 

```txt 
CSV Trajectory [timestamp, theta1, theta2]
                │
                ▼ (Trajectory.from_csv)
    Trajectory.compute_kinematics()
                │
                ▼
         KinematicProfile
                │
                ├───► RK4Overdamped.solve(kin, v0)
                │         ├── Local evaluation of v_limit(r, g, w, dw)
                │         │     └── Hydrodynamic + Centrifugal + Euler + Elasticity
                │         ├── 4th-order Runge-Kutta step (fixed dt)
                │         └── Instantaneous Re_p computation
                ▼
         SimulationResult
                │
                ▼
  CSV Export / 3D Trajectory Visualization / Residual Acceleration Metrics
```

For in-depth software design and physical derivations, see:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Class hierarchy, module contracts, and data containers.
- [docs/MATHEMATICS.md](docs/MATHEMATICS.md): Derivation of non-inertial equations of motion and Stokes regime scaling.

## 2.3 Project Structure 

The previous chart presented the data pipeline, below are presented the physical architecture of the project where all classes are defined. 

```txt 
.
├── CHANGELOG.md             # Project release and modification history
├── data/
│   └── trajectories/        # Biaxial RPM angle trajectories (.csv)
├── dev/                     # Prototyping notebooks (solvers, kinematics)
├── docs/                    # Mathematical formulations and architectural specs
├── pyproject.toml           # Project metadata, CLI entrypoints, and dependencies
├── README.md
├── src/
│   ├── cli.py               # Command-line interface and run launcher
│   ├── core/                # Conventions, 2-axis kinematics, physics dataclasses
│   ├── solver/              # Numerical integration engines (Solver, RK4Overdamped)
│   ├── trajectory/          # Trajectory loading, export, and kinematics pipeline
│   └── utils.py             # CSV header and metadata parsers
└── tests/                   # Pytest test suite
```

--- 

## 3. Getting Started 

### 3.1 Installation 

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

### 3.2 CLI Usage 

Below are some examples of the `prisma run` command and presets config using. 

```bash 
# Run with the calibrated macroscopic glycerol preset
prisma run -i data/trajectories/traj3_biaxial_desynchro.csv -p glycerol_bead -o results.csv

# Run with the intracellular statolith preset and custom actin stiffness
prisma run -i data/trajectories/traj3_biaxial_desynchro.csv -p statolith -k 2e-4 --x0 0.0 0.0 1e-6

# Inspect available CLI arguments
prisma run --help
```

### 3.3 Running tests

A complete `pytest` suite is maintained in the `test/` module and can be launched using : 

```bash 
pytest -q 
```