# ====================================================================
#                     Kinematics Converter
# ====================================================================
#
# Canonical 2-axis convention (see src/conventions.py / CONVENTIONS.md):
#   INNER axis theta1 (azimuth) about Z1 (vertical at rest), OUTER axis theta2
#   (tilt) about Y0 (horizontal). A "point" is the gravity DIRECTION in R2:
#       g / 9.81 = [cos(t1) sin(t2), sin(t1) sin(t2), -cos(t2)]
#   Rest (t1 = t2 = 0) -> [0, 0, -1]. Singularity at vertical gravity (|z| -> 1).

import numpy as np
from scipy.spatial.transform import Rotation


class CanonicalTwoAxis:
    """Single source of truth mapping motor angles <-> gravity direction.

    Implements the KinematicsBackend contract the MPC injects (duck-typed):
    n_axes, angles_to_point, point_to_angles, resolve_angles_batch,
    validate_motor_speeds_batch, per_axis_rpm_batch, jacobian_condition_batch,
    has_singularity, singularity_proximity_batch, refine_angles.
    """

    def __init__(self, n_axes: int = 2):
        self.n_axes = n_axes

    # -- Core bijection S^2 <-> angles ---------------------------------

    def angles_to_point(self, angles: np.ndarray) -> np.ndarray:
        """[theta1, theta2] -> gravity direction (forward kinematics)."""
        t1, t2 = angles[0], angles[1]
        return np.array([
            np.cos(t1) * np.sin(t2), 
            np.sin(t1) * np.sin(t2), 
            -np.cos(t2)
        ])
        # return np.array([
        #     np.cos(t2) * np.sin(t1),
        #     -np.sin(t2) * np.sin(t1),
        #     -np.cos(t1),
        # ])

    def point_to_angles(self, point: np.ndarray) -> np.ndarray:
        """Gravity direction -> [theta1, theta2] (analytic inverse).

        theta1 in (-pi, pi] is the azimuth (inner axis); theta2 in [0, pi] is
        the tilt (outer axis).
        """
        x, y, z = point[0], point[1], point[2]
        theta1 = np.arctan2(y, x)
        theta2 = np.arctan2(np.hypot(x, y), -z)
        return np.array([theta1, theta2])

    def rotation(self, angles: np.ndarray) -> Rotation:
        """Full orientation R0 -> R2 (lab -> sample) as a scipy Rotation.

        Generalizes angles_to_point: the gravity direction is
        ``rotation(a).apply(G_LAB) / G0``. Vectorized -- ``angles`` may be
        shape (2,) for one pose or (N, 2) for a batch, yielding a single or a
        length-N Rotation. Needed by the expected/monitoring generation
        (angular velocity, angular acceleration, orientation quaternion),
        which requires the whole orientation, not just gravity.

        Convention (CONVENTIONS.md 2.1): R = Rot(theta1) . Rot(theta2) with
        Rot(theta2) = R_y(-theta2) [outer tilt] and Rot(theta1) = R_z(theta1)
        [inner azimuth].
        """
        a = np.asarray(angles, dtype=float)
        t1 = a[..., 0]
        t2 = a[..., 1]
        if t1.ndim > 0:
            t1 = t1[..., np.newaxis]
            t2 = t2[..., np.newaxis]
        return Rotation.from_euler("z", t1) * Rotation.from_euler("y", -t2)

    def resolve_angles_batch(
        self,
        points: np.ndarray,
        current_angles: np.ndarray | None = None,
    ) -> np.ndarray:
        """Vectorized inverse kinematics: S^2 points -> [theta1, theta2].

        Named `resolve_angles_batch` to match the KinematicsBackend contract
        the MPC calls (`mpc.py` invokes it with the candidate points and the
        current angles). `current_angles` is unused: 2-axis IK is analytic
        and stateless.
        """
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        theta1 = np.arctan2(y, x)
        theta2 = np.arctan2(np.hypot(x, y), -z)
        return np.column_stack([theta1, theta2])

    # -- Motor feasibility --------------------------------------------

    def validate_motor_speeds_batch(
        self,
        candidate_angles: np.ndarray,
        current_angles: np.ndarray,
        max_rpms: tuple[float, ...],
        dt: float,
    ) -> np.ndarray:
        """Per-candidate motor-speed check against per-axis RPM limits."""
        rpms = self.per_axis_rpm_batch(candidate_angles, current_angles, dt)
        limits = np.array(max_rpms[:2])
        return ~np.any(rpms > limits[np.newaxis, :], axis=1)

    def per_axis_rpm_batch(
        self,
        candidate_angles: np.ndarray,
        current_angles: np.ndarray,
        dt: float,
    ) -> np.ndarray:
        """Per-axis |RPM|, shortest angular path (wrap at +/-pi) on both axes.

        theta1 is an azimuth that genuinely wraps across +/-pi; theta2 is a
        tilt bounded to [0, pi] (|delta| <= pi, so its wrap is a no-op).
        """
        deltas = candidate_angles - current_angles[np.newaxis, :]
        d1 = np.remainder(deltas[:, 0] + np.pi, 2 * np.pi) - np.pi
        d2 = np.remainder(deltas[:, 1] + np.pi, 2 * np.pi) - np.pi
        return np.column_stack([np.abs(d1), np.abs(d2)]) / dt * 60.0 / (2.0 * np.pi)

    # -- Singularity (vertical poles) ---------------------------------

    def jacobian_condition_batch(self, angles: np.ndarray) -> np.ndarray:
        """Condition number kappa ~ 1 / |sin(theta2)|.

        The map degenerates as theta2 -> 0 or pi (gravity vertical): the
        azimuth theta1 stops moving the gravity vector. Returns 1e12 at the
        pole to stay finite.
        """
        theta2 = angles[:, 1]
        st2 = np.abs(np.sin(theta2))
        return np.where(st2 > 1e-12, 1.0 / st2, 1e12)

    def has_singularity(self) -> bool:
        return True

    def singularity_proximity_batch(
        self,
        candidates: np.ndarray,
        threshold: float,
    ) -> np.ndarray:
        """Flag candidates near the vertical poles (|z| > 1 - threshold)."""
        return np.abs(candidates[:, 2]) > (1.0 - threshold)

    def refine_angles(
        self,
        target_point: np.ndarray,
        approx_angles: np.ndarray,
        max_iterations: int = 10,
    ) -> np.ndarray:
        """No-op for 2-axis: the analytic IK solution is already exact."""
        return approx_angles
