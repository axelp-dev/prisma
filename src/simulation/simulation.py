"""
Simulation container for all simulation operations (run, generate report, etc...)
"""

import numpy as np
from pathlib import Path
import pandas as pd
from dataclasses import asdict
import ast

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
        if self.config != None and self.config.log_report: 
            # Store PDF report next to simulation result 
            self.report_path = convert_to_pdf_path(self.config.output_file)
        else: 
            self.report_path = None
    
    # --- Public Methods -----------------------------------------------


    def run(self): 
        """Launch simulation using RK4Overdamped solver"""
        
        # Read trajectory from CSV file 
        self._load_trajectory()

        # --- Init simulation Math config ---
        # Initial position 
        x0_vec = np.array(self.config.init_pos, dtype=float)
        # Particle object 
        self.particle = Particle(
            radius=self.config.particle_radius, 
            rho=self.config.rho, 
            x0=x0_vec)
        # Fluid object
        self.fluid = Fluid(
            rho=self.config.rho_f, 
            mu=self.config.mu_f, 
            k=self.config.k
        )
        # PhysicalSystem for all simulation
        self.system = PhysicalSystem(particle=self.particle, fluid=self.fluid)

        # --- Simulating --- 
        self.config.LOG.info(
        f"Physical system initialized: tau_v={self.system.tau_v:.3e} s, "
        f"beta={self.system.beta:.4f}, tau_k={self.system.compute_tau_k()}"
        )

        self.config.LOG.info("Running RK4 overdamped solver...")
        # Creating solver object
        solver = RK4Overdamped(
            system=self.system,
            r_tube=self.config.tube_radius,
            LOG=self.config.LOG)
        
        # Launching solving...
        self.result = solver.solve(kin=self.kin, v0=np.zeros(3))
        
        # --- Reporting ---
        # Extract metrics
        max_reynolds = np.max(self.result.reynolds)
        self.config.LOG.info(f"Simulation completed. Maximum Re_p: {max_reynolds:.3e}")
        if max_reynolds >= 0.1:
            self.config.LOG.warning(f"Re_p exceeded 0.1 (Re_p={max_reynolds:.3e})!")

        # Writing result as CSV file 
        self._to_CSV()

        # Creating SimulationReport from CLI object 
        simulation_report = SimulationReport(
            result=self.result, 
            config=self.config, 
            kin=self.kin, 
            system=self.system, 
            r_tube=self.config.tube_radius, 
            output_path=self.report_path
        )

        if self.config.log_report: 
            self.show(simulation_report)


    def show(self, simulation_report: SimulationReport = None):
        """
        Displaying simulation result on CLI and generating PDF
        report if asked. 
        """
        # --- Init report builder ---
        if simulation_report == None: 
            self.simulation_report = self._init_report()
        else: 
            self.simulation_report = simulation_report
            self.simulation_report._show_CLI()

        # --- Build report ---- 
        self.config.LOG.info(f"Generating simulation report into {self.report_path}")
        self.simulation_report._assemble_pdf()
        self.config.LOG.info("Simulation PDF report successfully generated.")

    
    def from_CSV(self, input_file: str, LOG):
        """Build SimulationResult and SimulationConfig from existing CSV file"""
        
        # --- Build Config --- 
        metadata = self._parse_header(input_file)
        # print(metadata)
        self.config = SimulationConfig(
            input_file=metadata["input_file"], 
            output_file=input_file, 
            log_report=metadata["log_report"], 
            preset=metadata["preset"], 
            init_pos=metadata["init_pos"], 
            particle_radius=metadata["particle_radius"], 
            rho=metadata["rho"], 
            rho_f=metadata["rho_f"], 
            mu_f=metadata["mu_f"], 
            k=metadata["k"], 
            LOG=LOG
        )
        
        




    # --- Private Methods -----------------------------------------------

    def _load_trajectory(self): 
        """Load CSV trajectory file"""

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
   
    # TODO : 
    # - Rappatrier la lecture du SimulationResult à partir du CSV
    #   ici pour ensuite lancer un report desuss 
    # - Directement le faire dans from_CSV()
    # - Mettre à jour la doc dessus. 


    def _init_report(self): 
        """Init SImulationReport object"""

        # Init SimulationConfig 
        if self.simulation_report == None: 
            # Import simulation report from result
            self.simulation_report = SimulationReport.from_csv(
                filepath=self.config.input_path, 
                r_tube=self.config.tube_radius, 
                output_path=self.report_path
            )
        # Show CLI result 
        self.simulation_report._show_CLI()

    
    def _to_CSV(self): 
        """"Save SimulationResult as CSV file"""
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
            for key in dict_config.keys(): 
                if key != "LOG": 
                    # Write metadata as '# key : value' content in CSV file
                    content = f"# {str(key)} : {str(dict_config[key])}\n"
                    file.write(content)
            file.write("\n")
                
        
        # --- Creating dataframe ---  
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
        # Writting file 
        df_out.to_csv(output_path, index=False, mode='a')

        self.config.LOG.info(f"Succesfully saved simulation into : {self.config.output_file}")


    def _parse_header(self, input_file: str): 
        """Parse SimulationResult header to get metadata"""
        metadata = {}
        
        # Open file and readlines
        with open(input_file, 'r') as file: 
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
