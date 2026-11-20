import logging
from pathlib import Path

import numpy as np
import pytest

import src.core.conventions as cv
from src.config import TrajectoryConfig
from src.core.models import KinematicProfile
from src.trajectory.Trajectory import Trajectory


@pytest.fixture
def mock_logger():
    """Basic logger for tests."""
    return logging.getLogger("test_trajectory")


@pytest.fixture
def base_config(mock_logger, tmp_path):
    """Provide a default TrajectoryConfig pointing to a temporary directory."""
    return TrajectoryConfig(
        LOG=mock_logger,
        input_path=None,
        output_path=tmp_path / "out_traj.csv",
        report_path=tmp_path / "out_traj.pdf",
        date="2026-11-20 10:00:00",
        duration_s=2.0,
        step_s=0.01,
        profile="constant_speed_ratio",
        desc="Unit test profile",
        log_report=False,
    )


@pytest.fixture
def sample_trajectory_csv(tmp_path):
    """Generate a fixture CSV trajectory aligned with _to_csv format."""
    csv_file = tmp_path / "test_traj.csv"
    content = (
        "# profile : desynchronized_sine\n"
        "# description : Harmonic test\n"
        "# NB : All positions are in radians and steps in seconds.\n"
        "# duration_s : 2.0\n"
        "# step_s : 0.01\n"
        "# date : 2026-11-20 10:00:00\n"
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


def test_trajectory_init(base_config):
    """Check initial Trajectory object bound to TrajectoryConfig."""
    traj = Trajectory(config=base_config)
    assert traj.config == base_config
    assert traj.kin is None
    assert traj.timestamp is None
    assert traj.theta1 is None
    assert traj.theta2 is None
    assert traj.omega1 is None
    assert traj.omega2 is None


def test_trajectory_init_without_config_raises():
    """Check RuntimeError when instantiating Trajectory with None."""
    with pytest.raises(RuntimeError):
        Trajectory(config=None)  # type: ignore[arg-type]


def test_from_csv_loading(mock_logger, sample_trajectory_csv):
    """Check Trajectory.from_csv() factory and config metadata synchronization."""
    traj = Trajectory.from_csv(sample_trajectory_csv, mock_logger)

    assert traj.timestamp is not None
    assert traj.theta1 is not None
    assert traj.theta2 is not None
    assert len(traj.timestamp) == 201
    assert len(traj.theta1) == 201
    assert len(traj.theta2) == 201
    assert traj.config.duration_s == pytest.approx(2.0, abs=1e-5)
    assert traj.config.step_s == pytest.approx(0.01, abs=1e-5)
    assert traj.config.desc == "Harmonic test"
    assert traj.config.profile == "desynchronized_sine"
    assert traj.config.date == "2026-11-20 10:00:00"


def test_from_csv_missing_file(mock_logger, tmp_path):
    """Check FileNotFoundError for missing CSV input file."""
    missing = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError):
        Trajectory.from_csv(missing, mock_logger)


def test_generate_and_roundtrip(base_config):
    """Check full generate() -> CSV -> Trajectory.from_csv() consistency."""
    traj_src = Trajectory(config=base_config)
    traj_src.generate()

    assert base_config.output_path is not None
    assert Path(base_config.output_path).exists()

    traj_dst = Trajectory.from_csv(base_config.output_path, base_config.LOG)

    assert traj_src.timestamp is not None and traj_dst.timestamp is not None
    assert traj_src.theta1 is not None and traj_dst.theta1 is not None
    assert traj_src.theta2 is not None and traj_dst.theta2 is not None

    np.testing.assert_allclose(traj_src.timestamp, traj_dst.timestamp, atol=1e-5)
    np.testing.assert_allclose(traj_src.theta1, traj_dst.theta1, atol=1e-5)
    np.testing.assert_allclose(traj_src.theta2, traj_dst.theta2, atol=1e-5)
    assert traj_dst.config.profile == base_config.profile
    assert traj_dst.config.desc == base_config.desc


# --- B. Kinematic calculus and vectorization ---------------------------


def test_omegas_constant_speed(base_config):
    """Check numerical gradient speeds for linear angular trajectories."""
    traj = Trajectory(config=base_config)
    timestamp = np.linspace(0.0, 10.0, 1001)
    theta1 = 2.0 * timestamp
    theta2 = -1.0 * timestamp

    w1, w2 = traj._get_omegas(theta1, theta2, timestamp)
    np.testing.assert_allclose(w1, np.full_like(w1, 2.0), atol=1e-4)
    np.testing.assert_allclose(w2, np.full_like(w2, -1.0), atol=1e-4)


def test_gravity_at_rest(base_config):
    """Check bottom-oriented gravity vector for null rotation angles."""
    traj = Trajectory(config=base_config)
    theta1 = np.zeros(3)
    theta2 = np.zeros(3)

    g_pos = traj._get_gravity_positions(theta1, theta2)
    assert g_pos.shape == (3, 3)
    np.testing.assert_allclose(g_pos, np.tile(cv.G_LAB, (3, 1)), atol=1e-9)


def test_angular_velocity_frame_r2(base_config):
    """Check analytic Omega projection into moving frame R2."""
    traj = Trajectory(config=base_config)
    theta1 = np.array([0.0, np.pi / 2.0])
    w1 = np.array([1.0, 1.0])
    w2 = np.array([2.0, 2.0])

    expected = np.array(
        [
            [0.0, -2.0],
            [2.0, 0.0],
            [1.0, 1.0],
        ]
    )
    omega_vec = traj._process_angular_velocity(theta1, w1, w2)
    assert omega_vec.shape == (3, 2)
    np.testing.assert_allclose(omega_vec, expected, atol=1e-9)


def test_compute_kinematics_without_data_raises(base_config):
    """Check ValueError if compute_kinematics() is called before loading angles."""
    traj = Trajectory(config=base_config)
    with pytest.raises(ValueError):
        traj.compute_kinematics()


def test_compute_kinematics_pipeline(mock_logger, sample_trajectory_csv):
    """Check KinematicProfile container assembly from loaded CSV."""
    traj = Trajectory.from_csv(sample_trajectory_csv, mock_logger)
    profile = traj.compute_kinematics()

    assert isinstance(profile, KinematicProfile)
    assert traj.timestamp is not None
    n = len(traj.timestamp)

    assert profile.timestamp.shape == (n,)
    assert profile.g.shape == (n, 3)
    assert profile.omega1.shape == (n,)
    assert profile.omega2.shape == (n,)
    assert profile.Omega.shape == (3, n)
    assert profile.Omega_dot.shape == (3, n)

    g_norms = np.linalg.norm(profile.g, axis=1)
    np.testing.assert_allclose(g_norms, np.full(n, 9.81), atol=1e-7)


def test_trajectory_show_generates_pdf(mock_logger, sample_trajectory_csv, tmp_path):
    """Check that Trajectory.show() compiles a PDF report from an existing CSV."""
    pdf_out = tmp_path / "report_show.pdf"
    traj = Trajectory.from_csv(sample_trajectory_csv, mock_logger)
    traj.show(pdf_path=pdf_out)
    assert pdf_out.exists()

