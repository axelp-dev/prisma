"""PRISMA Report Generation Module for Trajectories and Simulation Dynamics."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from src.config import Config

class Report(ABC):
    """Abstract base contract for PRISMA reporting modules."""

    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def generate_report(self): 
        """Generate rpdf report"""
        pass 

    @abstractmethod
    def _compute_metrics(self) -> dict:
        """Compute characteristic metrics dictionary."""
        pass

    @abstractmethod
    def _generate_plots(self) -> dict:
        """Construct and return Matplotlib figures."""
        pass

    @abstractmethod
    def _assemble_pdf(self) -> Path:
        """Compile and serialize figures into a multi-page PDF document."""
        pass

    @abstractmethod
    def _show_CLI(self) -> None:
        """Print formatted summary metrics to standard output."""
        pass