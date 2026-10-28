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

    # Physics params 
    durations_s: float = 60.0
    step_s: float = 1.0
    profile: str = "random_walk"
    desc: str = None 

    # Flags 
    log_report: bool = True

# --- SimulationConfig ----------------------------------------------------

@dataclass 
class SimulationConfig(Config): 
    # Main arguments
    input_file: str
    output_file: str 
    log_report: bool = True 
    preset: str
    
    # Physical overrides 
    init_pos: np.ndarray = np.array([0.0, 0.0, 0.0])
    particle_radius: float = None 
    tube_radius: float = None 
    rho: float = None 
    rho_f: float = None 
    mu_f: float = None 
    k: float = None 