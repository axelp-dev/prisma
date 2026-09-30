"""Constants and reference frames for Gravilab

- R0 (lab): X0 towards the user, Y0 = OUTER AXIS (horizontal, to the
user's right), Z0 = vertical, pointing up. Right-handed orthonormal basis.
Gravity in R0: g = [0, 0, -9.81].
- R1 (outer frame / OUTER): rotation by theta2 (tilt) around Y0.
- R2 (inner frame / INNER = sample): rotation by theta1 (azimuth) around Z1
(which coincides with Z0 at rest).

This module contains ONLY reference frame constants and sensor mounts.
The kinematics (forward/IK theta <-> gravity) reside in `core/kinematics.py`.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

# --- Physics constants ---
G0: float = 9.81
G_LAB: np.ndarray = np.array([0.0, 0.0, -G0])  # R0 gravity

# --- R0 basis ---
X0: np.ndarray = np.array([1.0, 0.0, 0.0])  # to user
Y0: np.ndarray = np.array([0.0, 1.0, 0.0])  # OUTER AXIS
Z0: np.ndarray = np.array([0.0, 0.0, 1.0])  # verical axis

# --- Two frames rotations axis ---
OUTER_AXIS: np.ndarray = Y0          # theta2 (tilt) rotates around Y0 (horizontal)
INNER_AXIS_AT_REST: np.ndarray = Z0  # theta1 (azimuth) rotates around Z1 (= Z0 at rest)

_SENSOR_MOUNTS: dict[str, Rotation] = {
    "bottom": Rotation.identity(),
    "center": Rotation.identity(),
    "corner": Rotation.identity(),
}

def sensor_mount(placement: str) -> Rotation:
    key = placement.strip().lower()
    if key not in _SENSOR_MOUNTS:
        raise ValueError(
            f"Emplacement inconnu : {placement!r} (connus : {list(_SENSOR_MOUNTS)})"
        )
    return _SENSOR_MOUNTS[key]


# --- Sensor mounting positions p_S (metres, in the sample frame R2) ---
# Used by the expected-signal generation for the centrifugal / tangential
# terms. `center` sits at the rotation centre (no lever arm -> no centrifugal
# force). The others are PLACEHOLDERS: replace with the measured mounting
# offsets before trusting the off-centre a_sensor prediction.
_SENSOR_POSITIONS: dict[str, np.ndarray] = {
    "bottom": np.array([0.045, 0.025, 0.17]),
    "center": np.array([0.065, 0.07, 0.145]),
    "corner": np.array([0.05, 0.135, 0.16]),
}


def sensor_position(placement: str) -> np.ndarray:
    key = placement.strip().lower()
    if key not in _SENSOR_POSITIONS:
        raise ValueError(
            f"Emplacement inconnu : {placement!r} (connus : {list(_SENSOR_POSITIONS)})"
        )
    return _SENSOR_POSITIONS[key]