"""CLI wrapper for PRISMA simulation, trajectory management, and reporting using argparse."""

import argparse
import logging
import sys 
from pathlib import Path
from datetime import datetime

from src.trajectory.Trajectory import Trajectory
from src.trajectory.generators import PROFILES
from src.config import TrajectoryConfig, SimulationConfig


# --------- Helpers --------------

def convert_to_pdf_path(fp: Path): 
    """
    Convert a entered filepath into the same filepath 
    with a '.pdf' extension. 
    """
    new_fp = fp.with_suffix('')
    return new_fp.with_suffix('.pdf')

# ==============================================================================
# PARSER INITIALIZATION
# ==============================================================================

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
        "generate", 
        help="Generate CSV RPM trajectory from existing profiles."
    )
    # General arguments 
    generate_parser.add_argument(
        "-o", "--output", required=True, 
        help="Output path for the CSV trajectory commands."
    )
    generate_parser.add_argument(
        "-l", "--log-report", action="store_true", 
        help="Generate a side-acr PDF report if present."
    )
    # Physical values 
    generate_parser.add_argument(
        "-d", "--duration", type=float, default=60.0, 
        help="Trajectory duration (in seconds)"
    )
    generate_parser.add_argument(
        "-s", "--step", type=float, default=1.0,
        help="Time step duration between two points - dt (in seconds)."
    )
    generate_parser.add_argument(
        "-p", "--profile", type=str, choices=list(PROFILES.keys()), default="random_walk",
        help="Existing profile for trajectory generator."
    )
    generate_parser.add_argument(
        "-t", "--description-text", type=str,
        help="Trajectory description - writed in the CSV header file."
    )

    # --------- show subparser --------------
    # TODO : Complete this part 


def init_simulation(): 
    """
    Init simulation parser arguments. 
    """
    pass 


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
    # sim_parser = subparsers.add_parser(
    #     "simulation", 
    #     help="Run simulation from trajectory / display simulation results."
    # )

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
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                duration_s=args.duration, 
                step_s=args.step, 
                profile=args.profile, 
                desc=args.description_text, 
                log_report=args.log_report
            )
            # Instanciate trajectory 
            traj = Trajectory(config)
            # Launch generation 
            traj.generate()


        # elif args.trajectory_command == "show":
        #     LOG.debug("Launching trajectory generate command")
    # elif args.command == "run":
    #     launch_run(args, logger)
    # elif args.command == "result":
    #     if args.result_command == "show":
    #         launch_result_show(args, logger)


if __name__ == "__main__":
    main()


# def init_trajectory(traj_parser: argparse.ArgumentParser):
#     """Configure subparsers for motor trajectory manipulation (show & generate)."""
#     traj_subparsers = traj_parser.add_subparsers(
#         dest="trajectory_command", required=True
#     )

#     # --- Subcommand: show ---
#     show_parser = traj_subparsers.add_parser(
#         "show",
#         help="Inspect, summarize, or plot an existing trajectory CSV file.",
#     )
#     show_parser.add_argument(
#         "-i",
#         "--input",
#         type=Path,
#         required=True,
#         help="Path to the input CSV trajectory file.",
#     )
#     show_parser.add_argument(
#         "--report",
#         type=Path,
#         default=None,
#         help="Path to export a compiled 3-page PDF summary report.",
#     )

#     # --- Subcommand: generate ---
#     gen_parser = traj_subparsers.add_parser(
#         "generate",
#         help="Generate a synthetic motor profile and export to CSV.",
#     )
#     gen_parser.add_argument(
#         "-o",
#         "--output",
#         type=Path,
#         required=True,
#         help="Path to export the generated trajectory CSV.",
#     )
#     gen_parser.add_argument(
#         "-d",
#         "--duration",
#         type=float,
#         required=True,
#         help="Total duration of the trajectory in seconds.",
#     )
#     gen_parser.add_argument(
#         "--dt",
#         type=float,
#         default=0.01,
#         help="Temporal sampling step in seconds (default: 0.01).",
#     )
#     gen_parser.add_argument(
#         "-p",
#         "--profile",
#         type=str,
#         choices=PROFILES.keys(),
#         default="random_walk",
#         help="Kinematic trajectory generation using presets profiles",
#     )
#     gen_parser.add_argument(
#         "--desc",
#         type=str,
#         default="Synthetic RPM trajectory profile",
#         help="Description metadata injected into CSV header.",
#     )
#     gen_parser.add_argument(
#         "--log-report",
#         action="store_true",
#         help="Auto generate side-car PDF report."
#     )


# def init_run(run_parser: argparse.ArgumentParser):
#     """Configure parser options for particle dynamic numerical simulation."""
#     # --- I/O Arguments ---
#     io_group = run_parser.add_argument_group("I/O options")
#     io_group.add_argument(
#         "-i",
#         "--input",
#         type=Path,
#         required=True,
#         help="Path to the input CSV trajectory file.",
#     )
#     io_group.add_argument(
#         "-o",
#         "--output",
#         type=Path,
#         default=None,
#         help="Path to save the resulting simulation trajectory CSV.",
#     )
#     # io_group.add_argument(
#     #     "--report",
#     #     type=Path,
#     #     default=None,
#     #     help="Path to export a compiled 3-page PDF simulation report directly after solving.",
#     # )
#     io_group.add_argument(
#         "--log-report",
#         action="store_true",
#         help="Generate simulation side-car PDF report."
#     )

#     # --- Temporal & Numerical Setup ---
#     time_group = run_parser.add_argument_group("Temporal discretization")
#     time_group.add_argument(
#         "-d",
#         "--duration",
#         type=float,
#         default=None,
#         help="Simulation duration in seconds (defaults to trajectory full length).",
#     )
#     time_group.add_argument(
#         "--dt",
#         type=float,
#         default=None,
#         help="Simulation integration step in seconds (defaults to trajectory sampling step).",
#     )

#     # --- Presets & Initial Conditions ---
#     config_group = run_parser.add_argument_group("System configuration")
#     config_group.add_argument(
#         "-p",
#         "--preset",
#         type=str,
#         choices=["glycerol_bead", "statolith"],
#         default=None,
#         help="Predefined physical configuration preset.",
#     )
#     config_group.add_argument(
#         "--x0",
#         type=float,
#         nargs=3,
#         metavar=("X", "Y", "Z"),
#         default=[0.0, 0.0, 0.0],
#         help="Initial coordinates in sample frame R2 (in meters, e.g. --x0 0.0 0.0 0.005).",
#     )

#     # --- Physical Parameter Overrides ---
#     phys_group = run_parser.add_argument_group("Physical overrides")
#     phys_group.add_argument(
#         "-r",
#         "--radius",
#         dest="r",
#         type=float,
#         default=None,
#         help="Particle radius in meters.",
#     )
#     phys_group.add_argument(
#         "--rho",
#         type=float,
#         default=None,
#         help="Particle density in kg/m^3.",
#     )
#     phys_group.add_argument(
#         "--rho-f",
#         type=float,
#         default=None,
#         help="Fluid density in kg/m^3.",
#     )
#     phys_group.add_argument(
#         "--mu-f",
#         type=float,
#         default=None,
#         help="Fluid dynamic viscosity in Pa*s.",
#     )
#     phys_group.add_argument(
#         "-k",
#         "--elasticity",
#         dest="k",
#         type=float,
#         default=None,
#         help="Cytoskeletal actin restoring stiffness in N/m (defaults to 0.0).",
#     )
#     phys_group.add_argument(
#         "-rt",
#         "--tube-radius",
#         dest="tube_radius",
#         type=float,
#         default=None,
#         help="Confinement tube or cell radius in meters.",
#     )


# def init_result(result_parser: argparse.ArgumentParser):
#     """Configure subparsers for simulation result CSV files manipulation."""
#     res_subparsers = result_parser.add_subparsers(
#         dest="result_command", required=True
#     )

#     # --- Subcommand: show ---
#     show_parser = res_subparsers.add_parser(
#         "show",
#         help="Inspect, summarize, or plot an existing simulation result CSV file.",
#     )
#     show_parser.add_argument(
#         "-i",
#         "--input",
#         type=Path,
#         required=True,
#         help="Path to the input simulation result CSV file.",
#     )
#     show_parser.add_argument(
#         "-rt",
#         "--tube-radius",
#         dest="tube_radius",
#         type=float,
#         default=0.05,
#         help="Confinement tube or cell radius in meters (default: 0.05 m).",
#     )
#     show_parser.add_argument(
#         "--plot",
#         action="store_true",
#         help="Display interactive matplotlib diagnostic figures.",
#     )
#     show_parser.add_argument(
#         "--report",
#         type=Path,
#         default=None,
#         help="Path to export a compiled 3-page PDF simulation report.",
#     )


# ==============================================================================
# EXECUTION ROUTINES
# ==============================================================================


# def launch_trajectory_show(args, LOG: logging.Logger):
#     """Load, analyze, and display trajectory metrics, optional visual plots, or PDF reports."""
#     LOG.info(f"Loading trajectory for inspection: {args.input}")
#     report = TrajectoryReport.from_csv(filepath=args.input, output_path=args.report, log=LOG)
#     report.show_CLI()

#     if args.report:
#         LOG.info(f"Compiling and exporting 3-page PDF trajectory report to: {args.report}")
#         report.assemble_pdf()
#         LOG.info("PDF report successfully compiled.")


# def launch_trajectory_generate(args, LOG: logging.Logger):
#     """Generate synthetic angular motion profiles and write them to a structured CSV file."""
#     LOG.info(f"Generating trajectory profile '{args.profile}' (duration={args.duration}s, dt={args.dt}s)")
    
#     # Init trajectory object
#     traj = Trajectory(LOG=LOG)
    
#     # Launch generation
#     traj.generate(
#         durations_s=args.duration, 
#         step_s=args.dt, 
#         profile=args.profile)
    
    # if args.mode == "constant_speed":
    #     theta1 = (args.speed * t) % (2 * np.pi)
    #     theta2 = (args.speed * 0.7 * t) % (2 * np.pi)
    # elif args.mode == "desynchronized_sine":
    #     w1, w2 = args.speed, args.speed * np.sqrt(2)
    #     theta1 = np.pi * np.sin(w1 * t)
    #     theta2 = np.pi * np.sin(w2 * t)
    # else:
    #     raise ValueError(f"Unknown trajectory generation mode: {args.mode}")

    # traj = Trajectory(LOG=LOG)
    # traj.timestamp = t
    # traj.theta1 = theta1
    # traj.theta2 = theta2
    # traj.step_s = args.dt
    # traj.duration_s = args.duration
    # traj.description = f"{args.desc} [mode={args.mode}, speed={args.speed}]"
    # traj.generation_date = str(datetime.datetime.now())

    # Save trajectory in CSV file 
    # traj.description = f"{args.desc} [mode={args.profile}"
    # args.output.parent.mkdir(parents=True, exist_ok=True)
    # traj.to_csv(filepath=str(args.output))


    # # Generate report option 
    # if args.log_report: 
    #     # Replacing output extension from .csv to .pdf
    #     fp = Path(args.output)
    #     fp = fp.with_suffix('')
    #     fp = fp.with_suffix('.pdf')
    #     LOG.info(f"Compiling and exporting 3-page PDF trajectory report to: {fp}.pdf")

    #     # Generate report object 
    #     report = TrajectoryReport.from_csv(filepath=args.output, output_path=fp, log=LOG)
    #     report.show_CLI()
    #     report.assemble_pdf()
    #     LOG.info("PDF report successfully compiled.")


# def launch_run(args, LOG: logging.Logger):
#     """Extract run arguments, build physical models, execute RK4 solving, and generate reports."""
#     LOG.info(f"Loading motor trajectory from: {args.input}")
#     traj = Trajectory(LOG=LOG)
#     traj.from_csv(filepath=str(args.input))

#     LOG.info("Computing kinematic profile (apparent gravity & angular tensors)...")
#     kin = traj.compute_kinematics()

#     # 1. Physical Parameter Resolution (Preset + CLI Overrides)
#     params = {}
#     if getattr(args, "preset", None) and args.preset in PRESETS:
#         LOG.info(f"Applying physical preset: '{args.preset}'")
#         params.update(PRESETS[args.preset])
#     else:
#         params.update({
#             "radius": 1.5e-3,
#             "rho": 1202.0,
#             "rho_f": 1200.0,
#             "mu_f": 1.412,
#             "k": 0.0,
#             "r_tube": 0.05,
#         })

#     if getattr(args, "r", None) is not None:
#         params["radius"] = args.r
#     if getattr(args, "rho", None) is not None:
#         params["rho"] = args.rho
#     if getattr(args, "rho_f", None) is not None:
#         params["rho_f"] = args.rho_f
#     if getattr(args, "mu_f", None) is not None:
#         params["mu_f"] = args.mu_f
#     if getattr(args, "k", None) is not None:
#         params["k"] = args.k
#     if getattr(args, "tube_radius", None) is not None:
#         params["r_tube"] = args.tube_radius

#     # 2. Physics Objects Initialization
#     x0_vec = np.array(args.x0, dtype=float)
#     particle = Particle(radius=params["radius"], rho=params["rho"], x0=x0_vec)
#     fluid = Fluid(rho=params["rho_f"], mu=params["mu_f"], k=params["k"])
#     system = PhysicalSystem(particle=particle, fluid=fluid)

#     LOG.info(
#         f"Physical system initialized: tau_v={system.tau_v:.3e} s, "
#         f"beta={system.beta:.4f}, tau_k={system.compute_tau_k()}"
#     )

#     # 3. Solver Execution
#     LOG.info("Running RK4 overdamped solver...")
#     solver = RK4Overdamped(system=system, r_tube=params["r_tube"], LOG=LOG)
#     result = solver.solve(kin=kin, v0=np.zeros(3))

#     max_reynolds = np.max(result.reynolds)
#     LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
#     if max_reynolds >= 0.1:
#         LOG.warning(
#             f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})! Creeping flow assumption may be violated."
#         )

#     # 4. Result CSV Export
#     if getattr(args, "output", None):
#         output_path = Path(args.output)
#         output_path.parent.mkdir(parents=True, exist_ok=True)
#         LOG.info(f"Exporting trajectory results to {output_path}")

#         df_out = pd.DataFrame({
#             "timestamp": result.timestamp,
#             "x": result.positions[:, 0],
#             "y": result.positions[:, 1],
#             "z": result.positions[:, 2],
#             "vx": result.velocities[:, 0],
#             "vy": result.velocities[:, 1],
#             "vz": result.velocities[:, 2],
#             "reynolds": result.reynolds,
#         })
#         df_out.to_csv(output_path, index=False)

#     # 5. Direct Simulation Report Generation
#     if args.log_report:
#         # Use args.output path 
#         fp = Path(args.output)
#         fp = fp.with_suffix('')
#         fp = fp.with_suffix('.pdf')
#         LOG.info(f"Compiling simulation PDF report to: {fp}")
#         sim_report = SimulationReport(
#             result=result,
#             kin=kin,
#             system=system,
#             r_tube=params["r_tube"],
#             output_path=fp,
#         )
#         sim_report.show_CLI()
#         sim_report.assemble_pdf()
#         LOG.info("Simulation PDF report successfully generated.")

#     return result


# def launch_result_show(args, LOG: logging.Logger):
#     """Load an existing simulation result CSV, display diagnostics, and generate report."""
#     LOG.info(f"Loading simulation result CSV from: {args.input}")
#     sim_report = SimulationReport.from_csv(
#         filepath=args.input,
#         r_tube=args.tube_radius,
#         output_path=args.report,
#     )
#     sim_report.show_CLI()

#     if args.plot:
#         LOG.info("Rendering interactive simulation diagnostic plots...")
#         sim_report.generate_plots()
#         plt.show()

#     if args.report:
#         LOG.info(f"Compiling and exporting PDF simulation report to: {args.report}")
#         sim_report.assemble_pdf()
#         LOG.info("Simulation PDF report successfully compiled.")

