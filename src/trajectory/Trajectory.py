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
from src.core.models import KinematicProfile
from src.trajectory.generators import (
    PROFILES, 
    generate_random_walk, 
    generate_clinostat_1d, 
    generate_desynchronized_sine, 
    generate_centrifuge_sweep, 
    generate_constant_speed_ratio, 
    generate_static_1g
)
from src.config import TrajectoryConfig
from src.stats.trajectory_report import TrajectoryReport


class Trajectory: 

    def __init__(self, config: TrajectoryConfig):
        # Import config
        self.config = config
        self.kin = None

        # Physics values containers
        self.canon2axis = CanonicalTwoAxis(n_axes=2)
        self.theta1 = None 
        self.theta2 = None
        self.omega1 = None 
        self.omega2 = None

        # I/O features
        self.LOG = config.LOG

    # --------- Basic commands --------------

    def generate(self):
        """
        Launch generation process
        """
        # User display 
        self.LOG.info("Launching trajectory generation using config :")
        print(self.config)

        # Generate trajectory 
        self._load_profile_instructions()
        
        # Log content into CSV file 
        self._to_csv()
        self.LOG.info(f"Successfully generated trajectory into {self.config.output_path} !")

        # Generate PDF report if asked 
        if self.config.log_report: 
            # Instanciate TrajectoryReport object
            if self.kin == None: 
                self.kin = self.compute_kinematics()
            report_builder = TrajectoryReport(
                self.config, 
                self.kin
            )
            # Launch report generation 
            report_builder.generate_report()

    def show(self): 
        """
        Launch show process 
        """
        self.config.LOG.info(f"Generating PDF report from {self.config.input_path}...")

        # --- Import CSV file 
        self._from_csv()
        # Display loaded config
        # print(self.config)

        # --- Generating report
        # Process kinematics 
        self.kin = self.compute_kinematics()
        # Build report 
        report_builder = TrajectoryReport(
            self.config, 
            self.kin
        )
        report_builder.generate_report()

    # --------- Public Helper --------------
    
    def compute_kinematics(self): 
        """
        Compute all simulation kinematics in order to generate a KinematicProfile
        for the solver. 
        """
        g = self._get_gravity_positions()
        if self.omega1 is None or self.omega2 is None: 
            self.omega1, self.omega2 = self._get_omegas()
        Omega = self._process_angular_velocity(self.omega1, self.omega2)
        Omega_dot = np.gradient(Omega, self.timestamp, axis=1)
        
        return KinematicProfile(
            timestamp=self.timestamp, 
            omega1=self.omega1,
            omega2=self.omega2, 
            theta1=self.theta1, 
            theta2=self.theta2,
            Omega=Omega, 
            Omega_dot=Omega_dot, 
            g=g
        )

    # --------- Private helpers --------------

    def _from_csv(self):
        """
        Load Trajectory and metadata from CSV file.
        """
        input_file = Path(self.config.input_path)
        if not input_file.exists():
            self.LOG.error(f"No such file {input_file} for trajectory CSV import !")
            raise FileNotFoundError(f"File not found: {input_file}")

        # Temporal series extraction 
        traj = pd.read_csv(input_file, comment="#")
        np_traj = traj.to_numpy()
        self.timestamp = np_traj[:, 0]
        self.theta1 = np_traj[:, 1]
        self.theta2 = np_traj[:, 2]

        # Erase omega values to re-process them in compute_kinematics()
        self.omega1 = None
        self.omega2 = None

        # Get metadata
        metadata = get_metadata(input_file)

        # Get descriptions & title
        self.config.desc = str(metadata.get("description", "No description provided"))
        self.config.date = str(metadata.get("date", "Unknown"))

        # Get config 
        self.config.duration_s = float(metadata.get("duration_s", self.timestamp[-1]))
        self.config.step_s = float(metadata.get("step_s", self.timestamp[1] - self.timestamp[0]))

        if "profile" in metadata:
            self.config.profile = str(metadata["profile"])

        self.LOG.info(f"Successfully loaded trajectory from {input_file} !")

    def _to_csv(self): 
        """
        Write a (3,N) Numpy trajectory into a CSV file using 
        given config filepath. 
        """
        
        with open(self.config.output_path, "w") as file: 
            # Write header 
            file.write(f"# profile : {self.config.profile}\n")
            file.write(f"# description : {self.config.desc}\n")
            file.write("# NB : All positions are in radians and steps in seconds.\n")
            file.write(f"# duration_s : {self.config.duration_s}\n")
            file.write(f"# step_s : {self.config.step_s}\n")
            file.write(f"# date : {self.config.date}\n")
            file.write(f"# ============================================== \n")
            file.write(f"timestamp, theta1, theta2\n")

            # Write trajectory 
            traj = np.array([
                self.timestamp, 
                self.theta1, 
                self.theta2
            ])
            np.savetxt(file, traj.T, delimiter=",")

    def _load_profile_instructions(self): 
        """
        Get angles and speeds values from trajectory generators 
        using given profile. 
        """
        
        # Called asked generator function
        match self.config.profile: 
            case "random_walk": 
                values = generate_random_walk(
                    self.config.duration_s, 
                    self.config.step_s
                )
            case "desynchronized_sine": 
                values = generate_desynchronized_sine(
                    self.config.duration_s, 
                    self.config.step_s
                )
            case "constant_speed_ratio": 
                values = generate_constant_speed_ratio(
                    self.config.duration_s, 
                    self.config.step_s, 
                )
            case "static_1g": 
                values = generate_static_1g(
                    self.config.duration_s, 
                    self.config.step_s
                )
            case "clinostat_1d": 
                values = generate_clinostat_1d(
                    self.config.duration_s, 
                    self.config.step_s
                )
            case "centrifuge_sweep": 
                values = generate_centrifuge_sweep(
                    self.config.duration_s, 
                    self.config.step_s
                ) 
            case _: 
                # Default one 
                raise ValueError(f"Invalid trajectory profile, use : {PROFILES.keys}")

        # Unpack values
        self.timestamp, self.theta1, self.theta2, self.omega1, self.omega2 = values 

    
    def _get_gravity_positions(self): 
        """
        Process gravoity vector position using angles 
        and kinematics/conventions source files. 
        """
        g0 = conv.G_LAB
        angles = np.array([self.theta1, self.theta2]).T
        rot = self.canon2axis.rotation(angles)
        return rot.apply(g0)

    def _get_omegas(self): 
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

    def _process_angular_velocity(self, omega1, omega2): 
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



