"""
    CLI wrapper for prisma simulation using argparse
"""

import argparse
from pathlib import Path
import logging
import pandas as pd

from src.trajectory.Trajectory import Trajectory
from src.core.physics import *
from src.solver.solver import RK4Overdamped

# Init configs 
PRESETS = {
    "glycerol_bead": {
        "radius": 1.5e-3,
        "rho": 1202.0,
        "rho_f": 1200.0,
        "mu_f": 1.412,
        "k": 0.0,
        "r_tube": 0.05,
    },
    "statolith": {
        "radius": 1.5e-6,
        "rho": 1500.0,
        "rho_f": 1050.0,
        "mu_f": 0.1,
        "k": 1e-4,
        "r_tube": 20e-6,
    },
}

# --------------- PARSERS -------------------------

def init_trajectory(parser, traj_parser): 
    """
    Trajectory Parser : 

    """
    raise NotImplemented()

def init_run(parser, run_parser): 
    """
    Run Parser : 
    --input (-i):   CSV trajectory source file
    --output (-o):  CSV particle resulting trajectory output 
    --duration -(d):Simulation duration 
    --dt:           Simulation step (in s)
    --preset (-p):  Using preset config values 
        # TODO : Implement preset dictionnaries 
    --x0:           Init position 
    --k:            Elasticity coefficient 
    --r:            Particle radius 
    --rho:          Particle density 
    --rho-f:        Fluid density 
    --mu-f:         Fluid viscosity 
    --k:            Fluid elasticity recall 
    """
    # --- I/O Arguments ---
    io_group = run_parser.add_argument_group("I/O options")
    io_group.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input CSV trajectory file.",
    )
    io_group.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Path to save the resulting simulation trajectory CSV.",
    )

    # --- Temporal & Numerical Setup ---
    time_group = run_parser.add_argument_group("Temporal discretization")
    time_group.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        help="Simulation duration in seconds (defaults to trajectory full length).",
    )
    time_group.add_argument(
        "--dt",
        type=float,
        default=None,
        help="Simulation integration step in seconds (defaults to trajectory sampling step).",
    )

    # --- Presets & Initial Conditions ---
    config_group = run_parser.add_argument_group("System configuration")
    config_group.add_argument(
        "-p",
        "--preset",
        type=str,
        choices=["glycerol_bead", "statolith"],
        default=None,
        help="Predefined physical configuration preset.",
    )
    config_group.add_argument(
        "--x0",
        type=float,
        nargs=3,
        metavar=("X", "Y", "Z"),
        default=[0.0, 0.0, 0.0],
        help="Initial coordinates in sample frame R2 (in meters, e.g. --x0 0.0 0.0 0.005).",
    )

    # --- Physical Parameter Overrides ---
    phys_group = run_parser.add_argument_group("Physical overrides")
    phys_group.add_argument(
        "-r",
        "--radius",
        dest="r",
        type=float,
        default=None,
        help="Particle radius in meters.",
    )
    phys_group.add_argument(
        "--rho",
        type=float,
        default=None,
        help="Particle density in kg/m^3.",
    )
    phys_group.add_argument(
        "--rho-f",
        type=float,
        default=None,
        help="Fluid density in kg/m^3.",
    )
    phys_group.add_argument(
        "--mu-f",
        type=float,
        default=None,
        help="Fluid dynamic viscosity in Pa*s.",
    )
    phys_group.add_argument(
        "-k",
        "--elasticity",
        dest="k",
        type=float,
        default=None,
        help="Cytoskeletal actin restoring stiffness in N/m (defaults to 0.0).",
    )
    phys_group.add_argument(
            "-rt",
            "--tube-radius",
            dest="tube-radius",
            type=float,
            default=None,
            help="Tube radius in m",
        )

# --------------- LAUNCH -------------------------

def launch_run(args, LOG):
    """
    Extract run arguments, build physical models, and execute numerical simulation.
    """
    LOG.info(f"Loading motor trajectory from: {args.input}")
    traj = Trajectory(LOG=LOG)
    traj.from_csv(filepath=str(args.input))

    LOG.info("Computing kinematic profile (apparent gravity & angular tensors)...")
    kin = traj.compute_kinematics()

    # Get physics params and overides ones 
    params = {}
    if getattr(args, "preset", None) and args.preset in PRESETS:
        LOG.info(f"Applying physical preset: '{args.preset}'")
        params.update(PRESETS[args.preset])
    else:
        # Default values if not PRESET
        params.update({
            "radius": 1.5e-3,
            "rho": 1202.0,
            "rho_f": 1200.0,
            "mu_f": 1.412,
            "k": 0.0,
            "r_tube": 0.05,
        })

    # Overide on given params
    if getattr(args, "r", None) is not None:
        params["radius"] = args.r
    if getattr(args, "rho", None) is not None:
        params["rho"] = args.rho
    if getattr(args, "rho_f", None) is not None:
        params["rho_f"] = args.rho_f
    if getattr(args, "mu_f", None) is not None:
        params["mu_f"] = args.mu_f
    if getattr(args, "k", None) is not None:
        params["k"] = args.k

    # Build physics objects
    x0_vec = np.array(args.x0, dtype=float)
    particle = Particle(radius=params["radius"], rho=params["rho"], x0=x0_vec)
    fluid = Fluid(rho=params["rho_f"], mu=params["mu_f"], k=params["k"])
    system = PhysicalSystem(particle=particle, fluid=fluid)

    LOG.info(
        f"Physical system initialized: tau_v={system.tau_v:.3e} s, "
        f"beta={system.beta:.4f}, tau_k={system.compute_tau_k()}"
    )

    # Numerical RK4 solving
    LOG.info("Running RK4 overdamped solver...")
    solver = RK4Overdamped(system=system, r_tube=params["r_tube"], LOG=LOG)
    result = solver.solve(kin=kin, v0=np.zeros(3))

    max_reynolds = np.max(result.reynolds)
    LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
    if max_reynolds >= 0.1:
        LOG.warning(f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})! Creeping flow assumption may be violated.")

    # CSV save if asked
    if getattr(args, "output", None):
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        LOG.info(f"Exporting trajectory results to {output_path}")

        df_out = pd.DataFrame({
            "timestamp": result.timestamp,
            "x": result.positions[:, 0],
            "y": result.positions[:, 1],
            "z": result.positions[:, 2],
            "vx": result.velocities[:, 0],
            "vy": result.velocities[:, 1],
            "vz": result.velocities[:, 2],
            "reynolds": result.reynolds,
        })
        df_out.to_csv(output_path, index=False)

    return result



# --------------- MAIN -------------------------

def main(): 
    """
    - trajectory : Init and generates trajectories using Trajectory class. 
    Read CSV trajectories and parse them, able to display a trajectory using 
    --show argument. 
    
    - run : run a simulation using RK4Solver and Solver class.
    """
    # Define parsers
    parser = argparse.ArgumentParser(
        description="Cell organits simulation in RPM motion"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(name="run")

    init_run(parser, run_parser)

    # Parsing 
    args = parser.parse_args()

    if args.command == "run":
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
        logger = logging.getLogger("PRISMA")
        launch_run(args, logger)



if __name__ == "__main__":
    main()