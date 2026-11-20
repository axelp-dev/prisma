import logging
from pathlib import Path

import numpy as np
import pytest

from src.config import SimulationConfig, TrajectoryConfig
from src.simulation.simulation import Simulation
from src.trajectory.Trajectory import Trajectory


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_simulation")


@pytest.fixture
def generated_trajectory_file(mock_logger, tmp_path):
    """Generate a valid short trajectory CSV file for simulation integration tests."""
    traj_csv = tmp_path / "input_traj.csv"
    t_cfg = TrajectoryConfig(
        LOG=mock_logger,
        output_path=traj_csv,
        duration_s=1.0,
        step_s=0.01,
        profile="static_1g",
        log_report=False,
    )
    Trajectory(t_cfg).generate()
    return traj_csv


@pytest.fixture
def sim_config(mock_logger, generated_trajectory_file, tmp_path):
    """Provide a valid SimulationConfig for headless execution."""
    return SimulationConfig(
        LOG=mock_logger,
        input_file=str(generated_trajectory_file),
        output_file=str(tmp_path / "sim_out.csv"),
        log_report=False,
        preset="glycerol_bead",
        init_pos=np.array([0.0, 0.0, 0.0]),
        particle_radius=1.5e-3,
        tube_radius=0.05,
        rho=1202.0,
        rho_f=1200.0,
        mu_f=1.412,
        k=0.0,
    )


def test_simulation_init_without_config_raises():
    """Verify RuntimeError when instantiating Simulation without SimulationConfig."""
    with pytest.raises(RuntimeError):
        Simulation(config=None)


def test_simulation_init_with_report(sim_config):
    """Verify report_path mirrors output_file with .pdf extension when log_report is True."""
    sim_config.log_report = True
    sim = Simulation(config=sim_config)
    assert sim.config.output_file is not None
    assert sim.report_path == Path(sim_config.output_file).with_suffix(".pdf")


def test_simulation_run_and_csv_export(sim_config):
    """Verify end-to-end simulation execution and self-describing CSV serialization."""
    sim = Simulation(config=sim_config)
    sim.run()

    assert sim_config.output_file is not None
    out_path = Path(sim_config.output_file)
    assert out_path.exists()
    assert sim.result is not None
    assert sim.result.positions.shape[1] == 3


def test_parse_header_metadata(tmp_path):
    """Verify Simulation._parse_header accurately reconstructs typed metadata values."""
    csv_path = tmp_path / "header_test.csv"
    content = (
        "# ===============================================\n"
        "#             SIMULATION RESULT\n"
        "# ===============================================\n"
        "# input_file : data/trajectories/test.csv\n"
        "# log_report : False\n"
        "# preset : None\n"
        "# init_pos : [0.0, 0.0, 0.005]\n"
        "# particle_radius : 0.0015\n"
        "# tube_radius : 0.05\n"
        "# rho : 1202.0\n"
        "# rho_f : 1200.0\n"
        "# mu_f : 1.412\n"
        "# k : 0.0\n"
        "timestamp,x,y,z,vx,vy,vz,reynolds\n"
        "0.0,0.0,0.0,0.005,0.0,0.0,0.0,0.0\n"
    )
    csv_path.write_text(content, encoding="utf-8")

    meta = Simulation._parse_header(str(csv_path))

    assert meta["input_file"] == "data/trajectories/test.csv"
    assert meta["log_report"] is False
    assert meta["preset"] is None
    assert meta["particle_radius"] == pytest.approx(0.0015)
    np.testing.assert_allclose(meta["init_pos"], [0.0, 0.0, 0.005])


def test_simulation_from_csv_reload(mock_logger, sim_config):
    """Verify Simulation.from_csv reconstructs both SimulationConfig and SimulationResult."""
    sim_src = Simulation(config=sim_config)
    sim_src.run()

    assert sim_config.output_file is not None
    sim_dst = Simulation.from_csv(str(sim_config.output_file), mock_logger)

    assert sim_src.result is not None and sim_dst.result is not None
    np.testing.assert_allclose(
        sim_src.result.positions, sim_dst.result.positions, atol=1e-6
    )
    np.testing.assert_allclose(
        sim_src.result.reynolds, sim_dst.result.reynolds, atol=1e-6
    )
    assert sim_dst.config.particle_radius == pytest.approx(sim_config.particle_radius)
    assert sim_dst.config.tube_radius == pytest.approx(sim_config.tube_radius)


def test_simulation_show_generates_pdf(mock_logger, sim_config, tmp_path):
    """Verify Simulation.show() compiles the 3-page PDF simulation report."""
    sim = Simulation(config=sim_config)
    sim.run()

    assert sim_config.output_file is not None
    reloaded = Simulation.from_csv(str(sim_config.output_file), mock_logger)
    pdf_out = tmp_path / "sim_report_test.pdf"
    reloaded.show(pdf_path=str(pdf_out))

    assert pdf_out.exists()
