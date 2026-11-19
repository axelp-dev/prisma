# ==================================================
#               CLI wrapper
# ==================================================

"""
CLI wrapper for PRISMA simulation, trajectory
management, and reporting using argparse.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import SimulationConfig, TrajectoryConfig
from src.simulation.simulation import Simulation, from_csv
from src.trajectory.generators import PROFILES
from src.trajectory.Trajectory import Trajectory
from src.utils import *

# --------- DEFAULT --------------

# Default simulation params
DEFAULT_SIMULATION = {
    "radius": 1.5e-3,
    "rho": 1202.0,
    "rho_f": 1200.0,
    "mu_f": 1.412,
    "k": 0.0,
    "r_tube": 0.05,
}


# ==================================================
# PARSER INITIALIZATION
# ==================================================


def init_trajectory(traj_parser: argparse.ArgumentParser):
    """
    Init trajectory parser arguments.
    """
    # --------- trajectory subparser --------------
    # - trajectory generate: to generate a trajectory
    # - trajectory show: to generate pdf report from a trajectory

    # Init trajectory subparser
    traj_wrapper = traj_parser.add_subparsers(dest="trajectory_command", required=True)

    # --------- generate subparser --------------
    generate_parser = traj_wrapper.add_parser(
        "generate", help="Generate CSV RPM trajectory from existing profiles."
    )
    # General arguments
    generate_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path for the CSV trajectory commands.",
    )
    generate_parser.add_argument(
        "-l",
        "--log-report",
        action="store_true",
        help="Generate a side-acr PDF report if present.",
    )
    # Physical values
    generate_parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60.0,
        help="Trajectory duration (in seconds)",
    )
    generate_parser.add_argument(
        "-s",
        "--step",
        type=float,
        default=1.0,
        help="Time step duration between two points - dt (in seconds).",
    )
    generate_parser.add_argument(
        "-p",
        "--profile",
        type=str,
        choices=list(PROFILES.keys()),
        default="random_walk",
        help="Existing profile for trajectory generator.",
    )
    generate_parser.add_argument(
        "-t",
        "--description-text",
        type=str,
        help="Trajectory description - writed in the CSV header file.",
    )

    # --------- show subparser --------------
    show_parser = traj_wrapper.add_parser(
        "show", help="Generate PDF report from existing CSV trajectory."
    )
    # General arguments
    show_parser.add_argument(
        "-i", "--input", type=str, required=True, help="CSV trajectory filepath."
    )
    show_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="PDF report output path - default next to the input CSV.",
    )


def init_simulation(sim_parser):
    """
    Init simulation parser arguments.
    """
    # --- Create subparsers ---
    sim_wrapper = sim_parser.add_subparsers(dest="simulation_command", required=True)

    # --------- launch subparser --------------
    launch_parser = sim_wrapper.add_parser(
        "launch", help="Generate CSV RPM trajectory from existing profiles."
    )

    # --------- simulation show subparser --------------
    show_sim_parser = sim_wrapper.add_parser(
        "show",
        help="Compute simulation results to PDF report from existing CSV result.",
    )

    # --- I/O Arguments ---
    io_group = launch_parser.add_argument_group("I/O options")
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
    io_group.add_argument(
        "--log-report",
        action="store_true",
        help="Generate simulation side-car PDF report.",
    )

    # --- Temporal & Numerical Setup ---
    time_group = launch_parser.add_argument_group("Temporal discretization")
    time_group.add_argument(
        "-d",
        "--duration",
        type=float,
        default=120,
        help="Simulation duration in seconds (defaults to trajectory full length).",
    )
    time_group.add_argument(
        "--dt",
        type=float,
        default=0.1,
        help="Simulation integration step in seconds (defaults to trajectory sampling step).",
    )

    # --- Presets & Initial Conditions ---
    config_group = launch_parser.add_argument_group("System configuration")
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
    phys_group = launch_parser.add_argument_group("Physical overrides")
    phys_group.add_argument(
        "-r",
        "--radius",
        dest="r",
        type=float,
        default=DEFAULT_SIMULATION["radius"],
        help="Particle radius in meters.",
    )
    phys_group.add_argument(
        "--rho",
        type=float,
        default=DEFAULT_SIMULATION["rho"],
        help="Particle density in kg/m^3.",
    )
    phys_group.add_argument(
        "--rho-f",
        type=float,
        default=DEFAULT_SIMULATION["rho_f"],
        help="Fluid density in kg/m^3.",
    )
    phys_group.add_argument(
        "--mu-f",
        type=float,
        default=DEFAULT_SIMULATION["mu_f"],
        help="Fluid dynamic viscosity in Pa*s.",
    )
    phys_group.add_argument(
        "-k",
        "--elasticity",
        dest="k",
        type=float,
        default=DEFAULT_SIMULATION["k"],
        help="Cytoskeletal actin restoring stiffness in N/m (defaults to 0.0).",
    )
    phys_group.add_argument(
        "-rt",
        "--tube-radius",
        dest="tube_radius",
        type=float,
        default=DEFAULT_SIMULATION["r_tube"],
        help="Confinement tube or cell radius in meters.",
    )

    # --------- simulation show subparser --------------
    show_sim_parser.add_argument(
        "-i", "--input", type=str, required=True, help="CSV simulation result."
    )
    show_sim_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="PDF report output path - default next to the input CSV.",
    )


# ==================================================
# LAUNCHING MAIN PROGRAM
# ==================================================


def main():
    """Main CLI entrypoint for PRISMA."""

    # Init logging
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    LOG = logging.getLogger("PRISMA")

    # --------- Init Parsers --------------

    parser = argparse.ArgumentParser(
        prog="prisma",
        description="PRISMA: Microscale inclusion simulation under RPM kinematics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand trajectory
    traj_parser = subparsers.add_parser(
        "trajectory",
        help="Inspect, visualize, or generate RPM motor trajectories.",
    )
    init_trajectory(traj_parser)

    # Subcommand simulation
    show_sim_parser = subparsers.add_parser(
        "simulation",
        help="Run simulation from trajectory / display simulation results.",
    )
    init_simulation(show_sim_parser)

    # --------- Parse arguments--------------

    args = parser.parse_args()

    # Print help if empty command provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Parse commands
    if args.command == "trajectory":
        if args.trajectory_command == "generate":
            # Init config
            config = TrajectoryConfig(
                LOG,
                input_path=None,
                output_path=Path(args.output),
                report_path=convert_to_pdf_path(Path(args.output)),
                date=get_date(),
                duration_s=args.duration,
                step_s=args.step,
                profile=args.profile,
                desc=args.description_text,
                log_report=args.log_report,
            )
            # Instanciate trajectory
            traj = Trajectory(config)
            # Launch generation
            traj.generate()

        elif args.trajectory_command == "show":
            # View trajectory from CV file
            if args.output == None:
                output_filepath = convert_to_pdf_path(Path(args.input))
            else:
                output_filepath = Path(args.output)
            # Init config
            config = TrajectoryConfig(
                LOG=LOG,
                input_path=args.input,
                output_path=None,
                report_path=output_filepath,
                date=get_date(),
            )

            # Launch report building
            traj = Trajectory(config)
            traj.show()

    elif args.command == "simulation":
        if args.simulation_command == "launch":
            # --- Generating Config & Objects ---
            # Parsing general arguments and build SimulationConfig object
            config = SimulationConfig(
                input_file=args.input,
                output_file=args.output,
                log_report=args.log_report,
                preset=args.preset,
                init_pos=args.x0,
                particle_radius=args.r,
                tube_radius=args.tube_radius,
                rho=args.rho,
                rho_f=args.rho_f,
                mu_f=args.mu_f,
                k=args.k,
                LOG=LOG,
            )
            # Init simulation object
            simulation = Simulation(config)

            # --- Launching simulation ---
            # Loading trajectory from simulation object
            simulation.run()

        elif args.simulation_command == "show":
            # --- Generate report from existing simulation ---
            LOG.info(f"Loading simulation result CSV from: {args.input}")
            simulation = from_csv(Simulation, args.input, LOG)
            # TODO : branch Simulation::show() process


if __name__ == "__main__":
    main()
