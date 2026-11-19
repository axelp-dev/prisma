# 🦠 PRISMA

> **P**article in **R**andom-positioning **I**ntegrator for **S**imulated **M**icrogravity **A**nalysis
> **Version**: v0.2.0

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
      - [3.2.1 Trajectory module (`prisma trajectory`)](#321-trajectory-module-prisma-trajectory)
        - [Generate a trajectory using templates (`trajectory generate`)](#generate-a-trajectory-using-templates-trajectory-generate)
        - [Inspect an existing trajectory (`prisma trajectory show`)](#inspect-an-existing-trajectory-prisma-trajectory-show)
      - [3.2.2 Run Physical Numerical Simulation (`prisma simulation`)](#322-run-physical-numerical-simulation-prisma-simulation)
        - [Launch dynnamic numerical simulation](#launch-dynnamic-numerical-simulation)
      - [Inspect an existing simulation result (show)](#inspect-an-existing-simulation-result-show)
    - [3.3 Running tests](#33-running-tests)

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
4. **Solving Dynamics** using `RK4Overdamped` with boundary wall confinement.
5. **Serializing Outputs** to self-describing CSV files and multi-page vector PDF reports.

```txt
CLI: prisma simulation launch / show
               │
               ▼
       SimulationConfig (or Simulation.from_csv)
               │
               ▼
          Simulation
     ┌─────────┴─────────┐
     │                   │
     ▼ (launch)          ▼ (show)
_load_trajectory()    from_csv() (parses header & SimulationResult)
     │                   │
     ▼                   │
_build_physical_system() │
     │                   │
     ▼                   │
RK4Overdamped.solve()    │
     │                   │
     ▼                   │
  _to_CSV()              │
     │                   │
     └─────────┬─────────┘
               │
               ▼ (if log_report or show)
       SimulationReport
         ├── _compute_metrics() (Re_p, drift, tortuosity, FFT, confinement)
         ├── _generate_plots() (3D confinement, dynamics, phase/FFT)
         ├── _assemble_pdf()
         └── _show_CLI()
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
│   ├── results/             # Simulation output CSVs and PDF reports
│   └── trajectories/        # Biaxial RPM angle trajectories (.csv)
├── dev/                     # Prototyping notebooks (solvers, kinematics)
├── docs/                    # Mathematical formulations and architectural specs
├── pyproject.toml           # Project metadata, CLI entrypoints, and dependencies
├── README.md
├── src/
│   ├── cli.py               # Command-line interface and command launcher
│   ├── config.py            # Unified TrajectoryConfig and SimulationConfig contracts
│   ├── core/                # Conventions, 2-axis kinematics, physics dataclasses
│   ├── simulation/          # Simulation orchestrator and RK4Overdamped solver
│   ├── trajectory/          # Trajectory loading, export, and kinematics pipeline
│   ├── stats/               # PDF Generation (Simulation & Trajectory)
│   └── utils.py             # CSV header parsers and path utilities
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

Finish by importing `pyproject.toml` configuration to run notebooks in `dev`:

```bash
pip install -e .
```

### 3.2 CLI Usage

The CLI is structured into two main command suites: trajectory and simulation.

#### 3.2.1 Trajectory module (`prisma trajectory`)

##### Generate a trajectory using templates (`trajectory generate`)

```bash
prisma trajectory generate -o <output_path> [options]
```

| Option | Type | Required | Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `-o`, `--output` | `PATH` | **Yes** | — | Destination path for the generated trajectory CSV file. |
| `-p`, `--profile` | `STR` | No | `random_walk` | Kinematic preset (`random_walk`, `desynchronized_sine`, `constant_speed_ratio`, `static_1g`, `clinostat_1d`, `centrifuge_sweep`). |
| `-d`, `--duration` | `FLOAT` | No | `60.0` | Total trajectory duration in seconds. |
| `-s`, `--step` | `FLOAT` | No | `1.0` | Discretization time step $\Delta t$ between two points in seconds. |
| `-t`, `--description-text` | `STR` | No | `None` | Custom description metadata injected into the CSV header. |
| `-l`, `--log-report` | `FLAG` | No | `False` | Automatically compile a 3-page side-car PDF diagnostic report alongside the CSV. |

**Examples :**

```bash
# Generate 10-minute random walk with 100 Hz sampling and side-car PDF report
prisma trajectory generate -o data/trajectories/random_walk_10m.csv -p random_walk -d 600 -s 0.01 -l

# Generate 2D clinostat test profile
prisma trajectory generate -o data/trajectories/clinostat_1d_10m.csv -p clinostat_1d -d 600 -s 0.01
```

##### Inspect an existing trajectory (`prisma trajectory show`)

```bash
prisma trajectory show -i <input_path> [-o <report_path>]
```

| Option | Type | Required | Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `-i`, `--input` | `PATH` | **Yes** | — | Path to the existing trajectory CSV file. |
| `-o`, `--output` | `PATH` | No | `<input>.pdf` | Custom destination path for the compiled 3-page PDF report. |

**Example :**

```bash
prisma trajectory show -i data/trajectories/random_walk_10m.csv
```

#### 3.2.2 Run Physical Numerical Simulation (`prisma simulation`)

##### Launch dynnamic numerical simulation

```bash
prisma simulation launch -i <trajectory_csv> -o <result_csv> [options]
```

| Category | Option | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **I/O** | `-i`, `--input` | `PATH` | **Yes** | — | Path to the input motor trajectory CSV file. |
| **I/O** | `-o`, `--output` | `PATH` | No | `None` | Destination path for the resolved particle trajectory CSV file. |
| **I/O** | `--log-report` | `FLAG` | No | `False` | Automatically compile a 3-page side-car PDF simulation report. |
| **Time** | `-d`, `--duration` | `FLOAT` | No | `120` | Simulation duration in seconds (defaults to trajectory length). |
| **Time** | `--dt` | `FLOAT` | No | `0.1` | Numerical integration time step in seconds. |
| **Preset** | `-p`, `--preset` | `STR` | No | `None` | Predefined physical configuration (`glycerol_bead` or `statolith`). |
| **Initial** | `--x0` | `FLOAT[3]` | No | `[0.0, 0.0, 0.0]` | Initial equilibrium anchor coordinates `(X, Y, Z)` in sample frame $\mathcal{R}_2$ (in meters). |
| **Physics** | `-r`, `--radius` | `FLOAT` | No | `1.5e-3` | Inclusion radius in meters. |
| **Physics** | `--rho` | `FLOAT` | No | `1202.0` | Particle density in $\text{kg/m}^3$. |
| **Physics** | `--rho-f` | `FLOAT` | No | `1200.0` | Surrounding fluid density in $\text{kg/m}^3$. |
| **Physics** | `--mu-f` | `FLOAT` | No | `1.412` | Fluid dynamic viscosity in $\text{Pa}\cdot\text{s}$. |
| **Physics** | `-k`, `--elasticity` | `FLOAT` | No | `0.0` | Cytoskeletal actin restoring stiffness in $\text{N/m}$. |
| **Physics** | `-rt`, `--tube-radius` | `FLOAT` | No | `0.05` | Spherical confinement cell/tube radius in meters. |

**Examples :**

```bash
# Run statolith simulation with actin restoring stiffness and generate report
prisma simulation launch -i data/trajectories/constant_speed_10m.csv -o data/results/sim_statolith.csv -p statolith -k 1e-4 --log-report

# Run macroscopic glycerol bead test without elastic anchoring
prisma simulation launch -i data/trajectories/random_walk_10m.csv -o data/results/sim_bead.csv -p glycerol_bead --log-report
```

#### Inspect an existing simulation result (show)

```bash
prisma simulation show -i <result_csv> [-o <report_path>]
```

Reads physical metadata and trajectory parameters directly from the CSV comments header to generate diagnostics and assemble the 3-page summary PDF report.

| Option | Type | Required | Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `-i`, `--input` | `PATH` | **Yes** | — | Path to the existing simulation result CSV file. |
| `-o`, `--output` | `PATH` | No | `<input>.pdf` | Custom destination path for the compiled 3-page PDF report. |

### 3.3 Running tests

A complete `pytest` suite is maintained in the `test/` module and can be launched using :

```bash
pytest -q 
```
