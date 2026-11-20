"""
Simulation container for all simulation operations (run, generate report, etc...)
"""

import ast
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import SimulationConfig, TrajectoryConfig
from src.core.models import (
    Fluid,
    KinematicProfile,
    Particle,
    PhysicalSystem,
    SimulationResult,
)
from src.simulation.solver import RK4Overdamped
from src.stats.simulation_report import SimulationReport
from src.trajectory.Trajectory import Trajectory
from src.utils import *


class Simulation:
    def __init__(
        self,
        config: SimulationConfig | None = None,
    ):

        # Init attributes
        self.kin: KinematicProfile | None = None
        self.system: PhysicalSystem | None = None
        self.result: SimulationResult | None = None
        self.simulation_report: SimulationReport | None = None
        self.trajectory: Trajectory | None = None

        if config == None:
            raise RuntimeError("Unable to init Simulation without SimulationConfig.")

        # Building Simulation() from SimulationConfig object
        self.config = config

        # Init PDF report path if asked
        if self.config.log_report:
            # Store PDF report next to simulation result
            self.report_path = convert_to_pdf_path(self.config.output_file)

    # --- Public Methods -----------------------------------------------

    def run(self):
        """Launch simulation using RK4Overdamped solver"""

        # Init trajectory & kinematics from CSV file
        self.kin, self.trajectory = self._load_trajectory()

        # Init PhysicalSystem
        self.system = self._build_physical_system()

        # --- Simulating ---
        self.config.LOG.info(
            f"Physical system initialized: tau_v={self.system.tau_v:.3e} s, "
            f"beta={self.system.beta:.4f}, tau_k={self.system.compute_tau_k()}"
        )

        self.config.LOG.info("Running RK4 overdamped solver...")
        # Creating solver object
        solver = RK4Overdamped(
            system=self.system, r_tube=self.config.tube_radius, LOG=self.config.LOG
        )

        # Launching solving...
        self.result = solver.solve(kin=self.kin, v0=np.zeros(3))

        # Check reynolds
        self._log_reynold_summary(self.result)

        # Writing result as CSV file
        self._to_CSV(self.result)

        # Creating SimulationReport from CLI object
        simulation_report = SimulationReport(
            result=self.result,
            config=self.config,
            kin=self.kin,
            system=self.system,
            r_tube=self.config.tube_radius,
            output_path=self.report_path,
        )

        if self.config.log_report:
            self.show(simulation_report)

    def _log_reynold_summary(self, result: SimulationResult):
        """Compute reynolds summary and display it"""

        # Extract metrics
        max_reynolds = np.max(result.reynolds)
        self.config.LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
        if max_reynolds >= 0.1:
            self.config.LOG.warning(f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})!")

    def show(
        self,
        simulation_report: SimulationReport | None = None,
        pdf_path: str | None = None,
    ):
        """
        Displaying simulation result on CLI and generating PDF
        report if asked.
        """
        # --- Init report builder ---
        if simulation_report is None:
            report = self._init_report()
        else:
            report = simulation_report

        if pdf_path is not None:
            report.output_path = pdf_path
        else:
            # Store PDF report next to simulation result
            report.output_path = convert_to_pdf_path(self.config.output_file)

        report._show_CLI()

        # --- Build report ----
        self.config.LOG.info(f"Generating simulation report into {report.output_path}")
        report._assemble_pdf()
        self.config.LOG.info("Simulation PDF report successfully generated.")

    # --- Private Methods -----------------------------------------------

    def _load_trajectory(self) -> tuple[KinematicProfile, Trajectory]:
        """Load CSV trajectory file"""

        self.config.LOG.info(f"Loading motor trajectory from: {self.config.input_file}")

        # --- Loading trajectory ---
        # Creating minimal TrajectoryConfig to open CSV trajectory
        traj_config = TrajectoryConfig(
            LOG=self.config.LOG,
            input_path=Path(self.config.input_file),
            output_path=None,
            report_path=None,
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
        )
        trajectory = Trajectory(traj_config)
        kin = trajectory.compute_kinematics()
        return kin, trajectory

    def _build_physical_system(self) -> PhysicalSystem:
        """Build physical system from trajectory"""

        # Initial position
        x0_vec = np.array(self.config.init_pos, dtype=float)
        # Particle object
        particle = Particle(
            radius=self.config.particle_radius, rho=self.config.rho, x0=x0_vec
        )
        # Fluid object
        fluid = Fluid(rho=self.config.rho_f, mu=self.config.mu_f, k=self.config.k)

        return PhysicalSystem(particle=particle, fluid=fluid)

    def _init_report(self) -> SimulationReport:
        """Init SimulationReport object from
        self.config container"""

        # Import simulation report from result
        return SimulationReport.from_csv(
            filepath=self.config.output_file,
            r_tube=self.config.tube_radius,
            output_path=self.report_path,
        )

    def _to_CSV(self, result: SimulationResult):
        """ "Save SimulationResult as CSV file"""
        self.config.LOG.info(f"Writing SimulationResult into {self.config.output_file}")

        # --- Creating output path ---
        output_path = Path(self.config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.LOG.info(f"Exporting trajectory results to {output_path}")

        # --- Writing Metadata ---
        # Converting SimulationConfig as dict
        dict_config = asdict(self.config)
        with open(output_path, "w") as file:
            file.write("# ===============================================\n")
            file.write("#             SIMULATION RESULT\n")
            file.write("# ===============================================\n")
            for key in dict_config:
                if key != "LOG":
                    # Write metadata as '# key : value' content in CSV file
                    content = f"# {key!s} : {dict_config[key]!s}\n"
                    file.write(content)
            file.write("\n")

        # --- Creating dataframe ---
        df_out = pd.DataFrame(
            {
                "timestamp": result.timestamp,
                "x": result.positions[:, 0],
                "y": result.positions[:, 1],
                "z": result.positions[:, 2],
                "vx": result.velocities[:, 0],
                "vy": result.velocities[:, 1],
                "vz": result.velocities[:, 2],
                "reynolds": result.reynolds,
            }
        )
        # Writting file
        df_out.to_csv(output_path, index=False, mode="a")

        self.config.LOG.info(
            f"Succesfully saved simulation into : {self.config.output_file}"
        )

    @staticmethod
    def _parse_header(input_file: str):
        """Parse SimulationResult header to get metadata"""
        metadata = {}

        # Open file and readlines
        with open(input_file, "r") as file:
            for line in file:
                line = line.strip()

                # Extract only metadata
                if line.startswith("=") or line == "SIMULATION RESULT":
                    continue
                if not line.startswith("#"):
                    break
                clean_line = line.lstrip("#").strip()
                if ":" not in clean_line:
                    continue

                # Clean line
                key, raw_val = clean_line.split(":", 1)
                key = key.strip()
                raw_val = raw_val.strip()

                if raw_val == "None":
                    val = None
                elif raw_val == "True":
                    val = True
                elif raw_val == "False":
                    val = False
                elif raw_val.startswith("[") and raw_val.endswith("]"):
                    try:
                        parsed_list = ast.literal_eval(raw_val)
                        val = np.array(parsed_list, dtype=float)
                    except (ValueError, SyntaxError):
                        val = raw_val
                else:
                    try:
                        val = float(raw_val)
                    except ValueError:
                        val = raw_val

                metadata[key] = val

        return metadata

    @classmethod
    def from_csv(cls, csv_path: str, log: logging.Logger) -> "Simulation":
        """Build SimulationResult and SimulationConfig from existing CSV file"""

        if log == None:
            raise RuntimeError(
                "[ERROR] Cannot init SimulationConfig without LOG object"
            )

        # --- Build Config ---
        metadata = cls._parse_header(csv_path)
        # print(metadata)
        config = SimulationConfig(
            input_file=metadata["input_file"],
            output_file=csv_path,
            log_report=metadata["log_report"],
            preset=metadata["preset"],
            init_pos=metadata["init_pos"],
            particle_radius=metadata["particle_radius"],
            tube_radius=metadata["tube_radius"],
            rho=metadata["rho"],
            rho_f=metadata["rho_f"],
            mu_f=metadata["mu_f"],
            k=metadata["k"],
            LOG=log,
        )
        # Instanciate simulation
        sim = cls(config)
        print(config)

        # --- Build Result ---
        # Read csv_file content
        raw_results = pd.read_csv(csv_path, comment="#")
        timestamp = raw_results["timestamp"].to_numpy(dtype=np.float64)
        positions = raw_results[["x", "y", "z"]].to_numpy(dtype=np.float64)
        velocities = raw_results[["vx", "vy", "vz"]].to_numpy(dtype=np.float64)
        reynolds = raw_results["reynolds"].to_numpy(dtype=np.float64)
        # Build SimulationResult object
        result = SimulationResult(
            timestamp=timestamp,
            positions=positions,
            velocities=velocities,
            reynolds=reynolds,
        )

        sim.result = result
        return sim
