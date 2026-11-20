"""
General config definition for Trajectory and Simulation classes.
Used and managed by all classes, instanciated by cli.py
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# --- Presets & Profiles -----------------------------------------

# Simulation profiles
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

# Trajectory generation profiles
PROFILES = {
    # Stochastic speed variation mimicking commercial 3D RPM random walk modes
    "random_walk": {
        "omega_max": np.pi / 2,  # Upper angular velocity bound [rad/s] (~15 RPM)
        "omega_min": 0.0,  # Lower angular velocity bound [rad/s]
    },
    # Harmonic desynchronized oscillations spanning the 3D spherical space (Lissajous)
    "desynchronized_sine": {
        "omega_1": 5.0
        * np.sqrt(2),  # Inner gimbal angular pulsation [rad/s] (incommensurate ratio)
        "omega_2": 2.0,  # Outer gimbal angular pulsation [rad/s]
        "phi": 15.0,  # Phase offset between axes [rad]
        "amp1": np.pi,  # Inner gimbal oscillation amplitude [rad]
        "amp2": np.pi,  # Outer gimbal oscillation amplitude [rad]
    },
    # Continuous bi-axial rotation using an irrational gear ratio to prevent closed orbits
    "constant_speed_ratio": {
        "omega_max": np.pi / 2,  # Upper speed bound for random drawing [rad/s]
        "omega_min": 0.0,  # Lower speed bound for random drawing [rad/s]
        "factor": 0.732,  # Non-harmonic velocity coupling ratio (omega2 = factor * omega1)
    },
    # Ground-based baseline control reference (static laboratory 1g orientation)
    "static_1g": {
        "omega_1": 0.0,  # Inner gimbal locked speed [rad/s]
        "omega_2": 0.0,  # Outer gimbal locked speed [rad/s]
    },
    # Classical single-axis 2D clinostat rotation (rotational gravity averaging in a plane)
    "clinostat_1d": {
        "omega_1": 0.0,  # Inner gimbal fixed along rotation axis [rad/s]
        "omega_2": np.pi
        / 4.0,  # Outer gimbal continuous rotation velocity [rad/s] (~7.5 RPM)
    },
    # Asymptotic exponential speed ramp for centrifugal detachment and boundary testing
    "centrifuge_sweep": {
        "omega_max": np.pi,  # Asymptotic maximum speed ceiling [rad/s] (~30 RPM)
        "tau": 25.0,  # Characteristic saturation time constant [s] (63.2% of omega_max at t = tau)
    },
}


# --- Main Config ----------------------------------------------------


@dataclass
class Config:
    LOG: logging.Logger

    @staticmethod
    def _render_table(
        title: str, sections: list[tuple[str, list[tuple[str, Any]]]]
    ) -> str:
        """Render a fixed-width ASCII/Unicode key-value table for CLI output."""
        key_w = 18
        val_w = 42
        total_w = key_w + val_w + 5

        top = f"┌{'─' * (total_w - 2)}┐"
        mid = f"├{'─' * (total_w - 2)}┤"
        bot = f"└{'─' * (total_w - 2)}┘"

        lines = [
            "",
            top,
            f"│ {title.center(total_w - 4)} │",
        ]

        for sec_title, rows in sections:
            lines.append(mid)
            if sec_title:
                lines.append(f"│ [{sec_title}]{' ' * (total_w - len(sec_title) - 6)} │")
            for k, v in rows:
                val_str = str(v) if v is not None else "(none)"
                if len(val_str) > val_w:
                    val_str = "..." + val_str[-(val_w - 3) :]
                lines.append(f"│  {k:<{key_w}} : {val_str:<{val_w}}│")

        lines.append(bot)
        return "\n".join(lines)


# --- TrajectoryConfig ----------------------------------------------------


@dataclass
class TrajectoryConfig(Config):
    # Filepaths
    input_path: Path | None = None  # CSV pre-generated trajectory
    output_path: Path | None = None  # Filepath to log the generated trajectory
    report_path: Path | None = None  # Filepath for the trajectory PDFReport
    date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Physics params
    duration_s: float = 60.0
    step_s: float = 1.0
    profile: str = "random_walk"
    desc: str | None = None

    # Flags
    log_report: bool = True

    def __str__(self) -> str:
        samples = (
            int(self.duration_s / self.step_s) if self.step_s and self.step_s > 0 else 0
        )
        sections = [
            (
                "General & Metadata",
                [
                    ("Date", self.date),
                    ("Profile", self.profile),
                    ("Description", self.desc or "(default)"),
                ],
            ),
            (
                "Discretization",
                [
                    ("Duration", f"{self.duration_s:.2f} s"),
                    ("Step (dt)", f"{self.step_s:.4f} s ({samples} samples)"),
                ],
            ),
            (
                "I/O & Reporting",
                [
                    ("Input CSV", self.input_path),
                    ("Output CSV", self.output_path),
                    ("Report PDF", self.report_path),
                    ("Auto-report", "Enabled" if self.log_report else "Disabled"),
                ],
            ),
        ]
        return self._render_table("PRISMA TRAJECTORY CONFIGURATION", sections)


# --- SimulationConfig ----------------------------------------------------


@dataclass
class SimulationConfig(Config):
    # Main arguments
    input_file: str
    output_file: str

    # Physical overrides
    init_pos: np.ndarray
    particle_radius: float
    tube_radius: float
    rho: float
    rho_f: float
    mu_f: float
    k: float

    log_report: bool = True
    preset: str = "statolith"

    def __str__(self) -> str:
        x0 = self.init_pos if self.init_pos is not None else [0.0, 0.0, 0.0]
        x0_fmt = f"[{x0[0]:.2e}, {x0[1]:.2e}, {x0[2]:.2e}] m"
        sections = [
            (
                "I/O & Setup",
                [
                    ("Preset", self.preset),
                    ("Input Trajectory", self.input_file),
                    ("Output Result", self.output_file),
                    ("Auto-report", "Enabled" if self.log_report else "Disabled"),
                ],
            ),
            (
                "Particle & Confinement",
                [
                    ("Initial Anchor x0", x0_fmt),
                    ("Particle Radius R", f"{self.particle_radius:.3e} m"),
                    ("Particle Density", f"{self.rho:.1f} kg/m³"),
                    ("Tube Radius R_tube", f"{self.tube_radius:.3e} m"),
                ],
            ),
            (
                "Fluid & Viscoelasticity",
                [
                    ("Fluid Density", f"{self.rho_f:.1f} kg/m³"),
                    ("Dynamic Viscosity", f"{self.mu_f:.3e} Pa·s"),
                    ("Actin Stiffness k", f"{self.k:.3e} N/m"),
                ],
            ),
        ]
        return self._render_table("PRISMA SIMULATION CONFIGURATION", sections)
