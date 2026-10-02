import logging
import numpy as np
import pytest

from src.core.physics import Fluid, KinematicProfile, Particle, PhysicalSystem, SimulationResult
from src.solver.solver import RK4Overdamped, Solver

@pytest.fixture
def mock_logger():
    """Basic logging"""
    return logging.getLogger("test_solver")


@pytest.fixture
def physical_system():
    """Reference system : ball in pure glycerol"""
    p = Particle(radius=1.5e-3, rho=1202.0)
    f = Fluid(rho=1200.0, mu=1.412)
    return PhysicalSystem(particle=p, fluid=f)


@pytest.fixture
def static_kinematics():
    """At rest cinematic [0, 0, -9.81]."""
    n = 101
    t = np.linspace(0.0, 1.0, n)
    return KinematicProfile(
        timestamp=t,
        theta1=np.zeros(n),
        theta2=np.zeros(n),
        g=np.tile(np.array([0.0, 0.0, -9.81]), (n, 1)),
        omega1=np.zeros(n),
        omega2=np.zeros(n),
        Omega=np.zeros((3, n)),
        Omega_dot=np.zeros((3, n)),
    )


# --- A. Architecture & Initialization ----------------------------------

def test_solver_initialization(physical_system, mock_logger):
    """Checkc class instanciation."""
    solver = RK4Overdamped(system=physical_system, r_tube=0.05, LOG=mock_logger)
    assert solver.system == physical_system
    assert solver.r_tube == pytest.approx(0.05)
    assert not solver.overdamped


def test_base_solver_raises_not_implemented(physical_system, static_kinematics, mock_logger):
    """Check that Solver instanciation as to implements solve() method"""
    base_solver = Solver(system=physical_system, r_tube=0.05, LOG=mock_logger)
    with pytest.raises(NotImplementedError):
        base_solver.solve(static_kinematics, x0=np.zeros(3), v0=np.zeros(3))

# --- B. Local v_limit calculus ----------------------------------------

def test_v_limit_pure_gravity(physical_system, mock_logger):
    """At nul rotation, v_limit must be aligned to gravity and equals to tau_v * beta * g."""
    solver = RK4Overdamped(system=physical_system, r_tube=0.05, LOG=mock_logger)

    r = np.array([0.0, 0.0, 5e-3])
    g = np.array([0.0, 0.0, -9.81])
    omega = np.zeros(3)
    omega_dot = np.zeros(3)

    v_calc = solver.v_limit(r, g, omega, omega_dot)
    v_expected = physical_system.tau_v * physical_system.beta * g

    np.testing.assert_allclose(v_calc, v_expected, atol=1e-12)


def test_v_limit_centrifugal_cancellation(physical_system, mock_logger):
    """At center r=0, Euler and Centrifugal terms must be zero."""
    solver = RK4Overdamped(system=physical_system, r_tube=0.05, LOG=mock_logger)

    r_origin = np.zeros(3)
    g = np.array([0.0, 0.0, -9.81])
    omega = np.array([1.0, 2.0, 3.0])
    omega_dot = np.array([0.5, -0.5, 1.0])

    v_calc = solver.v_limit(r_origin, g, omega, omega_dot)
    v_expected = physical_system.tau_v * physical_system.beta * g

    np.testing.assert_allclose(v_calc, v_expected, atol=1e-12)


# --- C. RK4 Integration & Analytic solution -------------------------

def test_solve_static_linear_sedimentation(physical_system, static_kinematics, mock_logger):
    """With static gravity and constant speed, z(t) must follows z_0 + v_z * t."""
    solver = RK4Overdamped(system=physical_system, r_tube=0.05, LOG=mock_logger)

    x0 = np.array([0.0, 0.0, 5e-3])
    v0 = np.zeros(3)

    res = solver.solve(static_kinematics, x0=x0, v0=v0)

    assert isinstance(res, SimulationResult)
    assert len(res.timestamp) == len(static_kinematics.timestamp)
    assert res.positions.shape == (len(static_kinematics.timestamp), 3)

    v_limit_z = physical_system.tau_v * physical_system.beta * (-9.81)
    t = static_kinematics.timestamp

    np.testing.assert_allclose(res.positions[:, 0], 0.0, atol=1e-12)
    np.testing.assert_allclose(res.positions[:, 1], 0.0, atol=1e-12)

    z_expected = x0[2] + v_limit_z * t
    np.testing.assert_allclose(res.positions[:, 2], z_expected, atol=1e-10)


def test_solve_reynolds_consistency(physical_system, static_kinematics, mock_logger):
    """Check positive Re_p and << to Stoke threshold (0.1)"""
    solver = RK4Overdamped(system=physical_system, r_tube=0.05, LOG=mock_logger)

    res = solver.solve(static_kinematics, x0=np.array([0.0, 0.0, 5e-3]), v0=np.zeros(3))

    assert res.reynolds.shape == (len(static_kinematics.timestamp),)
    assert np.all(res.reynolds >= 0.0)
    assert np.all(res.reynolds < 0.1) 
