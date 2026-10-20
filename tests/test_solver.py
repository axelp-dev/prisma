"""Unit test suite for Runge-Kutta 4th-order overdamped solvers and physics integration.

This module validates:
- Polymorphic behavior of the base Solver class.
- Analytical consistency of the terminal limit velocity function v_limit.
- Viscous settling under static terrestrial gravity (linear regime).
- Viscoelastic exponential relaxation toward dynamic equilibrium when k > 0.
- Respect of the Stokes creeping-flow threshold (Re_p << 0.1).
"""

import logging
import numpy as np
import pytest

from src.core.physics import (
    Fluid,
    KinematicProfile,
    Particle,
    PhysicalSystem,
    SimulationResult,
)
from src.solver.solver import RK4Overdamped, Solver


@pytest.fixture
def mock_logger():
    """Provide a neutral mock logger for solver test execution."""
    return logging.getLogger("test_solver")


@pytest.fixture
def static_gravity_kinematics():
    """Generate a synthetic kinematic profile at complete rest under static gravity."""
    n_points = 201
    t = np.linspace(0.0, 2.0, n_points)
    return KinematicProfile(
        timestamp=t,
        theta1=np.zeros(n_points),
        theta2=np.zeros(n_points),
        g=np.tile(np.array([0.0, 0.0, -9.81]), (n_points, 1)),
        omega1=np.zeros(n_points),
        omega2=np.zeros(n_points),
        Omega=np.zeros((3, n_points)),
        Omega_dot=np.zeros((3, n_points)),
    )


# ==============================================================================
# A. Base Class & Polymorphism Tests
# ==============================================================================

def test_base_solver_raises_not_implemented(mock_logger, static_gravity_kinematics):
    """Ensure the abstract base Solver forces derived classes to implement solve()."""
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=np.array([0.0, 0.0, 5e-3]))
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.0)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    base_solver = Solver(system=system, r_tube=0.05, LOG=mock_logger)
    with pytest.raises(NotImplementedError):
        base_solver.solve(kin=static_gravity_kinematics, v0=np.zeros(3))


# ==============================================================================
# B. Local Terminal Velocity Function (v_limit) Tests
# ==============================================================================

def test_v_limit_pure_sedimentation_without_elasticity(mock_logger):
    """Verify v_limit when k = 0 matches the analytical settling velocity: tau_v * beta * g."""
    anchor_x0 = np.array([0.0, 0.0, 5e-3])
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=anchor_x0)
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.0)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    solver = RK4Overdamped(system=system, r_tube=0.05, LOG=mock_logger)

    current_r = np.array([0.0, 0.0, 10e-3])
    g_vector = np.array([0.0, 0.0, -9.81])
    zero_omega = np.zeros(3)

    v_computed = solver.v_limit(current_r, g_vector, zero_omega, zero_omega)
    v_expected = system.tau_v * system.beta * g_vector

    np.testing.assert_allclose(v_computed, v_expected, atol=1e-12)


def test_v_limit_with_elastic_restoring_force(mock_logger):
    """Verify v_limit includes Hookean damping toward particle.x0: - (r - x0) / tau_k."""
    anchor_x0 = np.array([0.0, 0.0, 5e-3])
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=anchor_x0)
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.05)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    solver = RK4Overdamped(system=system, r_tube=0.05, LOG=mock_logger)

    current_r = np.array([1e-3, 2e-3, 8e-3])
    g_vector = np.array([0.0, 0.0, -9.81])
    zero_omega = np.zeros(3)

    tau_k = system.compute_tau_k()
    v_computed = solver.v_limit(current_r, g_vector, zero_omega, zero_omega)

    v_sedimentation = system.tau_v * system.beta * g_vector
    v_elastic = - (current_r - anchor_x0) / tau_k
    v_expected = v_sedimentation + v_elastic

    np.testing.assert_allclose(v_computed, v_expected, atol=1e-12)


# ==============================================================================
# C. Integrated RK4 Trajectory & Physical Consistency Tests
# ==============================================================================

def test_rk4_constant_sedimentation_pure_viscous(mock_logger, static_gravity_kinematics):
    """Verify that a bead in pure viscous fluid (k=0) falls linearly at v_terminal."""
    anchor_x0 = np.array([0.0, 0.0, 5e-3])
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=anchor_x0)
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.0)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    solver = RK4Overdamped(system=system, r_tube=0.05, LOG=mock_logger)
    result = solver.solve(kin=static_gravity_kinematics, v0=np.zeros(3))

    assert isinstance(result, SimulationResult)
    t = static_gravity_kinematics.timestamp
    v_terminal_z = system.tau_v * system.beta * (-9.81)

    # Lateral coordinates in X and Y must remain strictly zero
    np.testing.assert_allclose(result.positions[:, 0], 0.0, atol=1e-12)
    np.testing.assert_allclose(result.positions[:, 1], 0.0, atol=1e-12)

    # Vertical position must match exact linear trajectory z(t) = z0 + v_terminal_z * t
    expected_z = anchor_x0[2] + v_terminal_z * t
    np.testing.assert_allclose(result.positions[:, 2], expected_z, atol=1e-10)


def test_rk4_exponential_relaxation_to_elastic_equilibrium(mock_logger, static_gravity_kinematics):
    """Verify that with stiffness k > 0, the trajectory converges exponentially to r_eq.

    Analytical 1st-order differential equation under static gravity:
        dz/dt = v_sed - (z - z0) / tau_k
        z_eq  = z0 + tau_k * v_sed
        z(t)  = z_eq + (z0 - z_eq) * exp(-t / tau_k)
    """
    anchor_x0 = np.array([0.0, 0.0, 5e-3])
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=anchor_x0)
    # Stiffness chosen to complete multiple relaxation cycles within 2 seconds
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.08)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    solver = RK4Overdamped(system=system, r_tube=0.05, LOG=mock_logger)
    result = solver.solve(kin=static_gravity_kinematics, v0=np.zeros(3))

    t = static_gravity_kinematics.timestamp
    tau_k = system.compute_tau_k()
    v_sed_z = system.tau_v * system.beta * (-9.81)

    # Calculate theoretical static equilibrium position
    z_eq = anchor_x0[2] + tau_k * v_sed_z

    # Closed-form analytical solution
    expected_z = z_eq + (anchor_x0[2] - z_eq) * np.exp(-t / tau_k)

    np.testing.assert_allclose(result.positions[:, 2], expected_z, atol=1e-9)


def test_rk4_stokes_reynolds_compliance(mock_logger, static_gravity_kinematics):
    """Verify that the computed particle Reynolds number remains strictly below Stokes limit (0.1)."""
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=np.array([0.0, 0.0, 5e-3]))
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.0)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    solver = RK4Overdamped(system=system, r_tube=0.05, LOG=mock_logger)
    result = solver.solve(kin=static_gravity_kinematics, v0=np.zeros(3))

    assert result.reynolds.shape == (len(static_gravity_kinematics.timestamp),)
    assert np.all(result.reynolds >= 0.0)
    assert np.all(result.reynolds < 0.1)