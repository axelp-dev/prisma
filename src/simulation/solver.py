import logging

import numpy as np

from src.core.models import KinematicProfile, PhysicalSystem, SimulationResult


class Solver:
    """Generic mother class for solvers implementations."""

    def __init__(self, system: PhysicalSystem, r_tube: float, LOG: logging.Logger):
        self.system = system
        self.r_tube = float(r_tube)
        self.overdamped = False
        self.LOG = LOG

    def solve(self, kin: KinematicProfile, v0: np.ndarray) -> SimulationResult:
        raise NotImplementedError("Sub-classes must implement solve() method.")


class RK4Overdamped(Solver):
    def __init__(self, system: PhysicalSystem, r_tube: float, LOG: logging.Logger):
        super().__init__(system=system, r_tube=r_tube, LOG=LOG)
        self.overdamped = True

    def solve(self, kin: KinematicProfile, v0: np.ndarray) -> SimulationResult:
        """
        Solve PRISMA overdamped dynamics using 4th-order Runge-Kutta integration
        with inelastic spherical boundary confinement at r = R_tube.
        """
        N = len(kin.timestamp)
        r_t = np.zeros((N, 3), dtype=np.float64)
        v_t = np.zeros((N, 3), dtype=np.float64)

        r0 = np.asarray(self.system.particle.x0, dtype=np.float64)
        r0_norm = np.linalg.norm(r0)
        if r0_norm > self.r_tube:
            self.LOG.warning(
                f"Initial anchor x0 (|x0|={r0_norm:.3e} m) exceeds R_tube={self.r_tube:.3e} m; clamping to wall."
            )
            r0 = (r0 / r0_norm) * self.r_tube
        r_t[0] = r0

        # Evaluate initial constrained velocity
        v_init = self.v_limit(r_t[0], kin.g[0], kin.Omega[:, 0], kin.Omega_dot[:, 0])
        v_t[0] = self._apply_wall_velocity_constraint(r_t[0], v_init)

        for n in range(N - 1):
            dt = float(kin.timestamp[n + 1] - kin.timestamp[n])
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

            r_next = rn + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

            # Inelastic spherical wall clamping: project onto inner wall R_tube
            r_norm = float(np.linalg.norm(r_next))
            if r_norm > self.r_tube:
                r_next = (r_next / r_norm) * self.r_tube

            r_t[n + 1] = r_next

            # Instantaneous physical velocity with normal wall suppression
            v_raw = self.v_limit(r_next, g_next, w_next, dw_next)
            v_t[n + 1] = self._apply_wall_velocity_constraint(r_next, v_raw)

        v_norm = np.linalg.norm(v_t, axis=1)
        re_p = self.system.compute_reynolds(v_norm=v_norm)
        return SimulationResult(
            timestamp=kin.timestamp, positions=r_t, velocities=v_t, reynolds=re_p
        )

    def _apply_wall_velocity_constraint(
        self, r: np.ndarray, v: np.ndarray, tol: float = 1e-12
    ) -> np.ndarray:
        """Suppress outward radial velocity when the particle is in contact with R_tube."""
        r_norm = float(np.linalg.norm(r))
        if r_norm >= self.r_tube * (1.0 - tol) and r_norm > 0.0:
            n_hat = r / r_norm
            v_radial = float(np.dot(v, n_hat))
            if v_radial > 0.0:
                return v - v_radial * n_hat
        return v

    def v_limit(
        self, r: np.ndarray, g: np.ndarray, Omega: np.ndarray, Omega_dot: np.ndarray
    ) -> np.ndarray:
        """Compute local terminal velocity v_limit in the overdamped Stokes regime."""
        centrifugal = np.cross(Omega, np.cross(Omega, r))
        euler = np.cross(Omega_dot, r)

        tau_k = self.system.compute_tau_k()
        if tau_k:
            return (
                self.system.tau_v * self.system.beta * (g - centrifugal - euler)
                - (r - self.system.particle.x0) / tau_k
            )
        return self.system.tau_v * self.system.beta * (g - centrifugal - euler)
