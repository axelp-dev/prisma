import logging
from pathlib import Path
import numpy as np
import pytest

from src.trajectory.Trajectory import KinematicProfile, Trajectory
import src.core.conventions as cv


@pytest.fixture
def mock_logger():
    """Basic logger for tests"""
    return logging.getLogger("test_trajectory")


@pytest.fixture
def sample_trajectory_csv(tmp_path):
    """Generates a fixture CSV trajectory"""
    csv_file = tmp_path / "test_traj.csv"
    content = (
        "# description : Harmonic test\n"
        "# NB : All positions are in radians and steps in seconds.\n"
        "# duration_s : 2.0\n"
        "# step_s : 0.01\n"
        "# generation : 2026-10-01 12:00:00\n"
        "# ==============================================\n"
        "timestamp, theta1, theta2\n"
    )
    t = np.arange(0.0, 2.01, 0.01)
    th1 = 0.2 * np.sin(2 * np.pi * t)
    th2 = 0.1 * np.cos(2 * np.pi * t)

    data_lines = [f"{ti:.4f},{p1:.6f},{p2:.6f}\n" for ti, p1, p2 in zip(t, th1, th2)]
    csv_file.write_text(content + "".join(data_lines), encoding="utf-8")
    
    return csv_file


# --- A. Initialization & I/O Validation --------------------------------

def test_trajectory_init(mock_logger):
    """Check initial Trajectory object"""
    traj = Trajectory(LOG=mock_logger)
    assert traj.theta1 is None
    assert traj.theta2 is None
    assert traj.step_s is None
    assert traj.duration_s is None


def test_from_csv_loading(mock_logger, sample_trajectory_csv):
    """Check CSV parsing and attributes setting"""
    traj = Trajectory(LOG=mock_logger)
    traj.from_csv(str(sample_trajectory_csv))

    assert len(traj.timestamp) == 201
    assert len(traj.theta1) == 201
    assert len(traj.theta2) == 201
    assert traj.duration_s == pytest.approx(2.0, abs=1e-5)
    assert traj.step_s == pytest.approx(0.01, abs=1e-5)
    assert traj.description == "Harmonic test"


def test_from_csv_missing_file(mock_logger, tmp_path):
    """Chech exception raise for NotFoundFile"""
    traj = Trajectory(LOG=mock_logger)
    missing = tmp_path / "non_existent.csv"
    with pytest.raises((FileNotFoundError, SystemExit)):
        traj.from_csv(str(missing))


def test_to_csv_roundtrip(mock_logger, sample_trajectory_csv, tmp_path):
    """Check import <-> export consistency."""
    traj_src = Trajectory(LOG=mock_logger)
    traj_src.from_csv(str(sample_trajectory_csv))

    export_path = tmp_path / "exported_traj.csv"
    traj_src.to_csv(str(export_path))

    traj_dst = Trajectory(LOG=mock_logger)
    traj_dst.from_csv(str(export_path))

    np.testing.assert_allclose(traj_src.timestamp, traj_dst.timestamp, atol=1e-5)
    np.testing.assert_allclose(traj_src.theta1, traj_dst.theta1, atol=1e-5)
    np.testing.assert_allclose(traj_src.theta2, traj_dst.theta2, atol=1e-5)


# --- B. Cinematic calculus and vectorization -------------------------

def test_omegas_constant_speed(mock_logger):
    """Check constant speed for linear angular speed"""
    traj = Trajectory(LOG=mock_logger)
    traj.timestamp = np.linspace(0.0, 10.0, 1001)
    traj.step_s = traj.timestamp[1] - traj.timestamp[0]
    
    # Theorical angular speeds : w1 = 2 rad/s, w2 = -1 rad/s
    traj.theta1 = 2.0 * traj.timestamp
    traj.theta2 = -1.0 * traj.timestamp

    w1, w2 = traj.get_omegas()
    np.testing.assert_allclose(w1, np.full_like(w1, 2.0), atol=1e-4)
    np.testing.assert_allclose(w2, np.full_like(w2, -1.0), atol=1e-4)


def test_gravity_at_rest(mock_logger):
    """Check bottom-oriented gravity vector for null rotation angles"""
    traj = Trajectory(LOG=mock_logger)
    traj.timestamp = np.array([0.0, 0.1, 0.2])
    traj.theta1 = np.zeros(3)
    traj.theta2 = np.zeros(3)

    g_pos = traj.get_gravity_positions()
    assert g_pos.shape == (3, 3)
    np.testing.assert_allclose(g_pos, np.tile(cv.G_LAB, (3, 1)), atol=1e-9)


def test_angular_velocity_frame_r2(mock_logger):
    """Check analytic Omega projection"""
    traj = Trajectory(LOG=mock_logger)
    traj.theta1 = np.array([0.0, np.pi / 2.0])
    w1 = np.array([1.0, 1.0])
    w2 = np.array([2.0, 2.0])

    # Case 1 : theta1 = 0 -> Omega = [0, w2, w1] = [0, 2, 1]
    # Case 2 : theta1 = pi/2 -> Omega = [-w2, 0, w1] = [-2, 0, 1]
    expected = np.array([
        [0.0, -2.0],
        [2.0, 0.0],
        [1.0, 1.0],
    ])
    omega_vec = traj.process_angular_velocity(w1, w2)
    assert omega_vec.shape == (3, 2)
    np.testing.assert_allclose(omega_vec, expected, atol=1e-9)


def test_compute_kinematics_pipeline(mock_logger, sample_trajectory_csv):
    """Check KinematicProfile object"""
    traj = Trajectory(LOG=mock_logger)
    traj.from_csv(str(sample_trajectory_csv))

    profile = traj.compute_kinematics()

    assert isinstance(profile, KinematicProfile)
    n = len(traj.timestamp)

    # Check shapes
    assert profile.timestamp.shape == (n,)
    assert profile.g.shape == (n, 3)
    assert profile.omega1.shape == (n,)
    assert profile.omega2.shape == (n,)
    assert profile.Omega.shape == (3, n)
    assert profile.Omega_dot.shape == (3, n)

    # Verify gravity norm
    g_norms = np.linalg.norm(profile.g, axis=1)
    np.testing.assert_allclose(g_norms, np.full(n, 9.81), atol=1e-7)