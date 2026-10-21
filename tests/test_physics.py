"""Unit test suite for physical models, fluid parameters, and data contracts.

This module validates:
- Particle and Fluid dataclass immutability and geometric property derivations.
- System-level dimensionless numbers (beta, gamma, tau_v).
- Viscoelastic timescale calculation (tau_k) for actin network elasticity.
- Dynamic calculation of the particle Reynolds number (Re_p) for scalars and arrays.
- Memory layout and dimensional shape consistency of data transfer objects.
"""

import numpy as np
import pytest

from src.core.physics import (
    Fluid,
    KinematicProfile,
    Particle,
    PhysicalSystem,
    SimulationResult,
)


# ==============================================================================
# A. Particle Model Tests
# ==============================================================================

def test_particle_immutability():
    """Verify that the Particle dataclass is frozen and prevents attribute mutation.

    This test ensures that critical particle parameters (such as radius, density,
    and initial equilibrium anchor position x0) cannot be accidentally modified
    during numerical time-stepping loops.
    """
    initial_position = np.array([0.0, 0.0, 5e-3])
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=initial_position)

    # Attempting to mutate physical radius should raise an exception
    with pytest.raises((AttributeError, TypeError)):
        particle.radius = 2.0e-3

    # Attempting to reassign the anchor vector should raise an exception
    with pytest.raises((AttributeError, TypeError)):
        particle.x0 = np.zeros(3)


def test_particle_geometric_volume_and_mass():
    """Validate analytical geometric volume and mass derivations for a sphere.

    Theoretical formulations:
        Volume = (4/3) * pi * R^3
        Mass   = rho * Volume
    """
    radius = 1.5e-3
    density = 1202.0
    initial_position = np.array([0.0, 0.0, 5e-3])

    particle = Particle(radius=radius, rho=density, x0=initial_position)

    expected_volume = (4.0 / 3.0) * np.pi * (radius**3)
    expected_mass = density * expected_volume

    assert particle.volume == pytest.approx(expected_volume, rel=1e-9)
    assert particle.mass == pytest.approx(expected_mass, rel=1e-9)
    np.testing.assert_allclose(particle.x0, initial_position, atol=1e-12)


# ==============================================================================
# B. Fluid Model Tests
# ==============================================================================

def test_fluid_immutability_and_defaults():
    """Ensure Fluid dataclass is frozen and defaults elasticity stiffness to zero.

    When stiffness parameter k = 0.0, the surrounding carrying medium behaves
    as a standard Newtonian fluid without viscoelastic restoring coupling.
    """
    fluid = Fluid(rho=1200.0, mu=1.412)
    assert fluid.k == pytest.approx(0.0)

    with pytest.raises((AttributeError, TypeError)):
        fluid.mu = 1.0


# ==============================================================================
# C. PhysicalSystem Dimensionless Properties & Timescales
# ==============================================================================

@pytest.fixture
def glycerol_system():
    """Provide a standard calibrated macroscopic benchmark system (bead in pure glycerol)."""
    particle = Particle(radius=1.5e-3, rho=1202.0, x0=np.array([0.0, 0.0, 5e-3]))
    fluid = Fluid(rho=1200.0, mu=1.412, k=0.0)
    return PhysicalSystem(particle=particle, fluid=fluid)


def test_physical_system_dimensionless_parameters(glycerol_system):
    """Validate numerical derivations of effective density denominator, beta, gamma, and tau_v.

    Theoretical formulations:
        denom = rho_p + 0.5 * rho_f
        beta  = (rho_p - rho_f) / denom
        gamma = rho_p / denom
        tau_v = (2/9) * (radius^2 * denom) / mu
    """
    system = glycerol_system
    r = system.particle.radius
    rho_p = system.particle.rho
    rho_f = system.fluid.rho
    mu = system.fluid.mu

    expected_denom = rho_p + 0.5 * rho_f
    expected_beta = (rho_p - rho_f) / expected_denom
    expected_gamma = rho_p / expected_denom
    expected_tau_v = (2.0 / 9.0) * (r**2 * expected_denom) / mu

    assert system.beta == pytest.approx(expected_beta, rel=1e-9)
    assert system.gamma == pytest.approx(expected_gamma, rel=1e-9)
    assert system.tau_v == pytest.approx(expected_tau_v, rel=1e-9)


def test_compute_tau_k_disabled_when_k_is_zero(glycerol_system):
    """Verify that compute_tau_k returns False when fluid stiffness k is 0.0.

    In the absence of an elastic restoring network (e.g., pure viscous glycerol),
    the system must explicitly return False to bypass elastic calculations.
    """
    assert glycerol_system.compute_tau_k() is False


def test_compute_tau_k_analytical_formulation():
    """Verify the viscoelastic relaxation timescale tau_k when stiffness k > 0.

    Analytical derivation:
        tau_k = (6 * pi * mu * R) / k
    """
    radius = 1.5e-6   # Typical statolith organelle radius (1.5 microns)
    viscosity = 0.1   # Cytoplasm dynamic viscosity (0.1 Pa.s)
    stiffness = 1e-4  # Equivalent actin filament network stiffness (N/m or kg/s^2)

    particle = Particle(radius=radius, rho=1500.0, x0=np.zeros(3))
    fluid = Fluid(rho=1050.0, mu=viscosity, k=stiffness)
    system = PhysicalSystem(particle=particle, fluid=fluid)

    expected_tau_k = (6.0 * np.pi * viscosity * radius) / stiffness
    calculated_tau_k = system.compute_tau_k()

    assert calculated_tau_k is not False
    assert calculated_tau_k == pytest.approx(expected_tau_k, rel=1e-9)


def test_reynolds_calculation_scalar_and_vectorized(glycerol_system):
    """Verify that compute_reynolds computes Re_p accurately for both scalars and ndarrays.

    Analytical formulation:
        Re_p = (2 * radius * rho_f * v_norm) / mu
    """
    system = glycerol_system
    r = system.particle.radius
    rho_f = system.fluid.rho
    mu = system.fluid.mu

    # Test with scalar input
    v_scalar = 1e-4
    expected_scalar = (2.0 * r * rho_f * v_scalar) / mu
    assert system.compute_reynolds(v_scalar) == pytest.approx(expected_scalar, rel=1e-9)

    # Test with multi-dimensional NumPy array input
    v_array = np.array([0.0, 1e-5, 5e-4, 1e-3])
    expected_array = (2.0 * r * rho_f * v_array) / mu
    re_p_array = system.compute_reynolds(v_array)

    assert isinstance(re_p_array, np.ndarray)
    assert re_p_array.shape == v_array.shape
    np.testing.assert_allclose(re_p_array, expected_array, atol=1e-12)


# ==============================================================================
# D. Dataclass Container Shape Integrity Tests
# ==============================================================================

def test_kinematic_profile_container():
    """Verify KinematicProfile field assignments and expected dimensional array shapes."""
    n = 25
    profile = KinematicProfile(
        timestamp=np.linspace(0.0, 1.0, n),
        theta1=np.zeros(n),
        theta2=np.zeros(n),
        g=np.zeros((n, 3)),
        omega1=np.zeros(n),
        omega2=np.zeros(n),
        Omega=np.zeros((3, n)),
        Omega_dot=np.zeros((3, n)),
    )
    assert profile.timestamp.shape == (n,)
    assert profile.g.shape == (n, 3)
    assert profile.Omega.shape == (3, n)
    assert profile.Omega_dot.shape == (3, n)


def test_simulation_result_container():
    """Verify SimulationResult field assignments and output shape contracts."""
    n = 50
    result = SimulationResult(
        timestamp=np.linspace(0.0, 2.0, n),
        positions=np.zeros((n, 3)),
        velocities=np.zeros((n, 3)),
        reynolds=np.zeros(n),
    )
    assert result.positions.shape == (n, 3)
    assert result.velocities.shape == (n, 3)
    assert result.reynolds.shape == (n,)