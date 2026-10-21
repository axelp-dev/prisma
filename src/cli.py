"""CLI wrapper for PRISMA simulation and trajectory management using argparse."""

import argparse
import datetime
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.core.physics import Fluid, Particle, PhysicalSystem
from src.solver.solver import RK4Overdamped
from src.trajectory.Trajectory import Trajectory

# Predefined physical setups
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


# ==============================================================================
# PARSER INITIALIZATION
# ==============================================================================


def init_trajectory(traj_parser: argparse.ArgumentParser):
    """Configure subparsers for motor trajectory manipulation (show & generate)."""
    traj_subparsers = traj_parser.add_subparsers(
        dest="trajectory_command", required=True
    )

    # --- Subcommand: show ---
    show_parser = traj_subparsers.add_parser(
        "show",
        help="Inspect, summarize, or plot an existing trajectory CSV file.",
    )
    show_parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input CSV trajectory file.",
    )
    show_parser.add_argument(
        "--plot",
        action="store_true",
        help="Display interactive matplotlib plots of angles and apparent gravity.",
    )
    show_parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Path to export a compiled summary report (PDF/Markdown format).",
    )

    # --- Subcommand: generate ---
    gen_parser = traj_subparsers.add_parser(
        "generate",
        help="Generate a synthetic motor profile and export to CSV.",
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to export the generated trajectory CSV.",
    )
    gen_parser.add_argument(
        "-d",
        "--duration",
        type=float,
        required=True,
        help="Total duration of the trajectory in seconds.",
    )
    gen_parser.add_argument(
        "--dt",
        type=float,
        default=0.01,
        help="Temporal sampling step in seconds (default: 0.01).",
    )
    gen_parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["constant_speed", "desynchronized_sine"],
        default="desynchronized_sine",
        help="Kinematic trajectory generation profile (default: desynchronized_sine).",
    )
    gen_parser.add_argument(
        "--speed",
        type=float,
        default=0.5,
        help="Nominal angular speed parameter in rad/s (default: 0.5).",
    )
    gen_parser.add_argument(
        "--desc",
        type=str,
        default="Synthetic RPM trajectory profile",
        help="Description metadata injected into CSV header.",
    )


def init_run(run_parser: argparse.ArgumentParser):
    """Configure parser options for particle dynamic numerical simulation."""
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
        dest="tube_radius",
        type=float,
        default=None,
        help="Confinement tube or cell radius in meters.",
    )


# ==============================================================================
# EXECUTION ROUTINES
# ==============================================================================


def launch_trajectory_show(args, LOG: logging.Logger):
    """Load, analyze, and display trajectory metrics and optional visual plots."""
    LOG.info(f"Loading trajectory for inspection: {args.input}")
    traj = Trajectory(LOG=LOG)
    traj.from_csv(filepath=str(args.input))

    kin = traj.compute_kinematics()

    # Time-averaged residual gravity vector
    mean_g = np.mean(kin.g, axis=0)
    mean_g_norm = np.linalg.norm(mean_g)
    max_omega1 = np.max(np.abs(kin.omega1))
    max_omega2 = np.max(np.abs(kin.omega2))

    print("\n" + "=" * 50)
    print("           TRAJECTORY SUMMARY METRICS            ")
    print("=" * 50)
    print(f"File Source      : {args.input}")
    print(f"Description      : {traj.description}")
    print(f"Duration         : {traj.duration_s:.2f} s")
    print(f"Sampling Step dt : {traj.step_s:.4f} s ({len(traj.timestamp)} points)")
    print(f"Max |omega1|     : {max_omega1:.3f} rad/s ({np.degrees(max_omega1):.1f} deg/s)")
    print(f"Max |omega2|     : {max_omega2:.3f} rad/s ({np.degrees(max_omega2):.1f} deg/s)")
    print(f"Mean Gravity g_R2: [{mean_g[0]:+.4e}, {mean_g[1]:+.4e}, {mean_g[2]:+.4e}] m/s^2")
    print(f"Residual g Norm  : {mean_g_norm:.4e} m/s^2 ({mean_g_norm / 9.81:.4e} g0)")
    print("=" * 50 + "\n")

    if args.plot:
        LOG.info("Generating trajectory diagnostic plots...")
        fig, axs = plt.subplots(2, 2, figsize=(11, 7))

        # Motor angles
        axs[0, 0].plot(traj.timestamp, traj.theta1, label=r"$\theta_1$ (inner)", color="tab:blue")
        axs[0, 0].plot(traj.timestamp, traj.theta2, label=r"$\theta_2$ (outer)", color="tab:orange")
        axs[0, 0].set_ylabel("Angle [rad]")
        axs[0, 0].set_title("Motor Angular Positions")
        axs[0, 0].legend()
        axs[0, 0].grid(True, alpha=0.3)

        # Angular velocities
        axs[0, 1].plot(traj.timestamp, kin.omega1, label=r"$\omega_1$", color="tab:blue")
        axs[0, 1].plot(traj.timestamp, kin.omega2, label=r"$\omega_2$", color="tab:orange")
        axs[0, 1].set_ylabel("Angular Velocity [rad/s]")
        axs[0, 1].set_title("Motor Velocities")
        axs[0, 1].legend()
        axs[0, 1].grid(True, alpha=0.3)

        # Apparent gravity components in R2
        axs[1, 0].plot(traj.timestamp, kin.g[:, 0], label=r"$g_x$")
        axs[1, 0].plot(traj.timestamp, kin.g[:, 1], label=r"$g_y$")
        axs[1, 0].plot(traj.timestamp, kin.g[:, 2], label=r"$g_z$")
        axs[1, 0].set_xlabel("Time [s]")
        axs[1, 0].set_ylabel(r"$g_{\mathcal{R}_2}\ [\mathrm{m/s^2}]$")
        axs[1, 0].set_title(r"Apparent Gravity Vector in $\mathcal{R}_2$")
        axs[1, 0].legend()
        axs[1, 0].grid(True, alpha=0.3)

        # Residual gravity convergence
        cum_mean_g = np.cumsum(kin.g, axis=0) / np.arange(1, len(traj.timestamp) + 1)[:, None]
        cum_norm = np.linalg.norm(cum_mean_g, axis=1)
        axs[1, 1].plot(traj.timestamp, cum_norm / 9.81, color="tab:red")
        axs[1, 1].set_xlabel("Time [s]")
        axs[1, 1].set_ylabel(r"$\|\langle \vec{g} \rangle\| / g_0$")
        axs[1, 1].set_title("Cumulative Time-Averaged Gravity")
        axs[1, 1].set_yscale("log")
        axs[1, 1].grid(True, which="both", alpha=0.3)

        plt.tight_layout()
        plt.show()

    if args.report:
        LOG.info(f"Report export requested: {args.report} (placeholder for stats module integration)")


def launch_trajectory_generate(args, LOG: logging.Logger):
    """Generate synthetic angular motion profiles and write them to a structured CSV file."""
    LOG.info(f"Generating trajectory profile '{args.mode}' (duration={args.duration}s, dt={args.dt}s)")
    t = np.arange(0.0, args.duration + args.dt, args.dt)

    if args.mode == "constant_speed":
        theta1 = (args.speed * t) % (2 * np.pi)
        theta2 = (args.speed * 0.7 * t) % (2 * np.pi)
    elif args.mode == "desynchronized_sine":
        # Desynchronized harmonic motion on both gimbals
        w1, w2 = args.speed, args.speed * np.sqrt(2)
        theta1 = np.pi * np.sin(w1 * t)
        theta2 = np.pi * np.sin(w2 * t)
    else:
        raise ValueError(f"Unknown trajectory generation mode: {args.mode}")

    traj = Trajectory(LOG=LOG)
    traj.timestamp = t
    traj.theta1 = theta1
    traj.theta2 = theta2
    traj.step_s = args.dt
    traj.duration_s = args.duration
    traj.description = f"{args.desc} [mode={args.mode}, speed={args.speed}]"
    traj.generation_date = str(datetime.datetime.now())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    traj.to_csv(filepath=str(args.output))


def launch_run(args, LOG: logging.Logger):
    """Extract run arguments, build physical models, and execute numerical simulation."""
    LOG.info(f"Loading motor trajectory from: {args.input}")
    traj = Trajectory(LOG=LOG)
    traj.from_csv(filepath=str(args.input))

    LOG.info("Computing kinematic profile (apparent gravity & angular tensors)...")
    kin = traj.compute_kinematics()

    # 1. Physical Parameter Resolution (Preset + CLI Overrides)
    params = {}
    if getattr(args, "preset", None) and args.preset in PRESETS:
        LOG.info(f"Applying physical preset: '{args.preset}'")
        params.update(PRESETS[args.preset])
    else:
        params.update({
            "radius": 1.5e-3,
            "rho": 1202.0,
            "rho_f": 1200.0,
            "mu_f": 1.412,
            "k": 0.0,
            "r_tube": 0.05,
        })

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
    if getattr(args, "tube_radius", None) is not None:
        params["r_tube"] = args.tube_radius

    # 2. Physics Objects Initialization
    x0_vec = np.array(args.x0, dtype=float)
    particle = Particle(radius=params["radius"], rho=params["rho"], x0=x0_vec)
    fluid = Fluid(rho=params["rho_f"], mu=params["mu_f"], k=params["k"])
    system = PhysicalSystem(particle=particle, fluid=fluid)

    LOG.info(
        f"Physical system initialized: tau_v={system.tau_v:.3e} s, "
        f"beta={system.beta:.4f}, tau_k={system.compute_tau_k()}"
    )

    # 3. Solver Execution
    LOG.info("Running RK4 overdamped solver...")
    solver = RK4Overdamped(system=system, r_tube=params["r_tube"], LOG=LOG)
    result = solver.solve(kin=kin, v0=np.zeros(3))

    max_reynolds = np.max(result.reynolds)
    LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
    if max_reynolds >= 0.1:
        LOG.warning(
            f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})! Creeping flow assumption may be violated."
        )

    # 4. Result Export
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


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================


def main():
    """Main CLI entrypoint for PRISMA."""
    parser = argparse.ArgumentParser(
        prog="prisma",
        description="PRISMA: Microscale inclusion simulation under RPM kinematics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: trajectory
    traj_parser = subparsers.add_parser(
        "trajectory",
        help="Inspect, visualize, or generate RPM motor trajectories.",
    )
    init_trajectory(traj_parser)

    # Subcommand: run
    run_parser = subparsers.add_parser(
        "run",
        help="Run particle numerical integration with RK4 solver.",
    )
    init_run(run_parser)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("PRISMA")

    if args.command == "trajectory":
        if args.trajectory_command == "show":
            launch_trajectory_show(args, logger)
        elif args.trajectory_command == "generate":
            launch_trajectory_generate(args, logger)
    elif args.command == "run":
        launch_run(args, logger)


if __name__ == "__main__":
    main()