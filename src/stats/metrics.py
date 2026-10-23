"""PRISMA Metrics calculation module for RPM Trajectories and Kinematics."""

import numpy as np


def compute_spectral_density(
    signal: np.ndarray, dt: float
) -> tuple[np.ndarray, np.ndarray]:
    """Compute single-sided Fast Fourier Transform (FFT) amplitude spectrum.

    Parameters:
        signal (np.ndarray): 1D temporal signal array.
        dt (float): Sampling step in seconds.

    Returns:
        tuple[np.ndarray, np.ndarray]:
            - freqs: Non-negative frequency bins [Hz].
            - amplitudes: Single-sided normalized amplitudes.
    """
    n = len(signal)
    fft_vals = np.fft.rfft(signal - np.mean(signal))  # Remove DC bias
    amplitudes = (2.0 / n) * np.abs(fft_vals)
    amplitudes[0] /= 2.0
    freqs = np.fft.rfftfreq(n, d=dt)
    return freqs, amplitudes


def compute_spatial_dispersion_stats(
    positions: np.ndarray, x0: np.ndarray
) -> dict:
    """Compute particle gyration radius, net drift, path length, and anchor deviation.

    Parameters:
        positions (np.ndarray): Shape (N, 3) trajectory array.
        x0 (np.ndarray): Initial equilibrium anchor vector (3,).

    Returns:
        dict: Spatial dispersion and trajectory extent indicators.
    """
    # Net drift and total integrated distance
    net_displacement_vec = positions[-1] - positions[0]
    net_drift = float(np.linalg.norm(net_displacement_vec))

    segment_vectors = np.diff(positions, axis=0)
    segment_lengths = np.linalg.norm(segment_vectors, axis=1)
    total_path_length = float(np.sum(segment_lengths))

    tortuosity = (
        float(total_path_length / net_drift)
        if net_drift > 1e-12
        else float("inf")
    )

    # Gyration radius around trajectory centroid
    centroid = np.mean(positions, axis=0)
    deviations = positions - centroid
    gyration_radius = float(np.sqrt(np.mean(np.sum(deviations**2, axis=1))))

    # RMS distance to elastic anchor x0
    elastic_anchor_deviations = positions - x0
    rms_anchor_distance = float(
        np.sqrt(np.mean(np.sum(elastic_anchor_deviations**2, axis=1)))
    )

    return {
        "centroid": centroid,
        "net_drift": net_drift,
        "total_path_length": total_path_length,
        "tortuosity": tortuosity,
        "gyration_radius": gyration_radius,
        "rms_anchor_distance": rms_anchor_distance,
    }


def compute_confinement_stats(
    positions: np.ndarray, r_tube: float
) -> dict:
    """Analyze wall proximity and inelastic contact occurrences."""
    radial_distances = np.linalg.norm(positions, axis=1)
    max_radial_distance = float(np.max(radial_distances))
    min_wall_distance = float(r_tube - max_radial_distance)

    # Fraction of time spent on or beyond boundary
    contact_indices = radial_distances >= (r_tube - 1e-8)
    contact_time_ratio = float(np.mean(contact_indices))

    return {
        "radial_distances": radial_distances,
        "max_radial_distance": max_radial_distance,
        "min_wall_distance": min_wall_distance,
        "contact_time_ratio": contact_time_ratio,
    }


def compute_reynolds_stats(reynolds_series: np.ndarray) -> dict:
    """Compute particle Reynolds number distribution indicators."""
    max_re = float(np.max(reynolds_series))
    mean_re = float(np.mean(reynolds_series))
    median_re = float(np.median(reynolds_series))
    re_exceeded = bool(max_re >= 0.1)

    return {
        "max_re": max_re,
        "mean_re": mean_re,
        "median_re": median_re,
        "re_exceeded": re_exceeded,
    }


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