from src.core.models import KinematicProfile, PhysicalSystem, SimulationResult
from src.stats.report import Report

from src.stats.metrics import (
    compute_confinement_stats,
    compute_reynolds_stats,
    compute_spatial_dispersion_stats,
    compute_spectral_density,
)
from src.stats.plotting import (
    render_particle_3d_confinement,
    render_spectral_and_phase_analysis,
    render_temporal_dynamics,
    THEME
)

from pathlib import Path
import numpy as np 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class SimulationReport(Report):
    """Generates CLI diagnostics, Matplotlib plots, and 3-page PDF reports for numerical particle simulations."""

    def __init__(
        self,
        result: SimulationResult,
        kin: KinematicProfile = None,
        system: PhysicalSystem = None,
        r_tube: float = 0.05,
        output_path = None
    ):
        super().__init__(output_path=output_path)
        self.result = result
        self.kin = kin
        self.system = system
        self.r_tube = float(r_tube)
        self.metrics: dict = {}
        self.figures: dict = {}

    @classmethod
    def from_csv(
        cls,
        filepath,
        r_tube: float = 0.05,
        output_path = None
    ) -> "SimulationReport":
        """Instantiate report from saved simulation output CSV."""
        import pandas as pd

        df = pd.read_csv(filepath)
        result = SimulationResult(
            timestamp=df["timestamp"].to_numpy(),
            positions=df[["x", "y", "z"]].to_numpy(),
            velocities=df[["vx", "vy", "vz"]].to_numpy(),
            reynolds=df["reynolds"].to_numpy(),
        )
        return cls(result=result, r_tube=r_tube, output_path=output_path)

    def compute_metrics(self) -> dict:
        """Compute full dynamic, confinement, spatial, and spectral metrics."""
        t = np.asarray(self.result.timestamp, dtype=float).flatten()
        dt = float(t[1] - t[0]) if len(t) > 1 else 0.01

        # Fallback for initial anchor if system is not supplied
        x0 = (
            self.system.particle.x0
            if self.system is not None
            else self.result.positions[0]
        )

        dispersion = compute_spatial_dispersion_stats(
            self.result.positions, x0
        )
        confinement = compute_confinement_stats(
            self.result.positions, self.r_tube
        )
        reynolds = compute_reynolds_stats(self.result.reynolds)

        # FFT Analysis on vertical displacement z(t) and vertical apparent gravity g_z(t)
        freqs_z, amp_z = compute_spectral_density(
            self.result.positions[:, 2], dt
        )
        if self.kin is not None:
            freqs_g, amp_g = compute_spectral_density(self.kin.g[:, 2], dt)
        else:
            freqs_g, amp_g = freqs_z, np.zeros_like(amp_z)

        # Viscoelastic cutoff frequency if actin stiffness k is enabled
        tau_k_cutoff_hz = None
        if self.system is not None:
            tau_k = self.system.compute_tau_k()
            if tau_k:
                tau_k_cutoff_hz = 1.0 / (2.0 * np.pi * tau_k)

        scale = 1e3 if self.r_tube >= 1e-3 else 1e6
        unit_str = "mm" if scale == 1e3 else r"\mu\mathrm{m}"

        self.metrics = {
            "timestamp": t,
            "positions": self.result.positions,
            "velocities": self.result.velocities,
            "reynolds": self.result.reynolds,
            "r_tube": self.r_tube,
            "x0": x0,
            "scale": scale,
            "unit_str": unit_str,
            # Confinement & spatial metrics
            "radial_distances": confinement["radial_distances"],
            "max_radial_distance": confinement["max_radial_distance"],
            "min_wall_distance": confinement["min_wall_distance"],
            "contact_time_ratio": confinement["contact_time_ratio"],
            "net_drift": dispersion["net_drift"],
            "total_path_length": dispersion["total_path_length"],
            "tortuosity": dispersion["tortuosity"],
            "gyration_radius": dispersion["gyration_radius"],
            "rms_anchor_distance": dispersion["rms_anchor_distance"],
            # Reynolds metrics
            "max_re": reynolds["max_re"],
            "mean_re": reynolds["mean_re"],
            "re_exceeded": reynolds["re_exceeded"],
            # Spectral metrics
            "fft_freqs_z": freqs_z,
            "fft_amp_z": amp_z,
            "fft_freqs_g": freqs_g,
            "fft_amp_g": amp_g,
            "tau_k_cutoff_hz": tau_k_cutoff_hz,
        }
        return self.metrics

    def generate_plots(self) -> dict:
        """Construct Matplotlib figures for the 3 simulation report pages."""
        if not self.metrics:
            self.compute_metrics()

        m = self.metrics

        # ================= PAGE 1: Physical Parameters & 3D Confinement =================
        fig1 = plt.figure(figsize=(11.5, 8.0))
        gs1 = fig1.add_gridspec(2, 2, width_ratios=[1.2, 1.0])

        ax_text = fig1.add_subplot(gs1[:, 0])
        ax_text.axis("off")

        sys_info = "Not supplied (CSV loaded)"
        if self.system is not None:
            sys_info = (
                f" - Particle Radius   : {self.system.particle.radius:.3e} m\n"
                f" - Particle Density  : {self.system.particle.rho:.1f} kg/m³\n"
                f" - Fluid Density     : {self.system.fluid.rho:.1f} kg/m³\n"
                f" - Fluid Viscosity   : {self.system.fluid.mu:.3e} Pa·s\n"
                f" - Actin Stiffness k : {self.system.fluid.k:.3e} N/m\n"
                f" - Stokes Time tau_v : {self.system.tau_v:.3e} s\n"
            )

        info_text = (
            "PRISMA NUMERICAL SIMULATION REPORT\n"
            "====================================================\n\n"
            "1. PHYSICAL SYSTEM\n"
            f"{sys_info}"
            f" - Tube Radius R_tube: {m['r_tube']:.3e} m\n\n"
            "2. STOKES REGIME CONTROL\n"
            f" - Maximum Re_p      : {m['max_re']:.3e} {'(VALID)' if not m['re_exceeded'] else '(VIOLATION >= 0.1)'}\n"
            f" - Mean Re_p         : {m['mean_re']:.3e}\n\n"
            "3. KINEMATIC DISPERSION & DRIFT\n"
            f" - Net Drift Length  : {m['net_drift'] * m['scale']:.3f} {m['unit_str']}\n"
            f" - Total Path Length : {m['total_path_length'] * m['scale']:.3f} {m['unit_str']}\n"
            f" - Path Tortuosity   : {m['tortuosity']:.2f}\n"
            f" - Gyration Radius Rg: {m['gyration_radius'] * m['scale']:.3f} {m['unit_str']}\n"
            f" - RMS Anchor Offset : {m['rms_anchor_distance'] * m['scale']:.3f} {m['unit_str']}\n\n"
            "4. CONFINEMENT ASSESSMENT\n"
            f" - Min Wall Clearance: {m['min_wall_distance'] * m['scale']:.3f} {m['unit_str']}\n"
            f" - Boundary Contact %: {m['contact_time_ratio'] * 100:.2f} %\n"
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

        ax_3d = fig1.add_subplot(gs1[:, 1], projection="3d")
        render_particle_3d_confinement(
            m["positions"], m["x0"], m["r_tube"], m["timestamp"], ax_3d
        )

        fig1.suptitle(
            "PRISMA Simulation Report - Page 1: Physical Parameters & 3D Confinement",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig1.tight_layout()

        # ================= PAGE 2: Temporal Dynamics & Stokes Limit =================
        fig2 = plt.figure(figsize=(11.5, 8.0))
        render_temporal_dynamics(m, fig2)
        fig2.suptitle(
            "PRISMA Simulation Report - Page 2: Temporal Trajectories & Hydrodynamic Regime",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig2.tight_layout()

        # ================= PAGE 3: Spectral (FFT) & Phase Analysis =================
        fig3 = plt.figure(figsize=(11.5, 8.0))
        render_spectral_and_phase_analysis(m, fig3)
        fig3.suptitle(
            "PRISMA Simulation Report - Page 3: Spectral (FFT) Response & Phase Space",
            fontsize=12,
            fontweight="bold",
            color=THEME["primary"],
            y=0.98,
        )
        fig3.tight_layout()

        self.figures = {
            "page1_summary": fig1,
            "page2_dynamics": fig2,
            "page3_spectral": fig3,
        }
        return self.figures

    def assemble_pdf(self) -> Path:
        """Assemble all 3 simulation report pages into a single PDF document."""
        destination = self.output_path
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
            pdf.savefig(self.figures["page2_dynamics"], dpi=250)
            pdf.savefig(self.figures["page3_spectral"], dpi=250)

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
        print("          PRISMA SIMULATION DIAGNOSTIC SUMMARY         ")
        print("=" * 55)
        print(f"Total Duration     : {m['timestamp'][-1]:.2f} s")
        print(f"Confinement R_tube : {m['r_tube']:.3e} m")
        print("-" * 55)
        print(f"Maximum Re_p       : {m['max_re']:.3e}")
        print(f"Mean Re_p          : {m['mean_re']:.3e}")
        print(f"Creeping Regime    : {'VALID (< 0.1)' if not m['re_exceeded'] else 'VIOLATED (>= 0.1)'}")
        print("-" * 55)
        print(f"Net Drift          : {m['net_drift'] * m['scale']:.3f} {m['unit_str']}")
        print(f"Path Length        : {m['total_path_length'] * m['scale']:.3f} {m['unit_str']}")
        print(f"Path Tortuosity    : {m['tortuosity']:.2f}")
        print(f"Gyration Radius Rg : {m['gyration_radius'] * m['scale']:.3f} {m['unit_str']}")
        print(f"Min Wall Clearance : {m['min_wall_distance'] * m['scale']:.3f} {m['unit_str']}")
        print("=" * 55 + "\n")