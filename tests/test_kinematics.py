import numpy as np
import pytest

from src.core import conventions as cv
from src.core.kinematics import CanonicalTwoAxis


@pytest.fixture
def kin():
    return CanonicalTwoAxis()


@pytest.fixture(autouse=True)
def _seed():
    """Make every np.random draw in this module deterministic."""
    np.random.seed(0)


# --- A. Forward map (the convention) --------------------------------

def test_has_singularity(kin):
    assert kin.has_singularity() is True


def test_rest_angles2point(kin):
    """At rest, gravity points straight down."""
    point = kin.angles_to_point(np.array([0.0, 0.0]))
    np.testing.assert_allclose(point, [0.0, 0.0, -1.0], atol=1e-9)


def test_angles2point_formulae(kin):
    """Forward map matches the canonical closed form."""
    t1, t2 = np.deg2rad(30), np.deg2rad(20)
    expected = np.array([
        np.cos(t1) * np.sin(t2),
        np.sin(t1) * np.sin(t2),
        -np.cos(t2),
    ])
    np.testing.assert_allclose(kin.angles_to_point(np.array([t1, t2])), expected, atol=1e-9)


def test_unity_norm(kin):
    """angles_to_point always returns a unit vector."""
    angles = np.random.uniform(0, np.pi, size=(10, 2))
    points = np.array([kin.angles_to_point(a) for a in angles])
    norms = np.linalg.norm(points, axis=1)
    np.testing.assert_allclose(norms, np.ones(10), atol=1e-9)


# --- B. INNER / OUTER physical properties (anti-T3 guardrails) ------

def test_inner_axis_keeps_gz(kin):
    """INNER (theta1) spins about the vertical: gz stays -cos(theta2)."""
    theta2 = np.full(10, np.random.uniform() * np.pi)    # tilt fixé
    theta1 = np.random.uniform(-np.pi, np.pi, size=10)    # azimuth varie
    angles = np.stack((theta1, theta2), axis=-1)
    points = np.array([kin.angles_to_point(a) for a in angles])
    np.testing.assert_allclose(points[:, 2], -np.cos(theta2), atol=1e-9)


def test_inner_spin_at_rest(kin):
    """At theta2 = 0 gravity is [0, 0, -1] whatever theta1 (inner spins about g)."""
    theta1 = np.random.uniform(-np.pi, np.pi, size=10)
    angles = np.stack((theta1, np.zeros(10)), axis=-1)
    points = np.array([kin.angles_to_point(a) for a in angles])
    np.testing.assert_allclose(points, np.tile([0.0, 0.0, -1.0], (10, 1)), atol=1e-9)


def test_outer_axis_in_xz_plane(kin):
    """OUTER (theta1) tilts gravity in the X-Z plane: gy = 0 when theta2 = 0."""
    theta2 = np.random.uniform(0, np.pi, size=10)
    angles = np.stack((theta2, np.zeros(10)), axis=-1)
    points = np.array([kin.angles_to_point(a) for a in angles])
    np.testing.assert_allclose(points[:, 1], np.zeros(10), atol=1e-9)


# --- B'. Full orientation consistent with the forward gravity map ---

def test_rotation_matches_forward(kin):
    """rotation(a).apply(G_LAB)/G0 == angles_to_point(a), batch and scalar."""
    angles = np.array(
        [[0.0, 0.0], [np.pi / 2, 0.0], [np.pi / 2, np.pi / 2], [1.1, -0.7], [2.3, 2.0]]
    )
    g_batch = kin.rotation(angles).apply(cv.G_LAB) / cv.G0
    expected = np.array([kin.angles_to_point(a) for a in angles])
    np.testing.assert_allclose(g_batch, expected, atol=1e-9)
    for a in angles:
        np.testing.assert_allclose(
            kin.rotation(a).apply(cv.G_LAB) / cv.G0, kin.angles_to_point(a), atol=1e-9
        )


# --- C. Round-trip (bijection), kept away from the poles ------------

def test_round_trip_angles(kin):
    """angles -> point -> angles, away from the vertical singularity."""
    theta1 = np.random.uniform(-np.pi + 0.05, np.pi - 0.05, size=10)   # azimuth
    theta2 = np.random.uniform(0.05, np.pi - 0.05, size=10)            # tilt
    angles = np.stack((theta1, theta2), axis=-1)
    points = np.array([kin.angles_to_point(a) for a in angles])
    back = np.array([kin.point_to_angles(p) for p in points])
    np.testing.assert_allclose(back, angles, atol=1e-9)


def test_round_trip_points(kin):
    """point -> angles -> point on the unit sphere (robust even at the poles)."""
    raw = np.random.uniform(-1, 1, size=(10, 3))
    points = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    angles = np.array([kin.point_to_angles(p) for p in points])
    back = np.array([kin.angles_to_point(a) for a in angles])
    np.testing.assert_allclose(back, points, atol=1e-9)


# --- D. Batch == scalar ---------------------------------------------

def test_resolve_batch_matches_scalar(kin):
    """resolve_angles_batch == stacked point_to_angles (called like the MPC)."""
    raw = np.random.uniform(-1, 1, size=(10, 3))
    points = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    scalar = np.array([kin.point_to_angles(p) for p in points])
    batch = kin.resolve_angles_batch(points, current_angles=np.zeros(2))
    np.testing.assert_allclose(batch, scalar, atol=1e-9)


# --- E. Singularity / Jacobian (poles are vertical) -----------------

def test_singularity_proximity(kin):
    """Vertical gravity is near-singular; equatorial is not."""
    candidates = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
    near = kin.singularity_proximity_batch(candidates, threshold=0.1)
    assert near[0]        # north pole
    assert near[1]        # south pole (rest)
    assert not near[2]    # equator


def test_jacobian_blows_up_at_pole(kin):
    """kappa ~ 1/|sin(theta2)|: huge at the poles, ~1 at the equator."""
    angles = np.array([[0.0, 1e-3], [0.0, np.pi / 2], [0.0, np.pi - 1e-3]])
    kappa = kin.jacobian_condition_batch(angles)
    assert kappa[0] > 100
    assert kappa[1] == pytest.approx(1.0, abs=1e-6)
    assert kappa[2] > 100


# --- F. Motor speeds / wrapping -------------------------------------

def test_azimuth_takes_shortest_path(kin):
    """theta2 is an azimuth: +3.0 -> -3.0 is a (2pi - 6) rad move, not 6 rad."""
    current = np.array([np.pi / 2, 3.0])
    candidate = np.array([[np.pi / 2, -3.0]])
    dt = 1.0
    rpm = kin.per_axis_rpm_batch(candidate, current, dt)
    shortest = 2 * np.pi - 6.0                       # ~0.283 rad
    expected = shortest / dt * 60.0 / (2 * np.pi)
    assert rpm[0, 0] == pytest.approx(0.0, abs=1e-9)  # theta1 unchanged
    assert rpm[0, 1] == pytest.approx(expected, abs=1e-9)


def test_validate_rejects_too_fast(kin):
    """A tiny move is allowed; a 3 rad move in 0.5 s exceeds 15 rpm."""
    current = np.array([0.0, 0.0])
    candidates = np.array([[0.01, 0.01], [3.0, 0.0]])
    ok = kin.validate_motor_speeds_batch(candidates, current, (15.0, 15.0), dt=0.5)
    assert ok[0]
    assert not ok[1]
