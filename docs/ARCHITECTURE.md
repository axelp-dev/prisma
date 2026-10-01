# PRISMA Architecture 

> This file details all the PRISMA tool architecture. 

## 1. Introduction 

At first, `PRISMA` is separated into 3 modules : 
- `core` defines all the essentials constants and referential frames to modelize and simulate a Random Positonning Machine. 
- `trajectory` implements RPM motors trajectory generation and CSV exports. 
- `solver`: a tool box to simulate the RPM trajectory and process the particle motion in the fluid. 

## 2. Class diagram

We present below a class diagram which represents the structure of the different modules and their interactions. 

```mermaid 
classDiagram
    %% Core & Trajectory
    class Trajectory {
        +ndarray timestamp
        +ndarray theta_1
        +ndarray theta_2
        +from_csv(path: Path) Trajectory$
        +to_csv(path : Path)
        +from_arrays(t, th1, th2) Trajectory$
        +compute_kinematics() KinematicProfile
        +generate(duration_s, step_s)
        +display(path: Path)
    }

    class KinematicProfile {
        +ndarray timestamp
        +ndarray g_b
        +ndarray omega_dot
        +ndarray omega_ddot
        +ndarray omega_1 
        +ndarray omega_2
    }

    Trajectory --> KinematicProfile : produces

    %% Physics
    class Particle {
        +float radius
        +float rho_p
        +float volume
        +float mass
    }

    class Fluid {
        +float rho_f
        +float mu
    }

    class PhysicalSystem {
        +Particle particle
        +Fluid fluid
        +float tau_v
        +float beta
        +float gamma
        +compute_reynolds(v: float) float
        +display()
    }

    PhysicalSystem *-- Particle
    PhysicalSystem *-- Fluid

    %% Solver
    class Simulation {
        +ndarray timestamp
        +ndarray positions
        +ndarray velocities
        +ndarray reynolds
        +bool collision_detected
        +float collision_time
        +plot_3d()
        +to_csv(path: Path)
    }

    class RK4StokesSolver {
        +PhysicalSystem system
        +float r_cuve
        +bool overdamped
        +solve(kinematics: KinematicProfile, x0: ndarray, v0: ndarray) Simulation
    }

    RK4StokesSolver ..> KinematicProfile : uses
    RK4StokesSolver ..> PhysicalSystem : uses
    RK4StokesSolver --> Simulation : produces
```