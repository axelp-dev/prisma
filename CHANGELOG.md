# PRISMA Changelogs 

> Describe all the changes and added/deleted/modified features in the project. 

---

## Unreleased 

### Changed 

### Added
- Update `ARCHITECTURE.md` and `MATHEMATICS.md` with implemented features. 
- `dev/RK4_solver.ipynb` : Runge-Kunta 4 order solver for movements equations depending on rotation angles and fluids properties. 
- `dev/trajectory.ipynb` : Basic scripts for trajectory generation using Numpy arrays `[timestamp, theta1, theta2]`. Display trajectories plots. 
- `src/core` : import `rpm-stats` core kinematics and backend for gravoty orientation calculus. 
- `test` : import `core` associated tests to prevent from code regression. 

### Removed 

### Fixed