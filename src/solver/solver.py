
import numpy as np 
import logging
from src.core.physics import PhysicalSystem, KinematicProfile, SimulationResult


class Solver: 

    """
    Generic mother class for solvers implementations. 
    """
    def __init__(self, 
                 system: PhysicalSystem, 
                 r_tube: float, 
                 LOG: logging): 
        # Simulation parameters
        self.system = system 

        # Harware parameters 
        self.r_tube = r_tube
        self.overdamped = False
        self.LOG = LOG

    def solve(self, kin: KinematicProfile, x0: np.ndarray, v0: np.ndarray) -> SimulationResult: 
        raise NotImplementedError("Sub-classes must implement solve() method.")

class RK4Overdamped(Solver): 

    def solve(self, 
              kin: KinematicProfile, 
              x0: np.ndarray, 
              v0: np.ndarray) -> SimulationResult: 
        """
        Solve PRISMA problem using Runge-Kunta 4 order method. 
        Assume that Re_p << 1 so we only have to solve the following 1st order
        equation : dr/dt = v_{limit}(r,t)
        """
        """
        TODO : Fill this part 
        """
        N = len(kin.timestamp)
        dt = kin.timestamp[1] - kin.timestamp[0]
        r_t = np.zeros((N, 3))
        r_t[0] = x0
    
        for n in range(N - 1):
            g_n, g_next = kin.g[n], kin.g[n + 1]
            w_n, w_next = kin.Omega[:, n], kin.Omega[:, n + 1]
            dw_n, dw_next = kin.Omega_dot[:, n], kin.Omega_dot[:, n + 1]
    
            g_mid = 0.5 * (g_n + g_next)
            w_mid = 0.5 * (w_n + w_next)
            dw_mid = 0.5 * (dw_n + dw_next)
    
            rn = r_t[n]
            k1 = self.v_limit(rn, g_n, w_n, dw_n)
            k2 = self.v_limit(rn + 0.5 * dt * k1, g_mid, w_mid, dw_mid)
            k3 = self.v_limit(rn + 0.5 * dt * k2, g_mid, w_mid, dw_mid)
            k4 = self.v_limit(rn + dt * k3, g_next, w_next, dw_next)
    
            r_t[n + 1] = rn + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    
        # Calcul dynamique des grandeurs dérivées
        v_t = np.gradient(r_t, dt, axis=0)
        v_norm = np.linalg.norm(v_t, axis=1)
        re_p = self.system.compute_reynolds(v_norm=v_norm)
        
        return SimulationResult(
            timestamp=kin.timestamp, 
            positions=r_t, 
            velocities=v_t, 
            reynolds=re_p
        )

    def v_limit(self, r: np.ndarray, 
                g: np.ndarray, 
                Omega: np.ndarray, 
                Omega_dot: np.ndarray):
        """
        Process local v_{limit} in overdamped regime. 
        """
        centrifugal = np.cross(Omega, np.cross(Omega, r))
        euler = np.cross(Omega_dot, r)
        return self.system.tau_v * self.system.beta * (g - centrifugal - euler)
