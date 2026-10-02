from dataclasses import dataclass
import numpy as np

@dataclass
class KinematicProfile: 
    """
    Dataclass container for Kinematics values
    """
    timestamp: np.ndarray
    theta1 : np.ndarray
    theta2 : np.ndarray
    g: np.ndarray
    omega1: np.ndarray
    omega2: np.ndarray
    Omega : np.ndarray
    Omega_dot : np.ndarray

@dataclass
class SimulationResult:
    """
    Simulation motion equations results container. 
    """
    timestamp: np.ndarray
    positions: np.ndarray      # (N, 3)
    velocities: np.ndarray     # (N, 3)
    reynolds: np.ndarray       # (N,)


@dataclass(frozen=True)
class Particle:
    """
    Modelise simulation particle. 
    """
    radius: float       # m
    rho: float          # kg/m^3

    @property
    def volume(self) -> float:
        return (4.0 / 3.0) * np.pi * self.radius**3

    @property
    def mass(self) -> float:
        return self.rho * self.volume


@dataclass(frozen=True)
class Fluid:
    """
    Modelize simulation Fluid properties. 
    """
    rho: float          # kg/m^3
    mu: float           # Pa·s


class PhysicalSystem:
    def __init__(self, particle: Particle, fluid: Fluid):
        self.particle = particle
        self.fluid = fluid

        # Instanciate simulation parameters from 
        # simulation objects ones
        denom = particle.rho + 0.5 * fluid.rho
        self.beta = (particle.rho - fluid.rho) / denom
        self.gamma = particle.rho / denom
        self.tau_v = (2.0 / 9.0) * (particle.radius**2 * denom) / fluid.mu

    def compute_reynolds(self, v_norm: np.ndarray | float) -> np.ndarray | float:
        """Compute Reynolds' particle number Re_p."""
        return (2.0 * self.particle.radius * self.fluid.rho * v_norm) / self.fluid.mu

    def display(self): 
        """
        Display PhysicalSystem config. 
        """

        # TODO : Implement this method. 