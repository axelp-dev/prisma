"""
Trajectory generators tools defined by the PROFILE configuration describing 
all properties for each trajectory profile. 
"""

import numpy as np 

# ==============================================================================
# KINEMATIC PROFILE PRESETS & TUNING PARAMETERS
# ==============================================================================

PROFILES = {
    # Stochastic speed variation mimicking commercial 3D RPM random walk modes
    "random_walk": {
        "omega_max": np.pi / 2,  # Upper angular velocity bound [rad/s] (~15 RPM)
        "omega_min": 0.0,        # Lower angular velocity bound [rad/s]
    },

    # Harmonic desynchronized oscillations spanning the 3D spherical space (Lissajous)
    "desynchronized_sine": {
        "omega_1": 5.0 * np.sqrt(2),  # Inner gimbal angular pulsation [rad/s] (incommensurate ratio)
        "omega_2": 2.0,               # Outer gimbal angular pulsation [rad/s]
        "phi": 15.0,                  # Phase offset between axes [rad]
        "amp1": np.pi,                # Inner gimbal oscillation amplitude [rad]
        "amp2": np.pi,                # Outer gimbal oscillation amplitude [rad]
    },

    # Continuous bi-axial rotation using an irrational gear ratio to prevent closed orbits
    "constant_speed_ratio": {
        "omega_max": np.pi / 2,  # Upper speed bound for random drawing [rad/s]
        "omega_min": 0.0,        # Lower speed bound for random drawing [rad/s]
        "factor": 0.732,         # Non-harmonic velocity coupling ratio (omega2 = factor * omega1)
    },

    # Ground-based baseline control reference (static laboratory 1g orientation)
    "static_1g": {
        "omega_1": 0.0,  # Inner gimbal locked speed [rad/s]
        "omega_2": 0.0,  # Outer gimbal locked speed [rad/s]
    },

    # Classical single-axis 2D clinostat rotation (rotational gravity averaging in a plane)
    "clinostat_1d": {
        "omega_1": 0.0,          # Inner gimbal fixed along rotation axis [rad/s]
        "omega_2": np.pi / 4.0,  # Outer gimbal continuous rotation velocity [rad/s] (~7.5 RPM)
    },

    # Asymptotic exponential speed ramp for centrifugal detachment and boundary testing
    "centrifuge_sweep": {
        "omega_max": np.pi,  # Asymptotic maximum speed ceiling [rad/s] (~30 RPM)
        "tau": 25.0,         # Characteristic saturation time constant [s] (63.2% of omega_max at t = tau)
    },
}

# ==============================================================================
# PROFILES GENERATORS
# ==============================================================================

def generate_random_walk(duration_s: float, dt: float):
    """
    Generate random walk trajectory using Gaussian speed sampling.
    Angular positions are integrated using cumulative discrete steps.
    """
    N = int(duration_s / dt)
    timestamp = np.linspace(0.0, duration_s, N)
    
    cfg = PROFILES["random_walk"]
    omega_max = cfg["omega_max"]
    omega_min = cfg["omega_min"]
    mean_speed = (omega_max - omega_min) / 2.0
    scale_speed = (omega_max - omega_min) / 4.0

    # Draw random speeds
    omega1 = np.random.normal(loc=mean_speed, scale=scale_speed, size=N)
    omega2 = np.random.normal(loc=mean_speed, scale=scale_speed, size=N)

    # Correct discrete time integration: theta = sum(omega * dt)
    theta1 = np.cumsum(omega1) * dt
    theta2 = np.cumsum(omega2) * dt

    return timestamp, theta1, theta2, omega1, omega2


def generate_desynchronized_sine(durations_s: float, step_s: float):
    """
    Generate harmonic desynchronized trajectory covering the spherical space.
    Positions and velocities are evaluated analytically.
    """
    cfg = PROFILES["desynchronized_sine"]
    w1 = cfg.get("omega_1", cfg.get("omega1", 1.0))
    w2 = cfg.get("omega_2", cfg.get("omega2", np.sqrt(2)))
    phi = cfg.get("phi", 0.0)
    a1 = cfg.get("amp1", np.pi)
    a2 = cfg.get("amp2", np.pi)

    N = int(durations_s / step_s)
    timestamp = np.linspace(0.0, durations_s, N)

    # Analytical harmonic positions
    theta1 = a1 * np.sin(w1 * timestamp)
    theta2 = a2 * np.sin(w2 * timestamp + phi)

    # Exact analytical time derivatives
    omega1 = a1 * w1 * np.cos(w1 * timestamp)
    omega2 = a2 * w2 * np.cos(w2 * timestamp + phi)

    return timestamp, theta1, theta2, omega1, omega2


def generate_constant_speed_ratio(durations_s: float, step_s: float, omega: float = None):
    """
    Generate continuous rotation with fixed desynchronized gear ratio.
    omega1 = omega, omega2 = omega * factor.
    """
    cfg = PROFILES["constant_speed_ratio"]
    if omega is None:
        omega_min = cfg["omega_min"]
        omega_max = cfg["omega_max"]
        omega = (omega_max + omega_min) / 2.0

    factor = cfg["factor"]
    N = int(durations_s / step_s)
    timestamp = np.linspace(0.0, durations_s, N)

    w1_val = float(omega)
    w2_val = float(omega * factor)

    omega1 = np.full(N, w1_val)
    omega2 = np.full(N, w2_val)

    # Analytical integration for constant speed: theta(t) = omega * t
    theta1 = w1_val * timestamp
    theta2 = w2_val * timestamp

    return timestamp, theta1, theta2, omega1, omega2


def generate_static_1g(durations_s: float, step_s: float):
    """
    Generate static ground baseline control trajectory (fixed 1g reference).
    """
    N = int(durations_s / step_s)
    timestamp = np.linspace(0.0, durations_s, N)

    theta1 = np.zeros(N)
    theta2 = np.zeros(N)
    omega1 = np.zeros(N)
    omega2 = np.zeros(N)

    return timestamp, theta1, theta2, omega1, omega2


def generate_clinostat_1d(durations_s: float, step_s: float):
    """
    Generate single-axis constant 2D clinostat rotation (axis 1 fixed, axis 2 rotating).
    """
    w2_val = PROFILES["clinostat_1d"].get("omega_2", PROFILES["clinostat_1d"].get("omega_1", np.pi / 2))
    N = int(durations_s / step_s)
    timestamp = np.linspace(0.0, durations_s, N)

    omega1 = np.zeros(N)
    omega2 = np.full(N, w2_val)

    theta1 = np.zeros(N)
    theta2 = w2_val * timestamp

    return timestamp, theta1, theta2, omega1, omega2


def generate_centrifuge_sweep(durations_s: float, step_s: float):
    """Generate a bounded saturation sweep trajectory for centrifugal testing.

    The angular velocity approaches omega_max smoothly using an exponential
    saturation curve: omega(t) = omega_max * (1 - exp(-t / tau)).
    Angles theta1 and theta2 are integrated using the constant time step dt.
    """
    # Retrieve profile kinematic parameters
    cfg = PROFILES.get("centrifuge_sweep", {})
    omega_max = cfg.get("omega_max", np.pi)
    tau = cfg.get("tau", durations_s / 4.0)

    # Build temporal discretization
    N = int(durations_s / step_s)
    timestamp = np.linspace(0.0, durations_s, N)
    dt = float(timestamp[1] - timestamp[0]) if N > 1 else step_s

    # Compute bounded velocity profiles
    omega1 = omega_max * (1.0 - np.exp(-timestamp / tau))
    omega2 = omega_max * (1.0 - np.exp(-timestamp / tau))

    # Integrate angular velocities to obtain continuous angular positions
    # theta(t) = \int omega(tau) dtau via discrete cumulative trapezoid/rectangle
    theta1 = np.cumsum(omega1) * dt
    theta2 = np.cumsum(omega2) * dt

    return timestamp, theta1, theta2, omega1, omega2