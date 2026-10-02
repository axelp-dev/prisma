# PRISMA Changelogs 

> Describe all the changes and added/deleted/modified features in the project. 

---

## Unreleased 

### Changed 

### Added
- Move `KinematicProfile` into `src/core/physics`. 
- Implements basic simulation elements with Python `@dataclass` (`Particle`, `Fluid`, etc...) and add test file for them. 
- `dev/RK4_solver.ipynb` : Runge-Kunta 4 order solver for movements equations depending on rotation angles and fluids properties. 
- `dev/trajectory.ipynb` : Basic scripts for trajectory generation using Numpy arrays `[timestamp, theta1, theta2]`. Display trajectories plots. 
- `src/core` : import `rpm-stats` core kinematics and backend for gravoty orientation calculus. 
- `test` : import `core` associated tests to prevent from code regression. 

### Removed 

### Fixed