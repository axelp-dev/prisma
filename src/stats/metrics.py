"""PRISMA Metrics calculation module for RPM Trajectories and Kinematics."""

import numpy as np


def compute_mean_vectorial_gravities(g_values: np.ndarray) -> np.ndarray:
    """Compute cumulative time-averaged gravity vector series: <g>(t)."""
    g_cumsum = np.cumsum(g_values, axis=0)
    counts = np.arange(1, len(g_values) + 1)[:, None]
    return g_cumsum / counts


def compute_residual_gravity_ratio(
    g_values: np.ndarray, g0: float = 9.81
) -> np.ndarray:
    """Compute instantaneous cumulative residual gravity ratio ||<g>(t)|| / g0."""
    g_means = compute_mean_vectorial_gravities(g_values)
    g_norms = np.linalg.norm(g_means, axis=1)
    return g_norms / g0


def compute_dispersion_tensor(
    g_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Compute the 3D directional orientation tensor S = (1/N) * sum(u_i @ u_i^T).

    Returns:
        tuple[np.ndarray, np.ndarray, float]:
            - S: 3x3 orientation tensor.
            - eigvals: sorted eigenvalues (lambda_1 <= lambda_2 <= lambda_3).
            - isotropy_index: 3 * lambda_1 (equals 1.0 for isotropic distribution).
    """
    norms = np.linalg.norm(g_values, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    u = g_values / norms

    tensor = (u.T @ u) / len(g_values)
    eigvals = np.sort(np.linalg.eigvalsh(tensor))
    isotropy_index = float(3.0 * eigvals[0])
    return tensor, eigvals, isotropy_index


def compute_extreme_kinematics(
    omega1: np.ndarray, omega2: np.ndarray, timestamp: np.ndarray
) -> dict:
    """Compute peak and RMS angular speeds and accelerations for both axes."""
    alpha1 = np.gradient(omega1, timestamp)
    alpha2 = np.gradient(omega2, timestamp)
    return {
        "max_alpha1": float(np.max(np.abs(alpha1))),
        "max_alpha2": float(np.max(np.abs(alpha2))),
        "max_omega1": float(np.max(np.abs(omega1))),
        "max_omega2": float(np.max(np.abs(omega2))),
        "rms_omega1": float(np.sqrt(np.mean(omega1**2))),
        "rms_omega2": float(np.sqrt(np.mean(omega2**2))),
    }


def compute_total_angular_velocity_stats(Omega: np.ndarray) -> dict:
    """Compute statistical properties of the sample frame R2 total angular velocity vector."""
    # Omega shape is (3, N) in KinematicProfile
    omega_norm = np.linalg.norm(Omega, axis=0)
    omega_rms = float(np.sqrt(np.mean(omega_norm**2)))
    max_omega = float(np.max(omega_norm))
    kinetic_rot_energy = float(np.mean(omega_norm**2))
    return {
        "omega_norm_series": omega_norm,
        "omega_rms": omega_rms,
        "max_omega": max_omega,
        "kinetic_rot_energy": kinetic_rot_energy,
    }


def compute_spherical_coordinates(
    g_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert Cartesian gravity vectors into spherical coordinates (longitude, latitude) in radians.

    Returns:
        tuple[np.ndarray, np.ndarray]:
            - lon: Longitude in [-pi, pi].
            - lat: Latitude in [-pi/2, pi/2].
    """
    norms = np.linalg.norm(g_values, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    u = g_values / norms

    lon = np.arctan2(u[:, 1], u[:, 0])
    lat = np.arcsin(np.clip(u[:, 2], -1.0, 1.0))
    return lon, lat