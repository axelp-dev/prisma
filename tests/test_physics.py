import numpy as np
import pytest

from src.core.physics import Fluid, KinematicProfile, Particle, PhysicalSystem, SimulationResult


# --- A. Particle tests ------------------------------------------------

def test_particle_immutability():
    """Particle must be frozen (immutable dataclass)."""
    p = Particle(radius=1.5e-3, rho=1202.0)
    with pytest.raises((AttributeError, TypeError)):
        p.radius = 2.0e-3


def test_particle_volume_and_mass():
    """Check geometric calculus on mass and volume."""
    r = 1.5e-3
    rho = 1200.0
    p = Particle(radius=r, rho=rho)

    expected_volume = (4.0 / 3.0) * np.pi * (r**3)
    expected_mass = rho * expected_volume

    assert p.volume == pytest.approx(expected_volume, rel=1e-9)
    assert p.mass == pytest.approx(expected_mass, rel=1e-9)


# --- B. Fluid tests ---------------------------------------------------

def test_fluid_immutability():
    """Fluid must be frozen."""
    f = Fluid(rho=1200.0, mu=1.412)
    with pytest.raises((AttributeError, TypeError)):
        f.mu = 1.0


# --- C. PhysicalSystem tests ------------------------------------------

@pytest.fixture
def glycerol_system():
    """Reference setup : ball in pure glycerol."""
    p = Particle(radius=1.5e-3, rho=1202.0)
    f = Fluid(rho=1200.0, mu=1.412)
    return PhysicalSystem(particle=p, fluid=f)


def test_physical_system_adimensional_params(glycerol_system):
    """Check analytic calculus on denom, beta, gamma and tau_v."""
    sys = glycerol_system
    r = sys.particle.radius
    rho_p = sys.particle.rho
    rho_f = sys.fluid.rho
    mu = sys.fluid.mu

    expected_denom = rho_p + 0.5 * rho_f
    expected_beta = (rho_p - rho_f) / expected_denom
    expected_gamma = rho_p / expected_denom
    expected_tau_v = (2.0 / 9.0) * (r**2 * expected_denom) / mu

    assert sys.beta == pytest.approx(expected_beta, rel=1e-9)
    assert sys.gamma == pytest.approx(expected_gamma, rel=1e-9)
    assert sys.tau_v == pytest.approx(expected_tau_v, rel=1e-9)


def test_physical_system_neutral_buoyancy():
    """For rho_p == rho_f, beta must be zero"""
    p = Particle(radius=1e-3, rho=1000.0)
    f = Fluid(rho=1000.0, mu=1.0)
    sys = PhysicalSystem(particle=p, fluid=f)

    assert sys.beta == pytest.approx(0.0, abs=1e-12)


def test_reynolds_computation_scalar(glycerol_system):
    """Check scalar calculus on Re_p = (2 * R * rho_f * v) / mu."""
    v_norm = 1e-4  # 0.1 mm/s
    re_p = glycerol_system.compute_reynolds(v_norm)

    expected = (2.0 * glycerol_system.particle.radius * glycerol_system.fluid.rho * v_norm) / glycerol_system.fluid.mu
    assert re_p == pytest.approx(expected, rel=1e-9)


def test_reynolds_computation_vectorized(glycerol_system):
    """Check that compute_reynolds preserves Numpy arrays."""
    v_norms = np.array([0.0, 1e-5, 5e-4, 1e-3])
    re_p = glycerol_system.compute_reynolds(v_norms)

    assert isinstance(re_p, np.ndarray)
    assert re_p.shape == v_norms.shape
    expected = (2.0 * glycerol_system.particle.radius * glycerol_system.fluid.rho * v_norms) / glycerol_system.fluid.mu
    np.testing.assert_allclose(re_p, expected, atol=1e-12)


# --- D. Dataclasses containers validation ------------------------------

def test_kinematic_profile_container():
    """Check KinematicProfile."""
    n = 10
    profile = KinematicProfile(
        timestamp=np.linspace(0, 1, n),
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


def test_simulation_result_container():
    """Check SimulationResult."""
    n = 50
    result = SimulationResult(
        timestamp=np.linspace(0, 5, n),
        positions=np.zeros((n, 3)),
        velocities=np.zeros((n, 3)),
        reynolds=np.zeros(n),
    )
    assert result.positions.shape == (n, 3)
    assert result.velocities.shape == (n, 3)
    assert result.reynolds.shape == (n,)