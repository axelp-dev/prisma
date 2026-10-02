"""
PRISMA Trajectory module. 
- describe a trajectory profile 
- generates a given trajectory 
- export/import trajectory 
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import datetime

from src.utils import get_metadata
import src.core.conventions as conv 
from src.core.kinematics import CanonicalTwoAxis
from src.core.physics import KinematicProfile


class Trajectory: 

    def __init__(self, LOG: logging):
        # Trajectory properties
        self.step_s = None 
        self.duration_s = None 
        self.description = None 
        self.generation_date = None
        self.kin = CanonicalTwoAxis(n_axes=2)
        self.theta1 = None 
        self.theta2 = None

        # I/O features
        self.LOG = LOG
    
    def from_csv(self, filepath: str): 
        """
        Load Trajectory from CSV file. 
        - filepath: source CSV file
        """
        # Test file existency 
        if not Path(filepath).exists(): 
            self.LOG.error(f"No such file {filepath} for trajectory CSV import !")
            raise FileNotFoundError()

        # Extract data 
        traj = pd.read_csv(filepath, comment="#")
        np_traj = traj.to_numpy()
        self.timestamp = (np_traj.T)[0]
        self.theta1 = (np_traj.T)[1]
        self.theta2 = (np_traj.T)[2]

        # Init local attributes 
        self.duration_s = self.timestamp[-1]
        self.step_s = self.timestamp[1] - self.timestamp[0]
        metadata = get_metadata(filepath)
        self.description = metadata["description"]
        self.generation_date = metadata["generation"]
        self.LOG.info(f"Successfully loaded trajectory from {filepath} !")

    def to_csv(self, filepath: str): 
        """
        Write a (3,N) Numpy trajectory into 
        a CSV files. 
        - export_path : CSV export filepath
        """
        
        with open(filepath, "w") as file: 
            # Write header 
            file.write(f"# description : {self.description}\n")
            file.write("# NB : All positions are in radians and steps in seconds.\n")
            file.write(f"# duration_s : {self.duration_s}\n")
            file.write(f"# step_s : {self.step_s}\n")
            file.write(f"# generation : {datetime.datetime.now()}\n")
            file.write(f"# ============================================== \n")
            file.write(f"timestamp, theta1, theta2\n")


            # Write trajectory 
            traj = np.array([
                self.timestamp, 
                self.theta1, 
                self.theta2
            ])
            np.savetxt(file, traj.T, delimiter=",")
        self.LOG.info(f"Successfully saved trajectory in {filepath} !")

    def display(self): 
        """
        Display trasjectory with CLI output and user-friendly array
        """
        
        # TODO : implement this method 
    
    def generate(durations_s: float, step_s: float): 
        """
        Generate a Trajectory object using a specific profile. 
        """

        # TODO : implement this method 

    def compute_kinematics(self): 
        """
        Compute all simulation kinematics in order to generate a KinematicProfile
        for the solver. 
        """
        g = self.get_gravity_positions()
        omega1, omega2 = self.get_omegas()
        Omega = self.process_angular_velocity(omega1, omega2)
        Omega_dot = np.gradient(Omega, self.timestamp, axis=1)
        return KinematicProfile(
            timestamp=self.timestamp, 
            omega1=omega1,
            omega2=omega2, 
            theta1=self.theta1, 
            theta2=self.theta2,
            Omega=Omega, 
            Omega_dot=Omega_dot, 
            g=g
        )

    def get_gravity_positions(self): 
        """
        Process gravoity vector position using angles 
        and kinematics/conventions source files. 
        """
        g0 = conv.G_LAB
        angles = np.array([self.theta1, self.theta2]).T
        rot = self.kin.rotation(angles)
        return rot.apply(g0)

    def get_omegas(self): 
        """
        Process omega1 and omega1 corresponding 
        to angular velocities using variation rate formula. 
        - theta1 : inner axis orientation (rad)
        - theta2 : outer axis orientation (rad)
        - timestamp : corresponding time (s)
        """
        omega1 = np.gradient(self.theta1, self.timestamp)
        omega2 = np.gradient(self.theta2, self.timestamp)
        return omega1, omega2

    def process_angular_velocity(self, omega1, omega2): 
        """
        Process angular velocity vector in R_2 referential frame 
        (the sample one) using this formula : 
        Omega = (
            - omega2 * sin(theta1)
            omega2 * cos(theta1)
            omega1    
        )
        - theta2 : outer axis orientation (rad)
        - omega1 : inner axis rotation speed (rad/s)
        - omega2 : outer axis rotation speed (rad/s)
        """

        Omegas = np.array([
            - omega2 * np.sin(self.theta1), 
            omega2 * np.cos(self.theta1), 
            omega1
        ])
        return Omegas 



