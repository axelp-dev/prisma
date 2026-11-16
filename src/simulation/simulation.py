"""
Simulation container for all simulation operations (run, generate report, etc...)
"""

from config import SimulationConfig


class Simulation: 

    def __init__(self, config: SimulationConfig): 
        self.config = config

    def load_trajectory(self): 
        """
        Load CSV trajectory file
        """
        self.config.LOG.info(f"Loading motor trajectory from: {self.config.input_file}")


    def launch_run(self): 
        """
        Launch simulation run
        """
        pass 