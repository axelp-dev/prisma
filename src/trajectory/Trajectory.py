"""
PRISMA Trajectory module.
- describe a trajectory profile
- generate a given trajectory
- export/import trajectory
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

import src.core.conventions as conv
from src.config import PROFILES, TrajectoryConfig
from src.core.kinematics import CanonicalTwoAxis
from src.core.models import KinematicProfile
from src.stats.trajectory_report import TrajectoryReport
from src.trajectory.generators import (
    generate_centrifuge_sweep,
    generate_clinostat_1d,
    generate_constant_speed_ratio,
    generate_desynchronized_sine,
    generate_random_walk,
    generate_static_1g,
)
from src.utils import convert_to_pdf_path, get_metadata

GENERATOR_MAP = {
    "random_walk": generate_random_walk,
    "desynchronized_sine": generate_desynchronized_sine,
    "constant_speed_ratio": generate_constant_speed_ratio,
    "static_1g": generate_static_1g,
    "clinostat_1d": generate_clinostat_1d,
    "centrifuge_sweep": generate_centrifuge_sweep,
}


class Trajectory:
    def __init__(self, config: TrajectoryConfig):
        if config is None:
            raise RuntimeError("Unable to init Trajectory without TrajectoryConfig.")

        self.config = config
        self.LOG = config.LOG
        self.kin: KinematicProfile | None = None

        # Physics values containers
        self.canon2axis = CanonicalTwoAxis(n_axes=2)
        self.timestamp: np.ndarray | None = None
        self.theta1: np.ndarray | None = None
        self.theta2: np.ndarray | None = None
        self.omega1: np.ndarray | None = None
        self.omega2: np.ndarray | None = None

    # --------- Constructors --------------

    @classmethod
    def from_csv(cls, csv_path: str | Path, log: logging.Logger) -> "Trajectory":
        """Build a Trajectory instance and its TrajectoryConfig from an existing CSV file."""
        if log is None:
            raise RuntimeError("Cannot init TrajectoryConfig without LOG object.")

        input_file = Path(csv_path)
        if not input_file.exists():
            log.error(f"No such file {input_file} for trajectory CSV import!")
            raise FileNotFoundError(f"File not found: {input_file}")

        # Extract time series
        traj_df = pd.read_csv(input_file, comment="#")
        np_traj = traj_df.to_numpy(dtype=np.float64)
        timestamp = np_traj[:, 0]
        theta1 = np_traj[:, 1]
        theta2 = np_traj[:, 2]

        # Extract header metadata
        metadata = get_metadata(input_file)
        duration_s = float(metadata.get("duration_s", timestamp[-1]))
        step_s = float(metadata.get("step_s", timestamp[1] - timestamp[0]))

        config = TrajectoryConfig(
            LOG=log,
            input_path=input_file,
            output_path=None,
            report_path=convert_to_pdf_path(input_file),
            date=str(metadata.get("date", "Unknown")),
            duration_s=duration_s,
            step_s=step_s,
            profile=str(metadata.get("profile", "unknown")),
            desc=str(metadata.get("description", "No description provided")),
            log_report=False,
        )

        instance = cls(config)
        instance.timestamp = timestamp
        instance.theta1 = theta1
        instance.theta2 = theta2
        # Keep omega1/omega2 as None so compute_kinematics() derives them via gradient
        log.info(f"Successfully loaded trajectory from {input_file}!")
        return instance

    # --------- Basic commands --------------

    def generate(self) -> None:
        """Launch synthetic trajectory generation, CSV serialization, and optional reporting."""
        self.LOG.info("Launching trajectory generation using config:")
        print(self.config)

        # Generate analytical/stochastic arrays in memory
        self._load_profile_instructions()

        # Export to CSV
        self._to_csv()
        self.LOG.info(
            f"Successfully generated trajectory into {self.config.output_path}!"
        )

        # Generate PDF report using exact analytical speeds already in memory
        if self.config.log_report:
            self.show()

    def show(self, pdf_path: str | Path | None = None) -> None:
        """Compute kinematics if needed, display CLI metrics, and assemble PDF report."""
        if pdf_path is not None:
            self.config.report_path = Path(pdf_path)
        elif self.config.report_path is None and self.config.input_path is not None:
            self.config.report_path = convert_to_pdf_path(Path(self.config.input_path))

        if self.kin is None:
            self.kin = self.compute_kinematics()

        report_builder = TrajectoryReport(self.config, self.kin)
        report_builder.generate_report()

    # --------- Public Helper --------------

    def compute_kinematics(self) -> KinematicProfile:
        """Compute full 3D kinematics in frame R2 from in-memory angles."""
        if self.timestamp is None or self.theta1 is None or self.theta2 is None:
            raise ValueError(
                "Trajectory angles are not loaded. Call generate() or Trajectory.from_csv() first."
            )

        # À partir d'ici, Pyright sait que timestamp, theta1 et theta2 sont strictement np.ndarray
        g = self._get_gravity_positions(self.theta1, self.theta2)
        if self.omega1 is None or self.omega2 is None:
            self.omega1, self.omega2 = self._get_omegas(
                self.theta1, self.theta2, self.timestamp
            )

        Omega = self._process_angular_velocity(self.theta1, self.omega1, self.omega2)
        Omega_dot = np.gradient(Omega, self.timestamp, axis=1)

        self.kin = KinematicProfile(
            timestamp=self.timestamp,
            omega1=self.omega1,
            omega2=self.omega2,
            theta1=self.theta1,
            theta2=self.theta2,
            Omega=Omega,
            Omega_dot=Omega_dot,
            g=g,
        )
        return self.kin

    # --------- Private helpers --------------

    def _to_csv(self) -> None:
        """Write (N, 3) trajectory arrays and metadata header into a CSV file."""
        if self.config.output_path is None:
            raise ValueError("No output_path configured in TrajectoryConfig.")

        out_path = Path(self.config.output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as file:
            file.write(f"# profile : {self.config.profile}\n")
            file.write(f"# description : {self.config.desc}\n")
            file.write("# NB : All positions are in radians and steps in seconds.\n")
            file.write(f"# duration_s : {self.config.duration_s}\n")
            file.write(f"# step_s : {self.config.step_s}\n")
            file.write(f"# date : {self.config.date}\n")
            file.write("# ==============================================\n")
            file.write("timestamp, theta1, theta2\n")

            traj = np.array([self.timestamp, self.theta1, self.theta2])
            np.savetxt(file, traj.T, delimiter=",")

    def _load_profile_instructions(self) -> None:
        """Dispatch profile generation using GENERATOR_MAP."""
        generator_fn = GENERATOR_MAP.get(self.config.profile)
        if generator_fn is None:
            raise ValueError(
                f"Invalid trajectory profile '{self.config.profile}'. "
                f"Available: {list(PROFILES.keys())}"
            )

        values = generator_fn(self.config.duration_s, self.config.step_s)
        self.timestamp, self.theta1, self.theta2, self.omega1, self.omega2 = values

    def _get_gravity_positions(
        self, theta1: np.ndarray, theta2: np.ndarray
    ) -> np.ndarray:
        """Compute apparent gravity vector g_R2(t) in sample frame."""
        angles = np.array([theta1, theta2]).T
        rot = self.canon2axis.rotation(angles)
        return rot.apply(conv.G_LAB)

    def _get_omegas(
        self, theta1: np.ndarray, theta2: np.ndarray, timestamp: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute numerical angular velocities via central finite differences."""
        omega1 = np.gradient(theta1, timestamp)
        omega2 = np.gradient(theta2, timestamp)
        return omega1, omega2

    def _process_angular_velocity(
        self, theta1: np.ndarray, omega1: np.ndarray, omega2: np.ndarray
    ) -> np.ndarray:
        """Project angular velocity vector Omega into moving frame R2."""
        return np.array([-omega2 * np.sin(theta1), omega2 * np.cos(theta1), omega1])
