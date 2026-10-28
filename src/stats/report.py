"""PRISMA Report Generation Module for Trajectories and Simulation Dynamics."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from src.stats.metrics import (
    compute_dispersion_tensor,
    compute_extreme_kinematics,
    compute_mean_vectorial_gravities,
    compute_residual_gravity_ratio,
    compute_spherical_coordinates,
    compute_total_angular_velocity_stats,
    compute_confinement_stats,
    compute_reynolds_stats,
    compute_spatial_dispersion_stats,
    compute_spectral_density,
)
from src.stats.plotting import (
    THEME,
    apply_axes_styling,
    render_mollweide_heatmap,
    render_motor_kinematics,
    render_unit_sphere_trajectory,
    render_particle_3d_confinement,
    render_spectral_and_phase_analysis,
    render_temporal_dynamics,
)
from src.trajectory.Trajectory import Trajectory
from src.core.models import KinematicProfile, PhysicalSystem, SimulationResult


class Report(ABC):
    """Abstract base contract for PRISMA reporting modules."""

    def __init__(self, output_path: Optional[Union[str, Path]] = None):
        self.output_path = Path(output_path) if output_path else None

    @abstractmethod
    def compute_metrics(self) -> dict:
        """Compute characteristic metrics dictionary."""
        pass

    @abstractmethod
    def generate_plots(self) -> dict:
        """Construct and return Matplotlib figures."""
        pass

    @abstractmethod
    def assemble_pdf(
        self, output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Compile and serialize figures into a multi-page PDF document."""
        pass

    @abstractmethod
    def show_CLI(self) -> None:
        """Print formatted summary metrics to standard output."""
        pass


class TrajectoryReport(Report):
    """Generates CLI diagnostics, Matplotlib plots, and 3-page PDF reports for RPM trajectories."""

    def __init__(
        self,
        trajectory: Trajectory,
        output_path: Optional[Union[str, Path]] = None,
    ):
        super().__init__(output_path=output_path)
        self.traj = trajectory
        self.metrics: dict = {}
        self.figures: dict = {}

    @classmethod
    def from_csv(
        cls,
        filepath: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        log=None,
    ) -> "TrajectoryReport":
        """Instantiate report directly by loading an existing CSV trajectory file."""
        import logging

        logger = log or logging.getLogger("PRISMA")
        traj = Trajectory(LOG=logger)
        traj.from_csv(filepath=str(filepath))
        return cls(trajectory=traj, output_path=output_path)

    def compute_metrics(self) -> dict:
        """Compute complete kinematic and statistical trajectory metrics."""
        kin = self.traj.compute_kinematics()

        mean_vectorial_g = compute_mean_vectorial_gravities(kin.g)
        residual_norm_series = compute_residual_gravity_ratio(kin.g)
        tensor, eigvals, isotropy = compute_dispersion_tensor(kin.g)
        extreme_motion = compute_extreme_kinematics(
            kin.omega1, kin.omega2, kin.timestamp
        )
        omega_stats = compute_total_angular_velocity_stats(kin.Omega)
        lon, lat = compute_spherical_coordinates(kin.g)

        final_mean_g = mean_vectorial_g[-1]
        final_residual_norm = float(np.linalg.norm(final_mean_g))

        self.metrics = {
            # Kinematic time series
            "timestamp": kin.timestamp,
            "theta1": kin.theta1,
            "theta2": kin.theta2,
            "omega1": kin.omega1,
            "omega2": kin.omega2,
            "Omega": kin.Omega,
            "Omega_dot": kin.Omega_dot,
            "g": kin.g,
            "mean_vectorial_g": mean_vectorial_g,
            "residual_norm_series": residual_norm_series,
            "omega_norm_series": omega_stats["omega_norm_series"],
            "lon": lon,
            "lat": lat,
            # Metadata
            "description": getattr(
                self.traj, "description", "No description provided"
            ),
            "generation_date": getattr(
                self.traj, "generation_date", "Unknown"
            ),
            "duration_s": float(self.traj.duration_s),
            "step_s": float(self.traj.step_s),
            "points_count": len(kin.timestamp),
            # Final scalars
            "final_mean_g": final_mean_g,
            "final_residual_norm": final_residual_norm,
            "final_residual_ratio": final_residual_norm / 9.81,
            "dispersion_tensor": tensor,
            "eigenvalues": eigvals,
            "isotropy_index": isotropy,
            "extreme_motion": extreme_motion,
            "omega_rms": omega_stats["omega_rms"],
            "max_omega": omega_stats["max_omega"],
            "kinetic_rot_energy": omega_stats["kinetic_rot_energy"],
        }
        return self.metrics

    def generate_plots(self) -> dict:
        """Construct and return the figures corresponding to the 3 report pages."""
        if not self.metrics:
            self.compute_metrics()

        m = self.metrics

        # ================= PAGE 1: Executive Summary & Overview =================
        fig1 = plt.figure(figsize=(11.5, 8.0))
        gs1 = fig1.add_gridspec(2, 2, width_ratios=[1.2, 1.0])

        # Subplot 1: Metadata & statistics summary card
        ax_text = fig1.add_subplot(gs1[:, 0])
        ax_text.axis("off")

        info_text = (
            "PRISMA MOTOR TRAJECTORY REPORT\n"
            "====================================================\n\n"
            "1. PROFILE METADATA\n"
            f" - Description       : {m['description']}\n"
            f" - Generation Date   : {m['generation_date']}\n"
            f" - Total Duration    : {m['duration_s']:.2f} s\n"
            f" - Sampling Step     : {m['step_s']:.4f} s ({m['points_count']} samples)\n\n"
            "2. MICROGRAVITY EFFECTIVENESS\n"
            f" - Mean Gravity <g>  : [{m['final_mean_g'][0]:+.3e}, {m['final_mean_g'][1]:+.3e}, {m['final_mean_g'][2]:+.3e}] m/s²\n"
            f" - Residual Norm     : {m['final_residual_norm']:.4e} m/s²\n"
            f" - Residual Ratio    : {m['final_residual_ratio']:.4e} g0\n"
            f" - Spatial Isotropy  : {m['isotropy_index']:.4f} (Ideal = 1.0000)\n"
            f" - Eigenvalues       : [{m['eigenvalues'][0]:.3f}, {m['eigenvalues'][1]:.3f}, {m['eigenvalues'][2]:.3f}]\n\n"
            "3. ROTATIONAL DYNAMICS\n"
            f" - Max |omega1|      : {m['extreme_motion']['max_omega1']:.3f} rad/s\n"
            f" - Max |omega2|      : {m['extreme_motion']['max_omega2']:.3f} rad/s\n"
            f" - Max |alpha1|      : {m['extreme_motion']['max_alpha1']:.3f} rad/s²\n"
            f" - Max |alpha2|      : {m['extreme_motion']['max_alpha2']:.3f} rad/s²\n"
            f" - Resulting RMS w   : {m['omega_rms']:.3f} rad/s\n"
            f" - Kinetic Energy    : {m['kinetic_rot_energy']:.3f} rad²/s²\n"
        )
        ax_text.text(
            0.05,
            0.95,
            info_text,
            transform=ax_text.transAxes,
            fontsize=9.5,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.8",
                facecolor=THEME["bg"],
                edgecolor=THEME["border"],
                alpha=0.9,
            ),
        )

        # Subplot 2: 3D Unit sphere coverage
        ax_3d = fig1.add_subplot(gs1[0, 1], projection="3d")
        render_unit_sphere_trajectory(m["g"], m["timestamp"], ax_3d)

        # Subplot 3: Cross-sectional horizontal scatter (gx vs gy)
        ax_trans = fig1.add_subplot(gs1[1, 1])
        apply_axes_styling(ax_trans)
        ax_trans.scatter(
            m["g"][:, 0],
            m["g"][:, 1],
            c=m["timestamp"],
            cmap="viridis",
            s=4,
            alpha=0.6,
            rasterized=True,
        )
        circle = plt.Circle(
            (0, 0),
            9.81,
            color="#718096",
            fill=False,
            linestyle="--",
            linewidth=0.9,
        )
        ax_trans.add_patch(circle)
        ax_trans.axhline(0, color="gray", linewidth=0.5)
        ax_trans.axvline(0, color="gray", linewidth=0.5)
        ax_trans.set_xlabel(r"$g_x\ [\mathrm{m/s^2}]$", fontsize=8)
        ax_trans.set_ylabel(r"$g_y\ [\mathrm{m/s^2}]$", fontsize=8)
        ax_trans.set_title(
            r"Transverse Orbit ($g_x, g_y$)",
            fontsize=10,
            fontweight="bold",
            color=THEME["primary"],
        )
        ax_trans.set_aspect("equal", "box")
        ax_trans.set_xlim([-10.5, 10.5])
        ax_trans.set_ylim([-10.5, 10.5])

        fig1.suptitle(
            "PRISMA Analysis Report - Page 1: Trajectory Metadata & Spatial Overview",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig1.tight_layout()

        # ================= PAGE 2: Base Motor Kinematics =================
        fig2 = plt.figure(figsize=(11.5, 8.0))
        render_motor_kinematics(m, fig2)
        fig2.suptitle(
            "PRISMA Analysis Report - Page 2: Gimbal States & Vectorized Kinematics",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig2.tight_layout()

        # ================= PAGE 3: Advanced Density & Distributions =================
        fig3 = plt.figure(figsize=(11.5, 8.0))

        # 1. Mollweide heatmap
        ax_moll = fig3.add_subplot(2, 2, (1, 2), projection="mollweide")
        render_mollweide_heatmap(m["lon"], m["lat"], ax_moll, bins=(72, 36))

        # 2. Angle probability distribution
        ax_dist = fig3.add_subplot(2, 2, 3)
        apply_axes_styling(ax_dist)
        bins_angle = np.linspace(-np.pi, np.pi, 37)
        ax_dist.hist(
            (m["theta1"] + np.pi) % (2 * np.pi) - np.pi,
            bins=bins_angle,
            density=True,
            alpha=0.6,
            color=THEME["secondary"],
            label=r"$\theta_1$ (Azimuth)",
        )
        ax_dist.hist(
            (m["theta2"] + np.pi) % (2 * np.pi) - np.pi,
            bins=bins_angle,
            density=True,
            alpha=0.6,
            color=THEME["accent"],
            label=r"$\theta_2$ (Tilt)",
        )
        ax_dist.axhline(
            1.0 / (2 * np.pi),
            color=THEME["text"],
            linestyle="--",
            linewidth=1.0,
            label="Ideal uniform",
        )
        ax_dist.set_xlabel("Angle [rad]", fontsize=8, fontweight="bold")
        ax_dist.set_ylabel("Probability Density", fontsize=8)
        ax_dist.set_title(
            "Angle Distribution Histogram",
            fontsize=10,
            fontweight="bold",
            color=THEME["primary"],
        )
        ax_dist.legend(frameon=True, facecolor="white", fontsize=8)

        # 3. Equirectangular heatmap without problematic TeX comparison operators
        ax_plate = fig3.add_subplot(2, 2, 4)
        apply_axes_styling(ax_plate)
        lon_deg = np.degrees(m["lon"])
        lat_deg = np.degrees(m["lat"])
        h2d = ax_plate.hist2d(
            lon_deg,
            lat_deg,
            bins=(60, 30),
            range=[[-180, 180], [-90, 90]],
            cmap="inferno",
            density=True,
        )
        ax_plate.set_xticks(np.arange(-180, 181, 60))
        ax_plate.set_yticks(np.arange(-90, 91, 30))
        ax_plate.set_xlabel(r"Azimuth $\phi$ [deg]", fontsize=8)
        ax_plate.set_ylabel(r"Tilt $\theta$ [deg]", fontsize=8)
        # Plain text range to avoid parser conflicts in different matplotlib versions
        ax_plate.set_title(
            r"Equirectangular Projection ($\phi \in [-\pi, \pi]$)",
            fontsize=10,
            fontweight="bold",
            color=THEME["primary"],
        )
        cbar_h = plt.colorbar(h2d[3], ax=ax_plate, shrink=0.8, pad=0.03)
        cbar_h.set_label("Density", fontsize=8)
        cbar_h.ax.tick_params(labelsize=7)

        fig3.suptitle(
            "PRISMA Analysis Report - Page 3: Advanced Spherical Densities & Spectra",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig3.tight_layout()

        self.figures = {
            "page1_summary": fig1,
            "page2_kinematics": fig2,
            "page3_advanced": fig3,
        }
        return self.figures

    def assemble_pdf(
        self, output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Assemble all 3 report pages into a single PDF document.

        Uses either the explicitly provided output_path or the one configured
        at class instantiation.
        """
        destination = output_path or self.output_path
        if destination is None:
            raise ValueError(
                "No output path specified. Provide it at instantiation or call assemble_pdf(path)."
            )

        out = Path(destination)
        out.parent.mkdir(parents=True, exist_ok=True)

        if not self.figures:
            self.generate_plots()

        with PdfPages(out) as pdf:
            pdf.savefig(self.figures["page1_summary"], dpi=250)
            pdf.savefig(self.figures["page2_kinematics"], dpi=250)
            pdf.savefig(self.figures["page3_advanced"], dpi=250)

        # Close canvas to prevent memory leaks and callback render exceptions
        for fig in self.figures.values():
            plt.close(fig)
        self.figures.clear()

        return out

    def show_CLI(self) -> None:
        """Display formatted diagnostic metrics in the console."""
        if not self.metrics:
            self.compute_metrics()

        m = self.metrics
        print("\n" + "=" * 55)
        print("          PRISMA TRAJECTORY DIAGNOSTIC SUMMARY         ")
        print("=" * 55)
        print(f"Description        : {m['description']}")
        print(f"Generation Date    : {m['generation_date']}")
        print(f"Duration           : {m['duration_s']:.2f} s")
        print(
            f"Sampling Step dt   : {m['step_s']:.4f} s ({m['points_count']} samples)"
        )
        print("-" * 55)
        print(
            f"Max |omega1|       : {m['extreme_motion']['max_omega1']:.3f} rad/s"
        )
        print(
            f"Max |omega2|       : {m['extreme_motion']['max_omega2']:.3f} rad/s"
        )
        print(
            f"Max |alpha1|       : {m['extreme_motion']['max_alpha1']:.3f} rad/s²"
        )
        print(
            f"Max |alpha2|       : {m['extreme_motion']['max_alpha2']:.3f} rad/s²"
        )
        print(f"Resulting RMS w    : {m['omega_rms']:.3f} rad/s")
        print("-" * 55)
        print(
            f"Mean Gravity <g>   : [{m['final_mean_g'][0]:+.3e}, {m['final_mean_g'][1]:+.3e}, {m['final_mean_g'][2]:+.3e}] m/s²"
        )
        print(
            f"Residual Ratio     : {m['final_residual_ratio']:.4e} g0 (Norm = {m['final_residual_norm']:.4e} m/s²)"
        )
        print(
            f"Isotropy Index     : {m['isotropy_index']:.4f} (Ideal isotropic = 1.000)"
        )
        print("=" * 55 + "\n")