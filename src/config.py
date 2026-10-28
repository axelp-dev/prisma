"""
General config definition for Trajectory and Simulation classes. 
Used and managed by all classes, instanciated by cli.py
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import numpy as np


# --- Presets ----------------------------------------------------
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

# --- Main Config ----------------------------------------------------


@dataclass 
class Config:
    LOG: logging 

# --- TrajectoryConfig ----------------------------------------------------

@dataclass 
class TrajectoryConfig(Config): 
    # Filepaths
    input_path: str = None          # CSV pre-generated trajectory
    output_path: str = None         # Filepath to log the generated trajectory
    report_path: str = None         # Filepath for the trajectory PDFReport
    date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Physics params 
    duration_s: float = 60.0
    step_s: float = 1.0
    profile: str = "random_walk"
    desc: str = None 

    # Flags 
    log_report: bool = True

    def __str__(self) -> str:
        sep = "-" * 48
        samples = (
            int(self.duration_s / self.step_s)
            if self.step_s and self.step_s > 0
            else 0
        )
        return (
            f"\n{sep}\n"
            f"  PRISMA TRAJECTORY CONFIGURATION\n"
            f"{sep}\n"
            f"  Date        : {self.date or '(none)'}\n"
            f"  Profile     : {self.profile}\n"
            f"  Description : {self.desc or '(default)'}\n"
            f"  Duration    : {self.duration_s} s\n"
            f"  Step (dt)   : {self.step_s} s ({samples} samples)\n"
            f"  Output CSV  : {self.output_path or '(none)'}\n"
            f"  Report PDF  : {self.report_path or '(none)'}\n"
            f"  Auto-report : {self.log_report}\n"
            f"{sep}"
        )

# --- SimulationConfig ----------------------------------------------------

@dataclass 
class SimulationConfig(Config): 
    # Main arguments
    input_file: str
    output_file: str 
    log_report: bool = True 
    preset: str = "statolith"
    
    # Physical overrides 
    init_pos: np.ndarray = None
    particle_radius: float = None 
    tube_radius: float = None 
    rho: float = None 
    rho_f: float = None 
    mu_f: float = None 
    k: float = None 