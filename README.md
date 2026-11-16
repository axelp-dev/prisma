# 🦠 PRISMA

> **P**article in **R**andom-positioning **I**ntegrator for **S**imulated **M**icrogravity **A**nalysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

---

- [🦠 PRISMA](#-prisma)
  - [1. Overview](#1-overview)
    - [1.1 Scientific Context](#11-scientific-context)
    - [1.2 Key Features](#12-key-features)
  - [2. Architecture \& Data Pipeline](#2-architecture--data-pipeline)
    - [2.1 Classes](#21-classes)
  - [2.2 Execution Pipeline](#22-execution-pipeline)
  - [2.3 Project Structure](#23-project-structure)
  - [3. Getting Started](#3-getting-started)
    - [3.1 Installation](#31-installation)
    - [3.2 CLI Usage](#32-cli-usage)
      - [3.2.1 Inspect and Plot Trajectories (`prisma trajectory`)](#321-inspect-and-plot-trajectories-prisma-trajectory)
      - [3.3.3 Generate motor profile (`prisma trajectory generate`)](#333-generate-motor-profile-prisma-trajectory-generate)
      - [3.3.4 Run Physical Numerical Simulation (`prisma run`)](#334-run-physical-numerical-simulation-prisma-run)
      - [3.3.5 Generate report from a CSV `SimulationResult` dump (`prisma result show`)](#335-generate-report-from-a-csv-simulationresult-dump-prisma-result-show)
    - [3.4 Running tests](#34-running-tests)


## 1. Overview

### 1.1 Scientific Context

**PRISMA** simulates the dynamics of microscopic intracellular inclusions (such as plant statoliths) enclosed within a fluid-filled cavity mounted on a biaxial **Random Positioning Machine (RPM)**. 

By continuously altering the orientation of two gimbal axes, the RPM averages the laboratory gravitational vector over time, generating functional microgravity analogs. PRISMA tracks the full non-inertial equations of motion in the moving sample frame $\mathcal{R}_2$, resolving coupled gravitational, centrifugal, Euler, and viscoelastic restoring forces within an overdamped Stokes hydrodynamic regime.

Detailed physical derivations and reference frame conventions are documented in [docs/MATHEMATICS.md](docs/MATHEMATICS.md).

### 1.2 Key Features

- **Vectorized Biaxial Kinematics:** Full rotation matrix mappings, apparent gravity transformations, and non-inertial angular velocity/acceleration tracking in frame $\mathcal{R}_2$.
- **Analytical & Stochastic Presets:** Six kinematic generators (`random_walk`, `desynchronized_sine`, `constant_speed_ratio`, `static_1g`, `clinostat_1d`, `centrifuge_sweep`).
- **Overdamped Stokes Solver:** Unconditionally stable numerical integration ($\dot{\vec{r}} = \vec{v}_{\text{limit}}$) under coupled apparent gravity and inertial fictitious forces.
- **Cytoskeletal Viscoelasticity:** Hookean restoring force ($\vec{F}_{\text{elast}} = -k(\vec{r} - \vec{x}_0)$) parameterized by the elastic relaxation timescale $\tau_k = (6\pi\mu R)/k$.
- **Creeping-Flow Verification:** Continuous evaluation of the particle Reynolds number ($Re_p < 0.1$) guaranteeing Stokes regime validity.
- **Comprehensive Vector Reporting:** Automated generation of 3-page publication-quality PDF reports covering spherical surface coverage (Mollweide projection), motor kinematics, spectral response, and confinement dynamics.
- **Unified Configuration Contracts:** Decoupled architecture using `TrajectoryConfig` and `SimulationConfig` dataclasses.

---

## 2. Architecture & Data Pipeline

Here are presented the project architecture and a brief introduction on the data pipeline for a simulation run. 

### 2.1 Classes

The package enforces a strict one-way dependency model:

```text
src/config.py (TrajectoryConfig, SimulationConfig, presets)
    ▲
    │
src/core/ (conventions, kinematics, passive dataclasses)
    ▲
    │
src/trajectory/ (Trajectory orchestrator, profile generators)
    ▲
    │
src/solver/ (RK4 solver, boundary clamping)
    ▲
    │
src/stats/ (metrics, plotting, PDF report assemblers)
    ▲
    │
src/cli.py (argparse command dispatching)
```

## 2.2 Execution Pipeline 

A standard PRISMA workflow consists of:
1. **Configuring execution** parameters into a `TrajectoryConfig` or `SimulationConfig`.
2. **Generating or Loading** motor angles ($\theta_1, \theta_2$) via `Trajectory`.
3. **Computing Kinematics** to derive $\vec{g}_{\mathcal{R}_2}(t)$, $\vec{\Omega}_{\mathcal{R}_2}(t)$, and $\dot{\vec{\Omega}}_{\mathcal{R}_2}(t)$.
4. **Solving Dynamics** using RK4Overdamped with boundary wall confinement.Serializing Outputs to self-describing CSV files and multi-page vector PDF reports.For a deeper dive into the class hierarchy and design patterns, see docs/ARCHITECTURE.md.


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
    ┌───────────└─────────┐
    │                     │
    ▼                     │
CSV Export                │
                          │
                          ▼
                     PDF Export
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
│   ├── stats/               # PDF Generation (Simulation & Trajectory)
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

Below are some examples of the `prisma` command and presets config using. 

#### 3.2.1 Inspect and Plot Trajectories (`prisma trajectory`)

```bash
# Print summary metrics (residual gravity, max speeds, duration)
prisma trajectory show -i data/trajectories/traj3_biaxial_desynchro.csv

# Show CLI trajectory and export PDF report in given --report filepath
prisma trajectory show -i data/trajectories/traj3_biaxial_desynchro.csv --report data/trajectories/traj3.pdf
```

#### 3.3.3 Generate motor profile (`prisma trajectory generate`)

```bash 
# Generate a 120-second random walk trajectory
prisma trajectory generate -o data/trajectories/traj_random_walk.csv -d 120 --dt 0.01 --profile random_walk

# Generate a 120-second centrifugal sweep trajectory and compile associated PDF report
prisma trajectory generate -o data/trajectories/traj_desynchro.csv -d 120 --dt 0.01 --profile centrifugal_sweep --log-report
```

#### 3.3.4 Run Physical Numerical Simulation (`prisma run`)

```bash 
# Run with the calibrated macroscopic glycerol preset
prisma run -i data/trajectories/traj3_biaxial_desynchro.csv -p glycerol_bead -o results.csv

# Run with the intracellular statolith preset and custom actin stiffness
prisma run -i data/trajectories/traj3_biaxial_desynchro.csv -p statolith -k 2e-4 --x0 0.0 0.0 1e-6

# Run with the intracellular statolith preset and generate a SimulationReport into given --report PDF filepath
prisma run -i data/trajectories/traj3_biaxial_desynchro.csv --report data/results/result_PDF_traj3.pdf
```

#### 3.3.5 Generate report from a CSV `SimulationResult` dump (`prisma result show`)

```bash 
# Show Matplotlib figures from existing CSV SimulationReport dump 
prisma result show -i <csv_dump_filepath> --plot

# Generate PDF report from existing CSV SimulationReport dump 
prisma result show -i  <csv_dump_filepath> --plot --report <exporting-pdf-filepath.pdf> 
```

### 3.4 Running tests

A complete `pytest` suite is maintained in the `test/` module and can be launched using : 

```bash 
pytest -q 
```