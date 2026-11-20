"""
CLI wrapper for PRISMA simulation, trajectory
management, and reporting using argparse.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import PRESETS, PROFILES, SimulationConfig, TrajectoryConfig
from src.simulation.simulation import Simulation
from src.trajectory.Trajectory import Trajectory
from src.utils import convert_to_pdf_path, get_date

PRESETS_KEYS = list(PRESETS.keys())
DEFAULT_PRESET = PRESETS_KEYS[0]


# ==================================================
# PARSER INITIALIZATION
# ==================================================


def init_trajectory(traj_parser: argparse.ArgumentParser) -> None:
    """Init trajectory parser arguments."""
    traj_wrapper = traj_parser.add_subparsers(dest="trajectory_command", required=True)

    # --------- generate subparser --------------
    generate_parser = traj_wrapper.add_parser(
        "generate", help="Generate CSV RPM trajectory from existing profiles."
    )
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
        help="Generate a side-car PDF report if present.",
    )
    generate_parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60.0,
        help="Trajectory duration (in seconds).",
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
        help="Trajectory description - written in the CSV header file.",
    )

    # --------- show subparser --------------
    show_parser = traj_wrapper.add_parser(
        "show", help="Generate PDF report from existing CSV trajectory."
    )
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


def init_simulation(sim_parser: argparse.ArgumentParser) -> None:
    """Init simulation parser arguments."""
    sim_wrapper = sim_parser.add_subparsers(dest="simulation_command", required=True)

    # --------- launch subparser --------------
    launch_parser = sim_wrapper.add_parser(
        "launch", help="Run particle dynamics simulation from a trajectory CSV."
    )

    # --------- show subparser --------------
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
    config_group = launch_parser.add_argument_group("System configuration")
    config_group.add_argument(
        "-p",
        "--preset",
        type=str,
        choices=PRESETS_KEYS,
        default=DEFAULT_PRESET,
        help=f"Predefined physical configuration preset (default: {DEFAULT_PRESET}).",
    )
    config_group.add_argument(
        "--x0",
        type=float,
        nargs=3,
        metavar=("X", "Y", "Z"),
        default=[0.0, 0.0, 0.0],
        help="Initial coordinates in sample frame R2 (in meters, e.g. --x0 0.0 0.0 0.005).",
    )

    # --- Physical Parameter Overrides (default=None so presets aren't overwritten) ---
    phys_group = launch_parser.add_argument_group("Physical overrides")
    phys_group.add_argument(
        "-r",
        "--radius",
        dest="r",
        type=float,
        default=None,
        help="Override particle radius in meters.",
    )
    phys_group.add_argument(
        "--rho",
        type=float,
        default=None,
        help="Override particle density in kg/m^3.",
    )
    phys_group.add_argument(
        "--rho-f",
        type=float,
        default=None,
        help="Override fluid density in kg/m^3.",
    )
    phys_group.add_argument(
        "--mu-f",
        type=float,
        default=None,
        help="Override fluid dynamic viscosity in Pa*s.",
    )
    phys_group.add_argument(
        "-k",
        "--elasticity",
        dest="k",
        type=float,
        default=None,
        help="Override cytoskeletal actin restoring stiffness in N/m.",
    )
    phys_group.add_argument(
        "-rt",
        "--tube-radius",
        dest="tube_radius",
        type=float,
        default=None,
        help="Override confinement tube or cell radius in meters.",
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


def main() -> None:
    """Main CLI entrypoint for PRISMA."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    LOG = logging.getLogger("PRISMA")

    parser = argparse.ArgumentParser(
        prog="prisma",
        description="PRISMA: Microscale inclusion simulation under RPM kinematics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    traj_parser = subparsers.add_parser(
        "trajectory",
        help="Inspect, visualize, or generate RPM motor trajectories.",
    )
    init_trajectory(traj_parser)

    sim_parser = subparsers.add_parser(
        "simulation",
        help="Run simulation from trajectory / display simulation results.",
    )
    init_simulation(sim_parser)

    # Print help if empty command provided BEFORE parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Parse commands
    if args.command == "trajectory":
        if args.trajectory_command == "generate":
            config = TrajectoryConfig(
                LOG=LOG,
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
            print(config)
            traj = Trajectory(config)
            traj.generate()

        elif args.trajectory_command == "show":
            output_filepath = (
                convert_to_pdf_path(Path(args.input))
                if args.output is None
                else Path(args.output)
            )
            config = TrajectoryConfig(
                LOG=LOG,
                input_path=args.input,
                output_path=None,
                report_path=output_filepath,
                date=get_date(),
            )
            print(config)
            traj = Trajectory(config)
            traj.show()

    elif args.command == "simulation":
        if args.simulation_command == "launch":
            # Resolve preset + explicit CLI overrides
            base = PRESETS[args.preset].copy()
            config = SimulationConfig(
                LOG=LOG,
                input_file=args.input,
                output_file=args.output,
                log_report=args.log_report,
                preset=args.preset,
                init_pos=args.x0,
                particle_radius=args.r if args.r is not None else base["radius"],
                tube_radius=(
                    args.tube_radius if args.tube_radius is not None else base["r_tube"]
                ),
                rho=args.rho if args.rho is not None else base["rho"],
                rho_f=args.rho_f if args.rho_f is not None else base["rho_f"],
                mu_f=args.mu_f if args.mu_f is not None else base["mu_f"],
                k=args.k if args.k is not None else base["k"],
            )
            print(config)
            simulation = Simulation(config)
            simulation.run()

        elif args.simulation_command == "show":
            simulation = Simulation.from_csv(args.input, LOG)
            simulation.show(pdf_path=args.output)


if __name__ == "__main__":
    main()
