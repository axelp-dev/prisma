import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from src.core import conventions as cv


def test_rest_gravity():
    np.testing.assert_allclose(cv.G_LAB, [0.0, 0.0, -9.81])

def test_R0_basis(): 
    M = np.array([cv.X0, cv.Y0, cv.Z0])
    # orthonormal : M @ M^T = I
    np.testing.assert_allclose(M @ M.T, np.eye(3), atol=1e-12)
    # direct : X0 ^ Y0 = Z0
    np.testing.assert_allclose(np.cross(cv.X0, cv.Y0), cv.Z0, atol=1e-12)


def test_outer_inner_axis():
    np.testing.assert_allclose(cv.OUTER_AXIS, cv.Y0)          # OUTER arount Y_0
    np.testing.assert_allclose(cv.INNER_AXIS_AT_REST, cv.Z0)  # INNER around Z1 = Z0 at rest


@pytest.mark.parametrize("placement", ["bottom", "center", "corner", "CENTER", " Bottom "])
def test_mount_roundtrip(placement):
    R = cv.sensor_mount(placement)
    v = np.array([0.3, -0.5, 0.81])
    np.testing.assert_allclose(R.inv().apply(R.apply(v)), v, atol=1e-12)


def test_mount_roundtrip_non_trivial():
    R = Rotation.from_euler("xyz", [37.0, -12.0, 95.0], degrees=True)
    v = np.array([0.3, -0.5, 0.81])
    np.testing.assert_allclose(R.inv().apply(R.apply(v)), v, atol=1e-12)

def test_mount_unknown():
    with pytest.raises(ValueError):
        cv.sensor_mount("nope")
