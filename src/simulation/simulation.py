"""
Simulation container for all simulation operations (run, generate report, etc...)
"""

import numpy as np
from pathlib import Path
import pandas as pd

from src.config import SimulationConfig, TrajectoryConfig
from src.trajectory.Trajectory import Trajectory
from src.utils import * 
from src.core.models import Particle, Fluid, PhysicalSystem   
from src.simulation.solver import RK4Overdamped
from src.stats.simulation_report import SimulationReport

class Simulation: 

    def __init__(self, config: SimulationConfig): 
        self.config = config
        self.simulation_report = None

        # Init PDF report path if asked 
        if self.config.log_report: 
            # Store PDF report next to simulation result 
            self.report_path = convert_to_pdf_path(self.config.output_file)
        else: 
            self.report_path = None
        

    def load_trajectory(self): 
        """
        Load CSV trajectory file
        """
        self.config.LOG.info(f"Loading motor trajectory from: {self.config.input_file}")
        # --- Loading trajectory --- 
        # Creating minimal TrajectoryConfig to open CSV trajectory
        traj_config = TrajectoryConfig(
            LOG=self.config.LOG, 
            input_path=self.config.input_file, 
            output_path=None, 
            report_path=None, 
            date=None, 
        )
        trajectory = Trajectory(traj_config)
        # Load trajectory profile 
        self.kin = trajectory.compute_kinematics()
    

    def launch_run(self): 
        """
        Launch simulation run
        """
        
        # --- Init simulation Math config 
        x0_vec = np.array(self.config.init_pos, dtype=float)
        self.particle = Particle(
            radius=self.config.particle_radius, 
            rho=self.config.rho, 
            x0=x0_vec)
        self.fluid = Fluid(
            rho=self.config.rho_f, 
            mu=self.config.mu_f, 
            k=self.config.k
        )
        self.system = PhysicalSystem(particle=self.particle, fluid=self.fluid)

        # --- Simulating...
        self.config.LOG.info(
        f"Physical system initialized: tau_v={self.system.tau_v:.3e} s, "
        f"beta={self.system.beta:.4f}, tau_k={self.system.compute_tau_k()}"
        )

        self.config.LOG.info("Running RK4 overdamped solver...")
        solver = RK4Overdamped(system=self.system, r_tube=self.config.tube_radius, LOG=self.config.LOG)
        self.result = solver.solve(kin=self.kin, v0=np.zeros(3))

        max_reynolds = np.max(self.result.reynolds)
        self.config.LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
        if max_reynolds >= 0.1:
            self.config.LOG.warning(
                f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})! Creeping flow assumption may be violated."
            )

        # --- Saving result as CSV ---
        output_path = Path(self.config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.LOG.info(f"Exporting trajectory results to {output_path}")

        df_out = pd.DataFrame({
            "timestamp": self.result.timestamp,
            "x": self.result.positions[:, 0],
            "y": self.result.positions[:, 1],
            "z": self.result.positions[:, 2],
            "vx": self.result.velocities[:, 0],
            "vy": self.result.velocities[:, 1],
            "vz": self.result.velocities[:, 2],
            "reynolds": self.result.reynolds,
        })
        df_out.to_csv(output_path, index=False)

        # --- Displaying CLI output
        # Init SimulationResult object
        self.simulation_report = SimulationReport(
            config=self.config,
            result=self.result, 
            kin=self.kin, 
            system=self.system, 
            r_tube=self.config.tube_radius, 
            output_path=self.report_path
        )

    def report(self):
        """
        Displaying simulation result on CLI and generating PDF
        report if asked. 
        """
        # Instanciate SimulationConfig if not created 
        if self.simulation_report == None: 
            # Import simulation report from result
            self.simulation_report = SimulationReport.from_csv(
                filepath=self.config.input_path, 
                r_tube=self.config.tube_radius, 
                output_path=self.report_path
            )
        # Show CLI result 
        self.simulation_report._show_CLI()
        

        # --- Generate PDF report 
        self.simulation_report._show_CLI()
        self.config.LOG.info(f"Generating simulation report into {self.report_path}")
        self.simulation_report._assemble_pdf()
        self.config.LOG.info("Simulation PDF report successfully generated.")

